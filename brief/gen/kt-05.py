import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/kotlin/src"
P = "kotlin/workbench/kotlin/l05"
DK = "kotlin/workbench/kotlin/l05/demo"
DJ = "java/workbench/kotlin/l05/demo"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :kotlin:demo -Pmain=workbench.kotlin.l05.demo."


def demo(name):
    """Kotlin demo with its runnable Java twin."""
    return {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{DK}/{name}.kt"),
            "run": RUN + name + "Kt", "file": f"{lab}/demo/{DK}/{name}.kt",
            "alt": {"lang": "java", "title": f"{name}Java.java", "src": read(f"{lab}/demo/{DJ}/{name}Java.java"),
                    "run": RUN + name + "Java", "file": f"{lab}/demo/{DJ}/{name}Java.java"}}


FIG = (
    '<svg viewBox="0 0 680 230" role="img" aria-label="A function with context parameters compiles to a static method whose first parameters are the context parameters, then the extension receiver, then the ordinary parameters">'
    '<text class="t-s t-m" x="340" y="20" text-anchor="middle">Kotlin declaration</text>'
    '<rect class="box-a" x="20" y="32" width="250" height="40" rx="8"/>'
    '<text class="t-s t-code" x="145" y="57" text-anchor="middle">context(logger: Logger, tx: TxId)</text>'
    '<rect class="box-b" x="290" y="32" width="150" height="40" rx="8"/>'
    '<text class="t-s t-code" x="365" y="57" text-anchor="middle">fun Payment.</text>'
    '<rect class="box" x="460" y="32" width="200" height="40" rx="8"/>'
    '<text class="t-s t-code" x="560" y="57" text-anchor="middle">authorize(merchant: String)</text>'
    '<line class="ln" x1="110" y1="72" x2="77" y2="138" marker-end="url(#arr)"/>'
    '<line class="ln" x1="180" y1="72" x2="212" y2="138" marker-end="url(#arr)"/>'
    '<line class="ln" x1="365" y1="72" x2="365" y2="138" marker-end="url(#arr)"/>'
    '<line class="ln" x1="560" y1="72" x2="560" y2="138" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="340" y="106" text-anchor="middle">order on the JVM</text>'
    '<rect class="box-a" x="20" y="142" width="115" height="40" rx="8"/>'
    '<text class="t t-code" x="77" y="167" text-anchor="middle">Logger</text>'
    '<rect class="box-a" x="155" y="142" width="115" height="40" rx="8"/>'
    '<text class="t t-code" x="212" y="167" text-anchor="middle">TxId</text>'
    '<rect class="box-b" x="290" y="142" width="150" height="40" rx="8"/>'
    '<text class="t t-code" x="365" y="167" text-anchor="middle">Payment</text>'
    '<rect class="box" x="460" y="142" width="200" height="40" rx="8"/>'
    '<text class="t t-code" x="560" y="167" text-anchor="middle">String</text>'
    '<text class="t-s t-code" x="340" y="212" text-anchor="middle">static boolean authorize(Logger, TxId, Payment, String)</text>'
    '</svg>'
)

L = {
 "id": "kt-05",
 "title": "Contracts and context parameters",
 "minutes": 35,
 "goal": "By the end you can write a contract that gives callers smart casts and in-place lambdas, explain why the compiler trusts it blindly, declare and call functions with context parameters in Kotlin 2.4, and predict their JVM signature.",
 "warmup": {
  "q": "`fun requireCurrency(c: String?) { if (c == null) throw IllegalArgumentException() }`. After `requireCurrency(currency)`, you write `currency.uppercase()` where `currency` is a `String?`. What happens?",
  "options": ["It compiles: the compiler sees the throw inside `requireCurrency`", "Compile error: `currency` is still a `String?` to the compiler", "It compiles with a warning", "It compiles, and throws NullPointerException if `currency` is null"],
  "answer": 1,
  "why": "The compiler analyzes each function on its own. It doesn't look inside `requireCurrency` to learn that a normal return means `c != null`, so `currency` stays nullable and you get `only safe (?.) or non-null asserted (!!.) calls are allowed on a nullable receiver of type 'String?'.` The standard library's `require` gets the smart cast because it declares a contract, which is the first half of this lesson."
 },
 "sections": [
  {
   "h": "Your own check functions teach the compiler nothing",
   "body": "The standard library's `require(currency != null)` makes `currency` usable as a `String` on the next line. Write the same check in your own function, and the compiler forgets it:\n\n```java\n// Java's type system doesn't track null at all, so the question never comes up\nstatic void requireCurrency(String currency) {\n    if (currency == null) throw new IllegalArgumentException(\"currency missing\");\n}\n\nrequireCurrency(currency);\nSystem.out.println(currency.toUpperCase());      // compiles, as everything does\n```\n\n```kotlin\nfun requireCurrencyPlain(currency: String?) {\n    if (currency == null) throw IllegalArgumentException(\"currency missing\")\n}\n\nrequireCurrencyPlain(currency)\nprintln(currency.uppercase())\n// error: only safe (?.) or non-null asserted (!!.) calls are allowed on a nullable receiver of type 'String?'.\n```\n\nThe feature that fails here is the **smart cast**: after a check such as `if (x != null)`, the compiler treats `x` as the narrower type. It does that only for checks it can see in the current function. It never reads the body of a function you call, because that body may change, or live in another module.\n\nA **contract** closes the gap. It is a `contract { }` block, written as the first statement of a function, that states something about the function's behavior that callers may rely on. Two kinds matter in practice. `returns() implies (currency != null)` says: if this function returns normally, the condition holds. `callsInPlace(block, InvocationKind.EXACTLY_ONCE)` says: the lambda runs exactly once, during this call, and is not stored. The other kinds are `AT_MOST_ONCE`, `AT_LEAST_ONCE` and `UNKNOWN`.\n\n```java\n// Java can't assign a local inside a lambda at all:\n// \"local variables referenced from a lambda expression must be final or effectively final\"\nString[] label = new String[1];\nContractsDemoKt.once(() -> { label[0] = \"batch-17\"; return Unit.INSTANCE; });\n```\n\n```kotlin\n@OptIn(ExperimentalContracts::class)\nfun requireCurrency(currency: String?) {\n    contract { returns() implies (currency != null) }\n    if (currency == null) throw IllegalArgumentException(\"currency missing\")\n}\n\n@OptIn(ExperimentalContracts::class)\ninline fun <T> once(block: () -> T): T {\n    contract { callsInPlace(block, InvocationKind.EXACTLY_ONCE) }\n    return block()\n}\n\nval label: String\nonce { label = \"batch-17\" }     // allowed: the block runs exactly once\n```\n\nThis is how `require`, `check`, `requireNotNull`, `run`, `let` and `apply` work in the standard library. Contracts are still Experimental in Kotlin 2.4: the 2.4.0 notes say so, and without `@OptIn(ExperimentalContracts::class)` every part of the block fails with `this declaration needs opt-in.` No compiler flag is needed, only the annotation.",
   "try": {
    "title": "Take each contract away",
    "minutes": 4,
    "steps": [
     "Run `ContractsDemo` (or `ContractsDemoJava`, which calls the same Kotlin functions).",
     "Wrong move 1: call `requireCurrencyPlain(currency)` instead of `requireCurrency(currency)`. Predict the error, run, undo.",
     "Wrong move 2: delete the `contract { callsInPlace(...) }` line in `once`. `once` is still inline. Predict whether that is enough, run, undo.",
     "Wrong move 3: delete the `@OptIn` above `isCaptured`, run, undo."
    ],
    "code": demo("ContractsDemo"),
    "expect": "The demo prints `currency = EUR`, `captured 1999` and `label = batch-17`. Move 1 fails on `currency.uppercase()` with the nullable-receiver error. Move 2 fails with `'val' cannot be reassigned.` and `variable 'label' must be initialized.`: being inline doesn't tell the compiler how many times the body calls `block`. Move 3 fails with `this declaration needs opt-in. Its usage must be marked with '@kotlin.contracts.ExperimentalContracts' or '@OptIn(kotlin.contracts.ExperimentalContracts::class)'`."
   },
   "refs": [{"title": "KEEP-0139: Kotlin contracts", "url": "https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0139-kotlin-contracts.md", "kind": "read"}]
  },
  {
   "h": "The compiler trusts a contract and never checks it",
   "body": "A contract is a promise, and the compiler doesn't check the body against it. The design document, KEEP-139, says the compiler \"trusts contracts unconditionally\" and that the programmer is \"responsible for writing correct and sound contracts\". Formal verification is listed as a non-goal. So this compiles without a single warning:\n\n```java\n// Java's version of the same lie: a check that always says yes, and a cast that believes it\nstatic boolean lyingIsCaptured(PaymentEvent e) { return true; }\n\nif (lyingIsCaptured(failed)) {\n    Captured c = (Captured) failed;              // ClassCastException\n}\n```\n\n```kotlin\n@OptIn(ExperimentalContracts::class)\nfun PaymentEvent.lyingIsCaptured(): Boolean {\n    contract { returns(true) implies (this@lyingIsCaptured is Captured) }\n    return true                                  // the lie\n}\n\nif (failed.lyingIsCaptured()) println(failed.amountMinor)   // ClassCastException\n```\n\nThe smart cast to `Captured` lets `failed.amountMinor` compile. At run time the JVM still checks the cast it was given, and `Failed` is not a `Captured`: `class ...Failed cannot be cast to class ...Captured`. A contract can't make a wrong value right. It moves the cast from your code, where a reviewer sees it, into a promise inside another function.\n\nLook one level down and the reason is plain. `javap -c` on the honest `isCaptured` shows a null check on the receiver, then `instanceof Captured` and `ireturn`: no trace of the contract. The contract lives in the Kotlin metadata of the class file, which only the Kotlin compiler reads when it compiles a caller. Java callers never see it, and nothing at run time enforces it.\n\nThe K2 compiler does catch some `callsInPlace` mistakes, as warnings. A block declared `EXACTLY_ONCE` but called twice gets `wrong invocation kind 'EXACTLY_ONCE' for 'block: () -> Unit' specified, the actual invocation kind is 'AT_LEAST_ONCE'.` A block declared in place but stored in a list gets `leaked in-place lambda 'block: () -> Unit'.` Nothing checks `returns ... implies`. And the block must come first: anything before it is `contract should be the first statement.`\n\nSo write contracts the way the standard library does: tiny functions whose body is the condition itself, such as `if (!condition) throw ...`, so a reader can check the promise in one glance. Kotlin 2.2.20 added more Experimental forms (contracts on property accessors, `returnsNotNull()`, `holdsIn`). The last two need a second opt-in, `ExperimentalExtendedContracts`.",
   "try": {
    "title": "Make a contract lie",
    "minutes": 3,
    "steps": [
     "Run `LyingContractDemo`. Before you do, predict: compile error, a warning, or a run-time failure?",
     "Run `LyingContractDemoJava`, which tells the same lie in Java with a cast, then calls the Kotlin function.",
     "Run `javap -c -p -cp kotlin/build/classes/kotlin/demo workbench.kotlin.l05.demo.ContractsDemoKt` from `labs/` and read `isCaptured`. Where is the contract?"
    ],
    "code": demo("LyingContractDemo"),
    "expect": "It compiles cleanly and fails at run time with `ClassCastException: class workbench.kotlin.l05.demo.Failed cannot be cast to class workbench.kotlin.l05.demo.Captured`. The Java twin fails the same way, then prints `Kotlin lyingIsCaptured from Java: true`: to Java it's a boolean method. In `javap`, `isCaptured` is a null check on the receiver, then `instanceof` and `ireturn`. The contract isn't in the bytecode at all."
   }
  },
  {
   "h": "Context parameters: arguments the compiler passes for you",
   "body": "Some values have to reach almost every function in a request: a logger, the transaction id, a clock. Passed by hand, they turn every signature into plumbing:\n\n```java\nboolean authorize(Logger logger, TxId tx, Payment payment, String merchant) { ... }\n\nString checkout(Logger logger, TxId tx, Payment payment, String merchant) {\n    boolean ok = authorize(logger, tx, payment, merchant);   // pass both on, by hand\n    audit(logger, \"checkout \" + tx.value());\n    return ok ? \"APPROVED\" : \"DECLINED\";\n}\n```\n\n```kotlin\ncontext(logger: Logger, tx: TxId)\nfun Payment.authorize(merchant: String): Boolean {\n    logger.log(\"[${tx.value}] authorizing $amountMinor for $merchant\")\n    return amountMinor < 100_000\n}\n\ncontext(logger: Logger, tx: TxId)\nfun checkout(payment: Payment, merchant: String): String {\n    val approved = payment.authorize(merchant)               // logger and tx flow on by themselves\n    audit(\"checkout ${tx.value}\")\n    return if (approved) \"APPROVED\" else \"DECLINED\"\n}\n```\n\nA **context parameter** is a parameter the caller doesn't write. You declare it in `context(...)` before `fun`, with a name and a type. At each call, the compiler finds a value of that type in the caller's surroundings and passes it: an enclosing function's own context parameter (as in `checkout` above), a `context(console, TxId(\"tx-42\")) { ... }` block from the standard library, or an implicit receiver, such as the `this` of a `with(console) { ... }` block. The value it finds is called the **context argument**. Inside the function, you use the parameter by its name. If you don't need a name, write `_` and read the value with `contextOf<Logger>()`.\n\nThe docs describe them as dependencies that are \"implicitly available in the surrounding context\". On the JVM there is nothing implicit about them, as the figure shows. They become ordinary leading parameters: the context parameters first, then the extension receiver, then the value parameters. `javap` prints `authorize(Logger, TxId, Payment, String)`, and Java calls it by passing all four.\n\nThe status changed a lot in a short time. Context parameters were a preview in Kotlin 2.2.0 behind `-Xcontext-parameters`, and became Stable in 2.4.0, \"except for context arguments and callable references\". So in 2.4 you need no flag. The old flag now earns `warning: the argument '-Xcontext-parameters' is redundant for the current language version 2.4.`, which tells you an older build file is still around.",
   "figure": {"svg": FIG, "caption": "On the JVM, context parameters are plain leading parameters, followed by the extension receiver and then the ordinary parameters."},
   "try": {
    "title": "Follow a context through two calls",
    "minutes": 4,
    "steps": [
     "Run `ContextParamsDemo`. Predict the six lines it prints for the two checkouts.",
     "Run `ContextParamsDemoJava`, which calls the same functions from Java with every argument spelled out.",
     "Run `javap -p -cp kotlin/build/classes/kotlin/demo workbench.kotlin.l05.demo.ContextParamsDemoKt` and match each parameter to the figure.",
     "Uncomment the wrong move at the end of `main` (a call outside any context). Predict the error, then run."
    ],
    "code": demo("ContextParamsDemo"),
    "expect": "Each checkout prints `[tx-42] authorizing ...`, then `AUDIT checkout tx-42 approved` (or `declined` for 250,000), then `APPROVED` or `DECLINED`, and the last line is `AUDIT an implicit receiver works too`. `javap` lists `authorize(Logger, TxId, Payment, String)`, `checkout(Logger, TxId, Payment, String)` and `audit(Logger, String)`. The wrong move fails twice: `no context argument for 'logger: Logger' found.` and the same for `tx: TxId`."
   },
   "refs": [{"title": "Context parameters (Kotlin docs)", "url": "https://kotlinlang.org/docs/context-parameters.html", "kind": "docs"},
            {"title": "What's new in Kotlin 2.4.0", "url": "https://kotlinlang.org/docs/whatsnew24.html", "kind": "docs"}]
  },
  {
   "h": "Resolution rules, limits, and when to use them",
   "body": "The compiler resolves context arguments by type, so two values of the same type in the same scope are a problem. `context(a, b) { use() }` with two `Logger`s fails with `multiple potential context arguments for 'l: Logger' in scope.` The docs give the rule: if several compatible values exist at the same scope level, the compiler reports an ambiguity. A nearer scope still wins over an outer one: in `context(a) { context(b) { note(\"x\") } }` the inner `b` is used. That's a reason to give context parameters specific types: a `TxId` class instead of a bare `String`, an `AuditLog` interface instead of `(String) -> Unit`.\n\nA few things are not allowed. Constructors can't have context parameters (`context parameters on primary constructors are unsupported.`). A property can have them only without a backing field, so it has to be a computed getter (`property with context parameters cannot be initialized because it has no backing field.`). And two parts are still not stable in 2.4: passing a context argument explicitly by name, behind `-Xexplicit-context-arguments`, and callable references such as `::checkout`. Leave both alone in production code for now.\n\nOne change in 2.3.20 can surprise you if you migrate older code. Overload resolution used to treat a declaration with context parameters as more specific than one without. The 2.3.20 notes say that rule no longer applies, so a pair of overloads that differed only by a context may become ambiguous.\n\nThe JVM shape has two consequences. Java code can call these functions, as long as it passes every argument. And adding a context parameter to a public function changes its JVM signature, exactly like adding a parameter, so already-compiled callers break. Treat it as an API change.\n\nWhere do they fit in a Quarkus service? Not for business dependencies: a `PaymentRepository` belongs in the constructor, where CDI injects it once. Context parameters suit values that belong to the current unit of work and are needed by many small functions: the transaction or trace id, an audit sink, a `Clock` for tests, the `TxContext` the lab uses. They are cheap, they are visible in every signature, and the compiler checks them, which a `ThreadLocal` or a static MDC never does.\n\nA check to finish: `fun handle(req: AuthRequest) = with(AuditLog { println(it) }) { context(TxContext(\"tx-9\")) { req.authorize(10_000) } }`. Will it compile, and where does each context argument come from? (Answer: it compiles. The `AuditLog` comes from the implicit receiver of `with`, and the `TxContext` from the `context(...)` block. Each type has exactly one candidate.)"
  }
 ],
 "analogy": "A contract is a signed statement from a colleague: \"if my check returns, the field is filled in\". The compiler files it and never opens the folder to see whether it's true, so a false statement passes every gate until the moment someone relies on it. A context parameter is the badge you wear inside a building: doors (functions) check that you have one of the right kind and let you through without asking for it again. The analogy breaks at the JVM: there the badge is just one more argument handed to every function, and Java has to hand it over in person.",
 "in_your_world": "Payment validation code is full of checks that should narrow types: `ensure(req.currency != null, \"CURRENCY_MISSING\")` followed by code that uses the currency. A small contract-backed `ensure` gives you that without a `!!` on every line, and with a stable error code for the API response. Context parameters fit the values your Quarkus request handlers drag through every layer today: the transaction id, the merchant id for logs, an audit sink, a `Clock` your tests can freeze. A Temporal activity implementation could open one `context(audit, TxContext(paymentId)) { ... }` block and call ten helpers that never mention either. Keep injected services in constructors, where CDI puts them, and keep contracts tiny, because nobody checks them but you.",
 "mistake": "Writing a contract that is almost true. A team adds `returns(true) implies (this@isFinal is Settled)` to `isFinal()`, which returns true for `Settled` and, after a later change, also for `Cancelled`. Every caller that wrote `if (p.isFinal()) p.settledAt` still compiles. It fails only at run time, with a `ClassCastException`, on the first cancelled payment:\n\n```java\n// Java makes the risky cast visible at every call site, where review can see it\nif (p.isFinal()) { Instant at = ((Settled) p).getSettledAt(); }\n```\n\n```kotlin\nif (p.isFinal()) println(p.settledAt)   // the cast is hidden in isFinal's contract\n```\n\nThe compiler trusts contracts unconditionally, so a change to the body never revisits the promise. Keep the body of a contract function identical to its promise (`return this is Settled`), and add a unit test that feeds each subtype through it.",
 "compare": {
  "title": "A validation helper with an audit trail: Java parameters vs Kotlin contracts and context parameters",
  "java": {"title": "Authorize.java", "src": "final class Authorize {\n    static void ensure(boolean condition, String code, Supplier<String> message) {\n        if (!condition) throw new PaymentRejected(code, message.get());\n    }\n\n    static Decision authorize(AuditLog audit, TxContext tx, AuthRequest req, long limitMinor) {\n        try {\n            ensure(req.amountMinor() <= limitMinor, \"OVER_LIMIT\", () -> \"over the limit\");\n            ensure(req.currency() != null, \"CURRENCY_MISSING\", () -> \"currency is required\");\n            audit.record(\"[\" + tx.txId() + \"] approved \" + req.currency().toUpperCase());\n            return Decision.APPROVED;\n        } catch (PaymentRejected e) {\n            audit.record(\"[\" + tx.txId() + \"] rejected \" + e.code());\n            return Decision.rejected(e.code());\n        }\n    }\n}"},
  "kotlin": {"title": "Authorize.kt", "src": "@OptIn(ExperimentalContracts::class)\ninline fun ensure(condition: Boolean, code: String, lazyMessage: () -> String) {\n    contract {\n        returns() implies condition\n        callsInPlace(lazyMessage, InvocationKind.AT_MOST_ONCE)\n    }\n    if (!condition) throw PaymentRejected(code, lazyMessage())\n}\n\ncontext(audit: AuditLog, tx: TxContext)\nfun AuthRequest.authorize(limitMinor: Long): Decision =\n    try {\n        ensure(amountMinor <= limitMinor, \"OVER_LIMIT\") { \"over the limit\" }\n        ensure(currency != null, \"CURRENCY_MISSING\") { \"currency is required\" }\n        audit.record(\"[${tx.txId}] approved ${currency.uppercase()}\")   // smart cast\n        Decision.Approved\n    } catch (e: PaymentRejected) {\n        audit.record(\"[${tx.txId}] rejected ${e.code}\")\n        Decision.Rejected(e.code)\n    }"},
  "note": "The Java version compiles because Java doesn't track null, so `req.currency().toUpperCase()` is accepted whether or not the check ran. The Kotlin version compiles only because the contract tells the compiler that `ensure` returns only when its condition holds. Kotlin's `ensure` is inline, so the message lambda costs nothing on the happy path; Java builds a `Supplier` on every call. The audit log and transaction appear in Java's signature as two extra parameters that every caller passes on. In Kotlin they are context parameters, filled in by the compiler, and they still compile to exactly those two leading parameters, so Java can call the Kotlin `authorize` with `authorize(audit, tx, req, limitMinor)`."
 },
 "worked": {
  "title": "Replace a ThreadLocal transaction id with a context parameter",
  "steps": [
   {"say": "A service keeps the current transaction id in a `ThreadLocal`, so deep helpers can log it. It works until a helper runs on another thread, or a test forgets to set it, and then the log says `tx=null`. The compiler can't help, because nothing in the signature says the value is needed.",
    "code": "final class Tx {\n    static final ThreadLocal<String> CURRENT = new ThreadLocal<>();\n}\n\nstatic void note(String line) {\n    System.out.println(\"[\" + Tx.CURRENT.get() + \"] \" + line);   // null if nobody set it\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "object Tx {\n    val current = ThreadLocal<String>()\n}\n\nfun note(line: String) {\n    println(\"[${Tx.current.get()}] $line\")                     // null if nobody set it\n}"},
   {"say": "Make the need part of the signature. The helper declares a context parameter, and so does every function that calls it, until you reach the place that knows the transaction.",
    "code": "class TxContext(val txId: String)\n\n// 1. the helper declares what it needs\ncontext(tx: TxContext)\nfun note(line: String) = println(\"[${tx.txId}] $line\")\n\n// 2. callers in between declare it too, and never pass it by hand\ncontext(tx: TxContext)\nfun capture(paymentId: String) {\n    note(\"capturing $paymentId\")\n}", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "// Java's honest equivalent: an explicit parameter on every function in the chain\nrecord TxContext(String txId) {}\n\nstatic void note(TxContext tx, String line) { System.out.println(\"[\" + tx.txId() + \"] \" + line); }\n\nstatic void capture(TxContext tx, String paymentId) { note(tx, \"capturing \" + paymentId); }"},
   {"say": "Open the context once, where the transaction starts: the Kafka listener or the REST resource. Forgetting it is now a compile error, `no context argument for 'tx: TxContext' found.`, instead of a `null` in production logs.",
    "code": "// 3. open the context where the transaction id is known\nfun onMessage(record: PaymentCommand) {\n    context(TxContext(record.txId)) {\n        capture(record.paymentId)\n    }\n}\n\n// capture(\"pay_7\")   // error: no context argument for 'tx: TxContext' found.", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "void onMessage(PaymentCommand record) {\n    capture(new TxContext(record.txId()), record.paymentId());\n}"},
   {"say": "Check the price: each function in the chain gets one more JVM parameter, and nothing else. No `ThreadLocal`, no lookup, and the value follows the call, not the thread, so it survives a hop to another thread or a coroutine. Keep MDC for the logging library if it needs it, and fill it from the context at the edge.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "A contract-backed ensure and a context-aware authorize",
  "minutes": 13,
  "files": [f"{lab}/main/{P}/Ensure.kt", f"{lab}/main/{P}/Authorize.kt", f"{lab}/main/{P}/Callers.kt"],
  "run": "./gradlew :kotlin:test --tests 'workbench.kotlin.l05.*'",
  "steps": [
   "Run the tests. All seven fail. `Callers.kt` exists for the same reason as in lesson 1: `ensure` is inline.",
   "Write the body of `ensure` (TODO 1): throw `PaymentRejected(code, lazyMessage())` when the condition is false. Leave the contract for later.",
   "Write `note` (TODO 3) with the two context parameters, used by name.",
   "Write `authorize` (TODO 4). Use `currency.uppercase()` with no `!!` and build: it fails on the nullable receiver.",
   "Add the contract to `ensure` (TODO 2), with `@OptIn(ExperimentalContracts::class)` and the imports. Build again: `authorize` compiles now.",
   "Run until all seven pass, including `AuthorizeFromJavaTest`, which calls `authorize(log, tx, request, limit)` from Java."
  ],
  "hints": [
   "`contract { returns() implies condition; callsInPlace(lazyMessage, InvocationKind.AT_MOST_ONCE) }` must be the first statement in `ensure`.",
   "Inside `authorize`, `amountMinor`, `currency` and `cardToken` are properties of the receiver, so the smart cast works on `currency` directly.",
   "Wrap the four `ensure` calls and the success `note` in `try`, and catch `PaymentRejected` to build `Decision.Rejected(e.code)`. `try` is an expression, so the function can be `= try { ... } catch (...) { ... }`.",
   "`note(...)` needs no arguments for the context: inside `authorize`, the `audit` and `tx` context parameters are in scope, and the compiler passes them on."
  ],
  "done_when": "All seven tests in `AuthorizeTest` and `AuthorizeFromJavaTest` pass."
 },
 "drill": {
  "title": "Write ensureNotNull with a contract, from memory",
  "minutes": 4,
  "prompt": "Close this page. Write `ensureNotNull(value, code, lazyMessage)` that returns the value as non-null, throws `PaymentRejected` when it's null, and gives callers a smart cast on the variable they passed. Include the opt-in. Then write the Java version. What does the Kotlin compiler check about your contract?",
  "answer": {"lang": "kotlin", "src": "@OptIn(ExperimentalContracts::class)\ninline fun <T : Any> ensureNotNull(value: T?, code: String, lazyMessage: () -> String): T {\n    contract {\n        returns() implies (value != null)                       // callers get a smart cast\n        callsInPlace(lazyMessage, InvocationKind.AT_MOST_ONCE)\n    }\n    if (value == null) throw PaymentRejected(code, lazyMessage())\n    return value\n}\n\n// it checks that contract { } comes first and warns on some callsInPlace mistakes;\n// it never checks that the body keeps the returns-implies promise",
             "alt": {"lang": "java", "title": "Ensure.java", "src": "static <T> T ensureNotNull(T value, String code, Supplier<String> message) {\n    if (value == null) throw new PaymentRejected(code, message.get());\n    return value;            // Java has no smart casts, so callers use the return value\n}"}}
 },
 "recap": [
  "The compiler never reads the body of a function you call, so your own check functions give no smart casts until they declare a contract.",
  "`returns() implies cond` gives callers a smart cast after a normal return. `callsInPlace(block, EXACTLY_ONCE)` lets them initialize a `val` inside the lambda.",
  "Contracts are Experimental in Kotlin 2.4 and need `@OptIn(ExperimentalContracts::class)`. The compiler trusts them without checking; a lie becomes a `ClassCastException` at run time.",
  "Context parameters, `context(tx: TxContext) fun ...`, are Stable since Kotlin 2.4.0. The compiler fills them by type from enclosing context parameters, `context(...) { }` blocks and implicit receivers.",
  "On the JVM they are leading parameters (context, then receiver, then the rest), so Java passes them by hand and adding one breaks binary compatibility.",
  "Avoid the parts that aren't stable yet: explicit context arguments and callable references to such functions."
 ],
 "quiz": [
  {"q": "What happens with this code?\n\n```kotlin\n@OptIn(ExperimentalContracts::class)\nfun PaymentEvent.isCaptured(): Boolean {\n    contract { returns(true) implies (this@isCaptured is Captured) }\n    return this is Captured || this is Refunded\n}\n\nif (event.isCaptured()) println(event.amountMinor)\n```",
   "options": ["A compile error: the body doesn't match the contract", "A compiler warning about an unsound contract", "It compiles; for a `Refunded` event the smart cast fails at run time with `ClassCastException`", "It compiles, and the smart cast is skipped when the contract is wrong"],
   "answer": 2, "why": "The compiler trusts `returns ... implies` without checking it, so `event.amountMinor` compiles as if `event` were a `Captured`. At run time the JVM checks the cast it was given, and a `Refunded` is not a `Captured`. K2 warns only about some `callsInPlace` mistakes, never about `implies`."},
  {"q": "Which contract makes this compile?\n\n```kotlin\nval total: Long\nwithLedgerLock { total = ledger.sum() }\nprintln(total)\n```",
   "options": ["`callsInPlace(block, InvocationKind.EXACTLY_ONCE)` in `withLedgerLock`", "`callsInPlace(block, InvocationKind.AT_MOST_ONCE)`", "No contract: making `withLedgerLock` inline is enough", "`returns() implies (block != null)`"],
   "answer": 0, "why": "A `val` must be assigned exactly once, and only `EXACTLY_ONCE` tells the compiler the assignment happens once, during the call. `AT_MOST_ONCE` allows zero runs, so `total` might be unassigned. Inline alone says nothing about how many times the body calls `block`: without the contract you get `'val' cannot be reassigned.`"},
  {"q": "How does Java call `context(audit: AuditLog) fun note(line: String)`?",
   "options": ["`note(line)`, and the audit log comes from a ThreadLocal", "`note(audit, line)`: the context parameter is the first JVM parameter", "`note(line, audit)`", "It can't: context parameters are Kotlin-only"],
   "answer": 1, "why": "On the JVM, context parameters become ordinary parameters placed first, then the extension receiver, then the value parameters. Java has no context, so it passes the value itself."},
  {"q": "Inside `context(primaryLog, backupLog) { note(\"x\") }`, both are `AuditLog`. What does the compiler do?",
   "options": ["Uses `primaryLog`, the first one listed", "Uses `backupLog`, the last one listed", "Passes both and lets `note` choose", "Reports `multiple potential context arguments for 'audit: AuditLog' in scope.`"],
   "answer": 3, "why": "Context arguments are resolved by type. Two compatible values at the same scope level are an ambiguity, and the compiler refuses to guess. Give the two roles different types, or open the contexts in nested blocks so that one is nearer."},
  {"q": "From lesson 1: a test class was compiled against the stub of the public inline function `ensure`. You fix `ensure` and recompile only `src/main`. What does the old test class run when it calls `ensure`?",
   "options": ["Your new body, because it's on the classpath", "The stub's body, copied into the test class when the test was compiled", "Nothing: it fails with `NoSuchMethodError`", "Whichever version the class loader finds first"],
   "answer": 1, "why": "An inline body is pasted into the caller at the caller's compile time, so the old test class holds its own copy of the stub. That's why the lab's tests call `Callers.ensuring`, an ordinary function compiled together with your code.",
   "from": "kt-01"}
 ],
 "flashcards": [
  {"front": "What is a Kotlin contract?", "back": "A `contract { }` block, the first statement of a function, that tells the compiler something it can't infer: how a lambda is called, or what a normal return implies."},
  {"front": "What does `returns() implies (x != null)` give the caller?", "back": "A smart cast: after the call returns normally, the compiler treats `x` as non-null."},
  {"front": "What does `callsInPlace(block, EXACTLY_ONCE)` allow in the caller?", "back": "Initializing a `val` inside the lambda, because the compiler now knows the block runs exactly once during the call."},
  {"front": "Does the compiler verify a contract against the function body?", "back": "No. It trusts it. A lying `returns(true) implies (this is Captured)` compiles and fails at run time with `ClassCastException`."},
  {"front": "What opt-in do contracts need in Kotlin 2.4?", "back": "`@OptIn(ExperimentalContracts::class)`. They are still Experimental. No compiler flag is needed."},
  {"front": "Where can a context argument come from?", "back": "From the caller's surroundings, matched by type: an enclosing function's context parameter, a `context(a, b) { }` block, or an implicit receiver such as `with(x) { }`."},
  {"front": "JVM signature of `context(l: Logger, tx: TxId) fun Payment.authorize(m: String): Boolean`?", "back": "`static boolean authorize(Logger, TxId, Payment, String)`: context parameters, then the receiver, then the value parameters."}
 ],
 "terms": [
  {"term": "Smart cast", "plain": "The compiler treating a variable as a narrower type after a check proves it, such as `String?` to `String` after `!= null`."},
  {"term": "Contract", "plain": "A `contract { }` block that states a fact about a function's behavior for callers to rely on. The compiler trusts it."},
  {"term": "callsInPlace", "plain": "A contract effect: the lambda runs during the call (not stored), a given number of times."},
  {"term": "returns implies", "plain": "A contract effect: if the function returns (or returns a given value), a condition holds."},
  {"term": "Context parameter", "plain": "A parameter declared in `context(...)` that callers don't write; the compiler fills it by type from the surroundings."},
  {"term": "Context argument", "plain": "The value the compiler finds and passes for a context parameter at a call site."},
  {"term": "Opt-in", "plain": "`@OptIn(...)`: your explicit agreement to use an Experimental API that may change."}
 ],
 "explain_back": {
  "prompt": "Explain to a teammate why `ensure(req.currency != null, \"CURRENCY_MISSING\") { ... }` followed by `req.currency.uppercase()` compiles only with a contract, and what the compiler does and doesn't check about that contract.",
  "answer": "The compiler decides smart casts inside one function at a time. It doesn't read the body of `ensure` when it compiles the caller, so without help it has no idea that `ensure` only returns when the condition is true, and `req.currency` stays a `String?`. The contract `returns() implies condition`, written as the first statement of `ensure`, is a promise stored in the Kotlin metadata: if this function returns normally, the condition holds. When the caller is compiled, the compiler reads that promise and treats `currency` as non-null after the call. It doesn't verify the promise. If the body of `ensure` returned without checking, the code would still compile and fail later at run time. The compiler checks only the form: the opt-in is there, the block is the first statement, and for `callsInPlace` it warns about some obvious misuse such as calling the lambda twice or storing it. So the body should be as simple as the promise, here a single `if (!condition) throw`."
 },
 "deeper": {
  "minutes": 8,
  "body": "Kotlin 2.4.0 added one more Experimental contract effect, `returnsResultOf()`, to help the new unused-return-value checker. It needs the flag `-Xallow-returns-result-of`, and the release notes warn that using it \"produces pre-release binaries that earlier Kotlin compiler versions can't read\". Keep it out of libraries that others consume.\n\nThe extended contracts from Kotlin 2.2.20 behave in an interesting way on the 2.4.21 compiler. Their old `-X` flags (`-Xallow-contracts-on-more-functions` and friends) now print `the argument '...' is redundant for the current language version 2.4.`, and a generic `returns(true) implies (this is Ok<T>)` or a `holdsIn` contract compiles without any flag. So they appear to be enabled by default from language version 2.3. They still need their opt-ins, though: `returnsNotNull()` without `@OptIn(ExperimentalExtendedContracts::class)` is an opt-in error.\n\nIf you're migrating from context receivers, three differences bite. Context parameters must be named (or `_`), and a context parameter is not a receiver in the body, so `log(\"x\")` becomes `logger.log(\"x\")`. `this@Logger` is gone; use the name or `contextOf<Logger>()`. And classes can't declare a context any more, only functions and properties.\n\nFinally, a design note. The docs mention \"simplified dependency injection\" as a use. Treat that carefully in a CDI application. A context parameter is resolved at compile time, at each call site, from what is lexically in scope. CDI resolves beans at startup, from the whole application. They answer different questions: context parameters suit per-call values, and CDI suits long-lived services."
 },
 "sources": [
  {"title": "Context parameters (Kotlin docs)", "url": "https://kotlinlang.org/docs/context-parameters.html"},
  {"title": "What's new in Kotlin 2.4.0", "url": "https://kotlinlang.org/docs/whatsnew24.html"},
  {"title": "KEEP-0139: Kotlin contracts", "url": "https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0139-kotlin-contracts.md"},
  {"title": "KEEP-0367: context parameters", "url": "https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0367-context-parameters.md"},
  {"title": "What's new in Kotlin 2.3.20", "url": "https://kotlinlang.org/docs/whatsnew2320.html"}
 ]
}
out = ROOT / "content/lessons/kt-05.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
