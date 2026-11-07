import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
LAB = "labs/generics/src"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :generics:demo -Pmain="
PKG = "workbench.generics.l05.demo"


def kdemo(name, alt=None):
    path = f"{LAB}/demo/kotlin/workbench/generics/l05/demo/{name}.kt"
    d = {"lang": "kotlin", "title": f"{name}.kt", "src": read(path), "run": f"{RUN}{PKG}.{name}Kt", "file": path}
    if alt:
        d["alt"] = jdemo(alt)
    return d


def jdemo(name):
    path = f"{LAB}/demo/java/workbench/generics/l05/demo/{name}.java"
    return {"lang": "java", "title": f"{name}.java", "src": read(path), "run": f"{RUN}{PKG}.{name}", "file": path}


def box(x, y, w, label, cls="box"):
    return (f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="38" rx="8"/>'
            f'<text class="t-s t-code" x="{x + w // 2}" y="{y + 24}" text-anchor="middle">{label}</text>')


FIG = (
    '<svg viewBox="0 0 700 280" role="img" aria-label="CardAuthorized is a subtype of PaymentEvent. For a producer declared out, the arrow keeps its direction: Source of CardAuthorized is a Source of PaymentEvent. '
    'For a consumer declared in, the arrow flips: Sink of PaymentEvent is a Sink of CardAuthorized.">'
    '<text class="t-s t-m" x="105" y="18" text-anchor="middle">element types</text>'
    '<text class="t-s t-m" x="340" y="18" text-anchor="middle">producer: out keeps it</text>'
    '<text class="t-s t-m" x="580" y="18" text-anchor="middle">consumer: in flips it</text>'
    + box(20, 32, 170, "PaymentEvent")
    + box(20, 200, 170, "CardAuthorized", "box-a")
    + '<line class="ln-a" x1="105" y1="200" x2="105" y2="72" marker-end="url(#arr)"/>'
    + box(235, 32, 210, "Source&lt;PaymentEvent&gt;")
    + box(235, 200, 210, "Source&lt;CardAuthorized&gt;", "box-a")
    + '<line class="ln-a" x1="340" y1="200" x2="340" y2="72" marker-end="url(#arr)"/>'
    + box(480, 32, 200, "Sink&lt;CardAuthorized&gt;")
    + box(480, 200, 200, "Sink&lt;PaymentEvent&gt;", "box-b")
    + '<line class="ln-a" x1="580" y1="200" x2="580" y2="72" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="113" y="140">is a</text>'
    '<text class="t-s t-m" x="348" y="140">is a</text>'
    '<text class="t-s t-m" x="588" y="140">is a</text>'
    '<text class="t-s t-m" x="350" y="262" text-anchor="middle">A sink that takes any event can stand in for a sink that only needs card authorizations.</text>'
    '</svg>'
)

S1 = """A **consumer** is a type whose values of `T` only ever go in. An audit log, a Kafka producer, a metrics counter, a `Comparator`, an event handler. You hand it a `T`, and it hands nothing typed `T` back.

Run the substitution test again, the other way round. Some code needs a sink for card authorizations. You hand it an audit log that accepts *any* payment event. Every call it can make passes a `CardAuthorized`, and the audit log takes every `PaymentEvent`, so it takes those too. Nothing can go wrong.

So for a consumer, the more general type is the one that can stand in. A `Sink<PaymentEvent>` can be used where a `Sink<CardAuthorized>` is expected. The subtype arrow **flips**. This is **contravariance**, and Kotlin declares it with **`in`**. Java writes it at each use with **`? super`**:

```java
interface Sink<T> {
    void accept(T item);
}

static void forwardAuthorizations(List<CardAuthorized> events, Sink<? super CardAuthorized> to) { ... }

Sink<PaymentEvent> audit = e -> System.out.println("audit: " + e.getPaymentId());
forwardAuthorizations(auths, audit);           // fine: the parameter says ? super
Sink<CardAuthorized> strict = audit;           // error: Sink<PaymentEvent> cannot be converted to Sink<CardAuthorized>
```

```kotlin
interface Sink<in T> {
    fun accept(item: T)
}

fun forwardAuthorizations(events: List<CardAuthorized>, to: Sink<CardAuthorized>) { ... }

val audit: Sink<PaymentEvent> = AuditLog()
forwardAuthorizations(auths, audit)            // fine: Sink is declared in
val cardSink: Sink<CardAuthorized> = audit     // also fine
```

The other direction fails, and it should. A `Sink<CardAuthorized>` might be a fraud checker that reads `cents`. Handing it a `RefundIssued` through a `Sink<PaymentEvent>` view would break it:

```text
error: initializer type mismatch: expected 'Sink<PaymentEvent>', actual 'Sink<CardAuthorized>'.
```

The position rules are the mirror image of `out`. In a type declared `in T`, `T` may appear in parameters, and not in return types or `val`s. Add `fun last(): T` to `Sink` and the compiler says `type parameter 'T' is declared as 'in' but occurs in 'out' position`. The reason mirrors lesson 4. Through a `Sink<CardAuthorized>` view of the audit log, `last()` would promise a `CardAuthorized`, and the log may be holding a `RefundIssued`.

The figure shows the two cases next to each other. Same element types, same "is a" arrow between them. A producer keeps the direction. A consumer reverses it."""

S2 = """You already use the most common consumer: a comparator. A comparator only *takes* values, two at a time, and returns an `Int`. So a comparator written for a supertype works for every subtype:

```java
Comparator<PaymentEvent> byId = Comparator.comparing(PaymentEvent::getPaymentId);

List<CardAuthorized> auths = new ArrayList<>(...);
auths.sort(byId);                                    // List<E>.sort(Comparator<? super E>)

Comparator<? super CardAuthorized> forCards = byId;  // fine
Comparator<CardAuthorized> strict = byId;            // error: Comparator<PaymentEvent> cannot be converted to Comparator<CardAuthorized>
```

```kotlin
val byId: Comparator<PaymentEvent> = compareBy { it.paymentId }

val auths = listOf(CardAuthorized("pay_3", 1_200), CardAuthorized("pay_1", 350))
auths.sortedWith(byId)                               // sortedWith(comparator: Comparator<in T>)

val forCards: Comparator<in CardAuthorized> = byId   // fine
val strict: Comparator<CardAuthorized> = byId        // error: expected 'Comparator<CardAuthorized>', actual 'Comparator<PaymentEvent>'
```

The last line surprises Kotlin developers. On the JVM, Kotlin's `Comparator` is `java.util.Comparator`, a Java interface, and Java interfaces have no declared variance. So Kotlin treats `Comparator` as invariant, exactly as Java does. The flexibility comes from the use site: the standard library declares `sortedWith(comparator: Comparator<in T>)`, the Kotlin spelling of Java's `? super T`.

The JDK made the same choice everywhere. `List.sort`, `Collections.sort`, `Stream.sorted` and the `TreeMap` constructor all take a `Comparator<? super E>`. If you write your own ranking helper and forget the projection, it accepts only a comparator of the exact element type, and the shared `byPaymentId` comparator that the rest of the codebase uses no longer fits.

Kotlin's own `Comparable` is different. It is declared `interface Comparable<in T>`, so the `in` is on the declaration. That is why lesson 2 of this track could call `maxOf2` on `LocalDate`, which is a `Comparable<ChronoLocalDate>`: a `Comparable<ChronoLocalDate>` is a `Comparable<LocalDate>`.

The rule of thumb for your own signatures: when a parameter is a comparator, a handler, a sink or a callback that *receives* your values, give it `in` (Kotlin) or `? super` (Java). The lab's `highest(items: List<T>, comparator: Comparator<in T>)` is the shape to copy."""

S3 = """Function types are where producers and consumers meet. `(P) -> R` is `Function1<in P, out R>`: a function consumes its parameter and produces its result. So a function type is contravariant on the left of the arrow and covariant on the right:

```java
// Java's Consumer and Function are plain invariant interfaces, so say it at the use site:
Consumer<PaymentEvent> auditAll = e -> System.out.println("audit " + e.getPaymentId());
Function<PaymentEvent, String> describe = e -> "event " + e.getPaymentId();

Consumer<? super CardAuthorized> onCard = auditAll;                       // fine
Function<? super CardAuthorized, ? extends Object> label = describe;      // fine
Consumer<CardAuthorized> strict = auditAll;     // error: cannot be converted
```

```kotlin
val auditAll: (PaymentEvent) -> Unit = { println("audit ${it.paymentId}") }
val describe: (PaymentEvent) -> String = { "event ${it.paymentId}" }

val onCard: (CardAuthorized) -> Unit = auditAll       // fine: takes more general input
val label: (CardAuthorized) -> Any = describe         // fine: in on the left, out on the right
val tooBroad: (PaymentEvent) -> Unit = onCard         // error: expected '(PaymentEvent) -> Unit', actual '(CardAuthorized) -> Unit'
```

This is why the lab's `Dispatcher<CardAuthorized>` accepts a handler written for every `PaymentEvent` without any extra work.

Function types also explain the odd cases from lesson 4 of this track. Follow the value. In `fun each(f: (T) -> Unit)`, the class calls `f` and hands it a `T`, so the `T` travels out of the class, even though it sits inside a parameter. In `fun handler(): (T) -> Unit`, the class hands a function to the caller, and the caller feeds it a `T`, so the `T` travels in. To get the same answer without tracing, give each position a sign: an out-position is `+`, an in-position is `−`. When one type sits inside another, multiply the signs. A plain parameter is `−`. The parameter of a function that is itself a parameter is `−` times `−`, which is `+`.

| Member in `class C<…T>` | Where `T` sits | Sign | Legal under `out T` | Legal under `in T` |
|---|---|---|---|---|
| `fun get(): T` | return | + | yes | no |
| `fun put(t: T)` | parameter | − | no | yes |
| `fun each(f: (T) -> Unit)` | parameter of a parameter | − × − = + | yes | no |
| `fun handler(): (T) -> Unit` | parameter of the result | + × − = − | no | yes |
| `fun putAll(xs: List<T>)` | `List<out E>` in a parameter | − × + = − | no | yes |

You won't run this table often. Use it when an error points at a callback and the intuition stops helping. The `Inbox` interface in the demo has three members to test it on."""

S4 = """Java programmers learn variance as **PECS**: Producer Extends, Consumer Super. It comes from *Effective Java* (Item 31), and the Kotlin docs cite it as the background for `out` and `in`. The mapping is one to one:

| Role of the parameter | Java | Kotlin |
|---|---|---|
| gives you `T` values (producer) | `? extends T` | `out T` |
| takes `T` values from you (consumer) | `? super T` | `in T` |
| both | `T` | `T` |

The JDK's copy method is the textbook case. `src` produces, `dest` consumes:

```java
// java.util.Collections:
// public static <T> void copy(List<? super T> dest, List<? extends T> src)

static <T> void copyInto(List<? extends T> from, List<? super T> to) {
    for (T x : from) to.add(x);
}

copyInto(List.of(1_200, 350), numbers);       // List<Integer> into a List<Number>
copyInto(numbers, new ArrayList<Integer>());  // error: method copyInto cannot be applied to given types
```

```kotlin
fun <T> copyInto(from: List<T>, to: MutableList<in T>) {
    for (x in from) to.add(x)
}

copyInto(listOf(1_200, 350), numbers)         // List<Int> into a MutableList<Number>
copyInto(numbers, mutableListOf<Int>())       // error: actual type is 'MutableList<Int>', but 'MutableList<in Number>' was expected
```

The Kotlin version needs only one projection, on `to`. `from` is a `List`, which is already `out`, so writing `List<out T>` would only earn a warning that the projection is redundant.

When you design a signature, ask one question per parameter: does this parameter *give* me values of `T`, *take* values of `T` from me, or both? Give: `out` / `? extends`. Take: `in` / `? super`. Both: plain `T`. The wrong answer is rarely a compile error in your own code. It shows up later, as a caller who can't pass a perfectly good `Comparator<PaymentEvent>` and writes a cast to get around you.

`MutableList<in T>` is a use-site projection: `MutableList` itself is invariant, and the function asks for a write-only view of it. Lesson 6 of this track is about those."""

L = {
    "id": "gen-05",
    "title": "Contravariance with in: consumers",
    "minutes": 35,
    "goal": "By the end you can recognise a consumer, declare it `in` in Kotlin (or write `? super` in Java), explain why a `Sink<PaymentEvent>` can stand in for a `Sink<CardAuthorized>`, and choose `out` or `in` for any parameter with the PECS question.",
    "warmup": {
        "q": "`val audit: Sink<PaymentEvent>` accepts any payment event. A function needs a `Sink<CardAuthorized>`. If `Sink` were declared `interface Sink<in T> { fun accept(item: T) }`, could you pass `audit`?",
        "options": [
            "No: PaymentEvent is the supertype, so it can never stand in for the subtype",
            "Yes: a sink that takes every event also takes card authorizations",
            "Only with a cast",
            "Only if `Sink` is declared `out T`"
        ],
        "answer": 1,
        "why": "For a consumer the arrow flips. The function will only ever pass `CardAuthorized` values in, and a sink of any `PaymentEvent` accepts all of them. `in` tells the compiler that `T` only flows in. `out` would be wrong: a sink doesn't produce."
    },
    "sections": [
        {
            "h": "A consumer only takes values in",
            "body": S1,
            "figure": {"svg": FIG, "caption": "Producers keep the subtype arrow (out). Consumers flip it (in): the sink for the general type stands in for the sink for the specific one."},
            "try": {
                "title": "Pass a general sink where a specific one is needed",
                "minutes": 4,
                "steps": [
                    "Run `SinkDemo` (or `SinkDemoJava`). Every authorization goes through the audit log.",
                    "Predict: does the wrong move at the bottom compile? Uncomment it and run.",
                    "In `SinkDemo.kt`, remove `in` from `interface Sink<in T>` and run again. Which line breaks now? Put it back."
                ],
                "code": kdemo("SinkDemo", "SinkDemoJava"),
                "expect": "Both print `audit: pay_1`, `audit: pay_2`, `audit: pay_3`. The wrong move fails: `Initializer type mismatch: expected 'Sink<PaymentEvent>', actual 'Sink<CardAuthorized>'.` in Kotlin and `Sink<PaymentEvent> cannot be converted to Sink<CardAuthorized>` in Java. Without `in`, Kotlin rejects both `forwardAuthorizations(..., audit)` and `val cardSink: Sink<CardAuthorized> = audit`: an invariant `Sink` behaves like Java's plain `Sink<T>`."
            }
        },
        {
            "h": "Comparator: one ordering for many types",
            "body": S2,
            "try": {
                "title": "Sort two kinds of event with one comparator",
                "minutes": 3,
                "steps": [
                    "Run `ComparatorDemo` (or `ComparatorDemoJava`). One `Comparator<PaymentEvent>` sorts both lists.",
                    "Uncomment the `strict` line and run. Then change its type to `Comparator<in CardAuthorized>` (Java: `Comparator<? super CardAuthorized>`) and run again."
                ],
                "code": kdemo("ComparatorDemo", "ComparatorDemoJava"),
                "expect": "Both print `[pay_1, pay_3]`, `[pay_4, pay_9]` and `forCards compares: 2`. The strict line fails in both languages: `expected 'Comparator<CardAuthorized>', actual 'Comparator<PaymentEvent>'` and `Comparator<PaymentEvent> cannot be converted to Comparator<CardAuthorized>`. `java.util.Comparator` is invariant on the JVM, even in Kotlin; the use-site `in` or `? super` fixes it."
            }
        },
        {
            "h": "Function types: in on the left, out on the right",
            "body": S3,
            "try": {
                "title": "Assign handlers, then test the sign rule",
                "minutes": 5,
                "steps": [
                    "Run `HandlerDemo` (or `HandlerDemoJava`) and uncomment the wrong move(s). Read the errors.",
                    "In `HandlerDemo.kt`, look at the `Inbox<in T>` interface. Use the sign table to predict which of the three numbered members compile.",
                    "Uncomment them one at a time and run to check your predictions."
                ],
                "code": kdemo("HandlerDemo", "HandlerDemoJava"),
                "expect": "The demo prints `audit pay_7` and `event pay_8`. `tooBroad` fails with `expected '(PaymentEvent) -> Unit', actual '(CardAuthorized) -> Unit'`; the Java twin's strict lines fail with `Consumer<PaymentEvent> cannot be converted to Consumer<CardAuthorized>` and `Function<PaymentEvent,String> cannot be converted to Function<CardAuthorized,Object>`. All three `Inbox` members fail with `declared as 'in' but occurs in 'out' position`: `peek(): T` is a return (+), and the `T` inside `(T) -> Unit` and `(T) -> Boolean` parameters is − × − = +."
            }
        },
        {
            "h": "PECS is out and in with Java spelling",
            "body": S4,
            "try": {
                "title": "Copy from a producer into a consumer",
                "minutes": 3,
                "steps": [
                    "Run `PecsDemo` (or `PecsDemoJava`). Both copy a list of ints into a list of numbers and a list of anything.",
                    "Uncomment the wrong move and run. Say in one sentence why copying numbers into a list of ints must fail."
                ],
                "code": kdemo("PecsDemo", "PecsDemoJava"),
                "expect": "Both print `numbers = [2.5, 1200, 350], anything = [EUR, 1200, 350]`, and Java also prints `slots = [1200, 350]` from `Collections.copy`. The wrong move fails with `actual type is 'MutableList<Int>', but 'MutableList<in Number>' was expected` (Kotlin) or `method copyInto ... cannot be applied to given types` (Java): a list of ints can't take the `2.5` that the source holds."
            },
            "refs": [
                {"title": "Collections.copy (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/Collections.html", "kind": "docs"}
            ]
        }
    ],
    "analogy": "A consumer is a recycling bin. A bin labeled \"any recyclables\" can stand in for a bin labeled \"glass only\": everyone who was going to drop glass into it still can. The reverse fails: if you hand out a glass-only bin as an \"any recyclables\" bin, someone drops cardboard in. So the bin with the wider label is the one that substitutes, which is the flip that `in` describes. The analogy breaks when you take things out: a real bin can be emptied and its contents inspected, but a `Sink<PaymentEvent>` seen as a `Sink<CardAuthorized>` gives you nothing typed back. Contravariant types are for putting values in, not for reading them.",
    "in_your_world": "Consumers are everywhere on the write side of a payment service: a Kafka producer wrapper that sends `PaymentEvent`s, an audit log, a metrics recorder, a `Comparator` that orders settlement lines, a Temporal activity callback, a handler registered on an event bus. Declare your own consumer interfaces `in T`, and one audit sink or one `(PaymentEvent) -> Unit` handler can be wired into every typed pipeline (`Sink<CardAuthorized>`, `Sink<RefundIssued>`) without adapters. In Java code you'll see the same contract as `Consumer<? super T>` and `Comparator<? super T>` in well-designed APIs.",
    "mistake": "The common mistake is writing a consumer parameter as plain `T`: `fun register(handler: Comparator<CardAuthorized>)` in Kotlin or `void register(Consumer<CardAuthorized> handler)` in Java. It compiles and works for the first caller. The second caller has a perfectly good `Comparator<PaymentEvent>` or `Consumer<PaymentEvent>` and gets a type mismatch, then writes a lambda adapter or a cast. People make the mistake because the plain type looks simpler and Kotlin's own `Comparator` is invariant on the JVM. The fix is to ask the PECS question for every parameter: if it only receives your values, write `Comparator<in T>` / `Consumer<? super T>`.",
    "compare": {
        "title": "A consumer, declared once in Kotlin, spelled at each use in Java",
        "java": {
            "title": "Sinks.java",
            "src": "import java.util.Comparator;\nimport java.util.List;\nimport java.util.function.Consumer;\n\ninterface Sink<T> {                          // no declaration-site variance in Java\n    void accept(T item);\n}\n\nclass Sinks {\n    // every consumer parameter must remember ? super\n    static <T> void feedAll(List<? extends T> items, Sink<? super T> sink) {\n        for (T item : items) sink.accept(item);\n    }\n\n    static <T> T highest(List<? extends T> items, Comparator<? super T> order) {\n        T best = items.get(0);\n        for (T item : items) if (order.compare(item, best) > 0) best = item;\n        return best;\n    }\n\n    static <E> void subscribe(Consumer<? super E> handler) { /* store it */ }\n}"
        },
        "kotlin": {
            "title": "Sinks.kt",
            "src": "interface Sink<in T> {                       // say it once\n    fun accept(item: T)\n}\n\n// Sink and List carry their variance, so these signatures stay plain\nfun <T> feedAll(items: List<T>, sink: Sink<T>) {\n    for (item in items) sink.accept(item)\n}\n\n// java.util.Comparator is a Java interface: invariant, so project it here\nfun <T> highest(items: List<T>, order: Comparator<in T>): T {\n    var best = items[0]\n    for (item in items) if (order.compare(item, best) > 0) best = item\n    return best\n}\n\n// function types are already Function1<in P, out R>\nfun <E> subscribe(handler: (E) -> Unit) { /* store it */ }"
        },
        "note": "The rule is identical: through a contravariant view you may put values in but get nothing typed back out. Java puts `? super` on every consumer parameter; Kotlin puts `in` on the consumer's declaration once, and its function types are contravariant in their parameters out of the box. The one trap is Java interfaces used from Kotlin. `Comparator`, `Consumer` and every other Java interface have no declared variance, so Kotlin treats them as invariant and you need a use-site `in` (`Comparator<in T>`), exactly where Java needs `? super T`. When Java calls Kotlin, a parameter of type `Sink<PaymentEvent>` shows up as `Sink<? super PaymentEvent>`."
    },
    "worked": {
        "title": "Design a dispatcher that accepts general handlers",
        "steps": [
            {"say": "A payment service publishes `CardAuthorized` events. The fraud team writes a handler for card authorizations. The audit team writes one handler for every `PaymentEvent`. You want both to subscribe to the same dispatcher. Start by naming the role of each type: the event is produced by the dispatcher and consumed by the handler.", "code": "interface PaymentEvent { val paymentId: String }\ndata class CardAuthorized(override val paymentId: String, val cents: Long) : PaymentEvent\n\nval fraudCheck: (CardAuthorized) -> Unit = { check(it.cents) }\nval auditAll: (PaymentEvent) -> Unit = { log(it.paymentId) }", "lang": "kotlin",
             "alt_lang": "java", "alt_code": "interface PaymentEvent { String paymentId(); }\nrecord CardAuthorized(String paymentId, long cents) implements PaymentEvent {}\n\nConsumer<CardAuthorized> fraudCheck = e -> check(e.cents());\nConsumer<PaymentEvent> auditAll = e -> log(e.paymentId());"},
            {"say": "1. Write the subscribe signature with the handler as a consumer of `E`. In Kotlin a function type already has `in` on its parameter, so `(E) -> Unit` is enough. In Java, `Consumer<E>` would reject the audit handler, so write `Consumer<? super E>`.", "code": "class Dispatcher<E> {\n    private val handlers = ArrayList<(E) -> Unit>()\n\n    fun subscribe(handler: (E) -> Unit) { handlers.add(handler) }\n\n    fun publish(event: E): Int {\n        for (h in handlers) h(event)\n        return handlers.size\n    }\n}", "lang": "kotlin",
             "alt_lang": "java", "alt_code": "class Dispatcher<E> {\n    private final List<Consumer<? super E>> handlers = new ArrayList<>();\n\n    void subscribe(Consumer<? super E> handler) { handlers.add(handler); }\n\n    int publish(E event) {\n        for (Consumer<? super E> h : handlers) h.accept(event);\n        return handlers.size();\n    }\n}"},
            {"say": "2. Wire it up. Both handlers subscribe to a `Dispatcher<CardAuthorized>`. Self-check before reading on: why can't the fraud handler subscribe to a `Dispatcher<PaymentEvent>`? (That dispatcher may publish a `RefundIssued`, and `fraudCheck` reads `cents` from a `CardAuthorized`.)", "code": "val cards = Dispatcher<CardAuthorized>()\ncards.subscribe(fraudCheck)\ncards.subscribe(auditAll)                // fine: (PaymentEvent) -> Unit is a (CardAuthorized) -> Unit\ncards.publish(CardAuthorized(\"pay_1\", 1_200))   // 2\n\nval all = Dispatcher<PaymentEvent>()\nall.subscribe(fraudCheck)\n// error: argument type mismatch: actual type is '(CardAuthorized) -> Unit',\n//        but '(PaymentEvent) -> Unit' was expected.", "lang": "kotlin",
             "alt_lang": "java", "alt_code": "var cards = new Dispatcher<CardAuthorized>();\ncards.subscribe(fraudCheck);\ncards.subscribe(auditAll);               // fine thanks to ? super E\ncards.publish(new CardAuthorized(\"pay_1\", 1_200));   // 2\n\nvar all = new Dispatcher<PaymentEvent>();\nall.subscribe(fraudCheck);\n// error: incompatible types: Consumer<CardAuthorized> cannot be converted to Consumer<? super PaymentEvent>"}
        ]
    },
    "lab": {
        "title": "Consumers: a contravariant Sink, a general comparator, a dispatcher",
        "minutes": 12,
        "files": [
            f"{LAB}/main/kotlin/workbench/generics/l05/Sink.kt",
            f"{LAB}/main/kotlin/workbench/generics/l05/Sorting.kt",
            f"{LAB}/main/kotlin/workbench/generics/l05/Dispatcher.kt"
        ],
        "run": "./gradlew :generics:test --tests 'workbench.generics.l05.*'",
        "steps": [
            "Run the tests. All eight fail. The variance test says `but was: \"Sink<PaymentEvent>\"`: Java sees no wildcard, because `Sink` is still invariant.",
            "In `Sink.kt`, add `in` to `Sink`'s type parameter. Then write `CollectingSink`: keep a private `ArrayList<T>`, and return a copy from `items`. Why can't `CollectingSink` itself be declared `in T`? (Hint: look at `items`.)",
            "Write `feedAll`.",
            "In `Sorting.kt`, write `highest` with a loop and `comparator.compare`. The test calls it with a `List<CardAuthorized>` and a `Comparator<PaymentEvent>`.",
            "In `Dispatcher.kt`, store the handlers in a private list and call them in order in `publish`.",
            "Run the tests until all eight pass."
        ],
        "hints": [
            "`CollectingSink<T>` hands `T` back out through `items`, so its own `T` is both in and out. The class stays invariant; only the `Sink` interface it implements is `in`.",
            "`accepted.toList()` returns a copy, which is what the snapshot test checks.",
            "`private val handlers = ArrayList<(E) -> Unit>()` is all the storage `Dispatcher` needs."
        ],
        "done_when": "All eight tests in `ContravarianceTest` pass."
    },
    "drill": {
        "title": "Pick out or in for five parameters",
        "minutes": 4,
        "prompt": "Close this page. For each parameter, write the Kotlin type and the Java type with the right variance: (1) `source`, a list you only read payments from; (2) `sink`, a mutable list you only add payments to; (3) `order`, a comparator of payments; (4) `onEvent`, a handler called with each payment event; (5) `buffer`, a mutable list you both read from and add to.",
        "answer": {
            "lang": "kotlin",
            "src": "fun process(\n    source: List<Payment>,                // 1: List is already out\n    sink: MutableList<in Payment>,        // 2: write-only view\n    order: Comparator<in Payment>,        // 3: java.util.Comparator needs a use-site in\n    onEvent: (PaymentEvent) -> Unit,      // 4: function parameters are already in\n    buffer: MutableList<Payment>          // 5: read and write: invariant\n) { }",
            "alt": {"lang": "java", "title": "Process.java", "src": "static void process(\n        List<? extends Payment> source,          // 1: producer extends\n        List<? super Payment> sink,              // 2: consumer super\n        Comparator<? super Payment> order,       // 3: consumer super\n        Consumer<? super PaymentEvent> onEvent,  // 4: consumer super\n        List<Payment> buffer) {                  // 5: both: no wildcard\n}"}
        }
    },
    "recap": [
        "A consumer only takes values of `T` in. A consumer of a supertype can stand in for a consumer of a subtype: the arrow flips. That is contravariance.",
        "Kotlin declares it with `in T`. Java writes `? super T` at each use.",
        "In an `in` type, `T` may appear in parameters, not in return types or `val`s.",
        "Function types are `Function1<in P, out R>`: a `(PaymentEvent) -> Unit` handler is a `(CardAuthorized) -> Unit`.",
        "`java.util.Comparator` is invariant even in Kotlin; write `Comparator<in T>` in your signatures.",
        "PECS: Producer Extends (`out`), Consumer Super (`in`). Ask of each parameter: does it give me `T`, take `T`, or both?"
    ],
    "quiz": [
        {
            "q": "`interface Sink<in T> { fun accept(item: T) }`. Which assignment compiles?",
            "options": [
                "`val a: Sink<PaymentEvent> = cardSink` where `cardSink: Sink<CardAuthorized>`",
                "`val b: Sink<CardAuthorized> = auditSink` where `auditSink: Sink<PaymentEvent>`",
                "Both",
                "Neither, unless `Sink` is declared `out`"
            ],
            "answer": 1,
            "why": "With `in`, the arrow flips: a sink of the supertype is a sink of the subtype. The reverse is unsafe: a card-only sink seen as a `Sink<PaymentEvent>` could be handed a refund."
        },
        {
            "q": "Which member can you add to `interface Sink<in T>`?",
            "options": [
                "`fun last(): T`",
                "`val pending: List<T>`",
                "`fun acceptAll(items: List<T>)`",
                "`fun forEachPending(f: (T) -> Unit)`"
            ],
            "answer": 2,
            "why": "`acceptAll` takes the items in: `List<out E>` inside a parameter is − × + = −, an in-position. `last()` and `pending` hand `T` out. In `forEachPending`, the `T` is the parameter of a parameter (− × − = +), so it is an out-position too."
        },
        {
            "q": "Kotlin: `val byId: Comparator<PaymentEvent> = compareBy { it.paymentId }`. Why does `val c: Comparator<CardAuthorized> = byId` fail?",
            "options": [
                "Comparators are covariant, so the arrow goes the other way",
                "`Comparator` is `java.util.Comparator`, a Java interface with no declared variance, so Kotlin treats it as invariant",
                "`compareBy` returns a raw type",
                "It doesn't fail; it compiles"
            ],
            "answer": 1,
            "why": "Kotlin can't add variance to a Java interface, so `Comparator<A>` and `Comparator<B>` are unrelated unless you project: `Comparator<in CardAuthorized>`. The standard library does that in `sortedWith(comparator: Comparator<in T>)`. Kotlin's own `Comparable` is declared `in T` and behaves differently."
        },
        {
            "q": "Java: you write `static void register(Consumer<CardAuthorized> handler)`. A teammate has a `Consumer<PaymentEvent>`. What is the right fix?",
            "options": [
                "Change the parameter to `Consumer<? super CardAuthorized>`",
                "Change the parameter to `Consumer<? extends CardAuthorized>`",
                "Ask the teammate to cast their handler",
                "Change the parameter to raw `Consumer`"
            ],
            "answer": 0,
            "why": "The handler consumes the events you pass it, so Consumer Super. `? extends` would let you pass a consumer of some unknown subtype, which you could never call safely. A raw type turns off checking altogether."
        },
        {
            "q": "From \"Covariance with out: producers\": why is `fun <R> map(f: (T) -> R): Page<R>` allowed inside `data class Page<out T>`?",
            "options": [
                "Because `map` has its own type parameter, which exempts the whole method",
                "Because `T` is the parameter of `f`, which is itself a parameter: two in-positions make an out-position",
                "Because data classes skip the variance check",
                "It isn't allowed; it needs `@UnsafeVariance`"
            ],
            "answer": 1,
            "why": "The page calls `f` and passes it a `T`, so values of `T` flow out of the page. By the sign rule, − × − = +. A new type parameter `R` doesn't exempt anything: `fun <R> bad(t: T): R` would still fail.",
            "from": "gen-04"
        }
    ],
    "flashcards": [
        {"front": "What makes a generic type safe to declare `in T`?", "back": "It only takes values of `T` in (parameters). No public member returns a `T`."},
        {"front": "With `Sink<in T>`, which way does the arrow go between `Sink<PaymentEvent>` and `Sink<CardAuthorized>`?", "back": "`Sink<PaymentEvent>` is a subtype of `Sink<CardAuthorized>`: the arrow flips."},
        {"front": "Kotlin's `in T` corresponds to what in Java?", "back": "`? super T`, written at the use site, e.g. `Consumer<? super CardAuthorized>`."},
        {"front": "Is `(PaymentEvent) -> Unit` a subtype of `(CardAuthorized) -> Unit`?", "back": "Yes. Function types are `Function1<in P, out R>`, so a handler of the general type fits where a specific one is expected."},
        {"front": "Why must Kotlin code write `Comparator<in T>` instead of plain `Comparator<T>`?", "back": "On the JVM, `Comparator` is the Java interface `java.util.Comparator`, which has no declared variance, so Kotlin treats it as invariant."},
        {"front": "What does PECS stand for?", "back": "Producer Extends, Consumer Super (Effective Java, Item 31). In Kotlin: producer `out`, consumer `in`."},
        {"front": "Sign rule: where does `T` sit in `fun each(f: (T) -> Unit)`?", "back": "Parameter of a parameter: − × − = +, an out-position. Legal under `out T`, illegal under `in T`."}
    ],
    "terms": [
        {"term": "Consumer", "plain": "A type whose `T` values only go in: sinks, comparators, handlers."},
        {"term": "Contravariant", "plain": "`C<Super>` is a subtype of `C<Sub>`: the arrow flips."},
        {"term": "in", "plain": "Kotlin's keyword on a type parameter: \"T only goes into this type\"."},
        {"term": "? super T", "plain": "Java's use-site wildcard for a consumer: \"T or any supertype of T\"."},
        {"term": "PECS", "plain": "Producer Extends, Consumer Super: the Java rule for choosing wildcards."},
        {"term": "Function1<in P, out R>", "plain": "The type behind `(P) -> R`: contravariant in the parameter, covariant in the result."},
        {"term": "Sign rule", "plain": "Out-positions are +, in-positions are −; multiply through nesting to find where `T` really sits."}
    ],
    "explain_back": {
        "prompt": "A teammate asks: \"Why is a sink of PaymentEvent a subtype of a sink of CardAuthorized? That's backwards.\" Explain it in your own words, and say how you'd write the same idea in Java.",
        "answer": "Subtyping means \"can be used wherever the other is expected without anything going wrong\". Code that expects a sink of card authorizations will only ever put card authorizations into it. A sink that accepts every payment event accepts those too, so it can stand in safely. The opposite substitution is unsafe: a card-only sink used as a sink of all events could be handed a refund. So for things that only take values in, the general one substitutes for the specific one, and the arrow points the other way from the element types. Kotlin declares this once with `interface Sink<in T>`. Java writes it at each use as `Sink<? super CardAuthorized>`, which is the Consumer Super half of PECS."
    },
    "deeper": {
        "minutes": 10,
        "body": "Contravariance explains a detail of Kotlin's `Comparable`. It is declared `public interface Comparable<in T>`. So when Kotlin writes a Java signature for `fun <T : Comparable<T>> max(a: T, b: T)`, the bound becomes `<T extends Comparable<? super T>>`, the same bound the JDK writes by hand in `Collections.max`. That is how `LocalDate`, a `Comparable<ChronoLocalDate>`, gets through a bound that says `Comparable<LocalDate>`.\n\nThe sign rule also covers type arguments of variant classes. Inside `class C<out T>`, a parameter of type `Comparable<T>` is allowed: the parameter is −, and `Comparable`'s `in` is −, so `T` ends up in a + position. A parameter of type `MutableList<T>` is not allowed in either kind of class: an invariant argument is a 0, and anything times 0 stays 0, which is neither in nor out.\n\nC# uses the same keywords, `in` and `out`, for interfaces and delegates, which is where Kotlin borrowed them. Scala writes `+T` and `-T`, the signs from the table.\n\nOne caution for Java interop: when Java calls a Kotlin function with a parameter `handler: (PaymentEvent) -> Unit`, it sees `Function1<? super PaymentEvent, Unit>`. A Java lambda fits that type, but it must return `Unit.INSTANCE`. Kotlin APIs meant for Java callers often take a Java functional interface instead, or are marked `fun interface`."
    },
    "sources": [
        {"title": "Generics: variance, in and out (Kotlin docs)", "url": "https://kotlinlang.org/docs/generics.html"},
        {"title": "Calling Kotlin from Java: variant generics (Kotlin docs)", "url": "https://kotlinlang.org/docs/java-to-kotlin-interop.html"},
        {"title": "Wildcard guidelines (The Java Tutorials)", "url": "https://docs.oracle.com/javase/tutorial/java/generics/wildcardGuidelines.html"}
    ]
}

out = ROOT / "content/lessons/gen-05.json"
out.write_text(json.dumps(L, indent=2, ensure_ascii=False) + "\n")
print("wrote", out)
