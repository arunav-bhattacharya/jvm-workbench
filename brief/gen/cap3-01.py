import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/events/src"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :events:demo -Pmain=workbench.events.l01.demo."


def demo(pkg, name):
    """A Kotlin demo with its Java twin, both in workbench.events.l01.demo.<pkg>."""
    k = f"{lab}/demo/kotlin/workbench/events/l01/demo/{pkg}/{name}.kt"
    j = f"{lab}/demo/java/workbench/events/l01/demo/{pkg}/{name}Java.java"
    return {"lang": "kotlin", "title": f"{name}.kt", "src": read(k),
            "run": f"{DEMO}{pkg}.{name}Kt", "file": k,
            "alt": {"lang": "java", "title": f"{name}Java.java", "src": read(j),
                    "run": f"{DEMO}{pkg}.{name}Java", "file": j}}


FIG_PLAN = (
    '<svg viewBox="0 0 680 250" role="img" aria-label="The library you will build: raw Kafka fields go through parseEvent at the edge, '
    'which either produces a PaymentEvent from the sealed model or a Rejected result for the dead-letter topic. Events go to the EventBus '
    'of lesson 2 and on to the handlers. Lesson 3 adds the API that Kotlin and Java callers use to reach the bus.">'
    '<text class="t-s t-m" x="270" y="80" text-anchor="middle">lesson 1: the model and its edge</text>'
    '<rect class="box" x="10" y="95" width="110" height="54" rx="8"/>'
    '<text class="t" x="65" y="118" text-anchor="middle">Kafka record</text>'
    '<text class="t-s t-m" x="65" y="137" text-anchor="middle">raw fields</text>'
    '<line class="ln" x1="120" y1="122" x2="148" y2="122" marker-end="url(#arr)"/>'
    '<rect class="box-a" x="150" y="95" width="110" height="54" rx="8"/>'
    '<text class="t t-code" x="205" y="118" text-anchor="middle">parseEvent</text>'
    '<text class="t-s" x="205" y="137" text-anchor="middle">the edge</text>'
    '<line class="ln" x1="260" y1="122" x2="288" y2="122" marker-end="url(#arr)"/>'
    '<rect class="box-ok" x="290" y="95" width="120" height="54" rx="8"/>'
    '<text class="t t-code" x="350" y="118" text-anchor="middle">PaymentEvent</text>'
    '<text class="t-s" x="350" y="137" text-anchor="middle">sealed model</text>'
    '<line class="ln" x1="410" y1="122" x2="438" y2="122" marker-end="url(#arr)"/>'
    '<rect class="box-b" x="440" y="95" width="110" height="54" rx="8"/>'
    '<text class="t t-code" x="495" y="118" text-anchor="middle">EventBus</text>'
    '<text class="t-s" x="495" y="137" text-anchor="middle">lesson 2</text>'
    '<line class="ln" x1="550" y1="122" x2="578" y2="122" marker-end="url(#arr)"/>'
    '<rect class="box" x="580" y="95" width="90" height="54" rx="8"/>'
    '<text class="t" x="625" y="118" text-anchor="middle">handlers</text>'
    '<text class="t-s t-m" x="625" y="137" text-anchor="middle">ledger, audit</text>'
    '<line class="ln-bad" x1="205" y1="149" x2="205" y2="183" marker-end="url(#arr)"/>'
    '<rect class="box-bad" x="150" y="185" width="110" height="50" rx="8"/>'
    '<text class="t" x="205" y="206" text-anchor="middle">Rejected</text>'
    '<text class="t-s" x="205" y="224" text-anchor="middle">dead letter</text>'
    '<rect class="box-dim" x="420" y="10" width="150" height="50" rx="8"/>'
    '<text class="t" x="495" y="31" text-anchor="middle">API for callers</text>'
    '<text class="t-s" x="495" y="50" text-anchor="middle">lesson 3: Kotlin, Java</text>'
    '<line class="ln-d" x1="495" y1="60" x2="495" y2="93" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="350" y="175" text-anchor="middle">no strings past this point</text>'
    '</svg>'
)

FIG_TREE = (
    '<svg viewBox="0 0 680 240" role="img" aria-label="The sealed hierarchy: PaymentEvent has three direct subtypes, PaymentAuthorized, '
    'PaymentDeclined and the sealed MoneyMovement. MoneyMovement has two, PaymentCaptured and PaymentRefunded. One branch for '
    'MoneyMovement covers both of its leaves.">'
    '<rect class="box-a" x="250" y="12" width="180" height="46" rx="8"/>'
    '<text class="t t-code" x="340" y="33" text-anchor="middle">PaymentEvent</text>'
    '<text class="t-s t-m" x="340" y="50" text-anchor="middle">sealed interface</text>'
    '<line class="ln" x1="340" y1="58" x2="95" y2="98"/>'
    '<line class="ln" x1="340" y1="58" x2="265" y2="98"/>'
    '<line class="ln" x1="340" y1="58" x2="515" y2="98"/>'
    '<rect class="box" x="20" y="98" width="150" height="46" rx="8"/>'
    '<text class="t-s t-code" x="95" y="118" text-anchor="middle">PaymentAuthorized</text>'
    '<text class="t-s t-m" x="95" y="135" text-anchor="middle">data class</text>'
    '<rect class="box" x="190" y="98" width="150" height="46" rx="8"/>'
    '<text class="t-s t-code" x="265" y="118" text-anchor="middle">PaymentDeclined</text>'
    '<text class="t-s t-m" x="265" y="135" text-anchor="middle">data class</text>'
    '<rect class="box-b" x="430" y="98" width="170" height="46" rx="8"/>'
    '<text class="t-s t-code" x="515" y="118" text-anchor="middle">MoneyMovement</text>'
    '<text class="t-s t-m" x="515" y="135" text-anchor="middle">sealed interface</text>'
    '<line class="ln" x1="515" y1="144" x2="425" y2="184"/>'
    '<line class="ln" x1="515" y1="144" x2="595" y2="184"/>'
    '<rect class="box" x="350" y="184" width="150" height="46" rx="8"/>'
    '<text class="t-s t-code" x="425" y="204" text-anchor="middle">PaymentCaptured</text>'
    '<text class="t-s t-m" x="425" y="221" text-anchor="middle">data class</text>'
    '<rect class="box" x="520" y="184" width="150" height="46" rx="8"/>'
    '<text class="t-s t-code" x="595" y="204" text-anchor="middle">PaymentRefunded</text>'
    '<text class="t-s t-m" x="595" y="221" text-anchor="middle">data class</text>'
    '<text class="t-s t-a" x="175" y="200" text-anchor="middle">is MoneyMovement covers</text>'
    '<text class="t-s t-a" x="175" y="217" text-anchor="middle">both of its leaves</text>'
    '</svg>'
)

S1 = """Over three lessons you'll build one small library: an in-process event library for a payments service. This lesson is the model, the types for every event the service can see. Lesson 2 of this track is the bus that routes those events to handlers. Lesson 3 is the API that Kotlin and Java code call. Each lab starts from the previous lab's solution, so you can pick up at any lesson.

Start with what goes wrong without a model. The demo below has three handlers for messages from a Kafka topic, and each one reads the raw string fields itself:

```java
static void ledger(Map<String, String> fields) {
    if ("captured".equals(fields.get("type"))) {
        long cents = Long.parseLong(fields.get("amountMinor"));   // parsing, deep inside a handler
        balanceCents += cents;
    }
}
```

```kotlin
fun ledger(fields: Map<String, String>) {
    if (fields["type"] == "captured") {
        val cents = fields.getValue("amountMinor").toLong()      // parsing, deep inside a handler
        balanceCents += cents
    }
}
```

Two bugs come out of three messages. A capture with `"amountMinor": "12.50"` throws `NumberFormatException` inside the ledger, after the audit handler has already logged it as a capture. And the receipts handler compares the type with `"capture"`, a typo, so it never fires and nothing complains. Each handler parses and checks for itself, so each one can get it wrong in its own way, and the compiler can't help with any of it.

The fix comes in three pieces, one per section. A closed set of event types, so the compiler knows every case; that's the tool from *Sealed types: hierarchies the compiler can check*. Small types for ids and amounts, so a bad value can't be built at all, from *Value classes and what they compile to*. And one function at the edge that turns raw fields into those types or refuses them, the idea from *Data-oriented programming, and Project Valhalla*. Behind that edge, no handler ever sees a string field again.

Before you run the demo, predict which message fails, in which handler, and how many receipts get sent."""

S2 = """Here is the model. Every event is a fact about one payment, named in the past tense. A command asks for something; an event says it already happened, so handlers can't refuse it, only react.

```java
sealed interface PaymentEvent permits PaymentAuthorized, PaymentDeclined, MoneyMovement {
    PaymentId paymentId();
}
record PaymentAuthorized(PaymentId paymentId, Money amount) implements PaymentEvent {}
record PaymentDeclined(PaymentId paymentId, DeclineReason reason) implements PaymentEvent {}

sealed interface MoneyMovement extends PaymentEvent permits PaymentCaptured, PaymentRefunded {
    Money amount();
}
record PaymentCaptured(PaymentId paymentId, Money amount) implements MoneyMovement {}
record PaymentRefunded(PaymentId paymentId, Money amount) implements MoneyMovement {}
```

```kotlin
sealed interface PaymentEvent { val paymentId: PaymentId }
data class PaymentAuthorized(override val paymentId: PaymentId, val amount: Money) : PaymentEvent
data class PaymentDeclined(override val paymentId: PaymentId, val reason: DeclineReason) : PaymentEvent

sealed interface MoneyMovement : PaymentEvent { val amount: Money }
data class PaymentCaptured(override val paymentId: PaymentId, override val amount: Money) : MoneyMovement
data class PaymentRefunded(override val paymentId: PaymentId, override val amount: Money) : MoneyMovement
```

`sealed` closes the list of direct subtypes. In Kotlin they must sit in the same package and the same module; Java lists them after `permits`. Data classes and records are final, so every branch ends at a leaf, except `MoneyMovement`, which is sealed again one level down. That middle level is a design decision you'll use in lesson 2: a handler for `MoneyMovement` will receive captures and refunds, and nothing else.

The payoff is the exhaustive `when`. Write it with no `else`, and the compiler checks that every leaf is covered:

```java
static boolean movesMoney(PaymentEvent e) {
    return switch (e) {
        case MoneyMovement m -> true;                 // one case covers both leaves
        case PaymentAuthorized a -> false;
        case PaymentDeclined d -> false;
    };
}
```

```kotlin
fun movesMoney(e: PaymentEvent): Boolean = when (e) {
    is MoneyMovement -> true                          // one branch covers both leaves
    is PaymentAuthorized, is PaymentDeclined -> false
}
```

Add a `PaymentDisputed` and every such `when` stops compiling: `'when' expression must be exhaustive. Add the 'is PaymentDisputed' branch or an 'else' branch.` As *State and Chain of Responsibility* put it, the compiler writes your to-do list. An `else` throws that list away: the new event quietly takes the `else` branch at every place nobody revisited.

One gap stays open at run time. If a jar compiled against the new model hands a `PaymentDisputed` to code compiled against the old one, Kotlin throws `NoWhenBranchMatchedException` and Java throws `MatchException`. In this library events reach the service as raw fields and pass the edge first, so an old service rejects the unknown type there instead.

In the demo, uncomment `PaymentDisputed` and predict which of the three functions stop compiling."""

S3 = """Look at this refund record: `RawRefund("pay_7781", 30, 500)`. Is 30 the amount and 500 the fee, or the other way round? The constructor takes two `Long`s, so a swapped call compiles and moves the wrong money. Value classes make that a compile error:

```java
record PaymentId(String value) {
    PaymentId {
        if (!value.matches("pay_[A-Za-z0-9]{4,24}"))
            throw new IllegalArgumentException("invalid payment id: '" + value + "'");
    }
}
record Money(long minor) {
    Money {
        if (minor < 0) throw new IllegalArgumentException("amount must not be negative: " + minor);
    }
}
```

```kotlin
@JvmInline
value class PaymentId(val value: String) {
    init { require(PATTERN.matches(value)) { "invalid payment id: '$value'" } }
    override fun toString(): String = value
    companion object { private val PATTERN = Regex("pay_[A-Za-z0-9]{4,24}") }
}

@JvmInline
value class Money(val minor: Long) {
    init { require(minor >= 0) { "amount must not be negative: $minor" } }
    override fun toString(): String = BigDecimal.valueOf(minor, 2).toPlainString()
}
```

Now `PaymentCaptured(Money(1_999), PaymentId("pay_7781"))` fails with `argument type mismatch: actual type is 'Money', but 'PaymentId' was expected.` And because `init` runs on every construction, a `PaymentId` that exists is a valid one. Nothing downstream needs to check the format again.

The cost is small, for the reason *Value classes and what they compile to* gave: where a value class is used as itself, the compiler erases it to its one field. The demo prints the fields of `PaymentCaptured` through Java reflection, and they are a `java.lang.String` and a `long`. The Java records are separate objects on the heap, one per id and one per amount. They are boxed in the places that lesson listed, such as a `List<PaymentId>`, a nullable `Money?` or a generic `T`.

The one-field rule also made a decision for this model. A real `Money` would carry its currency, but a value class can hold only one field until Project Valhalla arrives, and a data class with two fields would cost an object per amount. This service settles in euros only, so `Money` is euro cents and the currency lives nowhere. The design review in lesson 3 comes back to whether that was right.

Keep the explicit `: String` on `toString`. Kotlin 2.4.21 can crash with a backend error when a value class's `toString` infers its return type and the value is used in a string template.

In the demo, uncomment the swapped constructor call and read both errors. Then compare the field types the Kotlin and Java versions print."""

S4 = """The model refuses bad values, but bad values still arrive: from Kafka, from a webhook, from a database row someone edited by hand. So one function converts raw input into the model, in one place, at the edge of the service. It returns a result and never throws:

```java
static Parsed parse(Map<String, String> fields) {
    try {
        String type = field(fields, "type");
        return switch (type) {
            case "captured" -> new Ok(new PaymentCaptured(new PaymentId(field(fields, "paymentId")), amount(fields)));
            // ... one case per type
            default -> new Rejected("unknown event type: '" + type + "'");
        };
    } catch (IllegalArgumentException e) {
        return new Rejected(e.getMessage());     // a reader or a constructor said no
    }
}
```

```kotlin
fun parseEvent(fields: Map<String, String>): Parsed = try {
    when (val type = field(fields, "type")) {
        "captured" -> Parsed.Ok(PaymentCaptured(PaymentId(field(fields, "paymentId")), amount(fields)))
        // ... one branch per type
        else -> Parsed.Rejected("unknown event type: '$type'")
    }
} catch (e: IllegalArgumentException) {
    Parsed.Rejected(e.message ?: "invalid event")  // a reader or a constructor said no
}
```

Notice what `parse` does not do: it doesn't check the payment id's format or the sign of the amount. It calls `PaymentId(...)` and `Money(...)` and turns their refusal into a `Rejected`. The rules live in the constructors, once. A second copy of them in the parser would drift the first time someone edits one and not the other.

Why a result instead of an exception? Because the caller has to decide what a bad message means, and an exception makes that decision for it. In a Kafka consumer, an exception that escapes the loop sends the consumer back to its last committed offset, so the same record fails again after every restart, and the partition behind it stops moving. A `Rejected` can go to a dead-letter topic with its reason as a header, add one to a metric and let the consumer commit the offset and move on. Never retry it: a malformed message stays malformed.

Behind the edge, code trusts the types. A function that takes a `PaymentCaptured` has a valid id and a positive amount, because no other kind of `PaymentCaptured` can exist. There is no `!!`, no `toLong()` and no `if (type == ...)` anywhere in the handlers you'll write in lesson 2.

The demo's parser knows only captures and refunds. Predict which of its six messages are rejected, and for what reason, before you run it."""

L = {
 "id": "cap3-01",
 "title": "A sealed event model",
 "minutes": 40,
 "goal": "By the end you can model payment events as a sealed hierarchy of data classes with value-class ids and amounts, parse untrusted fields into that model at the edge without throwing, and write operations as exhaustive `when` expressions that turn a new event type into a list of compile errors.",
 "warmup": {
  "q": "A log helper reads `when (event) { is PaymentCaptured -> \"capture\"; is PaymentRefunded -> \"refund\"; else -> \"other\" }`. A teammate adds `PaymentDisputed` to the sealed `PaymentEvent` interface and ships. What happens to disputes?",
  "options": [
   "The build fails until the helper handles PaymentDisputed",
   "They are logged as \"other\", and nothing tells anyone",
   "The helper throws NoWhenBranchMatchedException at run time",
   "Kotlin adds a branch for the new type automatically"
  ],
  "answer": 1,
  "why": "The `else` branch matches anything, including types that didn't exist when it was written, so the compiler has nothing to report. Without the `else`, the same change is a compile error at this exact line. `NoWhenBranchMatchedException` only appears when a subtype compiled later reaches a `when` that was exhaustive when it was compiled."
 },
 "sections": [
  {
   "h": "What you'll build, and why it starts with the model",
   "body": S1,
   "figure": {"svg": FIG_PLAN, "caption": "The whole library. This lesson builds the model and the edge in front of it; lessons 2 and 3 add the bus and the API."},
   "try": {
    "title": "Feel the stringly typed version fail",
    "minutes": 4,
    "steps": [
     "Read `StringlyDemo.kt` (or `StringlyDemoJava.java`). Write down which message fails, in which handler, and how many receipts get sent.",
     "Run it with the command below.",
     "Find the line in the output that shows the bad message was already audited before it failed.",
     "Fix the typo in `receipts` and run again. Then answer: where would a check have to go so that `pay_7782` never reaches `audit` at all?"
    ],
    "code": demo("stringly", "StringlyDemo"),
    "expect": "The third message prints `audit    captured pay_7782` and then `FAILED   java.lang.NumberFormatException: For input string: \"12.50\"`, so the audit log already holds a capture the ledger never posted. `receipts sent: 0`, because of the typo; after the fix it's 1. The only place a check can stop `pay_7782` before every handler is in front of all of them, which is the edge this lesson builds."
   }
  },
  {
   "h": "A sealed interface lists every event the service can see",
   "body": S2,
   "figure": {"svg": FIG_TREE, "caption": "Five types, four leaves. Sealing MoneyMovement keeps the list closed one level down, so one branch can stand for captures and refunds."},
   "try": {
    "title": "Add an event and read the to-do list",
    "minutes": 5,
    "steps": [
     "Run `ExhaustiveDemo` and look at the `label` column: `other` for authorizations and declines.",
     "Uncomment `PaymentDisputed` in `ExhaustiveDemo.kt`. Predict which of `summary`, `movesMoney` and `label` will fail to compile. Run the demo again to compile it.",
     "In `ExhaustiveDemoJava.java`, uncomment the record and add `PaymentDisputed` to the `permits` list of `PaymentEvent`. Run the Java twin.",
     "Put both files back the way they were."
    ],
    "code": demo("exhaustive", "ExhaustiveDemo"),
    "expect": "kotlinc reports `'when' expression must be exhaustive. Add the 'is PaymentDisputed' branch or an 'else' branch.` twice, for `summary` and `movesMoney`. `label` compiles without a word, and every dispute would be labelled `other`. javac reports `the switch expression does not cover all possible input values` for the same two methods."
   }
  },
  {
   "h": "Value classes turn a swapped argument into a compile error",
   "body": S3,
   "try": {
    "title": "Swap two arguments, then look at the fields",
    "minutes": 4,
    "steps": [
     "Run `ValuesDemo`. Read the `RawRefund` line: which number is the fee?",
     "Uncomment the swapped `PaymentCaptured(Money(1_999), PaymentId(\"pay_7781\"))` line and run again. Read the errors.",
     "Comment it out again and run `ValuesDemoJava`. Compare the two `field` lines with the Kotlin output."
    ],
    "code": demo("values", "ValuesDemo"),
    "expect": "Kotlin gives two errors, `argument type mismatch: actual type is 'Money', but 'PaymentId' was expected.` and the mirror one; Java gives `incompatible types: Money cannot be converted to PaymentId`. Both print `refused: invalid payment id: '7781'` and `refused: amount must not be negative: -500`. Kotlin's fields are `java.lang.String` and `long`; Java's are the nested `PaymentId` and `Money` record classes, each a separate object."
   }
  },
  {
   "h": "Parse at the edge, then trust the types",
   "body": S4,
   "try": {
    "title": "Run six messages through the edge",
    "minutes": 5,
    "steps": [
     "Read the six messages in `EdgeDemo`'s `main`. For each, predict OK or REJECTED and the reason.",
     "Run it.",
     "Add a `declined` branch: a `PaymentDeclined(paymentId, reason: String)` data class (a record in Java), and a branch that reads the `reason` field. Run it again and check the count line."
    ],
    "code": demo("edge", "EdgeDemo"),
    "expect": "One message passes and five are rejected: `amountMinor is not a whole number: '12.50'`, `invalid payment id: '7781'`, `amount must not be negative: -500`, `missing field 'amountMinor'` and `unknown event type: 'declined'`. The id and the sign were refused by the constructors, not by the parser. With your `declined` branch the last line reads `2 accepted, 4 rejected`."
   }
  }
 ],
 "analogy": "Think of the mailroom of a bank. Every envelope is opened there, once. A clerk either fills in the right typed form (a transfer, a complaint, a change of address) and sends it to a desk, or returns the letter with a note saying what was missing. The desks behind the mailroom only ever see forms, so they never squint at handwriting. The analogy breaks at one point: a good clerk may guess what a messy letter meant. The edge function must never guess. A missing amount is a rejection, not a zero.",
 "in_your_world": "In a Quarkus service the edge is usually the Kafka consumer: the deserializer hands you the record's JSON, `parseEvent` turns it into a `PaymentEvent`, and a `Rejected` goes to a dead-letter topic with the reason in a header, so the consumer can commit and move on. Webhooks from a card issuer, rows read back from an Oracle outbox table and signals into a Temporal workflow are edges too: each gets one parse function and nothing past it handles raw fields. When the producer team adds a new event type, deploy the consumers first: an old consumer rejects the unknown type at its edge and keeps running.",
 "mistake": "The common mistake is an edge that throws. `parseEvent` uses `!!`, `toLong()` and `require` directly, so a malformed message escapes as `NullPointerException` or `NumberFormatException`. In a Kafka consumer that exception fails the same record on every retry, and the partition stalls behind it. People write it because the throwing version is shorter and the happy-path test passes. The fix is to catch `IllegalArgumentException` once, around the whole parse, and return `Parsed.Rejected(e.message)`, so the caller decides where the bad message goes. Keep the checks themselves in the constructors.",
 "compare": {
  "title": "The event model in Java and Kotlin",
  "java": {
   "title": "Model.java (Java 21)",
   "src": "record PaymentId(String value) {\n    PaymentId {\n        if (!value.matches(\"pay_[A-Za-z0-9]{4,24}\"))\n            throw new IllegalArgumentException(\"invalid payment id: '\" + value + \"'\");\n    }\n    @Override public String toString() { return value; }\n}\n\nrecord Money(long minor) {\n    Money { if (minor < 0) throw new IllegalArgumentException(\"amount must not be negative: \" + minor); }\n    @Override public String toString() { return BigDecimal.valueOf(minor, 2).toPlainString(); }\n}\n\nsealed interface PaymentEvent permits PaymentAuthorized, PaymentDeclined, MoneyMovement {\n    PaymentId paymentId();\n}\nrecord PaymentAuthorized(PaymentId paymentId, Money amount) implements PaymentEvent {\n    PaymentAuthorized { if (amount.minor() <= 0) throw new IllegalArgumentException(\"authorized amount must be positive: \" + amount); }\n}\nrecord PaymentDeclined(PaymentId paymentId, DeclineReason reason) implements PaymentEvent {}\n\nsealed interface MoneyMovement extends PaymentEvent permits PaymentCaptured, PaymentRefunded {\n    Money amount();\n}\nrecord PaymentCaptured(PaymentId paymentId, Money amount) implements MoneyMovement { /* same check */ }\nrecord PaymentRefunded(PaymentId paymentId, Money amount) implements MoneyMovement { /* same check */ }\n\nstatic String summary(PaymentEvent e) {\n    return switch (e) {                                   // no default\n        case PaymentAuthorized(var id, var amount) -> id + \" authorized \" + amount + \" EUR\";\n        case PaymentDeclined(var id, var reason) -> id + \" declined: \" + reason;\n        case PaymentCaptured(var id, var amount) -> id + \" captured \" + amount + \" EUR\";\n        case PaymentRefunded(var id, var amount) -> id + \" refunded \" + amount + \" EUR\";\n    };\n}"
  },
  "kotlin": {
   "title": "Model.kt",
   "src": "@JvmInline\nvalue class PaymentId(val value: String) {\n    init { require(PATTERN.matches(value)) { \"invalid payment id: '$value'\" } }\n    override fun toString(): String = value\n    companion object { private val PATTERN = Regex(\"pay_[A-Za-z0-9]{4,24}\") }\n}\n\n@JvmInline\nvalue class Money(val minor: Long) {\n    init { require(minor >= 0) { \"amount must not be negative: $minor\" } }\n    override fun toString(): String = BigDecimal.valueOf(minor, 2).toPlainString()\n}\n\nsealed interface PaymentEvent { val paymentId: PaymentId }\ndata class PaymentAuthorized(override val paymentId: PaymentId, val amount: Money) : PaymentEvent {\n    init { require(amount.minor > 0) { \"authorized amount must be positive: $amount\" } }\n}\ndata class PaymentDeclined(override val paymentId: PaymentId, val reason: DeclineReason) : PaymentEvent\n\nsealed interface MoneyMovement : PaymentEvent { val amount: Money }\ndata class PaymentCaptured(override val paymentId: PaymentId, override val amount: Money) : MoneyMovement { /* same check */ }\ndata class PaymentRefunded(override val paymentId: PaymentId, override val amount: Money) : MoneyMovement { /* same check */ }\n\nfun summary(event: PaymentEvent): String = when (event) {   // no else\n    is PaymentAuthorized -> \"${event.paymentId} authorized ${event.amount} EUR\"\n    is PaymentDeclined -> \"${event.paymentId} declined: ${event.reason}\"\n    is PaymentCaptured -> \"${event.paymentId} captured ${event.amount} EUR\"\n    is PaymentRefunded -> \"${event.paymentId} refunded ${event.amount} EUR\"\n}"
  },
  "note": "The shape is the same: sealed interfaces for the alternatives, final carriers for the leaves, validation in the constructor, and one exhaustive switch per operation. Three things differ. Kotlin's value classes compile to a `String` and a `long` wherever they're used as themselves, while Java's `PaymentId` and `Money` records are separate objects until value records arrive with Valhalla. Java names the subtypes in `permits` (or infers them within one file), while Kotlin requires them to share the package and module. And a data class's `copy()` runs `init`, so `captured.copy(amount = Money.ZERO)` throws; records have no `copy`. kotlinc writes the same `PermittedSubclasses` attribute that javac does, so Java code can switch exhaustively over this Kotlin model, which lesson 3 relies on."
 },
 "worked": {
  "title": "Add a new event type, end to end",
  "steps": [
   {
    "say": "Chargebacks arrive: a cardholder disputes `pay_7781`, and the card scheme holds 19.99 until it's decided. First decide where the event goes. Money is held, not captured or refunded, so it is not a `MoneyMovement`. It's a direct subtype of `PaymentEvent`, with the same positive-amount rule as the others.",
    "code": "data class PaymentDisputed(override val paymentId: PaymentId, val amount: Money) : PaymentEvent {\n    init { require(amount.minor > 0) { \"disputed amount must be positive: $amount\" } }\n}",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "// and add PaymentDisputed to the permits list of PaymentEvent\nrecord PaymentDisputed(PaymentId paymentId, Money amount) implements PaymentEvent {\n    PaymentDisputed {\n        if (amount.minor() <= 0) throw new IllegalArgumentException(\"disputed amount must be positive: \" + amount);\n    }\n}"
   },
   {
    "say": "Compile before you write anything else. Every exhaustive `when` over `PaymentEvent` fails with `'when' expression must be exhaustive. Add the 'is PaymentDisputed' branch or an 'else' branch.` That list is the to-do list. Anything written against `MoneyMovement` still compiles, because its list of subtypes didn't change. Add the branch to `summary`:",
    "code": "is PaymentDisputed -> \"${event.paymentId} disputed ${event.amount} EUR\"",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "case PaymentDisputed(var id, var amount) -> id + \" disputed \" + amount + \" EUR\";"
   },
   {
    "say": "Now the edge. Its `when` is over a string, which can't be exhaustive, so it has an `else` and the compiler says nothing. A test has to do that job. The lab's `every event type has a summary line` test compares its samples with `PaymentEvent::class.sealedSubclasses`, so it fails until someone adds a disputed sample, and that reminds them to add the parser branch and its test:",
    "code": "\"disputed\" -> PaymentDisputed(PaymentId(field(\"paymentId\")), amount())",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "case \"disputed\" -> new Ok(new PaymentDisputed(new PaymentId(field(fields, \"paymentId\")), amount(fields)));"
   },
   {
    "say": "Last, the deploy order. Services that haven't been redeployed still parse raw fields with the old parser, so a `disputed` message lands in their `else` branch and becomes `Rejected(\"unknown event type: 'disputed'\")` on the dead-letter topic. Nothing crashes. Deploy the consumers first, then the producer, and replay the dead letters if any arrived in between.",
    "code": "",
    "lang": ""
   }
  ]
 },
 "lab": {
  "title": "Build the event model and its edge",
  "minutes": 15,
  "files": [
   "labs/events/src/main/kotlin/workbench/events/l01/Values.kt",
   "labs/events/src/main/kotlin/workbench/events/l01/Model.kt",
   "labs/events/src/main/kotlin/workbench/events/l01/Parsing.kt",
   "labs/events/src/main/kotlin/workbench/events/l01/Summary.kt"
  ],
  "run": "./gradlew :events:test --tests 'workbench.events.l01.*'",
  "steps": [
   "Run the tests. Eleven of the twelve fail; the one that passes checks `toString`, which is given.",
   "`Values.kt` (TODOs 1 and 2): add a `require` to each `init` block, and write `plus` and `minus` with `Math.addExact` and `Math.subtractExact`. Why does `minus` need no check of its own for a result below zero?",
   "`Model.kt` (TODO 3): give the three events that carry an amount an `init` block that refuses zero.",
   "`Parsing.kt` (TODO 4): write `parseEvent`. Read the KDoc for the exact messages. It must never throw.",
   "`Summary.kt` (TODO 5): delete the `else` branch, run the tests to compile, and add the branches the error asks for.",
   "Run until all twelve pass. Then add a stray `else -> \"?\"` to `summary` and run again: the build stays green, and the only sign is the warning `'when' is exhaustive so 'else' is redundant here.` Delete it again."
  ],
  "hints": [
   "`require(condition) { \"message\" }` throws `IllegalArgumentException` with that message when the condition is false.",
   "`minus` builds a new `Money`, and the constructor already refuses a negative value.",
   "Inside `parseEvent`, write two local helpers: `field(name)`, which throws `IllegalArgumentException(\"missing field '$name'\")`, and `amount()`, which uses `toLongOrNull()` and throws when it gets `null`. Then wrap the whole `when` in one `try`/`catch (e: IllegalArgumentException)`.",
   "Inside the `try`, `else -> return Parsed.Rejected(\"unknown event type: '$type'\")` returns from `parseEvent` directly.",
   "`DeclineReason.entries.find { it.name == raw }` gives `null` for an unknown reason."
  ],
  "done_when": "All twelve tests in `ModelTest` pass."
 },
 "drill": {
  "title": "Write the hierarchy from memory",
  "minutes": 5,
  "prompt": "Close the lab. In a blank file, write the sealed hierarchy from memory: `PaymentEvent`, the sealed `MoneyMovement` and the four leaves (plain `String` ids and `Long` amounts are fine). Then write `movesMoney(e)` with no `else`, using one branch for `MoneyMovement`. Finally, add `PaymentDisputed` and say which of your functions must change.",
  "answer": {
   "lang": "kotlin",
   "src": "sealed interface PaymentEvent { val paymentId: String }\ndata class PaymentAuthorized(override val paymentId: String, val cents: Long) : PaymentEvent\ndata class PaymentDeclined(override val paymentId: String, val reason: String) : PaymentEvent\n\nsealed interface MoneyMovement : PaymentEvent { val cents: Long }\ndata class PaymentCaptured(override val paymentId: String, override val cents: Long) : MoneyMovement\ndata class PaymentRefunded(override val paymentId: String, override val cents: Long) : MoneyMovement\n\nfun movesMoney(e: PaymentEvent): Boolean = when (e) {\n    is MoneyMovement -> true\n    is PaymentAuthorized, is PaymentDeclined -> false\n}\n\n// PaymentDisputed : PaymentEvent breaks movesMoney (add `is PaymentDisputed -> false`).\n// A when over MoneyMovement alone would still compile.",
   "alt": {
    "lang": "java",
    "src": "sealed interface PaymentEvent permits PaymentAuthorized, PaymentDeclined, MoneyMovement { String paymentId(); }\nrecord PaymentAuthorized(String paymentId, long cents) implements PaymentEvent {}\nrecord PaymentDeclined(String paymentId, String reason) implements PaymentEvent {}\n\nsealed interface MoneyMovement extends PaymentEvent permits PaymentCaptured, PaymentRefunded { long cents(); }\nrecord PaymentCaptured(String paymentId, long cents) implements MoneyMovement {}\nrecord PaymentRefunded(String paymentId, long cents) implements MoneyMovement {}\n\nstatic boolean movesMoney(PaymentEvent e) {\n    return switch (e) {\n        case MoneyMovement m -> true;\n        case PaymentAuthorized a -> false;\n        case PaymentDeclined d -> false;\n    };\n}\n\n// PaymentDisputed (added to permits) breaks movesMoney: add `case PaymentDisputed d -> false;`."
   }
  }
 },
 "recap": [
  "Stringly typed handlers each parse and check for themselves, so a bad message fails deep inside one of them after others have already acted on it.",
  "A sealed interface closes the list of event types. Kotlin subtypes share its package and module; Java names them in `permits`. A sealed middle level such as `MoneyMovement` lets one branch stand for its leaves.",
  "Write every operation as a `when` or `switch` with no `else`, so a new event type becomes a compile error at each place that must handle it.",
  "Value classes make ids and amounts their own types at no cost where they're used as themselves, and their `init` blocks make every instance valid. One field only, so `Money` here is euro cents.",
  "Parse once, at the edge, into the model. Return `Ok` or `Rejected`, never throw, and let the constructors make the checks. Behind the edge, trust the types."
 ],
 "quiz": [
  {
   "q": "From *Sealed types: hierarchies the compiler can check*: you move `PaymentRefunded` into a new package, `workbench.events.refunds`, in the same module. It still implements the sealed `MoneyMovement`. What happens?",
   "options": [
    "It compiles: the same module is enough",
    "kotlinc reports an error: a direct subtype of a sealed interface must be in the same package and module",
    "It compiles with a warning, and `when` over MoneyMovement loses its exhaustiveness check",
    "It compiles as long as the file is listed in `permits`"
   ],
   "answer": 1,
   "why": "Kotlin's rule is the same package and the same module, with no `permits` clause at all. The closed list is what makes the `when` checkable, so the compiler refuses an inheritor elsewhere instead of quietly opening the hierarchy.",
   "from": "dop-02"
  },
  {
   "q": "From *Value classes and what they compile to*: a `val recent: List<PaymentId>` holds 10,000 ids. What does the list hold at run time?",
   "options": [
    "10,000 `PaymentId` boxes, each wrapping a `String`",
    "10,000 plain `String`s, because value classes are always erased",
    "One shared `PaymentId` object",
    "10,000 `PaymentId` objects, but only on JDK 25 and later"
   ],
   "answer": 0,
   "why": "A value class is boxed whenever it's used as another type, and a generic type argument is one of those places. `List<PaymentId>` costs the same as `List<Long>` would: one object per element. The erasure to a plain `String` happens for fields, parameters and return values typed `PaymentId`.",
   "from": "kt-02"
  },
  {
   "q": "`fun ledgerSign(e: MoneyMovement): Int = when (e) { is PaymentCaptured -> 1; is PaymentRefunded -> -1 }`. Someone adds `data class PaymentDisputed(...) : PaymentEvent`. Does `ledgerSign` still compile?",
   "options": [
    "No: every `when` over the hierarchy must handle the new type",
    "Only after adding an `else` branch",
    "Yes, but it throws for disputes",
    "Yes: the list of `MoneyMovement` subtypes didn't change"
   ],
   "answer": 3,
   "why": "`ledgerSign` switches over `MoneyMovement`, and a dispute isn't one. Only `when`s over `PaymentEvent` itself get the new error. That is the benefit of a sealed middle level: code written against it is shielded from changes elsewhere in the tree. And a dispute can't reach `ledgerSign`, because the parameter type won't accept it."
  },
  {
   "q": "From *Data-oriented programming, and Project Valhalla*: `parseEvent` receives `amountMinor = \"-500\"` for a refund. Which code should notice?",
   "options": [
    "`parseEvent`, with its own `if (minor < 0)` check before building the event",
    "The ledger handler, before it posts the refund",
    "`Money`'s `init` block, and `parseEvent` turns its exception into `Rejected`",
    "Nobody: a negative refund is a valid way to write a capture"
   ],
   "answer": 2,
   "why": "The rule lives in the constructor, once, so every path that builds a `Money` obeys it. The parser only converts the refusal into a value. A second check in the parser drifts from the first, and a check in the handler means invalid events got past the edge.",
   "from": "dop-04"
  },
  {
   "q": "From *State and Chain of Responsibility*: your service was compiled against model 1.4. At deploy time someone swaps in model 1.5, which adds `PaymentDisputed`, without recompiling the service. An in-process component built against 1.5 hands a dispute to the service's `summary`, which has no `else`. What happens?",
   "options": [
    "`summary` returns an empty string",
    "The JVM refuses to load `PaymentDisputed`",
    "`summary` falls through to its last branch",
    "`summary` throws `NoWhenBranchMatchedException`"
   ],
   "answer": 3,
   "why": "Exhaustiveness is checked at compile time. For an exhaustive `when` with no `else`, kotlinc adds a hidden throw for the remainder: a subtype it never saw. Java's switch throws `MatchException` in the same situation. Events that arrive as raw fields avoid this, because the old parser rejects the unknown type at the edge.",
   "from": "pat-09"
  }
 ],
 "flashcards": [
  {"front": "Why no `else` in a `when` over your own sealed type?", "back": "Without it, a new subtype is a compile error at every `when` that must handle it. With it, the new subtype silently takes the `else` branch."},
  {"front": "What does a sealed middle level like `MoneyMovement` give you?", "back": "One branch, `is MoneyMovement`, covers its leaves (captures and refunds), and code written against it doesn't break when siblings are added elsewhere."},
  {"front": "`@JvmInline value class PaymentId(val value: String)`: what is a `PaymentId` field at run time?", "back": "A plain `String` field. It is boxed only when used as another type: generic, nullable, interface or `Any`."},
  {"front": "Why is `Money` here euro cents, with no currency?", "back": "A JVM value class holds exactly one field. Amount plus currency would be a data class, one object per amount, and this service settles in euros only."},
  {"front": "What does the edge function return for a malformed message?", "back": "`Parsed.Rejected(reason)`, never an exception. The caller routes it: dead-letter topic, log line, metric."},
  {"front": "Where does `parseEvent` check that a payment id is well formed?", "back": "It doesn't. It calls `PaymentId(raw)`, whose `init` checks, and turns the `IllegalArgumentException` into `Rejected`."},
  {"front": "An old service gets a message of a new event type as raw fields. What happens?", "back": "Its parser's `else` branch returns `Rejected(\"unknown event type\")`. Nothing crashes, so deploy consumers before producers."}
 ],
 "terms": [
  {"term": "Sealed hierarchy", "plain": "A type whose list of direct subtypes is closed and known to the compiler."},
  {"term": "Exhaustive when", "plain": "A `when` or `switch` with a branch for every possible subtype and no `else`, checked at compile time."},
  {"term": "Value class", "plain": "A one-field wrapper that is its own type in Kotlin and compiles to its field where it can."},
  {"term": "Edge", "plain": "The one place where raw input from outside the service becomes model values, or is refused."},
  {"term": "Dead-letter topic", "plain": "A Kafka topic that holds messages a consumer refused, with the reason, so they can be inspected or replayed."},
  {"term": "Remainder", "plain": "The cases an exhaustive switch can still meet at run time: null, and subtypes compiled after it."}
 ],
 "explain_back": {
  "prompt": "A teammate asks why handlers take a `PaymentCaptured` instead of the Kafka record's `Map<String, String>`: \"the map has everything, and it's one less type to maintain.\" Explain what the sealed model and the edge buy you, using a bug you could get with the map.",
  "answer": "With the map, every handler parses and validates for itself. A capture with amount \"12.50\" throws inside the ledger after the audit handler already logged it, and a typo like \"capture\" silently never matches. The model closes the list of event types, so a `when` without `else` lists every place that must change when a type is added. Value classes make a swapped id and amount a compile error, and their constructors make every instance valid. The edge parses each record once and returns `Ok` or `Rejected`, so a bad message goes to the dead-letter topic before any handler acts. Behind it, a handler that takes a `PaymentCaptured` knows it has a valid id and a positive amount. The extra types cost a few lines; they remove a whole class of 2 a.m. bugs."
 },
 "deeper": {
  "minutes": 10,
  "body": """Three questions come up once a model like this is in production.

How do events evolve? Adding a field with a default is safe for consumers that parse at the edge: old messages lack the field and get the default. Renaming a type or a field is not. Keep the old name in the parser for as long as old messages can arrive, and map it to the new type there, so the model itself never carries the history. If you serialize the model with kotlinx.serialization, as *Compiler plugins: all-open, no-arg and kotlinx.serialization* showed, pin each type's name with `@SerialName` for the same reason.

Should the edge return `Either` instead of a sealed `Parsed`? `Either<String, PaymentEvent>` from *Generics workshop: a type-safe container and event bus* works, and composes with `map` and `flatMap`. A dedicated `Parsed` reads better at the call site (`is Parsed.Rejected`) and leaves room for a third case later, such as `Ignored` for event types a service deliberately doesn't handle. Kotlin's `Result<T>` is the wrong fit: its failure side is a `Throwable`, and a rejection is not an exception.

What about the database? Rows you read back are untrusted input too. A column holding `'captured'` and a nullable `amount_minor` is a raw map with a schema, and a migration or a manual fix can break it. Read rows through the same kind of edge function, or reuse `parseEvent` by turning each row into its field map.

Java has one tool here that Kotlin lacks: since JDK 21 a pattern switch can take `case null` explicitly, while Kotlin rules out null at compile time by declaring the parameter non-nullable. Both end up with the same guarantee behind the edge."""
 },
 "sources": [
  {"title": "Sealed classes and interfaces (Kotlin docs)", "url": "https://kotlinlang.org/docs/sealed-classes.html"},
  {"title": "Inline value classes (Kotlin docs)", "url": "https://kotlinlang.org/docs/inline-classes.html"},
  {"title": "JEP 409: Sealed Classes", "url": "https://openjdk.org/jeps/409"},
  {"title": "Brian Goetz, Data Oriented Programming in Java (InfoQ, 2022)", "url": "https://www.infoq.com/articles/data-oriented-programming-java/"},
  {"title": "Preparing for Change: Safe Switching over Sealed APIs (Bimpoudis, Buckley, Goetz, 2026)", "url": "https://github.com/openjdk/amber-docs/blob/master/site/guides/exhaustiveness-guide.md"}
 ]
}
out = ROOT / "content/lessons/cap3-01.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
