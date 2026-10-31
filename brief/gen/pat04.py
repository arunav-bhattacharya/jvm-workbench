import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/patterns/src"
J = "java/workbench/patterns/l04"
K = "kotlin/workbench/patterns/l04"
read = lambda p: (ROOT / p).read_text()
demo = lambda cls: f"./gradlew :patterns:demo -Pmain=workbench.patterns.l04.{cls}"


def code(lang, name, cls, alt_lang, alt_name, alt_cls):
    d1 = J if lang == "java" else K
    d2 = J if alt_lang == "java" else K
    return {"lang": lang, "title": name, "src": read(f"{lab}/demo/{d1}/{name}"), "run": demo(cls), "file": f"{lab}/demo/{d1}/{name}",
            "alt": {"lang": alt_lang, "title": alt_name, "src": read(f"{lab}/demo/{d2}/{alt_name}"), "run": demo(alt_cls), "file": f"{lab}/demo/{d2}/{alt_name}"}}


FIG = """<svg viewBox="0 0 700 270" role="img" aria-label="Callers make one call to CheckoutFacade, which uses three ports; each port has an adapter on the edge that talks to the issuer SDK, Oracle or Kafka">
<rect class="box-dim" x="132" y="14" width="318" height="246" rx="8"/>
<text class="t-s t-m" x="291" y="32" text-anchor="middle">your code: no vendor types</text>
<rect class="box" x="10" y="110" width="104" height="50" rx="8"/>
<text class="t" x="62" y="132" text-anchor="middle">callers</text>
<text class="t-s t-m" x="62" y="150" text-anchor="middle">REST, Kafka</text>
<rect class="box-a" x="145" y="110" width="135" height="50" rx="8"/>
<text class="t t-code" x="212" y="140" text-anchor="middle">CheckoutFacade</text>
<rect class="box" x="305" y="50" width="132" height="40" rx="8"/>
<text class="t-s t-code" x="371" y="75" text-anchor="middle">CardAuthorizer</text>
<rect class="box" x="305" y="115" width="132" height="40" rx="8"/>
<text class="t-s t-code" x="371" y="140" text-anchor="middle">Ledger</text>
<rect class="box" x="305" y="180" width="132" height="40" rx="8"/>
<text class="t-s t-code" x="371" y="205" text-anchor="middle">Notifier</text>
<rect class="box-b" x="465" y="50" width="125" height="40" rx="8"/>
<text class="t-s" x="527" y="75" text-anchor="middle">IssuerSdkAdapter</text>
<rect class="box-b" x="465" y="115" width="125" height="40" rx="8"/>
<text class="t-s" x="527" y="140" text-anchor="middle">OracleLedger</text>
<rect class="box-b" x="465" y="180" width="125" height="40" rx="8"/>
<text class="t-s" x="527" y="205" text-anchor="middle">KafkaNotifier</text>
<rect class="box-dim" x="605" y="50" width="88" height="40" rx="8"/>
<text class="t-s t-m" x="649" y="75" text-anchor="middle">issuer SDK</text>
<rect class="box-dim" x="605" y="115" width="88" height="40" rx="8"/>
<text class="t-s t-m" x="649" y="140" text-anchor="middle">Oracle</text>
<rect class="box-dim" x="605" y="180" width="88" height="40" rx="8"/>
<text class="t-s t-m" x="649" y="205" text-anchor="middle">Kafka</text>
<line class="ln-a" x1="114" y1="135" x2="141" y2="135" marker-end="url(#arr)"/>
<line class="ln" x1="280" y1="125" x2="302" y2="75" marker-end="url(#arr)"/>
<line class="ln" x1="280" y1="135" x2="302" y2="135" marker-end="url(#arr)"/>
<line class="ln" x1="280" y1="145" x2="302" y2="198" marker-end="url(#arr)"/>
<line class="ln-d" x1="437" y1="70" x2="462" y2="70" marker-end="url(#arr)"/>
<line class="ln-d" x1="437" y1="135" x2="462" y2="135" marker-end="url(#arr)"/>
<line class="ln-d" x1="437" y1="200" x2="462" y2="200" marker-end="url(#arr)"/>
<line class="ln" x1="590" y1="70" x2="602" y2="70" marker-end="url(#arr)"/>
<line class="ln" x1="590" y1="135" x2="602" y2="135" marker-end="url(#arr)"/>
<line class="ln" x1="590" y1="200" x2="602" y2="200" marker-end="url(#arr)"/>
<text class="t-s t-b" x="527" y="248" text-anchor="middle">adapters: translate</text>
</svg>""".replace("\n", "")

S1 = """An adapter converts the interface of a class you can't change into the interface your code expects. In payments you write them all the time: the issuer gives you a SOAP SDK, a PSP gives you an HTTP client with its own types, and one acquirer still sends fixed-width files. Your payment logic should see none of that. It should see your own port, in your own words:

```java
interface PaymentGateway {
    String charge(long amountMinor, String currency, String token);
}
```

```kotlin
fun interface PaymentGateway {
    fun charge(amountMinor: Long, currency: String, token: String): String
}
```

The adapter implements the port and holds the vendor object. All translation happens inside it, in both directions: your types into the vendor's on the way in, the vendor's results and errors into yours on the way out.

```java
record SoapGatewayAdapter(LegacySoapClient soap) implements PaymentGateway {
    public String charge(long amountMinor, String currency, String token) {
        String xml = "<txn amt='" + amountMinor + "' cur='" + currency + "' tok='" + token + "'/>";
        try {
            String resp = soap.submitTxn(xml);
            return resp.substring(resp.indexOf("ref='") + 5, resp.lastIndexOf("'"));   // vendor format ends here
        } catch (IOException e) {
            throw new GatewayUnavailable("issuer unreachable", e);                       // our exception, not theirs
        }
    }
}
```

```kotlin
class SoapGatewayAdapter(private val soap: LegacySoapClient) : PaymentGateway {
    override fun charge(amountMinor: Long, currency: String, token: String): String {
        val xml = "<txn amt='$amountMinor' cur='$currency' tok='$token'/>"
        try {
            val resp = soap.submitTxn(xml)
            return resp.substringAfter("ref='").substringBefore("'")          // vendor format ends here
        } catch (e: IOException) {
            throw GatewayUnavailable("issuer unreachable", e)                 // our exception, not theirs
        }
    }
}
```

The most common adapter bug is a leaky one. If `IOException`, the vendor's response codes or its DTOs show up in your service layer, every caller now depends on the vendor, and switching issuers means changing all of them.

Java's checked exceptions help here, almost by accident. The port doesn't declare `IOException`, so javac won't let the vendor's exception escape the adapter. Kotlin has no checked exceptions, so the same leak compiles without a word. In Kotlin, the discipline is yours.

When the port has one method, you don't need a class at all: a lambda or method reference is the adapter, in both languages."""

S2 = """Kotlin has a lighter adapter for data: the extension function. The issuer SDK hands you a `VendorTxn` with fields called `amt`, `ccyNum` and `respCd`, and you want your own `Receipt`. Write the mapping once, as an extension on the vendor type:

```kotlin
fun VendorTxn.toReceipt(): Receipt {
    val currency = Currency.getAvailableCurrencies().first { it.numericCode == ccyNum.toInt() }
    return Receipt(
        reference = txnRef,
        amountMinor = BigDecimal(amt).movePointRight(currency.defaultFractionDigits).longValueExact(),
        currency = currency.currencyCode,
        approved = respCd == "00",
    )
}

val receipts = fromSdk.map { it.toReceipt() }
```

```java
// Java has no extension functions: the same adapter is a static method
static Receipt toReceipt(VendorTxn txn) {
    Currency currency = Currency.getAvailableCurrencies().stream()
            .filter(c -> c.getNumericCode() == Integer.parseInt(txn.ccyNum()))
            .findFirst().orElseThrow();
    return new Receipt(txn.txnRef(),
            new BigDecimal(txn.amt()).movePointRight(currency.getDefaultFractionDigits()).longValueExact(),
            currency.getCurrencyCode(), txn.respCd().equals("00"));
}

List<Receipt> receipts = fromSdk.stream().map(Adapters::toReceipt).toList();
```

An extension function is not part of the class. It compiles to a static method that takes the receiver as its first parameter, which is exactly the Java twin. What changes is how the call reads, `txn.toReceipt()`, and where the IDE offers it: type `txn.` and it appears next to the vendor's own methods.

Two rules keep these adapters honest. Keep them in your adapter package, next to the code that calls the SDK, and not in a shared `utils` file: they are part of the translation layer. And use them for data, not for behavior. An extension can't hold state, can't implement your port, and can't be replaced in a test. When you need something your service depends on, write a port and a class.

The other light adapter in Kotlin is the `fun interface`. `PaymentGateway { amount, _, _ -> legacy.pay(amount) }` builds an adapter from a lambda, the same way a Java lambda implements a functional interface."""

S3 = """A facade gives callers one simple entry point to a subsystem. Checkout is the classic case: reserve stock, charge the card, post to the ledger, send a receipt. If every caller (the REST resource, the Kafka consumer for marketplace orders, the admin tool) makes those calls itself, each gets the order and the failure handling slightly different. Put the sequence in one class:

```java
record CheckoutFacade(Inventory inventory, Payments payments, Notifier notifier) {
    String checkout(String sku, long amountMinor, String token, String email) {
        if (!inventory.reserve(sku)) throw new IllegalStateException("out of stock: " + sku);   // 1. reserve
        String receipt;
        try {
            receipt = payments.charge(amountMinor, token);                                     // 2. charge
        } catch (RuntimeException e) {
            inventory.release(sku);                                                            // 3. undo the reservation
            throw e;
        }
        notifier.send(email, "paid " + receipt);                                               // 4. tell the customer
        return receipt;
    }
}
```

```kotlin
class CheckoutFacade(
    private val inventory: Inventory,
    private val payments: Payments,
    private val notifier: Notifier,
) {
    fun checkout(sku: String, amountMinor: Long, token: String, email: String): String {
        check(inventory.reserve(sku)) { "out of stock: $sku" }                     // 1. reserve
        val receipt = try {
            payments.charge(amountMinor, token)                                     // 2. charge
        } catch (e: RuntimeException) {
            inventory.release(sku)                                                  // 3. undo the reservation
            throw e
        }
        notifier.send(email, "paid $receipt")                                       // 4. tell the customer
        return receipt
    }
}
```

The facade owns two decisions: the order of the steps, and what a failure at each step means. Charging before reserving would take money for stock you don't have. A declined card must release the reservation. Those rules now live in one tested place, and each caller is one line.

Nothing in either language replaces Facade; records and constructor injection only make it shorter. The risk is growth. A facade should orchestrate and nothing else: no amount maths, no vendor codes, no SQL. When it reaches forty methods, it has become the god service it was meant to hide, so split it by use case (`CheckoutFacade`, `RefundFacade`).

One Java gotcha showed up while compiling this example. A record component can't be called `notify`: javac reports "illegal record component name", because the accessor `notify()` would clash with `Object.notify()`. The same goes for `wait`, `hashCode`, `toString`, `getClass` and the other no-argument `Object` methods. A Kotlin property named `notify` compiles to `getNotify()` and is fine."""

S4 = """Adapter and Facade both wrap something, and so do Decorator, Proxy and Bridge. Structure won't tell them apart. Intent will:

| Pattern | Wraps | Offers | Why |
|---|---|---|---|
| Adapter | one object you can't change | a different interface: yours | make it fit your port |
| Facade | several objects | a new, simpler interface | hide a sequence of calls |
| Decorator | one object | the same interface | add behavior (*Decorator and Proxy*, lesson 5 of this track) |
| Proxy | one object | the same interface | control access (lesson 5 of this track) |
| Bridge | an implementation you pick | your abstraction | vary two dimensions (lesson 6 of this track) |

In a service built with ports and adapters (often called hexagonal architecture), you see Adapter and Facade on one picture. The payment logic sits in the middle and talks only to ports: `CardAuthorizer`, `Ledger`, `Notifier`. Adapters sit on the edge, one per technology: the issuer SDK adapter, an Oracle ledger, a Kafka notifier. The facade is the front door, where a REST resource or a Kafka consumer makes one call.

That layout pays off twice. Switching issuers means writing one new adapter, and nothing in the middle changes. And the middle is tested with lambdas: `new CheckoutFacade((pan, amount, currency) -> new Approved("A1"), ledger, notifier)` needs no SDK, no database and no broker.

Domain-driven design calls a thick layer of adapters an anti-corruption layer: the place where the vendor's model (response code "51", numeric currency "978", amounts as strings) is translated into yours, so it never spreads. If you find `"51"` in a service class, the layer has a hole. The lab is that layer in miniature: an adapter that keeps an issuer SDK's quirks to itself, and a facade that callers can use without knowing the steps."""

L = {
 "id": "pat-04",
 "title": "Adapter and Facade",
 "minutes": 36,
 "goal": "By the end you can wrap a vendor SDK in an adapter that keeps its types, codes and exceptions to itself, use Kotlin extension functions for light data adapters, and put a multi-step checkout behind a facade that owns the order and the failure rules.",
 "warmup": {
  "q": "A Kotlin adapter implements `fun interface Gateway { fun charge(amountMinor: Long): String }` and calls a vendor method that throws `IOException`, with no try/catch. What happens when the vendor throws?",
  "options": ["It doesn't compile: the `IOException` must be caught or declared", "The `IOException` travels straight through the port to whoever called `charge`", "Kotlin wraps it in an `UndeclaredThrowableException`", "The exception is swallowed and `charge` returns an empty string"],
  "answer": 1,
  "why": "Kotlin has no checked exceptions, so the code compiles and the vendor's `IOException` reaches your service code through a port that never mentioned it. In Java the same adapter would not compile, because the port's method doesn't declare `IOException`. Translating vendor errors at the boundary is a habit you need in Kotlin."
 },
 "sections": [
  {
   "h": "Adapter: make their API fit your port",
   "body": S1,
   "try": {
    "title": "Let the vendor's exception leak",
    "minutes": 4,
    "steps": [
     "Run `SoapAdapterDemo` in either language with the command below. Read the three lines.",
     "In the Java version, delete the `try`/`catch` in `SoapGatewayAdapter.charge`, keeping the two lines inside the `try`. Predict, then run.",
     "Do the same in the Kotlin version. Predict, then run. Restore both files."
    ],
    "code": code("java", "SoapAdapterDemo.java", "SoapAdapterDemo", "kotlin", "SoapAdapterDemo.kt", "SoapAdapterDemoKt"),
    "expect": "Both versions print `charged, ref R-TOK_42`, `caller sees GatewayUnavailable: issuer unreachable` and `lambda adapter: QUICK-990`. Without the catch, Java refuses to compile: `unreported exception IOException; must be caught or declared to be thrown`. Kotlin compiles and prints `caller sees IOException: SOAP fault: 503 Service Unavailable`: the vendor's exception walked through your port."
   },
   "refs": [
    {"title": "Functional (SAM) interfaces (Kotlin docs)", "url": "https://kotlinlang.org/docs/fun-interfaces.html", "kind": "docs"}
   ]
  },
  {
   "h": "Extension functions are Kotlin's light adapters",
   "body": S2,
   "try": {
    "title": "Map vendor transactions to receipts",
    "minutes": 3,
    "steps": [
     "Read `ExtensionAdapters.kt` (or its Java twin). Predict the three receipts, and look hard at the yen one.",
     "Run it with the command below.",
     "Add `VendorTxn(\"T-1004\", \"0.05\", \"978\", \"05\")` to the list (`new VendorTxn(...)` in Java) and predict its `amountMinor` and `approved` before you run."
    ],
    "code": code("kotlin", "ExtensionAdapters.kt", "ExtensionAdaptersKt", "java", "ExtensionAdaptersJava.java", "ExtensionAdaptersJava"),
    "expect": "1250 EUR approved, 1250 JPY approved (the yen has no minor unit, so \"1250\" stays 1250), and 9999 USD not approved. The new one is 5 EUR, not approved. The Kotlin call site reads `it.toReceipt()`; the Java one reads `toReceipt(txn)`. Underneath, both are the same static method."
   },
   "refs": [
    {"title": "Extensions (Kotlin docs)", "url": "https://kotlinlang.org/docs/extensions.html", "kind": "docs"}
   ]
  },
  {
   "h": "Facade: one call for a job with several steps",
   "body": S3,
   "try": {
    "title": "Break the facade's cleanup rule",
    "minutes": 5,
    "steps": [
     "Run `CheckoutFacadeDemo` in either language and read the `still reserved` line.",
     "Remove the `try`/`catch` around the charge, so a decline no longer releases the stock. Predict the `still reserved` line, then run.",
     "Restore it. In the Java version only, rename the record component `notifier` to `notify` (and its use inside `checkout`). Compile."
    ],
    "code": code("java", "CheckoutFacadeDemo.java", "CheckoutFacadeDemo", "kotlin", "CheckoutFacadeDemo.kt", "CheckoutFacadeDemoKt"),
    "expect": "The first run mails a receipt for `sku-1`, then prints `failed: card declined; still reserved: [sku-1]`: the declined order gave `sku-2` back. Without the catch, the line ends `[sku-1, sku-2]`, so a declined card holds stock until someone notices. The rename gives `error: illegal record component name notify`. The Kotlin class can have a property called `notify`."
   },
   "refs": [
    {"title": "JLS chapter 8.10: Record classes", "url": "https://docs.oracle.com/javase/specs/jls/se25/html/jls-8.html#jls-8.10", "kind": "docs"}
   ]
  },
  {
   "h": "Ports and adapters: where the translation lives",
   "body": S4,
   "figure": {"svg": FIG, "caption": "Callers make one call to the facade. Your code talks only to ports, and adapters on the edge translate to each vendor."}
  }
 ],
 "analogy": "An adapter is the travel plug you carry abroad: the hotel's socket stays the same, your charger stays the same, and the plug translates between them. A facade is the hotel's front desk: you ask for a taxi to the airport at six, and the desk deals with the taxi company, the wake-up call and the bill. You never call the taxi company yourself. The analogy breaks on errors: a travel plug either fits or it doesn't, but a software adapter must also translate the vendor's failures into yours, and a leaky one passes the foreign voltage straight through.",
 "in_your_world": "Your Quarkus services already have ports and adapters, even if nobody calls them that: a REST client interface for a PSP, a `@ApplicationScoped` bean that wraps the issuer SDK, a Kafka emitter behind a `Notifier`. Check where the vendor's vocabulary ends. A response code \"05\" in a Temporal activity, or a vendor exception caught in a REST resource, means the adapter is leaking. Temporal makes this concrete: activity retry policies decide on exception types, so translate vendor errors into your own retryable and non-retryable exceptions inside the adapter, where you know which is which. And a checkout facade is a natural Temporal workflow later, once the steps need durable retries.",
 "mistake": "The most common mistake is the leaky adapter: it wraps the vendor's method calls but lets the vendor's model through. The adapter rethrows `SdkException` (or wraps it in a `RuntimeException` that callers unwrap), returns the vendor's response code as a string, or exposes the vendor's DTOs in its method signatures. It happens because translating every code and error feels like busywork when there is only one vendor. Then the second issuer arrives, and every service that checks `\"51\"` has to change. Translate everything at the boundary into your own sealed results and exceptions, and test the adapter against a fake of the vendor class.",
 "compare": {
  "title": "An anti-corruption adapter for a PSP webhook",
  "java": {"title": "PspWebhookAdapter.java", "src": """// the vendor's webhook body, with the vendor's names
record PspWebhook(String type, String pspRef, String amtMinor, String ccy) {}

// our model of what happened
sealed interface PaymentEvent {
    record Captured(String paymentRef, long amountMinor, String currency) implements PaymentEvent {}
    record Refunded(String paymentRef, long amountMinor) implements PaymentEvent {}
    record Ignored(String why) implements PaymentEvent {}
}

final class PspWebhookAdapter {
    private PspWebhookAdapter() {}

    static PaymentEvent toEvent(PspWebhook w) {
        return switch (w.type()) {          // vendor strings are an open set, so a default is right here
            case "charge.captured" -> new PaymentEvent.Captured(w.pspRef(), Long.parseLong(w.amtMinor()), w.ccy().toUpperCase());
            case "charge.refunded" -> new PaymentEvent.Refunded(w.pspRef(), Long.parseLong(w.amtMinor()));
            default -> new PaymentEvent.Ignored("unhandled PSP event " + w.type());
        };
    }
}"""},
  "kotlin": {"title": "PspWebhookAdapter.kt", "src": """// the vendor's webhook body, with the vendor's names
data class PspWebhook(val type: String, val pspRef: String, val amtMinor: String, val ccy: String)

// our model of what happened
sealed interface PaymentEvent {
    data class Captured(val paymentRef: String, val amountMinor: Long, val currency: String) : PaymentEvent
    data class Refunded(val paymentRef: String, val amountMinor: Long) : PaymentEvent
    data class Ignored(val why: String) : PaymentEvent
}

// the adapter as an extension: reads like a method on the vendor type
fun PspWebhook.toEvent(): PaymentEvent = when (type) {   // open set of vendor strings: else is right
    "charge.captured" -> PaymentEvent.Captured(pspRef, amtMinor.toLong(), ccy.uppercase())
    "charge.refunded" -> PaymentEvent.Refunded(pspRef, amtMinor.toLong())
    else -> PaymentEvent.Ignored("unhandled PSP event $type")
}"""},
  "note": "The translation is identical: vendor strings in, a sealed event of our own out. Kotlin writes it as an extension on the vendor type, so call sites read `webhook.toEvent()`; Java needs a static method on a holder class, so they read `PspWebhookAdapter.toEvent(webhook)`. In bytecode they are the same static method. Both use a catch-all branch on purpose: vendor event types are an open set you don't control, unlike your own sealed types, where a missing case should break the build. Code that consumes `PaymentEvent` then switches over it with no default. Neither language makes Adapter unnecessary; Kotlin just makes the data-mapping kind cheaper to write."
 },
 "worked": {
  "title": "Wrap a vendor FX feed behind a port, then test without it",
  "steps": [
   {"say": "A pricing service calls a vendor FX feed directly. The feed returns strings like `\"EURUSD=1.0842;ts=1730000000\"` and throws a checked `FeedException`. Before reading on, list every vendor detail that leaks into `priceInUsd`.",
    "code": """class Pricer {
    private final RateFeedClient feed = new RateFeedClient("https://fx.vendor.example");

    long priceInUsd(long amountMinorEur) throws FeedException {
        String raw = feed.quote("EURUSD");                                  // vendor pair format
        BigDecimal rate = new BigDecimal(raw.substring(raw.indexOf('=') + 1, raw.indexOf(';')));
        return new BigDecimal(amountMinorEur).multiply(rate).setScale(0, RoundingMode.HALF_EVEN).longValueExact();
    }
}""", "lang": "java",
    "alt_code": """class Pricer {
    private val feed = RateFeedClient("https://fx.vendor.example")

    fun priceInUsd(amountMinorEur: Long): Long {
        val raw = feed.quote("EURUSD")                                       // vendor pair format; FeedException leaks unseen
        val rate = BigDecimal(raw.substringAfter('=').substringBefore(';'))
        return BigDecimal(amountMinorEur).multiply(rate).setScale(0, RoundingMode.HALF_EVEN).longValueExact()
    }
}""", "alt_lang": "kotlin"},
   {"say": "Four leaks: the pair format, the response format, the checked exception, and the hard-wired URL. Define the port in your words first. It says nothing about strings or vendors, and an empty result means \"no rate right now\".",
    "code": """interface FxRates {
    Optional<BigDecimal> rate(String from, String to);      // 1. our words: currencies in, a rate or nothing out
}

class Pricer {
    private final FxRates rates;
    Pricer(FxRates rates) { this.rates = rates; }

    OptionalLong priceInUsd(long amountMinorEur) {
        return rates.rate("EUR", "USD")
                .map(r -> new BigDecimal(amountMinorEur).multiply(r).setScale(0, RoundingMode.HALF_EVEN).longValueExact())
                .map(OptionalLong::of).orElse(OptionalLong.empty());
    }
}""", "lang": "java",
    "alt_code": """fun interface FxRates {
    fun rate(from: String, to: String): BigDecimal?          // 1. our words: currencies in, a rate or null out
}

class Pricer(private val rates: FxRates) {
    fun priceInUsd(amountMinorEur: Long): Long? =
        rates.rate("EUR", "USD")?.let {
            BigDecimal(amountMinorEur).multiply(it).setScale(0, RoundingMode.HALF_EVEN).longValueExact()
        }
}""", "alt_lang": "kotlin"},
   {"say": "Now the adapter. Everything the vendor knows lives here: how pairs are spelled, how answers are packed, and which exception it throws. Why return empty instead of rethrowing on `FeedException`? Because the port promised \"a rate or nothing\", and the pricer decides what nothing means.",
    "code": """final class VendorFxRates implements FxRates {
    private final RateFeedClient feed;
    VendorFxRates(RateFeedClient feed) { this.feed = feed; }

    public Optional<BigDecimal> rate(String from, String to) {
        try {
            String raw = feed.quote(from + to);                                         // 2. our pair, their format
            return Optional.of(new BigDecimal(raw.substring(raw.indexOf('=') + 1, raw.indexOf(';'))));
        } catch (FeedException | RuntimeException e) {                                  // 3. their failure, our answer
            return Optional.empty();
        }
    }
}""", "lang": "java",
    "alt_code": """class VendorFxRates(private val feed: RateFeedClient) : FxRates {
    override fun rate(from: String, to: String): BigDecimal? =
        try {
            val raw = feed.quote(from + to)                                               // 2. our pair, their format
            BigDecimal(raw.substringAfter('=').substringBefore(';'))
        } catch (e: FeedException) {                                                      // 3. their failure, our answer
            null
        } catch (e: RuntimeException) {
            null
        }
}""", "alt_lang": "kotlin"},
   {"say": "Test the two halves separately. The pricer gets a lambda. The adapter gets a fake feed, a subclass of the vendor client that returns canned strings, which is how the lab tests its issuer adapter.",
    "code": """// 4. the core, with no vendor at all
assertThat(new Pricer((from, to) -> Optional.of(new BigDecimal("1.0842"))).priceInUsd(10_000)).hasValue(10_842);

// 5. the adapter, against a fake of the vendor class
RateFeedClient fake = new RateFeedClient("unused") {
    @Override public String quote(String pair) { return "EURUSD=1.0842;ts=1730000000"; }
};
assertThat(new VendorFxRates(fake).rate("EUR", "USD")).contains(new BigDecimal("1.0842"));""", "lang": "java",
    "alt_code": """// 4. the core, with no vendor at all
assertThat(Pricer { _, _ -> BigDecimal("1.0842") }.priceInUsd(10_000)).isEqualTo(10_842L)

// 5. the adapter, against a fake of the vendor class (open in the SDK, or use an interface)
val fake = object : RateFeedClient("unused") {
    override fun quote(pair: String) = "EURUSD=1.0842;ts=1730000000"
}
assertThat(VendorFxRates(fake).rate("EUR", "USD")).isEqualTo(BigDecimal("1.0842"))""", "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "An issuer SDK adapter and a checkout facade",
  "minutes": 13,
  "files": [f"{lab}/main/{J}/IssuerSdkAdapter.java", f"{lab}/main/{J}/CheckoutFacade.java"],
  "run": "./gradlew :patterns:test --tests 'workbench.patterns.l04.*'",
  "steps": [
   "Read `LegacyIssuerSdk.java`, `CardAuthorizer.java` and `Amounts.java`. They are given; don't edit them. Run the tests: all ten fail.",
   "Write `IssuerSdkAdapter.authorize`. Call `sdk.auth` with `Amounts.toDecimal` and `Amounts.numericCode`, catch `SdkException` and return `Unavailable(e.getMessage())`, then split the response on `|` and map the code with a `switch`.",
   "Write `CheckoutFacade.checkout` as a `switch` over the `AuthResult`. Approved: post, send the receipt (catching a failing notifier), return `Paid`. Declined: send the notice, return `Declined`. Unavailable: return `RetryLater`.",
   "Run the tests until all ten pass."
  ],
  "hints": [
   "`raw.split(\"\\\\|\", -1)` splits on a literal `|` and keeps the empty auth id in `\"51|\"`. The pipe must be escaped, because `split` takes a regex.",
   "A `switch` over the sealed `AuthResult` with `case AuthResult.Approved ok -> ...` needs no `default`: the compiler checks all three cases. In a switch expression, use `yield` to return from a block.",
   "Wrap only the notifier call in try/catch. If the ledger post throws, let it propagate: an approved payment that isn't on the ledger is an incident, not something to swallow."
  ],
  "done_when": "All ten tests in `AdapterFacadeTest` pass."
 },
 "drill": {
  "title": "An adapter from memory",
  "minutes": 5,
  "prompt": "Close this page. A vendor `GeoIpClient` has `String lookup(String ip) throws GeoException`, returning text like `\"DE;Berlin\"`. Your port is `interface CountryOf { Optional<String> country(String ip); }` (in Kotlin, `fun interface CountryOf { fun country(ip: String): String? }`). Write the adapter so the vendor's exception never escapes and an empty or malformed answer gives no country.",
  "answer": {"lang": "java", "src": """final class GeoIpCountryOf implements CountryOf {
    private final GeoIpClient client;
    GeoIpCountryOf(GeoIpClient client) { this.client = client; }

    @Override
    public Optional<String> country(String ip) {
        try {
            String raw = client.lookup(ip);                        // their format: "DE;Berlin"
            if (raw == null) return Optional.empty();
            String code = raw.split(";", 2)[0].trim();
            return code.length() == 2 ? Optional.of(code) : Optional.empty();
        } catch (GeoException e) {
            return Optional.empty();                               // their failure stops here
        }
    }
}""",
   "alt": {"lang": "kotlin", "title": "Kotlin", "src": """class GeoIpCountryOf(private val client: GeoIpClient) : CountryOf {
    override fun country(ip: String): String? =
        try {
            client.lookup(ip)                                      // their format: "DE;Berlin"
                ?.substringBefore(';')
                ?.trim()
                ?.takeIf { it.length == 2 }
        } catch (e: GeoException) {
            null                                                   // their failure stops here
        }
}"""}}
 },
 "recap": [
  "An adapter makes a class you can't change fit your port. It translates arguments on the way in, and results and errors on the way out.",
  "Keep vendor types, codes and exceptions inside the adapter. A `\"51\"` or an `SdkException` in a service class is a leak.",
  "Java's checked exceptions stop a vendor `IOException` from escaping a port that doesn't declare it; Kotlin compiles the same leak silently.",
  "For a one-method port, a lambda or a `fun interface` is the adapter. For data mapping in Kotlin, an extension like `VendorTxn.toReceipt()` is the light adapter; in Java it's a static method.",
  "A facade gives callers one call for a multi-step job and owns the order of the steps and what each failure means. Keep it orchestration only.",
  "A Java record component can't be named `notify`, `wait` or another no-argument `Object` method."
 ],
 "quiz": [
  {"q": "Your issuer adapter catches `SdkException` and rethrows it wrapped in a `RuntimeException`. The checkout service catches that and checks `getCause() instanceof SdkException` to decide whether to retry. What's wrong?",
   "options": ["Nothing, since the exception is unchecked now", "The vendor type still leaks: the service depends on the SDK, so switching issuers breaks it", "A `RuntimeException` can't wrap a checked exception", "Retry decisions belong inside the vendor SDK"],
   "answer": 1,
   "why": "Wrapping changed the exception's type, not who depends on it. The service still imports `SdkException`, so it's coupled to this vendor. Translate inside the adapter into your own result (`Unavailable`) or your own exception type that says retryable or not. A `RuntimeException` can wrap anything, so that option is simply false."},
  {"q": "Which statement about an adapter written in Kotlin is true?",
   "options": ["A vendor `IOException` thrown inside it can pass through your port without any compile error", "The compiler forces you to catch the vendor's checked exceptions", "Extension functions can implement your port interface", "`fun interface` ports can't be implemented with a lambda"],
   "answer": 0,
   "why": "Kotlin has no checked exceptions, so nothing stops the vendor's `IOException` from reaching callers of your port. Java would refuse to compile the same adapter. Extensions can't implement interfaces, and a `fun interface` exists precisely so a lambda can implement it."},
  {"q": "Three call sites (a REST resource, a Kafka consumer and an admin tool) each reserve stock, charge the card, post to the ledger and send an email, each with slightly different failure handling. Which pattern fits?",
   "options": ["Adapter", "Decorator", "Facade", "Singleton"],
   "answer": 2,
   "why": "A facade puts the sequence and its failure rules in one place, and each caller makes one call. An adapter changes one object's interface, a decorator adds behavior behind the same interface, and a singleton is about instance count, not about orchestrating steps."},
  {"q": "Which is the best use of a Kotlin extension function as an adapter?",
   "options": ["`fun LegacyIssuerSdk.authorize(...)`, which callers use instead of a `CardAuthorizer` port", "A global `fun Any.toJson()` in a shared utils file", "An extension that caches vendor results in a top-level map", "`fun VendorTxn.toReceipt(): Receipt`, kept in the issuer-adapter package"],
   "answer": 3,
   "why": "Mapping a vendor DTO to your own type is pure data translation, which is what extensions are good at, and keeping it in the adapter package keeps the vendor model contained. An extension on the SDK makes callers depend on the SDK and can't be swapped in a test. A global utils extension spreads everywhere, and caching in a top-level map is hidden shared state."},
  {"q": "From *Factory Method and Abstract Factory*: you now have one `IssuerSdkAdapter` for Visa's SDK and one for Mastercard's. Where should the choice between them live?",
   "options": ["In each REST resource, with an `if` on the card's BIN", "In one factory, a `switch` or `when` over the network with no default, injected into the facade", "Inside the facade's `checkout`, as string checks on the PAN", "In the adapters: each checks whether the card belongs to it"],
   "answer": 1,
   "why": "Choosing which product to build is a factory's job: one exhaustive `switch` or `when` over a sealed or enum network, so adding a network is a compile error in one place. Spreading BIN checks over resources or the facade copies the rule, and adapters checking ownership turns every call into a guessing game.",
   "from": "pat-02"}
 ],
 "flashcards": [
  {"front": "What does an adapter do?", "back": "Makes an object you can't change fit the interface (port) your code expects, translating arguments, results and errors."},
  {"front": "What is a leaky adapter?", "back": "One that lets the vendor's types, codes or exceptions (an `SdkException`, response code \"51\") reach your service code."},
  {"front": "A Kotlin adapter calls a method that throws `IOException` and has no catch. Does it compile?", "back": "Yes. Kotlin has no checked exceptions, so the vendor's `IOException` passes through your port silently. Java would refuse."},
  {"front": "What does a Kotlin extension function compile to?", "back": "A static method whose first parameter is the receiver. `txn.toReceipt()` is `toReceipt(txn)` in bytecode."},
  {"front": "What does a facade own?", "back": "The order of the steps in a multi-step job, and what a failure at each step means. Not maths, vendor codes or SQL."},
  {"front": "Can a Java record component be named `notify`?", "back": "No: \"illegal record component name\". Its accessor would clash with `Object.notify()`. The same goes for `wait`, `hashCode`, `toString` and the other no-arg `Object` methods."},
  {"front": "Adapter vs Facade, one line each?", "back": "Adapter: one object, given a different interface (yours). Facade: several objects behind one new, simpler interface."}
 ],
 "terms": [
  {"term": "Adapter", "plain": "A wrapper that makes an existing object fit the interface your code expects."},
  {"term": "Port", "plain": "An interface in your own words that your core code depends on, such as `CardAuthorizer`."},
  {"term": "Anti-corruption layer", "plain": "The adapters where a vendor's model is translated into yours, so it never spreads into your code."},
  {"term": "Facade", "plain": "One simple entry point that runs a multi-step job across several subsystems."},
  {"term": "Extension function", "plain": "A Kotlin function called like a method on a type it doesn't belong to; a static method underneath."},
  {"term": "Hexagonal architecture", "plain": "Core logic talks only to ports, and adapters on the edge connect each port to one technology."}
 ],
 "explain_back": {
  "prompt": "Explain to a new teammate why `IssuerSdkAdapter` returns `Unavailable` instead of letting `SdkException` through, and why `CheckoutFacade` swallows a failing receipt email but not a failing ledger post.",
  "answer": "The adapter is the only class allowed to know the issuer's SDK. If `SdkException` escaped, every caller would import the vendor's type and decide on its status codes, and switching issuers would mean changing all of them. So the adapter turns it into our own result, `Unavailable`, and the facade turns that into `RetryLater`. In the facade, the order matters: once the card is approved, the money moved, so the ledger post must happen, and if it fails, that's an incident we must see, so it propagates. The receipt email is best effort. A broken mail server shouldn't turn a completed payment into an error the customer retries, which could charge them twice."
 },
 "deeper": {
  "minutes": 10,
  "body": """The JDK has adapters you use daily. `InputStreamReader` adapts a byte stream into a character stream; its Javadoc calls it a bridge from byte streams to character streams, which shows how loosely the pattern names get used. `Arrays.asList` adapts an array into a fixed-size `List` that writes through to the array. `Collections.enumeration` and `Enumeration.asIterator()` (Java 9) adapt between the old and new iteration interfaces.

The GoF book describes two kinds of adapter. An object adapter holds the vendor object and delegates to it, as in this lesson. A class adapter inherits from the vendor class and implements your interface at the same time. Java and Kotlin allow the second only when the vendor class is open, and it is usually worse: your adapter inherits every public method of the SDK, so callers can bypass your translation. Prefer the object adapter.

Kotlin's `by` delegation (in *Decorator and Proxy*, lesson 5 of this track) can build an adapter that forwards most of an interface unchanged and overrides the few methods that need translation. That works when the two interfaces are almost the same, such as two versions of your own API. For a vendor SDK with a different model, write the translation out; it is the part that deserves a review.

Facades and transactions mix badly in one way. If a Spring or Quarkus facade method is `@Transactional` and calls an external issuer inside the transaction, a 120 ms issuer call holds a database connection for 120 ms. With a pool of 20 connections, a slow issuer starves the database. Charge first, outside the transaction, then post to the ledger in a short one, and make the post idempotent so a retry can't double-post."""
 },
 "sources": [
  {"title": "Extensions (Kotlin docs)", "url": "https://kotlinlang.org/docs/extensions.html"},
  {"title": "Functional (SAM) interfaces (Kotlin docs)", "url": "https://kotlinlang.org/docs/fun-interfaces.html"},
  {"title": "JLS chapter 8.10: Record classes", "url": "https://docs.oracle.com/javase/specs/jls/se25/html/jls-8.html#jls-8.10"},
  {"title": "InputStreamReader (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/io/InputStreamReader.html"}
 ]
}

out = ROOT / "content/lessons/pat-04.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print("wrote", out)
