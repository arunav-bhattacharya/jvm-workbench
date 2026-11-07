import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/patterns/src"
J = "java/workbench/patterns/l06"
K = "kotlin/workbench/patterns/l06"
read = lambda p: (ROOT / p).read_text()
demo = lambda cls: f"./gradlew :patterns:demo -Pmain=workbench.patterns.l06.{cls}"


def code(lang, name, cls, alt_lang, alt_name, alt_cls):
    d1 = J if lang == "java" else K
    d2 = J if alt_lang == "java" else K
    return {"lang": lang, "title": name, "src": read(f"{lab}/demo/{d1}/{name}"), "run": demo(cls), "file": f"{lab}/demo/{d1}/{name}",
            "alt": {"lang": alt_lang, "title": alt_name, "src": read(f"{lab}/demo/{d2}/{alt_name}"), "run": demo(alt_cls), "file": f"{lab}/demo/{d2}/{alt_name}"}}


FIG = """<svg viewBox="0 0 640 282" role="img" aria-label="A fee plan tree: AllOf at the root with Flat(30), Percent(290) and a nested AllOf holding Flat(5); on 10,000 the leaves give 30, 290 and 5 and the root adds them to 325">
<rect class="box-a" x="250" y="16" width="140" height="50" rx="8"/>
<text class="t t-code" x="320" y="38" text-anchor="middle">AllOf</text>
<text class="t-s t-a" x="320" y="56" text-anchor="middle">30 + 290 + 5 = 325</text>
<rect class="box" x="40" y="122" width="140" height="50" rx="8"/>
<text class="t t-code" x="110" y="144" text-anchor="middle">Flat(30)</text>
<text class="t-s t-m" x="110" y="162" text-anchor="middle">30</text>
<rect class="box" x="250" y="122" width="140" height="50" rx="8"/>
<text class="t t-code" x="320" y="144" text-anchor="middle">Percent(290)</text>
<text class="t-s t-m" x="320" y="162" text-anchor="middle">10,000 x 2.9% = 290</text>
<rect class="box-b" x="460" y="122" width="140" height="50" rx="8"/>
<text class="t t-code" x="530" y="144" text-anchor="middle">AllOf</text>
<text class="t-s" x="530" y="162" text-anchor="middle">5</text>
<rect class="box" x="460" y="220" width="140" height="50" rx="8"/>
<text class="t t-code" x="530" y="242" text-anchor="middle">Flat(5)</text>
<text class="t-s t-m" x="530" y="260" text-anchor="middle">5</text>
<line class="ln" x1="300" y1="66" x2="120" y2="119" marker-end="url(#arr)"/>
<line class="ln" x1="320" y1="66" x2="320" y2="119" marker-end="url(#arr)"/>
<line class="ln" x1="340" y1="66" x2="520" y2="119" marker-end="url(#arr)"/>
<line class="ln" x1="530" y1="172" x2="530" y2="217" marker-end="url(#arr)"/>
<text class="t-s t-m" x="220" y="232" text-anchor="middle">fee(10,000) asks every node</text>
<text class="t-s t-m" x="220" y="250" text-anchor="middle">the same question: leaf or group</text>
</svg>""".replace("\n", "")

S1 = """A merchant's fee plan is rarely one number. It's 0.30 plus 2.9%, plus a bundle of add-ons, and the bundle has rules of its own. **Composite** lets a group of rules and a single rule share one interface. A group answers by asking each of its children, so the code that prices a payment never checks whether it holds a leaf or a whole tree.

The GoF version is an abstract `Component` class with `add` and `remove` methods that leaves must implement somehow. Java 21 and Kotlin replace it with a sealed type and one exhaustive switch:

```java
sealed interface Rule permits Flat, Percent, AllOf {}
record Flat(long minor) implements Rule {}
record Percent(int bps) implements Rule {}
record AllOf(List<Rule> rules) implements Rule {
    AllOf { rules = List.copyOf(rules); }            // immutable: copy what the caller passed
}

static long fee(Rule r, long amountMinor) {
    return switch (r) {                               // no default
        case Flat f -> f.minor();
        case Percent p -> amountMinor * p.bps() / 10_000;
        case AllOf a -> a.rules().stream().mapToLong(x -> fee(x, amountMinor)).sum();
    };
}

Rule plan = new AllOf(List.of(new Flat(30), new Percent(290), new AllOf(List.of(new Flat(5)))));
```

```kotlin
sealed interface Rule {
    data class Flat(val minor: Long) : Rule
    data class Percent(val bps: Int) : Rule
    class AllOf(rules: List<Rule>) : Rule {
        val rules: List<Rule> = rules.toList()         // immutable: copy what the caller passed
    }
}

fun fee(r: Rule, amountMinor: Long): Long = when (r) {   // no else
    is Rule.Flat -> r.minor
    is Rule.Percent -> amountMinor * r.bps / 10_000
    is Rule.AllOf -> r.rules.sumOf { fee(it, amountMinor) }
}

val plan = Rule.AllOf(listOf(Rule.Flat(30), Rule.Percent(290), Rule.AllOf(listOf(Rule.Flat(5)))))
```

For a 100.00 payment, `fee(plan, 10_000)` is 30 + 290 + 5 = 325. The recursion follows the tree: `AllOf` adds up whatever its children return, and the children don't care who asked.

The sealed type buys you two things. The switch has no `default`, so adding a `Capped` node makes javac report "the switch expression does not cover all possible input values" (kotlinc: "'when' expression must be exhaustive") at every place that prices or prints a plan. And a second operation over the same tree, such as `describe`, is just another function. The node classes don't change.

Keep the tree immutable. `List.copyOf` in the compact constructor copies the caller's list, so a later edit to that list can't reach into a plan that is already in use. Kotlin's `List` is only a read-only view, so copy with `toList()`. An immutable tree can't grow a cycle, and threads can share it safely, which the last section relies on."""

S2 = """Payment ops wants alerts: payment failed, fraud suspected, settlement late. Each must go out by SMS, email or Slack. Model that with inheritance (`PaymentFailedSms`, `PaymentFailedEmail` and so on) and you write nine classes. A fourth channel costs three more, each a near copy of its neighbors.

**Bridge** splits the two dimensions. One side is the abstraction: what happened, the alert. The other is the implementor: how it travels, the channel. The alert holds a channel and calls it:

```java
interface Channel { void deliver(String to, String body); }             // implementor: how it travels

sealed interface Alert permits PaymentFailed, FraudSuspected {           // abstraction: what happened
    void raise(String to);
}
record PaymentFailed(Channel channel, String paymentId) implements Alert {
    public void raise(String to) { channel.deliver(to, "payment " + paymentId + " failed"); }
}
record FraudSuspected(Channel channel, String last4, int score) implements Alert {
    public void raise(String to) { channel.deliver(to, "card ****" + last4 + " flagged, risk " + score); }
}

new PaymentFailed(sms, "pay_881").raise("on-call");
new PaymentFailed(email, "pay_881").raise("on-call");   // same alert, other channel: no new class
```

```kotlin
fun interface Channel { fun deliver(to: String, body: String) }          // implementor: how it travels

sealed interface Alert { fun raise(to: String) }                           // abstraction: what happened
data class PaymentFailed(val channel: Channel, val paymentId: String) : Alert {
    override fun raise(to: String) = channel.deliver(to, "payment $paymentId failed")
}
data class FraudSuspected(val channel: Channel, val last4: String, val score: Int) : Alert {
    override fun raise(to: String) = channel.deliver(to, "card ****$last4 flagged, risk $score")
}

PaymentFailed(sms, "pay_881").raise("on-call")
PaymentFailed(email, "pay_881").raise("on-call")    // same alert, other channel: no new class
```

Three alert types and three channels are now six small pieces, and a new channel is one more. Every alert works with it, because alerts only know `Channel`. Tests pass a recording lambda as the channel and check the text, with no SMS vendor in sight.

In Kotlin the implementor side often shrinks to a function. With `fun interface Channel`, the lambda `Channel { to, body -> slack.post(to, body) }` is a whole channel. A plain function type, `(String, String) -> Unit`, works as well.

Bridge is easy to confuse with Adapter, because both put an interface between two pieces of code. The difference is when and why. You design a bridge up front, because you know two things will vary on their own. You write an adapter afterwards, because a class you can't change has the wrong interface. They often meet: each channel is usually an adapter around a vendor SDK, like the issuer adapter in *Adapter and Facade*.

Skip the bridge when only one dimension varies. If every alert goes by email, an alert with a `Mailer` field is plain composition, and calling it a pattern adds nothing."""

S3 = """Run `Integer a = 127, b = 127;` and `a == b` is true. Make both 128 and it's false. `Integer.valueOf`, which autoboxing calls, "will always cache values in the range -128 to 127, inclusive", so small values come from a shared pool and larger ones are new objects. That cache is a **flyweight**: many users share one immutable instance instead of each holding a copy.

The JDK has more of them. The JVM interns string literals, keeping one `String` per literal, and `s.intern()` returns the pooled copy of any string. `Currency` "is designed so that there's never more than one Currency instance for any given currency", which is why it has no public constructor and you call `Currency.getInstance("EUR")`. Enums are flyweights by definition, and so are Kotlin's `object` and `data object`.

The cache also explains one of the oldest bugs in Java payment code:

```java
Long settled = ledger.get("EUR");        // 25_000L, boxed when it went into the map
Long expected = report.get("EUR");       // 25_000L, boxed separately
if (settled == expected) { ... }         // false: two different Long objects
if (settled.equals(expected)) { ... }    // true
```

```kotlin
val settled: Long? = ledger["EUR"]       // 25_000L
val expected: Long? = report["EUR"]      // 25_000L
if (settled == expected) { /* ... */ }   // true: == calls equals()
if (settled === expected) { /* ... */ }  // false, and the compiler warns
```

Java's `==` on objects compares references. With test amounts under 128 the cache makes it pass; with real amounts it fails. Kotlin's `==` calls `equals`, so you only meet this bug with `===`, and on `Long?` kotlinc warns that "identity equality for arguments of types 'Long?' and 'Long?' is prohibited".

You build your own flyweight with a canonicalizing factory: a private constructor and an `of` method that returns the pooled instance from a `ConcurrentHashMap`. Use `computeIfAbsent`. It checks and inserts in one atomic step, so eight threads asking for a new code at the same moment still get one instance. A `get` followed by a `put` on a miss is check-then-act, and under load it builds duplicates.

Two more rules keep flyweights safe. They must be immutable, because every holder sees every change. And the pool must be bounded: interning merchant names from webhook payloads grows a map that never shrinks. Pool a known set, such as the merchant category codes in a reference table."""

S4 = """Composite and Flyweight work well together. A platform with 40,000 merchants rarely has 40,000 fee plans. It has a dozen: standard, high-risk, marketplace and a few negotiated ones. Build each plan tree once at startup and let every merchant point at one of them, instead of parsing a plan per merchant per payment.

The GoF book names the split that makes this work. **Intrinsic state** lives inside the shared object and is the same for every user: the rates and caps in the plan. **Extrinsic state** belongs to one use, so the caller passes it in: the payment amount. That's why `fee` takes the amount as an argument. A plan that kept "the current amount" in a field could not be shared, by two merchants or by two threads.

Sharing across threads costs nothing here, because the trees never change. Records have final fields, `List.copyOf` returns an unmodifiable list, and an object that never changes can be read by 200 request threads at once with no lock, once it has been published safely (in a `static final` field, or set before the threads start). *Don't share: immutability, confinement, ThreadLocal* in the concurrency track showed why that holds.

The same thinking fits the small values on every payment: currencies, merchant categories, card networks, response codes. If the set is closed and known when you compile, an `enum` (Java) or `enum class` (Kotlin) is the flyweight, with no pool to write. Reach for a pooled factory only when the set is open but bounded, such as category codes loaded from a table.

In the lab you build both halves: a five-node pricing composite with two operations, and a merchant-category flyweight that stays correct when eight threads ask for the same code at once.

Check yourself. Merchants want to see "fees charged this month", and a teammate adds a `var monthTotal` to the shared root of the standard plan. What goes wrong, and where should the total live? (Every merchant on the standard plan points at that one root, so they all add to one total, and two request threads adding at once can lose an update. The total is extrinsic state: keep it per merchant, outside the tree.)"""

L = {
 "id": "pat-06",
 "title": "Composite, Bridge and Flyweight",
 "minutes": 36,
 "goal": "By the end you can model a fee plan as an immutable sealed tree priced by one exhaustive switch, split two independent dimensions with a bridge, and share immutable values through a thread-safe flyweight factory without falling for boxed `==`.",
 "warmup": {
  "q": "In Java, `Integer a = 127, b = 127;` and `Integer c = 128, d = 128;`. What do `a == b` and `c == d` print with default JVM settings?",
  "options": ["true and true", "true and false", "false and false", "It doesn't compile: `==` can't compare Integer objects"],
  "answer": 1,
  "why": "Autoboxing calls `Integer.valueOf`, which always returns a cached, shared instance for -128 to 127. So `a` and `b` are the same object. 128 is outside the cache, so `c` and `d` are two different objects with equal values, and `==` compares references. That shared cache is a flyweight, and it's the reason boxed `==` bugs pass tests with small numbers."
 },
 "sections": [
  {
   "h": "Composite: a tree you price like a single rule",
   "body": S1,
   "figure": {"svg": FIG, "caption": "The root adds up what its children return. A nested group answers the same question, so one recursive function prices any plan."},
   "try": {
    "title": "Price a tree, then let the caller mutate it",
    "minutes": 4,
    "steps": [
     "Open `CompositeDemo.java` (or `CompositeDemo.kt`). Before you run it, work out the two fees in your head.",
     "Run it with the command below and check your numbers. Note the last line.",
     "Remove the copy: in Java delete the compact constructor `AllOf { rules = List.copyOf(rules); }`; in Kotlin change `= rules.toList()` to `= rules`. Predict the last line, then run."
    ],
    "code": code("java", "CompositeDemo.java", "CompositeDemo", "kotlin", "CompositeDemo.kt", "CompositeDemoKt"),
    "expect": "`plan: (30 + 2.90% + (5))`, fees 325 and 2935 (30 + 2,900 + 5), and `after editing the source list: (30 + 2.90% + (5))`. Without the copy, the last line becomes `(30 + 2.90% + (5 + 1000))`: a plan already in use silently gained a 10.00 fee because someone edited the list they built it from."
   },
   "refs": [
    {"title": "Sealed classes and interfaces (Kotlin docs)", "url": "https://kotlinlang.org/docs/sealed-classes.html", "kind": "docs"}
   ]
  },
  {
   "h": "Bridge: two dimensions without N times M classes",
   "body": S2,
   "try": {
    "title": "Add a channel without touching an alert",
    "minutes": 4,
    "steps": [
     "Run `BridgeDemo` in either language and count the lines: 2 alert types times 2 channels.",
     "Add a Slack channel. Java: `record Slack() implements Channel { public String deliver(String to, String body) { return \"SLACK #\" + to + \": \" + body; } }`, then add `new Slack()` to the list. Kotlin: `private val slack = AlertChannel { to, body -> \"SLACK #$to: $body\" }`, then add `slack` to the list.",
     "Predict how many lines print and how many alert types you had to edit. Run it."
    ],
    "code": code("java", "BridgeDemo.java", "BridgeDemo", "kotlin", "BridgeDemo.kt", "BridgeDemoKt"),
    "expect": "Four lines before; six after, the last two starting `SLACK #on-call` and `SLACK #risk-team`. You edited zero alert types. In Kotlin the new channel was one lambda; in Java it was one small record."
   },
   "refs": [
    {"title": "Functional (SAM) interfaces (Kotlin docs)", "url": "https://kotlinlang.org/docs/fun-interfaces.html", "kind": "docs"}
   ]
  },
  {
   "h": "Flyweight: share immutable objects instead of building new ones",
   "body": S3,
   "try": {
    "title": "Find out which objects are shared",
    "minutes": 4,
    "steps": [
     "Read `FlyweightDemo.java` (or `FlyweightDemo.kt`) and predict all five lines before you run it.",
     "Run it with the command below.",
     "Break the pool: make `Mcc.of` return `new Mcc(code)` (Kotlin: make `MccCode.of` return `MccCode(code)`). Predict the last line, then run."
    ],
    "code": code("java", "FlyweightDemo.java", "FlyweightDemo", "kotlin", "FlyweightDemo.kt", "FlyweightDemoKt"),
    "expect": "127 is shared (`true`), 128 is not (`false`, though `equals` is `true`), a parsed `\"5411\"` is a different object until you call `intern()`, `Currency` hands out one EUR, and the pool gives one `Mcc` with `instances built: 1`. Without the pool the last line reads `false   instances built: 2`."
   },
   "refs": [
    {"title": "Integer.valueOf(int) (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Integer.html#valueOf(int)", "kind": "docs"},
    {"title": "Currency (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/Currency.html", "kind": "docs"}
   ]
  },
  {
   "h": "Share the tree, pass in the amount",
   "body": S4
  }
 ],
 "analogy": "Think of a print shop. A job is either one sheet or a folder of jobs, and you price both by asking the same question: what does this cost? That's Composite. The paper stock is a flyweight: a hundred jobs say \"A4, 90 g\" and all point at one stock description, while each job brings its own page count, the extrinsic part. The job and the machine are a bridge: any job can go to the laser printer or the plotter. The analogy breaks on sharing. Two jobs can't print on the same physical sheet, but two payments can use the same fee plan object at the same instant, because nothing in it ever changes.",
 "in_your_world": "Merchant onboarding probably stores fee plans as JSON or as rows in Oracle. Parse each plan into an immutable sealed tree once, cache it by plan id, and the pricing path in your Quarkus authorization service becomes a pure function, `fee(plan, amount)`, that you test with no database. Your notification service is a bridge whether or not anyone named it: alert types from Kafka topics on one side, channel adapters around the SMS and email vendors on the other. And a Kafka consumer that deserializes a million payment events an hour builds a million `\"EUR\"` strings; mapping them to `Currency.getInstance` and enums at the edge leaves one object per value. In Java code, compare those amounts with `equals` or as primitive `long`, never `==` on `Long`.",
 "mistake": "The most common mistake is comparing boxed numbers with `==` in Java: `if (entity.getAmountMinor() == expected)` where both are `Long`. It passes every unit test, because test amounts like 100 or 50 sit inside the -128 to 127 cache and come back as the same shared object. In production a 250.00 payment is 25,000 minor units, the two `Long`s are different objects, and the check is false. People make it because `==` works on `long`, and nothing in the code shows the boxing. Use `equals` or `Objects.equals(a, b)`, or better, keep amounts as primitive `long` in your domain types. In Kotlin, `==` already calls `equals`; only `===` has the bug, and the compiler warns on it.",
 "compare": {
  "title": "A flyweight that callers can't bypass",
  "java": {"title": "CardBin.java", "src": """// Not a record: a record's canonical constructor can't be private,
// so `new CardBin(...)` would always bypass the pool.
public final class CardBin {
    private static final Map<String, CardBin> POOL = new ConcurrentHashMap<>();

    private final String bin;          // first six digits of the card number
    private final String issuer;

    private CardBin(String bin, String issuer) {
        this.bin = bin;
        this.issuer = issuer;
    }

    public static CardBin of(String bin, Function<String, String> issuerLookup) {
        return POOL.computeIfAbsent(bin, b -> new CardBin(b, issuerLookup.apply(b)));   // built once per BIN
    }

    public String bin() { return bin; }
    public String issuer() { return issuer; }
}"""},
  "kotlin": {"title": "CardBin.kt", "src": """// A plain class: a private constructor holds, and there is no generated copy() to go around it.
class CardBin private constructor(val bin: String, val issuer: String) {
    companion object {
        private val pool = ConcurrentHashMap<String, CardBin>()

        fun of(bin: String, issuerLookup: (String) -> String): CardBin =
            pool.computeIfAbsent(bin) { CardBin(it, issuerLookup(it)) }   // built once per BIN
    }
}"""},
  "note": "Both use `computeIfAbsent`, so the lookup runs at most once per BIN even under contention. The real difference is what each language lets you hide. A Java record would be the natural value type, but javac rejects a private canonical constructor (\"attempting to assign stronger access privileges; was public\"), so anyone could call `new` and skip the pool: use a final class. In Kotlin, a `data class` with a private constructor still exposes a public `copy()` in 2.4.21 unless you add `@ConsistentCopyVisibility`, as *Builder and Prototype* showed, so a plain class is the safe choice there too. Kotlin also makes the flyweight's identity matter less: `==` calls `equals`, so the pool is about memory and one place to validate, not about making comparisons work. For a closed set, skip the pool and use an enum in either language."
 },
 "worked": {
  "title": "Turn an alert class explosion into a bridge",
  "steps": [
   {"say": "The notification module grew by inheritance. Count the classes, then count what a WhatsApp channel would cost.",
    "code": """abstract class Alert { abstract void send(); }

class PaymentFailedSms extends Alert   { void send() { sms.send(phone, "payment " + id + " failed"); } }
class PaymentFailedEmail extends Alert { void send() { mail.send(address, "Payment alert", "payment " + id + " failed"); } }
class FraudSuspectedSms extends Alert  { void send() { /* the SMS code again */ } }
class FraudSuspectedEmail extends Alert { void send() { /* the email code again */ } }
// WhatsApp: PaymentFailedWhatsApp, FraudSuspectedWhatsApp, and one more per future alert""", "lang": "java",
    "alt_code": """abstract class Alert { abstract fun send() }

class PaymentFailedSms : Alert()    { override fun send() = sms.send(phone, "payment $id failed") }
class PaymentFailedEmail : Alert()  { override fun send() = mail.send(address, "Payment alert", "payment $id failed") }
class FraudSuspectedSms : Alert()   { override fun send() { /* the SMS code again */ } }
class FraudSuspectedEmail : Alert() { override fun send() { /* the email code again */ } }
// WhatsApp: PaymentFailedWhatsApp, FraudSuspectedWhatsApp, and one more per future alert""", "alt_lang": "kotlin"},
   {"say": "Four classes for two alerts and two channels, and WhatsApp adds two more. Name the two dimensions: what happened decides the text, the channel decides the transport. Pull the transport out behind one interface, the implementor.",
    "code": """interface Channel { void deliver(String to, String body); }                // 1. the implementor side

record SmsChannel(SmsVendor sms) implements Channel {                        // 2. one class per transport,
    public void deliver(String to, String body) { sms.send(to, body); }      //    usually an adapter
}
record EmailChannel(MailVendor mail) implements Channel {
    public void deliver(String to, String body) { mail.send(to, "Payment alert", body); }
}""", "lang": "java",
    "alt_code": """fun interface Channel { fun deliver(to: String, body: String) }           // 1. the implementor side

class SmsChannel(private val sms: SmsVendor) : Channel {                     // 2. one class per transport,
    override fun deliver(to: String, body: String) = sms.send(to, body)      //    usually an adapter
}
class EmailChannel(private val mail: MailVendor) : Channel {
    override fun deliver(to: String, body: String) = mail.send(to, "Payment alert", body)
}""", "alt_lang": "kotlin"},
   {"say": "Each alert now holds a channel and builds only its text. Ask yourself: which alert type would change if the SMS vendor changed its API? None. Only `SmsChannel` would.",
    "code": """sealed interface Alert permits PaymentFailed, FraudSuspected { void raise(String to); }   // 3. the abstraction side

record PaymentFailed(Channel channel, String paymentId) implements Alert {
    public void raise(String to) { channel.deliver(to, "payment " + paymentId + " failed"); }
}
record FraudSuspected(Channel channel, String last4, int score) implements Alert {
    public void raise(String to) { channel.deliver(to, "card ****" + last4 + " flagged, risk " + score); }
}""", "lang": "java",
    "alt_code": """sealed interface Alert { fun raise(to: String) }                                        // 3. the abstraction side

data class PaymentFailed(val channel: Channel, val paymentId: String) : Alert {
    override fun raise(to: String) = channel.deliver(to, "payment $paymentId failed")
}
data class FraudSuspected(val channel: Channel, val last4: String, val score: Int) : Alert {
    override fun raise(to: String) = channel.deliver(to, "card ****$last4 flagged, risk $score")
}""", "alt_lang": "kotlin"},
   {"say": "Test each side alone. A recording lambda is a complete channel, so alert tests need no vendor at all. WhatsApp is now one class, and no alert changes.",
    "code": """List<String> sent = new ArrayList<>();
Channel recording = (to, body) -> sent.add(to + ": " + body);               // 4. a fake channel in one line

new PaymentFailed(recording, "pay_881").raise("on-call");
assertThat(sent).containsExactly("on-call: payment pay_881 failed");""", "lang": "java",
    "alt_code": """val sent = mutableListOf<String>()
val recording = Channel { to, body -> sent += "$to: $body" }                 // 4. a fake channel in one line

PaymentFailed(recording, "pay_881").raise("on-call")
assertThat(sent).containsExactly("on-call: payment pay_881 failed")""", "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "A pricing composite and a merchant-category flyweight",
  "minutes": 13,
  "files": [f"{lab}/main/{K}/PricingRule.kt", f"{lab}/main/{K}/MerchantCategory.kt"],
  "run": "./gradlew :patterns:test --tests 'workbench.patterns.l06.*'",
  "steps": [
   "Read the five node types in `PricingRule.kt`; they are given. Run the tests: all eight fail.",
   "Write `fee` as one `when (this)` with five branches and no `else`. Leaves compute; `AllOf` sums its children, `CheapestOf` takes their minimum, `Capped` takes `minOf(rule.fee(amountMinor), capMinor)`.",
   "Write `describe` the same way, following the formats in its KDoc.",
   "In `MerchantCategory`, add a private pool to the companion object and write `of`: reject unknown codes first, then return the pooled instance.",
   "Run the tests until all eight pass. Then add `data class Discount(val bps: Int) : PricingRule` to the sealed interface, read the two compiler errors, and delete it again."
  ],
  "hints": [
   "`rules.sumOf { it.fee(amountMinor) }` returns a `Long` when the lambda does, and an empty list sums to 0. `rules.minOf { ... }` works the same way for `CheapestOf`.",
   "`joinToString(\" + \", \"(\", \")\") { it.describe() }` takes a separator, a prefix and a postfix, and gives `()` for an empty list. `\"%d.%02d%%\".format(bps / 100, bps % 100)` turns 5 into `0.05%`.",
   "`requireNotNull(KNOWN[code]) { \"unknown MCC: $code\" }` throws `IllegalArgumentException`. Then `pool.computeIfAbsent(code) { MerchantCategory(it, description) }`: a `get` then `put` would let two threads both build one."
  ],
  "done_when": "All eight tests in `CompositeFlyweightTest` pass."
 },
 "drill": {
  "title": "The pricing composite from memory",
  "minutes": 5,
  "prompt": "Close this page. Write a sealed `Rule` with `Flat`, `Percent` and an immutable `AllOf`, and a `fee` function that prices any tree with one exhaustive switch (or `when`) and no default. Then price `AllOf(Flat(30), Percent(290))` on 10,000 in your head. You should get 320.",
  "answer": {"lang": "java", "src": """sealed interface Rule permits Flat, Percent, AllOf {}
record Flat(long minor) implements Rule {}
record Percent(int bps) implements Rule {}
record AllOf(List<Rule> rules) implements Rule {
    AllOf { rules = List.copyOf(rules); }        // immutable: copy what the caller passed
}

static long fee(Rule r, long amountMinor) {
    return switch (r) {                           // no default: a new node type breaks the build
        case Flat f -> f.minor();
        case Percent p -> amountMinor * p.bps() / 10_000;
        case AllOf a -> a.rules().stream().mapToLong(x -> fee(x, amountMinor)).sum();
    };
}""",
   "alt": {"lang": "kotlin", "title": "Kotlin", "src": """sealed interface Rule {
    data class Flat(val minor: Long) : Rule
    data class Percent(val bps: Int) : Rule
    class AllOf(rules: List<Rule>) : Rule {
        val rules: List<Rule> = rules.toList()    // immutable: copy what the caller passed
    }
}

fun fee(r: Rule, amountMinor: Long): Long = when (r) {   // no else: a new node type breaks the build
    is Rule.Flat -> r.minor
    is Rule.Percent -> amountMinor * r.bps / 10_000
    is Rule.AllOf -> r.rules.sumOf { fee(it, amountMinor) }
}"""}}
 },
 "recap": [
  "Composite: single items and groups share one interface, and a group answers by asking its children. A sealed type plus an exhaustive `switch` or `when` replaces the GoF `Component` class.",
  "Leave out `default` and `else`, and a new node type becomes a compile error at every operation that handles the tree.",
  "Keep trees immutable with `List.copyOf` in a compact constructor (Java) or `toList()` (Kotlin), so they can be shared by many merchants and threads.",
  "Bridge splits two dimensions that vary on their own, such as alert type and channel, so they cost N + M classes instead of N x M. You design it up front; an adapter is retrofitted.",
  "Flyweight shares immutable instances: the `Integer` cache for -128 to 127, interned strings, `Currency`, enums. Build your own with a private constructor and `computeIfAbsent`, over a bounded set.",
  "Never compare boxed numbers with `==` in Java. Kotlin's `==` calls `equals`."
 ],
 "quiz": [
  {"q": "In Java, two totals are read from two maps: `Long settled = ledger.get(\"EUR\"); Long expected = report.get(\"EUR\");`. Each holds 25,000, boxed separately. What does `settled == expected` return on a standard JVM?",
   "options": ["true, because the values are equal", "false, because they are two different `Long` objects", "It doesn't compile", "It throws `NullPointerException`"],
   "answer": 1,
   "why": "`==` on objects compares references. `Long.valueOf` shares instances only for -128 to 127, so two separately boxed 25,000s are different objects. With a test value of 100 the cache makes it pass, which is how this bug reaches production. Use `equals`, or primitive `long`."},
  {"q": "What fee does `AllOf(Flat(30), CheapestOf(Percent(290), Flat(250)))` charge on 10,000 minor units?",
   "options": ["570", "320", "280", "250"],
   "answer": 2,
   "why": "`Percent(290)` on 10,000 is 290 and `Flat(250)` is 250, so `CheapestOf` returns 250. `AllOf` adds the flat 30: 280. The tempting 320 prices the percentage and forgets that `CheapestOf` picks the minimum."},
  {"q": "You're designing payment notifications: four alert types today, three channels (SMS, email, Slack), and both lists will grow. Which structure fits?",
   "options": ["Alerts that hold a `Channel` interface, with one class or lambda per channel", "Twelve classes, one per alert and channel pair", "An adapter per alert type", "A singleton per channel that every alert extends"],
   "answer": 0,
   "why": "Two dimensions that vary on their own are the case for Bridge: 4 + 3 pieces, and a new channel works with every alert. Twelve classes become fifteen with the next alert. An adapter fixes one mismatched interface, and extending a singleton puts the channel back into the class hierarchy."},
  {"q": "To save memory, a service puts every merchant name it receives in webhook payloads into a static `ConcurrentHashMap` pool and reuses the pooled string. What goes wrong over time?",
   "options": ["Two threads can get different instances for the same name", "Nothing: `ConcurrentHashMap` is thread-safe", "The pool grows with every new name and never shrinks: a slow memory leak", "Pooled strings can't be compared with `equals` any more"],
   "answer": 2,
   "why": "A flyweight pool must be bounded. Merchant names from outside are an open set, so the map keeps every name ever seen for the life of the JVM. Pool a known set (currencies, category codes from a reference table) or use a cache with eviction. Thread safety isn't the issue here; `computeIfAbsent` handles that."},
  {"q": "From *Don't share: immutability, confinement, ThreadLocal*: a fee plan tree is built once at startup from records whose lists go through `List.copyOf`, kept in a `static final` field, and read by 200 request threads. What do the reads need?",
   "options": ["A `synchronized` block around each `fee` call", "The read side of a `ReadWriteLock`", "`volatile` on every record field", "Nothing: the tree is immutable and safely published"],
   "answer": 3,
   "why": "Record fields are final, `List.copyOf` returns an unmodifiable list, and a `static final` field is published safely by class initialization. Nothing ever writes after that, so there is nothing to race on, and locks would only add contention.",
   "from": "conc-11"}
 ],
 "flashcards": [
  {"front": "What does Composite let you do?", "back": "Treat a single item and a group of items through one interface. A group answers by asking its children, so callers never check which one they hold."},
  {"front": "Why leave `default` out of the switch that walks a sealed composite?", "back": "So adding a node type is a compile error at every operation that handles the tree, instead of a silent fallback."},
  {"front": "What problem does Bridge solve?", "back": "Two dimensions that vary on their own (alert type and channel) without N x M classes: the abstraction holds an implementor and calls it."},
  {"front": "Bridge or Adapter: which one is designed up front?", "back": "Bridge. An adapter is retrofitted, to make a class you can't change fit your interface."},
  {"front": "Java: `Integer a = 128, b = 128;` What is `a == b`?", "back": "false with default settings. `Integer.valueOf` caches only -128 to 127; 128 gives two different objects."},
  {"front": "Why must a flyweight be immutable?", "back": "Every holder shares the same instance, so a change made by one would show up for all of them, on every thread."},
  {"front": "Why does a flyweight factory use `computeIfAbsent` instead of `get` then `put`?", "back": "`computeIfAbsent` checks and inserts in one atomic step, so concurrent callers get one instance. `get` then `put` is check-then-act and can build duplicates."}
 ],
 "terms": [
  {"term": "Composite", "plain": "A tree where groups and single items share one interface, so you handle both the same way."},
  {"term": "Leaf", "plain": "A node in a composite with no children, such as `Flat(30)`."},
  {"term": "Bridge", "plain": "Splitting two independent dimensions so one side holds the other through an interface."},
  {"term": "Implementor", "plain": "In a bridge, the side that does the low-level work, such as a `Channel` that delivers messages."},
  {"term": "Flyweight", "plain": "A small immutable object shared by many users instead of copied for each."},
  {"term": "Intrinsic and extrinsic state", "plain": "Intrinsic state lives in the shared flyweight; extrinsic state comes from the caller with each use."},
  {"term": "Canonicalizing factory", "plain": "A factory that returns the one pooled instance for a key, such as `Currency.getInstance(\"EUR\")`."}
 ],
 "explain_back": {
  "prompt": "Explain to a teammate why `fee` takes the payment amount as a parameter instead of storing it in the plan, and why that lets 40,000 merchants and 200 request threads share a dozen plan objects safely.",
  "answer": "The plan holds only what is the same for every use: the rates, fixed fees and caps. That is its intrinsic state. The amount changes with every payment, so it is extrinsic state, and the caller passes it in. Because the plan never stores anything per payment, one plan object can serve every merchant on that plan. It is also immutable: record fields are final and the child lists are copied with `List.copyOf`. Once it's published safely, for example in a `static final` field built at startup, any number of threads can read it at the same time with no locks, because nothing ever writes to it. If the plan kept \"the current amount\" in a field, two threads pricing at once would overwrite each other, and you'd need one plan per merchant or a lock on every call."
 },
 "deeper": {
  "minutes": 10,
  "body": """The GoF book spends pages on Composite's "transparency versus safety" choice: should `add` and `remove` live on the shared `Component` type, so leaves must throw, or only on groups, so callers must cast? A sealed type with immutable records ends the debate. There are no child-management methods at all: you build a new tree. Pattern matching gives each operation exact access to each node type, with no casts.

Recursion over a tree is fine for fee plans a few levels deep. A tree built from outside input (a rules engine fed by a merchant portal, say) could be thousands of levels deep and throw `StackOverflowError`. Validate the depth when you build the tree, or walk it with an explicit stack. Composite also pairs with Visitor; lesson 10 of this track, *Visitor, Iterator, Mediator and Memento*, shows why sealed types and pattern matching usually replace it.

The `Integer` cache bounds are part of the contract: `valueOf` "will always cache values in the range -128 to 127, inclusive, and may cache other values outside of this range". The upper bound can be raised with the `java.lang.Integer.IntegerCache.high` system property. That can make a boxed `==` bug disappear on one JVM and show up on another, which is one more reason never to rely on it.

String interning has a GC cousin. G1's `-XX:+UseStringDeduplication` lets the collector make duplicate `String` objects share one backing array, with no code change. It saves memory for services that hold many equal strings (currency codes, country codes, status names) but doesn't make `==` work, because the `String` objects themselves stay distinct."""
 },
 "sources": [
  {"title": "Sealed classes and interfaces (Kotlin docs)", "url": "https://kotlinlang.org/docs/sealed-classes.html"},
  {"title": "Integer.java at jdk-25-ga (valueOf and IntegerCache)", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Integer.java"},
  {"title": "Currency.java at jdk-25-ga", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/Currency.java"},
  {"title": "JLS 5.1.7: Boxing conversion", "url": "https://docs.oracle.com/javase/specs/jls/se25/html/jls-5.html#jls-5.1.7"},
  {"title": "JLS 8.10: Record classes", "url": "https://docs.oracle.com/javase/specs/jls/se25/html/jls-8.html#jls-8.10"}
 ]
}

out = ROOT / "content/lessons/pat-06.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print("wrote", out)
