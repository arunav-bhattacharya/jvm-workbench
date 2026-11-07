import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/modernjava/src"
P = "kotlin/workbench/modernjava/l04"
D = "java/workbench/modernjava/l04/demo"
K = "kotlin/workbench/modernjava/l04/demo"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :modernjava:demo -Pmain=workbench.modernjava.l04.demo."


def demo(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{D}/{name}.java"),
            "run": DEMO + name, "file": f"{lab}/demo/{D}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
                    "run": DEMO + name + "Kt", "file": f"{lab}/demo/{K}/{name}.kt"}}


FIG = (
    '<svg viewBox="0 0 680 260" role="img" aria-label="The expression problem as a grid: with methods on each class, adding a type is local and '
    'adding an operation edits every class; with sealed types and switches, adding an operation is local and adding a type breaks every switch, which the compiler lists">'
    '<text class="t t-a" x="300" y="34" text-anchor="middle">methods on each class</text>'
    '<text class="t t-a" x="545" y="34" text-anchor="middle">sealed types + switch</text>'
    '<text class="t" x="92" y="92" text-anchor="middle">add a type</text>'
    '<text class="t-s t-m" x="92" y="112" text-anchor="middle">e.g. Chargeback</text>'
    '<text class="t" x="92" y="182" text-anchor="middle">add an operation</text>'
    '<text class="t-s t-m" x="92" y="202" text-anchor="middle">e.g. riskScore</text>'
    '<rect class="box-ok" x="190" y="55" width="220" height="72" rx="8"/>'
    '<text class="t" x="300" y="86" text-anchor="middle">one new class</text>'
    '<text class="t-s t-m" x="300" y="108" text-anchor="middle">nothing else changes</text>'
    '<rect class="box-b" x="430" y="55" width="230" height="72" rx="8"/>'
    '<text class="t" x="545" y="86" text-anchor="middle">every switch breaks</text>'
    '<text class="t-s t-m" x="545" y="108" text-anchor="middle">the compiler lists each one</text>'
    '<rect class="box-bad" x="190" y="145" width="220" height="72" rx="8"/>'
    '<text class="t" x="300" y="176" text-anchor="middle">edit every class</text>'
    '<text class="t-s t-m" x="300" y="198" text-anchor="middle">or every Visitor</text>'
    '<rect class="box-ok" x="430" y="145" width="230" height="72" rx="8"/>'
    '<text class="t" x="545" y="176" text-anchor="middle">one new function</text>'
    '<text class="t-s t-m" x="545" y="198" text-anchor="middle">nothing else changes</text>'
    '<text class="t-s t-m" x="425" y="246" text-anchor="middle">payment data gains operations far more often than it gains types</text>'
    '</svg>'
)

S1 = """Here is how a card issuer's reply often arrives in a service: one class, every field optional.

```java
public class IssuerReplyDto {
    String status;               // "APPROVED", "DECLINED" or "SOFT_DECLINE"
    String authCode;             // only when approved
    Long amountMinor;            // only when approved
    String declineCode;          // only when declined
    Long retryAfterSeconds;      // only on a soft decline
}
```

```kotlin
data class IssuerReplyDto(
    val status: String?,         // "APPROVED", "DECLINED" or "SOFT_DECLINE"
    val authCode: String?,       // only when approved
    val amountMinor: Long?,      // only when approved
    val declineCode: String?,    // only when declined
    val retryAfterSeconds: Long?,// only on a soft decline
)
```

Count what this type allows. Three statuses, times four optional fields that are each set or null, gives 48 shapes. Three of them make sense. The other 45, such as approved with no auth code, or approved with a decline code, can be built, serialized and passed around, and the comments are the only place that says which fields go together. Every consumer has to re-check that, and one of them won't: the capture job sends `null` as the auth code.

Model the three outcomes instead, each with only its own fields:

```java
public sealed interface AuthResult permits Approved, Declined, RetryLater {}
public record Approved(AuthCode code, long amountMinor) implements AuthResult {}
public record Declined(DeclineReason reason) implements AuthResult {}
public record RetryLater(Duration after) implements AuthResult {}
```

```kotlin
sealed interface AuthResult {
    data class Approved(val code: AuthCode, val amountMinor: Long) : AuthResult
    data class Declined(val reason: DeclineReason) : AuthResult
    data class RetryLater(val after: Duration) : AuthResult
}
```

Now there are three shapes, and "approved with a decline code" can't even be written down. The checks that are left move into the constructors: an `AuthCode` is six letters or digits, an approved amount is positive. That is what "make illegal states unrepresentable" means in practice. The types and the canonical constructors refuse the bad values once, so no consumer has to.

Brian Goetz calls this style data-oriented programming: model the data as immutable records and sealed types, and write the logic as functions over them. He wrote it up in a 2022 InfoQ article, "Data Oriented Programming in Java". His 2019 design note on records and sealed types gives the vocabulary. A record is a product type: an `Approved` is a code *and* an amount, and its API models "the state, the whole state, and nothing but the state". A sealed interface is a sum type, "a discriminated union of a fixed set of types": an `AuthResult` is approved *or* declined *or* retry-later. Most messages a payment service handles have exactly this shape: a few alternatives, each a fixed set of fields."""

S2 = """The sealed model only helps if untrusted data can't get in around it. So the service converts raw input into the model in exactly one place, at its edge: the REST resource, the Kafka deserializer, the client for the issuer's API. Everything behind the edge works only with model values.

```java
static Parsed parse(IssuerReplyDto raw) {
    try {
        return switch (raw.status) {
            case "APPROVED" -> raw.authCode == null || raw.amountMinor == null
                    ? new Rejected("approved without a code or an amount")
                    : new Ok(new Approved(new AuthCode(raw.authCode), raw.amountMinor));
            case "DECLINED" -> new Ok(new Declined(DeclineReason.fromCode(raw.declineCode)));
            case "SOFT_DECLINE" -> raw.retryAfterSeconds == null
                    ? new Rejected("soft decline without retry-after")
                    : new Ok(new RetryLater(Duration.ofSeconds(raw.retryAfterSeconds)));
            case null, default -> new Rejected("unknown status: " + raw.status);
        };
    } catch (IllegalArgumentException e) {
        return new Rejected(e.getMessage());          // a constructor refused a value
    }
}
```

```kotlin
fun parse(raw: IssuerReplyDto): Parsed = try {
    when (raw.status) {
        "APPROVED" ->
            if (raw.authCode == null || raw.amountMinor == null) Rejected("approved without a code or an amount")
            else Ok(Approved(AuthCode(raw.authCode), raw.amountMinor))
        "DECLINED" -> Ok(Declined(DeclineReason.fromCode(raw.declineCode)))
        "SOFT_DECLINE" ->
            if (raw.retryAfterSeconds == null) Rejected("soft decline without retry-after")
            else Ok(RetryLater(Duration.ofSeconds(raw.retryAfterSeconds)))
        else -> Rejected("unknown status: ${raw.status}")
    }
} catch (e: IllegalArgumentException) {
    Rejected(e.message ?: "invalid reply")            // a constructor refused a value
}
```

Two details make this work. The function never throws. A reply the model refuses comes back as `Rejected` with a reason, and the caller decides what that means (log it, alert, fail the payment safely) instead of an exception escaping from somewhere inside a mapper. And the constructors stay the final check: `parse` doesn't repeat the auth-code rule, it calls `new AuthCode(...)` and turns the refusal into a `Rejected`.

Behind the edge, nothing re-validates. A method that takes an `Approved` knows it has a valid code and a positive amount, because no other kind of `Approved` can exist. Records, data classes and sealed types make this cheap: the model is a dozen lines, the edge is one function, and the compiler checks every switch in between. The lab builds exactly this for the issuer reply, in Kotlin, including the case the snippets above skip: an approved reply that also carries a decline code contradicts itself, and must be rejected."""

S3 = """In classic object-oriented design, behavior lives in the classes: `result.customerMessage()`, `result.nextStep()`, `result.metricTag()`, each written three times across `Approved`, `Declined` and `RetryLater`. Data-oriented code keeps the records plain and writes each operation as one function with a switch:

```java
static String customerMessage(AuthResult r) {
    return switch (r) {
        case Approved a -> "Payment approved.";
        case Declined(var reason) when reason == DeclineReason.INSUFFICIENT_FUNDS -> "Not enough funds. Try another card.";
        case Declined d -> "Payment declined.";
        case RetryLater(var after) -> "Your bank is busy. We'll try again in " + after.toSeconds() + " seconds.";
    };
}
```

```kotlin
fun customerMessage(r: AuthResult): String = when (r) {
    is Approved -> "Payment approved."
    is Declined if r.reason == DeclineReason.INSUFFICIENT_FUNDS -> "Not enough funds. Try another card."
    is Declined -> "Payment declined."
    is RetryLater -> "Your bank is busy. We'll try again in ${r.after.seconds} seconds."
}
```

Everything about customer messages sits in one function, the records don't depend on your translation code, and the next operation (a metrics tag, a ledger posting) is a new function that touches nothing else.

That is one side of the expression problem, which *Visitor, Iterator, Mediator and Memento* in the patterns track introduced. With methods on the classes, adding a type is local and adding an operation means editing every class. With sealed types and switches it is the other way round: a new operation is one function, and a new type breaks every switch until you handle it. Neither style makes both changes cheap, so choose by the change you expect more often.

For payment data (authorization results, events, ledger entries, scheme messages) the set of types changes rarely and new operations keep arriving, so the data-oriented side wins. For open hierarchies that other teams extend, such as fraud checks or the `PartnerMethod` branch from lesson 2, keep an interface with methods. And behavior that is about the value itself, like `Money.plus`, belongs on the record. Keep business decisions out of the records; small methods that compute with the value itself can stay."""

S4 = """Records are identity objects, and lesson 1 showed what that means. `==` compares references, you can lock on a record, and an array of `Money` is an array of references to separate heap objects. Project Valhalla's first feature lets a class give up identity:

```java
value record Money(long minor, String currency) {}   // JDK 28 early-access builds, --enable-preview
```

```kotlin
@JvmInline
value class AuthCode(val value: String)               // Kotlin today: one property, compiled away
```

The status is often misreported, so here it is precisely. JEP 401, Value Objects (Preview), together with JEP 539 (strict field initialization in the JVM), was integrated into the JDK mainline on 31 July 2026. JDK 27 had already branched off, so the feature ships in JDK 28, scheduled for 23 March 2027, and early-access builds of JDK 28 exist now. It is a preview: it needs `--enable-preview` and can still change. JDK 25, 26 and 27 don't have it.

The Valhalla docs define value objects as immutable objects that lack identity, "distinguished solely by the values of their fields". `==` compares two value objects by their state, and identity operations such as synchronization fail with an exception. In return, the JVM may store them flat. In JDK 28 that means two optimizations. Flattening stores a value's fields directly inside the field or array element that holds it, with no separate object and no pointer. Scalarization lets JIT-compiled code keep the fields in registers and skip the allocation. Both have limits the docs spell out. Flattened values are read and written atomically and must allow null, so value objects with 64 bits or more of field data "cannot normally be flattened". Scalarization only happens once C2, the JIT's optimizing compiler, has compiled the code. Polymorphic variables, including those in generic APIs, aren't flattened. By the first rule, the `Money` above would not normally be flattened, since its `long` alone is 64 bits. Small records of a few `int` or `short` fields gain first.

With the preview on, 28 JDK classes become value classes, among them `Integer`, `Long`, `Optional`, `LocalDate`, `Instant` and `Duration`. Synchronizing on an `Integer`, or putting one in a `WeakReference`, then throws `IdentityException`. Null-restricted types, the other thing people expect from Valhalla, are still draft JEPs.

Kotlin's `@JvmInline value class` is an older, different trick. It holds one property and is erased to that property where the compiler can: a function taking an `AuthCode` compiles to one taking a `String`, under a mangled name. It is boxed when used as a generic `T`, an interface or a nullable type. Kotlin's design notes say the annotation leaves room for real Valhalla value classes later, but no such mode has shipped, so a Kotlin data class on JDK 28 is still an identity object.

What to do today: don't depend on the identity of your records. No `==` between them, no `synchronized` on them, no identity-keyed maps. Then adopting `value` later is a one-word change."""

L = {
 "id": "dop-04",
 "title": "Data-oriented programming, and Project Valhalla",
 "minutes": 40,
 "goal": "By the end you can model an issuer reply so that contradictory states can't be built, parse untrusted input into that model at the edge, keep business operations in functions apart from the data, and say exactly what Project Valhalla has shipped and what it means for your records.",
 "warmup": {
  "q": "In which JDK can you compile `value record Point(int x, int y) {}` today?",
  "options": ["JDK 21: records are value types already, so `value` is just allowed",
              "JDK 25 LTS, with `--enable-preview`",
              "JDK 27, where value classes became final",
              "Only early-access builds of JDK 28, with `--enable-preview`"],
  "answer": 3,
  "why": "JEP 401 (value objects, preview) was integrated into the JDK mainline after JDK 27 had branched off, so it arrives in JDK 28, scheduled for March 2027; early-access builds have it now. JDK 25, 26 and 27 don't. Records are identity objects on every released JDK: `==` compares references, and you can synchronize on them."
 },
 "sections": [
  {
   "h": "Make illegal states unrepresentable",
   "body": S1,
   "try": {
    "title": "Count the shapes, then build a bad one",
    "minutes": 4,
    "steps": [
     "Run `IllegalStates` (or `IllegalStatesKt`). Read the `DTO consumer` line: what will the capture job send to the issuer?",
     "In the Java demo, try to build an `Approved` with a decline code. There is no constructor for it: the shape doesn't exist.",
     "In the Kotlin twin, change `AuthResult.Approved(\"\", 4_200)` to `AuthResult.Approved(null, 4_200)` and run. Which tool stopped you this time?"
    ],
    "code": demo("IllegalStates"),
    "expect": "Both print `shapes the DTO allows: 48, shapes that make sense: 3`, then `DTO consumer: capture 4200 with auth code null`: nothing stopped an approved reply with no code. The sealed model refuses it (`authCode is required`) and the valid approval prints `capture 4200 with auth code A1B2C3`. In Kotlin, `Approved(null, 4_200)` doesn't compile at all, because the property is a non-null `String`: the type system did the constructor's job."
   },
   "refs": [
    {"title": "Brian Goetz, Data Oriented Programming in Java (InfoQ, 2022)", "url": "https://www.infoq.com/articles/data-oriented-programming-java/", "kind": "read"}
   ]
  },
  {
   "h": "Parse at the edge, then trust the types",
   "body": S2,
   "try": {
    "title": "Predict what the edge does",
    "minutes": 3,
    "steps": [
     "The issuer sends `status: \"APPROVED \"` (with a trailing space), auth code `A1B2C3` and amount 4200. Which arm of `parse` takes it, and what does the capture job see?",
     "It sends a soft decline with `retryAfterSeconds: 0`. Does `parse` or a constructor produce the result?",
     "A teammate adds `if (approved.amountMinor() <= 0) return;` inside the capture job. Can that line ever run?"
    ],
    "expect": "The trailing space matches no status string, so `case null, default` returns `Rejected(\"unknown status: APPROVED \")` and the capture job never sees the reply: a strict edge turns a sloppy reply into a visible rejection instead of a capture with bad data. The zero wait gets past `parse`, because the field isn't null, and is refused by the `RetryLater` constructor once it has the range check (as the lab's does); the `catch` turns that refusal into `Rejected`. The teammate's line is dead code: an `Approved` with a non-positive amount can't be built, so the check can never be true."
   }
  },
  {
   "h": "Operations live outside the data",
   "body": S3,
   "figure": {"svg": FIG, "caption": "The expression problem: each style makes one kind of change local and the other kind expensive. Sealed types at least make the compiler find every place to change."},
   "try": {
    "title": "Pay both costs",
    "minutes": 6,
    "steps": [
     "Run `ExpressionProblem` (or `ExpressionProblemKt`).",
     "Write operation 3 where the comment says: `isCustomerFacing`, true for charges and refunds, false for fees. How many existing lines did you change?",
     "Add the `Chargeback` record (in Java, add it to `permits` too) and run. List the places the compiler asks you to change.",
     "Decide what a chargeback does to the balance and to the statement line, and handle it in each function."
    ],
    "code": demo("ExpressionProblem"),
    "expect": "The demo prints three statement lines and `balance 7465`. Adding `isCustomerFacing` changed no existing line. Adding `Chargeback` makes javac report each switch over `LedgerEntry` (`balanceDelta`, `statementLine` and your new one) with `does not cover all possible input values`, and kotlinc asks for `the 'is Chargeback' branch` in each `when`. A new operation cost one function; a new type cost one edit per operation, and the compiler found every one."
   }
  },
  {
   "h": "Project Valhalla: what has shipped",
   "body": S4,
   "try": {
    "title": "Look at identity, then at a Kotlin value class",
    "minutes": 4,
    "steps": [
     "Run `IdentityDemo`. Which of its lines would change if `Money` were a value record?",
     "Run `IdentityDemoKt`.",
     "From `labs/`, run `javap -p modernjava/build/classes/kotlin/demo/workbench/modernjava/l04/demo/IdentityDemoKt.class`. What parameter type does `describeIban` take?"
    ],
    "code": demo("IdentityDemo"),
    "expect": "`equals: true, ==: false`, different identity hash codes, a successful `synchronized`, `Integer 127 == 127: true, 128 == 128: false`, and `ledger[0] == ledger[2]: true, ledger[0] == ledger[1]: false`. With a value record, `==` would compare state, so `a == b` and `ledger[0] == ledger[1]` would be true, and `synchronized` would be refused. In Kotlin, `javap` shows `describeIban-JSx-I4w(java.lang.String)`: the value class is erased to a `String` under a mangled name, and the demo shows it boxed back into an `Iban` when stored as `Any` or in a `List`."
   },
   "refs": [
    {"title": "JEP 401: Value Objects (Preview)", "url": "https://openjdk.org/jeps/401", "kind": "read"},
    {"title": "Inline value classes (Kotlin docs)", "url": "https://kotlinlang.org/docs/inline-classes.html", "kind": "docs"}
   ]
  }
 ],
 "analogy": "Data-oriented code works like a payment network's message specification. A message is just fields with fixed meanings, the spec says which fields each message type carries, and every processor that reads the messages keeps its own logic (routing, risk, settlement) in its own system. Nobody ships behavior inside the message. A new processing step is easy to add, while a new message type means every processor updates its handling. The analogy breaks on enforcement: a spec is a document that a sender can violate, while a sealed type with validating constructors makes the bad message impossible to build in the first place.",
 "in_your_world": "Look at the DTOs your Quarkus REST clients and Kafka consumers map into. Many are one class per endpoint, with a status field and a dozen nullable fields, and the rules about which fields go together live in `if` statements spread across services. Pick the one that causes the most defensive code (usually the issuer or acquirer response) and put a sealed model behind it. The DTO stays at the edge, where your JSON mapper keeps filling it. One `parse` function turns it into the model. Everything downstream, from the capture job to the retry scheduler to the Temporal workflow waiting for a soft decline to clear, switches over three records instead of re-checking strings. Valhalla needs nothing from you yet: keep your records free of identity tricks, and look again when JDK 28 is final and your frameworks support it.",
 "mistake": "The common mistake is building the sealed model and then sneaking the old states back in: a shared `details` record with nullable fields inside each outcome, or a `status` enum stored next to the sealed type \"for convenience\". Now a `Declined` can carry `status = APPROVED`, and every consumer has to wonder which one is true. If two facts must agree, derive one from the other (a method computed from the type) or delete it. The opposite mistake is sealing an extension point, such as the interface partner teams implement, to get exhaustive switches; then every new partner needs a change in your module. Seal closed domains and leave plug-in points open.",
 "compare": {
  "title": "One model and one operation in Java and Kotlin",
  "java": {"title": "AuthResult.java", "src": "public record AuthCode(String value) {\n    public AuthCode {\n        if (value == null || !value.matches(\"[A-Z0-9]{6}\")) throw new IllegalArgumentException(\"bad auth code\");\n    }\n}\n\npublic sealed interface AuthResult permits Approved, Declined, RetryLater {}\npublic record Approved(AuthCode code, long amountMinor) implements AuthResult {\n    public Approved {\n        if (amountMinor <= 0) throw new IllegalArgumentException(\"amount must be positive\");\n    }\n}\npublic record Declined(DeclineReason reason) implements AuthResult {}\npublic record RetryLater(Duration after) implements AuthResult {}\n\nstatic String customerMessage(AuthResult r) {\n    return switch (r) {\n        case Approved a -> \"Payment approved.\";\n        case Declined(var reason) when reason == DeclineReason.SUSPECTED_FRAUD -> \"Payment declined. Please contact your bank.\";\n        case Declined d -> \"Payment declined.\";\n        case RetryLater(var after) -> \"Your bank is busy. We'll try again in \" + after.toSeconds() + \" seconds.\";\n    };\n}"},
  "kotlin": {"title": "AuthResult.kt", "src": "@JvmInline\nvalue class AuthCode(val value: String) {\n    init { require(value.matches(Regex(\"[A-Z0-9]{6}\"))) { \"bad auth code\" } }\n}\n\nsealed interface AuthResult {\n    data class Approved(val code: AuthCode, val amountMinor: Long) : AuthResult {\n        init { require(amountMinor > 0) { \"amount must be positive\" } }\n    }\n    data class Declined(val reason: DeclineReason) : AuthResult\n    data class RetryLater(val after: Duration) : AuthResult\n}\n\nfun customerMessage(r: AuthResult): String = when (r) {\n    is AuthResult.Approved -> \"Payment approved.\"\n    is AuthResult.Declined if r.reason == DeclineReason.SUSPECTED_FRAUD -> \"Payment declined. Please contact your bank.\"\n    is AuthResult.Declined -> \"Payment declined.\"\n    is AuthResult.RetryLater -> \"Your bank is busy. We'll try again in ${r.after.seconds} seconds.\"\n}"},
  "note": "The design is identical: a closed set of outcomes, each with only its own fields, constructors that refuse bad values, and an operation written as one exhaustive switch outside the data. Two things differ. Java's switch takes `Declined` apart in the label (`Declined(var reason)`), while Kotlin tests the type and reads `r.reason` after a smart cast. And `AuthCode` is a record in Java, which is a full object with identity, while Kotlin's `@JvmInline value class` is usually erased to a plain `String`. With JDK 28's preview, Java could write `value record AuthCode(String value)` and give up identity at the JVM level, which is something Kotlin's value class doesn't do today."
 },
 "worked": {
  "title": "From a payout webhook DTO to a closed model",
  "steps": [
   {"say": "A payout provider calls your webhook with this body. Its docs say: a `PAID` event has an arrival date, a `FAILED` event has a reason, and a `RETURNED` event has the returned amount. The DTO encodes none of that.",
    "code": "public record PayoutWebhookDto(String type, String payoutId, LocalDate arrivalDate,\n                               String failureReason, Long returnedMinor) {}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "data class PayoutWebhookDto(val type: String?, val payoutId: String?, val arrivalDate: LocalDate?,\n                            val failureReason: String?, val returnedMinor: Long?)"},
   {"say": "Write one record per row of the provider's docs. Every field is required, so the record can't be half a `PAID` event.",
    "code": "// 1. one record per valid combination\npublic sealed interface PayoutEvent permits Paid, PayoutFailed, Returned {}\npublic record Paid(String payoutId, LocalDate arrivalDate) implements PayoutEvent {}\npublic record PayoutFailed(String payoutId, String reason) implements PayoutEvent {}\npublic record Returned(String payoutId, long amountMinor) implements PayoutEvent {\n    public Returned {\n        if (amountMinor <= 0) throw new IllegalArgumentException(\"returned amount must be positive\");\n    }\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "// 1. one class per valid combination, with non-null properties\nsealed interface PayoutEvent {\n    data class Paid(val payoutId: String, val arrivalDate: LocalDate) : PayoutEvent\n    data class Failed(val payoutId: String, val reason: String) : PayoutEvent\n    data class Returned(val payoutId: String, val amountMinor: Long) : PayoutEvent {\n        init { require(amountMinor > 0) { \"returned amount must be positive\" } }\n    }\n}"},
   {"say": "Write the edge. It is the only code that looks at the DTO, and it checks that each type carries its own field. A null where the docs promise a value becomes a clear error here, not a `NullPointerException` three services later.",
    "code": "// 2. the edge: DTO in, model out\nstatic PayoutEvent toEvent(PayoutWebhookDto d) {\n    Objects.requireNonNull(d.payoutId(), \"payoutId\");\n    return switch (d.type()) {\n        case \"PAID\" -> new Paid(d.payoutId(), Objects.requireNonNull(d.arrivalDate(), \"arrivalDate\"));\n        case \"FAILED\" -> new PayoutFailed(d.payoutId(), Objects.requireNonNull(d.failureReason(), \"failureReason\"));\n        case \"RETURNED\" -> new Returned(d.payoutId(), Objects.requireNonNull(d.returnedMinor(), \"returnedMinor\"));\n        case null, default -> throw new IllegalArgumentException(\"unknown payout event: \" + d.type());\n    };\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "// 2. the edge: DTO in, model out\nfun toEvent(d: PayoutWebhookDto): PayoutEvent {\n    val id = requireNotNull(d.payoutId) { \"payoutId\" }\n    return when (d.type) {\n        \"PAID\" -> PayoutEvent.Paid(id, requireNotNull(d.arrivalDate) { \"arrivalDate\" })\n        \"FAILED\" -> PayoutEvent.Failed(id, requireNotNull(d.failureReason) { \"failureReason\" })\n        \"RETURNED\" -> PayoutEvent.Returned(id, requireNotNull(d.returnedMinor) { \"returnedMinor\" })\n        else -> throw IllegalArgumentException(\"unknown payout event: ${d.type}\")\n    }\n}"},
   {"say": "Now the consumer. The old one was thirty lines of `if (\"PAID\".equals(type) && arrivalDate != null)`. The new one is a switch with no default, so a new event type from the provider shows up as a compile error, not a silently ignored webhook.",
    "code": "// 3. behind the edge: trust the types\nstatic void apply(PayoutEvent e, Ledger ledger) {\n    switch (e) {\n        case Paid(var id, var date) -> ledger.markSettled(id, date);\n        case PayoutFailed(var id, var reason) -> ledger.reopen(id, reason);\n        case Returned(var id, long amount) -> ledger.credit(id, amount);\n    }\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "// 3. behind the edge: trust the types\nfun apply(e: PayoutEvent, ledger: Ledger) = when (e) {\n    is PayoutEvent.Paid -> ledger.markSettled(e.payoutId, e.arrivalDate)\n    is PayoutEvent.Failed -> ledger.reopen(e.payoutId, e.reason)\n    is PayoutEvent.Returned -> ledger.credit(e.payoutId, e.amountMinor)\n}"}
  ]
 },
 "lab": {
  "title": "Parse an issuer reply into a model with no illegal states",
  "minutes": 15,
  "files": [f"{lab}/main/{P}/AuthModel.kt", f"{lab}/main/{P}/IssuerReplies.kt"],
  "run": "./gradlew :modernjava:test --tests 'workbench.modernjava.l04.*'",
  "steps": [
   "Run the tests: all ten fail. This lab is in Kotlin. The model is in `AuthModel.kt` and the boundary and the operation are in `IssuerReplies.kt`.",
   "Make the model refuse what can't be real: write the `init` checks in `AuthCode`, `Approved` and `RetryLater` (TODO 1 to 3). Three tests should pass now.",
   "Write `parse` (TODO 4) as one `when` on the status. Let the constructors do their own checks, and turn their `IllegalArgumentException` into `Rejected`.",
   "Write `customerMessage` (TODO 5) as one `when` with guards and no `else`.",
   "When all ten pass, add `data class PartialApproval(val code: AuthCode, val approvedMinor: Long) : AuthResult` to the model and run `./gradlew :modernjava:compileKotlin`. Which function does kotlinc point at? Remove it again."
  ],
  "hints": [
   "A value class may have an `init` block: `init { require(Regex(\"[A-Z0-9]{6}\").matches(value)) { \"bad auth code: $value\" } }`.",
   "`Duration` is `Comparable`, so `after >= Duration.ofSeconds(1) && after <= Duration.ofHours(1)` works in Kotlin.",
   "Wrap the whole `when` in `try { ... } catch (e: IllegalArgumentException) { Rejected(e.message ?: \"invalid reply\") }`. `Duration.ofSeconds(0)` is fine; it is `RetryLater` that refuses it.",
   "After a branch like `raw.authCode == null -> Rejected(...)`, Kotlin smart-casts `raw.authCode` to `String` in the later branches, because it is a `val` of a class in the same module.",
   "A guard looks like `is Declined if result.reason == DeclineReason.SUSPECTED_FRAUD -> ...`."
  ],
  "done_when": "All ten tests in `AuthModelTest` pass."
 },
 "drill": {
  "title": "Model a webhook from memory",
  "minutes": 5,
  "prompt": "Close this page. A refund webhook has a `type` (`\"SUCCEEDED\"`, `\"FAILED\"` or `\"PENDING\"`), a `refundId`, and a `failureCode` that is present only when the refund failed. Write the sealed model in Java so that a failure can't lack its code, and a `parse(type, refundId, failureCode)` that throws `IllegalArgumentException` for an unknown or missing type. Then write the Kotlin version.",
  "answer": {"lang": "java", "src": "sealed interface RefundEvent permits Succeeded, Failed, Pending {}\nrecord Succeeded(String refundId) implements RefundEvent {}\nrecord Failed(String refundId, String failureCode) implements RefundEvent {\n    Failed { Objects.requireNonNull(failureCode, \"failureCode\"); }   // a failure always has a code\n}\nrecord Pending(String refundId) implements RefundEvent {}\n\nstatic RefundEvent parse(String type, String refundId, String failureCode) {\n    return switch (type) {\n        case \"SUCCEEDED\" -> new Succeeded(refundId);\n        case \"FAILED\" -> new Failed(refundId, failureCode);\n        case \"PENDING\" -> new Pending(refundId);\n        case null, default -> throw new IllegalArgumentException(\"unknown refund event: \" + type);\n    };\n}",
             "alt": {"lang": "kotlin", "src": "sealed interface RefundEvent {\n    data class Succeeded(val refundId: String) : RefundEvent\n    data class Failed(val refundId: String, val failureCode: String) : RefundEvent   // non-null: always has a code\n    data class Pending(val refundId: String) : RefundEvent\n}\n\nfun parse(type: String?, refundId: String, failureCode: String?): RefundEvent = when (type) {\n    \"SUCCEEDED\" -> RefundEvent.Succeeded(refundId)\n    \"FAILED\" -> RefundEvent.Failed(refundId, requireNotNull(failureCode) { \"failureCode\" })\n    \"PENDING\" -> RefundEvent.Pending(refundId)\n    else -> throw IllegalArgumentException(\"unknown refund event: $type\")\n}"}}
 },
 "recap": [
  "Model each valid combination as its own record under a sealed interface, and check values in the constructors. A shape that can't be written down can't reach your code.",
  "Records are product types (this and that) and sealed interfaces are sum types (this or that). Most payment messages are a few alternatives, each a fixed set of fields.",
  "Parse untrusted input into the model once, at the edge, and return a result instead of throwing. Behind the edge, trust the types.",
  "Write business operations as functions that switch over the data. A new operation is one function; a new type breaks every switch, and the compiler lists them.",
  "Keep interfaces with methods for open hierarchies that others extend, and keep methods about the value itself on the record.",
  "Valhalla's value objects are a preview feature of JDK 28, not of 25, 26 or 27. Records are identity objects, so don't depend on their identity."
 ],
 "quiz": [
  {"q": "Your issuer DTO has a `status` and four nullable fields, and the issuer's docs list three valid combinations. What does a sealed model with three records give you that careful validation in every consumer doesn't?",
   "options": ["Faster JSON mapping", "Invalid combinations can't be constructed, so no consumer can receive one", "Nothing, as long as every consumer validates", "Smaller objects on the heap"],
   "answer": 1, "why": "With the sealed model the bad shapes don't exist, and the constructors refuse bad values once. Validating in every consumer works only until one consumer forgets, and the DTO keeps letting 45 nonsense shapes travel through the system. Neither the mapping speed nor the object size changes."},
  {"q": "Teams add a new fraud check every month, each in its own module, and every check answers `score(payment)`. Which design fits?",
   "options": ["An enum listing all checks", "A sealed interface of records, scored by one switch in the risk module", "An interface `FraudCheck` with a `score` method that each team implements", "A sealed interface whose switch has a `default` branch for checks it doesn't know"],
   "answer": 2, "why": "Here the set of types grows and the operation stays the same, and the types live in other modules: the object-oriented side of the expression problem. A sealed hierarchy would force every new check into the risk module and break its switch each month. A default would just hide the new checks."},
  {"q": "Which statement about Project Valhalla is accurate?",
   "options": ["JDK 25 LTS ships value classes as a preview", "Records became value objects in JDK 27", "Null-restricted types such as `String!` are final in JDK 28", "JEP 401 value objects are a preview feature of JDK 28; JDK 25, 26 and 27 don't have them"],
   "answer": 3, "why": "JEP 401 was integrated after JDK 27 branched off, so it ships in JDK 28 (scheduled for March 2027) as a preview. Records are still identity objects; `value record` is only legal under that preview. Null-restricted types are still draft JEPs."},
  {"q": "From *Visitor, Iterator, Mediator and Memento*: you replaced a Visitor over a sealed `Expr` with switch functions. Now a new node type, `Pow`, arrives. What does each design make you do?",
   "options": ["Visitor: add `visitPow` to the interface and to every visitor. Switches: every switch fails to compile until it handles `Pow`", "Visitor: nothing. Switches: nothing, because sealed types accept new records", "Visitor: one new class. Switches: one new function", "Both: only add the new record"],
   "answer": 0, "why": "Visitor and sealed switches sit on the same side of the expression problem: adding a type is the expensive change in both. The difference is that the switches need no `accept` and no visitor interface, and the compiler points at each switch to fix.",
   "from": "pat-10"},
  {"q": "`@JvmInline value class AuthCode(val value: String)` and `fun describe(c: AuthCode)`. What does the JVM see for `describe(code)` and for `listOf(code)`?",
   "options": ["Two ordinary `AuthCode` objects, like any class", "A `String` in both places", "`describe` takes a `String` under a mangled name, and the list holds a boxed `AuthCode`", "A Valhalla value object, flattened in both places"],
   "answer": 2, "why": "Kotlin erases the value class to its one property where it can, so `describe` compiles to something like `describe-XXXX(String)`. Used as a generic `T`, as in a `List`, it must be boxed into a real `AuthCode` object. None of this uses Valhalla: it is compile-time work, and it works on any JVM."}
 ],
 "flashcards": [
  {"front": "What does \"make illegal states unrepresentable\" mean in Java and Kotlin?", "back": "Model each valid combination as its own record (or data class) under a sealed type, and check values in the constructors, so an invalid value can't be built."},
  {"front": "Record and sealed interface, in algebraic terms?", "back": "A record is a product type: this and that. A sealed interface is a sum type: this or that."},
  {"front": "Where should untrusted input be validated?", "back": "Once, at the edge: one parse function turns the DTO into the model or a rejection. Code behind the edge trusts the types."},
  {"front": "With sealed types and switches, what does adding an operation cost? And a type?", "back": "An operation is one new function. A type breaks every exhaustive switch over the hierarchy, and the compiler lists each one."},
  {"front": "When do you keep an interface with methods instead of a sealed type?", "back": "For open hierarchies that other teams extend (plug-ins, partner methods, fraud checks), and for behavior about the value itself, like `Money.plus`."},
  {"front": "Which JDK has JEP 401 value objects?", "back": "JDK 28, as a preview feature (scheduled for March 2027; early-access builds now). Not JDK 25, 26 or 27."},
  {"front": "Why won't `value record Money(long minor, String currency)` normally be flattened in JDK 28?", "back": "Flattened values must be read and written atomically and allow null, so values with 64 bits or more of field data aren't normally flattened. The `long` alone is 64 bits."}
 ],
 "terms": [
  {"term": "Data-oriented programming", "plain": "Modeling data as immutable records and sealed types, and writing operations as functions that switch over them."},
  {"term": "Product type", "plain": "A type whose value is several values together, like a record: a code and an amount."},
  {"term": "Sum type", "plain": "A type whose value is one of a fixed set of alternatives, like a sealed interface: approved or declined."},
  {"term": "Illegal state", "plain": "A combination of field values that the domain says can't happen, such as approved with a decline code."},
  {"term": "Expression problem", "plain": "No design makes both new types and new operations cheap; you pick the side that matches how your code changes."},
  {"term": "Value object", "plain": "Valhalla's identity-free object: compared by its fields, and free for the JVM to copy or flatten. Preview in JDK 28."},
  {"term": "Flattening", "plain": "Storing a value object's fields directly inside the field or array that holds it, instead of a reference to a separate object."}
 ],
 "explain_back": {
  "prompt": "Your team lead asks: \"Should we move our payment model to records and sealed types now, or wait for Valhalla to make it fast?\" Answer in your own words: what the data-oriented style gives you today, where you would and wouldn't use it, and what Valhalla changes.",
  "answer": "The data-oriented style pays off today, with no new JDK: records and sealed types are final since JDK 17, and pattern switches since 21. Modeling each valid outcome as its own record means contradictory states can't be built, parsing at the edge means only valid values get in, and exhaustive switches mean the compiler tells us every place to update when a type is added. I'd use it for closed domain data such as authorization results, payment events and ledger entries, and keep ordinary interfaces for things other teams extend, like fraud checks. Valhalla changes performance and identity; it doesn't change this design. JEP 401 is only a preview in JDK 28, and even there, records like `Money` with a `long` and a reference wouldn't normally be flattened. So we shouldn't wait for it; we should just avoid depending on record identity, so that adding `value` later is easy."
 },
 "deeper": {
  "minutes": 8,
  "body": """Brian Goetz's January 2026 design note, "Data-Oriented Programming for Java: Beyond Records", says where Amber goes next. It calls records, sealed classes and record patterns "the first feature arc of 'data-oriented programming' for Java", and announces the next arc: *carrier classes* and carrier interfaces. A carrier class is a normal class with a record-style state description in its header. It would declare its own fields and need not be final, yet still have a canonical constructor, accessors and a deconstruction pattern, so data that is almost a record (one cached field, one derived value) doesn't force you back to writing everything by hand.

The note also describes reconstruction, the `with` expression from JEP 468, and points out how much its block resembles a compact constructor body: the component variables start with the old values, your block changes some of them, and the canonical constructor builds the new value, so the invariants still hold. Goetz explains that JEP 468 has been "on hold" until there was a path to extend it beyond records. The note also mentions an upcoming pattern assignment statement, for taking a record apart in an ordinary assignment.

None of this is in a JDK or a JEP you can use. The design direction is useful anyway: it says the language will keep making "model the data with records and sealed types, switch over it" cheaper, so code written in that style today is code the platform is moving toward.

On the Valhalla side, the next pieces on the project page are null-restricted storage, array enhancements, unifying primitives with classes, and a parametric JVM that can specialize generics. Only the first piece, value objects, has a JEP that has been integrated, and it is a preview."""
 },
 "sources": [
  {"title": "Brian Goetz, Data Oriented Programming in Java (InfoQ, 2022)", "url": "https://www.infoq.com/articles/data-oriented-programming-java/"},
  {"title": "Brian Goetz, Data Classes and Sealed Types for Java (2019)", "url": "https://github.com/openjdk/amber-docs/blob/master/site/design-notes/records-and-sealed-classes.md"},
  {"title": "Brian Goetz, Data-Oriented Programming for Java: Beyond Records (2026)", "url": "https://github.com/openjdk/amber-docs/blob/master/site/design-notes/beyond-records.md"},
  {"title": "Project Valhalla (OpenJDK)", "url": "https://openjdk.org/projects/valhalla/"},
  {"title": "Inline value classes (Kotlin docs)", "url": "https://kotlinlang.org/docs/inline-classes.html"}
 ]
}
out = ROOT / "content/lessons/dop-04.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
