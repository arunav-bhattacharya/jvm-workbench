import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")

INTRO = """By the end of this track you'll have built one working library: a typed, in-process event library for a payments service. It has a sealed model of payment events with value-class ids and amounts, and one parser at the edge that turns raw Kafka fields into that model or rejects them. It has an event bus that routes each event to the handlers of its class and of every supertype, accepts one general handler for any subscription, survives a failing handler, and runs middleware and timing decorators. And it has an API that reads well from both sides: a subscription DSL for Kotlin, and overloads, statics and a facade for Java, checked by a Java test.

It draws on the whole of Part 3. The model comes from *Modern Java data modeling* (sealed types, pattern switches, parsing at the edge) and from the value classes of *Advanced Kotlin*. The bus is variance, reified type parameters and `KClass` from *Kotlin generics, properly*, put together with Observer, Chain of Responsibility and Decorator from *Design patterns in Java and Kotlin*. The API leans on inline functions and type-safe DSLs from *Advanced Kotlin*. Each lesson names the earlier lesson it relies on, so you can go back when a step doesn't stick.

The labs live in `labs/events`, one package per lesson (`workbench.events.l01` to `l03`). Each lab starts from the previous lab's solution, so you can begin at any lesson. Lessons 1 and 2 are written in Kotlin; lesson 3 adds a Java class, `RefundDesk`, and a Java test that uses the library the way a Java team would. Run `./gradlew :events:test --tests 'workbench.events.lNN.*'` from `labs/` until it passes, and `./gradlew :events:solutionTest` to check the reference answers. The tests use kotlin-reflect for two checks (`sealedSubclasses` and the variance of `Handler`); the library itself doesn't need it."""

CHEATSHEET = """## The model (lesson 1)

- [ ] Every event is a past-tense fact in one sealed hierarchy: `PaymentEvent`, with a sealed `MoneyMovement` in the middle for captures and refunds.
- [ ] Leaves are data classes (records in Java): final, compared by value, validated in `init`.
- [ ] Ids and amounts are value classes with `init` checks: `PaymentId`, `Money` (euro cents). Keep `toString(): String` explicit.
- [ ] Every operation is a `when` / `switch` with **no `else`** over your own sealed type.
- [ ] One edge function, `parseEvent(fields): Parsed`, returns `Ok` or `Rejected` and never throws. Rules live in the constructors; the parser turns their `IllegalArgumentException` into `Rejected`.
- [ ] `Rejected` goes to a dead-letter topic with its reason. Never retry it.

```java
sealed interface PaymentEvent permits PaymentAuthorized, PaymentDeclined, MoneyMovement { PaymentId paymentId(); }
sealed interface MoneyMovement extends PaymentEvent permits PaymentCaptured, PaymentRefunded { Money amount(); }
record PaymentCaptured(PaymentId paymentId, Money amount) implements MoneyMovement {}
```

```kotlin
sealed interface PaymentEvent { val paymentId: PaymentId }
sealed interface MoneyMovement : PaymentEvent { val amount: Money }
data class PaymentCaptured(override val paymentId: PaymentId, override val amount: Money) : MoneyMovement
```

## The bus (lesson 2)

- [ ] Registry keyed by `KClass`; dispatch keys = the event's class, then its event supertypes, nearest first, cached per class with `computeIfAbsent`. Java reflection (`getInterfaces`, `getSuperclass`) is enough: no kotlin-reflect.
- [ ] Delivery order is a promise: most specific key first, then wider ones; within a key, subscription order. Test it.
- [ ] `fun interface Handler<in E : PaymentEvent>`: a consumer, so `in`. Java sees `Handler<? super E>`.
- [ ] Store each handler behind an adapter `Handler<PaymentEvent> { e -> handler.handle(type.cast(e)) }`.
- [ ] `subscribe` returns a `Subscription : AutoCloseable` that removes exactly that adapter. Closing twice is harmless.
- [ ] `catch (e: Exception)` around each handler, reported to an injected `ErrorHandler` with the event.
- [ ] Each key's handlers in a `CopyOnWriteArrayList`: delivery iterates a snapshot, a handler may unsubscribe itself, publishers need no lock.
- [ ] Middleware (every event once: logging, dedupe) is a chain built once by `foldRight` over a copy of the list. Order is behavior.
- [ ] Per-handler concerns (timing) are decorators: same `Handler<E>`, record in `finally`, clock injected as a `Ticker`.

```java
<E extends PaymentEvent> AutoCloseable subscribe(Class<E> type, Handler<? super E> handler) {
    Handler<PaymentEvent> adapter = event -> handler.handle(type.cast(event));
    List<Handler<PaymentEvent>> list = registry.computeIfAbsent(type, t -> new CopyOnWriteArrayList<>());
    list.add(adapter);
    return () -> list.remove(adapter);
}
```

```kotlin
fun <E : PaymentEvent> subscribe(type: KClass<E>, handler: Handler<E>): Subscription {
    val adapter = Handler<PaymentEvent> { event -> handler.handle(type.cast(event)) }
    val list = registry.computeIfAbsent(type) { CopyOnWriteArrayList() }
    list += adapter
    return Subscription { list.remove(adapter) }
}
```

## The API (lesson 3)

- [ ] The DSL collects in `on` and subscribes in `commit`, after the block: a block that throws subscribes nothing; one handle closes all, in reverse.
- [ ] `inline fun <reified E> on(crossinline handler: (E) -> Unit)`: `crossinline` because the lambda runs inside a `Handler` object.
- [ ] `@DslMarker` on the builder classes; a `check(!committed)` for calls from inside handlers, which the marker can't see.
- [ ] Every reified or `KClass` function has a `Class<E>` overload that delegates with `type.kotlin`.
- [ ] `@JvmOverloads` on constructors with defaults, `@JvmStatic` on object members, `@JvmField` on companion constants, `@file:JvmName` on files of top-level functions.
- [ ] A facade (`Events.captured(String, long)`) that builds the value classes, so Java input is validated. Never `@JvmName` straight past `init`.
- [ ] Callbacks are `fun interface`s with `void`/`int` methods, and the Java DSL entry takes a `Consumer`: no `return Unit.INSTANCE`.
- [ ] One Java test in the Kotlin module's build.

| Kotlin as written | What Java gets | Fix |
|---|---|---|
| reified function | invisible (synthetic) | `Class<E>` overload |
| `KClass<E>` parameter | `JvmClassMappingKt.getKotlinClass(X.class)` | `Class<E>` overload |
| default arguments | all-defaults and full constructors only | `@JvmOverloads` |
| `object` member, companion `val` | `INSTANCE.f()`, `Companion.getX()` | `@JvmStatic`, `@JvmField` |
| value classes in a data class | private constructor, mangled getters | facade with plain types |

## Design review questions

| Question | Forced, or a judgment call? |
|---|---|
| No `else` on sealed `when`s? | forced: *Sealed types: hierarchies the compiler can check* |
| `Handler<in E>`? | forced: *Contravariance with in: consumers* |
| `Class<E>` overloads? | forced: *Type erasure and reified type parameters* |
| Value classes plus a Java facade? | judgment: undo if most callers are Java |
| `Money` without currency? | judgment: undo when a second currency arrives |
| Synchronous, in-memory delivery? | judgment: keep inside one service; durable events go through an outbox |
| Unbounded `DropDuplicates`? | judgment: undo; bound it or use a unique key in the handler's store |"""

RECAP = [
 "Parse raw input once, at the edge, into a sealed model; return `Ok` or `Rejected` and never throw. Behind the edge, handlers trust the types.",
 "A `when` with no `else` over your own sealed type turns a new event type into a list of compile errors. A sealed middle level lets one branch, or one handler, stand for its leaves.",
 "Value classes make ids and amounts their own types at no cost where used as themselves; their `init` blocks make every instance valid. One field only, so `Money` is euro cents until it needs a currency.",
 "Route each event to its class and then its event supertypes, nearest first, from a per-class cache. Declare handlers `in`, store them behind casting adapters.",
 "Observer rules hold: return a handle, isolate each handler's exception and report it, iterate a copy-on-write snapshot. Delivery stays synchronous, so keep handlers fast.",
 "Concerns for every event once are a middleware chain built by a fold, where order is behavior. Concerns for one handler are decorators. Test time with a fake ticker.",
 "The subscription DSL collects and commits, uses reified `on<E>` with `crossinline`, and `@DslMarker` so nested blocks can't reach the wrong builder.",
 "Give Java `Class<E>` overloads, `@JvmOverloads`, `@JvmStatic`, `@JvmField`, `@file:JvmName` and a facade that builds the value classes, and test it from Java.",
 "In the design review, defend forced choices by their mechanism and write down the judgment calls with the condition that would undo them."
]

QUIZ = [
 {
  "q": "A capture arrives as raw fields with `amountMinor = \"0\"`. Where is it refused, and what does the consumer see?",
  "options": [
   "In the ledger handler, which throws, and the consumer retries the record",
   "In `PaymentCaptured`'s `init`; `parseEvent` returns `Rejected` with that message",
   "In `parseEvent`, by its own `amount > 0` check, which returns `null`",
   "Nowhere: a zero capture is valid"
  ],
  "answer": 1,
  "why": "The rule lives in the constructor, once. The edge calls the constructor and turns its `IllegalArgumentException` into a `Rejected`, which the consumer sends to the dead-letter topic before any handler acts."
 },
 {
  "q": "`summary`, `movesMoney` and the metrics tag are `when`s over `PaymentEvent` with no `else`. Someone adds `PaymentDisputed : PaymentEvent`. What finds every place that must change?",
  "options": [
   "A run-time `NoWhenBranchMatchedException` in production",
   "A code search for `PaymentCaptured`",
   "The compiler: each of those `when`s fails until it handles disputes",
   "Nothing: `when` falls through to the last branch"
  ],
  "answer": 2,
  "why": "Exhaustiveness is checked at compile time, and with no `else` the new subtype is missing from each `when`. An `else` anywhere would swallow it silently. The run-time exception only happens when code compiled against the old model meets the new type."
 },
 {
  "q": "Why is `Money` a value class of euro cents with no currency field?",
  "options": [
   "Because a JVM value class can hold exactly one field, and this service settles in euros only",
   "Because value classes can't hold a `Currency` object",
   "Because Java callers can't read two fields",
   "Because data classes can't validate in `init`"
  ],
  "answer": 0,
  "why": "Until Valhalla, Kotlin's `@JvmInline value class` has one property. Amount plus currency would be a data class, one object per amount. The design review marks this as a judgment call to undo when a second currency arrives."
 },
 {
  "q": "Subscribed in this order: `audit` under `PaymentEvent`, `movements` under `MoneyMovement`, `ledger` then `receipts` under `PaymentCaptured`. You publish a capture. In what order do they run?",
  "options": [
   "audit, movements, ledger, receipts",
   "ledger, receipts, movements, audit",
   "receipts, ledger, movements, audit",
   "ledger, movements, audit, receipts"
  ],
  "answer": 1,
  "why": "Keys are visited nearest first: `PaymentCaptured`, then `MoneyMovement`, then `PaymentEvent`. Within one key, handlers run in subscription order, so `ledger` comes before `receipts`."
 },
 {
  "q": "In a Java class, `Handler<PaymentEvent> audit = e -> ...;` and then `bus.subscribe(PaymentCaptured.class, audit);` compiles. Why?",
  "options": [
   "Because Java generics are covariant",
   "Because `subscribe` casts its argument",
   "Because `PaymentCaptured.class` is a `Class<PaymentEvent>`",
   "Because `Handler` is declared `in`, so kotlinc writes `Handler<? super E>` into the Java signature"
  ],
  "answer": 3,
  "why": "Declaration-site `in` becomes a `? super` wildcard in parameter types. A handler of any event can then stand in for a handler of captures, in Java as in Kotlin. Java generics are invariant without a wildcard."
 },
 {
  "q": "Of three handlers for a capture, the second throws `IllegalStateException`. What does `publish` return, and what happens to the error?",
  "options": [
   "3; the bus reports it, with the event, to its `ErrorHandler`, and the third handler still runs",
   "1; `publish` stops at the failure and rethrows",
   "2; the failing handler isn't counted and the error is dropped",
   "It throws, after running all three"
  ],
  "answer": 0,
  "why": "Each call is wrapped in its own `try`, so one failure can't starve the rest, and `publish` counts the handlers it called. The bus doesn't decide what an error means: the injected `ErrorHandler` does."
 },
 {
  "q": "You want to know how long the receipts handler takes per event. Where does the timing go?",
  "options": [
   "A middleware, first in the list",
   "Inside `publish`, around `deliver`",
   "A decorator around the receipts handler: the same `Handler<E>`, timed in `finally`",
   "In the `ErrorHandler`"
  ],
  "answer": 2,
  "why": "Middleware and `publish` see one delivery to all of an event's handlers, so they'd add the ledger's time to the receipts' time. A decorator wraps exactly one handler, and with an injected `Ticker` its numbers are testable."
 },
 {
  "q": "A `bus.subscriptions { ... }` block declares two handlers and then throws because a config value is missing. How many handlers are subscribed afterwards?",
  "options": [
   "Two, and the caller has no handle to remove them",
   "One",
   "Two, removed again by a `finally` in the block",
   "None: the builder only subscribes after the block returns"
  ],
  "answer": 3,
  "why": "`on` only records a pending subscription, and `commit` runs after the block. So a failing block leaves the bus untouched, and a successful one returns a single handle for everything it declared."
 },
 {
  "q": "Java code needs a refund event for 5.00 on `pay_7781`. Which line compiles and validates?",
  "options": [
   "`new PaymentRefunded(new PaymentId(\"pay_7781\"), new Money(500))`",
   "`Events.refunded(\"pay_7781\", 500)`",
   "`new PaymentRefunded(\"pay_7781\", 500L)`",
   "`PaymentRefunded.Companion.of(\"pay_7781\", 500)`"
  ],
  "answer": 1,
  "why": "The value classes' constructors and the data class constructor are private to Java (javac reports `has private access` or `cannot find symbol`). The `@JvmStatic` facade takes plain values and builds the value classes, so their `init` checks run. There is no `Companion.of` in this library."
 },
 {
  "q": "The business adds payments in pounds. Which change comes first?",
  "options": [
   "Make `Money` a data class of amount and currency, and add a currency field to the edge parser",
   "Add an `else` branch to every `when` so new currencies don't break the build",
   "Key the bus by currency as well as by class",
   "Add `@JvmOverloads` to `Money`"
  ],
  "answer": 0,
  "why": "The euro-only `Money` was a judgment call made cheap by the one-field rule. A second currency is exactly the condition that undoes it. The model changes, the parser learns the new field, and the compiler points at every place that used the old `Money`."
 }
]

T = {"id": "cap3", "intro": INTRO, "cheatsheet": CHEATSHEET, "recap": RECAP, "quiz": QUIZ}
out = ROOT / "content/tracks/cap3.json"
out.write_text(json.dumps(T, indent=1, ensure_ascii=False) + "\n")
print(out)
