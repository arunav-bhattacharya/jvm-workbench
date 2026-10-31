import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/patterns/src"
J = "java/workbench/patterns/l03"
K = "kotlin/workbench/patterns/l03"
read = lambda p: (ROOT / p).read_text()
demo = lambda cls: f"./gradlew :patterns:demo -Pmain=workbench.patterns.l03.{cls}"

FIG = """<svg viewBox="0 0 660 250" role="img" aria-label="Left: a shallow copy, where c1 and c2 point to the same list. Right: a safe copy, where each cart has its own list">
<text class="t t-bad" x="165" y="24" text-anchor="middle">shallow copy</text>
<text class="t t-ok" x="500" y="24" text-anchor="middle">copy, then build a new list</text>
<rect class="box" x="20" y="50" width="130" height="40" rx="8"/>
<text class="t t-code" x="85" y="75" text-anchor="middle">c1</text>
<rect class="box" x="20" y="150" width="130" height="40" rx="8"/>
<text class="t t-code" x="85" y="175" text-anchor="middle">c2 = c1.copy()</text>
<rect class="box-bad" x="190" y="100" width="130" height="40" rx="8"/>
<text class="t-s t-code" x="255" y="125" text-anchor="middle">[sku-1, sku-2]</text>
<line class="ln-bad" x1="150" y1="72" x2="188" y2="110" marker-end="url(#arr)"/>
<line class="ln-bad" x1="150" y1="168" x2="188" y2="130" marker-end="url(#arr)"/>
<text class="t-s t-bad" x="170" y="225" text-anchor="middle">c2.skus += "sku-2" changes c1 too</text>
<line class="ln-d" x1="335" y1="40" x2="335" y2="235"/>
<rect class="box" x="355" y="50" width="130" height="40" rx="8"/>
<text class="t t-code" x="420" y="75" text-anchor="middle">c1</text>
<rect class="box" x="355" y="150" width="130" height="40" rx="8"/>
<text class="t t-code" x="420" y="175" text-anchor="middle">c2</text>
<rect class="box-ok" x="515" y="50" width="130" height="40" rx="8"/>
<text class="t-s t-code" x="580" y="75" text-anchor="middle">[sku-1]</text>
<rect class="box-ok" x="515" y="150" width="130" height="40" rx="8"/>
<text class="t-s t-code" x="580" y="175" text-anchor="middle">[sku-1, sku-2]</text>
<line class="ln-a" x1="485" y1="70" x2="511" y2="70" marker-end="url(#arr)"/>
<line class="ln-a" x1="485" y1="170" x2="511" y2="170" marker-end="url(#arr)"/>
<text class="t-s t-ok" x="500" y="225" text-anchor="middle">copy(skus = skus + "sku-2")</text>
</svg>""".replace("\n", "")

S1 = """A builder exists to fix the telescoping constructor: one constructor per combination of optional parameters, and call sites full of unlabeled literals.

```java
new ChargeRequest(1_250, "EUR", "tok_42", null, null, true, 2, 30_000);   // which one is the timeout?
```

```kotlin
ChargeRequest(1_250, "EUR", "tok_42", null, null, true, 2, 30_000)         // Kotlin allows the same mess
```

The Java fix is the builder from Effective Java item 2: a mutable helper class with one method per field and a `build()` at the end. It works, and it costs you a second class that repeats every field.

Kotlin removes the problem in the language. Parameters can have defaults, and callers can name them:

```kotlin
data class ChargeRequest(
    val amountMinor: Long,
    val currency: String,
    val token: String,
    val description: String? = null,
    val capture: Boolean = true,
    val maxRetries: Int = 0,
    val timeoutMs: Long = 10_000,
) {
    init { require(maxRetries >= 0) { "maxRetries must be >= 0" } }
}

val req = ChargeRequest(amountMinor = 1_250, currency = "EUR", token = "tok_42", maxRetries = 2)
val slower = req.copy(timeoutMs = 30_000)
```

```java
// Java has no named or default arguments: the record keeps the rules, a builder supplies the defaults
record ChargeRequest(long amountMinor, String currency, String token, String description,
                     boolean capture, int maxRetries, long timeoutMs) {
    ChargeRequest {
        if (maxRetries < 0) throw new IllegalArgumentException("maxRetries must be >= 0");
    }
    ChargeRequest withTimeoutMs(long ms) {
        return new ChargeRequest(amountMinor, currency, token, description, capture, maxRetries, ms);
    }
}

var req = ChargeRequest.builder(1_250, "EUR", "tok_42").maxRetries(2).build();   // the builder: next section
var slower = req.withTimeoutMs(30_000);
```

In the Kotlin version, every argument at the call site says what it is. Optional ones can be skipped, in any order. `copy` gives you a changed copy for free. And the `init` block runs for every construction, `copy` included, so nobody can skip the validation. That covers what most Java builders do.

Java callers are the gap. Java has no named arguments, so they see one constructor with seven parameters. `@JvmOverloads` on the constructor generates the telescoping overloads for them (one per trailing default), which is better than nothing and worse than a builder. If a Java team will call the class a lot, give them a real builder.

A rule of thumb for porting: if every call site of a Java builder sets two or three fields and leaves the rest at their defaults, the Kotlin version is a data class with defaults and nothing else. If call sites build the object across a loop or an `if`, keep a builder, as the next section explains."""

S2 = """Builders still win in four cases. The first is Java callers, as above. The second is validation that needs the whole object: "a statement descriptor is at most 22 characters, and only when `capture` is true" relates two fields. The third is construction spread across steps, such as headers added in a loop or 3-D Secure data added only for some cards; Kotlin's `buildList { }` and `buildString { }` are standard-library builders for exactly this. The fourth is nested data, which gets its own section next.

The modern Java shape is a record that validates plus a small builder that only collects:

```java
record IssuerCall(String url, String method, Map<String, String> headers, Duration timeout, int maxRetries) {
    IssuerCall {                                 // compact constructor: runs on every path
        Objects.requireNonNull(url, "url");
        headers = Map.copyOf(headers);           // immutable, and a copy
        if (maxRetries < 0) throw new IllegalArgumentException("maxRetries must be >= 0");
    }
    IssuerCall withTimeout(Duration t) { return new IssuerCall(url, method, headers, t, maxRetries); }
    static Builder builder(String url) { return new Builder(url); }
    // Builder: fields with defaults, one setter each, and build() calls the constructor
}
```

```kotlin
data class IssuerCall(
    val url: String,
    val method: String = "GET",
    val headers: Map<String, String> = emptyMap(),
    val timeout: Duration = Duration.ofSeconds(2),
    val maxRetries: Int = 0,
) {
    init { require(maxRetries >= 0) { "maxRetries must be >= 0" } }   // runs on every path, copy() too
}
// no builder and no withers: named arguments and copy(timeout = ...) do both jobs
```

The builder holds no rules. The rules live in the compact constructor, which `build()`, the wither `withTimeout` and a direct `new IssuerCall(...)` all go through. Withers are how you get Prototype on a record: Java has no `with` syntax, so you write one small method per field you want to change. The Kotlin twin needs neither builder nor withers, and its `init` block plays the role of the compact constructor.

The JDK's newer APIs follow the same idea of a builder that produces an immutable result: `HttpClient.newBuilder()`, and `Thread.ofVirtual()`, which returns a `Thread.Builder`.

One builder bug deserves a name. If `build()` validates but the class also has a public constructor that doesn't, half the code base skips the rules. Put the rules in the type, never only in the builder."""

S3 = """For nested data, Kotlin lets you write a builder that reads like a configuration file:

```kotlin
val req = paymentRequest {
    idempotencyKey = "order-981-attempt-1"
    lineItems {
        item("sku-1", 1_000)
        item("sku-2", 500)
    }
    metadata("orderId", "981")
}
```

```java
// Java has no lambdas with receivers; the closest is a Consumer that receives the builder
PaymentRequest req = paymentRequest(r -> {
    r.idempotencyKey("order-981-attempt-1");
    r.lineItems(items -> {
        items.item("sku-1", 1_000);
        items.item("sku-2", 500);
    });
    r.metadata("orderId", "981");
});
```

The trick is a **lambda with receiver**. `paymentRequest` takes a `PaymentRequestBuilder.() -> Unit`: a function that runs with a builder as `this`. Inside the braces, `idempotencyKey` and `lineItems` are members of that builder:

```kotlin
fun paymentRequest(block: PaymentRequestBuilder.() -> Unit): PaymentRequest =
    PaymentRequestBuilder().apply(block).build()

class PaymentRequestBuilder {
    var idempotencyKey: String? = null
    private val items = mutableListOf<LineItem>()
    fun lineItems(block: LineItemsBuilder.() -> Unit) { items += LineItemsBuilder().apply(block).build() }
    fun build(): PaymentRequest { /* validate, then copy into the request */ }
}
```

```java
static PaymentRequest paymentRequest(Consumer<PaymentRequestBuilder> block) {
    PaymentRequestBuilder b = new PaymentRequestBuilder();
    block.accept(b);                                   // the block gets the builder as a parameter
    return b.build();
}

final class PaymentRequestBuilder {
    private String idempotencyKey;
    private final List<LineItem> items = new ArrayList<>();
    void idempotencyKey(String key) { idempotencyKey = key; }
    void lineItems(Consumer<LineItemsBuilder> block) {
        LineItemsBuilder b = new LineItemsBuilder();
        block.accept(b);
        items.addAll(b.build());
    }
    PaymentRequest build() { /* validate, then copy into the request */ }
}
```

Gradle's Kotlin DSL, Ktor routing and kotlinx.html are built the same way. The Java shape, a `Consumer` per block, is what Spring Security's lambda configuration uses. The builder is still a builder: `build()` is the one place that sees every field, so it validates there.

There is one trap. Inside `lineItems { }`, two receivers are in scope: the `LineItemsBuilder` and the outer `PaymentRequestBuilder`. So `idempotencyKey = "x"` written inside the inner block compiles and quietly sets the outer field. `@DslMarker` closes that hole:

```kotlin
@DslMarker annotation class PaymentDsl

@PaymentDsl class PaymentRequestBuilder { ... }
@PaymentDsl class LineItemsBuilder { ... }
```

```java
// Java needs no marker: each block names its builder, so reaching the outer one means typing r
r.lineItems(items -> {
    items.item("sku-1", 1_000);
    r.idempotencyKey("x");       // compiles, but you can see it in review
});
```

With both builders marked, the compiler only lets you call members of the nearest receiver without a prefix. Reaching the outer one needs an explicit label, `this@paymentRequest.idempotencyKey`, which nobody writes by accident.

Build a DSL only when the data nests. A flat request with seven fields is clearer with named arguments, and a DSL would add two classes and a layer of indirection for nothing. The payoff comes with structure: line items under a payment, split payouts under a marketplace order, routing rules under a merchant. It also helps when many people write the same kind of configuration, because inside each block the IDE offers only that builder's methods."""

S4 = """Prototype means making a new object by copying an existing one and changing a few fields. Payment code does this constantly: a recurring-charge template copied per merchant, a default config copied per tenant, a test fixture copied per test.

Java's original mechanism, `Cloneable`, is broken by design. The interface has no `clone` method, so implementing it gives callers nothing to call. `Object.clone()` is protected and makes a shallow copy. To use it you override `clone`, call `super.clone()`, catch a `CloneNotSupportedException` that can't happen, and then fix every mutable field by hand. Skip it. Use a copy constructor, a static copy factory, or a wither on a record.

Records make withers easy to write and Kotlin data classes generate `copy()`. Neither copies deeply. The Kotlin docs say it plainly: `copy()` creates a shallow copy, and references to other objects are shared.

```kotlin
data class Cart(val id: String, val skus: MutableList<String>)
val c1 = Cart("c1", mutableListOf("sku-1"))
val c2 = c1.copy(id = "c2")
c2.skus += "sku-2"          // c1.skus is now [sku-1, sku-2]
```

```java
record Cart(String id, List<String> skus) {
    Cart withId(String newId) { return new Cart(newId, skus); }   // a wither: shares the list
}
var c1 = new Cart("c1", new ArrayList<>(List.of("sku-1")));
var c2 = c1.withId("c2");
c2.skus().add("sku-2");     // c1.skus() is now [sku-1, sku-2]
```

The fix is the same in both languages. Store collections you can't change (`List.copyOf` in a compact constructor in Java; a read-only `List` in Kotlin), and let withers build a new collection: `copy(skus = skus + "sku-2")`.

Kotlin has a second trap. `data class Email private constructor(val value: String)` still gets a public `copy()`, so `Email.of("anna@example.com").copy(value = "not-an-email")` compiles and skips your factory. Kotlin 2.4 only warns, and the warning says it becomes an error in language version 2.5. Add `@ConsistentCopyVisibility` to make `copy()` as private as the constructor in the current release. Validation in an `init` block is safer still, because `copy()` runs it. Java records never had the private-constructor illusion: a record's canonical constructor can't be less visible than the record, so the rules belong in the compact constructor from the start."""

L = {
 "id": "pat-03",
 "title": "Builder and Prototype",
 "minutes": 38,
 "goal": "By the end you can choose between named arguments, a Java record plus builder, and a Kotlin DSL builder, and make copies of templates that never share mutable state with the original.",
 "warmup": {
  "q": "`data class Cart(val id: String, val skus: MutableList<String>)`. You run `val c2 = c1.copy(id = \"c2\")` and then `c2.skus += \"sku-2\"`. What happens to `c1.skus`?",
  "options": ["Nothing: `copy()` makes a deep copy", "It now contains `sku-2` too, because both carts share one list", "It throws, because data class properties are immutable", "It depends on whether `c1` was declared with `val`"],
  "answer": 1,
  "why": "`copy()` is shallow. It copies the reference to the list, not the list, so `c1` and `c2` hold the same `MutableList`. `val` only stops you from pointing the property at another list; it says nothing about the list's contents. Records in Java behave the same way."
 },
 "sections": [
  {
   "h": "Named and default arguments replace most builders",
   "body": S1,
   "refs": [
    {"title": "Functions: named and default arguments (Kotlin docs)", "url": "https://kotlinlang.org/docs/functions.html", "kind": "docs"},
    {"title": "Effective Java 3e source, item 2: the Builder", "url": "https://raw.githubusercontent.com/jbloch/effective-java-3e-source-code/master/src/effectivejava/chapter2/item2/builder/NutritionFacts.java", "kind": "read"}
   ]
  },
  {
   "h": "When a builder still earns its place",
   "body": S2,
   "try": {
    "title": "Find where the rules live",
    "minutes": 4,
    "steps": [
     "Run `RecordBuilderDemo` with the command below and read the four lines.",
     "In the Java `main`, change `.maxRetries(2)` to `.maxRetries(-1)` (in Kotlin, `maxRetries = -1`). Predict: which line throws, and from where? Run it.",
     "Undo the change."
    ],
    "code": {"lang": "java", "title": "RecordBuilderDemo.java", "src": read(f"{lab}/demo/{J}/RecordBuilderDemo.java"),
             "run": demo("RecordBuilderDemo"), "file": f"{lab}/demo/{J}/RecordBuilderDemo.java",
             "alt": {"lang": "kotlin", "title": "RecordBuilderDemo.kt", "src": read(f"{lab}/demo/{K}/RecordBuilderDemo.kt"),
                     "run": demo("RecordBuilderDemoKt"), "file": f"{lab}/demo/{K}/RecordBuilderDemo.kt"}},
    "expect": "The first run prints the built call, `PT0.8S` for the faster copy, `headers: unmodifiable` and `wither: maxRetries must be >= 0, was -1`. With `.maxRetries(-1)` the program dies in `build()`, and the stack trace points into the record's compact constructor: the builder has no rules of its own, so it can't forget any. The Kotlin twin fails in the same place, its `init` block, and prints `copy(): maxRetries must be >= 0, was -1` for the copy."
   },
   "refs": [
    {"title": "HttpClient.Builder (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.net.http/java/net/http/HttpClient.Builder.html", "kind": "docs"}
   ]
  },
  {
   "h": "Type-safe builders: lambdas with receivers and @DslMarker",
   "body": S3,
   "try": {
    "title": "Make the inner block reach outside",
    "minutes": 5,
    "steps": [
     "Run `DslScope.kt` with the command below.",
     "Uncomment the line `reason = \"oops\"` inside the `refunds { }` block. Predict, then run.",
     "Now delete both `@RefundDsl` lines above the two builder classes (keep the annotation class itself) and run again. What is the batch's reason?",
     "Restore the file. Then open the Java twin and uncomment `batchB.reason(\"oops\")`: it compiles, but notice that you had to type the outer builder's name."
    ],
    "code": {"lang": "kotlin", "title": "DslScope.kt", "src": read(f"{lab}/demo/{K}/DslScope.kt"),
             "run": demo("DslScopeKt"), "file": f"{lab}/demo/{K}/DslScope.kt",
             "alt": {"lang": "java", "title": "DslScopeJava.java", "src": read(f"{lab}/demo/{J}/DslScopeJava.java"),
                     "run": demo("DslScopeJava"), "file": f"{lab}/demo/{J}/DslScopeJava.java"}},
    "expect": "The first run prints a batch with reason `duplicate charge` and `total refunded: 2240`. With the line uncommented, the build fails: `'var reason: String' cannot be called in this context with an implicit receiver. Use an explicit receiver if necessary.` Without the marker it compiles and prints `reason=oops`: the inner block silently rewrote the outer batch."
   },
   "refs": [
    {"title": "Type-safe builders (Kotlin docs)", "url": "https://kotlinlang.org/docs/type-safe-builders.html", "kind": "docs"}
   ]
  },
  {
   "h": "Prototype: every copy is shallow until you make it deep",
   "body": S4,
   "figure": {"svg": FIG, "caption": "A shallow copy shares the list, so changing one cart changes both. Build a new list in the copy instead."},
   "try": {
    "title": "Spring both copy traps",
    "minutes": 4,
    "steps": [
     "Read `CopyTrap.kt` (or its Java twin) and predict the three lines it prints.",
     "Run it. If Gradle recompiles the file, read the `w:` warnings too.",
     "Add `@ConsistentCopyVisibility` on the line above `data class Email` and run again."
    ],
    "code": {"lang": "kotlin", "title": "CopyTrap.kt", "src": read(f"{lab}/demo/{K}/CopyTrap.kt"),
             "run": demo("CopyTrapKt"), "file": f"{lab}/demo/{K}/CopyTrap.kt",
             "alt": {"lang": "java", "title": "CopyTrapJava.java", "src": read(f"{lab}/demo/{J}/CopyTrapJava.java"),
                     "run": demo("CopyTrapJava"), "file": f"{lab}/demo/{J}/CopyTrapJava.java"}},
    "expect": "It prints `c1.skus after changing c2: [sku-1, sku-2]` (the copy shared the list), `copy() skipped the factory: Email(value=not-an-email)`, and `negative amount: -1`, because `init` runs on `copy()`. The compiler warns that the non-public primary constructor is exposed via `copy()`. With `@ConsistentCopyVisibility`, the build stops with `Cannot access 'fun copy(value: String = ...): Email': it is private`. The Java twin prints the same story: the wither shares the list, `new Email(\"not-an-email\")` skips the factory, and the compact constructor rejects `-1`."
   },
   "refs": [
    {"title": "Data classes: copying (Kotlin docs)", "url": "https://kotlinlang.org/docs/data-classes.html", "kind": "docs"}
   ]
  }
 ],
 "analogy": "A builder is an order form at a card-printing desk: you tick the boxes you care about, leave the rest at their defaults, and the clerk checks the whole form before printing anything. Kotlin's named arguments are a form so short you fill it in at the counter. Prototype is photocopying a filled-in form and changing two fields. The analogy breaks on the shallow copy: a photocopy is a real, separate piece of paper, while `copy()` gives you a new form that still points at the same attached sheet of line items, so writing on the copy's attachment writes on the original's.",
 "in_your_world": "Payment requests to an issuer have a dozen optional fields: descriptor, 3-D Secure data, metadata, capture mode, retry policy. In Kotlin services, a data class with defaults and an `init` block is all you need. For a shared client library that Java services call, add a builder. Test fixtures are prototypes: one `baseAuthorization` copied per test with `copy(amountMinor = 0)`. If that fixture holds a `MutableList` of line items, one test can poison every test after it. The same goes for a Quarkus `@ApplicationScoped` bean that hands out a default config object which callers then copy and modify.",
 "mistake": "The most common mistake is trusting `copy()` or a record wither to make an independent object when a component is mutable. A `MutableList`, a `HashMap`, an array or a mutable `Date` is shared between the original and the copy, so changing one changes both. It happens because the class looks immutable: every property is `val`, or it's a record. The fix is to store copies that can't change (`List.copyOf` in a compact constructor, read-only types and `toList()` in Kotlin), and to make withers build new collections instead of mutating the shared one.",
 "compare": {
  "title": "A prototype that copies safely",
  "java": {"title": "TenantConfig.java", "src": """record TenantConfig(String tenantId, List<String> paymentMethods, Map<String, Long> dailyLimits) {
    TenantConfig {                                        // every copy passes through here
        paymentMethods = List.copyOf(paymentMethods);
        dailyLimits = Map.copyOf(dailyLimits);
    }

    TenantConfig forTenant(String id) {                   // safe to share: nothing can change
        return new TenantConfig(id, paymentMethods, dailyLimits);
    }

    TenantConfig withMethod(String method) {              // copy, change the copy, wrap again
        var methods = new ArrayList<>(paymentMethods);
        methods.add(method);
        return new TenantConfig(tenantId, methods, dailyLimits);
    }
}

var base = new TenantConfig("default", List.of("CARD"), Map.of("CARD", 500_000L));
var acme = base.forTenant("acme").withMethod("SEPA");"""},
  "kotlin": {"title": "TenantConfig.kt", "src": """data class TenantConfig(
    val tenantId: String,
    val paymentMethods: List<String>,          // read-only types
    val dailyLimits: Map<String, Long>,
)

val base = TenantConfig("default", listOf("CARD"), mapOf("CARD" to 500_000L))
val acme = base.copy(
    tenantId = "acme",
    paymentMethods = base.paymentMethods + "SEPA",  // + builds a new list
)"""},
  "note": "Kotlin generates `copy()` with named arguments, so it needs no withers, and `+` on a read-only `List` or `Map` returns a new collection. Java needs one hand-written wither per field. Both copies are shallow, and the safety comes from the components, not from the copy. There is one real difference: Java's compact constructor can replace the incoming list with `List.copyOf`, while a Kotlin data class property can't be reassigned in `init`. A Kotlin `List` parameter is only read-only, so a caller who passes a `MutableList` and keeps a reference can still change it. If that matters, take the list as a plain constructor parameter and store `toList()` in a property."
 },
 "worked": {
  "title": "From a telescoping constructor to a record and builder, and to a Kotlin class",
  "steps": [
   {"say": "Here is a call to an issuer charge request with eight positional arguments. Before reading on, say which argument is the statement descriptor, and which rule you'd expect `ChargeRequest` to enforce.",
    "code": """new ChargeRequest(1_250, "EUR", "tok_42", "ACME*ORDER 981", null, true, 2, 30_000);""", "lang": "java",
    "alt_code": """ChargeRequest(1_250, "EUR", "tok_42", "ACME*ORDER 981", null, true, 2, 30_000)""", "alt_lang": "kotlin"},
   {"say": "Put every rule in one place that all paths go through: the record's compact constructor in Java, the `init` block in Kotlin. The cross-field rule (a descriptor only on captured charges, and 22 characters at most) can only be checked where all fields are known. Kotlin also gets its defaults here, which is half of what a builder does.",
    "code": """record ChargeRequest(long amountMinor, String currency, String token, String descriptor,
                     String threeDsData, boolean capture, int maxRetries, long timeoutMs) {
    ChargeRequest {
        if (amountMinor <= 0) throw new IllegalArgumentException("amount must be positive");       // 1. single-field rules
        if (maxRetries < 0) throw new IllegalArgumentException("maxRetries must be >= 0");
        if (descriptor != null && (!capture || descriptor.length() > 22))                          // 2. cross-field rule
            throw new IllegalArgumentException("descriptor needs capture=true and at most 22 chars");
    }
}""", "lang": "java",
    "alt_code": """data class ChargeRequest @JvmOverloads constructor(
    val amountMinor: Long,
    val currency: String,
    val token: String,
    val descriptor: String? = null,                                  // 3. defaults live in the signature
    val threeDsData: String? = null,
    val capture: Boolean = true,
    val maxRetries: Int = 0,
    val timeoutMs: Long = 10_000,
) {
    init {
        require(amountMinor > 0) { "amount must be positive" }                   // 1. single-field rules
        require(maxRetries >= 0) { "maxRetries must be >= 0" }
        require(descriptor == null || (capture && descriptor.length <= 22)) {     // 2. cross-field rule
            "descriptor needs capture=true and at most 22 chars"
        }
    }
}""", "alt_lang": "kotlin"},
   {"say": "Java needs a builder that only collects and supplies defaults; its `build()` calls the canonical constructor, so the rules run there. Kotlin needs no builder: named arguments do the job, and `@JvmOverloads` gives Java callers some overloads. If Java teams call the Kotlin class often, add a builder for them too.",
    "code": """static final class Builder {
    private final long amountMinor; private final String currency; private final String token;
    private String descriptor; private String threeDsData;
    private boolean capture = true; private int maxRetries = 0; private long timeoutMs = 10_000;    // 3. defaults

    Builder(long amountMinor, String currency, String token) {
        this.amountMinor = amountMinor; this.currency = currency; this.token = token;              // 4. required up front
    }
    Builder descriptor(String d) { descriptor = d; return this; }
    Builder maxRetries(int n) { maxRetries = n; return this; }
    Builder timeoutMs(long ms) { timeoutMs = ms; return this; }
    ChargeRequest build() {
        return new ChargeRequest(amountMinor, currency, token, descriptor, threeDsData, capture, maxRetries, timeoutMs);
    }
}

var req = new ChargeRequest.Builder(1_250, "EUR", "tok_42").descriptor("ACME*ORDER 981").maxRetries(2).build();""", "lang": "java",
    "alt_code": """// 4. required values have no default, so the compiler insists on them
val req = ChargeRequest(1_250, "EUR", "tok_42", descriptor = "ACME*ORDER 981", maxRetries = 2)
val retryFaster = req.copy(timeoutMs = 2_000)        // the "wither" is generated""", "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "A validating payment DSL, and a prototype that stops leaking",
  "minutes": 14,
  "files": [f"{lab}/main/{K}/PaymentRequestDsl.kt", f"{lab}/main/{J}/ChargeTemplate.java"],
  "run": "./gradlew :patterns:test --tests 'workbench.patterns.l03.*'",
  "steps": [
   "Run the tests. Twelve of thirteen fail: the DSL is all `TODO`, and `ChargeTemplate` leaks tags and metadata between copies.",
   "In `PaymentRequestDsl.kt`, write `LineItemsBuilder`: keep a private `MutableList`, and return `toList()` from `build()`.",
   "Write `PaymentRequestBuilder`: `lineItems` runs the block on a fresh `LineItemsBuilder` and keeps its items; `metadata` puts into a private map; `build()` validates with `require` and copies the collections into the `PaymentRequest`. Then write `paymentRequest`.",
   "Put `@PaymentDsl` on both builder classes.",
   "Fix `ChargeTemplate.java`: add a compact constructor that stores `List.copyOf` and `Map.copyOf`, and make the withers copy the collection, change the copy, and build a new template.",
   "Run the tests until all thirteen pass."
  ],
  "hints": [
   "`require(condition) { \"idempotency key is required\" }` throws `IllegalArgumentException` with that message when the condition is false.",
   "`currency.matches(Regex(\"[A-Z]{3}\"))` checks for three capital letters.",
   "`LineItemsBuilder().apply(block).build()`: `apply` runs the lambda with the builder as `this` and returns the builder.",
   "In a record's compact constructor, `tags = List.copyOf(tags);` reassigns the parameter before the field is set. You don't write `this.tags = ...`."
  ],
  "done_when": "All thirteen tests in `PaymentDslTest` and `ChargeTemplateTest` pass."
 },
 "drill": {
  "title": "A two-level DSL from memory",
  "minutes": 6,
  "prompt": "Close this page. Write `fun refundBatch(block: RefundBatchBuilder.() -> Unit): RefundBatch`, where the builder has a `var reason` and a nested `refunds { refund(paymentId, amountMinor) }` block, and `@DslMarker` stops the inner block from setting `reason`. Then compare with the answer, and with the Java twin built from `Consumer`s.",
  "answer": {"lang": "kotlin", "src": """@DslMarker annotation class RefundDsl

data class Refund(val paymentId: String, val amountMinor: Long)
data class RefundBatch(val reason: String, val refunds: List<Refund>)

@RefundDsl
class RefundsBuilder {
    private val refunds = mutableListOf<Refund>()
    fun refund(paymentId: String, amountMinor: Long) { refunds += Refund(paymentId, amountMinor) }
    fun build() = refunds.toList()
}

@RefundDsl
class RefundBatchBuilder {
    var reason: String = "unspecified"
    private var refunds: List<Refund> = emptyList()
    fun refunds(block: RefundsBuilder.() -> Unit) { refunds = RefundsBuilder().apply(block).build() }
    fun build() = RefundBatch(reason, refunds)
}

fun refundBatch(block: RefundBatchBuilder.() -> Unit): RefundBatch =
    RefundBatchBuilder().apply(block).build()""",
   "alt": {"lang": "java", "title": "Java", "src": """// Java has no lambdas with receivers: each block is a Consumer of its builder
record Refund(String paymentId, long amountMinor) {}
record RefundBatch(String reason, List<Refund> refunds) {}

final class RefundsBuilder {
    private final List<Refund> refunds = new ArrayList<>();
    void refund(String paymentId, long amountMinor) { refunds.add(new Refund(paymentId, amountMinor)); }
    List<Refund> build() { return List.copyOf(refunds); }
}

final class RefundBatchBuilder {
    private String reason = "unspecified";
    private List<Refund> refunds = List.of();
    void reason(String r) { reason = r; }
    void refunds(Consumer<RefundsBuilder> block) {
        RefundsBuilder b = new RefundsBuilder();
        block.accept(b);
        refunds = b.build();
    }
    RefundBatch build() { return new RefundBatch(reason, refunds); }
}

static RefundBatch refundBatch(Consumer<RefundBatchBuilder> block) {
    RefundBatchBuilder b = new RefundBatchBuilder();
    block.accept(b);
    return b.build();
}"""}}
 },
 "recap": [
  "Kotlin named and default arguments, plus `copy()`, replace most builders. Put validation in `init`: it runs for every construction, `copy()` included.",
  "A builder still helps for Java callers, for construction spread over several steps, and for nested data. In Java, pair a validating record (compact constructor) with a builder that only collects.",
  "A type-safe DSL is a function that takes a lambda with receiver (`Builder.() -> Unit`). `@DslMarker` stops an inner block from silently reaching an outer builder.",
  "`Cloneable` has no `clone` method and `Object.clone()` is shallow. Use copy constructors, copy factories or withers.",
  "Record withers and data class `copy()` are shallow. Store collections that can't change, and build new collections in withers.",
  "In Kotlin 2.4 a private constructor doesn't make `copy()` private. Add `@ConsistentCopyVisibility`, or rely on `init` checks, which `copy()` runs."
 ],
 "quiz": [
  {"q": "`data class Fee(val bps: Int) { init { require(bps in 0..1_000) } }`. What does `Fee(290).copy(bps = 5_000)` do?",
   "options": ["Returns `Fee(5000)`, because `copy()` skips `init`", "Throws `IllegalArgumentException`, because `copy()` runs `init`", "Doesn't compile", "Returns `Fee(290)` unchanged"],
   "answer": 1,
   "why": "`copy()` calls the primary constructor with the new values, so every `init` block runs again and `require` throws. That's why `init` is the safest place for a data class's rules. What `copy()` does skip is a validating factory, when the constructor is private."},
  {"q": "A Java team will call your Kotlin `ChargeRequest(amountMinor, currency, token, descriptor = null, capture = true, maxRetries = 0)` constructor from many places. What helps them most?",
   "options": ["Nothing; Java 21 supports named arguments", "Mark the class `data`", "Put `@JvmStatic` on the constructor", "Add `@JvmOverloads`, or give them a builder"],
   "answer": 3,
   "why": "Java has no named or default arguments, so it sees one six-parameter constructor. `@JvmOverloads` generates overloads that drop trailing defaults, and a builder lets them set any subset by name. `@JvmStatic` applies to companion members, not constructors, and `data` changes nothing for Java callers here."},
  {"q": "A DSL has no `@DslMarker`. Inside `lineItems { }`, someone writes `currency = \"USD\"`. `LineItemsBuilder` has no `currency`, but the outer `PaymentRequestBuilder` does. What happens?",
   "options": ["It sets the outer builder's `currency`", "Compile error: unresolved reference", "A runtime exception", "It declares a local variable"],
   "answer": 0,
   "why": "Both receivers are in scope inside the inner lambda, so the compiler resolves `currency` on the outer builder and sets it. Nothing fails. With `@DslMarker` on both builders, that line becomes a compile error unless you write `this@paymentRequest.currency`."},
  {"q": "`record Cart(String id, List<String> skus) {}`. `c1` was built with `new ArrayList<>(List.of(\"a\"))`. Then `Cart c2 = new Cart(\"c2\", c1.skus()); c2.skus().add(\"b\");`. What happens?",
   "options": ["`c1` is unchanged, because records are immutable", "The `add` throws `UnsupportedOperationException`", "`c1.skus()` now contains `b` too", "It doesn't compile"],
   "answer": 2,
   "why": "Records are only shallowly immutable: the field can't point elsewhere, but the `ArrayList` it points to can change, and `c2` shares it. A compact constructor with `skus = List.copyOf(skus);` would give each record its own unmodifiable list, and the `add` would then throw."},
  {"q": "From *Factory Method and Abstract Factory*: you hide a data class's constructor (`data class Email private constructor(val value: String)`) and offer a validating `Email.of(raw)`. In Kotlin 2.4, which line still creates an unvalidated `Email`?",
   "options": ["`Email(\"x\")` in another file", "`Email.of(\"a@b.example\").copy(value = \"x\")`", "`Email.of(\"x\")`", "None: a private constructor covers every path"],
   "answer": 1,
   "why": "The generated `copy()` stays public even when the constructor is private; Kotlin 2.4 only warns about it. So `copy` creates an `Email` your factory never saw. `@ConsistentCopyVisibility` makes `copy()` private, and an `init` check would run on `copy()` too. A direct constructor call from outside does not compile.",
   "from": "pat-02"}
 ],
 "flashcards": [
  {"front": "Does a Kotlin data class's `init` block run on `copy()`?", "back": "Yes. `copy()` calls the primary constructor, so `require` checks in `init` run again."},
  {"front": "What is a lambda with receiver?", "back": "A function type like `Builder.() -> Unit`. Inside the lambda, `this` is the Builder, so you call its members without a prefix."},
  {"front": "What does `@DslMarker` prevent?", "back": "Calling a member of an outer DSL receiver implicitly from inside an inner block. Reaching it then needs an explicit `this@label`."},
  {"front": "Why is `Cloneable` considered broken?", "back": "It declares no `clone` method, and `Object.clone()` is protected, shallow and throws a checked exception. Use copy constructors or withers."},
  {"front": "Is a Kotlin data class `copy()` deep or shallow?", "back": "Shallow. A property that holds a mutable object, such as a `MutableList`, is shared by the original and the copy."},
  {"front": "Where does validation go for a Java record that has a builder?", "back": "In the record's compact constructor, so `build()`, withers and direct `new` calls all run it."},
  {"front": "`data class Email private constructor(...)`: is its `copy()` private in Kotlin 2.4?", "back": "No. It stays public, with a warning. Add `@ConsistentCopyVisibility` to make it private."}
 ],
 "terms": [
  {"term": "Telescoping constructor", "plain": "A chain of constructors, each adding one more optional parameter."},
  {"term": "Builder", "plain": "A helper that collects values step by step and makes the finished object in `build()`."},
  {"term": "Lambda with receiver", "plain": "A lambda whose `this` is a given object, written `T.() -> R`."},
  {"term": "DslMarker", "plain": "A meta-annotation for DSL marker annotations that limits implicit calls to the nearest receiver."},
  {"term": "Prototype", "plain": "Making a new object by copying an existing one and changing a few fields."},
  {"term": "Wither", "plain": "A method like `withTimeout(t)` that returns a copy with one field changed."},
  {"term": "Shallow copy", "plain": "A copy that shares the objects its fields point to, instead of copying them too."}
 ],
 "explain_back": {
  "prompt": "A colleague says: \"Kotlin data classes are immutable, so `copy()` gives us safe, independent templates.\" Explain where that's wrong, and how you'd make templates safe in Kotlin and in Java.",
  "answer": "Data classes are only as immutable as their properties. `val` stops a property from pointing somewhere else, but if it holds a `MutableList` or a `HashMap`, `copy()` copies the reference, so the template and every copy share that collection, and changing one changes all of them. To make templates safe, give them collections that can't change: in Kotlin, read-only `List` and `Map` types and `copy(items = items + x)` to build new ones; in Java, a record whose compact constructor stores `List.copyOf` and `Map.copyOf`, and withers that copy, change the copy and construct a new record. I'd also put the rules in `init` or the compact constructor, because `copy()` and withers go through them."
 },
 "deeper": {
  "minutes": 10,
  "body": """Effective Java's hierarchical builder solves a problem you may meet in a shared Java library: a `Pizza.Builder` that subclasses (`NyPizza.Builder`, `Calzone.Builder`) extend without losing the subclass type in a chain. It uses a recursive type parameter, `Builder<T extends Builder<T>>`, and an abstract `self()` method that each subclass implements as `return this;`. The generics track explains why that recursive bound works. In Kotlin you almost never need it, because named arguments and `copy()` remove the chain.

Java has no `with` syntax for records yet. Project Amber has proposed one, derived record creation (JEP 468), where you would write something like `point with { x = 3; }`. Check its status on the JEP page before you plan around it. Until then, write withers for the fields that really change.

People sometimes deep-copy an object graph by serializing and deserializing it, or with a reflection library. It works, it is slow, and it copies things you didn't mean to copy, such as a shared `Clock` or a connection. If you need a deep copy, the cleaner fix is usually to make the components immutable so a shallow copy is enough.

Kotlin's `buildList { add(...) }`, `buildMap { }` and `buildString { }` are small standard-library builders with receivers. Use them when you build a collection with loops or conditions; the result is read-only once the block returns."""
 },
 "sources": [
  {"title": "Type-safe builders (Kotlin docs)", "url": "https://kotlinlang.org/docs/type-safe-builders.html"},
  {"title": "Data classes (Kotlin docs)", "url": "https://kotlinlang.org/docs/data-classes.html"},
  {"title": "Cloneable (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Cloneable.html"},
  {"title": "Effective Java 3e source, item 2: hierarchical builder", "url": "https://raw.githubusercontent.com/jbloch/effective-java-3e-source-code/master/src/effectivejava/chapter2/item2/hierarchicalbuilder/Pizza.java"}
 ]
}

out = ROOT / "content/lessons/pat-03.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print("wrote", out)
