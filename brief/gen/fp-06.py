import json, pathlib

ROOT = pathlib.Path("/home/user/jvm-workbench")
LAB = "labs/functional/src"
K = "kotlin/workbench/functional/l06"
J = "java/workbench/functional/l06"
read = lambda p: (ROOT / p).read_text()
run = lambda cls: f"./gradlew :functional:demo -Pmain=workbench.functional.l06.{cls}"


def tryit(kt, java):
    k, j = kt.replace(".kt", ""), java.replace(".java", "")
    return {"lang": "kotlin", "title": kt, "src": read(f"{LAB}/demo/{K}/{kt}"), "run": run(k + "Kt"), "file": f"{LAB}/demo/{K}/{kt}",
            "alt": {"lang": "java", "title": java, "src": read(f"{LAB}/demo/{J}/{java}"), "run": run(j), "file": f"{LAB}/demo/{J}/{java}"}}


FIG = (
    '<svg viewBox="0 0 640 300" role="img" aria-label="A two by two grid. Columns: returns the block result, or returns the object itself. '
    'Rows: the object is this, or the object is it. run and with: this, block result. apply: this, the object. let: it, block result. also: it, the object.">'
    '<text class="t" x="300" y="40" text-anchor="middle">returns the block\'s result</text>'
    '<text class="t" x="500" y="40" text-anchor="middle">returns the object itself</text>'
    '<text class="t" x="100" y="106" text-anchor="middle">object is this</text>'
    '<text class="t-s t-m" x="100" y="126" text-anchor="middle">(receiver)</text>'
    '<text class="t" x="100" y="196" text-anchor="middle">object is it</text>'
    '<text class="t-s t-m" x="100" y="216" text-anchor="middle">(argument)</text>'
    '<rect class="box-a" x="210" y="70" width="180" height="70" rx="8"/>'
    '<text class="t t-code" x="300" y="100" text-anchor="middle">run, with</text>'
    '<text class="t-s" x="300" y="124" text-anchor="middle">compute from members</text>'
    '<rect class="box-b" x="410" y="70" width="180" height="70" rx="8"/>'
    '<text class="t t-code" x="500" y="100" text-anchor="middle">apply</text>'
    '<text class="t-s" x="500" y="124" text-anchor="middle">configure an object</text>'
    '<rect class="box-a" x="210" y="160" width="180" height="70" rx="8"/>'
    '<text class="t t-code" x="300" y="190" text-anchor="middle">let</text>'
    '<text class="t-s" x="300" y="214" text-anchor="middle">transform, null check</text>'
    '<rect class="box-b" x="410" y="160" width="180" height="70" rx="8"/>'
    '<text class="t t-code" x="500" y="190" text-anchor="middle">also</text>'
    '<text class="t-s" x="500" y="214" text-anchor="middle">side effect, keep the value</text>'
    '<text class="t-s t-m" x="320" y="262" text-anchor="middle">Non-extension run { } has no object: a block where an expression is needed.</text>'
    '<text class="t-s t-m" x="320" y="284" text-anchor="middle">All five are inline and run the block exactly once, right there.</text>'
    '</svg>'
)

L = {
 "id": "fp-06",
 "title": "Scope functions: let, run, with, apply and also, on purpose",
 "minutes": 38,
 "goal": "By the end you can pick `let`, `run`, `with`, `apply` or `also` by answering two questions, spot the four scope-function bugs that compile without a warning, and handle nulls with `?.`, `?:`, `takeIf` and `requireNotNull` instead of reaching for `Optional`.",
 "warmup": {
  "q": "`payment.status` is `AUTHORIZED`. After `val captured = payment.also { it.copy(status = Status.CAPTURED) }`, what is `captured.status`?",
  "options": [
   "`CAPTURED`",
   "`AUTHORIZED`",
   "It doesn't compile: the block of `also` must return `Unit`",
   "It throws, because data classes are immutable"
  ],
  "answer": 1,
  "why": "`also` runs the block and then returns the object it was called on. Its block has the type `(T) -> Unit`, so the copy the block makes is thrown away. Kotlin 2.4.21 compiles this without a warning. `payment.let { it.copy(...) }`, or simply `payment.copy(...)`, gives you the copy."
 },
 "sections": [
  {
   "h": "A scope function is a two-line function you could write yourself",
   "body": """Here is code that builds a gateway request and logs it. It is how most of us write it on day one:

```kotlin
val request = PaymentRequest()
request.amount = Money(1_999, "EUR")
request.merchantId = "m-42"
request.reference = order.id
log.info("sending {}", request)
```

```java
PaymentRequest request = new PaymentRequest();
request.setAmount(new Money(1_999, "EUR"));
request.setMerchantId("m-42");
request.setReference(order.id());
log.info("sending {}", request);
```

Nothing is wrong with it. It repeats `request.` on every line, and nothing marks where the setup ends. Kotlin code often says the same thing like this:

```kotlin
val request = PaymentRequest().apply {
    amount = Money(1_999, "EUR")
    merchantId = "m-42"
    reference = order.id
}.also { log.info("sending {}", it) }
```

```java
// Java equivalent: a helper that takes a Consumer and returns the object
PaymentRequest request = apply(new PaymentRequest(), r -> {
    r.setAmount(new Money(1_999, "EUR"));
    r.setMerchantId("m-42");
    r.setReference(order.id());
});
log.info("sending {}", request);
```

`apply` and `also` look like keywords. They are ordinary functions in the standard library, a couple of lines each. Here are `let` and `apply` written by hand:

```kotlin
fun <T, R> T.myLet(block: (T) -> R): R = block(this)                 // object in as `it`, block's result out
fun <T> T.myApply(block: T.() -> Unit): T { block(); return this }   // object is `this` inside, object out
```

```java
static <T, R> R let(T value, Function<T, R> block) { return block.apply(value); }
static <T> T apply(T value, Consumer<T> block) { block.accept(value); return value; }
```

Both are extension functions on any type `T`. The difference is the type of `block`. `(T) -> R` is a plain function type: the object arrives as the lambda's parameter, `it`. `T.() -> Unit` is a function type with a receiver, which "Function types, lambdas and closures" showed briefly: inside the lambda the object is `this`, so `amount = ...` means `this.amount = ...`. Java has no lambdas with a receiver, which is why the Java helper needs `r.` on every line.

The real `let` in the Kotlin 2.4.21 standard library is that same line plus two things:

```kotlin solo
@kotlin.internal.InlineOnly
public inline fun <T, R> T.let(block: (T) -> R): R {
    contract { callsInPlace(block, InvocationKind.EXACTLY_ONCE) }
    return block(this)
}
```

`inline` makes the compiler paste the block into your code, so no lambda object exists at run time ("Higher-order functions: functions in, functions out" explained why). The contract is the next section's topic. So every scope function has one of these shapes, and the five differ in exactly two ways: whether the block sees the object as `this` or as `it`, and whether the call returns **the object** or **the block's result**.""",
   "try": {
    "title": "One block, five functions, two answers",
    "minutes": 3,
    "steps": [
     "Open `ScopeReturns.kt`. The same block, `amountMinor * 2`, runs through all five scope functions. Write down what each line prints before you run it.",
     "Run it.",
     "On the `also` line, change `also` to `let`. Predict the output, then run it.",
     "Read `ScopeReturnsJava.java`: what does Java write for each one?"
    ],
    "code": tryit("ScopeReturns.kt", "ScopeReturnsJava.java"),
    "expect": "`let`, `run` and `with` print `3998`, because they return the block's result. `also` and `apply` print the `Charge` itself: they run the block and drop its result. `myLet` and `myApply` behave the same, because that is all the real ones do. Changing `also` to `let` changes the value of the whole expression from the `Charge` to `3998`. In Java, \"compute something\" is a plain expression and \"keep the object\" needs a helper that takes a `Consumer`."
   }
  },
  {
   "h": "Two questions pick the function",
   "body": """Because the five differ in only two ways, two questions pick one.

First, **what should the expression give back?** If you want the same object (to keep chaining it, return it or assign it), use `apply` or `also`. If you want something new, a computed value or a different object, use `let`, `run` or `with`.

Second, how does the block use the object? If it mostly sets or calls the object's own members, a receiver reads best: `apply`, `run`, `with`. If it passes the object to other functions, or it also needs the `this` of the class around it, use an argument: `also`, `let`.

The figure puts the answers in a grid. The Kotlin docs give the same advice as a list of purposes, and each purpose lands in one cell:

| You want to | Use | Payments example |
|---|---|---|
| configure an object | `apply` | `PaymentRequest().apply { amount = total; merchantId = id }` |
| do something extra and keep the object | `also` | `authorize(req).also { audit.record(it) }` |
| run code on a non-null value, or scope a temporary | `let` | `card.token?.let { vault.lookup(it) }` |
| configure and compute a result | `run` | `client.run { timeoutMs = 800; charge(req) }` |
| run statements where an expression is needed | `run { }` | `val limit = run { val base = tier.limit(); base + overdraft }` |
| group calls on an object you already have | `with` | `with(settlement) { "$merchantId paid $amount on $date" }` |

`run` and `with` do the same job. `with(x) { }` reads well on a line of its own; `x.run { }` is the one that fits in a chain and after `?.`. There is no `?.with`.

The five share one more property, and it explains code that looks like it shouldn't compile:

```kotlin
val authCode: String
val auth = gateway.authorize(request).also { authCode = it.code }   // compiles
```

```java
// Java equivalent: a lambda can't assign a local at all, so this is a plain statement
Authorization auth = gateway.authorize(request);
final String authCode = auth.code();
```

A `val` may be assigned only once, and here the assignment sits inside a lambda. The compiler accepts it because `also` declares a **contract**, `callsInPlace(block, InvocationKind.EXACTLY_ONCE)`: a promise that the block runs right here, exactly one time. All five scope functions declare it. Write your own `also` without the contract and the same line fails with `Captured values cannot be initialized because of possible reassignments.` Contracts are an Experimental API that the compiler trusts and never checks. The Advanced Kotlin track covers them in "Contracts and context parameters".

Because the five are `inline`, a bare `return` inside the block returns from the function around it, not from the block. In `payment?.let { if (it.isTest) return; ledger.post(it) }`, a test payment leaves the whole function.""",
   "figure": {"svg": FIG, "caption": "Two questions: is the object this or it inside the block, and does the call give back the block's result or the object?"},
   "try": {
    "title": "Assign a val inside a block",
    "minutes": 4,
    "steps": [
     "Run `ValInit.kt`. Both `val`s are assigned inside a block.",
     "Uncomment the two `plainAlso` lines at the end of `main` and run it again. Read the compiler error, then comment them out again.",
     "In `contractAlso`, delete the `contract { ... }` line but keep `inline`. Predict: is `inline` enough on its own? Run it.",
     "Uncomment the two lines in `ValInitJava.java` and run it. Read javac's error."
    ],
    "code": tryit("ValInit.kt", "ValInitJava.java"),
    "expect": "The first run prints `also: A-5 for 1999` and `contractAlso: A-262 for 4250`. With `plainAlso`, the build fails with `Captured values cannot be initialized because of possible reassignments.`, because the compiler can't see how often the block runs. Without the contract, `inline` is not enough: the errors are `'val' cannot be reassigned.` and `Variable 'code2' must be initialized.` The contract is what carries the promise. javac says `local variables referenced from a lambda expression must be final or effectively final`: Java never lets a lambda assign a local."
   },
   "refs": [{"title": "Scope functions (Kotlin docs)", "url": "https://kotlinlang.org/docs/scope-functions.html", "kind": "docs"}]
  },
  {
   "h": "Four bugs that compile without a warning",
   "body": """Scope functions are inlined, so they cost nothing at run time. Their cost is in reading. Each of these four compiles on Kotlin 2.4.21 without a warning, and each one looks fine in a code review.

The first is `?.let { } ?: run { }` used as if/else. Here it fronts a cache:

```kotlin
fun settle(cached: Payment?, ledger: Ledger, fetch: () -> Payment): String? =
    cached?.let { ledger.post(it) }          // post returns null for a duplicate
        ?: run { ledger.post(fetch()) }
```

```java
String settle(Payment cached, Ledger ledger, Supplier<Payment> fetch) {
    return Optional.ofNullable(cached).map(ledger::post)   // map turns a null result into empty
            .orElseGet(() -> ledger.post(fetch.get()));
}
```

It reads as "if cached, post it, else fetch and post". But `?:` tests the value on its left, and that value is the result of the `let` block, not `cached`. `ledger.post` returns `null` for a payment it has already seen, so a cache hit on a duplicate **runs both branches**: one database fetch and a second post. Java's `Optional.map(...).orElseGet(...)` has exactly the same trap. Write the branch you mean with `if` or `when`, or decide the value first: `val payment = cached ?: fetch()`, then post once.

The second is `also` or `apply` used to compute. `payment.also { it.copy(status = CAPTURED) }` returns the original payment, because the block's type is `(T) -> Unit` and the copy is dropped. `payments.apply { sumOf { it.amountMinor } }` returns the list, not the total. A declared type catches the second one (`val total: Long = ...` fails with `Initializer type mismatch: expected 'Long', actual 'List<Payment>'.`). Nothing catches the first. When you want the block's result, use `let` or `run`.

The third is nested receivers. In `form.apply { fx.apply { amount = 500 } }`, the bare `amount` binds to the innermost receiver that has one, `fx`. Delete `amount` from `Fx` a year later and the same line still compiles, and now it writes `form.amount`. A change in one class has changed code in another. Java's double-brace initialization follows the same rule and has the same trap. Don't nest `apply`; write the target (`fx.amount = 500`).

The fourth is a nested `it`. In `merchants[id]?.let { schedules[it.scheduleId]?.let { "${it.name}: ${it.rateBps} bps" } }`, the second `it.name` is the schedule's name, not the merchant's. Java can't make this mistake: it makes you name both lambda parameters and refuses to reuse a name. In Kotlin, name them, or better, flatten the chain:

```kotlin
val merchant = merchants[id] ?: return "$id: no fee schedule"
val schedule = schedules[merchant.scheduleId] ?: return "$id: no fee schedule"
return "${merchant.name}: ${schedule.rateBps} bps"
```

```java
Merchant merchant = merchants.get(id);
if (merchant == null) return id + ": no fee schedule";
FeeSchedule schedule = schedules.get(merchant.scheduleId());
if (schedule == null) return id + ": no fee schedule";
return merchant.name() + ": " + schedule.rateBps() + " bps";
```""",
   "try": {
    "title": "Run the four bugs",
    "minutes": 5,
    "steps": [
     "Read `ScopeBugs.kt`. For each of the four numbered parts, predict what it prints.",
     "Run it.",
     "In `class Fx`, delete `var amount: Long = 0`. In part 3, change the `println` to print only `form.amount`. Predict the value, then run.",
     "Run `ScopeBugsJava.java`. Which of the four bugs does Java share, and which can't it have?"
    ],
    "code": tryit("ScopeBugs.kt", "ScopeBugsJava.java"),
    "expect": "The second settle prints `cache miss, fetching from the database` and then `null`, although the payment was in the cache: the `let` block returned `null`, so `run` ran too. `also { copy }` leaves the status `AUTHORIZED`, and `apply { sumOf }` prints the list. The nested `apply` gives `form.amount = 0, form.fx.amount = 500`; after you delete `Fx.amount`, the unchanged line sets `form.amount = 500` and the compiler says nothing. The label is `standard-eu: 290 bps`, the schedule's name. Java shares the first three (`orElseGet`, `peek`, double-brace initialization) and gets the label right, because both parameters have names."
   },
   "refs": [{"title": "This expressions: qualified this (Kotlin docs)", "url": "https://kotlinlang.org/docs/this-expressions.html", "kind": "docs"}]
  },
  {
   "h": "Nulls are values: ?., ?:, takeIf and requireNotNull",
   "body": """A Java developer new to Kotlin often reaches for `Optional`. You don't need it. A nullable type `T?` is not a wrapper. In the words of the Kotlin docs, "at runtime, objects of nullable types and objects of non-nullable types are treated the same": the checks all happen at compile time. The operators do what `Optional`'s methods do, with no extra object:

| Java `Optional` | Kotlin |
|---|---|
| `opt.map(f)` | `x?.let(f)` or `x?.f()` |
| `opt.orElse(d)` | `x ?: d` |
| `opt.orElseGet(() -> ...)` | `x ?: run { ... }`, also lazy |
| `opt.orElseThrow()` | `x ?: throw ...` or `requireNotNull(x)` |
| `opt.filter(p)` | `x?.takeIf(p)` |
| `opt.ifPresent(c)` | `x?.let(c)` or `x?.also(c)` |

The right side of `?:` can `return` or `throw`, because both are expressions in Kotlin. That turns a guard clause into one line, and every line after it works with a non-null value:

```kotlin
val token = card?.token ?: return Declined("no card token")
```

```java
String token = card == null ? null : card.token();
if (token == null) return new Declined("no card token");
```

`takeIf { }` is a filter for one value: the object if the predicate holds, `null` if not. It earns its place inside a chain, as in `amount.takeIf { it > 0 }?.let(::charge)`. As a guard on its own, a plain `if` reads better. The predicate always runs, so keep side effects out of it. For collections, `mapNotNull { }` maps and drops the nulls in one pass.

When a `null` means somebody broke a rule, fail loudly and say why. `requireNotNull(x) { "..." }` throws `IllegalArgumentException`, for bad input from a caller. `checkNotNull(x) { "..." }` throws `IllegalStateException`, for our own broken state. Both carry a contract that tells the compiler `x` is not null afterwards, so `x` is smart-cast from the next line on. `!!` throws a `NullPointerException` with no message at all. Java's `Objects.requireNonNull(x, "...")` takes a message but still throws `NullPointerException`.

Smart casts have one limit you will hit. A `var` property is never smart-cast, because other code could change it between the check and the use. `if (pendingRefund != null) send(pendingRefund)` fails with `Smart cast to 'Long' is impossible, because 'pendingRefund' is a mutable property that could be mutated concurrently.` This is where `?.let` is the right tool: `pendingRefund?.let(send)` reads the property once. `val refund = pendingRefund ?: return` works too.

Arrow, the library in the next lesson, gives the same advice about its own `Option` type: "Typically, when working in Kotlin, you should prefer working with nullable types over Option as it is more idiomatic." It keeps `Option` for nested nullability in generic code and for libraries such as Reactor that forbid `null`.""",
   "try": {
    "title": "Four null tools, two languages",
    "minutes": 4,
    "steps": [
     "Run `NullTools.kt`, then `NullToolsJava.java`. Compare the exception each null check throws.",
     "In `Checkout.process`, uncomment the `if` line and run. Read the error, then comment it out again.",
     "Change the first line of `tokenFor` to `val token = requireNotNull(card?.token) { \"no card token\" }`. Predict what happens to the second call in `main`. Is that better or worse here?"
    ],
    "code": tryit("NullTools.kt", "NullToolsJava.java"),
    "expect": "Kotlin prints `IllegalArgumentException: refund p9 has no amount` and `IllegalStateException: ledger session not opened`; Java's `Objects.requireNonNull` prints `NullPointerException: refund p9 has no amount`. The `if` line fails with the smart-cast error, because `pendingRefund` is a `var` property. With `requireNotNull`, the second call stops `main` with an `IllegalArgumentException`. That is worse here: a card without a token is an expected outcome (a decline), not a bug, so it belongs in the return value. The next lesson makes that line its whole topic."
   },
   "refs": [{"title": "Null safety (Kotlin docs)", "url": "https://kotlinlang.org/docs/null-safety.html", "kind": "docs"}]
  },
  {
   "h": "A checklist you can run in five seconds",
   "body": """When your fingers are about to type a scope function, run down this list and stop at the first line that settles it.

1. Do you need one at all? A plain call, `a?.b()`, an `if` on a local `val`, or `val x = y ?: return` is often clearer. Detekt ships `UnnecessaryLet` and `UnnecessaryApply` rules for exactly this case.
2. What should the expression give back? The same object: `apply` or `also`. Something new: `let`, `run` or `with`.
3. How does the block use the object? Its own members: `apply`, `run`, `with`. Passed to other functions, or the outer `this` must stay visible: `also`, `let`.
4. Is the value nullable? Use `?.let`, `?.run`, `?.also` or `?.apply`, never `with`. If you add `?: something`, make sure the block on the left can never produce `null`. If it can, write `if` or `when`.
5. Is the block nested, longer than about five lines, or the third link in a chain? Extract a function or use named `val`s. The Kotlin docs ask you not to nest scope functions, because "it's easy to get confused about the current context object and value of `this` or `it`".

Try the list on one line: `PaymentRequest().apply { reference = order.id }.also { log.info("sending {}", it) }`. Line 1 has something to say about the `apply`: a block with a single assignment is exactly what detekt's `UnnecessaryApply` flags. Line 2 approves of the `also`: it is a side step, and the request flows on unchanged.""",
  }
 ],
 "analogy": "Think of a post office counter. You hand over a parcel. With `apply`, the clerk works on the parcel itself, adds stamps and a label, and hands the same parcel back. With `also`, the clerk photographs it for the records and hands it back untouched. With `let` or `run`, the clerk weighs it and hands you a receipt with the price: you get something new back, and the parcel drops out of the conversation. `this` or `it` is whether the clerk opens the parcel and works inside it, or treats it as one item to pass along. The analogy breaks in one place: a real clerk who promised you a receipt can't secretly repackage your parcel too. A `run` block can change the object and return something else, and none of the five stops you from doing the wrong kind of work inside the block.",
 "in_your_world": "Scope functions show up all over a Quarkus payments service. `ProducerRecord(topic, key, value).apply { headers().add(\"idempotency-key\", key.toByteArray()) }` configures a Kafka record before `send`. `.also { meter.counter(\"payments.sent\").increment() }` counts it without touching it. Panache entities are where the null rules bite: their fields are `var` properties, so `entity.cardToken` is never smart-cast, and `entity.cardToken?.let { vault.lookup(it) }` or a local `val` is the right tool. And look hard at every `?.let { ... } ?: run { ... }` around a repository or a map lookup. `HashMap.put` returns the previous value, which is `null` the first time, so `found?.let { cache.put(id, it) } ?: run { log.warn(\"missing\") }` warns on every first insert.",
 "mistake": "The most common real mistake is reading `x?.let { A } ?: run { B }` as \"if x, then A, else B\". People write it because it looks like `Optional.map(...).orElseGet(...)` or Swift's `if let`, and in the happy path it behaves that way. But `?:` checks the value of the whole left side, which is the result of block A. Whenever A ends in a call that can return `null` (a repository `find`, `map[key]`, `HashMap.put`, a `save()` that returns an optional id), B runs as well, after A already did its work. In payments that means a second fetch, a second post or a misleading log line. The fix is to write the branch you mean: `if (x != null) A else B`, or a `when`. If A is only a side effect, `x?.also { A } ?: B` is safe, because `also` returns `x` itself, which is not null.",
 "compare": {
  "title": "Configure, log and compute: scope functions vs plain Java",
  "java": {"title": "Checkout.java", "src": "PaymentRequest request = new PaymentRequest();      // configure: a variable and setters\nrequest.setAmount(order.total());\nrequest.setMerchantId(order.merchantId());\nrequest.setReference(order.id());\nlog.info(\"sending {}\", request);                     // a side step is just a statement\n\nlong risk = riskModel.score(request.getAmount(), request.getMerchantId());   // compute\n\nString token = Optional.ofNullable(card).map(Card::token)                     // null check with a message\n        .orElseThrow(() -> new IllegalArgumentException(\"no card token\"));"},
  "kotlin": {"title": "Checkout.kt", "src": "val request = PaymentRequest().apply {                // configure: this, returns the request\n    amount = order.total\n    merchantId = order.merchantId\n    reference = order.id\n}.also { log.info(\"sending {}\", it) }                 // side step: it, returns the request\n\nval risk = request.run { riskModel.score(amount, merchantId) }   // compute: this, returns the score\n\nval token = requireNotNull(card?.token) { \"no card token\" }      // null check with a message"},
  "note": "At run time the two are the same. Every scope function is inlined, so the bytecode is the same local variable, setter calls and statements the Java version has. What differs is what the code tells the reader and what the compiler can check. `apply` puts the whole setup in one block, so the request is finished when the block ends, and `also` marks the log line as a side step that can't change the value flowing through. Java needs an `Optional` object to chain a null check; Kotlin's `?.` and `requireNotNull` exist only at compile time, and `requireNotNull` smart-casts what follows. Java lambdas have no receiver and can't assign locals. That is why Java has no `apply` and no `val`-inside-`also`, and also why it can't have the nested-receiver bug."
 },
 "worked": {
  "title": "Untangle a refund handler",
  "steps": [
   {"say": "A refund handler written as one expression. `gateway.refund` returns `null` when the acquirer rejects the refund. Before reading on, find every outcome that ends up in the wrong place.", "code": "fun handleRefund(cmd: RefundCommand): RefundOutcome =\n    payments.find(cmd.paymentId)?.let {\n        it.takeIf { it.status == Status.CAPTURED }?.let {\n            gateway.refund(it.id, cmd.amount)\n        }?.let { RefundOutcome.Accepted(it) }\n    } ?: run { RefundOutcome.NotRefundable(cmd.paymentId) }", "lang": "kotlin", "alt_lang": "java", "alt_code": "RefundOutcome handleRefund(RefundCommand cmd) {\n    return payments.find(cmd.paymentId())                     // Optional<Payment>\n            .filter(p -> p.status() == Status.CAPTURED)\n            .map(p -> gateway.refund(p.id(), cmd.amount()))   // null when rejected: map makes it empty\n            .<RefundOutcome>map(RefundOutcome.Accepted::new)\n            .orElseGet(() -> new RefundOutcome.NotRefundable(cmd.paymentId()));\n}"},
   {"code": "", "lang": "", "say": "Three different failures come out as one. A payment that doesn't exist, a payment that isn't captured, and a refund the acquirer rejected all become `null` somewhere in the chain, so `?: run` reports all three as `NotRefundable`. Support will tell the merchant to stop retrying a refund that only failed at the acquirer. And there are four `it`s with three meanings."},
   {"say": "Rewrite it top to bottom. 1. Load, and leave early if it's missing. 2. Check the business rule. 3. Do the work, and name its failure. 4. Put the happy path last. Each failure now has its own outcome, and no line depends on which `it` is in scope.", "code": "fun handleRefund(cmd: RefundCommand): RefundOutcome {\n    val payment = payments.find(cmd.paymentId)            // 1. load\n        ?: return RefundOutcome.NotFound(cmd.paymentId)\n    if (payment.status != Status.CAPTURED)                // 2. check the rule\n        return RefundOutcome.NotRefundable(payment.id, payment.status)\n    val refundId = gateway.refund(payment.id, cmd.amount) // 3. act\n        ?: return RefundOutcome.Rejected(payment.id)\n    return RefundOutcome.Accepted(refundId)               // 4. the happy path, last\n}", "lang": "kotlin", "alt_lang": "java", "alt_code": "RefundOutcome handleRefund(RefundCommand cmd) {\n    Payment payment = payments.find(cmd.paymentId()).orElse(null);   // 1. load\n    if (payment == null) return new RefundOutcome.NotFound(cmd.paymentId());\n    if (payment.status() != Status.CAPTURED)                         // 2. check the rule\n        return new RefundOutcome.NotRefundable(payment.id(), payment.status());\n    RefundId refundId = gateway.refund(payment.id(), cmd.amount());  // 3. act\n    if (refundId == null) return new RefundOutcome.Rejected(payment.id());\n    return new RefundOutcome.Accepted(refundId);                     // 4. the happy path, last\n}"},
   {"say": "A scope function still has a place here: a side step that must not change the result. `also` logs the outcome and returns it unchanged, which is what the reader expects from the word.", "code": "    return RefundOutcome.Accepted(refundId)\n        .also { log.info(\"refund accepted: {}\", it) }     // side step: the value flows through", "lang": "kotlin", "alt_lang": "java", "alt_code": "    RefundOutcome outcome = new RefundOutcome.Accepted(refundId);\n    log.info(\"refund accepted: {}\", outcome);              // Java: just a statement\n    return outcome;"}
  ]
 },
 "lab": {
  "title": "Fix four scope-function bugs at the settlement desk",
  "minutes": 13,
  "files": [f"{LAB}/main/{K}/SettlementDesk.kt", f"{LAB}/main/{K}/Model.kt"],
  "run": "./gradlew :functional:test --tests 'workbench.functional.l06.*'",
  "steps": [
   "Run the tests. Four of ten fail, one for each function in `SettlementDesk.kt`. Read each failure message before you read the code. `Model.kt` holds the types and needs no changes.",
   "`settle`: a cache hit on an already-posted payment must not fetch or post again. Rewrite it without `?: run`.",
   "`capture`: return the captured copy.",
   "`buildRequest`: the order id belongs in `request.reference`, not `metadata.reference`.",
   "`feeLabel`: show the merchant's name, not the schedule's. Use named values instead of `it`.",
   "Run the tests until all ten pass. Then run the five-second checklist over your four functions."
  ],
  "hints": [
   "For `settle`, decide the payment first (`cached ?: fetch()`), then post it once. `?: return` handles the duplicate.",
   "`capture` is a two-branch `if` expression. It needs no scope function.",
   "In `buildRequest`, a nested `apply` with one line inside can become `metadata.channel = \"ecom\"`.",
   "In `feeLabel`, two `val`s, each with `?: return \"...\"`, read top to bottom and can't mix up the merchant and the schedule."
  ],
  "done_when": "All ten tests in `ScopeFunctionsTest` pass."
 },
 "drill": {
  "title": "The grid from memory",
  "minutes": 4,
  "prompt": "Close this page. Draw the 2x2 grid (`this` or `it`, the object or the block's result) and put the five functions in it. Then write one payments line for each, and next to it, what the whole expression evaluates to. Check your grid against the figure.",
  "answer": {
   "lang": "kotlin",
   "src": "//            returns the object | returns the block's result\n// this:      apply              | run, with\n// it:        also               | let\n\nval req = PaymentRequest().apply { amount = total; merchantId = \"m-42\" }   // the request\nval auth = gateway.authorize(req).also { audit.record(it) }               // the authorization\nval risk = req.run { riskModel.score(amount, merchantId) }                // the score\nval line = with(auth) { \"$code for $amountMinor\" }                        // the String\nval entry = card.token?.let { vault.lookup(it) }                          // the lookup result, or null",
   "alt": {"lang": "java", "src": "// Java has no scope functions; each line is the plain Java it stands for\nPaymentRequest req = new PaymentRequest(); req.setAmount(total); req.setMerchantId(\"m-42\");\nAuthorization auth = gateway.authorize(req); audit.record(auth);\nlong risk = riskModel.score(req.getAmount(), req.getMerchantId());\nString line = auth.code() + \" for \" + auth.amountMinor();\nVaultEntry entry = card.token() == null ? null : vault.lookup(card.token());"}
  }
 },
 "recap": [
  "A scope function is a tiny inline function: it runs a block with the object as `this` (`run`, `with`, `apply`) or `it` (`let`, `also`), and returns the object (`apply`, `also`) or the block's result (`let`, `run`, `with`).",
  "Pick by two questions: what should the expression give back, and does the block use the object's members or pass the object along?",
  "All five are inline and declare `callsInPlace(block, EXACTLY_ONCE)`: no lambda objects, a `val` can be assigned inside, and a bare `return` leaves the enclosing function.",
  "`x?.let { A } ?: B` runs B whenever A evaluates to null, not only when x is null. When A can be null, write `if` or `when`.",
  "`also` and `apply` drop the block's result, and nested receivers and nested `it` quietly pick the innermost one. None of these gets a warning.",
  "Nullable types replace `Optional`: `?.` maps, `?:` defaults, returns or throws, `takeIf` filters, and `requireNotNull`/`checkNotNull` fail with a message and smart-cast."
 ],
 "quiz": [
  {"q": "You build a Kafka `ProducerRecord`, add two headers to it, and pass the record on in the same chain. Which scope function fits?", "options": ["`let`", "`apply`", "`run`", "`with`"], "answer": 1, "why": "You want the same record back (so the chain continues) and the block works on the record's own members (`headers()`): that is the `this`, returns-the-object cell. `let` and `run` would return whatever the last header call returned. `with` can't sit in a chain."},
  {"q": "`val rate = merchant?.let { schedules[it.scheduleId]?.rate } ?: DEFAULT_RATE`. The merchant exists, but its schedule is missing from the map. What is `rate`?", "options": ["`DEFAULT_RATE`", "`null`", "It throws a NullPointerException", "It doesn't compile, because `let` can't return null"], "answer": 0, "why": "`?:` checks the result of the `let` block, which is `null` because the schedule is missing, so you get `DEFAULT_RATE`. Here that is what you want. It's the same mechanism that makes `?.let { } ?: run { }` run both branches when the left block can return null for a reason you didn't mean."},
  {"q": "What does `val total: Long = refunds.apply { sumOf { it.amountMinor } }` do?", "options": ["Sets `total` to the sum of the refunds", "Sets `total` to 0", "Throws ClassCastException at run time", "Fails to compile: `Initializer type mismatch: expected 'Long', actual 'List<Refund>'.`"], "answer": 3, "why": "`apply` returns the object it was called on, the list, and drops the block's result. The declared `Long` type makes the compiler catch it. Without the type, `total` would silently be the list. `run { sumOf { ... } }`, or just `sumOf { }`, returns the sum."},
  {"q": "A Panache entity has `var cardToken: String?`. Which line compiles and uses the token you checked?", "options": ["`if (entity.cardToken != null) vault.lookup(entity.cardToken)`", "`with(entity.cardToken) { vault.lookup(this) }`", "`entity.cardToken?.let { vault.lookup(it) }`", "`entity.cardToken.takeIf { it != null }.let { vault.lookup(it) }`"], "answer": 2, "why": "`?.let` reads the property once and gives the block a non-null `it`. The `if` version fails: a `var` property is never smart-cast. Inside `with`, `this` is still `String?`. `takeIf` returns `String?`, and the plain `.let` hands that nullable value to `lookup`, which doesn't compile either."},
  {"q": "From the sequences lesson: `val all = allSettlements(api)` is a `sequence { }` that fetches pages. The code runs `all.also { log.info(\"{} settlements\", it.count()) }.first { it.amountCents > 50_000 }`. What does the API see?", "options": ["Only the pages `first` needs", "Every page for `count()`, then the pages from page 0 again for `first`", "Nothing, because `also` doesn't run on a sequence", "One pass, then an IllegalStateException on the second read"], "answer": 1, "why": "`also` runs its block right away, and `count()` is a terminal operation that reads the whole sequence. Then `also` returns the same sequence, a recipe, and `first` runs it again from page 0. The `sequence { }` builder can be read twice, so nothing throws; it just fetches twice.", "from": "fp-05"}
 ],
 "flashcards": [
  {"front": "Which scope functions return the object itself?", "back": "`apply` and `also`. `let`, `run` and `with` return the block's result."},
  {"front": "In which scope functions is the object `this`?", "back": "`run`, `with` and `apply`, whose blocks are lambdas with a receiver. In `let` and `also` it is `it`."},
  {"front": "`x?.let { f(it) } ?: g()`: x is not null but `f(x)` returns null. Does `g()` run?", "back": "Yes. `?:` tests the result of the `let` block, not `x`."},
  {"front": "Why does `val code: String; auth.also { code = it.code }` compile?", "back": "`also` declares the contract `callsInPlace(block, EXACTLY_ONCE)`, so the compiler knows the block runs exactly once, right there. `inline` alone isn't enough."},
  {"front": "What does `payment.also { it.copy(status = CAPTURED) }` return?", "back": "The original payment. The block's type is `(T) -> Unit`, so the copy is thrown away."},
  {"front": "`requireNotNull`, `checkNotNull` or `!!`?", "back": "`requireNotNull`: IllegalArgumentException with your message (bad input). `checkNotNull`: IllegalStateException (bad state). `!!`: NullPointerException, no message. The first two smart-cast afterwards."},
  {"front": "Why does `if (prop != null) use(prop)` fail when `prop` is a `var` property?", "back": "A `var` property is never smart-cast: it could change between the check and the use. Use `prop?.let(::use)` or copy it into a local `val`."}
 ],
 "terms": [
  {"term": "Scope function", "plain": "One of `let`, `run`, `with`, `apply`, `also`: a small inline function that runs a block with an object in scope."},
  {"term": "Context object", "plain": "The object a scope function is called on. Inside the block it is `this` or `it`."},
  {"term": "Lambda with receiver", "plain": "A lambda of type `T.() -> R`. Inside it, the `T` value is `this`, so its members need no prefix."},
  {"term": "Contract", "plain": "A promise a function makes to the compiler, such as \"I call this block exactly once\". The compiler trusts it and doesn't check it."},
  {"term": "Smart cast", "plain": "The compiler treating a value as a narrower type (for example non-null) after a check, when it can prove nothing changed in between."},
  {"term": "Elvis operator", "plain": "`a ?: b`: the value of `a` if it isn't null, otherwise `b`. `b` can be `return` or `throw`."}
 ],
 "explain_back": {
  "prompt": "A teammate writes `repo.find(id)?.let { cache.put(id, it) } ?: run { log.warn(\"missing $id\") }` and says it means \"cache it if found, warn if not\". `cache` is a `HashMap`. Explain when it does something else, and what you'd write instead.",
  "answer": "The Elvis operator doesn't look at what `find` returned. It looks at the value of the whole left side, which is the result of the `let` block, and that is whatever `cache.put` returned. `HashMap.put` returns the previous value for the key, which is null the first time. So every time an entity is found and cached for the first time, the block returns null and the warning runs too: \"missing\" gets logged for entities that were found. It only behaves as intended when an older value was already cached. I'd write the branch I mean: `val entity = repo.find(id); if (entity != null) cache[id] = entity else log.warn(\"missing $id\")`. Or, since caching is only a side effect, `repo.find(id)?.also { cache[id] = it } ?: log.warn(...)`, because `also` returns the entity itself, which is not null."
 },
 "deeper": {
  "minutes": 8,
  "body": """Two things are changing around scope functions, and one tool can enforce the checklist for you.

**The return-value checker.** Kotlin 2.3.0 added an Experimental checker that warns when you ignore a function's result. It is off by default; `-Xreturn-value-checker=check` reports ignored results of functions the standard library marks, and `full` treats every function as marked. In Kotlin 2.4.21, all six scope functions (the five plus non-extension `run`) carry `@IgnorableReturnValue`, so `payment.let { it.copy(status = CAPTURED) }` as a bare statement is not reported. `takeIf` and `takeUnless` don't carry it. On the standard library's main branch, after 2.4.21, `let`, `run` and `with` have dropped `@IgnorableReturnValue` for a new `returnsResultOf(block)` contract, which Kotlin 2.4.0 introduced as Experimental. With it, the checker can tell `x?.let { builder.append(it) }` (fine to ignore) from `x?.let { "kotlin.$it" }` (a value you computed and dropped). Which release will ship that change isn't known yet. `apply` and `also` keep `@IgnorableReturnValue`, so the `also { it.copy() }` bug stays invisible to the checker.

**Labels for nested receivers.** When you can't avoid a nested receiver, `this@label` says which one you mean. Two nested `apply` blocks share the implicit label `@apply`, so you need your own: `form.apply outer@{ fx.apply { this@outer.amount = 500 } }`. If you need a label, that is usually a sign to flatten the code instead.

**Detekt.** Detekt 1.23.8, the current stable release, has rules for most of the checklist: `UnnecessaryLet`, `UnnecessaryApply` (active by default since 1.16.0), `AlsoCouldBeApply` and `UseLet` in the style rule set, and `NestedScopeFunctions` in the complexity rule set. Apart from `UnnecessaryApply`, they are off until you enable them. `UseLet` pulls the other way from `UnnecessaryLet`: it wants `if (x != null) f(x) else null` written as `x?.let { f(it) }`. A rule of thumb that satisfies both: use `?.let` when the non-null value flows into an expression, and use `if` on a local `val` for control flow and for branches with more than one statement."""
 },
 "sources": [
  {"title": "Scope functions (Kotlin docs)", "url": "https://kotlinlang.org/docs/scope-functions.html"},
  {"title": "Null safety (Kotlin docs)", "url": "https://kotlinlang.org/docs/null-safety.html"},
  {"title": "Standard.kt, Kotlin 2.4.21 stdlib source", "url": "https://github.com/JetBrains/kotlin/blob/v2.4.21/libraries/stdlib/src/kotlin/util/Standard.kt"},
  {"title": "Nullable and Option, Arrow docs source", "url": "https://github.com/arrow-kt/arrow-website/blob/main/content/docs/learn/typed-errors/wrappers/nullable-and-option.md"},
  {"title": "NestedScopeFunctions rule, detekt 1.23.8 source", "url": "https://github.com/detekt/detekt/blob/v1.23.8/detekt-rules-complexity/src/main/kotlin/io/gitlab/arturbosch/detekt/rules/complexity/NestedScopeFunctions.kt"}
 ]
}

out = ROOT / "content/lessons/fp-06.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
