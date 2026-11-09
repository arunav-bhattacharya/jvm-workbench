# Teach Functional Kotlin by Retraining Java Instincts

The best way to teach functional programming in Kotlin to an experienced Java/Kotlin backend engineer is as a sequence of concrete habits whose payoff and cost can be shown on the JVM, not as theory. Start with pure functions, referential transparency and immutability (the "why"). Move to function values and what they compile to, then to collection pipelines and laziness, where FP becomes daily work. Then cover Kotlin's idiom layer of nullable types and scope functions, then errors as values, and leave composition, currying and tail recursion for last. One idea organises the whole course: many Kotlin features that look like guarantees are only signals. `val` does not freeze an object, `List` is a read-only view that a cast can mutate, `copy()` is shallow, a misplaced `tailrec` only produces a warning, and `kotlin.Result` was explicitly not designed for domain errors. Each module should therefore centre on a demo where students predict the output, then run it, and the output breaks one Java-trained instinct. Examples are a "harmless" refactoring that charges a card twice, an `associateBy` that silently drops duplicate keys where Java's `toMap` throws, a `?.let { } ?: run { }` that runs both branches, and a `runCatching` that lets a cancelled coroutine keep charging. For a performance-minded audience the news is good. `Iterable` operations and all scope functions are `inline`, so idiomatic chains compile to plain loops with no lambda objects, and nullable types cost almost nothing at runtime. The real costs are specific and measurable: intermediate lists, boxing, and one object per stage in sequences. Kotlin sequences work like Java streams in one respect: both are lazy and pass one element at a time through every step. Unlike streams, sequences can be iterated more than once, have no parallel mode and no primitive specialisations, and end in direct functions rather than `Collectors`. Several of these facts changed between 2024 and 2026, and native error unions are still only a proposal, so the course must pin versions: Kotlin 2.4.21, Arrow 2.3.0, kotlinx.collections.immutable 0.5.2.

## Eight modules, ordered from consequences to abstractions

The case for FP that persuades backend engineers is modularity and testability, not mathematical elegance. John Hughes's classic paper argues that listing what FP forbids (assignment, side effects) misses the point. The real gain, he argues, is new kinds of glue for building modular programs, namely higher-order functions and lazy evaluation ([Hughes, Why Functional Programming Matters](https://www.cse.chalmers.se/~rjmh/Papers/whyfp.pdf)). That framing maps directly onto a course plan. First, establish why pure, immutable code is easier to reason about. Then teach the two kinds of glue as Kotlin implements them: lambdas with inline higher-order functions, and sequences. Then cover the Kotlin-specific idioms. Finish with typed errors as the architecture that ties everything together. The table gives the order and the one demo that should anchor each module.

| # | Module | Java instinct to retrain | Anchor demo (predict, then run) |
|---|---|---|---|
| 1 | Pure functions, referential transparency, functional core/imperative shell, expressions over statements | "Extract variable" is always safe; branches assign a `var` | Inline `feeFor(x)` twice (same result) vs `chargeCard(x)` twice (two provider calls) |
| 2 | Immutability: `val`, read-only vs immutable collections, `copy()`, persistent collections | `final` plus an unmodifiable-looking type means nothing can change | `(listOf(1, 2, 3) as MutableList<Int>)[0] = 99` succeeds; `p1.copy().tags.add(…)` also changes `p1` |
| 3 | Function types, lambdas, closures, higher-order functions, `inline` | Lambdas are anonymous classes and always allocate | `javap`: a lambda is `invokedynamic`, `::f` is a generated class, `forEach { total += it }` is a bare loop; a captured `var` loses updates across threads |
| 4 | Collection operations: `map`, `filter`, `fold`, `flatMap`, grouping | `collect(Collectors…)`; `reduce` returns `Optional` | `associateBy` silently keeps the last duplicate while `toMap` throws; `reduce` on an empty list throws |
| 5 | Sequences, laziness, and Java streams | Kotlin `List` operations are lazy like streams | `println` trace of one chain on a `List` vs a `Sequence`; `sorted()` pulls in everything |
| 6 | Null handling and scope functions | `Optional` everywhere; `return` in a lambda returns from the lambda | `cached?.let { post(it) } ?: run { … }` runs both branches; `also { it.copy(…) }` discards the copy |
| 7 | Errors as values: sealed types, `Result`, `Either` | Checked exceptions document failure | Adding a sealed case breaks every exhaustive `when`; `runCatching` swallows `CancellationException` |
| 8 | Composition, currying, partial application, recursion, `tailrec` | Recursion is elegant and `tailrec` makes it safe | `f andThen g` does not compile against the stdlib; a misplaced `tailrec` only warns and still overflows |

Four teaching principles follow from the research. **First, lead with misconceptions.** These learners already hold confident mental models shaped by Java. Each module has a demo whose output contradicts a specific belief, and students should write down their prediction before running it. **Second, stay in one domain the audience knows**, such as payments. Then "pure" means a fee calculation, "side effect" means a ledger write, and money pitfalls (`BigDecimal` scale, `Int` overflow on cents) come up naturally. **Third, make the JVM visible.** These engineers trust bytecode more than slogans, and `javap -c` settles questions such as "does this lambda allocate?" in seconds. **Fourth, teach when not to use each tool, as the sources themselves do.** The official scope-function page warns against overuse and nesting ([Kotlin docs: Scope functions](https://kotlinlang.org/docs/scope-functions.html)). The official sequence page warns that laziness adds overhead ([Kotlin docs: Sequences](https://kotlinlang.org/docs/sequences.html)). Arrow recommends plain nullable types over its own `Option` ([Arrow docs source: Nullable and Option](https://github.com/arrow-kt/arrow-website/blob/main/content/docs/learn/typed-errors/wrappers/nullable-and-option.md)).

Version pinning matters because several facts a lesson would state changed recently:
- Lambdas have compiled to `invokedynamic` by default only since Kotlin 2.0 ([What's new in Kotlin 2.0.0](https://kotlinlang.org/docs/whatsnew20.html)).
- Context parameters became stable in 2.4.0 ([Kotlin language features and proposals](https://kotlinlang.org/docs/kotlin-language-features-and-proposals.html)).
- The unused-return-value checker arrived as an experiment in 2.3.0 ([What's new in Kotlin 2.3.0](https://kotlinlang.org/docs/whatsnew23.html)).
- kotlinx.collections.immutable renamed its copy-returning methods in 0.5.0 ([kotlinx.collections.immutable CHANGELOG](https://github.com/Kotlin/kotlinx.collections.immutable/blob/master/CHANGELOG.md)).

When this report says something was observed or measured, it means the research team's own checks on the Kotlin 2.4.21 compiler and OpenJDK 21.0.12, using `javap` and JMH 1.37. These checks are reproducible but unpublished. The scope-function demos were worked out from the verified stdlib source but not executed, so run each one once before it goes on a slide. Several classic FP sources could not be retrieved during research: Hughes's paper, Gary Bernhardt's screencasts, Scott Wlaschin's railway articles and *Effective Kotlin*. This report paraphrases them, so check their exact wording before quoting them.

## Purity and immutability are signals Kotlin cannot enforce

### The double-charge refactoring teaches referential transparency in one line

A pure function's result depends only on its arguments, and calling it changes nothing outside it. That rules out I/O, writes to shared state, and hidden inputs such as `LocalDate.now()`, `Random` or a mutable global. **Referential transparency** is the practical consequence: you can replace any call with its result without changing what the program does. The one-line lesson is a refactoring every Java engineer performs without thinking. `val fee = feeFor(amount); fee + fee` and `feeFor(amount) + feeFor(amount)` are interchangeable only because `feeFor` is pure. Apply the same "extract variable" or "inline variable" step to `chargeCard(amount)`, and the customer is charged once or twice depending on how the code is written. The testing payoff follows at once. You can test `fun lateFee(invoice: Invoice, today: LocalDate): Money` with plain values and no mocks. An `applyLateFee(inv)` that reads the clock, mutates `inv.fee` and logs needs a fake clock and assertions on mutated state. Pure functions are also safe to cache, retry and run in parallel, which matters for payment retries and idempotency.

The architecture that makes purity practical is Gary Bernhardt's "functional core, imperative shell". The core has many code paths but few dependencies, and the shell has few code paths but many dependencies. The core therefore gets fast unit tests, and the shell gets a handful of integration tests ([Destroy All Software: Functional Core, Imperative Shell](https://www.destroyallsoftware.com/screencasts/catalog/functional-core-imperative-shell); [secondary summary](https://waggertron.github.io/tech-learning/topics/cs/functional-core-imperative-shell/)). In a payment service, the shell loads the account, the FX rate and `Clock.instant()`. It then calls a pure `decide(cmd: Charge, account: Account, rate: Rate, now: Instant): Decision`, which returns a value such as `Approve(ledgerEntries)` or `Reject(reason)`. Finally the shell performs the database write and the provider call. This corrects the most damaging beginner misconception, that FP means no state or I/O. The program still does I/O; only the decisions are pure.

**Kotlin cannot check any of this.** It has no `pure` modifier and no purity checker, so purity is a property of individual calls. You can only signal it: with `val` parameters, immutable value types, functions that return new values instead of `Unit`, and signatures with no `suspend` or I/O dependencies. The nearest compiler help is the unused-return-value checker. It has been experimental since Kotlin 2.3.0 and is off by default, and it warns when a non-`Unit` result is silently dropped ([What's new in Kotlin 2.3.0](https://kotlinlang.org/docs/whatsnew23.html); [Kotlin docs: Unused return value checker](https://kotlinlang.org/docs/unused-return-value-checker.html)). Pure APIs that return a modified copy instead of changing the original invite exactly that bug, so the checker is worth enabling in the course labs.

The same module should turn statements into expressions, because code built from values is where purity comes naturally. In Kotlin, `if`, `when` and `try` are expressions. A `when` used as an expression must cover every case, and when its subject is an enum or a sealed type it needs no `else` ([Kotlin docs: Conditions and loops](https://kotlinlang.org/docs/control-flow.html)). `throw` has type `Nothing`, the bottom type, which is why `person.name ?: fail("Name required")` type-checks ([Kotlin docs: Exceptions](https://kotlinlang.org/docs/exceptions.html)). The Java habit `var status; if (code == 200) status = APPROVED else if …` becomes `val status = when (code) { 200 -> APPROVED; 402 -> DECLINED; else -> ERROR }`. That version cannot be left unassigned or reassigned later. Make the subject a sealed type and the compiler rejects a missing case, which sets up the error-handling module.

### Read-only is not immutable, and copy is not deep

`val` means only that the reference is never reassigned. It compiles to a `final` field and says nothing about the object behind it, so `val payments = mutableListOf<Payment>()` happily accepts `add`. Collections are subtler. The official docs define `List` as a read-only interface paired with `MutableList`, and send readers who need real immutability to the kotlinx-collections-immutable library ([Kotlin docs: Collections overview](https://kotlinlang.org/docs/collections-overview.html)). The stdlib source shows why: `listOf(vararg)` returns `elements.asList()` ([stdlib Collections.kt](https://github.com/JetBrains/kotlin/blob/master/libraries/stdlib/src/kotlin/collections/Collections.kt)), which on the JVM is a `java.util.Arrays$ArrayList`. In the team's checks:
- `(listOf(1, 2, 3) as MutableList<Int>)[0] = 99` succeeded, and the "read-only" list printed `[99, 2, 3]`.
- `add` on the same cast list threw `UnsupportedOperationException`.
- A `List` reference to a `MutableList` changed whenever the underlying list did.

Data classes add their own trap. The docs state plainly that `copy()` "creates a shallow copy", so nested references are shared ([Kotlin docs: Data classes](https://kotlinlang.org/docs/data-classes.html)). As a result, `p1.copy(id = "p2").tags.add("refund")` also changes `p1.tags`. Payments add one more pitfall: data-class equality uses `BigDecimal.equals`, which compares scale. Two otherwise identical payments of `10.00` and `10.0` were unequal, which is a reason to normalise scale or wrap money in a value type.

**Real immutability has three layers**:
1. `val` properties.
2. Property types that are themselves immutable, such as `String`, `BigDecimal`, `Instant`, other immutable data classes and `ImmutableList`.
3. No mutable internals leaked to callers.

kotlinx.collections.immutable supplies the collection part. Its design document distinguishes two kinds of collection. Immutable collections guarantee by contract that they never change. Persistent collections have "modification" operations that return new instances, which share most of their structure with the original ([kotlinx.collections.immutable proposal](https://github.com/Kotlin/kotlinx.collections.immutable/blob/master/docs/proposal.md)).

Two caveats belong in the lesson. First, the library is at **0.5.2 and still carries an Alpha badge**, with a note that it is experimental and its API may change ([GitHub: kotlinx.collections.immutable](https://github.com/Kotlin/kotlinx.collections.immutable)). Its changelog, however, describes 0.5.0 as promoting a beta "to stable", so present it as pre-1.0. Second, **0.5.0 renamed the copy-returning methods to participles**: `add`/`remove`/`put`/`set` became `adding`/`removing`/`putting`/`replacingAt`. The rename follows the draft KEEP-0459, which names the bug it targets: calling `persistentList.add(x)` and silently discarding the result ([CHANGELOG](https://github.com/Kotlin/kotlinx.collections.immutable/blob/master/CHANGELOG.md); [KEEP-0459](https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0459-naming-conventions-for-copy-returning-operations.md)).

A good exercise is `data class Ledger(val entries: PersistentList<Entry>, val balance: Money)` with `fun Ledger.post(e: Entry) = copy(entries = entries.adding(e), balance = balance + e.amount)`. It teaches state changes that return new values, and it shows that the old ledger stays valid for audits and test assertions. Tie it back to concurrency, which these engineers already know: an object with `final` fields and no writes after construction can be shared across threads without locks.

## Function values are objects unless the compiler inlines them away

Kotlin's function types are ordinary types:
- `(A, B) -> C` takes two arguments and returns `C`, and a `Unit` return type cannot be omitted.
- A receiver type `A.(B) -> C` can be used wherever `(A, B) -> C` is expected, and vice versa.
- A nullable function type needs parentheses, as in `((Int, Int) -> Int)?`.
- The arrow is right-associative, so `(Int) -> (Int) -> Unit` is a function that returns a function.

([Kotlin docs: Higher-order functions and lambdas](https://kotlinlang.org/docs/lambdas.html))

A function value can come from a lambda, an anonymous function, a callable reference (`::isOdd`, `String::toInt`, `::Regex`, `foo::toString`), or a class that implements the type. A bound reference captures its receiver, so `jane::hasName` has type `(String) -> Boolean`, while the unbound `User::hasName` has type `(User, String) -> Boolean` ([Kotlin docs: Higher-order functions and lambdas](https://kotlinlang.org/docs/lambdas.html)). A higher-order function is simply one that takes or returns such values. The stdlib's `fold`, for example, is literally an inline `for` loop that calls `operation(accumulator, element)` ([stdlib _Collections.kt](https://github.com/JetBrains/kotlin/blob/master/libraries/stdlib/common/src/generated/_Collections.kt)). Returning functions is the first genuinely new idea for many Java engineers. A fee-rule factory makes it concrete: `fun feeRule(percent: BigDecimal, min: BigDecimal): (BigDecimal) -> BigDecimal = { amt -> (amt * percent).max(min) }`. Lambdas with receivers then explain the builder style behind `buildList { }` and HTML-style DSLs.

One difference in `return` trips up every Java engineer. A bare `return` inside a lambda is allowed only when the lambda is passed to an inline function, and it returns from the enclosing function, not from the lambda. Inside an anonymous function, `return` exits only that function ([Kotlin docs: Higher-order functions and lambdas](https://kotlinlang.org/docs/lambdas.html); [Kotlin docs: Inline functions](https://kotlinlang.org/docs/inline-functions.html)). In Java's `Stream.forEach`, `return` behaves like `continue`. In Kotlin's inline `forEach`, it exits the whole method, and `return@forEach` gives the Java-style behaviour.

Then open `javap`. Kotlin 1.5 began compiling SAM conversions with `invokedynamic` and `LambdaMetafactory` ([What's new in Kotlin 1.5.0](https://kotlinlang.org/docs/whatsnew15.html)). **Kotlin 2.0 made `invokedynamic` the default for lambdas**, with three side effects:
- These lambdas cannot be serialized.
- The experimental `reflect()` API does not support them.
- `toString()` output is less readable.

`@JvmSerializableLambda` (on one lambda) or `-Xlambdas=class` (for the whole module) brings back the old behaviour ([What's new in Kotlin 2.0.0](https://kotlinlang.org/docs/whatsnew20.html)). The team's inspection of 2.4.21 output adds detail the docs do not mention:
- Lambdas, anonymous functions and SAM conversions produce no class file.
- **Callable references (`::addFee`, `account::canPay`, `::Account`) still compile to synthetic classes extending `FunctionReferenceImpl`.**
- `String::length` is a property reference (`PropertyReference1Impl`), not a method reference.
- `suspend` lambdas compile to `SuspendLambda` classes that implement a state machine.
- A lambda that captures nothing is created once and reused, so two evaluations are `===`.
- A capturing lambda allocates a new object on every evaluation and has no structural equality.
- A call through `Function1` boxes `Int` to `Integer`.

A five-minute "predict the bytecode" quiz on these cases replaces two folk beliefs, "lambdas always allocate" and "lambdas are free", with an accurate model.

Closures deserve their own demo because they connect FP to the Java Memory Model. The docs allow a lambda to modify variables it captures ([Kotlin docs: Higher-order functions and lambdas](https://kotlinlang.org/docs/lambdas.html)). On the JVM, a captured `var` becomes a `kotlin.jvm.internal.Ref$IntRef` or `Ref$LongRef` box, whose `element` field is plain and not volatile ([stdlib Ref.java](https://github.com/JetBrains/kotlin/blob/master/libraries/stdlib/jvm/runtime/kotlin/jvm/internal/Ref.java)). In the team's test, four pool threads each ran `repeat(250_000) { total += 1 }` on a captured `var total = 0L`. One of three runs printed **778,714 instead of 1,000,000**, while a `fold` over immutable input was always correct. Lost updates appear only some of the time, so the demo should loop five to ten times.

**`inline` is what makes functional Kotlin cheap.** The docs explain that each function value is an object holding its captured variables, and that the allocations and virtual calls cost time. `inline` copies both the function and its lambda arguments into the call site. The docs say this "will pay off" especially at megamorphic call sites inside loops, meaning call sites that see many different implementations ([Kotlin docs: Inline functions](https://kotlinlang.org/docs/inline-functions.html)). Three modifiers adjust this:
- `noinline` keeps a lambda parameter as a real object that can be stored or passed on.
- `crossinline` forbids non-local returns from a lambda that is called from another context, such as another object.
- `reified` type parameters work only in inline functions.

In the team's bytecode, `xs.forEach { total += it }` contained no `invokedynamic` and no `Ref$IntRef`, and `total` stayed a local `int`. `xs.map(::addFee)` became a loop with a direct static call. The cost model to teach is short:
- A lambda that captures nothing is a single instance, created once and reused.
- A capturing lambda or a bound reference allocates on every evaluation, plus one box per captured `var`.
- Primitives are boxed when a lambda is called through the `FunctionN` interfaces.
- A lambda passed to an inline function costs nothing.

## Collection chains are eager loops, while sequences and streams are lazy pipelines

### Every eager step allocates a list, but no lambdas

Almost every `Iterable` operation is `inline` and writes into a brand-new collection. `map` is `mapTo(ArrayList<R>(collectionSizeOrDefault(10)), transform)`, and `filter` is `filterTo(ArrayList<T>(), predicate)` ([stdlib _Collections.kt @v2.4.21](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Collections.kt)). The bytecode of `ps.filter { it.status == SETTLED }.map { it.amountCents }.sum()` shows two `new ArrayList` calls, a `Long.valueOf` for each mapped element, and **no `invokedynamic` or `Function1` anywhere**. That reframes the performance conversation. On lists, functional style does not allocate lambdas. It allocates an intermediate collection per step, and it boxes primitives that are collected into a `List<Long>`.

The operations themselves are easy. The edge cases are where engineers get burned, so teach them in contrast with Java:
- `flatMap` is `map` followed by `flatten` ([Kotlin docs: Collection transformations](https://kotlinlang.org/docs/collection-transformations.html)).
- `fold` takes an initial value, while `reduce` starts from the first element ([Kotlin docs: Aggregate operations](https://kotlinlang.org/docs/collection-aggregate.html)).
- So **`reduce` on an empty collection throws `UnsupportedOperationException("Empty collection can't be reduced.")`**, and its accumulator type must be a supertype of the element type ([stdlib _Collections.kt @v2.4.21](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Collections.kt)). On an empty input, Java's `Stream.reduce` returns `Optional.empty` instead.
- The docs' own cautionary example, `reduce { sum, e -> sum + e * 2 }`, never doubles the first element and returns 37 instead of 42 ([Kotlin docs: Aggregate operations](https://kotlinlang.org/docs/collection-aggregate.html)).
- `first()` and `maxOf {}` throw `NoSuchElementException` on empty input. `firstOrNull()`, `maxOrNull()` and `reduceOrNull()` return `null`.

The rule to teach: when input can legitimately be empty, use `fold`, `sumOf`, `count` or `maxByOrNull`. Use `reduce` only when an empty input is a bug you want to surface loudly.

Map-building functions differ from Java in ways that matter for payments:
- **Key order.** `groupBy` keeps keys in first-seen order ([stdlib _Collections.kt @v2.4.21](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Collections.kt)), and returned a `LinkedHashMap` in the team's run. `Collectors.groupingBy` guarantees neither the map type nor its order ([OpenJDK Collectors.java](https://raw.githubusercontent.com/openjdk/jdk21u/master/src/java.base/share/classes/java/util/stream/Collectors.java)), and on JDK 21 it returned a hash-ordered `HashMap`.
- **One-pass aggregation.** `groupingBy { }` returns a lazy `Grouping`. Its `eachCount()`, `fold()` and `aggregate()` make a single pass and keep one accumulator per key, without building a list per group ([Kotlin docs: Grouping](https://kotlinlang.org/docs/collection-grouping.html); [stdlib Grouping.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/src/kotlin/collections/Grouping.kt)).
- **Duplicate keys.** Most dangerously, **`associateBy` keeps the last value on duplicate keys without any warning** ([Kotlin docs: Collection transformations](https://kotlinlang.org/docs/collection-transformations.html)), while Java's `Collectors.toMap` throws `IllegalStateException` ([OpenJDK Collectors.java](https://raw.githubusercontent.com/openjdk/jdk21u/master/src/java.base/share/classes/java/util/stream/Collectors.java)). For payments keyed by idempotency key or external ID, that silent overwrite loses data. `groupingBy { it.key }.eachCount().filterValues { it > 1 }` finds duplicates first.

Smaller traps round out the lesson ([Kotlin docs: Retrieve collection parts](https://kotlinlang.org/docs/collection-parts.html)):
- `zip` truncates to the shorter input.
- `distinctBy` keeps the first element for each key.
- `sortedBy` is stable, so elements with equal keys keep their order.
- `takeWhile` stops at the first element that fails the predicate. It does not filter the rest.

`runningFold` and `scan` produce running balances, and `chunked`, `windowed` and `zipWithNext` cover payout batching and moving averages.

The most valuable exercise in this module is rewriting:

| Instead of | Write | Why |
|---|---|---|
| `filter { p }.count()` | `count { p }` | No intermediate list |
| `filter { p }.first()` | `first { p }` | Stops early, no list |
| `map { f }.filterNotNull()` | `mapNotNull { f }` | One list instead of two |
| `fold(0L) { a, p -> a + p.amount }` | `sumOf { it.amount }` | Says what it means |
| `groupBy { k }.mapValues { it.value.size }` | `groupingBy { k }.eachCount()` | No list per group |
| `associate { it.id to it }` | `associateBy { it.id }` | No `Pair` objects; the docs warn `associate` creates short-lived ones |
| `sortedBy { it.x }.first()` | `minByOrNull { it.x }` | O(n), and safe on empty input |

Engineers converting nested loops also need to hear that `payments.flatMap { p -> refunds.filter { it.paymentId == p.id }.map { p to it } }` is exactly as O(n·m) as the loop it replaced. Indexing once with `associateBy` and then calling `mapNotNull` is O(n+m). A `forEach` that pushes into `good` and `bad` lists or increments a counter should become `partition`, `groupingBy { }.fold()` or `sumOf`.

### Laziness wins by four orders of magnitude only when work can stop early

The official definitions are crisp. An `Iterable` chain finishes each step for the whole collection before starting the next. A `Sequence` runs one element through all the steps before pulling the next element, and does nothing until a terminal operation asks for results ([Kotlin docs: Sequences](https://kotlinlang.org/docs/sequences.html)). The docs' own demo filters words longer than three letters, maps them to their lengths, and takes four. Run eagerly, it makes 9 filter calls and 5 map calls; run lazily, 6 and 4 ([Kotlin docs: Sequences](https://kotlinlang.org/docs/sequences.html)). The team ran `filter → map → take(2)` over five payments with `println` in each lambda. The list printed all five filter calls before any map call. The sequence printed nothing until `toList()`, and never touched payments four and five. Students should predict both traces before running them.

The mechanism explains the costs:
- **Wrapper objects.** Sequence intermediate operations are ordinary, non-inline functions. Each one wraps the previous stage in an object such as `TransformingSequence` or `FilteringSequence` ([stdlib _Sequences.kt @v2.4.21](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Sequences.kt); [stdlib Sequences.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/src/kotlin/collections/Sequences.kt)). So each lambda becomes a real `Function1` object, and primitives are boxed when they pass through it.
- **Stateful steps are barriers.** On first iteration, `Sequence.sorted()` copies every element from the earlier stages into a list ([stdlib _Sequences.kt @v2.4.21](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Sequences.kt)). So `asSequence().onEach { log }.sortedBy { it.amountCents }.first()` logs every element before returning.
- **Reuse.** Most sequences can be iterated again, but each iteration recomputes the whole pipeline, side effects included. A `generateSequence` without a seed, or one made by `iterator().asSequence()`, can be iterated only once. A second pass throws `IllegalStateException: This sequence can be consumed only once.` ([stdlib Sequences.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/src/kotlin/collections/Sequences.kt)).

The sequence builders are where sequences shine in backend code. `generateSequence(100L) { (it * 2).takeIf { d -> d <= 1_600 } }` is a retry-backoff schedule. `sequence { for (page in 1..n) yieldAll(fetch(page)) }` is built on a restricted suspend lambda that pauses at each `yield` ([stdlib SequenceBuilder.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/src/kotlin/collections/SequenceBuilder.kt)). In the team's run it fetched only the pages that a `.first { }` needed.

The team's JMH run (Kotlin 2.4.21, OpenJDK 21 with the C2 compiler, 1 GB heap) gives the course real numbers. It ran on a heavily loaded four-vCPU VM, so treat the timings as order-of-magnitude only. Bytes allocated per call do not depend on load and are the reliable signal.

| Variant, 1,000,000 payments | Time per call | Allocated per call |
|---|---|---|
| Hand-written `for` loop | 5.2 ms | ≈0 B |
| `filter{}.map{}.sum()` on `List` | 148 ms | 26.5 MB |
| Fused `sumOf { if (settled) amount else 0L }` | 2.6 ms | ≈0 B |
| `asSequence().filter{}.map{}.sum()` | 9.0 ms | 189 B |
| `stream().filter{}.mapToLong{}.sum()` | 8.9 ms | 428 B |
| `stream().filter{}.map{}.reduce(0L){…}` (boxed) | 14 ms | 28.8 MB |
| Short-circuit `firstOrNull` (match at index 101) on `List` | 4.4 ms | 243 KB |
| Short-circuit `firstOrNull` on `Sequence` | 141 ns | ≈0 B |
| Short-circuit `findFirst` on `Stream` | 981 ns | 320 B |

Three lessons come out of the table, and the third matters most:
1. Laziness pays off hugely, by about 30,000× here, when the terminal operation can stop early (`first`, `any`, `take`).
2. For a full pass over the data, laziness is a moderate win at large sizes.
3. **The fastest idiomatic option was neither a list chain nor a sequence, but a single fused inline call.** It compiles to the hand-written loop.

The folklore that sequences are slower on small collections did not reproduce for this pipeline: 39 ns for the sequence versus 156 ns for the list at n=10. The docs themselves say only that the overhead "may be significant" ([Kotlin docs: Sequences](https://kotlinlang.org/docs/sequences.html)). The sequence's near-zero allocation also depended on the JIT's escape analysis in a simple benchmark where each call site saw only one lambda, so do not promise it in general.

JetBrains' tooling encodes a similar rule of thumb. IntelliJ's K2 inspection suggests `asSequence()` for collection call chains of five or more calls by default, as a weak warning ([IntelliJ inspection source](https://raw.githubusercontent.com/JetBrains/intellij-community/master/plugins/kotlin/code-insight/inspections-k2/src/org/jetbrains/kotlin/idea/codeInsight/inspections/collections/ConvertCallChainIntoSequenceInspection.kt)). The practical rule:
- Default to `Iterable` operations.
- Fuse steps when a purpose-built function such as `sumOf` exists.
- Reach for `asSequence()` when the terminal operation can stop early, or for long chains over large inputs.
- Use `sequence { }` or `generateSequence` for paging, retries and other data that is produced lazily.

### Java streams share the laziness but not the contract

Java engineers will map sequences onto streams, and the mapping is half right. The `java.util.stream` package docs describe streams as having no storage, "laziness-seeking", possibly unbounded, and "consumable", meaning their elements are visited only once ([OpenJDK stream package-info](https://raw.githubusercontent.com/openjdk/jdk21u/master/src/java.base/share/classes/java/util/stream/package-info.java)). In the team's checks, the same `filter → map → limit` trace printed in the same element-by-element order as a Kotlin sequence, and `sorted()` buffered everything just as it does in Kotlin. The differences are in the contract:
- **Single use.** A stream may be operated on only once ([OpenJDK Stream.java](https://raw.githubusercontent.com/openjdk/jdk21u/master/src/java.base/share/classes/java/util/stream/Stream.java)). A second `count()` threw `IllegalStateException: stream has already been operated upon or closed`.
- **Parallelism.** Streams can go parallel with `parallel()` or `parallelStream()`. The Javadoc itself flags `forEach(s -> results.add(s))` as an "Unnecessary use of side-effects!" that breaks under parallelism ([OpenJDK stream package-info](https://raw.githubusercontent.com/openjdk/jdk21u/master/src/java.base/share/classes/java/util/stream/package-info.java)). Kotlin's sequence API has no parallel mode at all. Sequences are part of the stdlib code shared by every platform, though, so they work on every Kotlin target ([stdlib _Sequences.kt @v2.4.21](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Sequences.kt)).
- **Primitives.** Streams have `IntStream`, `LongStream` and `DoubleStream`. The boxing difference is stark in the table above: 28.8 MB per call for a boxed `reduce`, versus 0.4 KB for `mapToLong().sum()`. Kotlin has no `LongSequence`; its answer is `LongArray` or a fused `sumOf`.
- **Terminal operations.** Streams end in `collect(Collectors…)`, whose results come with "no guarantees on the type, mutability, serializability, or thread-safety" ([OpenJDK Collectors.java](https://raw.githubusercontent.com/openjdk/jdk21u/master/src/java.base/share/classes/java/util/stream/Collectors.java)). Kotlin offers direct terminal functions with documented ordering.

Two interop details catch people out. First, `Stream.toList()` (JDK 16+) returns an unmodifiable list ([OpenJDK Stream.java](https://raw.githubusercontent.com/openjdk/jdk21u/master/src/java.base/share/classes/java/util/stream/Stream.java)). In Kotlin code, that JDK method takes precedence over Kotlin's own `Stream<T>.toList()` extension, so the result is not a mutable `ArrayList`. Second, conversion is one call each way, `asSequence()` and `asStream()` ([stdlib Streams.kt](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/jdk8/src/kotlin/streams/Streams.kt)). Finally, JDK 24 added `Gatherers`, with `windowFixed`, `windowSliding`, `fold`, `scan` and `mapConcurrent` ([OpenJDK 25 Gatherers.java](https://raw.githubusercontent.com/openjdk/jdk25u/master/src/java.base/share/classes/java/util/stream/Gatherers.java)). They close a gap: JDK 21 streams had nothing like Kotlin's `chunked`, `windowed` or `runningFold`.

| Concern | Kotlin `Iterable` operations | Kotlin `Sequence` | Java `Stream` |
|---|---|---|---|
| Evaluation | Eager; a new collection per step | Lazy; one element through all steps | Lazy; one element through all steps |
| Reuse | Always | Usually, but recomputes; some are once-only | Never; second use throws |
| Parallelism | None | None | `parallel()`, `parallelStream()` |
| Primitives | Boxed in `List<Long>`; use `LongArray` or `sumOf` | Boxed only | `IntStream`, `LongStream`, `DoubleStream` |
| Terminal API | Direct: `groupBy`, `associateBy`, `partition`, `sumOf` | Same names | `collect(Collectors…)`, `toList()`; `reduce` returns `Optional` |
| Duplicate map keys | Last value wins silently | Last value wins silently | `toMap` throws |
| Map ordering | `LinkedHashMap`, first-seen order | Same | No guarantee |
| Windowing and scans | `chunked`, `windowed`, `runningFold` | Same, lazily | JDK 24+ `Gatherers` only |
| Lambda cost | Inlined; no lambda objects | One object per stage | One object per stage |
| Platforms | All Kotlin targets | All Kotlin targets | JVM only |

The official Java-to-Kotlin guide maps the idioms. `Collectors.groupingBy(f, counting())` becomes `groupingBy(f).eachCount()`, and `IntStream.iterate(1, e -> e + 3).limit(10).sum()` becomes `generateSequence(1) { it + 3 }.take(10).sum()`. But the guide never says when to prefer a sequence over a stream ([Kotlin docs: Collections in Java and Kotlin](https://kotlinlang.org/docs/java-to-kotlin-collections-guide.html)). The defensible course answer: reach for Java streams only when a task needs parallelism, a `Gatherer`, primitive streams at scale, or a Java API that already returns a `Stream`.

## Nullable types and scope functions are where idioms turn into bugs

### `T?` already is Kotlin's Optional

Teach null handling before scope functions, because the safe-call operator `?.` is what turns `let` into a null check. Kotlin's nullable type is checked at compile time and is not a wrapper object: "A nullable type isn't a wrapper for a non-nullable type. All checks are performed at compile time." As a result, there is "almost no runtime overhead" ([Kotlin docs: Nullability in Java and Kotlin](https://kotlinlang.org/docs/java-to-kotlin-nullability-guide.html)). The null operators form a small functional toolkit ([Kotlin docs: Null safety](https://kotlinlang.org/docs/null-safety.html); [stdlib _Collections.kt @v2.4.21](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/common/src/generated/_Collections.kt)):
- `?.` returns `null` instead of throwing. If any link in a chain is `null`, the rest is skipped, even the right-hand side of an assignment.
- `?:` evaluates its right side only when the left is `null`. Because `return` and `throw` are expressions, it doubles as a guard clause, as in `val parent = node.getParent() ?: return null`.
- `as?` is a safe cast that returns `null` instead of throwing.
- `filterNotNull()`, `mapNotNull {}` and `firstNotNullOfOrNull {}` bring the same handling to collections.

Java engineers learn fastest from a translation table.

| Java `Optional` | Kotlin nullable equivalent |
|---|---|
| `opt.map(f)` | `x?.let(f)` or `x?.f()` |
| `opt.flatMap(f)` | `x?.let(f)` where `f` returns `T?` (nullability flattens automatically) |
| `opt.filter(p)` | `x?.takeIf(p)` |
| `opt.orElse(d)` | `x ?: d` |
| `opt.orElseGet { … }` | `x ?: run { … }` (also lazy) |
| `opt.orElseThrow()` | `x ?: throw …` or `requireNotNull(x) { … }` |
| `opt.ifPresent(c)` | `x?.let(c)` or `x?.also(c)` |

After an `if (x != null)` check, the compiler smart-casts `x` to its non-null type, but only when it can prove the value has not changed in between ([Kotlin docs: Type checks and casts](https://kotlinlang.org/docs/typecasts.html)):

| Variable kind | Smart cast after a null check |
|---|---|
| Local `val` | Always |
| `val` property | Only if private, internal or checked in the same module, and not open and without a custom getter |
| Local `var` | Only if not modified between check and use, and not captured by a lambda that modifies it |
| `var` property | **Never** |

The last row explains when `?.let` is legitimate. `if (pendingRefund != null) send(pendingRefund)` does not compile for a `var` property, so the fix is `pendingRefund?.let(::send)` or `val r = pendingRefund ?: return`.

For validation, use `requireNotNull` and `checkNotNull` rather than `!!`:
- `requireNotNull` throws `IllegalArgumentException`, and `checkNotNull` throws `IllegalStateException`.
- Both declare a contract `returns() implies (value != null)`, so the argument is smart-cast to non-null afterwards ([stdlib Preconditions.kt](https://github.com/JetBrains/kotlin/blob/v2.4.21/libraries/stdlib/src/kotlin/util/Preconditions.kt)).
- They carry a message and the right exception type, which `!!` does not.
- Detekt's default rules push `require(x != null)` toward them ([detekt UseRequireNotNull](https://github.com/detekt/detekt/blob/main/detekt-rules-standard-library/src/main/kotlin/dev/detekt/rules/standardlibrary/UseRequireNotNull.kt)).

Arrow, the main FP library, tells readers to "prefer working with nullable types over Option as it is more idiomatic". It reserves `Option` for two cases. The first is nested nullability in generic code: `firstOrNull()` cannot distinguish an empty list from one whose first element is `null`. The second is libraries such as Reactor or RxJava that reject nulls ([Arrow docs source: Nullable and Option](https://github.com/arrow-kt/arrow-website/blob/main/content/docs/learn/typed-errors/wrappers/nullable-and-option.md)). The course should therefore not present `Optional` or `Option` as the "functional" way to express absence in Kotlin.

### Two questions choose the scope function, and one Elvis breaks it

The stdlib source demystifies scope functions immediately. `let`, `run` (both forms), `with`, `apply` and `also` are one-line `inline` functions. Each declares a contract, `callsInPlace(block, InvocationKind.EXACTLY_ONCE)`, which promises the compiler that the block runs exactly once ([stdlib Standard.kt @v2.4.21](https://github.com/JetBrains/kotlin/blob/v2.4.21/libraries/stdlib/src/kotlin/util/Standard.kt)). Inlining means they cost nothing at runtime. The contract lets the compiler accept a `val` that is assigned inside the block, as in `val authCode: String; gatewayAuthorize(req).also { authCode = it.code }`. The stdlib's own contract samples show exactly this kind of `val` initialisation ([stdlib contracts samples](https://github.com/JetBrains/kotlin/blob/v2.4.21/libraries/stdlib/samples/test/samples/contracts/contracts.kt)). The official docs reduce the choice to two differences: how the block refers to the object, and what the call returns ([Kotlin docs: Scope functions](https://kotlinlang.org/docs/scope-functions.html)).

| | Returns the lambda result | Returns the context object |
|---|---|---|
| Object is `this` (receiver) | `run`, `with` | `apply` |
| Object is `it` (argument) | `let` | `also` |
| No object | non-extension `run` | — |

The docs' short guide assigns an intent to each function:
- `let`: run a block on non-null objects, or introduce a local variable.
- `apply`: configure an object.
- `run`: configure an object and compute a result.
- Non-extension `run`: run statements where an expression is required.
- `also`: perform additional effects.
- `with`: group calls on an object.

The docs also warn: "avoid nesting scope functions and be careful when chaining them because it's easy to get confused about the current context object and value of `this` or `it`" ([Kotlin docs: Scope functions](https://kotlinlang.org/docs/scope-functions.html)). That page is effectively the only official guidance. The Kotlin coding conventions simply link to it ([Kotlin docs: Coding conventions](https://kotlinlang.org/docs/coding-conventions.html)), and the Android Kotlin style guide does not mention scope functions at all ([Android Kotlin style guide](https://developer.android.com/kotlin/style-guide)). The framing that sticks is that the choice of function is a message to the reader. `apply` says "only configuring", `also` says "side step; the value flows through unchanged", and `let` says "transform into something else". `with` takes its object as an ordinary parameter, so it has no safe-call form and is the wrong choice for nullable values.

Four anti-patterns deserve explicit demos, and each follows directly from the signatures.

**1. `?.let { A } ?: run { B }` is not an if/else.** B also runs whenever A evaluates to `null`, because the Elvis operator tests the result of the `let` block, not the original value ([Kotlin docs: Null safety](https://kotlinlang.org/docs/null-safety.html); [Kotlin docs: Scope functions](https://kotlinlang.org/docs/scope-functions.html)). No official page names this pattern, but the payments version is easy to stage:

```kotlin
// post() returns null when the payment was already posted
fun settle(cached: Payment?, ledger: Ledger, fetch: () -> Payment): String? =
    cached?.let { ledger.post(it) } ?: run { log("cache miss"); ledger.post(fetch()) }
// Second call with the same cached payment: post() returns null, so the
// "cache miss" branch also runs and attempts a second posting.
```

The fix is an `if` or `when`, or `?.also { }` when the non-null branch is only a side effect.

**2. `apply` and `also` discard the block's value.** Their blocks return `Unit`, so a value computed on the last line is thrown away. `payment.also { it.copy(status = CAPTURED) }` returns the original, uncaptured payment, and `list.apply { sumOf { … } }` returns the list. An explicit type such as `val total: Long` catches the second case.

**3. Nested receivers resolve names to the innermost object.** An unqualified name binds to the innermost receiver that has it, so in `form.apply { fx.apply { amount = 500 } }` the assignment targets `fx`. If a later refactor deletes `Fx.amount`, the same line silently writes `form.amount` instead. A labelled `this@label` can make the target explicit ([Kotlin docs: This expressions](https://kotlinlang.org/docs/this-expressions.html)), but the better rule is not to nest, which detekt's `NestedScopeFunctions` rule enforces ([detekt NestedScopeFunctions](https://github.com/detekt/detekt/blob/main/detekt-rules-standard-library/src/main/kotlin/dev/detekt/rules/standardlibrary/NestedScopeFunctions.kt)).

**4. A bare `return` exits the enclosing function.** The lambdas are inline and none is marked `crossinline`, so a bare `return` inside `let` exits the enclosing function ([Kotlin docs: Inline functions](https://kotlinlang.org/docs/inline-functions.html)). The conventions advise against several labelled returns in one lambda, and against a labelled return on a lambda's last line ([Kotlin docs: Coding conventions](https://kotlinlang.org/docs/coding-conventions.html)). So a guard before the block, such as `val token = card?.token ?: return Declined("no token")`, usually reads better than `return@let` inside it.

Tooling can carry part of this load, but not by default. In detekt 1.23.8, the current stable release, `UnnecessaryLet`, `NestedScopeFunctions`, `AlsoCouldBeApply` and `UseLet` are opt-in, while `UnnecessaryApply` is active by default ([detekt UnnecessaryLet](https://github.com/detekt/detekt/blob/v1.23.8/detekt-rules-style/src/main/kotlin/io/gitlab/arturbosch/detekt/rules/style/UnnecessaryLet.kt); [detekt UnnecessaryApply](https://github.com/detekt/detekt/blob/v1.23.8/detekt-rules-style/src/main/kotlin/io/gitlab/arturbosch/detekt/rules/style/UnnecessaryApply.kt)). Two of them pull in opposite directions. `UseLet` pushes `if (x != null) f(x) else null` toward `x?.let { f(it) }` ([detekt UseLet](https://github.com/detekt/detekt/blob/main/detekt-rules-standard-library/src/main/kotlin/dev/detekt/rules/standardlibrary/UseLet.kt)), while `UnnecessaryLet` pushes trivial `let`s back toward plain calls. A rule that reconciles them: use `?.let` when the non-null value flows into an expression, and use `if` with a smart cast for control flow or multi-statement branches.

The decision then reduces to a short checklist:
1. Would a plain call, a safe call, a smart-cast `if` or a `?: return` be clearer than any scope function?
2. What should the expression evaluate to: the same object, or a new value?
3. Does the block mainly work on the object's members (`this`), or pass the object to other functions (`it`)?
4. Is the value nullable? Use only the extension forms (`?.let`, `?.run`, `?.also`, `?.apply`), and check that no `?:` follows a block that can return `null`.
5. Does the block nest, run past about five lines, or chain more than twice? Extract a function.

One version-sensitive detail deserves a footnote. Since Kotlin 2.3.0, the scope functions carry `@IgnorableReturnValue`, so the experimental unused-return-value checker does not report a discarded `let` result. On the stdlib's `master` branch, however, `let`, `run` and `with` have switched to `returnsResultOf`, an experimental contract added in 2.4.0. It lets the checker report a discarded result when the block's own value matters ([stdlib Standard.kt @master](https://github.com/JetBrains/kotlin/blob/master/libraries/stdlib/src/kotlin/util/Standard.kt); [What's new in Kotlin 2.4.0](https://kotlinlang.org/docs/whatsnew24.html)). It is not yet known which release will ship that change.

## Sealed types carry domain errors, while kotlin.Result stays at the edges

### Exhaustive `when` replaces the `throws` clause

The case for errors as values is stronger in Kotlin than in Java, because Kotlin removed checked exceptions. "Kotlin treats all exceptions as unchecked by default," and `@Throws` exists only to inform Java, Swift and Objective-C callers ([Kotlin docs: Exceptions](https://kotlinlang.org/docs/exceptions.html)). Nothing in a `charge()` signature tells the caller it can fail. The Kotlin team's own design notes draw the line the course should teach. The design document for `Result` says "Use nullable types or domain-specific classes to represent failures that need specific handling," and illustrates it with a sealed `FindUserResult` of `Found`, `NotFound` and `MalformedName` ([KEEP: Result](https://github.com/Kotlin/KEEP/blob/master/proposals/stdlib/result.md)). The 2025–26 rich-errors proposal asks whether exceptions are going away and answers "Definitely not", keeping them mainly "for unrecoverable errors and non-local handling" ([KEEP-0441](https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0441-rich-errors-motivation.md)). Arrow agrees. It separates logical failures, such as "user not found", from truly exceptional ones, such as a dropped database connection ([Arrow docs source: Working with typed errors](https://raw.githubusercontent.com/arrow-kt/arrow-website/main/content/docs/learn/typed-errors/working-with-typed-errors.md)). The rule:
- Expected failures that the caller can act on become values.
- Broken invariants use `require`, `check` or `error`.
- Infrastructure failures stay exceptions caught at the edge, or become values at an adapter if the domain has a meaningful response to them.

Sealed interfaces are how plain Kotlin expresses this. All direct subtypes are known at compile time and must live in the same module and package. As a result, the compiler can check a `when` expression over them for exhaustiveness, with no `else` needed ([Kotlin docs: Sealed classes and interfaces](https://kotlinlang.org/docs/sealed-classes.html)). When the team added `FraudSuspected` to a `PaymentError` hierarchy, Kotlin 2.4.21 rejected the existing `when` with: "'when' expression must be exhaustive. Add the 'is FraudSuspected' branch or an 'else' branch." This is the Kotlin equivalent of a new checked exception breaking every caller, except that the error appears where the failure is handled rather than in the signature. Two habits make the safety net hold:
- No `else` branch on sealed subjects, because `else` silently absorbs new cases.
- `data object` for cases with no data, so equality and `toString` behave sensibly.

Before introducing a library, students should write the "railway" by hand. It takes ten lines:

```kotlin
sealed interface Outcome<out E, out A> {
    data class Ok<A>(val value: A) : Outcome<Nothing, A>
    data class Err<E>(val error: E) : Outcome<E, Nothing>
}
inline fun <E, A, B> Outcome<E, A>.map(f: (A) -> B): Outcome<E, B> =
    when (this) { is Outcome.Ok -> Outcome.Ok(f(value)); is Outcome.Err -> this }
inline fun <E, A, B> Outcome<E, A>.andThen(f: (A) -> Outcome<E, B>): Outcome<E, B> =
    when (this) { is Outcome.Ok -> f(value); is Outcome.Err -> this }
```

With it, `validate(r).andThen(::authorise).andThen(::capture).map { it.uppercase() }` returned `Ok`, `Err(Invalid)` or `Err(Declined)` as expected. This is Scott Wlaschin's "railway-oriented programming", in which each step is either on a success track or a failure track. `andThen` is his `bind`, and `map` adapts an ordinary function to work on both tracks ([Wlaschin: Railway Oriented Programming](https://fsharpforfunandprofit.com/rop/)). The `out` variance plus `Nothing` is what lets `Err` pass through unchanged. That is a good moment to explain variance to engineers who have only seen Java's `? extends`.

### runCatching lets a cancelled coroutine keep charging

`kotlin.Result` looks like Kotlin's `Either`, and it is not. It is a value class whose failure side is always a `Throwable`, created mainly for `Continuation.resumeWith`. Its design document says outright that it "is not designed to represent domain-specific error conditions" ([KEEP: Result](https://github.com/Kotlin/KEEP/blob/master/proposals/stdlib/result.md)). KEEP-0441 adds that it is "not a sealed class" and has a single type parameter, so the error type cannot be expressed ([KEEP-0441](https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0441-rich-errors-motivation.md)). The old ban on returning `Result` from a function was lifted in Kotlin 1.5 ([KEEP: Result](https://github.com/Kotlin/KEEP/blob/master/proposals/stdlib/result.md)), so that is no longer a reason to avoid it.

The real reason is `runCatching`, which catches "any `Throwable`" ([Kotlin API: runCatching](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/run-catching.html)). The team's demo showed what that means in coroutine code:
- A coroutine wrapped `delay(1_000)` in `runCatching` and was cancelled after 50 ms. It got a failure holding `JobCancellationException`.
- It then **printed "charging card anyway"**, because code that does not suspend kept running until the next suspension point.
- A `withTimeout` failure looked like any ordinary failure.
- `OutOfMemoryError` and `StackOverflowError` were caught too.

A request for a version of `runCatching` that does not swallow cancellation has been open in kotlinx.coroutines since 18 February 2020 ([kotlinx.coroutines #1814](https://github.com/Kotlin/kotlinx.coroutines/issues/1814)). Two more traps belong in the lesson. `Result.map` rethrows an exception thrown by its lambda; only `mapCatching` captures it. And the fix has limits: a short wrapper, `runCatching(block).onFailure { if (it is CancellationException) throw it }`, fixed the leak in the demo, but it still swallows JVM `Error`s. Teach `Result` as a typed `try`/`catch` for foreign code at adapter boundaries, and for collecting per-item outcomes of parallel work. Never use it as a domain return type.

### Arrow 2.3 adds accumulation, while native error unions remain a design

Arrow is the library to introduce once the hand-written railway makes sense. Its current release is **2.3.0, published 26 October 2026**. The next day brought 2.3.0.1, an emergency compatibility release for IntelliJ 2026.3, and Arrow's alpha releases had already moved to Kotlin 2.4.21 ([Maven Central: arrow-core](https://repo1.maven.org/maven2/io/arrow-kt/arrow-core/maven-metadata.xml); [GitHub: Arrow releases](https://github.com/arrow-kt/arrow/releases)). Arrow pairs a value type, `Either<E, A>`, with a context, `Raise<E>`, in which failures can be raised. Inside `either { }` ([Arrow docs source: Working with typed errors](https://raw.githubusercontent.com/arrow-kt/arrow-website/main/content/docs/learn/typed-errors/working-with-typed-errors.md)):
- `ensure(cond) { error }` works like `require`, but raises a typed error.
- `ensureNotNull` raises on null and smart-casts the value otherwise.
- `.bind()` unwraps another `Either`, or stops at its error.
- `recover` handles logical failures.
- `catch` turns foreign exceptions into values while "automatically" letting fatal exceptions and `CancellationException` through.

In the team's run, `Either.catch` rethrew `OutOfMemoryError` and `CancellationException` but returned `Left` for an `IllegalStateException`, which is exactly the behaviour `runCatching` lacks. Kotlin 2.4 makes Arrow more natural to use. Context parameters have been stable since 2.4.0 ([Kotlin language features and proposals](https://kotlinlang.org/docs/kotlin-language-features-and-proposals.html)), and Arrow 2.3.0 ships a matching `arrow.core.raise.context` package. In the team's test, `context(_: Raise<PayErr>) fun checkCurrency(c: String): String` compiled without any compiler flag, even though Arrow's documentation still describes context parameters as a future feature.

What Arrow adds beyond a hand-written `Outcome` is **error accumulation**, and it maps cleanly onto request validation. `either { }` stops at the first failure and "only returns one error, even if there were two problems". `zipOrAccumulate` runs independent validations, and `mapOrAccumulate` validates every element of a collection; both return `Either<NonEmptyList<E>, A>` ([Arrow docs source: Validation](https://raw.githubusercontent.com/arrow-kt/arrow-website/main/content/docs/learn/typed-errors/validation.md)). On the same bad input (amount −5, currency "XYZ"), the stop-at-first version returned only `InvalidAmount`, while `zipOrAccumulate` returned both errors. The newer `accumulate { ensureOrAccumulate(…) }` style still requires `@OptIn(ExperimentalRaiseAccumulateApi::class)` in 2.3.0.

The resulting architecture is the course capstone:
1. Accumulate errors during request validation, so the client sees every problem at once.
2. Run authorise → risk-check → capture → ledger as a pipeline that stops at the first failure.
3. At the adapters, convert only infrastructure failures that have a domain meaning, such as a provider `SocketTimeoutException` becoming a retryable `ProviderUnavailable`, and let everything else propagate.
4. Map the sealed error type to HTTP statuses in one exhaustive `when` at the edge.

Neither JetBrains nor Arrow publishes guidance specific to payments, so present this as a synthesis of the sources above.

Students will ask about the language-level future, and the honest answer is that it is not here yet. KEEP-0441 proposes "rich errors" ([KEEP-0441](https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0441-rich-errors-motivation.md)):
- an `error` soft keyword for declaring error types;
- unions written with `|`, such as `fun load(): User | NotFound`;
- `?.` that propagates errors, while Elvis does not work on error unions;
- error types that cannot be generic or have supertypes.

That last restriction means `Result` could map onto the design but `Either` could not. The proposal's status is "Design review". The official feature table lists it as "Exploration and design", with no target version ([Kotlin language features and proposals](https://kotlinlang.org/docs/kotlin-language-features-and-proposals.html)). The discussion of the detailed design, KEEP-0462, opened on 20 May 2026. There, co-author Michail Zarečenskij wrote "we're not rushing with the feature" ([KEEP discussion #487](https://github.com/Kotlin/KEEP/discussions/487)). Kotlin 2.4.21 rejects the syntax with a syntax error, and the compiler has no flag to enable it. Show it as a preview only. Note also that a sealed `PaymentError` hierarchy would not translate one-to-one, because error types could not share a supertype.

## Composition, currying and tailrec are power tools, not daily habits

Function composition is the purest form of FP's "glue", and Kotlin's standard library does not include it. Kotlin 2.4.21 has no `compose`, `andThen` or `curried`, and `f andThen g` fails with "unresolved reference 'andThen'". That makes it a good exercise rather than a gap, because each extension takes one line:

```kotlin
infix fun <A, B, C> ((A) -> B).andThen(g: (B) -> C): (A) -> C = { a -> g(this(a)) }
fun <A, B, C> ((A, B) -> C).curried(): (A) -> (B) -> C = { a -> { b -> this(a, b) } }
val price = addVat andThen applyDiscount andThen roundToCents
```

Arrow provides the full set in a separate module, `arrow-functions` (2.3.0), not in `arrow-core`. It includes `curried` overloads for up to 22 parameters (matching `Function22`), `partially1`, and memoisation ([Maven Central: arrow-functions](https://repo1.maven.org/maven2/io/arrow-kt/arrow-functions/maven-metadata.xml)). Composition earns its place in three situations:
- Configurable pipelines of steps with the same shape, for example `steps.fold({ it }) { acc, f -> acc andThen f }` over a `List<(Payment) -> Payment>`.
- Decorators, such as retry-then-log.
- Building specialised functions once at startup, such as one fee function per merchant tier.

Currying rarely earns its place in backend code. Kotlin already covers partial application more readably than `fee.curried()(tier)` does, with:
- named and default arguments ([Kotlin docs: Functions](https://kotlinlang.org/docs/functions.html));
- bound references such as `merchant::feeFor`;
- a one-line lambda such as `{ amount -> fee(tier, amount) }`.

Curried signatures also clutter IDE hints, appear as `$$Lambda` frames in stack traces, and allocate a closure for each argument applied. Teach currying so engineers recognise it, and make extension-function chains such as `amount.withVat().roundedToCents()` the default.

Recursion needs the same calibration. The JVM does not eliminate tail calls in general. Kotlin's `tailrec` makes the compiler rewrite a function whose final operation is a call to itself into a loop. It cannot do this when more code follows the call, when the call is inside `try`/`catch`/`finally`, or when the function is open ([Kotlin docs: Functions](https://kotlinlang.org/docs/functions.html)). The language specification requires only a **warning** when `tailrec` cannot be applied ([Kotlin spec: Declarations](https://kotlinlang.org/spec/declarations.html)), so such code compiles to ordinary recursion and can still overflow the stack. The `javap` demo settles it:
- `tailrec fun gcd(a: Long, b: Long): Long = if (b == 0L) a else gcd(b, a % b)` compiles to stores into the parameter slots and a `goto 0`, which is a loop.
- A version of `sumTo` that carries a running total as an extra parameter returned 500,000,500,000 for `sumTo(1_000_000)`.
- The naive `n + sumToNaive(n - 1)` threw `StackOverflowError`.
- Marking a naive version `tailrec` produced the warning "recursive call is not a tail call", and the bytecode kept the recursive call.

The general fix is to move the pending work into an accumulator parameter. `tailrec` does not cover mutual recursion; for that, the stdlib's `DeepRecursiveFunction` keeps the call stack on the heap. But for tasks like "sum the ledger" or "apply all events to the state", `fold`, `sumOf` and `firstOrNull` say what is meant in one line and compile to the same loop. Head/tail recursion with `drop(1)`, by contrast, copies the list at every step and is O(n²). A closing exercise sums a ledger three ways (naive recursion, `tailrec`, and `fold`) and then shows in `javap` that the last two are both loops. It ends the course on its central theme: functional Kotlin is valuable because it makes code easier to reason about, and cheap whenever the compiler turns it into the loop the engineer would have written anyway.

## Conclusion

The deepest lesson of this material is that teaching functional Kotlin to Java engineers is less about adding abstractions than about recalibrating trust. Each Java safety mechanism these engineers rely on — `final`, unmodifiable collections, `Optional`, checked exceptions, streams — has a Kotlin counterpart that is lighter and is mostly a compile-time signal. FP discipline is what turns those signals back into guarantees: immutable types all the way down, exhaustive `when` without `else`, typed error values, and a return-value checker that catches discarded results. A successful course leaves engineers able to say, for any line of code, which invariants the compiler actually enforces and which they are merely hoping for; being able to write `curried()` is a minor by-product. The material also turns the usual performance objection around. Because `Iterable` operations and scope functions are inlined into loops, the idiomatic path is usually as cheap as the imperative one. "FP is slow" thus becomes a narrow, testable claim about sequences, capturing lambdas and boxing.

The other implication is that parts of this curriculum will go out of date quickly. The return-value checker and its `returnsResultOf` refinement, Arrow's experimental accumulation API, kotlinx.collections.immutable's pre-1.0 API, and above all the rich-errors proposal could each change what the immutability and error-handling modules should recommend within a release or two. Build the course with explicit version anchors. Keep the hand-written `Outcome` as the conceptual core, so the lessons survive a shift from Arrow to native error unions. Re-run the demo suite against each new Kotlin release, applying the same predict-then-run discipline the course teaches.
