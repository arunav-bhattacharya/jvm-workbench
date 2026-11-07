import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
LAB = "labs/generics/src"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :generics:demo -Pmain="
PKG = "workbench.generics.l11.demo"


def kdemo(name, alt=None):
    path = f"{LAB}/demo/kotlin/workbench/generics/l11/demo/{name}.kt"
    d = {"lang": "kotlin", "title": f"{name}.kt", "src": read(path), "run": f"{RUN}{PKG}.{name}Kt", "file": path}
    if alt:
        d["alt"] = jdemo(alt)
    return d


def jdemo(name):
    path = f"{LAB}/demo/java/workbench/generics/l11/demo/{name}.java"
    return {"lang": "java", "title": f"{name}.java", "src": read(path), "run": f"{RUN}{PKG}.{name}", "file": path}


def box(x, y, w, label, cls="box", tcls="t-s t-code"):
    return (f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="38" rx="8"/>'
            f'<text class="{tcls}" x="{x + w // 2}" y="{y + 24}" text-anchor="middle">{label}</text>')


FIG = ('<svg viewBox="0 0 700 300" role="img" aria-label="A typed event bus. Publishers produce CardAuthorized and RefundIssued events, which flow out into the bus. '
       'The bus keys its adapters by KClass of out PaymentEvent. Handlers consume: a CardAuthorized handler, a handler for every PaymentEvent, and a RefundIssued handler. '
       'The general PaymentEvent handler can be subscribed under CardAuthorized because function parameters are in.">'
       '<text class="t-s t-m" x="100" y="24" text-anchor="middle">producers: events go out</text>'
       '<text class="t-s t-m" x="592" y="24" text-anchor="middle">consumers: events go in</text>'
       + box(15, 60, 170, "CardAuthorized", "box-a")
       + box(15, 140, 170, "RefundIssued", "box-a")
       + '<line class="ln-a" x1="187" y1="79" x2="228" y2="100" marker-end="url(#arr)"/>'
         '<line class="ln-a" x1="187" y1="159" x2="228" y2="140" marker-end="url(#arr)"/>'
         '<rect class="box" x="230" y="40" width="240" height="160" rx="8"/>'
         '<text class="t" x="350" y="66" text-anchor="middle">EventBus</text>'
         '<text class="t-s t-code" x="350" y="98" text-anchor="middle">KClass&lt;out PaymentEvent&gt;</text>'
         '<text class="t-s t-m" x="350" y="120" text-anchor="middle">maps to a list of adapters</text>'
         '<text class="t-s t-code" x="350" y="152" text-anchor="middle">type.safeCast(e)?.let(h)</text>'
         '<text class="t-s t-m" x="350" y="176" text-anchor="middle">check, then hand over</text>'
       + '<line class="ln-a" x1="472" y1="90" x2="496" y2="59" marker-end="url(#arr)"/>'
         '<line class="ln-a" x1="472" y1="120" x2="496" y2="119" marker-end="url(#arr)"/>'
         '<line class="ln-a" x1="472" y1="150" x2="496" y2="179" marker-end="url(#arr)"/>'
       + box(500, 40, 185, "(CardAuthorized) -&gt; Unit", "box-b")
       + box(500, 100, 185, "(PaymentEvent) -&gt; Unit", "box-b")
       + box(500, 160, 185, "(RefundIssued) -&gt; Unit", "box-b")
       + '<text class="t-s t-m" x="350" y="240" text-anchor="middle">The (PaymentEvent) -&gt; Unit handler fits under CardAuthorized::class: function parameters are in.</text>'
         '<text class="t-s t-m" x="350" y="262" text-anchor="middle">The keys come from event::class, which is a KClass&lt;out PaymentEvent&gt;.</text>'
         '</svg>')

S1 = """This lesson puts the whole track to work in four small designs. Each one uses a different tool, and the lab asks you to build all four. The first is a result type that is either a failure or a success:

```java
// Java 21: a sealed interface and records. Java has no Nothing, so Left carries an R it never uses.
sealed interface Either<L, R> permits Left, Right {}
record Left<L, R>(L value) implements Either<L, R> {}
record Right<L, R>(R value) implements Either<L, R> {}

static <L, R, R2> Either<L, R2> map(Either<L, R> e, Function<? super R, ? extends R2> f) {
    return switch (e) {
        case Left<L, R> l -> new Left<>(l.value());          // must rebuild: a Left<L, R> is not a Left<L, R2>
        case Right<L, R> r -> new Right<>(f.apply(r.value()));
    };
}
```

```kotlin
sealed interface Either<out L, out R> {
    data class Left<out L>(val value: L) : Either<L, Nothing>
    data class Right<out R>(val value: R) : Either<Nothing, R>
}

fun <L, R, R2> Either<L, R>.map(f: (R) -> R2): Either<L, R2> = when (this) {
    is Either.Left -> this                                 // no rebuild needed
    is Either.Right -> Either.Right(f(value))
}
```

Two tools from this track meet here. `Either` only hands values out, so both parameters are `out` (lesson 4). And `Left` fills the unused side with `Nothing`, the bottom type from lesson 10. Put together, a `Left<String>` is an `Either<String, Nothing>`, and because `Nothing` is a subtype of every type and `R` is `out`, it is also an `Either<String, R2>` for any `R2`. That's why `is Either.Left -> this` type-checks: the same object is a valid result for any success type. Java has neither tool, so its `map` must build a new `Left` every time.

Covariance also makes results compose: an `Either<String, Long>` is an `Either<Any, Number>`, so a function that reports any failure and any numeric result accepts it. Remove the `out`s and almost everything breaks at once, including the `Left` and `Right` declarations themselves: `Type parameter 'L' is declared as 'out' but occurs in 'invariant' position in type 'Either<L (of class Left<out L>), Nothing>'.` A supertype is a position too."""

S2 = """The second design is a repository. A full repository both takes entities (`save`) and returns them (`findAll`, `findById`), so it must be invariant, and an audit job that wants to read *any* repository can't accept a `Repository<Merchant, Long>` as a `Repository<Entity<Long>, Long>`. The fix is to split the interface by variance: put the reading half in its own covariant interface.

```java
interface ReadRepository<T> { List<T> findAll(); }               // Java: invariant, so...

static void printAll(ReadRepository<? extends Entity<?>> repo) {  // ...each reader writes ? extends
    for (Entity<?> e : repo.findAll()) System.out.println("entity " + e.getId());
}
```

```kotlin
interface Entity<ID : Comparable<ID>> { val id: ID }

interface ReadRepository<out T> { fun findAll(): List<T> }      // only hands T out

interface Repository<T : Entity<ID>, ID : Comparable<ID>> : ReadRepository<T> {
    fun save(entity: T): T                                        // takes T in: invariant
    fun findById(id: ID): T?
}

fun printAll(repo: ReadRepository<Entity<*>>) {
    for (e in repo.findAll()) println("entity ${e.id}")
}
```

Now `printAll` accepts a `Repository<Merchant, Long>` and a `Repository<Settlement, String>`, because each one *is* a `ReadRepository` of its entity, and the read side is covariant. The full repository is still invariant, and the compiler still refuses `val anyEntity: Repository<Entity<Long>, Long> = merchants` with `Initializer type mismatch`. Nothing was weakened; the safe half was given its own name.

The bounds are lesson 2's tools: `ID : Comparable<ID>` lets the in-memory implementation keep entities in a `TreeMap` sorted by id, and `T : Entity<ID>` ties each entity to its id type. The Kotlin docs give the same advice for reading and writing dictionaries: split the interface instead of casting. This is interface segregation, done by variance."""

S3 = """The third design is the one in the figure: an event bus for a payment service. Events flow *out* of publishers, and handlers take them *in*. That's lessons 4 and 5 in one class.

```java
final class Router {
    private final List<Consumer<PaymentEvent>> adapters = new ArrayList<>();

    <E extends PaymentEvent> void on(Class<E> type, Consumer<? super E> handler) {   // Consumer Super
        adapters.add(event -> {
            if (type.isInstance(event)) handler.accept(type.cast(event));
        });
    }
}
```

```kotlin
class EventBus {
    private val handlers = HashMap<KClass<out PaymentEvent>, MutableList<(PaymentEvent) -> Unit>>()

    fun <E : PaymentEvent> subscribe(type: KClass<E>, handler: (E) -> Unit) {
        handlers.getOrPut(type) { mutableListOf() }
            .add { event -> type.safeCast(event)?.let(handler) }      // the adapter
    }

    fun publish(event: PaymentEvent) { handlers[event::class]?.forEach { it(event) } }
}
```

Every piece has a reason. The map's keys are `KClass<out PaymentEvent>`, because that's the type of `event::class` (lesson 9). The handler can't go into the list as it is, and the compiler explains why: `Argument type mismatch: actual type is '(E (of fun <E : PaymentEvent> on)) -> Unit', but '(PaymentEvent) -> Unit' was expected.` A function that only takes `CardAuthorized` can't be handed a `RefundIssued`; function parameters are `in`. So the bus stores an adapter that takes any `PaymentEvent`, checks it with `safeCast`, and passes on only an `E`. The same `in` works in your favor at the call site: an audit handler of type `(PaymentEvent) -> Unit` can subscribe under `CardAuthorized::class`.

For Kotlin callers, add the reified wrapper from lesson 8, with one new word:

```java
// Java callers pass the class: bus.subscribe(CardAuthorized.class, e -> fraudCheck(e));
// There is no Java equivalent of the reified, noinline wrapper.
```

```kotlin
inline fun <reified E : PaymentEvent> subscribe(noinline handler: (E) -> Unit) = subscribe(E::class, handler)

bus.subscribe<CardAuthorized> { fraudCheck(it) }
```

A lambda passed to an inline function is normally inlined too, which means it doesn't exist as an object. This one gets stored in the map, so it has to stay an object: `noinline` says so."""

S4 = """The last design is a container for values of many types, the kind of per-payment context a Quarkus request or a Temporal workflow carries around: the accepted currencies, the retry delays, the retry count. Lesson 9's registry used the type as the whole key. Here the key is a small object that carries a name *and* the full type of its value:

```java
record Key<T>(String name, Type type) {                       // Type from a super type token
    static <T> Key<T> of(String name, TypeRef<T> ref) { return new Key<>(name, ref.type); }
}
static final Key<List<String>> CURRENCIES = Key.of("currencies", new TypeRef<List<String>>() {});

<T> void set(Key<T> key, T value) { values.put(key, value); }
@SuppressWarnings("unchecked")
<T> T get(Key<T> key) { return (T) values.get(key); }        // safe: only set puts values in
```

```kotlin
data class Key<T>(val name: String, val type: KType)
inline fun <reified T> key(name: String) = Key<T>(name, typeOf<T>())

val CURRENCIES = key<List<String>>("currencies")

operator fun <T> set(key: Key<T>, value: T) { values[key] = value }
@Suppress("UNCHECKED_CAST")
operator fun <T> get(key: Key<T>): T? = values[key] as T?   // safe: only set puts values in

val currencies: List<String>? = attributes[CURRENCIES]       // no cast, no type argument at the call site
```

The key's type parameter does the typing: `attributes[CURRENCIES]` is a `List<String>?` with no cast at the call site, and `attributes[CURRENCIES] = 42` is a compile error (`Argument type mismatch: actual type is 'Int', but 'List<String>' was expected.`). The `KType` inside the key makes `key<List<Long>>("retries")` and `key<Int>("retries")` different keys, so two teams can't collide by picking the same name.

`Key<T>` is invariant on purpose, and this is the last variance decision of the track. Declare it `out T`, and a `Key<List<String>>` becomes a `Key<Any>`. Then `attributes[currencies] = 42` compiles, with `T` inferred as `Any`, and the next read of the currencies throws `ClassCastException: class java.lang.Integer cannot be cast to class java.util.List`. A key is used to write as well as to read, so it can't be a producer. The one unchecked cast in `get` stays safe only as long as that holds."""

L = {
    "id": "gen-11",
    "title": "Generics workshop: a type-safe container and event bus",
    "minutes": 40,
    "goal": "By the end you can build four small designs that use the whole track: an `Either<out L, out R>` that leans on `Nothing`, a repository with a covariant read view, a typed event bus that stores handlers as adapters, and a container of typed keys that carry a `KType`, and you can say why each type parameter is `out`, `in` or invariant.",
    "warmup": {
        "q": "`sealed interface Either<out L, out R>` with `data class Left<out L>(val value: L) : Either<L, Nothing>`. In `fun <L, R, R2> Either<L, R>.map(f: (R) -> R2): Either<L, R2>`, can the `Left` branch simply return `this`?",
        "options": [
            "No: `this` is an `Either<L, R>`, and the function must return an `Either<L, R2>`",
            "Yes: a `Left<L>` is an `Either<L, Nothing>`, which is an `Either<L, R2>` because `Nothing` is a subtype of `R2` and `R` is `out`",
            "Only with an unchecked cast to `Either<L, R2>`",
            "Only if `R2` is the same type as `R`"
        ],
        "answer": 1,
        "why": "After the smart cast, `this` is a `Left<L>`, whose declared supertype is `Either<L, Nothing>`. With `out R`, `Nothing` below `R2` means `Either<L, Nothing>` is below `Either<L, R2>`. So one `Left` object is a valid result for any success type. Java, with no `Nothing`, has to build a new `Left` in that branch."
    },
    "sections": [
        {
            "h": "Either: two out parameters and Nothing do the work",
            "body": S1,
            "try": {
                "title": "Fold, mapLeft, then remove out",
                "minutes": 4,
                "steps": [
                    "Run `EitherDemo` and `EitherDemoJava`. Compare how `mapLeft` handles the `Right` branch in each.",
                    "In `EitherDemo.kt`, remove both `out`s from `sealed interface Either` (keep the ones on `Left` and `Right`). Predict how many lines break, then run.",
                    "Put the `out`s back."
                ],
                "code": kdemo("EitherDemo", "EitherDemoJava"),
                "expect": "Both print `cents: 1200`, the upper-cased failure (`Left(value=NOT A NUMBER: 12,00)` in Kotlin, `Left[value=...]` for the Java record) and `wider = Right(value=1200)`. Kotlin's `mapLeft` returns `this` for a `Right`; Java builds a new `Right`. Without the `out`s you get six errors: `Left` and `Right` themselves (`Type parameter 'L' is declared as 'out' but occurs in 'invariant' position ...`), `mapLeft`'s `when`, two in `parseCents`, and `Initializer type mismatch: expected 'Either<Any, Number>', actual 'Either<String, Long>'.`"
            },
            "refs": [
                {"title": "Sealed classes and interfaces (Kotlin docs)", "url": "https://kotlinlang.org/docs/sealed-classes.html", "kind": "docs"}
            ]
        },
        {
            "h": "Split reading from writing: a covariant repository view",
            "body": S2,
            "try": {
                "title": "Audit any repository through its read view",
                "minutes": 3,
                "steps": [
                    "Run `RepositoryDemo` (or `RepositoryDemoJava`). One `printAll` reads merchants, settlements and a writable repository.",
                    "Uncomment the wrong move in each file, predict, run.",
                    "Remove `out` from `ReadRepository` in the Kotlin file. Which calls to `printAll` still compile?"
                ],
                "code": kdemo("RepositoryDemo", "RepositoryDemoJava"),
                "expect": "Both print the entities `2`, `7` and `s-1`; Kotlin also prints `entity 9` from the writable repository. The wrong moves fail with `Initializer type mismatch: expected 'Repository<Entity<Long>, Long>', actual 'Repository<Merchant, Long>'.` (the full repository is invariant) and `ReadRepository<Merchant> cannot be converted to ReadRepository<Entity<?>>` in Java (no wildcard on the variable). Without `out`, none of the three `printAll` calls compile."
            }
        },
        {
            "h": "A typed event bus: events flow out, handlers take them in",
            "body": S3,
            "figure": {"svg": FIG, "caption": "Publishers produce events, handlers consume them. The bus keys adapters by the event's class and checks each event before handing it over."},
            "try": {
                "title": "Route events to typed handlers",
                "minutes": 4,
                "steps": [
                    "Run `EventBusDemo` (or `EventBusDemoJava`). The audit handler takes every `PaymentEvent` but is subscribed under `CardAuthorized`.",
                    "Uncomment wrong move 1 inside `Router.on` (comment out the adapter line below it). Read the error.",
                    "Restore it, then uncomment wrong move 2 in `main`. Why is a handler for one subtype refused for the supertype?"
                ],
                "code": kdemo("EventBusDemo", "EventBusDemoJava"),
                "expect": "Both print `fraud check 1200`, `audit pay_1` and `refund 500`. Wrong move 1: `Argument type mismatch: actual type is '(E (of fun <E : PaymentEvent> on)) -> Unit', but '(PaymentEvent) -> Unit' was expected.` Wrong move 2: `Argument type mismatch: actual type is '(CardAuthorized) -> Unit', but '(PaymentEvent) -> Unit' was expected.`: subscribing under `PaymentEvent::class` would hand a `RefundIssued` to a card-only handler."
            }
        },
        {
            "h": "Typed keys: one map, many value types, no casts at the call site",
            "body": S4,
            "try": {
                "title": "Store typed attributes, then break the key",
                "minutes": 4,
                "steps": [
                    "Run `TypedKeysDemo` and `TypedKeysDemoJava`. Neither call site has a cast.",
                    "Read `LeakyKey` in the Kotlin file: the same key with `out T`. Find the line where the bad value goes in, and the line where it fails.",
                    "Uncomment the wrong move in each file. The invariant key stops at compile time what the leaky key let through."
                ],
                "code": kdemo("TypedKeysDemo", "TypedKeysDemoJava"),
                "expect": "Both print `currencies = [EUR, USD], retries = 3`. Kotlin then prints `ClassCastException: class java.lang.Integer cannot be cast to class java.util.List`: `leaky[leakyCurrencies] = 42` compiled because `out T` let `T` be inferred as `Any`, and the read failed later. The wrong move fails with `Argument type mismatch: actual type is 'Int', but 'List<String>' was expected.` in Kotlin and `method set in class Attributes cannot be applied to given types` in Java."
            },
            "refs": [
                {"title": "Reflection: typeOf (Kotlin docs)", "url": "https://kotlinlang.org/docs/reflection.html", "kind": "docs"}
            ]
        }
    ],
    "analogy": "The event bus is a post office sorting room. Letters (events) come in from every counter, which is the producing side. Each pigeonhole is labeled with a letter class, such as \"registered\", and each pigeonhole has clerks assigned to it, which is the consuming side. A clerk trained to handle any letter can be assigned to the registered pigeonhole: that's the `(PaymentEvent) -> Unit` handler under `CardAuthorized::class`. A clerk who only handles registered letters can't be given the general pile, so the office puts a checker in front of him who passes on only registered mail: that's the `safeCast` adapter. The analogy breaks at the checker. A real clerk would notice a wrong letter himself, but a Kotlin lambda can't: if you skip the adapter and cast the handler instead, the wrong event reaches it and fails with a `ClassCastException` inside the handler.",
    "in_your_world": "These four shapes map straight onto a payment service. A Kafka consumer decodes each record and publishes it on an in-process bus, where the fraud check, the ledger writer and the audit log subscribe by event class, and the audit log takes every `PaymentEvent`. Validation of an incoming authorization returns `Either<RejectReason, AuthorizedPayment>` instead of throwing, so a Temporal workflow can branch on it without catching exceptions across the activity boundary. A reporting job that reads merchants and settlements from Oracle takes `ReadRepository<Entity<*>>`, while only the write path sees the invariant `Repository`. And per-request context in a Quarkus endpoint (the merchant id, the accepted currencies, the idempotency key) fits a typed-key container, so `context[IDEMPOTENCY_KEY]` comes back as a `String` with no cast.",
    "mistake": "The common mistake in an event bus is casting the handler instead of wrapping it: `handlers.add(handler as (PaymentEvent) -> Unit)` under `@Suppress(\"UNCHECKED_CAST\")`. It compiles, and every test that publishes the right event type passes. The first time an event of another class reaches that list, through a shared key, a supertype subscription or a bug in the routing, the handler receives it and throws `ClassCastException: class RefundIssued cannot be cast to class CardAuthorized` from inside its own body, far from the subscription that caused it. People write the cast because the adapter looks like extra ceremony, and because erasure makes the cast itself succeed. The fix is the adapter, `{ event -> type.safeCast(event)?.let(handler) }`, which costs one line and makes the wrong event a no-op.",
    "compare": {
        "title": "The typed event bus in Java and Kotlin",
        "java": {
            "title": "EventBus.java",
            "src": "import java.util.ArrayList;\nimport java.util.HashMap;\nimport java.util.List;\nimport java.util.Map;\nimport java.util.function.Consumer;\n\nfinal class EventBus {\n    private final Map<Class<? extends PaymentEvent>, List<Consumer<PaymentEvent>>> handlers = new HashMap<>();\n\n    // Consumer<? super E>: a handler for E or for any supertype of E\n    <E extends PaymentEvent> void subscribe(Class<E> type, Consumer<? super E> handler) {\n        handlers.computeIfAbsent(type, t -> new ArrayList<>()).add(event -> {\n            if (type.isInstance(event)) handler.accept(type.cast(event));   // the adapter\n        });\n    }\n\n    int publish(PaymentEvent event) {\n        List<Consumer<PaymentEvent>> list = handlers.getOrDefault(event.getClass(), List.of());\n        list.forEach(h -> h.accept(event));\n        return list.size();\n    }\n}\n\n// bus.subscribe(CardAuthorized.class, e -> fraudCheck(e));"
        },
        "kotlin": {
            "title": "EventBus.kt",
            "src": "class EventBus {\n    private val handlers = HashMap<KClass<out PaymentEvent>, MutableList<(PaymentEvent) -> Unit>>()\n\n    // (E) -> Unit is already Function1<in E, ...>: a handler for any supertype of E fits\n    fun <E : PaymentEvent> subscribe(type: KClass<E>, handler: (E) -> Unit) {\n        handlers.getOrPut(type) { mutableListOf() }\n            .add { event -> type.safeCast(event)?.let(handler) }           // the adapter\n    }\n\n    inline fun <reified E : PaymentEvent> subscribe(noinline handler: (E) -> Unit) = subscribe(E::class, handler)\n\n    fun publish(event: PaymentEvent): Int {\n        val list = handlers[event::class] ?: return 0\n        for (h in list) h(event)\n        return list.size\n    }\n}\n\n// bus.subscribe<CardAuthorized> { fraudCheck(it) }"
        },
        "note": "The design is the same in both languages: keys from the event's run-time class, handlers stored behind an adapter that checks the class and casts, and a handler parameter that accepts supertypes. Where Java writes the variance at each use (`Class<? extends PaymentEvent>` keys, `Consumer<? super E>` handlers), Kotlin gets it from declarations: `event::class` is already a `KClass<out PaymentEvent>`, and a function type is already `in` on its parameter, so `(E) -> Unit` needs no projection. Kotlin also adds the reified wrapper, which needs `noinline` because the lambda is stored. Java callers can use the `KClass` version only through `JvmClassMappingKt.getKotlinClass(CardAuthorized.class)`, so a bus meant for Java code should also offer a `Class<E>` overload."
    },
    "worked": {
        "title": "Route a card-issuer webhook through all four designs",
        "steps": [
            {"say": "A webhook body arrives. 1. Parse it into an `Either` instead of throwing, so the caller decides what a bad body means.",
             "code": "fun parseWebhook(body: Map<*, *>): Either<String, PaymentEvent> {\n    val id = body[\"id\"] as? String ?: return Either.Left(\"missing id\")\n    val cents = (body[\"cents\"] as? Number)?.toLong() ?: return Either.Left(\"missing cents\")\n    return when (body[\"type\"]) {\n        \"auth\" -> Either.Right(CardAuthorized(id, cents))\n        \"refund\" -> Either.Right(RefundIssued(id, cents))\n        else -> Either.Left(\"unknown type ${body[\"type\"]}\")\n    }\n}",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "static Either<String, PaymentEvent> parseWebhook(Map<?, ?> body) {\n    if (!(body.get(\"id\") instanceof String id)) return new Left<>(\"missing id\");\n    if (!(body.get(\"cents\") instanceof Number n)) return new Left<>(\"missing cents\");\n    long cents = n.longValue();\n    Object type = body.get(\"type\");\n    if (\"auth\".equals(type)) return new Right<>(new CardAuthorized(id, cents));\n    if (\"refund\".equals(type)) return new Right<>(new RefundIssued(id, cents));\n    return new Left<>(\"unknown type \" + type);\n}"},
            {"say": "2. Publish the successes on the bus. 3. Record the failures in the request's typed attributes. Self-check before reading the comment: why can `Either.Right(CardAuthorized(...))` be returned where `Either<String, PaymentEvent>` is expected? (`Right<CardAuthorized>` is an `Either<Nothing, CardAuthorized>`, and both parameters are `out`.)",
             "code": "val LAST_ERROR = key<String>(\"webhook.lastError\")\n\nfun handle(body: Map<*, *>, bus: EventBus, context: Attributes): Int =\n    when (val parsed = parseWebhook(body)) {\n        is Either.Right -> bus.publish(parsed.value)              // events flow out to the handlers\n        is Either.Left -> { context[LAST_ERROR] = parsed.value; 0 }\n    }",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "static final Key<String> LAST_ERROR = Key.of(\"webhook.lastError\", new TypeRef<String>() {});\n\nstatic int handle(Map<?, ?> body, EventBus bus, Attributes context) {\n    return switch (parseWebhook(body)) {\n        case Right<String, PaymentEvent> r -> bus.publish(r.value());\n        case Left<String, PaymentEvent> l -> { context.set(LAST_ERROR, l.value()); yield 0; }\n    };\n}"},
            {"say": "4. Wire the handlers once, at startup. The audit log is a `(PaymentEvent) -> Unit` and subscribes under both event classes; the fraud check only understands card authorizations. A nightly report reads merchants through the covariant `ReadRepository<Entity<*>>` view. Every type parameter in this flow has the variance its role demands, and the only casts are the two that are safe by construction: `safeCast` in the bus adapter and the unchecked cast inside `Attributes.get`.",
             "code": "val auditAll: (PaymentEvent) -> Unit = { audit.write(it.paymentId) }\nbus.subscribe(CardAuthorized::class, auditAll)\nbus.subscribe(RefundIssued::class, auditAll)\nbus.subscribe<CardAuthorized> { fraud.check(it.paymentId, it.cents) }\n\nhandle(mapOf(\"id\" to \"pay_1\", \"cents\" to 1_200, \"type\" to \"auth\"), bus, context)   // 2 handlers ran\nhandle(mapOf(\"id\" to \"pay_2\"), bus, context)                                     // context[LAST_ERROR] == \"missing cents\"",
             "lang": "kotlin",
             "alt_lang": "java",
             "alt_code": "Consumer<PaymentEvent> auditAll = e -> audit.write(e.getPaymentId());\nbus.subscribe(CardAuthorized.class, auditAll);\nbus.subscribe(RefundIssued.class, auditAll);\nbus.subscribe(CardAuthorized.class, e -> fraud.check(e.getPaymentId(), e.getCents()));\n\nhandle(Map.of(\"id\", \"pay_1\", \"cents\", 1_200, \"type\", \"auth\"), bus, context);   // 2 handlers ran\nhandle(Map.of(\"id\", \"pay_2\"), bus, context);                                     // LAST_ERROR is \"missing cents\""}
        ]
    },
    "lab": {
        "title": "Build Either, a repository, an event bus and typed keys",
        "minutes": 16,
        "files": [
            f"{LAB}/main/kotlin/workbench/generics/l11/Either.kt",
            f"{LAB}/main/kotlin/workbench/generics/l11/Repository.kt",
            f"{LAB}/main/kotlin/workbench/generics/l11/EventBus.kt",
            f"{LAB}/main/kotlin/workbench/generics/l11/Attributes.kt",
            f"{LAB}/main/kotlin/workbench/generics/l11/Callers.kt"
        ],
        "run": "./gradlew :generics:test --tests 'workbench.generics.l11.*'",
        "steps": [
            "Run the tests. All thirteen fail. Work through the files in order; each part has its own tests.",
            "`Either.kt` (TODO in two functions): write `map` with `is Either.Left -> this`, and `getOrElse`.",
            "`Repository.kt` (TODOs 1 to 3): add `out` to `ReadRepository`. Back `InMemoryRepository` with a `java.util.TreeMap<ID, T>`. Write `saveAll` and `describeAll`.",
            "`EventBus.kt` (TODOs 4 to 6): store an adapter in `subscribe`, make the one-argument `subscribe` inline with `reified E` and a `noinline` handler, and write `publish` so it returns the number of handlers that ran.",
            "`Attributes.kt` (TODOs 7 and 8): make `key` inline and reified with `typeOf<T>()`, then write `set`, `get`, `getOrDefault` and `remove`. Use `key in values` for `getOrDefault`, so a stored `null` is not mistaken for a missing key.",
            "Run until all thirteen pass. Then remove `out` from `ReadRepository` once more and watch which test turns red."
        ],
        "hints": [
            "`TreeMap` works as `byId[entity.id] = entity`, and `byId.values.toList()` is already in id order.",
            "The adapter is `handlers.getOrPut(type) { mutableListOf() }.add { event -> type.safeCast(event)?.let(handler) }`. `safeCast` needs `import kotlin.reflect.safeCast`.",
            "`publish`: `val list = handlers[event::class] ?: return 0`, then call each and return `list.size`.",
            "Each unchecked cast in `Attributes` needs `@Suppress(\"UNCHECKED_CAST\")`. Write one comment saying why it's safe: only `set(key: Key<T>, value: T)` puts values in, and `Key` is invariant."
        ],
        "done_when": "All thirteen tests in `WorkshopTest` pass."
    },
    "drill": {
        "title": "Write Either and map from memory",
        "minutes": 5,
        "prompt": "Close this page. Write `Either` with `Left` and `Right` in Kotlin, with the variance and the `Nothing` that let `map` return `this` for a `Left`. Write `map`. Then write the Java version with a sealed interface and records, and point at the line where Java has to build a new object.",
        "answer": {
            "lang": "kotlin",
            "src": "sealed interface Either<out L, out R> {\n    data class Left<out L>(val value: L) : Either<L, Nothing>\n    data class Right<out R>(val value: R) : Either<Nothing, R>\n}\n\nfun <L, R, R2> Either<L, R>.map(f: (R) -> R2): Either<L, R2> = when (this) {\n    is Either.Left -> this                      // Either<L, Nothing> is an Either<L, R2>\n    is Either.Right -> Either.Right(f(value))\n}",
            "alt": {"lang": "java", "title": "Either.java", "src": "sealed interface Either<L, R> permits Left, Right {}\nrecord Left<L, R>(L value) implements Either<L, R> {}\nrecord Right<L, R>(R value) implements Either<L, R> {}\n\nstatic <L, R, R2> Either<L, R2> map(Either<L, R> e, Function<? super R, ? extends R2> f) {\n    return switch (e) {\n        case Left<L, R> l -> new Left<>(l.value());          // here: no Nothing, so a new Left\n        case Right<L, R> r -> new Right<>(f.apply(r.value()));\n    };\n}"}
        }
    },
    "recap": [
        "`Either<out L, out R>` with `Left : Either<L, Nothing>` lets one `Left` stand for every success type, so `map` can return `this`. Java must rebuild it.",
        "When a type both reads and writes `T`, split out the reading half as an `out T` interface. Readers get covariance; the full type stays invariant and safe.",
        "In an event bus, events are produced and handlers consume. Keys are `KClass<out PaymentEvent>` from `event::class`, and handlers are stored behind a `safeCast` adapter.",
        "A reified wrapper that stores its lambda needs `noinline`.",
        "A typed key carries its value type (`Key<T>` with a `KType` inside), so reads need no cast and same-named keys of different types don't collide.",
        "A key is used to write, so it must be invariant. With `out T`, a wrong value goes in and fails later as a `ClassCastException`."
    ],
    "quiz": [
        {
            "q": "Which interface can safely be declared with `out T`?",
            "options": [
                "`interface Repository<T> { fun save(entity: T): T }`",
                "`interface Cache<T> { var current: T }`",
                "`interface ReadRepository<T> { fun findAll(): List<T> }`",
                "`interface Key<T> { val name: String }`, used as `set(key: Key<T>, value: T)`"
            ],
            "answer": 2,
            "why": "`ReadRepository` only hands `T` out. `save` takes a `T`, and a `var` is both read and written, so those must be invariant. The key is the subtle one: it has no `T` member at all, so `out T` would compile, but it is used to choose what may be written, and `out` would let `set(key, 42)` through."
        },
        {
            "q": "In the event bus, why can't `subscribe` simply do `handlers[type]!!.add(handler)` with `handler: (E) -> Unit` and a list of `(PaymentEvent) -> Unit`?",
            "options": [
                "Because lambdas can't be stored in a map",
                "Because `(E) -> Unit` is not a `(PaymentEvent) -> Unit`: function parameters are `in`, and a card-only handler can't take a refund",
                "Because `E` is erased, so the list can't hold it",
                "It can; the adapter is only for performance"
            ],
            "answer": 1,
            "why": "A `(PaymentEvent) -> Unit` must accept every event. A handler that only takes `CardAuthorized` doesn't, so the compiler refuses the add. The adapter takes any event and passes on only those that `safeCast` to `E`. The reverse direction works: a `(PaymentEvent) -> Unit` handler is a `(CardAuthorized) -> Unit`."
        },
        {
            "q": "Why does the reified `subscribe` need `noinline` on its handler parameter?",
            "options": [
                "Because reified functions can't take lambdas",
                "Because Java callers need it",
                "Because the handler is stored in the map, so it must exist as an object instead of being inlined",
                "Because `noinline` makes the type parameter reified"
            ],
            "answer": 2,
            "why": "Lambdas passed to an inline function are inlined too, so they don't exist as values. A lambda you store, return or pass on to a non-inline function must stay an object, which `noinline` requests. It has nothing to do with `reified`, which is about the type parameter."
        },
        {
            "q": "`data class Key<T>(val name: String, val type: KType)`. Why include the `KType` when the key already has a name?",
            "options": [
                "So that `key<List<Long>>(\"retries\")` and `key<Int>(\"retries\")` are different keys and can't collide",
                "Because a data class needs at least two properties",
                "So that `get` can cast without an unchecked warning",
                "Because `KType` makes the key covariant"
            ],
            "answer": 0,
            "why": "With the name alone, two keys with the same name and different value types would share one slot, and reading one would return the other's value. The `KType` from `typeOf<T>()` makes them unequal. The cast in `get` is still unchecked; it is safe because only `set` puts values in."
        },
        {
            "q": "From \"Star projection: when you don't know the type\": a metrics helper reports the size of any in-memory buffer, a `MutableList<CardAuthorized>`, a `MutableList<String>` or anything else. Which parameter type fits best?",
            "options": [
                "`MutableList<Any?>`",
                "`MutableList<in Any>`",
                "`MutableList<PaymentEvent>`",
                "`MutableList<*>`"
            ],
            "answer": 3,
            "why": "The helper neither reads typed elements nor writes any, so a star projection says exactly that and accepts every mutable list. `MutableList<Any?>` accepts only lists whose element type is exactly `Any?`, and `in Any` accepts only lists of `Any` or `Any?`. (A plain `Collection<*>` would be even more general.)",
            "from": "gen-07"
        }
    ],
    "flashcards": [
        {"front": "Why is `Left` declared `Left<out L>(val value: L) : Either<L, Nothing>`?", "back": "So one `Left` fits `Either<L, R>` for every `R`: `Nothing` is a subtype of every type, and `Either` is `out` in `R`."},
        {"front": "A repository both saves and returns `T`. How do you let read-only code accept a repository of any entity?", "back": "Split out `interface ReadRepository<out T> { fun findAll(): List<T> }` and have the full `Repository` extend it. Readers take `ReadRepository<Entity<*>>`."},
        {"front": "What type do the keys of a class-keyed event bus have, and why?", "back": "`KClass<out PaymentEvent>`, because `event::class` on a `PaymentEvent` has exactly that type."},
        {"front": "How do you store a `(CardAuthorized) -> Unit` in a list of `(PaymentEvent) -> Unit`?", "back": "Wrap it: `{ event -> CardAuthorized::class.safeCast(event)?.let(handler) }`. The adapter takes any event and passes on only a `CardAuthorized`."},
        {"front": "When does a lambda parameter of an inline function need `noinline`?", "back": "When the function stores it, returns it or passes it to non-inline code, as `subscribe` does with its handler map."},
        {"front": "Why must a typed `Key<T>` be invariant?", "back": "It decides what may be written. With `out T`, a `Key<List<String>>` could act as a `Key<Any>`, `set(key, 42)` would compile, and the next read would throw `ClassCastException`."}
    ],
    "terms": [
        {"term": "Either", "plain": "A result that is a failure (`Left`) or a success (`Right`), declared `out` in both."},
        {"term": "Interface segregation by variance", "plain": "Splitting a type's reading half into its own covariant interface, so readers get flexibility the full type can't have."},
        {"term": "Adapter", "plain": "A small wrapper that turns one function type into another, here by checking the event's class first."},
        {"term": "noinline", "plain": "Marks a lambda parameter of an inline function that must stay an object, because it is stored."},
        {"term": "Typed key", "plain": "A key object that carries the type of its value, so a container can return that type without casts."},
        {"term": "Safe by construction", "plain": "An unchecked cast that can't fail, because a private invariant guarantees what was stored."}
    ],
    "explain_back": {
        "prompt": "A teammate reviews the lab's `EventBus` and asks two things: why the bus wraps every handler in a lambda instead of storing it directly, and why the audit handler, typed `(PaymentEvent) -> Unit`, can subscribe under `CardAuthorized::class`. Explain both with the producer and consumer picture.",
        "answer": "Events are produced by publishers and consumed by handlers, so a handler's type is `in` on its parameter. That gives both answers. A handler typed `(CardAuthorized) -> Unit` can only consume card authorizations, so it is not a `(PaymentEvent) -> Unit`, which must consume any event. The bus keeps one list of `(PaymentEvent) -> Unit` per class, so it can't store the card handler as it is. It stores an adapter instead: a function that takes any `PaymentEvent`, checks it with `CardAuthorized::class.safeCast`, and passes it on only if it really is a card authorization. Casting the handler would compile but fail with a `ClassCastException` inside the handler the first time a wrong event arrived. The audit handler goes the other way. It consumes every `PaymentEvent`, so it can certainly consume card authorizations: because the parameter is `in`, a `(PaymentEvent) -> Unit` is a `(CardAuthorized) -> Unit`, and `subscribe(CardAuthorized::class, auditAll)` type-checks with `E = CardAuthorized`."
    },
    "deeper": {
        "minutes": 10,
        "body": "Each design has a natural next step.\n\nThe bus delivers only to the event's exact class. To deliver a `CardAuthorized` to handlers subscribed under `PaymentEvent::class` too, `publish` must walk the event's supertypes. Without kotlin-reflect you can do that through Java reflection: `event.javaClass.interfaces` and `event.javaClass.superclass`, converted with `.kotlin`. With kotlin-reflect, `KClass.allSuperclasses` lists them directly. Cache the result per class, since the walk is the same every time.\n\n`Either` gets more useful with `flatMap`, which chains steps that can each fail: `fun <L, R, R2> Either<L, R>.flatMap(f: (R) -> Either<L, R2>): Either<L, R2>`. Its `Left` branch returns `this` for the same reason `map` can. The standard library's own `Result<out T>` is also declared `out`, but its failure side is always a `Throwable`; `Either` lets the failure be a domain type such as `RejectReason`. Libraries such as Arrow ship a full `Either`.\n\nThe repository can grow a write-only view too: `interface WriteRepository<in T> { fun save(entity: T) }`. A loader that writes `Merchant`s can then accept a `WriteRepository<Entity<Long>>`. With both views, the invariant `Repository` is simply the type that is both.\n\nThe typed keys can carry a default: `class Key<T>(val name: String, val type: KType, val default: T)`, with `get` returning `T` instead of `T?`. Keep `Key` invariant when you do: `default` is read, but `set` still writes through the key."
    },
    "sources": [
        {"title": "Generics: variance, in and out (Kotlin docs)", "url": "https://kotlinlang.org/docs/generics.html"},
        {"title": "Reflection (Kotlin docs)", "url": "https://kotlinlang.org/docs/reflection.html"},
        {"title": "Inline functions: noinline (Kotlin docs)", "url": "https://kotlinlang.org/docs/inline-functions.html"},
        {"title": "Sealed classes and interfaces (Kotlin docs)", "url": "https://kotlinlang.org/docs/sealed-classes.html"}
    ]
}

out = ROOT / "content/lessons/gen-11.json"
out.write_text(json.dumps(L, indent=2, ensure_ascii=False) + "\n")
print("wrote", out)
