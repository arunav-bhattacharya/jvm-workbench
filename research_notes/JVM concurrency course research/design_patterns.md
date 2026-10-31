# GoF + Concurrency Design Patterns in Modern Java (21-25+) and Kotlin 2.x — research notes (as of 2026-10-30)

How these notes were produced, and how to read them:
- **Network limits.** This session could reach only `kotlinlang.org`, `raw.githubusercontent.com`/`github.com` and `repo1.maven.org`. The following hosts were blocked by the session's egress policy and could NOT be fetched: openjdk.org (JEP pages), docs.oracle.com, docs.spring.io, resilience4j.readme.io, refactoring.guru, quarkus.io, infoq.com, inside.java, dev.java, baeldung.com, youtube.com. To compensate, primary sources were read from their **GitHub source of truth** instead: the OpenJDK source tree at the `jdk-25-ga`, `jdk-26-ga`, `jdk-27-ga` and `master` tags (the Javadoc lives in the `.java` files), the Spring Framework and Quarkus AsciiDoc sources, Resilience4j source, Joshua Bloch's official Effective Java 3e code repo, and Brian Goetz's design notes in `openjdk/amber-docs`.
- **Every code sample below was compiled and run in this session.** Java ran on `javac`/`java` 21.0.12.1 with `--release 21` and no preview flags. Kotlin ran on `kotlinc-jvm` 2.4.21 with kotlinx-coroutines 1.11.0. Resilience4j 2.4.0 jars came from Maven Central. The samples include assertion-style tests, and all of them passed. Some claims are marked **[local]**: that means the compiler or a run in this session showed it, not a web page.
- **Evidence tags.** **[src]** = read from a fetched primary source (a link is given). **[local]** = reproduced by compiling or running here. **[search]** = seen only in a web-search snippet, page not fetched; re-check before quoting in a lesson. **[bg]** = background knowledge that could not be checked here because the source was blocked; this also appears under Gaps.

---

## Key Question 1 — Per-pattern catalog: intent, backend problem, modern Java, idiomatic Kotlin, what the language makes unnecessary, main pitfall

### Takeaway
In Java 21+ and Kotlin 2.x, most GoF patterns are still worth teaching, but many become **a few lines of language feature rather than a class hierarchy**:
- Strategy, Template Method and Command turn into function values.
- Visitor and State turn into sealed types plus an exhaustive `switch`/`when`.
- Builder mostly turns into named/default arguments (Kotlin) or records plus a small builder (Java).
- Decorator turns into Kotlin `by` delegation or default-method combinators.
- Singleton turns into `enum`/holder (Java) and `object`/`lazy` (Kotlin).

Patterns that remain structurally important are the ones built on runtime indirection: **Proxy** (Spring/Quarkus AOP), **Chain of Responsibility** (servlet filters, OkHttp interceptors), **Observer** (Flow/StateFlow/Reactor), and the concurrency patterns. JDK 21 virtual threads and library-level circuit breakers and bulkheads change how those concurrency patterns are applied.

### Cited Findings

#### 0. Platform baseline (verify before each lesson; these move)
- **JDK releases.** JDK 25 GA had Stable Values as a preview API (JEP 502, `StableValue`, `@since 25`) and Structured Concurrency as JEP 505 "Fifth Preview" — [PreviewFeature.java @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/jdk/internal/javac/PreviewFeature.java), [StableValue.java @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/StableValue.java)
- **ScopedValue is final in JDK 25.** It is `@since 25` and has no `@PreviewFeature` annotation — [ScopedValue.java @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/ScopedValue.java)
- **JDK 26 GA.** Stable Values was renamed to **Lazy Constants** (JEP 526, "Second Preview"; `java.lang.LazyConstant`, `@since 26`, a `sealed interface`), and `StableValue.java` no longer exists at that tag (HTTP 404). Structured Concurrency moved to JEP 525 "Sixth Preview" — [PreviewFeature.java @ jdk-26-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-26-ga/src/java.base/share/classes/jdk/internal/javac/PreviewFeature.java)
- **JDK 27 GA.** GA date 2026-09-15. Lazy Constants is JEP 531 "Third Preview" and Structured Concurrency is JEP 533 "Seventh Preview" — [version-numbers.conf @ jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/make/conf/version-numbers.conf), [PreviewFeature.java @ jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/java.base/share/classes/jdk/internal/javac/PreviewFeature.java)
- **OpenJDK `master` is JDK 28, still in development.** `DEFAULT_VERSION_DATE=2027-03-23`. There, `StructuredTaskScope` is `@since 28` with **no `@PreviewFeature`**, which suggests it will become final in JDK 28 (in development, so subject to change), while Lazy Constants stays preview (JEP 531) — [version-numbers.conf @ master](https://raw.githubusercontent.com/openjdk/jdk/master/make/conf/version-numbers.conf), [StructuredTaskScope.java @ master](https://raw.githubusercontent.com/openjdk/jdk/master/src/java.base/share/classes/java/util/concurrent/StructuredTaskScope.java), [PreviewFeature.java @ master](https://raw.githubusercontent.com/openjdk/jdk/master/src/java.base/share/classes/jdk/internal/javac/PreviewFeature.java)
- **Final in JDK 21.** Records, sealed interfaces, pattern matching for `switch` with guards (`when`), and record patterns (including nested ones) all compiled and ran with `--release 21` and no `--enable-preview`. **[local]**
- **Kotlin.** The latest stable on Maven Central is **2.4.21**; 2.5.0-Beta2 was published (metadata lastUpdated 2026-10-21) — [kotlin-stdlib maven-metadata](https://repo1.maven.org/maven2/org/jetbrains/kotlin/kotlin-stdlib/maven-metadata.xml). kotlinx-coroutines latest is 1.11.0 — [coroutines maven-metadata](https://repo1.maven.org/maven2/org/jetbrains/kotlinx/kotlinx-coroutines-core/maven-metadata.xml)
- **Kotlin 2.2.0** (released June 23, 2025) made these Stable: "Guard conditions in `when` with a subject", "Non-local `break` and `continue`", and "Multi-dollar interpolation". **Context parameters** were preview (`-Xcontext-parameters`) — [Kotlin 2.2.0 What's new](https://kotlinlang.org/docs/whatsnew22.html)
- **Resilience4j.** The latest release on Maven Central is **2.4.0** (metadata lastUpdated 2026-03-14) — [maven-metadata](https://repo1.maven.org/maven2/io/github/resilience4j/resilience4j-circuitbreaker/maven-metadata.xml). The `master` README says "Resilience4j 3 requires Java 21" and adds virtual-thread schedulers (`resilience4j.thread.type: virtual`). Version 3 was not on Central when checked — [Resilience4j README @ master](https://raw.githubusercontent.com/resilience4j/resilience4j/master/README.adoc)
- **Spring Framework 7.0** added core resilience annotations (`@Retryable`, `@ConcurrencyLimit`) and the `@Proxyable` proxy-type override — [Spring resilience.adoc](https://raw.githubusercontent.com/spring-projects/spring-framework/main/framework-docs/modules/ROOT/pages/core/resilience.adoc), [Spring proxying.adoc](https://raw.githubusercontent.com/spring-projects/spring-framework/main/framework-docs/modules/ROOT/pages/core/aop/proxying.adoc)

---

#### CREATIONAL

##### Singleton
- **Intent.** Guarantee one instance and a global access point. Kotlin docs: "A singleton ensures that a class has only one instance and provides a global point of access to it." — [Kotlin object declarations](https://kotlinlang.org/docs/object-declarations.html)
- **Backend problem.** One process-wide ID generator, metrics registry, or connection-pool holder. In practice prefer a DI-container singleton scope; the hand-rolled pattern belongs at library edges.
- **JDK example.** "Every Java application has a single instance of class `Runtime`… An application cannot create its own instance of this class." `getRuntime()` simply returns the static `currentRuntime` field — [Runtime.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Runtime.java)
- **Effective Java Item 3.** The official code repo labels the enum version "Enum singleton - the preferred approach (Page 18)" and also shows the "public final field" variant (page 17) and the static-factory variant — [EJ3 item3 enumtype/Elvis.java](https://raw.githubusercontent.com/jbloch/effective-java-3e-source-code/master/src/effectivejava/chapter2/item3/enumtype/Elvis.java), [field/Elvis.java](https://raw.githubusercontent.com/jbloch/effective-java-3e-source-code/master/src/effectivejava/chapter2/item3/field/Elvis.java)
- **Java, three thread-safe variants.** Uniqueness was checked under 1,000 concurrent virtual-thread calls. **[local]**
```java
enum IdGenerator {                                   // (a) enum: serialization- and reflection-safe
    INSTANCE;
    private final AtomicLong next = new AtomicLong();
    long nextId() { return next.incrementAndGet(); }
}
static final class FxRates {                         // (b) initialization-on-demand holder: lazy, lock-free
    private FxRates() { }
    private static final class Holder { static final FxRates INSTANCE = new FxRates(); }
    static FxRates getInstance() { return Holder.INSTANCE; }
}
static final class GatewayConfig {                   // (c) double-checked locking: needs volatile
    private static volatile GatewayConfig instance;
    private GatewayConfig() { }
    static GatewayConfig getInstance() {
        GatewayConfig local = instance;              // one volatile read on the fast path
        if (local == null) {
            synchronized (GatewayConfig.class) {
                local = instance;
                if (local == null) instance = local = new GatewayConfig();
            }
        }
        return local;
    }
}
```
- **Why the holder idiom and DCL are correct.** The holder relies on the JVM initializing `Holder` lazily, exactly once, under the class-initialization lock. DCL is correct only because `volatile` gives safe publication under the Java Memory Model (since Java 5 / JSR-133). **[bg]** JLS 12.4.2 and EJ Item 83 could not be fetched.
- **Modern JDK option (preview only).**
  - JDK 25's `StableValue` is "a holder of contents that can be set at most once" — [StableValue.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/StableValue.java).
  - In JDK 26+ it became `LazyConstant.of(() -> …)`. `get()` guarantees "out of several threads trying to invoke the computing function simultaneously, only one is ever selected for computation".
  - It can never hold `null`: a null result throws `NoSuchElementException`.
  - A failed computation moves it to an **error state**; later `get()` calls throw without re-running the function.
  - Source: [LazyConstant.java @ master](https://raw.githubusercontent.com/openjdk/jdk/master/src/java.base/share/classes/java/lang/LazyConstant.java). Teach this as "preview, still changing" (third preview in JDK 27).
- **Kotlin `object`.** "The initialization of an object declaration is thread-safe and done on first access." A companion object "is initialized when the corresponding class is loaded (resolved) that matches the semantics of a Java static initializer". Companion members "look like static members… they are actually instance members of the companion object". `@JvmStatic` makes real JVM statics — [Kotlin object declarations](https://kotlinlang.org/docs/object-declarations.html)
- **`data object`.** It generates `toString()` (the object's name) plus `equals()`/`hashCode()`. Because serialization or reflection can create a second instance, the docs say: compare data objects with `==`, "never by reference (using the `===` operator)" — [Kotlin object declarations](https://kotlinlang.org/docs/object-declarations.html)
- **Kotlin `lazy` modes** (verbatim from the stdlib docs) — [LazyThreadSafetyMode](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-lazy-thread-safety-mode/):
  - `SYNCHRONIZED`: "Uses a lock to ensure that only a single thread can initialize a Lazy instance, and ensures that initialized value is visible by all threads."
  - `PUBLICATION`: "Initializer function can be called several times on concurrent access… but only one computed value will be used."
  - `NONE`: "No locks are used… If the instance is accessed from multiple threads, its behavior is unspecified."
- **Default `lazy` mode.** "By default, the evaluation of lazy properties is synchronized: the value is computed only in one thread, but all threads will see the same value." — [Kotlin delegated properties](https://kotlinlang.org/docs/delegated-properties.html)
```kotlin
object IdGenerator { private val next = AtomicInteger(); fun nextId() = next.incrementAndGet() }
class FxService {
    val rates: Map<String, Double> by lazy { loadRates() }                       // SYNCHRONIZED (default)
    val cheap: String by lazy(LazyThreadSafetyMode.PUBLICATION) { compute() }  // may run >1 time; one value wins
    val local: String by lazy(LazyThreadSafetyMode.NONE) { compute() }         // single-thread confinement only
}
```
- **What the language makes unnecessary.** The Java `enum` and Kotlin `object` remove all hand-written locking. Kotlin `lazy` removes DCL.
- **Main pitfalls.**
  - DCL without `volatile`. **[bg]**
  - Choosing `PUBLICATION` when the initializer has side effects (such as opening a pool), since it may run several times. **[src]** see quote above.
  - Hidden global state that makes tests order-dependent. **[bg]**

##### Factory Method (and the static factory)
- **Intent.** Let a creator decide which concrete product to instantiate, so clients depend only on an interface.
- **Backend problem.** Choose the PSP gateway (Stripe, Adyen, fake) by configuration or tenant. Choose a JDBC driver by URL.
- **JDK example.** `DriverManager` is "The basic service for managing a set of JDBC drivers". It discovers drivers "via the service-provider loading mechanism" (`ServiceLoader`). `getConnection(String url)` returns a `Connection` from whichever driver accepts the URL — [DriverManager.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.sql/share/classes/java/sql/DriverManager.java)
- **Effective Java 3e Item 1** (static factory methods) is the modern default. The EJ repo also has a static-factory Elvis singleton variant — [EJ3 item3 staticfactory](https://raw.githubusercontent.com/jbloch/effective-java-3e-source-code/master/src/effectivejava/chapter2/item3/staticfactory/Elvis.java)
- **Java.** **[local]**
```java
sealed interface PaymentGateway permits StripeGateway, AdyenGateway, FakeGateway {
    Receipt charge(Money amount, String token);
    static PaymentGateway of(Provider p) {               // static factory; exhaustive enum switch, no default
        return switch (p) {
            case STRIPE -> new StripeGateway();
            case ADYEN  -> new AdyenGateway();
            case FAKE   -> new FakeGateway();
        };
    }
}
// GoF Factory Method proper: subclass overrides the creation hook
static abstract class CheckoutService {
    protected abstract PaymentGateway createGateway();
    final Receipt pay(Money m, String token) { return createGateway().charge(m, token); }
}
// Modern replacement: inject the factory as a function
record FunctionalCheckout(Supplier<? extends PaymentGateway> gatewayFactory) {
    Receipt pay(Money m, String token) { return gatewayFactory.get().charge(m, token); }
}
// usage: new FunctionalCheckout(StripeGateway::new)
```
- **Kotlin.** **[local]** Kotlin docs show a companion object implementing an interface (`companion object : Factory<User>`) — [Kotlin object declarations](https://kotlinlang.org/docs/object-declarations.html)
```kotlin
sealed interface PaymentGateway {
    fun charge(m: Money, token: String): String
    companion object {
        fun of(p: Provider): PaymentGateway = when (p) { Provider.STRIPE -> Stripe; Provider.ADYEN -> Adyen; Provider.FAKE -> Fake() }
    }
}
class Checkout(private val gatewayFactory: () -> PaymentGateway) { fun pay(m: Money, t: String) = gatewayFactory().charge(m, t) }
// Checkout(::Fake)
```
- **What the language makes unnecessary.** Creator subclasses: a `Supplier`/`() -> T` or a constructor reference *is* the factory. With a sealed product hierarchy, the compiler checks that every product is covered by the factory `switch`. **[local]**
- **Pitfall.** A factory `switch` with `default ->` hides new products from the compiler. A god-factory that also wires configuration belongs in the DI container. **[local]** default-branch behavior shown in the exhaustiveness tests below.

##### Abstract Factory
- **Intent.** Create *families* of related objects without naming concrete classes.
- **Backend problem.** A messaging family (publisher + subscriber) for Kafka in production vs. in-memory in tests. A cloud family (queue + blob + KMS) per provider.
- **Java.** **[local]**
```java
interface MessagingFactory { Publisher publisher(); Subscriber subscriber(); }
static final class InMemoryMessaging implements MessagingFactory {
    private final Map<String, List<String>> topics = new ConcurrentHashMap<>();
    public Publisher publisher()  { return (t, m) -> topics.computeIfAbsent(t, k -> new CopyOnWriteArrayList<>()).add(m); }
    public Subscriber subscriber() { return t -> List.copyOf(topics.getOrDefault(t, List.of())); }
}
```
- **Kotlin.** Same shape. Usually an `interface` plus `object InMemoryMessaging : MessagingFactory`, or a class with constructor parameters.
- **What the language makes unnecessary.** When each product is a functional interface, the products become lambdas (above). The family is just "a record or interface of functions".
- **Pitfall.** Adding a new product type forces a change to every factory (the classic weakness). In DI-heavy services, Spring profiles or Quarkus build-time configuration often replace the pattern. **[bg]**

##### Builder
- **Intent.** Separate the step-by-step construction of a complex object from its representation.
- **Backend problem.** HTTP request specs, PSP charge requests with many optional fields, test fixtures.
- **JDK examples.** `HttpClient.newBuilder()`, and `Thread.ofPlatform()` / `Thread.ofVirtual()`, which return the `Thread.Builder` sealed interface — [HttpClient.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.net.http/share/classes/java/net/http/HttpClient.java), [Thread.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Thread.java)
- **Effective Java Item 2.** The repo includes `NutritionFacts` (telescoping vs builder) and "Builder pattern for class hierarchies (Page 14)". The latter uses a recursive generic `Builder<T extends Builder<T>>` with an abstract `self()` method (the "simulated self-type" idiom) — [EJ3 item2 hierarchicalbuilder/Pizza.java](https://raw.githubusercontent.com/jbloch/effective-java-3e-source-code/master/src/effectivejava/chapter2/item2/hierarchicalbuilder/Pizza.java)
- **Java (record + nested builder + "wither").** **[local]** Mutating `headers()` threw `UnsupportedOperationException`.
```java
record HttpRequestSpec(URI uri, String method, Map<String,String> headers, Duration timeout, int maxRetries) {
    HttpRequestSpec {                                   // compact canonical ctor: validate + normalize
        Objects.requireNonNull(uri);
        headers = Map.copyOf(headers);                  // defensive copy -> really immutable
        if (maxRetries < 0) throw new IllegalArgumentException("maxRetries < 0");
    }
    static Builder builder(URI uri) { return new Builder(uri); }
    HttpRequestSpec withTimeout(Duration t) { return new HttpRequestSpec(uri, method, headers, t, maxRetries); }
    static final class Builder {
        private final URI uri; private String method = "GET";
        private final Map<String,String> headers = new LinkedHashMap<>();
        private Duration timeout = Duration.ofSeconds(10); private int maxRetries = 0;
        private Builder(URI uri) { this.uri = uri; }
        Builder method(String m) { this.method = m; return this; }
        Builder header(String k, String v) { headers.put(k, v); return this; }
        Builder timeout(Duration t) { this.timeout = t; return this; }
        Builder maxRetries(int n) { this.maxRetries = n; return this; }
        HttpRequestSpec build() { return new HttpRequestSpec(uri, method, headers, timeout, maxRetries); }
    }
}
```
- **Kotlin: named and default arguments replace most builders.** The compiler-generated `copy` acts as the "wither". **[local]**
```kotlin
data class HttpRequestSpec(
    val url: String, val method: String = "GET", val headers: Map<String, String> = emptyMap(),
    val timeoutMs: Long = 10_000, val maxRetries: Int = 0,
) { init { require(maxRetries >= 0) } }
val spec = HttpRequestSpec(url = "https://psp.example/charge", method = "POST", maxRetries = 2)
val faster = spec.copy(timeoutMs = 2_000)
```
- **When a builder still helps (Kotlin or Java).**
  - Java callers, which have no named arguments.
  - Construction spread across steps or conditionals: stdlib `buildList { … }` / `buildString`. **[local]**
  - Hierarchical, nested data, which calls for a type-safe DSL builder.
  - Validation that needs the whole object.
- **Type-safe DSL builders.** "By using well-named functions as builders in combination with function literals with receiver, it is possible to create type-safe, statically-typed builders". `@DslMarker` makes "the Kotlin compiler… allow to call members of the nearest receivers only". "It's enough to annotate only the superclass". An outer receiver stays reachable explicitly via `this@html` — [Kotlin type-safe builders](https://kotlinlang.org/docs/type-safe-builders.html)
```kotlin
@DslMarker annotation class PaymentDsl
@PaymentDsl class LineItemsBuilder { private val items = mutableListOf<Pair<String, Long>>()
    fun item(sku: String, minor: Long) { items += sku to minor }; fun build() = items.toList() }
@PaymentDsl class PaymentRequestBuilder {
    var amount: Long = 0; var currency: String = "EUR"
    private var lines: List<Pair<String, Long>> = emptyList()
    fun lineItems(block: LineItemsBuilder.() -> Unit) { lines = LineItemsBuilder().apply(block).build() }
    fun build() = PaymentRequest(amount, currency, lines)
}
fun paymentRequest(block: PaymentRequestBuilder.() -> Unit) = PaymentRequestBuilder().apply(block).build()
val req = paymentRequest { amount = 1_500; lineItems { item("sku-1", 1_000); item("sku-2", 500) } }
```
- **Negative compile test [local].** Writing `amount = 1` inside `lineItems { }` fails with: "error: 'var amount: Long' cannot be called in this context with an implicit receiver. Use an explicit receiver if necessary."
- **Pitfall (Java).** Builders that skip validation in `build()`. Put invariants in the record's compact constructor so *every* path validates, withers included.
- **Pitfall (Kotlin).** See the `copy()` visibility trap under Prototype.

##### Prototype
- **Intent.** Create new objects by copying an existing one.
- **Backend problem.** Cloning a template payment request, a default config, or a test fixture, then changing a few fields.
- **`Cloneable` is broken by design.**
  - "Note that this interface does *not* contain the `clone` method. Therefore, it is not possible to clone an object merely by virtue of the fact that it implements this interface." — [Cloneable.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Cloneable.java)
  - `Object.clone()` "performs a 'shallow copy' of this object, not a 'deep copy' operation." — [Object.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Object.java)
  - EJ Item 13's `Stack.clone()` has to `super.clone()`, then manually `result.elements = elements.clone()`, and catch an impossible `CloneNotSupportedException` with `throw new AssertionError()`. That is the boilerplate students should see once — [EJ3 item13 Stack.java](https://raw.githubusercontent.com/jbloch/effective-java-3e-source-code/master/src/effectivejava/chapter3/item13/Stack.java)
- **Modern Java.** Use copy constructors or static copy factories, records with withers, and `List.copyOf` for components.
- **The shallow-copy trap is real for records too [local].** `new Cart("c2", c1.items())` followed by `c2.items().add(..)` mutates `c1`. The fix:
```java
record SafeCart(String id, List<String> items) {
    SafeCart { items = List.copyOf(items); }
    SafeCart withItem(String sku) { var copy = new ArrayList<>(items); copy.add(sku); return new SafeCart(id, copy); }
}
```
- **Kotlin `copy()` is shallow.** "The `copy()` function creates a shallow copy of the instance. In other words, it doesn't copy components recursively. As a result, references to other objects are shared." Explicit implementations of `copy()`/`componentN()` are not allowed, and only primary-constructor properties take part — [Kotlin data classes](https://kotlinlang.org/docs/data-classes.html)
- **Shallow trap reproduced [local].** `val c2 = c1.copy(id = "c2"); c2.items += "sku-2"` changes `c1.items` when `items` is a `MutableList`. Fix it with read-only `List` plus `copy(items = items + x)`.
- **`copy()` visibility trap [local] (kotlinc 2.4.21).**
  - `data class Email private constructor(val value: String)` still gets a **public** `copy()`. The compiler only warns: "non-public primary constructor is exposed via the generated 'copy()' method of the 'data' class. The generated 'copy()' will change its visibility in future releases."
  - So `Email.of("a@b").copy(value = "not-an-email")` **compiles and bypasses validation done in a factory**.
  - Annotating the class with `@ConsistentCopyVisibility` makes `copy` private (call → "cannot access 'fun copy…': it is private").
  - Validation inside `init { require(...) }` *does* run on `copy()`: `Amount(5).copy(minor = -1)` threw "negative".
- **What the language makes unnecessary.** `Cloneable`/`clone()` entirely.
- **Pitfall.** Shallow copies of mutable components, in both languages.

---

#### STRUCTURAL

##### Adapter
- **Intent.** Convert one interface into another that clients expect.
- **Backend problem.** Wrapping a legacy SOAP PSP client, a vendor SDK, or a different HTTP client behind your `PaymentGateway` port (hexagonal-architecture "adapters").
- **Java.** **[local]**
```java
record SoapGatewayAdapter(LegacySoapClient soap) implements PaymentGateway {
    public String charge(Money m, String token) {
        return soap.submitTxn("<txn amt='" + m.minor() + "' cur='" + m.currency() + "' tok='" + token + "'/>");
    }
}
// functional-interface adapter: any compatible lambda/method ref adapts
static PaymentGateway lambdaAdapter(BiFunction<Long, String, String> legacy) { return (m, t) -> legacy.apply(m.minor(), t); }
```
- **Kotlin.** A class implementing the target interface, or an **extension function** that adapts at the call site (`fun LegacyTxn.toReceipt(): Receipt`). SAM conversion lets `fun interface` targets be satisfied by lambdas (OkHttp's `fun interface Interceptor` is a real example; see CoR).
- **What the language makes unnecessary.** For single-method targets, a lambda or method reference *is* the adapter.
- **Pitfall.** "Leaky" adapters that expose vendor exceptions and types. Translate errors to domain errors at the adapter boundary. **[bg]**

##### Facade
- **Intent.** Provide one simplified interface to a subsystem.
- **Backend problem.** A `CheckoutFacade` that orchestrates inventory reservation, payment, and notification, so controllers stay thin.
- **Java.** **[local]**
```java
record CheckoutFacade(Inventory inv, PaymentGateway pay, Notifier notifier) {
    String checkout(String sku, Money m, String token, String email) {
        if (!inv.reserve(sku)) throw new IllegalStateException("out of stock");
        String receipt = pay.charge(m, token);
        notifier.send(email, "paid " + receipt);
        return receipt;
    }
}
```
- **Gotcha found while compiling [local].** The component was first named `notify`, and javac 21 rejected it: "error: illegal record component name notify". A record component cannot share a name with a no-arg `Object` method (accessor clash). Worth a slide.
- **Kotlin.** Same shape, as a class with constructor-injected collaborators.
- **What the language makes unnecessary.** Nothing structural. Records shrink the boilerplate.
- **Pitfall.** A Facade that grows into a god service. Keep it orchestration-only.

##### Decorator
- **Intent.** Attach responsibilities to an object dynamically by wrapping it behind the same interface.
- **Backend problem.** Fee calculators (base % + fixed + cross-border surcharge + cap). Also HTTP clients wrapped with logging, metrics, or retry.
- **JDK classic.** "A `FilterInputStream` wraps some other input stream, which it uses as its basic source of data, possibly transforming the data along the way or providing additional functionality." — [FilterInputStream.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/io/FilterInputStream.java). A `DataOutputStream(BufferedOutputStream(GZIPOutputStream(...)))` round-trip passed. **[local]**
- **Java (default-method combinators; each returns a wrapping lambda).** **[local]** Expected values: 10,000 minor domestic → 320; cross-border → 420; 100,000 cross-border → 500 (capped). Moving `cappedAt` *before* `crossBorder` gives 1,500, so **order matters**.
```java
@FunctionalInterface interface FeeCalculator {
    long feeMinor(Payment p);
    static FeeCalculator percent(int bps) { return p -> p.amount().minor() * bps / 10_000; }
    default FeeCalculator plusFixed(long fixed) { return p -> feeMinor(p) + fixed; }
    default FeeCalculator crossBorder(String home, int extraBps) {
        return p -> feeMinor(p) + (p.country().equals(home) ? 0 : p.amount().minor() * extraBps / 10_000);
    }
    default FeeCalculator cappedAt(long cap) { return p -> Math.min(feeMinor(p), cap); }
}
FeeCalculator calc = FeeCalculator.percent(290).plusFixed(30).crossBorder("DE", 100).cappedAt(500);
```
- **Kotlin class delegation.** "The Delegation pattern has proven to be a good alternative to implementation inheritance, and Kotlin supports it natively requiring zero boilerplate code." With `class Derived(b: Base) : Base by b`, "the compiler will generate all the methods of `Base` that forward to `b`." Caveat: "members overridden in this way do not get called from the members of the delegate object, which can only access its own implementations of the interface members." — [Kotlin delegation](https://kotlinlang.org/docs/delegation.html)
- **Proof of the caveat [local].** In a `CountingMap : MutableMap<K,V> by inner` that overrides only `put`, `put("a",1); putAll(mapOf("b" to 2, "c" to 3))` leaves `puts == 1` with `size == 3`. `putAll` goes straight to `inner`.
```kotlin
class CountingMap<K, V>(private val inner: MutableMap<K, V> = HashMap()) : MutableMap<K, V> by inner {
    var puts = 0
    override fun put(key: K, value: V): V? { puts++; return inner.put(key, value) }
}
fun interface FeeCalculator { fun fee(amount: Long, crossBorder: Boolean): Long }
class Capped(private val inner: FeeCalculator, private val cap: Long) : FeeCalculator by inner {
    override fun fee(amount: Long, crossBorder: Boolean) = minOf(inner.fee(amount, crossBorder), cap)
}
fun FeeCalculator.plusFixed(f: Long) = FeeCalculator { a, cb -> fee(a, cb) + f }   // extension-function decorators
```
- **Libraries.** Resilience4j is explicitly a decorator library: it "provides higher-order functions (decorators) to enhance any functional interface, lambda expression or method reference with a Circuit Breaker, Rate Limiter, Retry or Bulkhead… You can stack more than one decorator" — [Resilience4j README](https://raw.githubusercontent.com/resilience4j/resilience4j/master/README.adoc)
- **What the language makes unnecessary.** Abstract `Decorator` base classes with N forwarding methods: Kotlin `by` generates them. In Java, functional interfaces plus default methods make decorators one-liners.
- **Pitfalls.**
  - Order of decoration changes results (shown above).
  - Kotlin `by` does not give "open recursion" (shown above).
  - Identity and `equals` of the wrapper differ from the wrapped object. **[bg]**

##### Proxy (dynamic proxies, Spring/Quarkus, the self-invocation pitfall)
- **Intent.** Provide a surrogate that controls access to another object: lazy (virtual), remote, protection, or cross-cutting (AOP).
- **Backend problem.** Transparent retries, timeouts, metrics, `@Transactional`, caching, authorization around a service.
- **`java.lang.reflect.Proxy`.** It "provides static methods for creating objects that act like instances of interfaces but allow for customized method invocation." A proxy class "is a class created at runtime that implements a specified list of interfaces". Calls are "dispatched to the `invoke` method of the instance's invocation handler". A proxy class is "final and non-abstract", "extends `java.lang.reflect.Proxy`", and `Proxy.isProxyClass` detects it — [Proxy.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/reflect/Proxy.java)
- **Java retrying proxy.** **[local]** The flaky target fails twice, then succeeds, after 3 calls.
```java
@SuppressWarnings("unchecked")
static <T> T retrying(Class<T> iface, T target, int maxAttempts, Predicate<Throwable> retryOn) {
    InvocationHandler h = (proxy, method, args) -> {
        Throwable last = null;
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try { return method.invoke(target, args); }
            catch (InvocationTargetException e) {          // MUST unwrap, or callers see the reflective wrapper
                last = e.getCause();
                if (!retryOn.test(last)) throw last;
            }
        }
        throw last;
    };
    return (T) Proxy.newProxyInstance(iface.getClassLoader(), new Class<?>[]{iface}, h);
}
```
- **Kotlin retrying proxy.** `reified` removes the `Class<T>` parameter. **[local]**
```kotlin
inline fun <reified T : Any> retrying(target: T, maxAttempts: Int): T =
    Proxy.newProxyInstance(T::class.java.classLoader, arrayOf(T::class.java)) { _, method, args ->
        var last: Throwable? = null
        repeat(maxAttempts) {
            try { return@newProxyInstance method.invoke(target, *(args ?: emptyArray())) }
            catch (e: InvocationTargetException) { last = e.cause }
        }
        throw last!!
    } as T
```
- **Spring AOP.**
  - "Spring AOP uses either JDK dynamic proxies or CGLIB… If the target object to be proxied implements at least one interface, a JDK dynamic proxy is used… If the target object does not implement any interfaces, a CGLIB proxy is created which is a runtime-generated subclass of the target type."
  - "`final` methods cannot be advised… `private` methods cannot be advised."
  - "While the core framework suggests interface-based proxies by default, Spring Boot may - depending on configuration properties - enable class-based proxies by default."
  - "As of 7.0", `@Proxyable(INTERFACES)` / `@Proxyable(TARGET_CLASS)` override the proxy type per bean.
  - Source: [Spring proxying.adoc](https://raw.githubusercontent.com/spring-projects/spring-framework/main/framework-docs/modules/ROOT/pages/core/aop/proxying.adoc)
- **Self-invocation (Spring docs).**
  - "once the call has finally reached the target object… any method calls that it may make on itself, such as `this.bar()`… are going to be invoked against the `this` reference, and not the proxy… self invocation via an explicit or implicit `this` reference will bypass the advice."
  - Remedies in order of preference: refactor so self-invocation doesn't happen ("the best, least-invasive approach"); self-injection; `AopContext.currentProxy()`, which "is highly discouraged", "totally couples your code to Spring AOP" and needs the proxy to be exposed.
  - Source: [Spring proxying.adoc](https://raw.githubusercontent.com/spring-projects/spring-framework/main/framework-docs/modules/ROOT/pages/core/aop/proxying.adoc)
- **Self-invocation demo [local].** A tracing JDK proxy around a `Ledger` whose `postTwice()` calls `this.post()` twice records **only** `["postTwice"]`. The two inner `post` calls never pass through the proxy.
- **Quarkus differs.**
  - "Quarkus supports what is known as intercepted self-invocation or just self-interception… This is a non-standard feature as CDI specification doesn't define whether self-interception should work or not." In the doc's example, a `@Transactional` method called from another method of the same bean "will trigger interception".
  - Quarkus can also handle `final` classes and methods (common in Kotlin) when `quarkus.arc.transform-unproxyable-classes` is `true` (the default).
  - "Private static methods are never intercepted."
  - Source: [Quarkus cdi-reference.adoc](https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/cdi-reference.adoc)
- **Kotlin + Spring.** "In Kotlin, classes and their members are `final` by default. This can cause issues with frameworks and libraries that rely on subclassing and runtime proxies". The `kotlin-spring` compiler plugin "makes a class and its members `open` when they have a Spring annotation" (Gradle: `kotlin("plugin.allopen")`; docs show version 2.4.21) — [Kotlin all-open plugin](https://kotlinlang.org/docs/all-open-plugin.html)
- **Spring 7 retry is proxy-based.** `@Retryable` applies to an annotated method, "or for all proxy-invoked methods in a given class hierarchy". Defaults: "at most 3 retry attempts (`maxRetries = 3`) after an initial failure, and a delay of 1 second"; "total attempts = 1 initial attempt + maxRetries attempts". It is enabled via `@EnableResilientMethods` — [Spring resilience.adoc](https://raw.githubusercontent.com/spring-projects/spring-framework/main/framework-docs/modules/ROOT/pages/core/resilience.adoc)
- **What the language makes unnecessary.** Hand-written static proxies per interface. Kotlin `by` makes a static proxy almost free when you only override one method.
- **Main pitfalls.**
  - Self-invocation in Spring.
  - Final classes and methods (Kotlin) with CGLIB.
  - Not unwrapping `InvocationTargetException`.
  - Retrying non-idempotent operations (charges) without an idempotency key. **[bg]**

##### Composite
- **Intent.** Treat individual objects and compositions uniformly in a tree.
- **Backend problem.** Pricing and fee rules ("flat 30 + 2.9% + (sub-bundle)"), permission trees, routing rule groups.
- **Java (sealed tree + exhaustive switch).** **[local]** The rule tree below evaluates to 325 for amount 10,000.
```java
sealed interface PricingRule permits Flat, Percent, AllOf { }
record Flat(long minor) implements PricingRule { }
record Percent(int bps) implements PricingRule { }
record AllOf(List<PricingRule> rules) implements PricingRule { AllOf { rules = List.copyOf(rules); } }
static long fee(PricingRule r, long amount) {
    return switch (r) {
        case Flat f -> f.minor();
        case Percent p -> amount * p.bps() / 10_000;
        case AllOf a -> a.rules().stream().mapToLong(x -> fee(x, amount)).sum();
    };
}
// fee(new AllOf(List.of(new Flat(30), new Percent(290), new AllOf(List.of(new Flat(5))))), 10_000) == 325
```
- **Kotlin.** `sealed interface PricingRule` with `data class` leaves, evaluated by `when`.
- **What the language makes unnecessary.** The `Component` abstract class with child-management methods on leaves (the GoF "transparency vs. safety" debate). Records plus sealed types give safety without casts.
- **Pitfall.** Deep recursion on huge trees, and cycles if the tree is built from mutable references. Composite trees should be immutable (`List.copyOf`).

##### Bridge
- **Intent.** Decouple an abstraction from its implementation so the two vary independently.
- **Backend problem.** Alert types (PaymentFailed, FraudSuspected) × delivery channels (SMS, Email, Slack) without N×M classes.
- **Java.** **[local]**
```java
interface Channel { String deliver(String to, String body); }                      // implementor side
record Sms() implements Channel { public String deliver(String to, String b) { return "SMS " + to + ": " + b; } }
sealed interface Alert permits PaymentFailed, FraudSuspected { Channel channel(); String raise(String to); }
record PaymentFailed(Channel channel, String paymentId) implements Alert {
    public String raise(String to) { return channel.deliver(to, "Payment " + paymentId + " failed"); }
}
```
- **Kotlin.** Identical composition: the abstraction holds a `Channel` (or a `(String, String) -> Unit` function type).
- **What the language makes unnecessary.** Little. Bridge is "composition over inheritance", which function types make lighter.
- **Pitfall.** Confusing Bridge with Adapter. Bridge is designed up front; Adapter is retrofitted. Also over-engineering when only one dimension varies.

##### Flyweight
- **Intent.** Share fine-grained immutable objects to save memory.
- **JDK: Integer cache.** `Integer.valueOf(int)` "will always cache values in the range -128 to 127, inclusive, and may cache other values outside of this range". The upper bound is tunable via `java.lang.Integer.IntegerCache.high`. The source comment notes "range [-128, 127] must be interned (JLS7 5.1.7)" — [Integer.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Integer.java)
- **Cache demo [local].** `Integer a=127,b=127` gives `a==b` true, while `128==128` was `false` under default JVM flags.
- **JDK: String interning.** "A pool of strings… is maintained privately by the class `String`… `s.intern() == t.intern()` is `true` if and only if `s.equals(t)`… All literal strings and string-valued constant expressions are interned." — [String.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/String.java)
- **JDK: Currency.** "The class is designed so that there's never more than one `Currency` instance for any given currency. Therefore, there's no public constructor." — [Currency.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/Currency.java). `Currency.getInstance("EUR") == Currency.getInstance("EUR")` holds. **[local]**
- **Java (custom canonicalizing factory).** **[local]**
```java
record MerchantCategory(String mcc, String description) {
    private static final Map<String, MerchantCategory> POOL = new ConcurrentHashMap<>();
    static MerchantCategory of(String mcc, String description) { return POOL.computeIfAbsent(mcc, k -> new MerchantCategory(k, description)); }
}
```
- **Kotlin.** Same approach, with `object` holding the pool. `enum class` and `data object` are the trivial flyweights.
- **Pitfall.** Comparing boxed numbers with `==`, which works by accident inside -128..127. Unbounded pools leak memory. Flyweights must be immutable.

---

#### BEHAVIORAL

##### Strategy
- **Intent.** Encapsulate interchangeable algorithms behind one interface.
- **Backend problem.** Fee or routing logic per payment method or PSP, retry back-off policy, serialization format.
- **JDK example.** `Comparator.comparing(Person::getLastName)` — "Accepts a function that extracts a Comparable sort key… and returns a Comparator" (since 1.8) — [Comparator.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/Comparator.java)
- **Java: refactor if/else → strategy map (open set) or exhaustive switch (closed set).** **[local]** A parity test confirms all three agree for every `Method`.
```java
@FunctionalInterface interface FeeStrategy { long fee(Payment p); }
static final Map<Method, FeeStrategy> STRATEGIES = new EnumMap<>(Map.of(
        Method.CARD,   p -> 30 + p.amountMinor() * 290 / 10_000,
        Method.SEPA,   p -> 25,
        Method.WALLET, p -> p.amountMinor() * 150 / 10_000));
static long feeSwitch(Payment p) {
    return switch (p.method()) {                      // closed set, compiler-checked
        case CARD -> 30 + p.amountMinor() * 290 / 10_000;
        case SEPA -> 25;
        case WALLET -> p.amountMinor() * 150 / 10_000;
    };
}
```
- **Kotlin.** `val feeStrategies: Map<Method, (Long) -> Long> = mapOf(Method.CARD to { a -> 30 + a * 290 / 10_000 }, …)`. Function types replace the interface. **[local]**
- **What the language makes unnecessary.** Strategy interface plus N concrete classes: a lambda or method reference is the strategy.
- **Pitfalls.**
  - With an `EnumMap`, a missing entry is a *runtime* NPE. With a `switch`, it is a *compile* error.
  - Pick the map for open/plug-in sets and the switch for closed domain sets.
  - Lambdas that capture mutable state.

##### Template Method
- **Intent.** Define an algorithm skeleton, deferring some steps to subclasses.
- **Backend problem.** Every outbound PSP call needs timing, metrics, error mapping and logging around a varying core.
- **Java: classic vs execute-around.** **[local]**
```java
static abstract class OutboundCall<T> {                     // classic: inheritance + hook
    final T execute() { long s = System.nanoTime(); try { return doCall(); } finally { record(System.nanoTime() - s); } }
    protected abstract T doCall();
    protected void record(long nanos) { }
}
static <T> T timed(String name, Map<String, Long> metrics, Supplier<T> body) {   // modern: higher-order function
    long start = System.nanoTime();
    try { return body.get(); } finally { metrics.merge(name, System.nanoTime() - start, Long::sum); }
}
```
- **Kotlin.** `inline fun <T> timed(metrics: MutableMap<String, Long>, name: String, block: () -> T): T`. Being `inline`, it adds no lambda allocation and allows non-local returns. **[local]**
- **What the language makes unnecessary.** The subclass-per-variant. Venkat Subramaniam's talk covers "Execute Around Method" as a lambda-era pattern. **[search]** (see Key Question 3)
- **Pitfall.** Inheritance-based templates couple hooks to base-class internals (the fragile base class problem). Avoid calling overridable methods from constructors. **[bg]**

##### Observer (and Flow / StateFlow / Reactor)
- **Intent.** One-to-many dependency: when a subject changes, its dependents are notified.
- **Backend problem.** Domain events ("payment captured") feeding ledger, email, analytics. Config reload listeners.
- **Java (in-process bus).** **[local]** The faulty listener does not stop the others, and closing the subscription stops delivery.
```java
static final class EventBus<E> {
    private final List<Consumer<? super E>> listeners = new CopyOnWriteArrayList<>();
    AutoCloseable subscribe(Consumer<? super E> l) { listeners.add(l); return () -> listeners.remove(l); }
    void publish(E event) { for (var l : listeners) { try { l.accept(event); } catch (RuntimeException e) { /* log */ } } }
}
```
- **JDK reactive streams.** `java.util.concurrent.Flow` is "Interrelated interfaces and static methods for establishing flow-controlled components in which Publishers produce items consumed by one or more Subscribers, each managed by a Subscription. These interfaces correspond to the reactive-streams specification." — [Flow.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/Flow.java). `SubmissionPublisher.consume(...)` with `submit(1); submit(2)` delivered `[1, 2]`. **[local]**
- **Reactor.** It describes itself as "Non-Blocking Reactive Streams Foundation for the JVM both implementing a Reactive Extensions inspired API and efficient event streaming support" — [reactor-core README](https://raw.githubusercontent.com/reactor/reactor-core/main/README.md). Observer plus backpressure: `Flux`/`Mono` are Publishers.
- **Kotlin StateFlow** — [StateFlow API](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-state-flow/):
  - "A SharedFlow that represents a read-only state with a single updatable data value… A state flow is a hot flow".
  - "State flow never completes".
  - "Updates to the value are always conflated. So a slow collector skips fast updates".
  - "Values in state flow are conflated using Any.equals comparison in a similar way to distinctUntilChanged".
  - It equals `MutableSharedFlow(replay = 1, onBufferOverflow = DROP_OLDEST)` plus `distinctUntilChanged()`.
  - "All methods of state flow are thread-safe".
  - The canonical idiom is `private val _counter = MutableStateFlow(0); val counter = _counter.asStateFlow()` with `_counter.update { it + 1 }`.
- **StateFlow conflation demo [local].** Emitting `AUTHORIZED`, `AUTHORIZED`, `CAPTURED` to a collector produced `[NEW, AUTHORIZED, CAPTURED]`; the duplicate was suppressed.
- **Kotlin `Delegates.observable`.** "The handler is called every time you assign to the property (after the assignment has been performed)". `vetoable` is called *before* the assignment — [Kotlin delegated properties](https://kotlinlang.org/docs/delegated-properties.html). It printed `NEW->AUTHORIZED`, `AUTHORIZED->CAPTURED`. **[local]**
- **What the language makes unnecessary.** Custom `Listener` interfaces (use `Consumer<E>` or `(E) -> Unit`), and hand-rolled thread-safe subject state (use `StateFlow`).
- **Pitfalls.**
  - Lapsed-listener leaks: always return an unsubscribe handle.
  - One throwing listener breaking the rest.
  - Synchronous re-entrancy.
  - Using **StateFlow for events**: equal consecutive events are dropped and slow collectors skip values. Use `SharedFlow`/`Channel` for events. This follows from the StateFlow docs above.

##### Command (and undo)
- **Intent.** Encapsulate a request as an object: queue, log, retry, undo.
- **Backend problem.** Ledger operations with compensation, job queues, an outbox of commands, saga steps.
- **Java.** **[local]** Deposit 100, Withdraw 30, failed Withdraw 1000 (not logged), undo → balance 100.
```java
sealed interface Command permits Deposit, Withdraw { void apply(Account a); void undo(Account a); }
record Deposit(long amt) implements Command { public void apply(Account a) { a.balance += amt; } public void undo(Account a) { a.balance -= amt; } }
record Withdraw(long amt) implements Command {
    public void apply(Account a) { if (a.balance < amt) throw new IllegalStateException("NSF"); a.balance -= amt; }
    public void undo(Account a) { a.balance += amt; }
}
static final class CommandLog {
    private final Deque<Command> history = new ArrayDeque<>();
    void run(Command c, Account a) { c.apply(a); history.push(c); }        // push only after success
    void undoLast(Account a) { var c = history.poll(); if (c != null) c.undo(a); }
}
```
- **Kotlin.** `sealed interface Command` with `data class` commands, and `ArrayDeque` as the history. **[local]** For fire-and-forget commands, a `() -> Unit` lambda is enough.
- **What the language makes unnecessary.** For non-undoable commands, the Command class itself: `Runnable`/`Callable`/`() -> Unit`. Records make commands serializable-friendly *data* (e.g., to an outbox).
- **Pitfall.** Recording a command before it succeeds. Undo is not the same as compensation in distributed systems: a refund is not "undo charge". **[bg]**

##### State (sealed types)
- **Intent.** Let an object change behavior when its internal state changes.
- **Backend problem.** Payment lifecycle: Created → Authorized → Captured → Refunded, with Failed from Created/Authorized.
- **Java 21 (sealed states + sealed events + nested record patterns + guards).** **[local]** The happy path ends in `Refunded`, and `Capture` on `Created` throws.
```java
sealed interface PaymentState permits Created, Authorized, Captured, Refunded, Failed { }
record Created(String id) implements PaymentState { }
record Authorized(String id, String authCode, long amount) implements PaymentState { }
record Captured(String id, long amount) implements PaymentState { }
record Refunded(String id, long amount) implements PaymentState { }
record Failed(String id, String reason) implements PaymentState { }
sealed interface PaymentEvent permits Authorize, Capture, Refund, Decline { }
record Authorize(String authCode, long amount) implements PaymentEvent { }
record Capture() implements PaymentEvent { }
record Refund(long amount) implements PaymentEvent { }
record Decline(String reason) implements PaymentEvent { }

static PaymentState transition(PaymentState s, PaymentEvent e) {
    return switch (s) {                               // NO default on the outer switch: new states break the build
        case Created c -> switch (e) {
            case Authorize(var code, var amt) when amt > 0 -> new Authorized(c.id(), code, amt);
            case Decline(var reason) -> new Failed(c.id(), reason);
            default -> throw illegal(s, e);
        };
        case Authorized a -> switch (e) {
            case Capture() -> new Captured(a.id(), a.amount());
            case Decline(var reason) -> new Failed(a.id(), reason);
            default -> throw illegal(s, e);
        };
        case Captured(var id, var amt) -> switch (e) {
            case Refund(var r) when r > 0 && r <= amt -> new Refunded(id, r);
            default -> throw illegal(s, e);
        };
        case Refunded r -> throw illegal(s, e);       // terminal
        case Failed f -> throw illegal(s, e);         // terminal
    };
}
```
- **Kotlin 2.x (guards in `when` are stable since 2.2.0).** **[local]** Compiled on 2.4.21 with no flags.
```kotlin
fun PState.on(e: PEvent): PState = when (this) {
    is PState.Created -> when (e) {
        is PEvent.Authorize if e.amount > 0 -> PState.Authorized(id, e.amount)
        is PEvent.Decline -> PState.Failed(id, e.reason)
        else -> error("$e not allowed in $this")
    }
    is PState.Authorized -> when (e) { PEvent.Capture -> PState.Captured(id, amount); is PEvent.Decline -> PState.Failed(id, e.reason); else -> error("$e not allowed in $this") }
    is PState.Captured -> when (e) { is PEvent.Refund if e.amount in 1..amount -> PState.Refunded(id, e.amount); else -> error("$e not allowed in $this") }
    is PState.Refunded, is PState.Failed -> error("terminal state $this")
}
```
- **Kotlin docs on sealed types.** "All direct subclasses of a sealed class are known at compile time. No other subclasses may appear outside the module and package within which the sealed class is defined". "Direct subclasses… must be declared in the same package". "The `when` expression, used with a sealed class, allows the Kotlin compiler to check exhaustively that all possible cases are covered… you don't need to add an `else` clause". In multiplatform `expect` code you still need `else`. The docs' own example is a `UIState` sealed class (`data object Loading`, `data class Success`, `data class Error`) — [Kotlin sealed classes](https://kotlinlang.org/docs/sealed-classes.html)
- **Exhaustiveness errors [local].**
  - Java: "error: the switch expression does not cover all possible input values".
  - Kotlin: "error: 'when' expression must be exhaustive. Add the 'is B' branch or an 'else' branch."
- **What the language makes unnecessary.** The GoF State interface with one method per event, implemented by every state class. State becomes **data** plus a pure transition function, which is easy to test, persist and log.
- **Pitfalls.**
  - `default`/`else` branches on the *state* switch silently accept new states.
  - Mutable state objects.
  - Mixing side effects (calling the PSP) into the transition function: keep it pure and return commands/effects instead. **[bg]**

##### Chain of Responsibility (servlet filters, interceptors)
- **Intent.** Pass a request along a chain of handlers, each of which may handle it, transform it, or pass it on.
- **Backend problem.** Auth, logging, rate limiting and idempotency checks around HTTP handlers. Outbound HTTP client middleware.
- **Jakarta Servlet.** "A FilterChain is an object provided by the servlet container… Filters use the FilterChain to invoke the next filter in the chain, or if the calling filter is the last filter in the chain, to invoke the resource at the end of the chain." Signatures: `FilterChain.doFilter(ServletRequest, ServletResponse)` and `Filter.doFilter(ServletRequest, ServletResponse, FilterChain)` — [FilterChain.java](https://raw.githubusercontent.com/jakartaee/servlet/master/api/src/main/java/jakarta/servlet/FilterChain.java), [Filter.java](https://raw.githubusercontent.com/jakartaee/servlet/master/api/src/main/java/jakarta/servlet/Filter.java)
- **OkHttp.** `fun interface Interceptor { fun intercept(chain: Chain): Response }`, built from a lambda: `Interceptor { chain -> chain.proceed(chain.request()) }` — [OkHttp Interceptor.kt](https://raw.githubusercontent.com/square/okhttp/master/okhttp/src/commonJvmAndroid/kotlin/okhttp3/Interceptor.kt)
- **Java (immutable OkHttp-style chain).** **[local]** `/pay` → 200 (auth header added), `/blocked` → 403 (short-circuit).
```java
interface Chain { Response proceed(Request r); }
@FunctionalInterface interface Interceptor { Response intercept(Request r, Chain next); }
record RealChain(List<Interceptor> interceptors, int index, Function<Request, Response> terminal) implements Chain {
    public Response proceed(Request r) {
        if (index == interceptors.size()) return terminal.apply(r);
        return interceptors.get(index).intercept(r, new RealChain(interceptors, index + 1, terminal));
    }
}
```
- **Kotlin (fold function types into a chain).** **[local]**
```kotlin
fun interface Interceptor { fun intercept(r: Req, next: (Req) -> Int): Int }
fun chain(interceptors: List<Interceptor>, terminal: (Req) -> Int): (Req) -> Int =
    interceptors.foldRight(terminal) { ic, next -> { r -> ic.intercept(r, next) } }
```
- **What the language makes unnecessary.** Abstract `Handler` with a `setNext()` linked list: a list of lambdas plus fold is enough.
- **Pitfalls.**
  - Order dependence (auth before logging of headers?).
  - Forgetting to call `next` (silent drop).
  - Calling `next` twice (double execution).
  - Exceptions skipping "after" logic: use try/finally.

##### Iterator (Kotlin sequences / iterator builders)
- **Intent.** Access elements sequentially without exposing representation.
- **JDK example.** "An iterator over a collection. `Iterator` takes the place of `Enumeration`… Iterators allow the caller to remove elements from the underlying collection during the iteration with well-defined semantics." — [Iterator.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/Iterator.java)
- **Backend problem.** Lazily walk a cursor-paginated PSP or REST API ("list all refunds") without loading everything.
- **Java.** **[local]** Pages `[a,b]`, `[]`, `[c]` yield `a,b,c`; the empty middle page is the classic bug. `Stream.iterate(1, i -> i < 20, i -> i * 2)` gives `[1,2,4,8,16]`.
```java
static Iterator<String> paged(Function<Integer, Page> fetch) {
    return new Iterator<>() {
        private Iterator<String> current = Collections.emptyIterator();
        private Integer cursor = 0;                               // null = no more pages
        public boolean hasNext() {
            while (!current.hasNext() && cursor != null) {        // while, not if: skip empty pages
                Page p = fetch.apply(cursor); current = p.items().iterator(); cursor = p.nextCursor();
            }
            return current.hasNext();
        }
        public String next() { if (!hasNext()) throw new NoSuchElementException(); return current.next(); }
    };
}
```
- **Kotlin sequences.** Sequence steps are lazy ("actual computing happens only when the result of the whole processing chain is requested"), and "Sequence performs all the processing steps one-by-one for every single element". `sequence { }` with `yield`/`yieldAll` "suspend the execution of `sequence()` until the next element is requested by the consumer" — [Kotlin sequences](https://kotlinlang.org/docs/sequences.html)
- **Kotlin `iterator { }`** (since 1.3) "Builds an Iterator lazily yielding values one by one". Warning: if the consumer stops early, "the remainder of the computation will not run at all. In particular, it means that `finally` blocks may be left unexecuted." — [kotlin.sequences.iterator](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.sequences/iterator.html)
```kotlin
fun pagedSequence(fetch: (Int) -> Page): Sequence<String> = sequence {
    var cursor: Int? = 0
    while (cursor != null) { val p = fetch(cursor); yieldAll(p.items); cursor = p.next }
}
```
- **What the language makes unnecessary.** Hand-written iterator state machines (Kotlin generators). Java has no generators; `Stream.iterate`/`Spliterator` cover part of the need.
- **Pitfalls.**
  - `finally`-based resource cleanup inside `iterator {}`/`sequence {}` may never run if the caller stops early (quoted above). Prefer `use {}` at the call site.
  - `ConcurrentModificationException` when modifying a collection during iteration. **[bg]**

##### Visitor (vs sealed types + exhaustive switch/when; the expression problem)
- **Intent.** Add new operations over an object structure without changing its classes (double dispatch).
- **Goetz on Visitor.** From "Pattern Matching for Java" (Gavin Bierman & Brian Goetz, Sept 2018) — [amber-docs pattern-matching-for-java.md](https://raw.githubusercontent.com/openjdk/amber-docs/master/site/design-notes/patterns/pattern-matching-for-java.md):
  - "the visitor pattern has costs… visitors rightly have a reputation for being verbose and rigid".
  - "pattern matching gets us the type-driven traversal that Visitor offers, without its verbosity, intrusiveness, or restrictions".
  - "pattern matching doesn't even have the 'stable hierarchy' requirement -- or indeed, any hierarchy requirement -- that Visitor does".
  - "It is sometimes said that many 'design patterns' are workarounds for features missing from the language. While this claim may be too facile, it is reasonably accurate in the case of Visitor -- if your language has sufficiently powerful pattern matching, the Visitor pattern is almost completely unnecessary."
  - Also: "Supporting ad-hoc polymorphism with pattern matching doesn't mean that inheritance hierarchies and virtual methods are wrong".
- **Java: classic visitor vs data-oriented switch.** **[local]** Both give 14 for `2 + 3*4`.
```java
interface ExprVisitor<R> { R visitNum(Num n); R visitAdd(Add a); R visitMul(Mul m); }
sealed interface Expr permits Num, Add, Mul { <R> R accept(ExprVisitor<R> v); }
record Num(int value) implements Expr { public <R> R accept(ExprVisitor<R> v) { return v.visitNum(this); } }
record Add(Expr l, Expr r) implements Expr { public <R> R accept(ExprVisitor<R> v) { return v.visitAdd(this); } }
record Mul(Expr l, Expr r) implements Expr { public <R> R accept(ExprVisitor<R> v) { return v.visitMul(this); } }

static int eval(Expr e) {                       // no accept(), no visitor interface
    return switch (e) {
        case Num(var v) -> v;
        case Add(var l, var r) -> eval(l) + eval(r);
        case Mul(Num(var z), var r) when z == 0 -> 0;     // nested record pattern + guard: hard with visitors
        case Mul(var l, var r) -> eval(l) * eval(r);
    };
}
```
- **Kotlin.** `sealed interface Expr` with `data class` cases and `fun eval(e: Expr): Int = when (e) { is Num -> e.v; is Add -> …; is Mul -> … }`. **[local]**
- **Expression problem (teaching framing).**
  - Sealed + switch makes adding **operations** cheap: write a new function. Adding a **case** is expensive, because every switch breaks, but the compiler lists every site.
  - Virtual methods are the reverse: new cases are cheap, new operations touch every class.
  - Visitor just encodes the "functional" side in an OO language.
  - Goetz's exhaustiveness note explains the runtime "remainder": novel subtypes from separate compilation and `null` are not matched by an exhaustive pattern set — [amber-docs exhaustiveness.md (Goetz & Bierman, 2023-05-23)](https://raw.githubusercontent.com/openjdk/amber-docs/master/site/design-notes/patterns/exhaustiveness.md). JEP 441 specifies `MatchException` for this case. **[bg]**: openjdk.org was blocked.
- **What the language makes unnecessary.** Visitor, for closed hierarchies you own.
- **When Visitor still fits.** Open hierarchies across modules, or libraries that already expose visitors (annotation processors, ASM, javac Tree API). **[bg]**
- **Pitfall.** Using `default` in a sealed switch, which throws away the main benefit.

##### Mediator
- **Intent.** Centralize complex communication so colleagues don't reference each other.
- **Backend problem.** Order or checkout coordination (inventory, payment, shipping, email reacting to each other). In distributed form this becomes a saga orchestrator or message broker. **[bg]**
- **Java.** **[local]**
```java
interface Colleague { void receive(String event); }
static final class OrderMediator {
    private final Map<String, List<Colleague>> routes = new HashMap<>();
    void on(String event, Colleague c) { routes.computeIfAbsent(event, k -> new ArrayList<>()).add(c); }
    void emit(String event) { routes.getOrDefault(event, List.of()).forEach(c -> c.receive(event)); }
}
```
- **Kotlin.** Same. A `MutableSharedFlow<Event>` is a natural coroutine-era mediator bus.
- **What the language makes unnecessary.** Colleague interfaces (lambdas).
- **Pitfall.** The mediator becoming a god object. Mediator vs Observer: Observer is one-to-many from a subject; Mediator is many-to-many through a hub.

##### Memento
- **Intent.** Capture and restore an object's internal state without violating encapsulation.
- **Backend problem.** Draft invoices or carts with undo, snapshotting aggregates (event-sourcing snapshots), rollback of in-memory config.
- **Java (records are perfect mementos).** **[local]**
```java
record DraftMemento(String text, int cursor) { }
static final class InvoiceDraft {
    private String text = ""; private int cursor = 0;
    void type(String s) { text = text + s; cursor = text.length(); }
    DraftMemento save() { return new DraftMemento(text, cursor); }
    void restore(DraftMemento m) { text = m.text(); cursor = m.cursor(); }
}
```
- **Kotlin.** `data class` snapshot. If the whole state is an immutable `data class`, the memento *is* the state: keep a `List<State>` history.
- **What the language makes unnecessary.** Most of the ceremony, once state is immutable.
- **Pitfall.** Mementos holding references to mutable internals (shallow copy again), and unbounded history growth.

---

#### CONCURRENCY PATTERNS

##### Producer-consumer
- **Intent.** Decouple producers from consumers through a (bounded) buffer.
- **Backend problem.** Webhook ingestion → workers. Outbox relay. Batched ledger writes.
- **JDK.** The `BlockingQueue` Javadoc contains a canonical "producer-consumer scenario" (`queue.put(produce())` / `consume(queue.take())`) and notes "a `BlockingQueue` can safely be used with multiple producers and multiple consumers" — [BlockingQueue.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/BlockingQueue.java)
- **Java 21 (bounded queue + sealed poison pill + virtual-thread consumers).** **[local]** 1,000 jobs and 4 consumers gave 1,000 processed.
```java
sealed interface Msg permits Job, Stop { }  record Job(int id) implements Msg { }  record Stop() implements Msg { }
BlockingQueue<Msg> q = new ArrayBlockingQueue<>(16);              // bounded = backpressure
try (var ex = Executors.newVirtualThreadPerTaskExecutor()) {
    for (int c = 0; c < consumers; c++) ex.submit(() -> { while (true) { if (q.take() instanceof Job) processed.incrementAndGet(); else return null; } });
    for (int i = 0; i < jobs; i++) q.put(new Job(i));
    for (int c = 0; c < consumers; c++) q.put(new Stop());          // one pill PER consumer
}                                                                   // close() waits for tasks
```
- **`ExecutorService` is `AutoCloseable` since JDK 19.** Its `default void close()` calls `shutdown()` and waits — [ExecutorService.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/ExecutorService.java)
- **Kotlin channels.**
  - "There is a convenient coroutine builder named `produce`… and an extension function `consumeEach`".
  - Fan-out: "Multiple coroutines may receive from the same channel, distributing work between themselves".
  - The `for (x in channel)` loop "is perfectly safe to use from multiple coroutines", whereas `consumeEach` "always consumes (cancels) the underlying channel".
  - "Unbuffered channels transfer elements when sender and receiver meet each other (aka rendezvous)". `Channel(capacity)` buffers, and send "will suspend when buffer is full".
  - Channels are "fair… first-in first-out".
  - Source: [Kotlin channels](https://kotlinlang.org/docs/channels.html)
```kotlin
val ch = Channel<Int>(capacity = 16)
val workers = List(4) { launch(Dispatchers.Default) { for (x in ch) process(x) } }   // fan-out
repeat(1_000) { ch.send(it) }
ch.close(); workers.joinAll()                                                    // close = poison pill
```
- **Pitfalls.**
  - Unbounded queues hide overload (OOM).
  - One poison pill for N consumers.
  - Swallowing `InterruptedException`.
  - In Kotlin, `consumeEach` in multiple workers cancels the channel for all of them.

##### Thread pool / worker
- **Intent.** Reuse a bounded set of worker threads for many tasks.
- **JDK.** `Executors.newFixedThreadPool(n)`. Since JDK 21, `Executors.newVirtualThreadPerTaskExecutor()` ("a new executor that creates a new virtual Thread for each task", equivalent to `newThreadPerTaskExecutor` with a virtual thread factory) — [Executors.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/Executors.java)
- **Modern guidance.** Platform-thread pools stay right for CPU-bound work. For blocking I/O, use virtual threads per task and limit concurrency with a **semaphore or bulkhead**, not pool size. The JEP 444 guidance "do not pool virtual threads" is **[bg]**: openjdk.org was blocked.
- **Resilience4j `ThreadPoolBulkhead`** "uses a bounded queue and a fixed thread pool". Defaults: `maxThreadPoolSize = availableProcessors()`, `coreThreadPoolSize = availableProcessors() - 1` (min 1), `queueCapacity = 100`, `keepAliveDuration = 20ms` — [README](https://raw.githubusercontent.com/resilience4j/resilience4j/master/README.adoc), [ThreadPoolBulkheadConfig.java](https://raw.githubusercontent.com/resilience4j/resilience4j/master/resilience4j-bulkhead/src/main/java/io/github/resilience4j/bulkhead/ThreadPoolBulkheadConfig.java)
- **Pitfalls.**
  - Unbounded work queues in `newFixedThreadPool`. **[bg]**
  - Blocking inside `ForkJoinPool.commonPool()`. CompletableFuture uses it by default; see Future/promise.

##### Active object
- **Intent.** Decouple method invocation from execution: calls return futures, and one scheduler thread owns the state.
- **Backend problem.** A per-account balance actor; a single-writer sequencer for idempotency keys.
- **Java.** **[local]** 100 concurrent deposits gave balance 100, with no locks.
```java
static final class AccountActor implements AutoCloseable {
    private final ExecutorService mailbox = Executors.newSingleThreadExecutor();
    private long balance;                                          // confined to the mailbox thread
    CompletableFuture<Long> deposit(long amt) { return CompletableFuture.supplyAsync(() -> balance += amt, mailbox); }
    CompletableFuture<Long> balance()         { return CompletableFuture.supplyAsync(() -> balance, mailbox); }
    public void close() { mailbox.close(); }
}
```
- **Kotlin.** A coroutine that owns state and reads commands from a `Channel` (the "actor" shape built from channels). **[bg]**: the kotlinx `actor {}` builder's status (obsolete API) was not verified.
- **Pitfalls.**
  - Calling a blocking `join()` from inside the actor on its own future (self-deadlock).
  - Unbounded mailbox.

##### Guarded suspension
- **Intent.** Block until a precondition (guard) holds.
- **JDK.** `Object.wait` docs: "so-called *spurious wakeup*… applications must guard against it by testing for the condition that should have caused the thread to be awakened, and continuing to wait if the condition is not satisfied" — [Object.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Object.java)
- **Java.** **[local]** Completion arrives from a virtual thread; a 20 ms timeout throws `TimeoutException`.
```java
static final class ResponseSlot<T> {
    private T value;
    synchronized void complete(T v) { value = v; notifyAll(); }
    synchronized T await(Duration timeout) throws InterruptedException, TimeoutException {
        long deadline = System.nanoTime() + timeout.toNanos();
        while (value == null) {                                    // while, never if
            long remainingMs = TimeUnit.NANOSECONDS.toMillis(deadline - System.nanoTime());
            if (remainingMs <= 0) throw new TimeoutException();
            wait(remainingMs);
        }
        return value;
    }
}
```
- **Modern alternative.** Prefer `CompletableFuture`, `CountDownLatch` or `Condition` over raw `wait`/`notify`. In Kotlin, use `CompletableDeferred`/`await` (suspends, does not block). **[bg]**
- **Pitfall.** `if` instead of `while`; `notify` instead of `notifyAll` with multiple guards; waiting without a timeout.

##### Balking
- **Intent.** If the object is not in the right state, return immediately instead of waiting.
- **Backend problem.** A scheduled settlement or reconciliation job that must not run concurrently with itself. "Save if dirty".
- **Java.** **[local]** The second concurrent call balks.
```java
static final class SettlementJob {
    private final AtomicBoolean running = new AtomicBoolean();
    boolean runIfIdle(Runnable work) {
        if (!running.compareAndSet(false, true)) return false;      // balk
        try { work.run(); return true; } finally { running.set(false); }
    }
}
```
- **Kotlin.** The same `AtomicBoolean`, or `Mutex.tryLock()` in coroutines. **[bg]**
- **Pitfall.** Check-then-act with a plain `boolean` (race). Across multiple instances or pods you need a distributed lock or lease. **[bg]**

##### Read-write lock
- **Intent.** Allow many concurrent readers or one writer.
- **JDK (`ReentrantReadWriteLock`).** "Reentrancy also allows downgrading from the write lock to a read lock… However, upgrading from a read lock to the write lock is **not** possible." The Javadoc includes `CachedData` and `RWDictionary` samples — [ReentrantReadWriteLock.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/locks/ReentrantReadWriteLock.java)
- **JDK (`StampedLock`).** It adds "Optimistic Reading" via `tryOptimisticRead()` plus `validate()` — [StampedLock.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/locks/StampedLock.java)
- **Java.** **[local]**
```java
static final class FxRateCache {
    private final Map<String, Double> rates = new HashMap<>();
    private final ReentrantReadWriteLock rw = new ReentrantReadWriteLock();
    Double get(String pair) { rw.readLock().lock(); try { return rates.get(pair); } finally { rw.readLock().unlock(); } }
    void refresh(Map<String, Double> fresh) { rw.writeLock().lock(); try { rates.clear(); rates.putAll(fresh); } finally { rw.writeLock().unlock(); } }
}
```
- **Often better.** Replace the lock with an `AtomicReference<Map>`/`volatile` holding an immutable `Map.copyOf(...)` snapshot (copy-on-write). This combines the immutable-object pattern with this one. **[bg]**
- **Pitfall.** Trying to upgrade read → write deadlocks (documented above). Write starvation.

##### Immutable object
- **Intent.** State never changes after construction, so instances are freely shareable across threads.
- **Java.** Records plus compact-constructor defensive copies. **[local]** Mutating the source list after construction doesn't affect the record.
```java
record Settlement(String batchId, List<String> paymentIds) { Settlement { paymentIds = List.copyOf(paymentIds); } }
```
- **Goetz's framing.** Records model "the state, the whole state" and are "transparent" data carriers — [amber-docs records-and-sealed-classes.md (Goetz, Feb 2019)](https://raw.githubusercontent.com/openjdk/amber-docs/master/site/design-notes/records-and-sealed-classes.md)
- **Kotlin.** `data class` with `val` and read-only `List`. Note that a read-only interface is not an immutable object: a `List` may be backed by a `MutableList`. **[bg]**
- **Pitfall.** "Records/data classes are immutable" is only *shallowly* true (see Prototype). Arrays as record components. `Collections.unmodifiableList` is a *view* (it "reads through"), not a copy.

##### Thread-per-message
- **Intent.** Handle each request or message in its own thread.
- **Java 21+.** Feasible again with virtual threads. **[local]** 10,000 tasks each sleeping 10 ms completed quickly via `newVirtualThreadPerTaskExecutor()`.
```java
try (var ex = Executors.newVirtualThreadPerTaskExecutor()) {
    for (var msg : messages) ex.submit(() -> handle(msg));
}
```
- **Kotlin.** `launch { handle(msg) }` per message in a `CoroutineScope`, which is structured concurrency by default.
- **Pitfall.** Unlimited concurrency against a downstream (DB pool, PSP rate limit). Pair it with a bulkhead or semaphore (Spring 7 `@ConcurrencyLimit`, Resilience4j `Bulkhead`).
- **Pinning.** Pinning on `synchronized` was addressed in JDK 24 (JEP 491). **[bg]**: not verified here.

##### Future / promise
- **Intent.** A placeholder for a result computed asynchronously, with composition.
- **JDK (`CompletableFuture`).** "All async methods without an explicit Executor argument, as well as those involving delays are performed using the `ForkJoinPool.commonPool()`." It has `orTimeout` and `completeOnTimeout` — [CompletableFuture.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/CompletableFuture.java)
- **Java.** **[local]** The slow branch fell back to 0.5 after 50 ms.
```java
var io = Executors.newVirtualThreadPerTaskExecutor();
var fx   = CompletableFuture.supplyAsync(() -> 1.08, io);
var risk = CompletableFuture.supplyAsync(() -> slowRiskScore(), io).completeOnTimeout(0.5, 50, TimeUnit.MILLISECONDS);
double combined = fx.thenCombine(risk, (a, b) -> a * b).join();
```
- **Structured alternative (preview through JDK 27).** `try (var scope = StructuredTaskScope.open()) { var a = scope.fork(..); var b = scope.fork(..); scope.join(); … }` (JDK 25 API with `Joiner`s) — [StructuredTaskScope.java @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/StructuredTaskScope.java). Preview status per JDK release is under Platform baseline.
- **Kotlin.** `async {}` / `Deferred.await()` within `coroutineScope {}`.
- **Pitfalls.**
  - Blocking I/O on the common pool: pass an executor.
  - Lost exceptions in fire-and-forget chains.
  - `join()` on the caller thread inside an event loop.

##### Circuit breaker (Resilience4j)
- **Intent.** Stop calling a failing dependency for a while, failing fast, then probe to see whether it has recovered.
- **Resilience4j states.** CLOSED ("operating normally"), OPEN ("has tripped and will not allow requests through"), HALF_OPEN, plus DISABLED, METRICS_ONLY and FORCED_OPEN. `CallNotPermittedException` is thrown "when the state is OPEN or FORCED_OPEN" — [CircuitBreaker.java](https://raw.githubusercontent.com/resilience4j/resilience4j/master/resilience4j-circuitbreaker/src/main/java/io/github/resilience4j/circuitbreaker/CircuitBreaker.java)
- **Resilience4j defaults** (source constants, and printed at runtime from 2.4.0 **[local]**) — [CircuitBreakerConfig.java](https://raw.githubusercontent.com/resilience4j/resilience4j/master/resilience4j-circuitbreaker/src/main/java/io/github/resilience4j/circuitbreaker/CircuitBreakerConfig.java):

  | Setting | Default |
  |---|---|
  | `failureRateThreshold` | 50 (%) |
  | `slowCallRateThreshold` | 100 (%) |
  | `slowCallDurationThreshold` | 60 s |
  | `waitDurationInOpenState` | 60 s |
  | `permittedNumberOfCallsInHalfOpenState` | 10 |
  | `minimumNumberOfCalls` | 100 |
  | `slidingWindowSize` | 100 |
  | `slidingWindowType` | `COUNT_BASED` |
  | record exceptions | all exceptions recorded |
  | ignore exceptions | none ignored |
- **Java usage (2.4.0).** **[local]** Five failures (≥ `minimumNumberOfCalls` 5) → OPEN → `CallNotPermittedException`.
```java
var cfg = CircuitBreakerConfig.custom().slidingWindowType(CircuitBreakerConfig.SlidingWindowType.COUNT_BASED)
        .slidingWindowSize(10).minimumNumberOfCalls(5).failureRateThreshold(50)
        .waitDurationInOpenState(Duration.ofSeconds(30)).build();
CircuitBreaker cb = CircuitBreaker.of("psp", cfg);
Supplier<String> guarded = CircuitBreaker.decorateSupplier(cb, pspClient::charge);
```
- **Teaching version (State + Strategy + immutability in one class).** A hand-rolled breaker using a sealed `State` (`Closed(failures)`, `Open(until)`, `HalfOpen`) in an `AtomicReference`, with an injectable `Clock`. It opens after the threshold, rejects while open, and closes after a successful half-open probe once the clock advances 31 s. Full code is in the exercise section. **[local]**
- **Pitfalls.**
  - Default `minimumNumberOfCalls = 100` means "my breaker never opens in tests".
  - Counting 4xx client errors as failures (use `ignoreExceptions`/`recordExceptions`).
  - Per-instance breakers in a fleet. **[bg]**

##### Bulkhead (Resilience4j)
- **Intent.** Isolate resources so one slow dependency can't exhaust all threads or connections.
- **Resilience4j `SemaphoreBulkhead`.** "A Bulkhead can be used to limit the amount of parallel executions… It is based on a semaphore, and unlike Hystrix, does not provide 'shadow' thread pool option." Defaults: `maxConcurrentCalls = 25`, `maxWaitDuration = 0` — [README](https://raw.githubusercontent.com/resilience4j/resilience4j/master/README.adoc), [BulkheadConfig.java](https://raw.githubusercontent.com/resilience4j/resilience4j/master/resilience4j-bulkhead/src/main/java/io/github/resilience4j/bulkhead/BulkheadConfig.java)
- **Demo [local].** `maxConcurrentCalls(2)` with two in-flight calls makes the 3rd call throw `BulkheadFullException`.
- **Spring 7.** `@ConcurrencyLimit(10)` on a method or type "specifies a concurrency limit… for all proxy-invoked methods". It is backed by `ConcurrencyThrottleInterceptor` — [Spring resilience.adoc](https://raw.githubusercontent.com/spring-projects/spring-framework/main/framework-docs/modules/ROOT/pages/core/resilience.adoc)
- **Pitfall.** Bulkhead size not aligned with the downstream connection pool. With virtual threads, the *semaphore* bulkhead is the natural limiter; thread-pool bulkheads reintroduce pools. This is an inference from the sources above.

### Inferences
- The GoF patterns sort into three groups for these languages:
  - **Absorbed by language features:** Strategy, Command, Template Method, Visitor, State, Builder (Kotlin), Prototype, Singleton.
  - **Absorbed by libraries/frameworks:** Proxy and Decorator in AOP and Resilience4j; Chain of Responsibility in filters and interceptors; Observer in Flow, Reactor and StateFlow.
  - **Still hand-designed:** Facade, Adapter, Bridge, Composite, Mediator, Flyweight.

  Lessons can teach the "absorbed" ones as "recognize the shape, then use the feature".
- The most valuable pitfall lessons are the ones where the *language feature* has a sharp edge that the GoF book never mentioned:
  - Kotlin `by` has no open recursion.
  - `data class copy()` is shallow and, in 2.4.21, still public for private constructors.
  - `default` defeats sealed exhaustiveness.
  - Record components can't be named `notify`.
  - `PUBLICATION` lazy may run the initializer twice.
  - Spring self-invocation, which Quarkus intercepts and Spring does not.
- Because Spring AOP self-invocation behaves differently from Quarkus ArC, a cross-framework exercise is a good way to show that "Proxy is an implementation detail with observable semantics".

### Gaps
- JEP pages (395, 409, 440, 441, 444, 491, 502, 505/525/533, 526/531) could not be fetched (openjdk.org blocked). JEP *numbers and statuses* above come from `PreviewFeature.java` annotations in the JDK source. Final status in JDK 21 is proven by compiling with `--release 21`. JEP prose (motivation, `MatchException` wording) is **[bg]**.
- JLS 12.4.2 (class initialization lock) and the JMM/JSR-133 justification for `volatile` in DCL were not fetched. Effective Java Items 1, 2, 3, 13, 18 and 83 are known only through the official code repo comments and directory names, not the book text.
- The Kotlin `actor {}` builder's current status, `Mutex.tryLock` and `CompletableDeferred` were not fetched.
- Whether `@ConsistentCopyVisibility` becomes the default in a specific upcoming Kotlin version was not found in the fetched docs. Only the 2.4.21 warning text is verified.
- The Resilience4j 3.0 release date: it is not on Maven Central as of the metadata check.

---

## Key Question 2 — Which patterns appear inside the JDK and well-known frameworks (real code lessons can point to)?

### Takeaway
Almost every pattern in the track has a production-grade example in the JDK or a mainstream framework, and all of the following were verified in source:
- **Proxy:** `java.lang.reflect.Proxy`, Spring AOP.
- **Decorator:** `java.io.Filter*Stream`, Resilience4j decorators.
- **Protection proxy / decorator view:** `Collections.unmodifiableList`.
- **Strategy:** `Comparator.comparing`.
- **Singleton:** `Runtime`.
- **Factory with service discovery:** `DriverManager`.
- **Iterator:** `java.util.Iterator`.
- **Flyweight:** the Integer cache, String interning, `Currency`.
- **Builder:** `HttpClient.newBuilder`, `Thread.Builder`.
- **Chain of Responsibility:** Servlet `FilterChain`, OkHttp `Interceptor`.
- **Observer / reactive:** `Flow`, `SubmissionPublisher`, Reactor, `StateFlow`.
- **Producer-consumer:** `BlockingQueue`.
- **Thread-per-message:** the virtual-thread executor.

### Cited Findings
| Pattern | Real code | Evidence |
|---|---|---|
| Proxy | `java.lang.reflect.Proxy.newProxyInstance(loader, interfaces, handler)`; proxy classes are final, extend `Proxy`; their names are unspecified, but names starting with `$Proxy` are reserved for them | [Proxy.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/reflect/Proxy.java) |
| Proxy (AOP) | Spring: JDK proxy when the target implements at least one interface, else a CGLIB subclass; self-invocation bypasses advice; `@Proxyable` (7.0) | [Spring proxying.adoc](https://raw.githubusercontent.com/spring-projects/spring-framework/main/framework-docs/modules/ROOT/pages/core/aop/proxying.adoc) |
| Proxy (CDI) | Quarkus ArC: self-interception supported (non-standard); final classes transformable | [Quarkus cdi-reference.adoc](https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/cdi-reference.adoc) |
| Proxy (retry/limit) | Spring 7 `@Retryable`, `@ConcurrencyLimit` on "proxy-invoked methods" | [Spring resilience.adoc](https://raw.githubusercontent.com/spring-projects/spring-framework/main/framework-docs/modules/ROOT/pages/core/resilience.adoc) |
| Protection proxy / decorator view | `Collections.unmodifiableList`: "Query operations on the returned list 'read through' to the specified list, and attempts to modify the returned list… result in an `UnsupportedOperationException`"; `@implNote` "may return its argument if the argument is already unmodifiable" | [Collections.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/Collections.java) |
| Decorator | `FilterInputStream` "wraps some other input stream… possibly transforming the data along the way or providing additional functionality" | [FilterInputStream.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/io/FilterInputStream.java) |
| Decorator (resilience) | Resilience4j: "higher-order functions (decorators)… You can stack more than one decorator"; `CircuitBreaker.decorateSupplier`, `Retry.decorateSupplier`, `Bulkhead.decorateSupplier` | [Resilience4j README](https://raw.githubusercontent.com/resilience4j/resilience4j/master/README.adoc) |
| Strategy | `Comparator.comparing(Person::getLastName)` (since 1.8) | [Comparator.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/Comparator.java) |
| Singleton | `Runtime.getRuntime()`: "Every Java application has a single instance of class `Runtime`" | [Runtime.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Runtime.java) |
| Factory + service discovery | `DriverManager.getConnection(url)`; drivers loaded via `ServiceLoader` | [DriverManager.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.sql/share/classes/java/sql/DriverManager.java) |
| Builder | `HttpClient.newBuilder()`; `Thread.ofVirtual()` / `Thread.ofPlatform()` returning the `sealed interface Builder` | [HttpClient.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.net.http/share/classes/java/net/http/HttpClient.java), [Thread.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Thread.java) |
| Iterator | `java.util.Iterator` "takes the place of `Enumeration`" | [Iterator.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/Iterator.java) |
| Iterator (Kotlin) | `sequence {}`, `iterator {}` builders | [sequences](https://kotlinlang.org/docs/sequences.html), [iterator()](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.sequences/iterator.html) |
| Flyweight | `Integer.valueOf` cache -128..127 (tunable high bound); `String.intern()`; `Currency` "never more than one instance" | [Integer.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Integer.java), [String.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/String.java), [Currency.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/Currency.java) |
| Prototype (anti-example) | `Cloneable` has no `clone` method; `Object.clone` is shallow | [Cloneable.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Cloneable.java), [Object.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Object.java) |
| Chain of Responsibility | Jakarta `Filter.doFilter(req, res, chain)` / `FilterChain.doFilter(req, res)` | [FilterChain.java](https://raw.githubusercontent.com/jakartaee/servlet/master/api/src/main/java/jakarta/servlet/FilterChain.java), [Filter.java](https://raw.githubusercontent.com/jakartaee/servlet/master/api/src/main/java/jakarta/servlet/Filter.java) |
| Chain of Responsibility | OkHttp `fun interface Interceptor { fun intercept(chain: Chain): Response }` | [Interceptor.kt](https://raw.githubusercontent.com/square/okhttp/master/okhttp/src/commonJvmAndroid/kotlin/okhttp3/Interceptor.kt) |
| Observer / reactive | `java.util.concurrent.Flow` (reactive-streams interfaces); Reactor; Kotlin `StateFlow` | [Flow.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/Flow.java), [reactor-core README](https://raw.githubusercontent.com/reactor/reactor-core/main/README.md), [StateFlow](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-state-flow/) |
| Producer-consumer | `BlockingQueue` Javadoc example | [BlockingQueue.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/BlockingQueue.java) |
| Thread pool / thread-per-message | `Executors.newFixedThreadPool`, `newVirtualThreadPerTaskExecutor()` (since 21); `ExecutorService.close()` (since 19) | [Executors.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/Executors.java), [ExecutorService.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/ExecutorService.java) |
| Read-write lock | `ReentrantReadWriteLock` (no upgrade), `StampedLock` (optimistic reads) | [RRWL.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/locks/ReentrantReadWriteLock.java), [StampedLock.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/locks/StampedLock.java) |
| Future/promise | `CompletableFuture` (commonPool default, `orTimeout`, `completeOnTimeout`); `StructuredTaskScope` (preview) | [CompletableFuture.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/CompletableFuture.java), [StructuredTaskScope.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/StructuredTaskScope.java) |
| Lazy singleton / holder | `StableValue` (JDK 25 preview) → `LazyConstant` (JDK 26-27 preview) | [StableValue.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/StableValue.java), [LazyConstant.java](https://raw.githubusercontent.com/openjdk/jdk/master/src/java.base/share/classes/java/lang/LazyConstant.java) |
| Circuit breaker / bulkhead | Resilience4j `CircuitBreaker`, `Bulkhead`, `ThreadPoolBulkhead` | [CircuitBreaker.java](https://raw.githubusercontent.com/resilience4j/resilience4j/master/resilience4j-circuitbreaker/src/main/java/io/github/resilience4j/circuitbreaker/CircuitBreaker.java), [BulkheadConfig.java](https://raw.githubusercontent.com/resilience4j/resilience4j/master/resilience4j-bulkhead/src/main/java/io/github/resilience4j/bulkhead/BulkheadConfig.java) |
| Decorator (Kotlin) | class delegation `by` | [Kotlin delegation](https://kotlinlang.org/docs/delegation.html) |
| Builder (Kotlin) | Ktor routing and HTML DSLs are cited as builder use cases | [Kotlin type-safe builders](https://kotlinlang.org/docs/type-safe-builders.html) |

### Inferences
- `Collections.unmodifiableList` can be presented as **both** Proxy and Decorator. Structurally it is a same-interface wrapper; by intent it is access control. That makes it an ideal "same structure, different intent" discussion piece.
- For "point to real code" slides, the GitHub `openjdk/jdk` tag `jdk-25-ga` is a stable permalink base (JDK 25 is an LTS release **[bg]**). The `master` branch moves.

### Gaps
- Spring's `TransactionInterceptor`/`@Transactional` docs, `JdbcTemplate` (Template Method and callbacks), and `RestClient.builder()` were not fetched. Their pattern use is **[bg]** only.
- Reactor's own reference docs (projectreactor.io) were not reachable. Only the README was read.

---

## Key Question 3 — What do authoritative modern sources say about which GoF patterns are obsolete or changed in modern Java/Kotlin?

### Takeaway
The strongest primary-source statement is Brian Goetz's:
- Visitor becomes "almost completely unnecessary" with sufficiently powerful pattern matching.
- Records plus sealed types give Java algebraic data types ("records offer us a compact expression for product types, and sealing offers us the other half, sum types").
- Virtual methods are *not* wrong; pattern matching is an additional tool for "data-driven polymorphism".

Kotlin's docs present delegation as "a good alternative to implementation inheritance" with "zero boilerplate", and DSL builders as the idiomatic replacement for hand-written builders. Venkat Subramaniam's long-running talk reworks Strategy, Decorator, (virtual) Proxy and Execute-Around with lambdas; this was seen only in search snippets.

### Cited Findings
- **Goetz on Visitor.** "if your language has sufficiently powerful pattern matching, the Visitor pattern is almost completely unnecessary". The claim that many patterns are workarounds for missing language features is called "too facile" in general, "reasonably accurate in the case of Visitor" — [Pattern Matching for Java (Bierman & Goetz, 2018)](https://raw.githubusercontent.com/openjdk/amber-docs/master/site/design-notes/patterns/pattern-matching-for-java.md)
- **Pattern matching vs. inheritance.** "Pattern matching allows you to achieve the same result without the machinery of Visitors… resulting in cleaner, simpler, more transparent, and more flexible code". It also "doesn't mean that inheritance hierarchies and virtual methods are wrong… sometimes an operation is an ideal candidate for including in the hierarchy" — [same](https://raw.githubusercontent.com/openjdk/amber-docs/master/site/design-notes/patterns/pattern-matching-for-java.md)
- **Records and sealing as ADTs.** "records offer us a compact expression for product types, and sealing offers us the other half, sum types" (the same document refers to "algebraic data types") — [same](https://raw.githubusercontent.com/openjdk/amber-docs/master/site/design-notes/patterns/pattern-matching-for-java.md)
- **Records as transparent data.** Records/data classes model "the state, the whole state" and are "transparent". The boilerplate is "just a symptom of a deeper problem" — [Data Classes and Sealed Types for Java (Goetz, Feb 2019)](https://raw.githubusercontent.com/openjdk/amber-docs/master/site/design-notes/records-and-sealed-classes.md)
- **Exhaustiveness has a runtime "remainder".** For sealed types the remainder includes `null` and subtypes unknown at compile time. That is why exhaustive switches still need a runtime safety net — [Exhaustiveness, Unconditionality, and Remainder (Goetz & Bierman, 2023-05-23)](https://raw.githubusercontent.com/openjdk/amber-docs/master/site/design-notes/patterns/exhaustiveness.md)
- **Goetz's InfoQ article.** "Data Oriented Programming in Java" appeared on InfoQ in **June 2022** — **[search]** (InfoQ blocked; snippet from a conference listing found via search, URL given as [infoq.com/articles/data-oriented-programming-java](https://www.infoq.com/articles/data-oriented-programming-java/)). Secondary summaries list the principles as roughly:
  - "Model the data, the whole data, and nothing but the data"
  - "Data is immutable"
  - "Validate at the boundary"
  - "Make illegal states unrepresentable"

  An Inside Java post (2024-06-26) proposes a "v1.1" adding "separate operations from data" — **[search]** [inside.java/2024/06/26/dop-v1-1-why-update](https://inside.java/2024/06/26/dop-v1-1-why-update/). **Re-verify exact wording before quoting.**
- **Kotlin on delegation.** "The Delegation pattern has proven to be a good alternative to implementation inheritance, and Kotlin supports it natively requiring zero boilerplate code." — [Kotlin delegation](https://kotlinlang.org/docs/delegation.html)
- **Kotlin on builders.** "Type-safe builders allow creating Kotlin-based domain-specific languages (DSLs) suitable for building complex hierarchical data structures in a semi-declarative way." — [Kotlin type-safe builders](https://kotlinlang.org/docs/type-safe-builders.html)
- **Kotlin on singletons.** The language has singletons built in: "objects allow you to define a class and create an instance of it in a single step" — [Kotlin object declarations](https://kotlinlang.org/docs/object-declarations.html)
- **Venkat Subramaniam.** "Design Patterns in the Light of Lambda Expressions" has been delivered at Devoxx, NFJS and JUGs. The Devoxx recording (~53 min) covers Strategy, Lazy Evaluation, Virtual Proxy, Decorator, Composed Method and Execute Around Method — **[search]** ([Class Central listing](https://classcentral.com/course/youtube-design-patterns-in-the-light-of-lambda-expressions-venkat-subramaniam-agile-developer-inc-196000), [DevNexus 2015](https://devnexus.com/archive/devnexus2015/presentations/4440.html)).
- **Venkat at Devoxx BE 2022.** An InfoQ news item reported a session implementing Iterator, Strategy, Decorator and Factory Method in modern Java, with Subramaniam's view that design patterns are "phenomenal as a communication tool, but a disaster as a software design tool" — **[search]** ([InfoQ news 2022/10](https://www.infoq.com/news/2022/10/modern-java-design-patterns)). The quote is from a search summary; **verify before using.**
- **Resilience4j's own design statement.** It is "designed for functional programming" and decorates "any functional interface, lambda expression or method reference". In other words, Decorator implemented as higher-order functions — [Resilience4j README](https://raw.githubusercontent.com/resilience4j/resilience4j/master/README.adoc)

### Inferences
- A defensible one-line position for the track: "Patterns are vocabulary. Modern Java and Kotlin turn several of them into language features. Learn the intent so you recognize the feature, and so you know when the feature is *not* enough (open hierarchies, cross-cutting concerns, distributed coordination)."
- "Obsolete" is too strong for State and Strategy. The *intent* remains; only the *implementation* changes (data plus functions instead of class hierarchies). Visitor is the only GoF pattern a primary source calls "almost completely unnecessary", and only for languages with strong pattern matching.

### Gaps
- No primary Venkat source (slides or video) was reachable. JetBrains blog posts on Kotlin idioms for patterns were not searched. Peter Norvig's 1996 "Design Patterns in Dynamic Languages" (the classic "16 of 23 patterns are invisible or simpler" claim) was not verified this session.
- The InfoQ DOP article text was not readable (domain blocked), so its principles are secondhand.

---

## Key Question 4 — Good hands-on exercises with tests

### Takeaway
Every exercise below was prototyped and its expected outputs were produced by running the code in this session. Give learners the "before" code and a failing test suite, and ask for a refactor that keeps the tests green and adds the new ones.

### Cited Findings (expected outcomes are [local] unless noted)
1. **If-else payment router → Strategy (map) and → exhaustive switch.**
   - Starter: `feeIfElse(Payment)` with CARD = 30 + 2.9%, SEPA = 25 flat, WALLET = 1.5%.
   - Tests: a parity property over every enum value (`feeIfElse == strategyMap == switch`), plus fixed points for 10,000 minor units: CARD → **320**, SEPA → **25**, WALLET → **150**.
   - Twist: add `Method.CRYPTO`. The switch version fails to compile; the map version fails at runtime (NPE or `getValue` exception). Learners must explain which they prefer and why.
2. **Fee calculator Decorator chain.**
   - `percent(290).plusFixed(30).crossBorder("DE",100).cappedAt(500)`.
   - Tests: domestic 10,000 → **320**; cross-border 10,000 → **420**; cross-border 100,000 → **500** (capped).
   - Order test: moving `cappedAt` before `crossBorder` gives **1,500**.
   - Kotlin variant: implement `Capped` with `: FeeCalculator by inner`, and the others as extension functions.
3. **Retrying Proxy.**
   - Build `retrying(Class<T>, T, maxAttempts, Predicate<Throwable>)` with `java.lang.reflect.Proxy`.
   - Tests: a flaky target fails twice → success with exactly **3** target calls; a non-retryable exception propagates **once** and unwrapped (assert the type, not `InvocationTargetException`/`UndeclaredThrowableException`); `Proxy.isProxyClass(proxy.getClass())` is true.
   - Self-invocation test: a tracing proxy around an object whose `postTwice()` calls `this.post()` records only `["postTwice"]`.
   - Stretch: compare with Spring 7 `@Retryable` (`maxRetries = 3` means 4 total attempts — [Spring resilience.adoc](https://raw.githubusercontent.com/spring-projects/spring-framework/main/framework-docs/modules/ROOT/pages/core/resilience.adoc)), and show that a same-class call bypasses it in Spring but not in Quarkus ([Quarkus cdi-reference](https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/cdi-reference.adoc)).
4. **Sealed-class State machine for the payment lifecycle.**
   - States `Created/Authorized/Captured/Refunded/Failed`; events `Authorize/Capture/Refund/Decline`.
   - Tests: `Created→Authorize(5000)→Capture→Refund(2000)` ends in `Refunded(p1, 2000)`; `Created + Capture` throws `IllegalStateException`; `Refund(r)` with `r > captured` throws; terminal states reject everything.
   - Twist: add `Disputed`. With no `default` in the outer switch, javac reports "the switch expression does not cover all possible input values", and kotlinc reports "'when' expression must be exhaustive". The compiler errors *are* the to-do list.
   - Kotlin version uses guards (`is Refund if e.amount in 1..amount`), stable since 2.2.0 ([whatsnew22](https://kotlinlang.org/docs/whatsnew22.html)).
5. **Visitor → sealed refactor (expression problem lab).**
   - Given a classic `ExprVisitor` with `EvalVisitor`, add (a) a new *operation* `PrettyPrint` and (b) a new *case* `Neg`, in both styles. Count the files touched each way.
   - Test: `eval(Add(Num(2), Mul(Num(3), Num(4)))) == 14` in both.
   - Add a nested-pattern optimization `Mul(Num(0), _) -> 0` that is trivial with record patterns and awkward with visitors.
6. **Kotlin delegation trap.**
   - Implement `CountingMap : MutableMap by inner` overriding `put`. Ask learners to *predict* `puts` after `put("a",1); putAll(mapOf("b" to 2,"c" to 3))`. Answer: **1**, with `size == 3`.
   - Then compare with Java `extends HashMap` (inheritance version, EJ Item 18 territory **[bg]**) and discuss fragile base class vs. no open recursion.
7. **Builder vs named args vs DSL.**
   - Build `HttpRequestSpec` three ways: a Java record + builder with a compact-constructor invariant (`maxRetries >= 0`, headers immutable), Kotlin named/default args + `copy`, and a `paymentRequest { lineItems { item(..) } }` DSL with `@DslMarker`.
   - Negative compile test: `amount = 1` inside `lineItems {}` must not compile.
   - Bonus: the `data class Email private constructor` + `copy()` hole, and the `@ConsistentCopyVisibility` fix.
8. **Prototype trap.** A test that fails on `record Cart(String id, List<String> items)` (mutating a "copy" mutates the original), then passes after `List.copyOf` in the compact constructor. Kotlin: the same with `MutableList` vs `List` plus `copy(items = items + x)`.
9. **Observer with StateFlow vs SharedFlow.** Emit `AUTHORIZED, AUTHORIZED, CAPTURED` into `MutableStateFlow("NEW")`. A collector sees `[NEW, AUTHORIZED, CAPTURED]` (the duplicate is conflated). Ask learners to switch to `MutableSharedFlow(replay=0)` so each *event* is delivered, and explain why payment *events* shouldn't use `StateFlow` ([StateFlow docs](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-state-flow/)).
10. **Producer-consumer with poison pills.**
    - Java: `ArrayBlockingQueue(16)`, 4 virtual-thread consumers, 1,000 jobs → exactly **1,000** processed, and the executor `close()` returns (no hang). Bug to plant: one `Stop` pill for 4 consumers makes the test hang, so use a timeout assertion.
    - Kotlin: `Channel(16)` + 4 `for (x in ch)` workers + `ch.close()`. Bug to plant: `consumeEach` in each worker.
11. **Circuit breaker with a fake clock.**
    - Hand-roll a breaker with a sealed `State` in an `AtomicReference` and an injectable `Clock`. Tests: 3 failures → `Open`; a call while open → rejected; advance the clock 31 s → the half-open probe succeeds → `Closed`; a failure in half-open → `Open` again.
    - Then port to Resilience4j: with `minimumNumberOfCalls(5)`, `slidingWindowSize(10)`, `failureRateThreshold(50)`, 5 failures → `State.OPEN` → `CallNotPermittedException`.
    - Discussion: why the default `minimumNumberOfCalls = 100` makes naive tests never open ([CircuitBreakerConfig.java](https://raw.githubusercontent.com/resilience4j/resilience4j/master/resilience4j-circuitbreaker/src/main/java/io/github/resilience4j/circuitbreaker/CircuitBreakerConfig.java)).
12. **Bulkhead.** `Bulkhead` with `maxConcurrentCalls(2)`, `maxWaitDuration(ZERO)`: two calls parked on a latch, and the 3rd call throws **`BulkheadFullException`**. Compare with Spring 7 `@ConcurrencyLimit(2)`.
13. **Guarded suspension and balking.**
    - `ResponseSlot.await(Duration)` returns the value when completed from another thread, and throws `TimeoutException` after 20 ms otherwise.
    - `SettlementJob.runIfIdle` returns `false` for an overlapping call.
    - Code review: spot `if (value == null) wait()` (spurious wakeups; [Object.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Object.java)).

Reference: the hand-rolled breaker used in exercise 11 (compiled and tested **[local]**):
```java
static final class MiniBreaker {
    sealed interface State permits Closed, Open, HalfOpen { }
    record Closed(int consecutiveFailures) implements State { }
    record Open(Instant until) implements State { }
    record HalfOpen() implements State { }
    private final AtomicReference<State> state = new AtomicReference<>(new Closed(0));
    private final int threshold; private final Duration openFor; private final Clock clock;
    MiniBreaker(int threshold, Duration openFor, Clock clock) { this.threshold = threshold; this.openFor = openFor; this.clock = clock; }
    <T> T call(Supplier<T> op) {
        State s = state.updateAndGet(cur -> cur instanceof Open(var until) && !clock.instant().isBefore(until) ? new HalfOpen() : cur);
        if (s instanceof Open) throw new IllegalStateException("circuit open");
        try { T r = op.get(); state.set(new Closed(0)); return r; }
        catch (RuntimeException e) {
            state.updateAndGet(cur -> switch (cur) {
                case HalfOpen h -> new Open(clock.instant().plus(openFor));
                case Closed(var n) when n + 1 >= threshold -> new Open(clock.instant().plus(openFor));
                case Closed(var n) -> new Closed(n + 1);
                case Open o -> o;
            });
            throw e;
        }
    }
}
```

### Inferences
- Exercises 4, 5 and 11 reinforce each other: the breaker *is* a State machine. Teach State/Visitor before circuit breaker so the concurrency lesson can reuse sealed types.
- Prefer injectable `Clock`s and latches over `Thread.sleep` in tests. The breaker and bulkhead tests above are deterministic because of this.
- Note that the simple breaker lets multiple threads probe concurrently in half-open, unlike Resilience4j's `permittedNumberOfCallsInHalfOpenState`. That is a good "why use the library" discussion point.

### Gaps
- No existing public exercise repositories (for example refactoring.guru's Java examples) were evaluated, because refactoring.guru was blocked. JUnit/Kotest scaffolding was not produced; the tests here are plain assertions in `main`.

---

## Verified URLs
Each entry below was fetched successfully in this session (WebFetch or `curl` returning HTTP 200). Search-result-only URLs are **not** listed here; they are marked **[search]** above.

**kotlinlang.org (WebFetch)**
- https://kotlinlang.org/docs/delegation.html — class delegation `by`, the override caveat, "alternative to implementation inheritance".
- https://kotlinlang.org/docs/type-safe-builders.html — lambdas with receiver, the HTML builder, `@DslMarker`, `this@html`.
- https://kotlinlang.org/docs/object-declarations.html — `object` singletons (thread-safe, lazy), companion objects (static-initializer semantics, `@JvmStatic`), `data object`, object expressions.
- https://kotlinlang.org/docs/delegated-properties.html — `lazy` (default synchronized; PUBLICATION, NONE), `observable`/`vetoable`, map delegation, `provideDelegate`.
- https://kotlinlang.org/docs/data-classes.html — `copy()` is shallow, generated members come from primary-constructor properties only.
- https://kotlinlang.org/docs/sequences.html — lazy, element-by-element evaluation; the `sequence {}` builder; `generateSequence`.
- https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.sequences/iterator.html — the `iterator {}` builder; skipped `finally` caveat.
- https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-lazy-thread-safety-mode/ — verbatim SYNCHRONIZED/PUBLICATION/NONE semantics.
- https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-state-flow/ — StateFlow: hot, conflated, equality-based, never completes, thread-safe.
- https://kotlinlang.org/docs/sealed-classes.html — sealed rules, exhaustive `when`, the UIState example.
- https://kotlinlang.org/docs/all-open-plugin.html — final-by-default vs proxies; `kotlin-spring`/all-open.
- https://kotlinlang.org/docs/whatsnew22.html — Kotlin 2.2.0 (June 23, 2025): when-guards stable; context parameters in preview.
- https://kotlinlang.org/docs/channels.html — `produce`, pipelines, fan-out/fan-in, buffered channels, fairness, tickers.

**OpenJDK source (raw.githubusercontent.com, curl)**
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/reflect/Proxy.java — dynamic proxy spec.
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Integer.java — `IntegerCache`, `valueOf` caching contract.
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/Collections.java — `unmodifiableList` "unmodifiable view".
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Runtime.java — `Runtime` singleton.
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/String.java — `intern()` pool.
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Cloneable.java — Cloneable has no `clone` method.
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Object.java — `clone()` is shallow; spurious wakeups in `wait`.
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/Comparator.java — `Comparator.comparing`.
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/Iterator.java — Iterator contract.
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/Currency.java — one instance per currency.
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/io/FilterInputStream.java — decorator base class.
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.sql/share/classes/java/sql/DriverManager.java — JDBC driver factory via ServiceLoader.
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.net.http/share/classes/java/net/http/HttpClient.java — `newBuilder()`.
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Thread.java — `ofVirtual()`/`ofPlatform()`, sealed `Builder`.
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/BlockingQueue.java — producer-consumer example.
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/Executors.java — `newVirtualThreadPerTaskExecutor` (since 21).
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/ExecutorService.java — `close()` (since 19).
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/CompletableFuture.java — commonPool default; `orTimeout`/`completeOnTimeout`.
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/Flow.java — reactive-streams interfaces.
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/locks/ReentrantReadWriteLock.java — no read→write upgrade; downgrading allowed.
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/locks/StampedLock.java — optimistic reads.
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/StableValue.java — JDK 25 preview StableValue.
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/StructuredTaskScope.java — JDK 25 preview API (`open()`, `fork`, `join`).
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/ScopedValue.java — final in 25.
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/jdk/internal/javac/PreviewFeature.java — JDK 25 preview list (JEP 502, 505, 470).
- https://raw.githubusercontent.com/openjdk/jdk/jdk-26-ga/src/java.base/share/classes/jdk/internal/javac/PreviewFeature.java — JDK 26 preview list (JEP 525, 526, 524).
- https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/java.base/share/classes/jdk/internal/javac/PreviewFeature.java — JDK 27 preview list (JEP 533, 531, 538).
- https://raw.githubusercontent.com/openjdk/jdk/master/src/java.base/share/classes/jdk/internal/javac/PreviewFeature.java — master (JDK 28) preview list (JEP 539, 401, 531).
- https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/make/conf/version-numbers.conf — JDK 27 GA date 2026-09-15.
- https://raw.githubusercontent.com/openjdk/jdk/master/make/conf/version-numbers.conf — master = JDK 28, date 2027-03-23.
- https://raw.githubusercontent.com/openjdk/jdk/master/src/java.base/share/classes/java/lang/LazyConstant.java — LazyConstant semantics.
- https://raw.githubusercontent.com/openjdk/jdk/jdk-26-ga/src/java.base/share/classes/java/lang/LazyConstant.java and https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/java.base/share/classes/java/lang/LazyConstant.java — `@since 26`, still preview.
- https://raw.githubusercontent.com/openjdk/jdk/master/src/java.base/share/classes/java/util/concurrent/StructuredTaskScope.java — `@since 28`, no preview annotation.
- https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/java.base/share/classes/java/util/concurrent/StructuredTaskScope.java — JDK 27 API shape (`open()`, `Joiner`).

**Brian Goetz / Amber design notes (raw GitHub)**
- https://raw.githubusercontent.com/openjdk/amber-docs/master/site/design-notes/patterns/pattern-matching-for-java.md — Visitor critique, "almost completely unnecessary", ADTs.
- https://raw.githubusercontent.com/openjdk/amber-docs/master/site/design-notes/records-and-sealed-classes.md — records as transparent carriers of "the state, the whole state".
- https://raw.githubusercontent.com/openjdk/amber-docs/master/site/design-notes/patterns/exhaustiveness.md — exhaustiveness and remainder (null, novel subtypes).
- https://raw.githubusercontent.com/openjdk/amber-docs/master/site/design-notes/patterns/pattern-match-semantics.md — pattern semantics (Aug 2020); fetched, not quoted.

**Effective Java 3e official code (raw GitHub)**
- https://raw.githubusercontent.com/jbloch/effective-java-3e-source-code/master/src/effectivejava/chapter2/item3/enumtype/Elvis.java — enum singleton, "the preferred approach".
- https://raw.githubusercontent.com/jbloch/effective-java-3e-source-code/master/src/effectivejava/chapter2/item3/field/Elvis.java — public-final-field singleton.
- https://raw.githubusercontent.com/jbloch/effective-java-3e-source-code/master/src/effectivejava/chapter2/item3/staticfactory/Elvis.java — static-factory singleton.
- https://raw.githubusercontent.com/jbloch/effective-java-3e-source-code/master/src/effectivejava/chapter2/item2/builder/NutritionFacts.java — Builder.
- https://raw.githubusercontent.com/jbloch/effective-java-3e-source-code/master/src/effectivejava/chapter2/item2/hierarchicalbuilder/Pizza.java — hierarchical builder with simulated self-type.
- https://raw.githubusercontent.com/jbloch/effective-java-3e-source-code/master/src/effectivejava/chapter3/item13/Stack.java — Cloneable Stack (deep-copying the array).
- https://raw.githubusercontent.com/jbloch/effective-java-3e-source-code/master/src/effectivejava/chapter3/item13/PhoneNumber.java — clone example; fetched, not quoted.

**Spring / Quarkus / Jakarta / OkHttp / Reactor (raw GitHub)**
- https://raw.githubusercontent.com/spring-projects/spring-framework/main/framework-docs/modules/ROOT/pages/core/aop/proxying.adoc — JDK vs CGLIB proxies, final/private limits, self-invocation, `@Proxyable` (7.0).
- https://raw.githubusercontent.com/spring-projects/spring-framework/main/framework-docs/modules/ROOT/pages/core/resilience.adoc — Spring 7 `@Retryable`, `@ConcurrencyLimit`, `@EnableResilientMethods`.
- https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/cdi-reference.adoc — Quarkus self-interception, final-class transformation, static method interception.
- https://raw.githubusercontent.com/jakartaee/servlet/master/api/src/main/java/jakarta/servlet/FilterChain.java — FilterChain contract.
- https://raw.githubusercontent.com/jakartaee/servlet/master/api/src/main/java/jakarta/servlet/Filter.java — `Filter.doFilter(req, res, chain)`.
- https://raw.githubusercontent.com/square/okhttp/master/okhttp/src/commonJvmAndroid/kotlin/okhttp3/Interceptor.kt — OkHttp `fun interface Interceptor`.
- https://raw.githubusercontent.com/reactor/reactor-core/main/README.md — Reactor self-description.

**Resilience4j (raw GitHub + Maven Central)**
- https://raw.githubusercontent.com/resilience4j/resilience4j/master/README.adoc — decorators, "Resilience4j 3 requires Java 21", virtual-thread option, bulkhead examples.
- https://raw.githubusercontent.com/resilience4j/resilience4j/master/resilience4j-circuitbreaker/src/main/java/io/github/resilience4j/circuitbreaker/CircuitBreakerConfig.java — default values.
- https://raw.githubusercontent.com/resilience4j/resilience4j/master/resilience4j-circuitbreaker/src/main/java/io/github/resilience4j/circuitbreaker/CircuitBreaker.java — the six states, `decorateSupplier`, `CallNotPermittedException`.
- https://raw.githubusercontent.com/resilience4j/resilience4j/master/resilience4j-bulkhead/src/main/java/io/github/resilience4j/bulkhead/BulkheadConfig.java — semaphore bulkhead defaults.
- https://raw.githubusercontent.com/resilience4j/resilience4j/master/resilience4j-bulkhead/src/main/java/io/github/resilience4j/bulkhead/ThreadPoolBulkheadConfig.java — thread-pool bulkhead defaults.
- https://repo1.maven.org/maven2/io/github/resilience4j/resilience4j-circuitbreaker/maven-metadata.xml — latest release 2.4.0.
- https://repo1.maven.org/maven2/org/jetbrains/kotlin/kotlin-stdlib/maven-metadata.xml — Kotlin 2.4.21 latest stable; 2.5.0-Beta2.
- https://repo1.maven.org/maven2/org/jetbrains/kotlinx/kotlinx-coroutines-core/maven-metadata.xml — coroutines 1.11.0.

**Toolchain downloads used for compile verification**
- https://github.com/JetBrains/kotlin/releases/download/v2.4.21/kotlin-compiler-2.4.21.zip — kotlinc 2.4.21.
- Maven Central jars: resilience4j-circuitbreaker/-core/-bulkhead 2.4.0, slf4j-api 2.0.17, kotlinx-coroutines-core-jvm 1.11.0 (under https://repo1.maven.org/maven2/).

**Attempted but blocked (NOT verified):** openjdk.org/jeps/409, /440, /441; infoq.com (Goetz DOP); docs.spring.io; resilience4j.readme.io; refactoring.guru; quarkus.io; docs.oracle.com; inside.java; dev.java.

---

## Teaching notes

### Suggested grouping for the 11 lessons (and why)
1. **Singleton + Immutable Object + lazy init.**
   - Java: enum, holder, DCL/volatile, `LazyConstant` preview. Kotlin: `object`, companion, `lazy` modes.
   - Why together: all three are about *safe publication* and initialization. They bridge into the concurrency lessons.
2. **Factory Method + Abstract Factory** (static factories, `DriverManager`/`ServiceLoader`, function-typed factories).
   - Why together: same intent at two granularities. Sealed products make factories compiler-checked.
3. **Builder + Prototype** (records, compact constructors, withers, named/default args, `copy()` traps, DSLs with `@DslMarker`).
   - Why together: both are about *constructing* values; Kotlin answers both with `data class` + `copy`.
4. **Adapter + Facade + Bridge.**
   - Why together: three "wrap/compose for a cleaner interface" patterns that students confuse. Contrast intent (retrofit vs simplify vs designed-in decoupling).
5. **Decorator + Proxy** (`java.io`, Kotlin `by`, Resilience4j decorators, `java.lang.reflect.Proxy`, Spring/Quarkus AOP, self-invocation, `kotlin-spring`).
   - Why together: identical structure, different intent. This is the single most important "real-world" lesson for backend devs.
6. **Composite + Iterator + Flyweight** (sealed trees, paging iterators, Kotlin `sequence {}`, Integer cache, interning).
   - Why together: trees, traversal and sharing of immutable nodes.
7. **Strategy + Template Method + Command** (function types, execute-around, undo log).
   - Why together: "behavior as a value". The lambda revolution in one lesson.
8. **State + Visitor + Memento** (sealed types, exhaustive `switch`/`when`, record patterns, guards, the expression problem, snapshots).
   - Why together: the data-oriented programming lesson. Goetz's Visitor quote anchors it.
9. **Observer + Mediator + Chain of Responsibility** (EventBus, `Flow`/`SubmissionPublisher`, Reactor, `StateFlow`/`SharedFlow`, servlet filters, OkHttp interceptors).
   - Why together: all route messages between decoupled parties.
10. **Concurrency I: producer-consumer, thread pool/worker, thread-per-message, active object, future/promise** (`BlockingQueue`, virtual threads, `CompletableFuture`, `StructuredTaskScope` preview, Kotlin channels/async).
11. **Concurrency II: guarded suspension, balking, read-write lock, circuit breaker, bulkhead** (wait/notify loop, CAS, RRWL/StampedLock, Resilience4j, Spring 7 `@ConcurrencyLimit`/`@Retryable`).
    - Why the circuit breaker is last: it reuses State (sealed) and Decorator (Resilience4j decorators), so it doubles as a capstone.

### Common misconceptions to address explicitly
- **"Companion object members are static."** They are instance members of the companion object unless `@JvmStatic` — [Kotlin object declarations](https://kotlinlang.org/docs/object-declarations.html).
- **"`lazy` is always safe."** `PUBLICATION` may run the initializer several times, and `NONE` is unspecified across threads — [LazyThreadSafetyMode](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-lazy-thread-safety-mode/).
- **"Records/data classes are immutable."** Only shallowly. `copy()` "doesn't copy components recursively" — [Kotlin data classes](https://kotlinlang.org/docs/data-classes.html). The Java record trap was reproduced **[local]**.
- **"A private constructor protects my data class invariants."** Not in Kotlin 2.4.21: `copy()` stays public (warning only) unless `@ConsistentCopyVisibility` is applied. Put invariants in `init`. **[local]**
- **"`by` delegation is like inheritance."** The delegate never calls your overrides ([Kotlin delegation](https://kotlinlang.org/docs/delegation.html)); `putAll` bypassed the overridden `put` **[local]**. This is a feature (no fragile base class), but surprising.
- **"`Collections.unmodifiableList` makes an immutable copy."** It is a read-through *view* — [Collections.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/Collections.java). Use `List.copyOf` for a snapshot.
- **"`@Transactional`/`@Retryable` on a method always applies."** Not on self-invocation in Spring, not on `final`/`private` methods, and not on final Kotlin classes without `kotlin-spring` — [Spring proxying.adoc](https://raw.githubusercontent.com/spring-projects/spring-framework/main/framework-docs/modules/ROOT/pages/core/aop/proxying.adoc), [Kotlin all-open](https://kotlinlang.org/docs/all-open-plugin.html). Quarkus *does* intercept self-invocation — [Quarkus cdi-reference](https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/cdi-reference.adoc).
- **"Sealed + switch is always exhaustive and safe."** Only if you avoid `default`/`else`. Even then a runtime remainder exists (`null`, separately compiled subtypes) — [exhaustiveness.md](https://raw.githubusercontent.com/openjdk/amber-docs/master/site/design-notes/patterns/exhaustiveness.md).
- **"Visitor is dead."** Goetz says "almost completely unnecessary" *given powerful pattern matching*, and explicitly not that virtual methods are wrong — [pattern-matching-for-java.md](https://raw.githubusercontent.com/openjdk/amber-docs/master/site/design-notes/patterns/pattern-matching-for-java.md). Visitor still fits open or library hierarchies.
- **"StateFlow is an event bus."** It conflates and drops equal consecutive values — [StateFlow](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-state-flow/).
- **"`Integer` `==` works."** Only inside the cache range by default — [Integer.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Integer.java). It printed `false` for 128 **[local]**.
- **"`Cloneable` gives you `clone()`."** The interface has no `clone` method — [Cloneable.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Cloneable.java).
- **"Upgrade the read lock when you need to write."** Upgrading read→write is "not possible" with `ReentrantReadWriteLock` — [RRWL.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/locks/ReentrantReadWriteLock.java).
- **"`if (!ready) wait()` is fine."** Spurious wakeups require a `while` loop — [Object.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Object.java).
- **"`StableValue` is the JDK 25+ singleton API."** It was a JDK 25 preview, was renamed `LazyConstant` in JDK 26, and is still preview in JDK 27 (JEP 531). Don't build lessons on it as final — [PreviewFeature.java @ jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/java.base/share/classes/jdk/internal/javac/PreviewFeature.java).
- **Record component names.** A record component can't be called `notify` (or other no-arg `Object` method names): javac reports "illegal record component name". **[local]**
- **"Strategy and State are different structures."** They are structurally identical. The difference is that State objects (or the transition function) choose the next state; strategies are chosen by the client.

### Exercise ideas with expected outcomes (short list; full details in Key Question 4)
- Payment router → Strategy: CARD/SEPA/WALLET on 10,000 → 320/25/150. Adding an enum constant breaks the `switch` at compile time.
- Fee Decorator chain: 320 / 420 / 500; reordered → 1,500.
- Retrying Proxy: 3 target calls; unwrapped exceptions; self-invocation trace = `["postTwice"]`.
- Payment State machine: `Refunded(p1, 2000)`; illegal transitions throw; adding `Disputed` gives compile errors (javac: "does not cover all possible input values"; kotlinc: "must be exhaustive").
- Kotlin `by` trap: `puts == 1`, `size == 3`.
- StateFlow conflation: `[NEW, AUTHORIZED, CAPTURED]`.
- Producer-consumer: 1,000 in = 1,000 out; a single pill hangs (timeout assertion).
- Circuit breaker: opens after threshold; `CallNotPermittedException`; closes after the half-open probe with a fake clock.
- Bulkhead: the 3rd concurrent call throws `BulkheadFullException`.

### Practical notes for lesson writers
- Use JDK 25 (LTS **[bg]**) as the target, but keep all examples compilable on 21. Everything in these notes compiles with `--release 21`. Mark `StructuredTaskScope` and `LazyConstant` as preview, with the per-release JEP numbers listed under Platform baseline.
- Target Kotlin 2.2+ if you use `when` guards. The samples were verified on 2.4.21.
- For Kotlin + Spring examples, always show the `kotlin("plugin.spring")`/all-open setup, otherwise proxy examples silently fail on final classes.
- Resilience4j: show 2.4.0 APIs (the latest on Central). Mention that 3.x (Java 21 baseline, virtual-thread schedulers) is in development on `master`.
- Source of compiled samples: Java samples were checked with `javac --release 21` and run on JDK 21.0.12.1. Kotlin samples were checked with kotlinc 2.4.21 and kotlinx-coroutines 1.11.0. All assertion tests passed. The code embedded above is excerpted from those runnable files.
