import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/patterns/src"
J = "java/workbench/patterns/l02"
K = "kotlin/workbench/patterns/l02"
read = lambda p: (ROOT / p).read_text()
demo = lambda cls: f"./gradlew :patterns:demo -Pmain=workbench.patterns.l02.{cls}"

FIG = """<svg viewBox="0 0 660 270" role="img" aria-label="Checkout asks the CardNetworkClients factory for one family; the Visa family and the Mastercard family each create their own authorizer and refunder">
<rect class="box" x="15" y="110" width="120" height="44" rx="8"/>
<text class="t" x="75" y="137" text-anchor="middle">Checkout</text>
<rect class="box-a" x="190" y="110" width="180" height="44" rx="8"/>
<text class="t t-code" x="280" y="137" text-anchor="middle">CardNetworkClients</text>
<text class="t-s t-m" x="280" y="176" text-anchor="middle">sandbox(network)</text>
<line class="ln-a" x1="135" y1="132" x2="186" y2="132" marker-end="url(#arr)"/>
<text class="t-s t-m" x="160" y="104" text-anchor="middle">once</text>
<rect class="box-b" x="420" y="15" width="225" height="110" rx="8"/>
<text class="t t-b" x="532" y="40" text-anchor="middle">Visa family</text>
<rect class="box" x="432" y="58" width="98" height="44" rx="8"/>
<text class="t-s" x="481" y="85" text-anchor="middle">authorizer()</text>
<rect class="box" x="537" y="58" width="98" height="44" rx="8"/>
<text class="t-s" x="586" y="85" text-anchor="middle">refunder()</text>
<rect class="box-b" x="420" y="145" width="225" height="110" rx="8"/>
<text class="t t-b" x="532" y="170" text-anchor="middle">Mastercard family</text>
<rect class="box" x="432" y="188" width="98" height="44" rx="8"/>
<text class="t-s" x="481" y="215" text-anchor="middle">authorizer()</text>
<rect class="box" x="537" y="188" width="98" height="44" rx="8"/>
<text class="t-s" x="586" y="215" text-anchor="middle">refunder()</text>
<line class="ln" x1="370" y1="124" x2="416" y2="72" marker-end="url(#arr)"/>
<line class="ln" x1="370" y1="140" x2="416" y2="196" marker-end="url(#arr)"/>
<text class="t-s t-m" x="280" y="230" text-anchor="middle">both products come from</text>
<text class="t-s t-m" x="280" y="248" text-anchor="middle">the same family, so they match</text>
</svg>""".replace("\n", "")

S1 = """A static factory method is a static method that returns an instance of its class, or of some class behind an interface. Effective Java opens with it (item 1: consider static factory methods instead of constructors), and the JDK is full of them: `List.of`, `Duration.ofMinutes`, `Integer.valueOf`, `HttpClient.newHttpClient`, `Thread.ofVirtual`.

A constructor can do one thing: make a new object of exactly that class. A static factory can do four things a constructor can't.

1. It has a name. `Duration.ofMinutes(2)` and `Duration.ofSeconds(2)` both take a `long`. Two constructors with the same parameter types can't exist, and `new Duration(2)` would say nothing anyway.
2. It can return a cached instance. `Integer.valueOf(100)` hands back the same object every time.
3. It can return any subtype, chosen from the input. `List.of(1)` and `List.of(1, 2, 3)` return two different private classes. `EnumSet.noneOf` picks a set backed by a single `long` when the enum has 64 constants or fewer, and a larger one otherwise. Callers never see the class names.
4. The class it returns doesn't have to exist when the factory is written. `DriverManager.getConnection(url)` returns a `Connection` from whichever JDBC driver on the classpath accepts the URL, found through `ServiceLoader`. The Oracle driver in your service was written long after `java.sql`.

The downsides are small. A class with only private constructors can't be subclassed, which pushes you toward composition and costs little. Factories are also harder to spot in an IDE than constructors, so stick to the usual names: `of`, `from`, `valueOf`, `parse`, `newX`, `create`.

For your own value types, make this the default. Make the constructor private and offer `Money.ofMinor(1250, "EUR")` and `Money.parse("12.50 EUR")`. With the constructor private, every `Money` in the system went through your validation."""

S2 = """The GoF Factory Method is a related idea with a confusingly similar name. A class needs to create something, but it shouldn't decide which concrete class. In the book's version, an abstract creator declares a creation hook and subclasses override it:

```java
abstract class CheckoutService {
    protected abstract PaymentGateway createGateway();       // the factory method
    final String pay(long amountMinor, String token) {
        return createGateway().charge(amountMinor, token);
    }
}
class AdyenCheckout extends CheckoutService {
    protected PaymentGateway createGateway() { return new AdyenGateway(); }
}
```

```kotlin
abstract class CheckoutService {
    protected abstract fun createGateway(): PaymentGateway      // the factory method
    fun pay(amountMinor: Long, token: String) = createGateway().charge(amountMinor, token)
}
class AdyenCheckout : CheckoutService() {
    override fun createGateway(): PaymentGateway = AdyenGateway()
}
```

That is one subclass per product, just to pick a constructor. Since Java 8, a function does the same job. A `Supplier<PaymentGateway>` (in Kotlin, a `() -> PaymentGateway`) is a factory, and a constructor reference is the shortest way to write one:

```java
record Checkout(Supplier<? extends PaymentGateway> gateways) {
    String pay(long amountMinor, String token) { return gateways.get().charge(amountMinor, token); }
}
new Checkout(AdyenGateway::new);   // production
new Checkout(FakeGateway::new);    // test
```

```kotlin
class Checkout(private val gateways: () -> PaymentGateway) {
    fun pay(amountMinor: Long, token: String) = gateways().charge(amountMinor, token)
}
Checkout(::AdyenGateway)   // production
Checkout(::FakeGateway)    // test
```

When the choice depends on data (a config value, a tenant, the BIN of a card), put it in one static factory over a sealed product family:

```java
static PaymentGateway of(Provider p) {
    return switch (p) {            // no default branch, on purpose
        case ADYEN -> new AdyenGateway();
        case STRIPE -> new StripeGateway();
        case FAKE -> new FakeGateway();
    };
}
```

```kotlin
fun gatewayOf(p: Provider): PaymentGateway = when (p) {   // no else branch, on purpose
    Provider.ADYEN -> AdyenGateway()
    Provider.STRIPE -> StripeGateway()
    Provider.FAKE -> FakeGateway()
}
```

Leave out `default` (or `else` in Kotlin). When someone adds `KLARNA` to the enum, this switch stops compiling, and the compiler points at the one place that needs a new gateway. With a catch-all branch that returns `FakeGateway`, the build stays green and real Klarna payments go to the fake. It is the factory bug I see most often in review.

People mix up the two names, so keep them apart. A static factory is about how one class hands out its own instances. Factory Method is about who decides the concrete class: not the code that uses the object.

You already write factory methods in your services under another name. A Quarkus `@Produces` method or a Spring `@Bean` method is a factory method that the container calls. It decides how to build the `KafkaProducer` or the issuer client, and the rest of the code injects only the interface. The container calls it when it creates the bean, not once per request, so a choice that depends on the current request (which network this card belongs to) still needs a factory you call yourself."""

S3 = """Kotlin has no `static`, so its factories live in three other places.

The **companion object** is the direct translation of a Java static factory. Make the constructor private and put the factory next to it:

```kotlin
class Card private constructor(val network: Network, val last4: String) {
    companion object {
        fun parse(raw: String): CardResult { /* validate, then Card(network, last4) */ }
    }
}
```

```java
public final class Card {
    private final Network network;
    private final String last4;
    private Card(Network network, String last4) { this.network = network; this.last4 = last4; }

    public static CardResult parse(String raw) { /* validate, then new Card(network, last4) */ }
}
```

An `operator fun invoke` on the companion lets callers write what looks like a constructor call, `Fee(290)`, while you run a factory that validates or returns a cached instance. Use it sparingly: readers expect `Fee(290)` to make a new object.

The third shape is a top-level function named like the type. The Kotlin coding conventions allow a factory function to share the name of the abstract type it returns, and kotlinx.coroutines does exactly that: `Job()`, `CoroutineScope(context)` and `MutableStateFlow(0)` are functions that return a private implementation class.

What a factory returns matters as much as where it lives. A parser that throws makes every caller remember a `try`. A factory that returns a sealed result makes the compiler remember for them:

```kotlin
sealed interface CardResult {
    data class Valid(val card: Card) : CardResult
    data class Invalid(val reason: String) : CardResult
}

when (val r = Card.parse(input)) {      // no else
    is CardResult.Valid -> charge(r.card)
    is CardResult.Invalid -> reject(r.reason)
}
```

```java
public sealed interface CardResult {
    record Valid(Card card) implements CardResult {}
    record Invalid(String reason) implements CardResult {}
}

switch (Card.parse(input)) {             // no default
    case CardResult.Valid v -> charge(v.card());
    case CardResult.Invalid i -> reject(i.reason());
}
```

Add a third case later, say `Expired`, and every `when` without an `else` stops compiling until it handles it. Java 21 gives you the same check with a sealed interface, records and a `switch` with type patterns, as the Java twin shows. Throw exceptions for bugs and broken infrastructure. Return a sealed result for outcomes the caller is expected to handle, like a mistyped card number."""

S4 = """Sometimes you create several objects that must match. A card network gives you an authorization API and a refund API, and a Visa auth code means nothing to Mastercard's refund endpoint. If every call site picks its own authorizer and its own refunder, sooner or later a code path that runs once a month pairs a Visa authorizer with a Mastercard refunder.

Abstract Factory puts that choice in one place. One interface creates every product of the family, with one implementation per family:

```kotlin
interface CardNetworkClients {
    val network: Network
    fun authorizer(): Authorizer
    fun refunder(): Refunder

    companion object {
        fun sandbox(network: Network): CardNetworkClients = when (network) {
            Network.VISA -> SandboxClients(Network.VISA, "https://sandbox.visa.example", "V")
            Network.MASTERCARD -> SandboxClients(Network.MASTERCARD, "https://sandbox.mastercard.example", "M")
        }
    }
}
```

```java
public interface CardNetworkClients {
    Network network();
    Authorizer authorizer();
    Refunder refunder();

    static CardNetworkClients sandbox(Network network) {
        return switch (network) {
            case VISA -> new SandboxClients(Network.VISA, "https://sandbox.visa.example", "V");
            case MASTERCARD -> new SandboxClients(Network.MASTERCARD, "https://sandbox.mastercard.example", "M");
        };
    }
}
```

Callers ask for the family once, `clientsFor(card.network)`, and take both products from it. They can't mix families because they never pick a product directly.

Each family here is one class built from settings, not a `VisaAuthorizer` plus a `VisaRefunder`. When the products are single-method interfaces, a family is just a class (or a Java record) of functions. The GoF diagram with two parallel class hierarchies is the worst case, not a requirement.

The weakness runs the other way. Adding a family is cheap: one more implementation. Adding a product, say a `Tokenizer`, changes the interface and every family. And with a DI container you may not need to write the factory at all: Quarkus build profiles or Spring profiles can pick the Kafka messaging family in production and an in-memory one in tests. Write the factory yourself when the choice depends on runtime data, such as the card in this request.

Check yourself. Card ops adds `AMEX` to `Network`. Where does the build fail, and which callers change? (It fails in `sandbox`, because its `when` and `switch` have no `else` or `default`, so you add an Amex branch with its own settings. No caller changes: callers only ask for a family and never name a product class.)"""

L = {
 "id": "pat-02",
 "title": "Factory Method and Abstract Factory",
 "minutes": 35,
 "goal": "By the end you can replace constructor calls with named static or companion factories that validate and return sealed results, pass factories around as functions, and group matching products behind an abstract factory.",
 "warmup": {
  "q": "`List.of(1)` and `List.of(1, 2, 3)` both return a `List<Integer>`. What do you expect `getClass()` to say for each?",
  "options": ["Both are `ArrayList`", "Both are the same private immutable class", "Two different private classes, chosen by the factory from the number of elements", "`List` itself, since `List.of` is defined on the interface"],
  "answer": 2,
  "why": "`List.of` is a static factory, so it can return any implementation it likes. In JDK 21 it returns `List12` for one or two elements and `ListN` for more, both private classes. A constructor could never do that: `new X()` always gives you an `X`. An interface can't be instantiated, so `List` itself is impossible."
 },
 "sections": [
  {
   "h": "Static factory methods are constructors with names",
   "body": S1,
   "try": {
    "title": "Watch the JDK's factories choose",
    "minutes": 4,
    "steps": [
     "Read `FactoriesInTheJdk`. For each of the first four lines, predict the class name you'll see. The Kotlin twin adds three lines for Kotlin's own `listOf`.",
     "Run it with the command below.",
     "Try `EnumSet.noneOf(TimeUnit.class).getClass()` in your IDE's auto-complete: can you type `RegularEnumSet` yourself?"
    ],
    "code": {"lang": "java", "title": "FactoriesInTheJdk.java", "src": read(f"{lab}/demo/{J}/FactoriesInTheJdk.java"),
             "run": demo("FactoriesInTheJdk"), "file": f"{lab}/demo/{J}/FactoriesInTheJdk.java",
             "alt": {"lang": "kotlin", "title": "FactoriesInTheJdk.kt", "src": read(f"{lab}/demo/{K}/FactoriesInTheJdk.kt"),
                     "run": demo("FactoriesInTheJdkKt"), "file": f"{lab}/demo/{K}/FactoriesInTheJdk.kt"}},
    "expect": "`List12` for one element and `ListN` for three. `RegularEnumSet` for `TimeUnit` (7 constants) and `JumboEnumSet` for `Character.UnicodeScript` (well over 64 constants). Both `same object?` lines print `true`, because the factories handed back cached instances. None of these classes are public, so you can't name them in your code. The factory is the only door. Kotlin's `listOf` plays the same game: `EmptyList`, `Collections$SingletonList` and `Arrays$ArrayList`, depending on how many elements you pass."
   },
   "refs": [
    {"title": "DriverManager (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.sql/java/sql/DriverManager.html", "kind": "docs"}
   ]
  },
  {
   "h": "Factory Method: let someone else choose the class",
   "body": S2,
   "try": {
    "title": "Break a factory on purpose",
    "minutes": 5,
    "steps": [
     "Run `GatewayFactory` with the command below.",
     "Add `KLARNA` to the `Provider` enum and run it again. Read the compiler error.",
     "Now add a catch-all as the last branch (`default -> new FakeGateway();` in Java, `else -> FakeGateway()` in Kotlin), keep `KLARNA`, and run again. Where does Klarna's charge go?",
     "Undo both changes."
    ],
    "code": {"lang": "java", "title": "GatewayFactory.java", "src": read(f"{lab}/demo/{J}/GatewayFactory.java"),
             "run": demo("GatewayFactory"), "file": f"{lab}/demo/{J}/GatewayFactory.java",
             "alt": {"lang": "kotlin", "title": "GatewayFactory.kt", "src": read(f"{lab}/demo/{K}/GatewayFactory.kt"),
                     "run": demo("GatewayFactoryKt"), "file": f"{lab}/demo/{K}/GatewayFactory.kt"}},
    "expect": "The first run prints one charge per provider and `test checkout -> fake:ok`. With `KLARNA` added, the build fails, pointing at the factory: javac says `error: the switch expression does not cover all possible input values`, and kotlinc says `'when' expression must be exhaustive. Add the 'KLARNA' branch or an 'else' branch.` With a catch-all branch it compiles and prints `KLARNA -> fake:ok`: a customer's payment would go to the fake gateway, and nothing warns you."
   }
  },
  {
   "h": "Kotlin factories: companion, invoke and sealed results",
   "body": S3,
   "try": {
    "title": "Let the compiler find the missing case",
    "minutes": 4,
    "steps": [
     "Run `CompanionFactories` (Kotlin, or its Java twin) with the command below and read the three `parse` lines.",
     "Add a fourth result: `data class Blocked(val country: String) : IbanResult` in Kotlin, or `record Blocked(String country) implements IbanResult {}` in Java. Predict what happens, then run.",
     "Fix it by adding a branch for `Blocked` to `describe`, not an `else` or `default`."
    ],
    "code": {"lang": "kotlin", "title": "CompanionFactories.kt", "src": read(f"{lab}/demo/{K}/CompanionFactories.kt"),
             "run": demo("CompanionFactoriesKt"), "file": f"{lab}/demo/{K}/CompanionFactories.kt",
             "alt": {"lang": "java", "title": "CompanionFactoriesJava.java", "src": read(f"{lab}/demo/{J}/CompanionFactoriesJava.java"),
                     "run": demo("CompanionFactoriesJava"), "file": f"{lab}/demo/{J}/CompanionFactoriesJava.java"}},
    "expect": "The first run prints `ok: DE****3000`, `too short (8 chars)` and `bad country code '12'`, then `true` for the cached `Fee` with 290 bps and `false` for 150. Java has no `operator invoke`, so its twin needs a named factory, `Fee.of(290)`. After adding `Blocked`, the build stops: kotlinc says `'when' expression must be exhaustive. Add the 'is Blocked' branch or an 'else' branch.`, and javac says `the switch expression does not cover all possible input values`. The compiler found the one place that needs the new case."
   },
   "refs": [
    {"title": "Coding conventions: naming rules (Kotlin docs)", "url": "https://kotlinlang.org/docs/coding-conventions.html", "kind": "docs"},
    {"title": "Sealed classes and interfaces (Kotlin docs)", "url": "https://kotlinlang.org/docs/sealed-classes.html", "kind": "docs"}
   ]
  },
  {
   "h": "Abstract Factory: one choice for a whole family",
   "body": S4,
   "figure": {"svg": FIG, "caption": "Checkout asks for a family once. Both products come from that family, so a Visa auth code never reaches a Mastercard refund."}
  }
 ],
 "analogy": "A static factory is the counter at a bank branch. You ask for \"a debit card for this account\", and the clerk decides which card stock, which network and which design you get. You never walk into the print room. An abstract factory is a branch that only issues matching sets: your card, PIN letter and online-banking token all come from the same issuer, so they work together. The analogy breaks on cost: a bank can add a new kind of card at one counter, but adding a new product to an abstract factory means teaching every family to make it.",
 "in_your_world": "Card BIN routing is a factory: the first digits pick the network, and the network picks the issuer client, its base URL, its timeouts and its error mapping. Put that decision in one `when` over a sealed `Network`, return a sealed result for numbers you can't route, and inject the family factory as a function into your Quarkus resource or Temporal activity. Then a test passes a lambda that returns a fake family and records which network was asked for. For Kafka, a family of producer plus consumer plus serde, chosen once by a build profile, keeps the in-memory test setup from leaking into production config.",
 "mistake": "The most common mistake is a factory `switch` or `when` with a `default` or `else` branch that returns something plausible, such as a fake or the most common implementation. It looks defensive. In practice it turns \"you forgot to handle the new provider\" from a compile error into a production incident. Write the switch over a sealed type or an enum with no default, so the compiler forces a decision for every new case. If some input really has no product, return a sealed `Invalid` result instead of guessing.",
 "compare": {
  "title": "A validating factory that returns a sealed result",
  "java": {"title": "Money.java", "src": """public final class Money {
    private final long minor;
    private final String currency;
    private Money(long minor, String currency) { this.minor = minor; this.currency = currency; }

    public static Money ofMinor(long minor, String currency) {        // named and validating
        if (minor < 0) throw new IllegalArgumentException("negative amount");
        return new Money(minor, currency);
    }

    public sealed interface Parsed permits Ok, Bad {}
    public record Ok(Money money) implements Parsed {}
    public record Bad(String reason) implements Parsed {}

    public static Parsed parse(String text) {                         // "12.50 EUR"
        String[] parts = text.trim().split(" ");
        if (parts.length != 2) return new Bad("expected '<amount> <currency>'");
        try {
            long minor = new BigDecimal(parts[0]).movePointRight(2).longValueExact();
            return new Ok(ofMinor(minor, parts[1]));
        } catch (ArithmeticException | IllegalArgumentException e) {
            return new Bad("not an amount: " + parts[0]);
        }
    }
}

// caller: the compiler checks both cases are handled
String shown = switch (Money.parse(input)) {
    case Money.Ok(Money m) -> "charge " + m;
    case Money.Bad(String why) -> "rejected: " + why;
};"""},
  "kotlin": {"title": "Money.kt", "src": """class Money private constructor(val minor: Long, val currency: String) {
    companion object {
        @JvmStatic fun ofMinor(minor: Long, currency: String): Money {
            require(minor >= 0) { "negative amount" }
            return Money(minor, currency)
        }

        @JvmStatic fun parse(text: String): Parsed {                   // "12.50 EUR"
            val parts = text.trim().split(" ")
            if (parts.size != 2) return Parsed.Bad("expected '<amount> <currency>'")
            val minor = parts[0].toBigDecimalOrNull()
                ?.movePointRight(2)
                ?.runCatching { longValueExact() }?.getOrNull()
                ?: return Parsed.Bad("not an amount: ${parts[0]}")
            return if (minor < 0) Parsed.Bad("negative amount") else Parsed.Ok(Money(minor, parts[1]))
        }
    }
}

sealed interface Parsed {
    data class Ok(val money: Money) : Parsed
    data class Bad(val reason: String) : Parsed
}

// caller
val shown = when (val p = Money.parse(input)) {
    is Parsed.Ok -> "charge ${p.money}"
    is Parsed.Bad -> "rejected: ${p.reason}"
}"""},
  "note": "The shape is the same: private constructor, named factories, a sealed result and an exhaustive switch or `when` at the call site. Java 21 deconstructs the result with record patterns (`case Money.Ok(Money m)`), Kotlin smart-casts it after `is`. The real difference is where the factory lives. Kotlin has no `static`: `ofMinor` is a method on the companion object, so Java callers would write `Money.Companion.ofMinor(...)` without `@JvmStatic`. Kotlin also gives you `operator fun invoke` and top-level factory functions, and its named arguments remove a lot of the constructor ambiguity that pushes Java code toward factories in the first place."
 },
 "worked": {
  "title": "Replace ambiguous constructors with named factories",
  "steps": [
   {"say": "A `Refund` class grew four constructors. Look at the last line and decide what it creates before reading on.",
    "code": """public class Refund {
    public Refund(String paymentId, long amountMinor) { ... }                 // partial
    public Refund(String paymentId) { ... }                                   // full
    public Refund(String paymentId, long amountMinor, String reason) { ... }  // partial, with reason
    public Refund(String paymentId, String reason) { ... }                    // full, with reason
}

new Refund("p-1", "duplicate");   // ?""", "lang": "java",
    "alt_code": """class Refund {
    constructor(paymentId: String, amountMinor: Long) { ... }                 // partial
    constructor(paymentId: String) { ... }                                    // full
    constructor(paymentId: String, amountMinor: Long, reason: String) { ... } // partial, with reason
    constructor(paymentId: String, reason: String) { ... }                    // full, with reason
}

Refund("p-1", "duplicate")   // ?""", "alt_lang": "kotlin"},
   {"say": "It's a full refund with a reason, but only the parameter types say so. Adding a chargeback reversal would mean a fifth constructor with another type mix. Give each kind a name, validate there, and make the constructor private so every `Refund` goes through a factory.",
    "code": """public final class Refund {
    private final String paymentId;
    private final OptionalLong amountMinor;      // empty = full refund
    private final String reason;

    private Refund(String paymentId, OptionalLong amountMinor, String reason) {
        this.paymentId = paymentId; this.amountMinor = amountMinor; this.reason = reason;
    }

    public static Refund full(String paymentId, String reason) {                 // 1. the name says what you get
        return new Refund(paymentId, OptionalLong.empty(), reason);
    }

    public static Refund partial(String paymentId, long amountMinor, String reason) {
        if (amountMinor <= 0) throw new IllegalArgumentException("partial refund needs a positive amount");  // 2. validate per kind
        return new Refund(paymentId, OptionalLong.of(amountMinor), reason);
    }
}

Refund.full("p-1", "duplicate");
Refund.partial("p-1", 500, "damaged item");""", "lang": "java",
    "alt_code": """class Refund private constructor(
    val paymentId: String,
    val amountMinor: Long?,                      // null = full refund
    val reason: String,
) {
    companion object {
        fun full(paymentId: String, reason: String) = Refund(paymentId, null, reason)       // 1. the name says what you get

        fun partial(paymentId: String, amountMinor: Long, reason: String): Refund {
            require(amountMinor > 0) { "partial refund needs a positive amount" }         // 2. validate per kind
            return Refund(paymentId, amountMinor, reason)
        }
    }
}

Refund.full("p-1", "duplicate")
Refund.partial("p-1", 500, "damaged item")""", "alt_lang": "kotlin"},
   {"say": "Downstream, a full refund also releases the authorization hold. When the kinds behave differently, let the same factories return different records (or data classes) behind a sealed interface. Callers don't change, and code that handles refunds can switch over the two cases with the compiler checking it covers both. In Kotlin, `@JvmStatic` keeps `Refund.full(...)` working for Java callers, and Kotlin callers could also write `Refund.Partial(paymentId = \"p-1\", amountMinor = 500, reason = \"damaged\")`: named arguments already remove the ambiguity that started this.",
    "code": """public sealed interface Refund permits FullRefund, PartialRefund {
    String paymentId();

    static Refund full(String paymentId, String reason) { return new FullRefund(paymentId, reason); }
    static Refund partial(String paymentId, long amountMinor, String reason) {
        return new PartialRefund(paymentId, amountMinor, reason);                // 3. the factory picks the record
    }
}

record FullRefund(String paymentId, String reason) implements Refund {}
record PartialRefund(String paymentId, long amountMinor, String reason) implements Refund {
    PartialRefund {                                                              // 4. the invariant lives in the record
        if (amountMinor <= 0) throw new IllegalArgumentException("amount must be positive");
    }
}""", "lang": "java",
    "alt_code": """sealed interface Refund {
    val paymentId: String

    data class Full(override val paymentId: String, val reason: String) : Refund
    data class Partial(override val paymentId: String, val amountMinor: Long, val reason: String) : Refund {
        init { require(amountMinor > 0) { "amount must be positive" } }        // 4. the invariant lives in the class
    }

    companion object {
        @JvmStatic fun full(paymentId: String, reason: String): Refund = Full(paymentId, reason)
        @JvmStatic fun partial(paymentId: String, amountMinor: Long, reason: String): Refund =
            Partial(paymentId, amountMinor, reason)                            // 3. the factory picks the class
    }
}""", "alt_lang": "kotlin"}
  ]
 },
 "lab": {
  "title": "A card factory, a network family, and a checkout that only knows interfaces",
  "minutes": 13,
  "files": [f"{lab}/main/{K}/Card.kt", f"{lab}/main/{K}/CardNetworkClients.kt", f"{lab}/main/{K}/Checkout.kt"],
  "run": "./gradlew :patterns:test --tests 'workbench.patterns.l02.*'",
  "steps": [
   "Run the tests. All nine fail with `NotImplementedError`.",
   "Write `Card.parse` in `Card.kt`. Apply the four checks from its KDoc in order and return `CardResult.Invalid(reason)` with the exact reason strings. Only `parse` may call the private constructor.",
   "Write `CardNetworkClients.sandbox`. One private class built from settings (network, base URL, prefix) can serve both families. Use `require` for the cross-network checks, and an exhaustive `when` with no `else`.",
   "Write `Checkout.pay` as a `when` over `Card.parse(rawPan)`. Call `clientsFor` only for a valid card.",
   "Run the tests until all nine pass."
  ],
  "hints": [
   "`raw.replace(\" \", \"\")`, then `digits.all { it in '0'..'9' }` and `digits.length !in 12..19` cover the first two checks. `luhnOk` is already written.",
   "For the network, `digits.startsWith(\"4\")` is Visa. For Mastercard, check `digits.take(2).toInt() in 51..55 || digits.take(4).toInt() in 2221..2720`.",
   "`Authorizer` and `Refunder` are `fun interface`s, so `Authorizer { card, amount -> ... }` builds one from a lambda.",
   "`require(condition) { \"message\" }` throws `IllegalArgumentException` when the condition is false."
  ],
  "done_when": "All nine tests in `FactoryTest` pass."
 },
 "drill": {
  "title": "A sealed-result factory from memory",
  "minutes": 5,
  "prompt": "Close this page. In Kotlin (or Java, with a static `parse`), write `Email` with a private constructor and a companion `parse(raw: String): EmailResult`. It returns `Ok(email)` when the trimmed text has exactly one `@` with something on both sides, and `Invalid(reason)` otherwise. Then write a caller that uses `when` (or `switch`) with no `else` or `default`.",
  "answer": {"lang": "kotlin", "src": """class Email private constructor(val value: String) {
    companion object {
        fun parse(raw: String): EmailResult {
            val parts = raw.trim().split("@")
            return if (parts.size == 2 && parts.all { it.isNotEmpty() }) EmailResult.Ok(Email(raw.trim()))
            else EmailResult.Invalid("expected name@domain")
        }
    }
}

sealed interface EmailResult {
    data class Ok(val email: Email) : EmailResult
    data class Invalid(val reason: String) : EmailResult
}

fun receiptTarget(raw: String): String = when (val r = Email.parse(raw)) {
    is EmailResult.Ok -> "sending receipt to ${r.email.value}"
    is EmailResult.Invalid -> "skipped: ${r.reason}"
}""",
   "alt": {"lang": "java", "title": "Java", "src": """public final class Email {
    private final String value;
    private Email(String value) { this.value = value; }
    public String value() { return value; }

    public static EmailResult parse(String raw) {
        String[] parts = raw.trim().split("@", -1);
        return parts.length == 2 && !parts[0].isEmpty() && !parts[1].isEmpty()
                ? new EmailResult.Ok(new Email(raw.trim()))
                : new EmailResult.Invalid("expected name@domain");
    }
}

public sealed interface EmailResult {
    record Ok(Email email) implements EmailResult {}
    record Invalid(String reason) implements EmailResult {}
}

static String receiptTarget(String raw) {
    return switch (Email.parse(raw)) {
        case EmailResult.Ok ok -> "sending receipt to " + ok.email().value();
        case EmailResult.Invalid bad -> "skipped: " + bad.reason();
    };
}"""}}
 },
 "recap": [
  "A static factory is a constructor with a name. It can cache, return any subtype, and pick the class from its input (`List.of`, `EnumSet.noneOf`, `DriverManager.getConnection`).",
  "Make the constructor private and validate in the factory, so every instance in the system is a valid one.",
  "The GoF Factory Method (a subclass overrides a creation hook) is now usually a `Supplier<T>` or `() -> T`, often a constructor reference such as `FakeGateway::new`.",
  "A factory's `switch` or `when` over a sealed type or enum gets no `default` or `else`, so a new case is a compile error at the one place that must change.",
  "Kotlin factories live in the companion object, in `operator fun invoke`, or in a top-level function named like the type (`Job()`, `MutableStateFlow(0)`). Return a sealed result for outcomes callers must handle.",
  "Abstract Factory makes a family of matching products from one choice. New families are cheap; a new product touches every family."
 ],
 "quiz": [
  {"q": "Which of these can a static factory do that a constructor can never do?",
   "options": ["Return an instance of a subtype chosen from its arguments", "Validate its arguments", "Be called from another package", "Throw a checked exception"],
   "answer": 0,
   "why": "Constructors can validate, be public and throw checked exceptions too. Only a factory can return a cached object or a different class, like `List.of` returning `List12` or `ListN` depending on how many elements you pass."},
  {"q": "A factory has `switch (provider) { case ADYEN -> ...; case STRIPE -> ...; default -> new FakeGateway(); }`. A teammate adds `KLARNA` to the enum. What happens?",
   "options": ["A compile error in the factory", "A `MatchException` at runtime", "Klarna payments silently go to the fake gateway", "The switch throws `NullPointerException`"],
   "answer": 2,
   "why": "The `default` branch catches every new constant, so the build stays green and Klarna gets the fake gateway. Without `default`, a switch expression over an enum must cover every constant, and adding `KLARNA` would be a compile error at exactly this line."},
  {"q": "Which Kotlin shape lets callers write `Fee(290)` while you return a cached instance?",
   "options": ["A secondary constructor", "`operator fun invoke` in the companion object", "An `init` block", "A `data class` with a default argument"],
   "answer": 1,
   "why": "A constructor always makes a new object, whether primary or secondary. `operator fun invoke(bps: Int): Fee` on the companion turns `Fee(290)` into a function call that can return anything, including a cached instance. Readers expect a new object from that syntax, so use it with care."},
  {"q": "You have `interface MessagingFactory { Publisher publisher(); Subscriber subscriber(); }` with a Kafka family and an in-memory family. Now you need a `DeadLetterQueue` product too. What does that cost?",
   "options": ["Nothing: add one new class", "Only the Kafka family changes", "You have to switch to Factory Method", "The interface and every existing family change"],
   "answer": 3,
   "why": "Abstract Factory makes new families cheap and new products expensive: every family must now produce a dead-letter queue, including the in-memory one used in tests. Weigh that before you add a product to the interface."},
  {"q": "From lesson 1 of this track: a Kotlin `companion object` holds a factory `of(...)` and `val cache = loadCache()`. When does `loadCache()` run?",
   "options": ["When the outer class is loaded, like a Java static initializer", "Lazily, the first time `cache` is read, under a lock", "Every time `of` is called", "At application startup, for every class on the classpath"],
   "answer": 0,
   "why": "A companion object is initialized when its outer class is loaded, which matches a Java static initializer, so `loadCache()` runs then even if nobody reads `cache`. If you want it on first read, write `val cache by lazy { loadCache() }`.",
   "from": "pat-01"}
 ],
 "flashcards": [
  {"front": "Name two things a static factory can do that a constructor can't.", "back": "Return a cached instance, and return a subtype chosen from its arguments (`List.of` gives `List12` or `ListN`). It also has a name."},
  {"front": "Why leave out `default` in a factory's switch over a sealed type or enum?", "back": "So adding a new case is a compile error at the factory. With `default`, the new case silently takes the default branch."},
  {"front": "What replaced the GoF Factory Method's creator subclass in modern Java?", "back": "A function: a `Supplier<PaymentGateway>`, usually written as a constructor reference such as `AdyenGateway::new`."},
  {"front": "Kotlin has no `static`. Where does a class's named factory usually live?", "back": "In its `companion object`: `companion object { fun parse(raw: String): CardResult }`."},
  {"front": "What name may a Kotlin factory function have, by the coding conventions?", "back": "The same name as the abstract type it returns, like `fun Job(): Job` or `MutableStateFlow(0)`."},
  {"front": "When should a factory return a sealed result instead of throwing?", "back": "When the failure is an outcome the caller is expected to handle, like a mistyped card number. Keep exceptions for bugs and broken infrastructure."},
  {"front": "Abstract Factory: what is cheap to add, and what is expensive?", "back": "A new family is cheap (one implementation). A new product is expensive (the interface and every family change)."}
 ],
 "terms": [
  {"term": "Static factory method", "plain": "A static method that returns an instance, used instead of a public constructor."},
  {"term": "Factory Method (GoF)", "plain": "A creation hook that lets something other than the caller pick the concrete class. Now often a `Supplier<T>` or `() -> T`."},
  {"term": "Abstract Factory", "plain": "An interface that creates a whole family of matching objects, with one implementation per family."},
  {"term": "Product family", "plain": "Objects that must be used together, such as one network's authorizer and refunder."},
  {"term": "Sealed result", "plain": "A sealed set of outcomes (`Valid`, `Invalid`) returned instead of throwing. A `switch` or `when` must handle every case."},
  {"term": "Companion object", "plain": "A Kotlin object tied to a class, and the usual home for that class's factories."}
 ],
 "explain_back": {
  "prompt": "Explain to a teammate why `CardNetworkClients.sandbox(network)` has no `else` branch, and why `Checkout` takes a `(Network) -> CardNetworkClients` instead of calling `sandbox` directly.",
  "answer": "With no `else`, the `when` has to name every `Network`. When someone adds `AMEX`, the factory stops compiling until they decide which family Amex gets, instead of quietly falling into a default. The function parameter keeps `Checkout` ignorant of which families exist and how they're built. Production passes `CardNetworkClients::sandbox` or a live factory, and a test passes a lambda that returns a fake family and records which network was asked for. So the choice of concrete classes lives in one place, and the checkout logic can be tested without any network client."
 },
 "deeper": {
  "minutes": 10,
  "body": """`DriverManager` is a factory whose products did not exist when it was written. On first use it asks `ServiceLoader` for every `java.sql.Driver` that a JAR on the classpath lists in a `META-INF/services/java.sql.Driver` file. `getConnection(url)` then offers the URL to each driver until one accepts it. You can build the same plug-in mechanism yourself: define an interface, list the implementations in `META-INF/services/<interface name>`, and call `ServiceLoader.load(YourInterface.class)`. The module system adds `provides ... with ...` and `uses ...` declarations for the same thing.

Effective Java lists conventional factory names, and sticking to them makes factories easy to find: `from` for a one-argument conversion (`Date.from(instant)`), `of` for aggregation (`EnumSet.of(...)`), `valueOf`, `getInstance` or `instance`, `create` or `newInstance` when each call returns a new object, `getType` and `newType` when the factory lives in another class (`Files.newBufferedReader`), and a bare `type` (`Collections.list`).

From Java, a Kotlin companion factory is `Money.Companion.parse(...)`. Annotate it with `@JvmStatic` and Java callers can write `Money.parse(...)`. If a Java team consumes your Kotlin library, do it for every public factory. The same goes for `@JvmOverloads` on functions with default arguments, which you'll meet in *Builder and Prototype* (lesson 3 of this track)."""
 },
 "sources": [
  {"title": "Object declarations and companion objects (Kotlin docs)", "url": "https://kotlinlang.org/docs/object-declarations.html"},
  {"title": "Sealed classes and interfaces (Kotlin docs)", "url": "https://kotlinlang.org/docs/sealed-classes.html"},
  {"title": "JEP 441: Pattern Matching for switch", "url": "https://openjdk.org/jeps/441"},
  {"title": "DriverManager (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.sql/java/sql/DriverManager.html"}
 ]
}

out = ROOT / "content/lessons/pat-02.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print("wrote", out)
