import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
LAB = "labs/generics/src"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :generics:demo -Pmain="
PKG = "workbench.generics.l10.demo"


def kdemo(name, alt=None):
    path = f"{LAB}/demo/kotlin/workbench/generics/l10/demo/{name}.kt"
    d = {"lang": "kotlin", "title": f"{name}.kt", "src": read(path), "run": f"{RUN}{PKG}.{name}Kt", "file": path}
    if alt:
        d["alt"] = jdemo(alt)
    return d


def jdemo(name):
    path = f"{LAB}/demo/java/workbench/generics/l10/demo/{name}.java"
    return {"lang": "java", "title": f"{name}.java", "src": read(path), "run": f"{RUN}{PKG}.{name}", "file": path}


def box(x, y, w, label, cls="box", tcls="t-s t-code"):
    return (f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="38" rx="8"/>'
            f'<text class="{tcls}" x="{x + w // 2}" y="{y + 24}" text-anchor="middle">{label}</text>')


def arrow(x1, x2, y):
    return f'<line class="ln-a" x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" marker-end="url(#arr)"/>'


FIG = ('<svg viewBox="0 0 700 280" role="img" aria-label="Two builder chains. With a self type, CardBuilder().amount(1_200) returns B, which is CardBuilder, so cardToken can be called next. '
       'Without one, PlainCardBuilder().amount(1_200) returns PlainBuilder, and cardToken is an unresolved reference. '
       'The subclass declaration, class CardBuilder extends Builder of CardBuilder, fills B with the subclass itself.">'
       '<text class="t-s t-m" x="15" y="20">with a self type</text>'
       + box(15, 30, 190, "CardBuilder()") + arrow(207, 243, 49)
       + box(245, 30, 210, ".amount(1_200): B", "box-a") + arrow(457, 493, 49)
       + box(495, 30, 190, ".cardToken(\"tok_1\")", "box-ok")
       + '<text class="t-s t-a" x="350" y="88" text-anchor="middle">B = CardBuilder</text>'
         '<text class="t-s t-m" x="15" y="126">without one</text>'
       + box(15, 136, 190, "PlainCardBuilder()") + arrow(207, 243, 155)
       + box(245, 136, 210, ".amount(1_200)", "box") + arrow(457, 493, 155)
       + box(495, 136, 190, ".cardToken(\"tok_1\")", "box-bad")
       + '<text class="t-s t-m" x="350" y="194" text-anchor="middle">returns PlainBuilder</text>'
         '<text class="t-s t-bad" x="590" y="194" text-anchor="middle">Unresolved reference</text>'
       + '<rect class="box-dim" x="15" y="214" width="670" height="38" rx="8"/>'
         '<text class="t-s t-code" x="350" y="238" text-anchor="middle">class CardBuilder : Builder&lt;CardBuilder&gt;()    // the subclass fills B with itself</text>'
         '</svg>')

S1 = """Builders are where the plain generics of lessons 1 to 9 stop being enough. Put the common setters in a base class, add a subclass with its own setter, and the chain breaks as soon as a base setter runs:

```java
class PlainBuilder {
    protected long cents;
    PlainBuilder amount(long cents) { this.cents = cents; return this; }
}
class PlainCardBuilder extends PlainBuilder {
    PlainCardBuilder cardToken(String t) { ... }
}

new PlainCardBuilder().amount(1_200).cardToken("tok_1");   // error: cannot find symbol
```

```kotlin
open class PlainBuilder {
    protected var cents = 0L
    fun amount(cents: Long): PlainBuilder { this.cents = cents; return this }
}
class PlainCardBuilder : PlainBuilder() {
    fun cardToken(t: String): PlainCardBuilder { ... }
}

PlainCardBuilder().amount(1_200).cardToken("tok_1")
// error: Unresolved reference 'cardToken' on receiver of type 'PlainBuilder'.
```

`amount` returns a `PlainBuilder`, because that's all the base class knows about itself. The object is still a `PlainCardBuilder`, but the static type has lost it. The base class needs a way to say "I return whatever subclass I really am". The answer is a **self type**, written as a **recursive bound**:

```java
abstract class Builder<B extends Builder<B>> {
    protected long cents;
    B amount(long cents) { this.cents = cents; return self(); }
    protected abstract B self();
}
final class CardBuilder extends Builder<CardBuilder> {
    CardBuilder cardToken(String t) { ...; return this; }
    @Override protected CardBuilder self() { return this; }
}
```

```kotlin
abstract class Builder<B : Builder<B>> {
    protected var cents = 0L
    fun amount(cents: Long): B { this.cents = cents; return self() }
    protected abstract fun self(): B
}
class CardBuilder : Builder<CardBuilder>() {
    fun cardToken(t: String): CardBuilder { ...; return this }
    override fun self() = this
}
```

Read `B : Builder<B>` as "B is a builder whose own B is B". The only types that fit are subclasses that name themselves, as `CardBuilder : Builder<CardBuilder>()` does. Inside the base class, `B` stands for "my concrete subclass", so `amount` can return it. You met the shape already: lesson 2's `T : Comparable<T>` is a recursive bound, and Java's own `Enum<E extends Enum<E>>` is one too.

Two details matter. The abstract `self()` keeps the code checked: each subclass returns `this`, and the compiler verifies it is a `B`. And the bound can't force honesty: `class Liar : Builder<CardBuilder>()` compiles. If you write `self()` as abstract, the liar must return a `CardBuilder` it doesn't have, which is where you'd notice.

In pure Kotlin code you often don't need a builder at all. A data class with default arguments and `copy` covers most cases. Reach for self types when Java callers need a builder, or when you extend a Java class that already uses one."""

S2 = """The default bound of a type parameter is `Any?` (lesson 2), so a plain `T` may be a nullable type. Sometimes you know that one particular value is not null, and you want the type to say so. Kotlin writes that as `T & Any`, a **definitely non-nullable type**: "`T`, with null taken out".

```java
// Java's types say nothing about null. The best you can do is a comment and a run-time check.
static <T> T firstNotNullValue(List<T> items) {
    for (T item : items) if (item != null) return item;
    throw new NoSuchElementException("no non-null element");
}

String first = firstNotNullValue(Arrays.asList(null, "eur", "usd"));
```

```kotlin
fun <T> List<T>.firstNotNullValue(): T & Any {
    for (item in this) if (item != null) return item     // smart cast: item is T & Any here
    throw NoSuchElementException("no non-null element")
}

val first: String = listOf(null, "eur", "usd").firstNotNullValue()   // T = String?, result String
```

With `T = String?`, `T & Any` is `String`. With `T = Payment`, it's `Payment`. The compiler holds you to it: returning a plain `T` gives `Return type mismatch: expected 'T (of fun <T> forget) & Any', actual 'T (of fun <T> forget)'.`

The Kotlin docs name the main use case: overriding Java methods whose generic parameters are annotated `@NotNull`. Kotlin reads `@NotNull T` in a Java interface as `T & Any`:

```java
public interface NotNullTransformer<T> {
    @NotNull T transform(@NotNull T value);
}
```

```kotlin
class UpperCaser<T : CharSequence?> : NotNullTransformer<T> {
    override fun transform(value: T & Any): T & Any = ...
}
```

Two rules come with it. The left side must be a type parameter with a nullable bound; with `T : Any` there is no null to remove, and the compiler says `Intersection types are supported only for definitely non-nullable types: left part must be a type parameter with nullable bounds.` And the guarantee is Kotlin-only: Java sees `<T> T firstNotNullValue(List<T>)` with no trace of `& Any`.

The docs also say that when you work only with Kotlin, you'll rarely need to write it, because inference handles it. Expect to type `T & Any` at the Java boundary and in small helpers. One more that earns its keep in a message handler:

```java
// Java: the null check happens, but the type can't record it
static <T> T requireValue(T value, String name) {
    if (value == null) throw new IllegalArgumentException(name + " is required");
    return value;
}
```

```kotlin
fun <T> T.requireValue(name: String): T & Any = this ?: throw IllegalArgumentException("$name is required")

val token: String = message.cardToken.requireValue("card token")   // cardToken is a String?
```

It turns an optional field of a Kafka message into a value the rest of the handler can use without `!!`."""

S3 = """Here is a puzzle from lesson 4. `List` is declared `interface List<out E>`, and an `out` parameter can't appear in a parameter position. Yet you call `list.contains(x)` every day. The standard library's source (2.4.21) shows how:

```text
public operator fun contains(element: @UnsafeVariance E): Boolean
public fun indexOf(element: @UnsafeVariance E): Int
```

`@UnsafeVariance` "suppresses errors about variance conflict" for one type use. It is a promise from the author: this parameter is only compared, never stored, so a `List<Int>` seen as a `List<Number>` can't be damaged by it. `contains(2.5)` on that list just returns `false`.

Why take an `E` at all, when `Any?` would need no annotation? Because the `E` lets the compiler catch nonsense checks. Java chose `Object`, and pays for it:

```java
Set<Long> paymentIds = Set.of(42L);
paymentIds.contains(42);                      // false: 42 is boxed to an Integer, and Integer(42) != Long(42)
List.of(1_200, 350).contains("1200");         // compiles, always false
```

```kotlin
val paymentIds: Set<Long> = setOf(42L)
paymentIds.contains(42)                       // true: the literal 42 is typed as a Long here
listOf(1_200, 350).contains("1200")
// error: Type inference failed. The value of the type parameter 'T' must be mentioned in input types ...
```

That first Java line is a real bug class: an `int` payment id looked up in a set of `Long`s, false every time.

The annotation is called unsafe for a reason. It switches the check off, and the compiler believes you:

```java
// Java's way to break a ? extends view on purpose is an unchecked cast:
List<? extends Object> view = ids;
((List<Object>) view).add(42);
String lastId = ids.get(ids.size() - 1);      // ClassCastException
```

```kotlin
class Ledger<out T>(first: T) {
    private val entries = mutableListOf(first)
    fun add(entry: @UnsafeVariance T) { entries.add(entry) }   // stores it: a broken promise
    fun last(): T = entries.last()
}

val ids: Ledger<String> = Ledger("pay_1")
val anything: Ledger<Any> = ids               // fine: Ledger is out T
anything.add(42)                              // compiles
val lastId: String = ids.last()               // ClassCastException
```

Use `@UnsafeVariance` only on parameters that are read and compared (`contains`, `indexOf`, an equality check), never on ones that are kept. You might write it yourself on a read-only covariant type that offers a lookup, such as `interface Page<out T> { fun indexOf(item: @UnsafeVariance T): Int }`. To check that it's honest, follow the parameter through the body. If it only reaches `==`, `equals` or `hashCode`, the promise holds. If it reaches a field, a collection or a callback that keeps it, remove the annotation and make the type invariant, or split it into a read view and a write view, as lesson 11 of this track does."""

S4 = """Three more tools sit at the edges of the type system.

Function types carry variance on both ends. `(P) -> R` is `Function1<in P, out R>` (lesson 5), so a composition helper accepts a more general second step and can hand back a more general result:

```java
// Function<T, R> is invariant, so the JDK writes the variance into the signature:
// default <V> Function<T, V> andThen(Function<? super R, ? extends V> after)
Function<String, Long> parseCents = s -> Long.parseLong(s.replace(".", ""));
Function<Object, String> describe = x -> "<" + x + ">";
Function<String, String> pipeline = parseCents.andThen(describe);      // <1250> for "12.50"
```

```kotlin
fun <A, B, C> andThen(first: (A) -> B, second: (B) -> C): (A) -> C = { a -> second(first(a)) }

val parseCents: (String) -> Long = { it.replace(".", "").toLong() }
val describe: (Any) -> String = { "<$it>" }                  // takes Any, not just Long
val pipeline: (String) -> CharSequence = andThen(parseCents, describe)   // <1250> for "12.50"
```

`Nothing` is the **bottom type**: a subtype of every type, with no values at all. `throw` and `TODO()` have type `Nothing`, which is why `val strict: Long = text.toLongOrNull() ?: fail("not a number")` type-checks when `fun fail(reason: String): Nothing`. It also explains `emptyList()`: one shared `List<Nothing>` fits every `List<Payment>`, because `List` is `out E` and `Nothing` is below `Payment`. Lesson 11 uses the same trick for `Either`. Java has no bottom type. `Collections.emptyList()` is a generic method whose `T` is inferred at each call, and a Kotlin `List<Nothing>` reaches Java as a raw `List`.

A **type alias** gives an existing type a shorter name, and it can be generic:

```java
// Java has no type aliases. The nearest thing, a functional interface, is a new, separate type.
@FunctionalInterface interface Handler<E> { void handle(E event); }
```

```kotlin
typealias Handler<E> = (E) -> Unit           // just a name: a Handler<E> IS an (E) -> Unit
typealias Table<K> = MutableMap<K, MutableList<K>>

val audit: Handler<CardAuthorized> = { println("audit ${it.paymentId}") }
val plain: (CardAuthorized) -> Unit = audit  // same type, no conversion
```

Because an alias is only a name, it has the variance of what it stands for: a `Handler<PaymentEvent>` is a `Handler<CardAuthorized>`, exactly as with the function type. Aliases nested inside a class became Stable in Kotlin 2.3, with one limit: they can't mention the outer class's type parameters."""

L = {
    "id": "gen-10",
    "title": "Advanced generics: recursive bounds, T & Any, @UnsafeVariance",
    "minutes": 38,
    "goal": "By the end you can write a self-typed builder hierarchy with a recursive bound in Kotlin and Java, use `T & Any` for values known not to be null, explain why `List<out E>` may take an `E` in `contains` and when `@UnsafeVariance` is a lie, and use function-type variance, `Nothing` and generic type aliases on purpose.",
    "warmup": {
        "q": "`open class Base { fun amount(c: Long): Base = this }` and `class Card : Base() { fun token(t: String): Card = this }`. Which chain compiles?",
        "options": [
            "`Card().amount(1_200).token(\"tok_1\")`",
            "`Card().token(\"tok_1\").amount(1_200)`",
            "Both, because the object is a `Card` either way",
            "Neither"
        ],
        "answer": 1,
        "why": "Each call returns its declared type. `token` returns a `Card`, so `amount` can follow. `amount` returns a `Base`, and `Base` has no `token`, even though the object is really a `Card`. The compiler goes by static types, which is the problem self types solve."
    },
    "sections": [
        {
            "h": "A self type lets base-class setters return the subclass",
            "body": S1,
            "figure": {"svg": FIG, "caption": "A recursive bound lets the base class return its concrete subclass, so a chain keeps the subclass's own setters in reach."},
            "try": {
                "title": "Break a builder chain, then fix it with B : Builder<B>",
                "minutes": 4,
                "steps": [
                    "Run `SelfTypeDemo` (or `SelfTypeDemoJava`). Compare the static type and the run-time class on the first line.",
                    "Uncomment wrong move 1, predict, run.",
                    "Uncomment wrong move 2, the `Liar` class. It compiles. Add `println(Liar().amount(5)::class.simpleName)` below it and predict what prints."
                ],
                "code": kdemo("SelfTypeDemo", "SelfTypeDemoJava"),
                "expect": "Both print `after amount(): static type PlainBuilder, run-time class PlainCardBuilder` and `card 1200 with tok_1`. Wrong move 1 fails with `Unresolved reference 'cardToken' on receiver of type 'PlainBuilder'.` (Java: `cannot find symbol`). The `Liar` compiles because the bound only asks for some builder, and `Liar().amount(5)` prints `CardBuilder`: a fresh object, not the liar you configured. Nothing forces a subclass to pass itself."
            },
            "refs": [
                {"title": "Generics: upper bounds (Kotlin docs)", "url": "https://kotlinlang.org/docs/generics.html", "kind": "docs"}
            ]
        },
        {
            "h": "T & Any says definitely not null",
            "body": S2,
            "try": {
                "title": "Take null out of a type",
                "minutes": 4,
                "steps": [
                    "Run `NonNullDemo` (or `NonNullDemoJava`). Open `NotNullTransformer.java` next to it: a Java interface with `@NotNull`.",
                    "Uncomment wrong moves 1 and 2 in `NonNullDemo.kt` one at a time. Predict first.",
                    "Uncomment function 3 at the bottom. In the Java twin, uncomment the `oops` line and run: what does Java catch, and when?"
                ],
                "code": kdemo("NonNullDemo", "NonNullDemoJava"),
                "expect": "Both print `first = eur, shown = no note` and `transformed = PAY_1`. Kotlin's wrong moves: (1) `Return type mismatch: expected 'T (of fun <T> forget) & Any', actual 'T (of fun <T> forget)'.`, (2) `Null cannot be a value of a non-null type 'String'.`: for `T = String?`, `T & Any` is `String`. Function 3: `Intersection types are supported only for definitely non-nullable types: left part must be a type parameter with nullable bounds.` The Java `oops` line compiles and throws `NullPointerException` from `Objects.requireNonNull` at run time."
            }
        },
        {
            "h": "@UnsafeVariance: how List<out E> can take an E in contains",
            "body": S3,
            "try": {
                "title": "Use the annotation well, then badly",
                "minutes": 4,
                "steps": [
                    "Run `UnsafeVarianceDemo` and `UnsafeVarianceDemoJava`. Find the line that compiles in Java and is rejected in Kotlin.",
                    "Uncomment wrong move 1 in the Kotlin file, predict, run.",
                    "Uncomment wrong move 2 (`Ledger2`) and read the error. That's the check `@UnsafeVariance` switched off in `Ledger`."
                ],
                "code": kdemo("UnsafeVarianceDemo", "UnsafeVarianceDemoJava"),
                "expect": "Both print `contains(350): true, contains(2.5): false` and `ClassCastException: class java.lang.Integer cannot be cast to class java.lang.String`. Java also prints `contains(\"1200\") compiles in Java: false`. In Kotlin, wrong move 1 fails with `Type inference failed. The value of the type parameter 'T' must be mentioned in input types ...`, and `Ledger2` fails with `Type parameter 'T' is declared as 'out' but occurs in 'in' position in type 'T (of class Ledger2<out T>)'.`"
            },
            "refs": [
                {"title": "UnsafeVariance (Kotlin stdlib API)", "url": "https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-unsafe-variance/", "kind": "docs"}
            ]
        },
        {
            "h": "Function types, Nothing and type aliases",
            "body": S4,
            "try": {
                "title": "Compose with variance, fail with Nothing",
                "minutes": 4,
                "steps": [
                    "Run `FunctionTypesDemo` (or `FunctionTypesDemoJava`, which also calls the JDK's own `andThen`).",
                    "Uncomment the wrong move and read which type the compiler inferred for the pipeline.",
                    "Change `fail`'s return type from `Nothing` to `Unit`. Which line breaks, and why?"
                ],
                "code": kdemo("FunctionTypesDemo", "FunctionTypesDemoJava"),
                "expect": "Kotlin prints `pipeline(\"12.50\") = <1250>`, `none = [], cents = 0, strict = 1200` and `audit pay_1`; Java prints the same plus `JDK andThen: <350>`. The wrong move fails with `Initializer type mismatch: expected '(Any) -> String', actual '(String) -> String'.`: a function that needs a `String` input can't stand in for one that takes `Any`. With `Unit`, the `strict` line fails with `Initializer type mismatch: expected 'Long', actual 'Any'.`: the elvis expression's type becomes the common supertype of `Long` and `Unit`. `Nothing` fits there because it is a subtype of `Long`."
            },
            "refs": [
                {"title": "Type aliases (Kotlin docs)", "url": "https://kotlinlang.org/docs/type-aliases.html", "kind": "docs"}
            ]
        }
    ],
    "analogy": "A self type is like a franchise operations manual. Head office writes it once, and every step ends with \"hand the tray back to the counter of ______\". When a restaurant joins, it writes its own name in the blank: that's `CardBuilder : Builder<CardBuilder>()`. Every franchise then gets a manual that sends trays back to its own counter, without head office knowing any franchise by name. The analogy breaks in the same place the code does: a franchise could write another restaurant's name in the blank, and the manual can't stop it. The recursive bound only checks that the name belongs to some franchise.",
    "in_your_world": "You meet self types in Java libraries before you write one. Testcontainers declares `GenericContainer<SELF extends GenericContainer<SELF>>`, which is why Kotlin test code for an Oracle or Kafka integration test sometimes needs `class KGenericContainer(image: String) : GenericContainer<KGenericContainer>(image)` just to use the fluent `withEnv(...)` chain. Card-issuer and banking SDKs in Java often ship builder hierarchies with the same shape. `T & Any` shows up when your Kotlin code implements a Java interface from such an SDK that marks generic parameters `@NotNull`. And `Nothing` is the honest return type for helpers like `fun rejectPayment(reason: String): Nothing` in a Temporal activity, which lets `val card = request.card ?: rejectPayment(\"no card\")` type-check without a dummy value.",
    "mistake": "The common mistake in self-typed builders is the unchecked shortcut: `@Suppress(\"UNCHECKED_CAST\") fun amount(c: Long): B { cents = c; return this as B }` in the base class, with no `self()`. It works until someone copies a subclass and forgets to change the type argument: `class WalletBuilder : Builder<CardBuilder>()`. That compiles, and `WalletBuilder().amount(5)` throws `ClassCastException: class WalletBuilder cannot be cast to class CardBuilder` at the call site, because erasure made the cast inside `amount` check nothing. People write the cast because it saves one override per subclass. The fix is an abstract `protected abstract fun self(): B` that each subclass implements as `= this`. Then the same copy-paste slip is a compile error: `Return type mismatch: expected 'CardPaymentBuilder', actual 'WalletPaymentBuilder'.`",
    "compare": {
        "title": "A self-typed builder hierarchy in Java and Kotlin",
        "java": {
            "title": "PaymentRequestBuilder.java",
            "src": "abstract class PaymentRequestBuilder<B extends PaymentRequestBuilder<B>> {\n    protected long cents;\n    protected String currency;\n\n    B amount(long cents) { this.cents = cents; return self(); }\n    B currency(String code) { this.currency = code; return self(); }\n    protected abstract B self();\n}\n\nfinal class CardPaymentBuilder extends PaymentRequestBuilder<CardPaymentBuilder> {\n    private String token;\n\n    CardPaymentBuilder cardToken(String token) { this.token = token; return this; }\n    @Override protected CardPaymentBuilder self() { return this; }\n\n    CardPayment build() {\n        if (cents <= 0) throw new IllegalStateException(\"amount must be positive\");\n        return new CardPayment(cents, currency, \"\", token);\n    }\n}\n\n// new CardPaymentBuilder().amount(1_200).currency(\"EUR\").cardToken(\"tok_42\").build();"
        },
        "kotlin": {
            "title": "PaymentRequestBuilder.kt",
            "src": "abstract class PaymentRequestBuilder<B : PaymentRequestBuilder<B>> {\n    protected var cents: Long = 0\n    protected var currency: String? = null\n\n    fun amount(cents: Long): B { this.cents = cents; return self() }\n    fun currency(code: String): B { currency = code; return self() }\n    protected abstract fun self(): B\n}\n\nclass CardPaymentBuilder : PaymentRequestBuilder<CardPaymentBuilder>() {\n    private var token: String? = null\n\n    fun cardToken(token: String): CardPaymentBuilder { this.token = token; return this }\n    override fun self() = this\n\n    fun build(): CardPayment {\n        check(cents > 0) { \"amount must be positive\" }\n        return CardPayment(cents, currency!!, \"\", checkNotNull(token))\n    }\n}\n\n// CardPaymentBuilder().amount(1_200).currency(\"EUR\").cardToken(\"tok_42\").build()"
        },
        "note": "The recursive bound is the same idea in both languages: `B extends PaymentRequestBuilder<B>` and `B : PaymentRequestBuilder<B>`, with each subclass passing itself and an abstract `self()` instead of an unchecked cast. Kotlin adds checks Java can't express: `currency` is a `String?`, so `build()` must deal with a missing value, and helpers like `check` and `checkNotNull` throw `IllegalStateException` with your message. The other three tools of this lesson have no Java twin: `T & Any` (Java types carry no nullability), `@UnsafeVariance` (Java has no declaration-site variance to suppress), and `Nothing` (Java has no bottom type). Java also has no type aliases. And in Kotlin you can often skip the builder entirely with a data class, default arguments and `copy`."
    },
    "worked": {
        "title": "Add a wallet payment to the builder hierarchy",
        "steps": [
            {"say": "The lab's hierarchy has card payments and bank transfers. Product wants wallet payments too. The quickest path is copy and paste from `CardPaymentBuilder`, and that's how the classic bug gets in: the type argument still says `CardPaymentBuilder`.",
             "code": "class WalletPaymentBuilder : PaymentRequestBuilder<CardPaymentBuilder>() {   // copied, not changed\n    private var walletId: String? = null\n    fun walletId(id: String): WalletPaymentBuilder { walletId = id; return this }\n    override fun self(): CardPaymentBuilder = this\n}\n// error: Return type mismatch: expected 'CardPaymentBuilder', actual 'WalletPaymentBuilder'.",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "final class WalletPaymentBuilder extends PaymentRequestBuilder<CardPaymentBuilder> {   // copied, not changed\n    private String walletId;\n    WalletPaymentBuilder walletId(String id) { walletId = id; return this; }\n    @Override protected CardPaymentBuilder self() { return this; }\n}\n// error: incompatible types: WalletPaymentBuilder cannot be converted to CardPaymentBuilder"},
            {"say": "1. The abstract `self()` caught it at compile time. With `return this as B` in the base class it would have compiled and failed later, at the first `amount(...)` call. Fix the declaration: the subclass passes itself.",
             "code": "class WalletPaymentBuilder : PaymentRequestBuilder<WalletPaymentBuilder>() {\n    private var walletId: String? = null\n    fun walletId(id: String): WalletPaymentBuilder { walletId = id; return this }\n    override fun self() = this       // B is WalletPaymentBuilder: no cast",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "final class WalletPaymentBuilder extends PaymentRequestBuilder<WalletPaymentBuilder> {\n    private String walletId;\n    WalletPaymentBuilder walletId(String id) { walletId = id; return this; }\n    @Override protected WalletPaymentBuilder self() { return this; }   // no cast"},
            {"say": "2. Build: check the common fields with the base class's `checkCommon()`, then the wallet's own field. Self-check: why does `amount(...)` in the chain below return a `WalletPaymentBuilder` without any change to the base class? (Because `B` is filled with `WalletPaymentBuilder` in the declaration, and `amount` returns `B`.)",
             "code": "    fun build(): WalletPayment {\n        checkCommon()\n        val id = checkNotNull(walletId) { \"wallet id is required\" }\n        return WalletPayment(cents, currency!!, reference, id)\n    }\n}\n\nval p = WalletPaymentBuilder().amount(2_500).currency(\"EUR\").walletId(\"wal_9\").build()",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "    WalletPayment build() {\n        checkCommon();\n        if (walletId == null) throw new IllegalStateException(\"wallet id is required\");\n        return new WalletPayment(cents, currency, reference, walletId);\n    }\n}\n\nWalletPayment p = new WalletPaymentBuilder().amount(2_500).currency(\"EUR\").walletId(\"wal_9\").build();"}
        ]
    },
    "lab": {
        "title": "A self-typed builder hierarchy, and functions with variance",
        "minutes": 13,
        "files": [
            f"{LAB}/main/kotlin/workbench/generics/l10/Builders.kt",
            f"{LAB}/main/kotlin/workbench/generics/l10/Functions.kt"
        ],
        "run": "./gradlew :generics:test --tests 'workbench.generics.l10.*'",
        "steps": [
            "Run the tests. All eight fail. The signatures are done; read them first, especially `PaymentRequestBuilder<B : PaymentRequestBuilder<B>>` and the two subclass declarations.",
            "In `Builders.kt`, write the three base setters: store the value, then `return self()`. Write `checkCommon()` with two `check(...)` calls.",
            "Write `self()`, the setter and `build()` in `CardPaymentBuilder` and `BankTransferBuilder`. `build()` calls `checkCommon()` first, then checks its own field.",
            "In `Functions.kt`, write `andThen` as a lambda, and `fanOut` as a lambda that calls each handler in order. Read the `fanOut` test: it passes a `Handler<PaymentEvent>` where `Handler<CardAuthorized>` is expected.",
            "Write `firstNotNullValue` with a loop. Notice that returning the smart-cast `item` satisfies `T & Any`.",
            "Run the tests until all eight pass."
        ],
        "hints": [
            "`fun amount(cents: Long): B { this.cents = cents; return self() }` is the whole pattern for each setter.",
            "`checkNotNull(token) { \"card token is required\" }` returns the non-null value or throws `IllegalStateException` with that message.",
            "`andThen` is one line: `= { a -> second(first(a)) }`. `fanOut` is `= { event -> for (h in handlers) h(event) }`."
        ],
        "done_when": "All eight tests in `AdvancedTest` pass."
    },
    "drill": {
        "title": "Write a self-typed builder from memory",
        "minutes": 5,
        "prompt": "Close this page. Write an abstract `Builder` with a recursive bound, one setter `amount(cents)` that returns the subclass type, and an abstract `self()`. Then write `CardBuilder` with `cardToken(t)` and `build()`, so that `CardBuilder().amount(1_200).cardToken(\"tok_1\").build()` compiles. Do it in Kotlin, then in Java.",
        "answer": {
            "lang": "kotlin",
            "src": "abstract class Builder<B : Builder<B>> {\n    protected var cents = 0L\n    fun amount(cents: Long): B { this.cents = cents; return self() }\n    protected abstract fun self(): B\n}\n\nclass CardBuilder : Builder<CardBuilder>() {      // the subclass fills B with itself\n    private var token = \"\"\n    fun cardToken(t: String): CardBuilder { token = t; return this }\n    override fun self() = this\n    fun build() = \"card $cents with $token\"\n}",
            "alt": {"lang": "java", "title": "Builder.java", "src": "abstract class Builder<B extends Builder<B>> {\n    protected long cents;\n    B amount(long cents) { this.cents = cents; return self(); }\n    protected abstract B self();\n}\n\nfinal class CardBuilder extends Builder<CardBuilder> {   // the subclass fills B with itself\n    private String token = \"\";\n    CardBuilder cardToken(String t) { token = t; return this; }\n    @Override protected CardBuilder self() { return this; }\n    String build() { return \"card \" + cents + \" with \" + token; }\n}"}
        }
    },
    "recap": [
        "A recursive bound, `B : Builder<B>`, lets a base class name its own concrete subclass, so base setters can return it and chains keep subclass methods.",
        "Each subclass passes itself (`CardBuilder : Builder<CardBuilder>()`) and implements an abstract `self() = this`. Avoid `this as B`: it is unchecked and fails late.",
        "`T & Any` is \"T without null\": for `T = String?` it's `String`. Its main use is overriding Java generic methods marked `@NotNull`.",
        "`List<out E>` declares `contains(element: @UnsafeVariance E)`. That's safe because `contains` only compares, and the `E` lets Kotlin reject `listOf(1).contains(\"1\")`.",
        "`@UnsafeVariance` on a parameter that gets stored breaks type safety and ends in a `ClassCastException`.",
        "`Nothing` is a subtype of every type, so `emptyList()` fits any `List<T>` and `?: fail(...)` type-checks. A type alias is only a new name, with the variance of the type it names."
    ],
    "quiz": [
        {
            "q": "`abstract class Builder<B : Builder<B>> { fun amount(c: Long): B; ... }` and `class CardBuilder : Builder<CardBuilder>()`. What is the static type of `CardBuilder().amount(1_200)`?",
            "options": [
                "`Builder<CardBuilder>`",
                "`CardBuilder`",
                "`Builder<*>`",
                "`B`, which the compiler can't resolve outside the class"
            ],
            "answer": 1,
            "why": "`amount` returns `B`, and the subclass declaration fills `B` with `CardBuilder`. So at the call site the result is a `CardBuilder`, and its own methods are still available. That is the whole point of the recursive bound."
        },
        {
            "q": "`fun <T> List<T>.firstNotNullValue(): T & Any`. What is the type of `listOf<String?>(null, \"EUR\").firstNotNullValue()`?",
            "options": [
                "`String`",
                "`String?`",
                "`Any`",
                "`String & Any?`"
            ],
            "answer": 0,
            "why": "`T` is `String?`, and `& Any` removes the null: `String?` minus null is `String`. With `T = Payment` it would be `Payment`. That's why the result can go straight into a `val code: String`."
        },
        {
            "q": "Why can `interface List<out E>` declare `fun contains(element: @UnsafeVariance E): Boolean` without risk?",
            "options": [
                "Because the annotation makes the check happen at run time instead",
                "Because `List` is immutable, so nothing can be stored",
                "Because `contains` only compares the argument and never stores it, so a `List<Int>` seen as `List<Number>` can't be damaged",
                "Because `E` is erased, so variance doesn't apply at run time"
            ],
            "answer": 2,
            "why": "Variance protects against storing a wrong value. `contains` stores nothing; asking a list of ints whether it contains `2.5` just returns `false`. The annotation is a promise about that. It isn't a run-time check, and \"immutable\" isn't the reason: `@UnsafeVariance` on a storing method breaks even an immutable-looking class, as the `Ledger` demo shows."
        },
        {
            "q": "`val parse: (String) -> Long` and `val describe: (Any) -> String`. Does `val p: (String) -> CharSequence = andThen(parse, describe)` compile, with `fun <A, B, C> andThen(first: (A) -> B, second: (B) -> C): (A) -> C`?",
            "options": [
                "No: `describe` must be exactly `(Long) -> String`",
                "No: the result would be `(String) -> String`, which is not a `(String) -> CharSequence`",
                "Only with an explicit cast",
                "Yes: `(Any) -> String` is a `(Long) -> String` (in on the parameter), and `(String) -> String` is a `(String) -> CharSequence` (out on the result)"
            ],
            "answer": 3,
            "why": "Function types are `Function1<in P, out R>`. A function that accepts any value can stand in for one that accepts a `Long`, and a function that returns a `String` can stand in for one that returns a `CharSequence`. This is the \"pick the right variance\" check from lesson 5 applied twice in one call."
        },
        {
            "q": "From \"Covariance with out: producers\": `class Ledger<out T> { fun add(entry: T) {} }` doesn't compile. What does the compiler object to?",
            "options": [
                "`T` appears in an in-position (a parameter) in a class that declared it `out`",
                "`add` is public; it would compile if it were `protected`",
                "Classes declared `out` can't have functions with parameters",
                "`Ledger` needs a constructor that takes a `T`"
            ],
            "answer": 0,
            "why": "An `out` parameter may appear only in out-positions such as return types; a parameter is an in-position. `protected` members are checked too; only `private` ones are exempt. `@UnsafeVariance` would silence the error, and this lesson's demo shows what that costs when `add` stores the value.",
            "from": "gen-04"
        }
    ],
    "flashcards": [
        {"front": "What problem does `abstract class Builder<B : Builder<B>>` solve?", "back": "Base-class setters can return `B`, the concrete subclass, so a chain like `CardBuilder().amount(1).cardToken(\"t\")` keeps the subclass's methods."},
        {"front": "Why an abstract `self(): B` instead of `return this as B`?", "back": "`this as B` is unchecked and fails late if a subclass passes the wrong type argument. An overridden `self() = this` is checked by the compiler."},
        {"front": "What does `T & Any` mean?", "back": "`T` with null removed: a definitely non-nullable type. For `T = String?` it is `String`."},
        {"front": "What is the main use of `T & Any`?", "back": "Overriding Java generic methods whose parameters or results are annotated `@NotNull`."},
        {"front": "How does `List<out E>` get away with `contains(element: E)`?", "back": "The parameter is marked `@UnsafeVariance`. It's safe because `contains` only compares the element and never stores it."},
        {"front": "Why does `val none: List<Payment> = emptyList()` compile?", "back": "`emptyList()` gives a `List<Nothing>`. `Nothing` is a subtype of every type, and `List` is `out E`, so it is a `List<Payment>`."},
        {"front": "Is `typealias Handler<E> = (E) -> Unit` a new type?", "back": "No. It's only a name: a `Handler<CardAuthorized>` is an `(CardAuthorized) -> Unit`, with the same variance."}
    ],
    "terms": [
        {"term": "Recursive bound", "plain": "A bound that mentions the type parameter itself: `T : Comparable<T>`, `B : Builder<B>`."},
        {"term": "Self type", "plain": "A type parameter that stands for \"my own concrete subclass\", so base methods can return it."},
        {"term": "Definitely non-nullable type", "plain": "`T & Any`: the type parameter `T` with null taken out."},
        {"term": "@UnsafeVariance", "plain": "An annotation that switches off the variance check for one type use. A promise, not a check."},
        {"term": "Nothing", "plain": "Kotlin's bottom type: a subtype of every type, with no values. The type of `throw` and `TODO()`."},
        {"term": "Type alias", "plain": "A new name for an existing type, such as `typealias Handler<E> = (E) -> Unit`. Not a new type."}
    ],
    "explain_back": {
        "prompt": "A teammate sees `abstract class PaymentRequestBuilder<B : PaymentRequestBuilder<B>>` in a code review and says it looks circular and pointless. Explain in your own words what problem it solves, how a subclass uses it, and what it can't prevent.",
        "answer": "Without it, a setter in the base class can only return the base class type, so after calling `amount()` on a `CardPaymentBuilder` the compiler thinks it has a plain builder and won't let you call `cardToken()`. The recursive bound gives the base class a name, `B`, for \"whatever concrete subclass I am\". Each subclass fills it in with itself, as in `class CardPaymentBuilder : PaymentRequestBuilder<CardPaymentBuilder>()`, so inside that subclass `B` means `CardPaymentBuilder` and every inherited setter returns that type. The bound only looks circular: it reads \"B is a builder whose B is B\", which only self-naming subclasses satisfy. Each subclass implements `self()` as `this`, which the compiler checks, so no unchecked cast is needed. What it can't prevent is a subclass passing the wrong class, such as a wallet builder that says `PaymentRequestBuilder<CardPaymentBuilder>`. The abstract `self()` turns that into a compile error, which is why it's better than `this as B`."
    },
    "deeper": {
        "minutes": 10,
        "body": "Recursive bounds go further than builders. `java.lang.Enum` is declared `Enum<E extends Enum<E>>` so that `compareTo` takes the same enum type, and `EnumSet.noneOf(Class<E>)` is bounded `<E extends Enum<E>>`. Kotlin's `Enum<E : Enum<E>>` is the same declaration. Lesson 2's `fun <T : Comparable<T>> maxOf2(a: T, b: T)` is the most common recursive bound of all; the Java signature Kotlin generates for it is `<T extends Comparable<? super T>>`, because Kotlin's `Comparable` is declared `in T`.\n\nThe standard library's use of `@UnsafeVariance` is easy to check. In the 2.4.21 sources (`kotlin-stdlib-sources.jar`, file `Collections.kt`) it appears on `contains`, `containsAll` and `indexOf` of `List`, and on `AbstractCollection.contains`. The `contains(\"1200\")` error you saw comes from a second safety net: when the member `contains(element: Int)` doesn't accept a `String`, the compiler tries the extension `Iterable<T>.contains(element: T)`, whose `T` is marked so that it must match the receiver's element type, and inference fails with the message you read.\n\nTwo small facts about `Nothing`. The type of the literal `null` is `Nothing?`, which is why `null` fits every nullable type. And when a Kotlin function returns `List<Nothing>`, Java sees a raw `List`, because Java has no bottom type to write there.\n\nType aliases can't create the distinct types people sometimes want from them. `typealias PaymentId = String` lets you pass any `String` where a `PaymentId` is expected. If you want the compiler to keep payment ids and refund ids apart, use a value class, `@JvmInline value class PaymentId(val value: String)`, which is a real type with no wrapper object at run time in most uses."
    },
    "sources": [
        {"title": "Generics: definitely non-nullable types and variance (Kotlin docs)", "url": "https://kotlinlang.org/docs/generics.html"},
        {"title": "UnsafeVariance (Kotlin stdlib API)", "url": "https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-unsafe-variance/"},
        {"title": "Type aliases (Kotlin docs)", "url": "https://kotlinlang.org/docs/type-aliases.html"},
        {"title": "What's new in Kotlin 2.3.0: nested type aliases", "url": "https://kotlinlang.org/docs/whatsnew23.html"}
    ]
}

out = ROOT / "content/lessons/gen-10.json"
out.write_text(json.dumps(L, indent=2, ensure_ascii=False) + "\n")
print("wrote", out)
