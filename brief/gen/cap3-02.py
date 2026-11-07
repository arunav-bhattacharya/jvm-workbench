import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/events/src"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :events:demo -Pmain=workbench.events.l02.demo."


def demo(pkg, name):
    """A Kotlin demo with its Java twin, both in workbench.events.l02.demo.<pkg>."""
    k = f"{lab}/demo/kotlin/workbench/events/l02/demo/{pkg}/{name}.kt"
    j = f"{lab}/demo/java/workbench/events/l02/demo/{pkg}/{name}Java.java"
    return {"lang": "kotlin", "title": f"{name}.kt", "src": read(k),
            "run": f"{DEMO}{pkg}.{name}Kt", "file": k,
            "alt": {"lang": "java", "title": f"{name}Java.java", "src": read(j),
                    "run": f"{DEMO}{pkg}.{name}Java", "file": j}}


FIG = (
    '<svg viewBox="0 0 680 270" role="img" aria-label="Publishing a PaymentCaptured: the bus looks up three dispatch keys, nearest first: '
    'PaymentCaptured, then MoneyMovement, then PaymentEvent. Under each key it calls the handlers in subscription order: ledger and receipts, '
    'then movements, then audit. The PaymentRefunded key is never visited.">'
    '<text class="t-s t-m" x="285" y="24" text-anchor="middle">dispatch keys, nearest first</text>'
    '<text class="t-s t-m" x="540" y="24" text-anchor="middle">handlers, in subscription order</text>'
    '<rect class="box-a" x="10" y="100" width="150" height="50" rx="8"/>'
    '<text class="t-s t-code" x="85" y="121" text-anchor="middle">PaymentCaptured</text>'
    '<text class="t-s" x="85" y="139" text-anchor="middle">publish(capture)</text>'
    '<line class="ln" x1="160" y1="118" x2="206" y2="60" marker-end="url(#arr)"/>'
    '<line class="ln" x1="160" y1="125" x2="206" y2="128" marker-end="url(#arr)"/>'
    '<line class="ln" x1="160" y1="132" x2="206" y2="196" marker-end="url(#arr)"/>'
    '<rect class="box" x="210" y="40" width="150" height="36" rx="8"/>'
    '<text class="t-s t-code" x="285" y="63" text-anchor="middle">1 PaymentCaptured</text>'
    '<rect class="box-b" x="210" y="110" width="150" height="36" rx="8"/>'
    '<text class="t-s t-code" x="285" y="133" text-anchor="middle">2 MoneyMovement</text>'
    '<rect class="box" x="210" y="180" width="150" height="36" rx="8"/>'
    '<text class="t-s t-code" x="285" y="203" text-anchor="middle">3 PaymentEvent</text>'
    '<line class="ln-a" x1="360" y1="58" x2="406" y2="58" marker-end="url(#arr)"/>'
    '<line class="ln-a" x1="360" y1="128" x2="406" y2="128" marker-end="url(#arr)"/>'
    '<line class="ln-a" x1="360" y1="198" x2="406" y2="198" marker-end="url(#arr)"/>'
    '<rect class="box-ok" x="410" y="40" width="260" height="36" rx="8"/>'
    '<text class="t-s" x="540" y="63" text-anchor="middle">ledger, then receipts</text>'
    '<rect class="box-ok" x="410" y="110" width="260" height="36" rx="8"/>'
    '<text class="t-s" x="540" y="133" text-anchor="middle">movements</text>'
    '<rect class="box-ok" x="410" y="180" width="260" height="36" rx="8"/>'
    '<text class="t-s" x="540" y="203" text-anchor="middle">audit</text>'
    '<rect class="box-dim" x="210" y="228" width="150" height="32" rx="8"/>'
    '<text class="t-s t-m t-code" x="285" y="249" text-anchor="middle">PaymentRefunded</text>'
    '<rect class="box-dim" x="410" y="228" width="260" height="32" rx="8"/>'
    '<text class="t-s t-m" x="540" y="249" text-anchor="middle">refunds: not visited</text>'
    '</svg>'
)

S1 = """*Generics workshop: a type-safe container and event bus* built a bus that keys handlers by `event::class`. It has a hole you met in the warm-up: an audit handler subscribed under `PaymentEvent::class` never runs, because no event's run-time class is the interface itself. The same goes for a handler of `MoneyMovement`. Lesson 1 of this track made that middle level on purpose, so the bus has to honor it.

There are two honest fixes. The first keeps one flat list of (type, handler) pairs and asks `type.isInstance(event)` of each. It is short and correct, and every publish checks every subscription: forty handlers, forty checks per event, almost all of them misses. The second keeps the registry keyed by `KClass`, as *KClass, Class and type tokens* did, and works out for each event class the list of keys to visit: the class itself, then each supertype that is an event, nearest first.

```java
static List<Class<?>> dispatchKeys(Class<?> type) {
    LinkedHashSet<Class<?>> found = new LinkedHashSet<>();
    ArrayDeque<Class<?>> queue = new ArrayDeque<>(List.of(type));
    while (!queue.isEmpty()) {
        Class<?> c = queue.removeFirst();
        if (!PaymentEvent.class.isAssignableFrom(c) || !found.add(c)) continue;
        queue.addAll(List.of(c.getInterfaces()));
        if (c.getSuperclass() != null) queue.add(c.getSuperclass());
    }
    return List.copyOf(found);
}
```

```kotlin
private fun dispatchKeys(type: Class<*>): List<KClass<*>> = keyCache.computeIfAbsent(type) {
    val found = LinkedHashSet<Class<*>>()
    val queue = ArrayDeque<Class<*>>().apply { add(type) }
    while (queue.isNotEmpty()) {
        val c = queue.removeFirst()
        if (!PaymentEvent::class.java.isAssignableFrom(c) || !found.add(c)) continue
        queue.addAll(c.interfaces)
        c.superclass?.let(queue::add)
    }
    found.map { it.kotlin }
}
```

For `PaymentCaptured` the walk gives `[PaymentCaptured, MoneyMovement, PaymentEvent]`, and publish looks up only those three keys. The breadth-first order is a promise to callers: specific handlers run before general ones, and within one key, in subscription order. Guava's `EventBus` routes the same way, to subscribers of "any type to which the event is assignable", and caches the flattened hierarchy per class.

The walk uses Java reflection, `getInterfaces()` and `getSuperclass()`, which costs no extra jar. kotlin-reflect's `allSuperclasses` would also work, but that lesson's rule applies: describing a class needs the 3.8 MB kotlin-reflect at run time, and naming and casting don't. The answer never changes for a class, so `computeIfAbsent` caches it once per class. On a `ConcurrentHashMap` that call is one atomic step, so two threads publishing the first capture at once don't race to fill the cache.

Before you run the demo, predict the keys it prints for `PaymentDeclined`."""

S2 = """A handler only ever takes an event in. It never hands one back. That makes it a consumer, and *Contravariance with in: consumers* gave the rule: declare the type parameter `in`.

```java
@FunctionalInterface
interface Handler<E extends PaymentEvent> { void handle(E event); }    // Java: invariant

<E extends PaymentEvent> Subscription subscribe(Class<E> type, Handler<? super E> handler) { ... }
```

```kotlin
fun interface Handler<in E : PaymentEvent> { fun handle(event: E) }

fun <E : PaymentEvent> subscribe(type: KClass<E>, handler: Handler<E>): Subscription { ... }
```

Now an audit handler written for every event fits any subscription: `bus.subscribe(PaymentCaptured::class, audit)` compiles with `audit: Handler<PaymentEvent>`. Delete the `in` and the same line fails with `argument type mismatch: actual type is 'Handler<PaymentEvent>', but 'Handler<PaymentCaptured>' was expected.` Java has no declaration-site variance, so the Java version writes `? super E` at every use. kotlinc writes that wildcard for you: the Java signature of the Kotlin `subscribe` is `subscribe(KClass<E>, Handler<? super E>)`, which is why Java callers in lesson 3 get the same freedom.

Why a `fun interface` and not the function type `(E) -> Unit`? A function type is already `in` on its parameter, so variance would be free. But Java would see a `Function1<? super E, Unit>`, and every Java lambda would have to end with `return Unit.INSTANCE`. A `fun interface` with a `void` method takes a plain Java lambda. Lesson 3 is about exactly that surface.

Inside the bus, handlers of different types share one map, so each one is stored behind an adapter that takes any `PaymentEvent`:

```java
Handler<PaymentEvent> adapter = event -> handler.handle(type.cast(event));
```

```kotlin
val adapter = Handler<PaymentEvent> { event -> handler.handle(type.cast(event)) }
```

The generics workshop used `safeCast`, so a wrong event became a no-op. Here the dispatch keys already guarantee the type, so a mismatch can only be a bug in the bus, and `cast` makes that bug loud. The next section makes sure loud doesn't mean fatal.

Kotlin callers get a reified wrapper, as *Type erasure and reified type parameters* showed: `inline fun <reified E : PaymentEvent> subscribe(handler: Handler<E>) = subscribe(E::class, handler)`. It needs no `noinline`. Only parameters of function type are inlined, and a `Handler` is an ordinary object.

In the demo, delete `in` and predict which two lines break."""

S3 = """The bus is the subject from *Observer and Command*, so that lesson's three rules apply, and the lab tests each one.

`subscribe` returns a handle. `Subscription` extends `AutoCloseable`, and closing it removes exactly the adapter that `subscribe` stored. Without a handle, a handler owned by a short-lived object stays in the map forever: a lapsed listener that keeps reacting to events and can't be garbage collected.

One failing handler must not stop the others. `deliver` catches `Exception` around each call and reports it, with the event, to an `ErrorHandler` the bus was built with:

```java
for (Handler<PaymentEvent> handler : handlers) {     // a snapshot: copy-on-write
    called++;
    try {
        handler.handle(event);
    } catch (Exception e) {
        onError.onError(event, e);                    // one failure must not starve the rest
    }
}
```

```kotlin
for (handler in handlers) {                           // a snapshot: copy-on-write
    called++
    try {
        handler.handle(event)
    } catch (e: Exception) {
        onError.onError(event, e)                     // one failure must not starve the rest
    }
}
```

It catches `Exception`, not `Throwable`: an `OutOfMemoryError` should still take the service down. And the bus doesn't decide what an error means. Guava's `EventBus` catches and logs, and its own Javadoc says that "is rarely the right solution for error handling". Here the service passes in its own `ErrorHandler`, which can count the failure and send the event to a retry topic.

Each key's handlers live in a `CopyOnWriteArrayList`, so delivery iterates a snapshot. A handler may close its own subscription while it runs (a welcome email that fires once), and the loop carries on. With an `ArrayList` the next step of the loop throws `ConcurrentModificationException`. Copy-on-write makes `subscribe` copy the array, which is fine: subscriptions change at start-up, and events arrive all day.

Those two collections also make the bus safe for many publishers with no lock of its own. `ConcurrentHashMap` guards the registry, and each list is replaced, never changed in place. The lab's load test runs eight publishers while another thread subscribes and closes in a loop, and counts every event.

One rule doesn't change: delivery is synchronous. Every handler runs on the publisher's thread, which for a Kafka consumer is the poll loop. The design review in lesson 3 comes back to that.

The demo runs the same three handlers on three buses. Predict what each run prints before you run it."""

S4 = """Some extra behavior belongs to every event once: logging, tracing, dropping a Kafka redelivery. Some belongs to one handler: timing the ledger, retrying the receipt email. The first kind is a chain of responsibility around `publish`. The second is a decorator around one handler. They look alike, and choosing the wrong one gives the wrong numbers.

The chain is the one from *State and Chain of Responsibility*. Each middleware gets the event and `next`, the rest of the chain, and either passes the event on or returns 0 to stop it. The bus builds the chain once, at construction, by folding a copy of the list from the right, so the first middleware wraps all the others and the last one wraps delivery:

```java
Next pipeline = this::deliver;
for (int i = middleware.size() - 1; i >= 0; i--) {
    Middleware m = middleware.get(i);
    Next rest = pipeline;
    pipeline = event -> m.intercept(event, rest);
}
```

```kotlin
private val pipeline: Next = middleware.toList()
    .foldRight(Next(::deliver)) { m, next -> Next { event -> m.intercept(event, next) } }
```

Order is behavior. With `[dedupe, logging]` a redelivery is dropped before anything logs it. With `[logging, dedupe]` it is logged and then dropped, which is what you want when you need to count redeliveries. Pick one and pin it in a test. The dedupe middleware itself is one line, `if (seen.add(event)) next.proceed(event) else 0`. `add` is the check and the act in one step, the fix from *Race conditions: why count++ lies*, so eight consumer threads can't all let the same capture through. Its "same event" is data-class equality: same type, same id, same amount.

The decorator is the one from *Decorator and Proxy*: it implements the same `Handler<E>`, adds one behavior and forwards the call.

```java
static <E extends PaymentEvent> Handler<E> timed(Handler<E> inner, String name, Timings timings) {
    return event -> {
        long start = timings.ticker().nanos();
        try { inner.handle(event); }
        finally { timings.record(name, timings.ticker().nanos() - start); }
    };
}
```

```kotlin
fun <E : PaymentEvent> Handler<E>.timed(name: String, timings: Timings): Handler<E> {
    val inner = this
    return Handler { event ->
        val start = timings.ticker.nanos()
        try { inner.handle(event) } finally { timings.record(name, timings.ticker.nanos() - start) }
    }
}
```

It records in `finally`, so a handler that throws is timed too, and the exception still reaches the bus's isolation. The clock is a `Ticker` you pass in. Tests use a fake one that moves forward by a fixed step on every read, so they check exact numbers with no sleeps and no flaky margins. A timing middleware couldn't do this job: it sees one delivery to all of an event's handlers, so it would add the ledger's 2 ms to the receipt email's 300 ms.

In the demo, swap the first two middleware and predict what the redelivery prints."""

L = {
 "id": "cap3-02",
 "title": "A typed event bus",
 "minutes": 40,
 "goal": "By the end you can build an in-process event bus that routes each event to the handlers of its class and of every event supertype, declare its handler type `in` so one general handler fits any subscription, keep a failing or self-removing handler from hurting the others, and add a middleware chain around delivery and a timing decorator around a handler.",
 "warmup": {
  "q": "The bus from *Generics workshop: a type-safe container and event bus* stores handlers in a map keyed by `event::class`. You subscribe an audit handler under `PaymentEvent::class` and publish a `PaymentCaptured`. How many times does the audit handler run?",
  "options": [
   "Once: a PaymentCaptured is a PaymentEvent",
   "Never: no event's run-time class is the interface PaymentEvent",
   "It doesn't compile: you can't subscribe under an interface",
   "Twice: once for the class and once for the interface"
  ],
  "answer": 1,
  "why": "The lookup uses the event's exact run-time class, `PaymentCaptured`, and nobody subscribed under that key. The subscription itself compiles, because `PaymentEvent::class` is a `KClass<PaymentEvent>`. Delivering to supertypes takes a walk up the event's type hierarchy, which this lesson adds."
 },
 "sections": [
  {
   "h": "Route by the event's class, then walk up its supertypes",
   "body": S1,
   "figure": {"svg": FIG, "caption": "One publish visits three keys, nearest first, and calls each key's handlers in the order they subscribed. Keys of sibling types are never touched."},
   "try": {
    "title": "Exact class versus supertypes",
    "minutes": 4,
    "steps": [
     "Read `DispatchDemo.kt` (or `DispatchDemoJava.java`). Three handlers subscribe under three types, and the same capture is published to a bus that looks up the exact class only, then to one that walks supertypes.",
     "Predict both `ran` lists and the keys for `PaymentDeclined`. Run it.",
     "Add `bus.subscribe(MoneyMovement::class) { ran += \"audit again\" }` (in Java, `bus.subscribe(MoneyMovement.class, e -> ran.add(\"audit again\"))`) as the last subscription, after the ledger line. Predict where `audit again` appears in the second list, then run."
    ],
    "code": demo("dispatch", "DispatchDemo"),
    "expect": "`exact class only: [ledger]` and `walking supertypes: [ledger, movements, audit]`. The keys are `[PaymentCaptured, MoneyMovement, PaymentEvent]` and `[PaymentDeclined, PaymentEvent]`. After your change the second list is `[ledger, movements, audit again, audit]`: keys go nearest first, and within the `MoneyMovement` key the handlers run in subscription order."
   },
   "refs": [{"title": "Guava EventBus source and Javadoc", "url": "https://raw.githubusercontent.com/google/guava/master/guava/src/com/google/common/eventbus/EventBus.java", "kind": "read"}]
  },
  {
   "h": "Handlers only consume events, so declare them in",
   "body": S2,
   "try": {
    "title": "Take the in away",
    "minutes": 4,
    "steps": [
     "Run `VarianceDemo`. Read the last line: the Java signature of the Kotlin `subscribe`.",
     "Delete the word `in` from `Handler` and run again. Predict which two lines fail.",
     "Put `in` back, uncomment the `tooWide` line and run once more.",
     "In `VarianceDemoJava`, change `Handler<? super E>` to `Handler<E>` in `subscribe` and run it."
    ],
    "code": demo("variance", "VarianceDemo"),
    "expect": "With `in`, the audit handler runs for both captures and the signature ends with `Handler<? super E>)`. Without it, kotlinc reports `argument type mismatch: actual type is 'Handler<PaymentEvent>', but 'Handler<PaymentCaptured>' was expected.` at the subscribe call and `initializer type mismatch` at `forCaptures`. `tooWide` fails the other way: `expected 'Handler<PaymentEvent>', actual 'Handler<PaymentCaptured>'`. javac, without `? super`, says `inference variable E has incompatible equality constraints PaymentEvent,PaymentCaptured`."
   },
   "refs": [{"title": "Calling Kotlin from Java: variant generics (Kotlin docs)", "url": "https://kotlinlang.org/docs/java-to-kotlin-interop.html", "kind": "docs"}]
  },
  {
   "h": "Observer rules: return a handle, isolate failures, iterate a snapshot",
   "body": S3,
   "try": {
    "title": "One bad handler, three buses",
    "minutes": 4,
    "steps": [
     "Read `IsolationDemo`. The first handler unsubscribes itself, the second always throws, the third sends a receipt. Each bus gets two captures.",
     "Predict the output of each of the three runs. Run it.",
     "In the isolated run, change `catch (e: Exception)` to catch only `IllegalArgumentException` (in Java, `RuntimeException` to `IllegalArgumentException`). Predict, then run."
    ],
    "code": demo("isolation", "IsolationDemo"),
    "expect": "The `ArrayList` bus prints the welcome email and then `publish threw java.util.ConcurrentModificationException`, because the list changed under its own loop. The copy-on-write bus without isolation gets past that and dies on `ledger is down`; no receipt is sent. The isolated bus sends both receipts and reports two errors. With the narrower catch, the third run fails like the second: the `IllegalStateException` is no longer caught."
   },
   "refs": [{"title": "CopyOnWriteArrayList (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CopyOnWriteArrayList.html", "kind": "docs"}]
  },
  {
   "h": "Middleware is a chain, timing is a decorator",
   "body": S4,
   "try": {
    "title": "Reorder the chain",
    "minutes": 4,
    "steps": [
     "Run `ChainDemo` and read the nesting of the `>` and `<` lines.",
     "Swap `logging(\"outer\")` and `dropDuplicates()` in the list. Predict what the redelivery prints now, and run.",
     "Change `tick()` to add 90,000 instead of 40,000. Predict the `ledger took` line before you run."
    ],
    "code": demo("chain", "ChainDemo"),
    "expect": "First run: `outer >`, `inner >`, the ledger lines, then `inner <` and `outer <` in reverse. The redelivery prints `outer >` and `outer <: 0 handler(s)`: logged, then dropped. After the swap the redelivery prints nothing at all below the `--` line. With 90,000 per read, `ledger took 90 us`: the decorator reads the clock twice, so the time is exactly one step."
   }
  }
 ],
 "analogy": "Picture a newspaper's wire desk. A story about a football transfer goes to the football editor first, then to the sports editor, then to the chief editor, who wants everything: the most specific desk first, then each wider one. Before any editor sees it, a clerk stamps it and throws away a copy that already came in. One editor who spills coffee on his copy doesn't stop the others from reading theirs. The analogy breaks in one place: in a newsroom each editor gets a separate copy at the same moment. This bus hands the same object to each handler in turn, on one thread, so a slow editor makes everyone after him wait.",
 "in_your_world": "Quarkus has a bus like this built in: CDI events, fired with `Event<T>.fire(...)` and received by `@Observes` methods, and an observer of a supertype receives its subtypes too. Knowing the mechanism tells you what to check there: the delivery order, what happens when an observer throws, and which thread runs it. In a Kafka consumer the publisher's thread is the poll loop. If the handlers for one batch of records take longer than `max.poll.interval.ms` in total, the consumer is considered failed and the group rebalances. In a Temporal worker, publish from activities. Workflow code is replayed and must stay deterministic, so it shouldn't trigger in-process side effects at all.",
 "mistake": "The common mistake is doing slow work inside a handler: an HTTP call to the email provider, a database write with retries. The bus makes `publish` look like fire-and-forget, so it feels free. It isn't: delivery is synchronous, so a 300 ms receipt call makes every capture 300 ms slower, and the Kafka consumer that published it falls behind. The fix is to keep handlers fast and hand slow work to something built for it: write a row to an outbox table in the same transaction, or put the work on a bounded executor. Then time each handler with the decorator, so the next slow one shows up in a metric before it shows up in the lag.",
 "compare": {
  "title": "The bus in Java and Kotlin",
  "java": {
   "title": "EventBus.java",
   "src": "@FunctionalInterface interface Handler<E extends PaymentEvent> { void handle(E event); }\n@FunctionalInterface interface ErrorHandler { void onError(PaymentEvent event, Exception error); }\n@FunctionalInterface interface Next { int proceed(PaymentEvent event); }\n@FunctionalInterface interface Middleware { int intercept(PaymentEvent event, Next next); }\n\nfinal class EventBus {\n    private final Map<Class<?>, List<Handler<PaymentEvent>>> registry = new ConcurrentHashMap<>();\n    private final Map<Class<?>, List<Class<?>>> keyCache = new ConcurrentHashMap<>();\n    private final ErrorHandler onError;\n    private final Next pipeline;\n\n    EventBus(List<Middleware> middleware, ErrorHandler onError) {\n        this.onError = onError;\n        Next next = this::deliver;\n        for (Middleware m : List.copyOf(middleware).reversed()) {   // reversed(): JDK 21\n            Next rest = next;\n            next = event -> m.intercept(event, rest);\n        }\n        this.pipeline = next;\n    }\n\n    <E extends PaymentEvent> AutoCloseable subscribe(Class<E> type, Handler<? super E> handler) {\n        Handler<PaymentEvent> adapter = event -> handler.handle(type.cast(event));\n        List<Handler<PaymentEvent>> handlers = registry.computeIfAbsent(type, t -> new CopyOnWriteArrayList<>());\n        handlers.add(adapter);\n        return () -> handlers.remove(adapter);\n    }\n\n    int publish(PaymentEvent event) { return pipeline.proceed(event); }\n\n    private int deliver(PaymentEvent event) {\n        int called = 0;\n        for (Class<?> key : keyCache.computeIfAbsent(event.getClass(), EventBus::dispatchKeys)) {\n            for (Handler<PaymentEvent> h : registry.getOrDefault(key, List.of())) {\n                called++;\n                try { h.handle(event); } catch (Exception e) { onError.onError(event, e); }\n            }\n        }\n        return called;\n    }\n\n    private static List<Class<?>> dispatchKeys(Class<?> type) { /* breadth-first walk, as above */ }\n}"
  },
  "kotlin": {
   "title": "EventBus.kt",
   "src": "fun interface Handler<in E : PaymentEvent> { fun handle(event: E) }\nfun interface Next { fun proceed(event: PaymentEvent): Int }\nfun interface Middleware { fun intercept(event: PaymentEvent, next: Next): Int }\n\nclass EventBus(\n    middleware: List<Middleware> = emptyList(),\n    private val onError: ErrorHandler = ErrorHandler.PRINT,\n) {\n    private val registry = ConcurrentHashMap<KClass<*>, CopyOnWriteArrayList<Handler<PaymentEvent>>>()\n    private val keyCache = ConcurrentHashMap<Class<*>, List<KClass<*>>>()\n    private val pipeline: Next = middleware.toList()\n        .foldRight(Next(::deliver)) { m, next -> Next { event -> m.intercept(event, next) } }\n\n    fun <E : PaymentEvent> subscribe(type: KClass<E>, handler: Handler<E>): Subscription {\n        val adapter = Handler<PaymentEvent> { event -> handler.handle(type.cast(event)) }\n        val handlers = registry.computeIfAbsent(type) { CopyOnWriteArrayList() }\n        handlers += adapter\n        return Subscription { handlers.remove(adapter) }\n    }\n\n    inline fun <reified E : PaymentEvent> subscribe(handler: Handler<E>): Subscription = subscribe(E::class, handler)\n\n    fun publish(event: PaymentEvent): Int = pipeline.proceed(event)\n\n    private fun deliver(event: PaymentEvent): Int {\n        var called = 0\n        for (key in dispatchKeys(event.javaClass)) {\n            for (handler in registry[key] ?: continue) {\n                called++\n                try { handler.handle(event) } catch (e: Exception) { onError.onError(event, e) }\n            }\n        }\n        return called\n    }\n\n    private fun dispatchKeys(type: Class<*>): List<KClass<*>> = keyCache.computeIfAbsent(type) { /* the walk */ }\n}"
  },
  "note": "The mechanism is identical: the same registry, the same walk, the same adapter, the same fold and the same catch. The differences are in who writes what. Java writes `Handler<? super E>` at the use site; Kotlin declares `in` once and kotlinc puts the wildcard into the Java signature. Kotlin gets default arguments on the constructor and a reified `subscribe<E>` for its own callers; Java callers get neither until lesson 3 adds `@JvmOverloads` and a `Class<E>` overload. And Kotlin's `Next(::deliver)` turns a function reference into a `fun interface` object, where Java writes `this::deliver` against its functional interface."
 },
 "worked": {
  "title": "Wire up receipts, and put each concern in its place",
  "steps": [
   {
    "say": "Every capture should send a receipt email. That's one handler for one event type. Subscribe it under `PaymentCaptured`, the most specific key, so it never sees a refund.",
    "code": "val receipts = Handler<PaymentCaptured> { email.sendReceipt(it.paymentId, it.amount) }\nval receiptsSubscription = bus.subscribe<PaymentCaptured>(receipts)",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "// the Java bus from the comparison below\nHandler<PaymentCaptured> receipts = e -> email.sendReceipt(e.paymentId(), e.amount());\nAutoCloseable receiptsSubscription = bus.subscribe(PaymentCaptured.class, receipts);"
   },
   {
    "say": "The email provider fails about one call in two hundred. Isolation already keeps the ledger and the audit log running when it does. What the service still has to decide is what a failure means. Here the error handler counts it and puts the event on a retry topic.",
    "code": "val bus = EventBus(\n    middleware = listOf(DropDuplicates()),\n    onError = ErrorHandler { event, error ->\n        metrics.increment(\"handler.failures\")\n        retryTopic.send(event, error.toString())\n    },\n)",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "ErrorHandler onError = (event, error) -> {\n    metrics.increment(\"handler.failures\");\n    retryTopic.send(event, error.toString());\n};\nEventBus bus = new EventBus(List.of(new DropDuplicates()), onError);"
   },
   {
    "say": "After a consumer rebalance Kafka redelivers the last few records, and the customer must not get two receipts. Deduplication applies to every event once, before any handler, so it's middleware, first in the list. A decorator on the receipts handler would dedupe receipts only, and the ledger would still post twice.",
    "code": "middleware = listOf(DropDuplicates(), logging)     // dedupe first: redeliveries are never logged",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "List<Middleware> middleware = List.of(new DropDuplicates(), logging);   // dedupe first: redeliveries are never logged"
   },
   {
    "say": "How long does a receipt take? That's a question about one handler, so it's a decorator: wrap the handler, not the bus. The timings now show about 300 ms per capture under `receipts`, all of it on the consumer thread. That number is the case for moving the email to an outbox, which lesson 3's design review makes.",
    "code": "bus.subscribe<PaymentCaptured>(receipts.timed(\"receipts\", timings))",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "bus.subscribe(PaymentCaptured.class, timed(receipts, \"receipts\", timings));   // the static timed(...) from the last section"
   }
  ]
 },
 "lab": {
  "title": "Build the bus: dispatch, variance, isolation, chain and decorator",
  "minutes": 15,
  "files": [
   "labs/events/src/main/kotlin/workbench/events/l02/Bus.kt",
   "labs/events/src/main/kotlin/workbench/events/l02/Middlewares.kt",
   "labs/events/src/main/kotlin/workbench/events/l02/Timing.kt"
  ],
  "run": "./gradlew :events:test --tests 'workbench.events.l02.*'",
  "steps": [
   "The package starts with lesson 1's solution (`Values.kt`, `Model.kt`, `Parsing.kt`, `Summary.kt`). Don't edit `Callers.kt`: the tests reach your inline `subscribe` through it. Run the tests: all sixteen fail.",
   "`Bus.kt` TODO 1: add the one word that makes `Handler` contravariant. Two variance tests turn green.",
   "TODO 2, `subscribe`: build the adapter with `type.cast`, add it to the list for `type` with `computeIfAbsent`, and return a `Subscription` that removes that adapter.",
   "TODO 3, `deliver`: loop over `dispatchKeys(event.javaClass)` (given), call each key's handlers in order, count the calls, and send any `Exception` to `onError`.",
   "TODO 4, `pipeline`: fold a copy of `middleware` from the right, starting from `Next(::deliver)`. TODO 5: the reified `subscribe` in one line.",
   "`Middlewares.kt` TODO 6 and `Timing.kt` TODO 7: `DropDuplicates` and the `timed` decorator.",
   "Run until all sixteen pass, then run them twice more: three tests use eight threads."
  ],
  "hints": [
   "`registry.computeIfAbsent(type) { CopyOnWriteArrayList() }` returns the list for that key, creating it the first time. Keep a reference to it for the `Subscription`.",
   "`Subscription { handlers.remove(adapter) }` builds the handle. `remove` returns false the second time, so closing twice is harmless.",
   "`for (handler in registry[key] ?: continue)` skips keys nobody subscribed to.",
   "The fold: `middleware.toList().foldRight(Next(::deliver)) { m, next -> Next { e -> m.intercept(e, next) } }`. `foldRight` visits the last middleware first, so it ends up innermost.",
   "`DropDuplicates`: `if (seen.add(event)) next.proceed(event) else 0`. A `contains` check followed by `add` lets two threads through with the same event.",
   "In `timed`, keep `val inner = this` before the `Handler { ... }` lambda, call `inner.handle(event)` inside `try`, and record in `finally`."
  ],
  "done_when": "All sixteen tests in `BusTest` pass, three runs in a row."
 },
 "drill": {
  "title": "Delivery and the chain from memory",
  "minutes": 5,
  "prompt": "Close the lab. From memory, write `deliver(event)` (dispatch keys, handlers in order, a count, one `try` per handler) and the one expression that builds the middleware chain. Then answer: in `[logging, dedupe]`, does a redelivery get logged?",
  "answer": {
   "lang": "kotlin",
   "src": "private fun deliver(event: PaymentEvent): Int {\n    var called = 0\n    for (key in dispatchKeys(event.javaClass)) {\n        for (handler in registry[key] ?: continue) {        // copy-on-write snapshot\n            called++\n            try {\n                handler.handle(event)\n            } catch (e: Exception) {\n                onError.onError(event, e)\n            }\n        }\n    }\n    return called\n}\n\nprivate val pipeline: Next = middleware.toList()\n    .foldRight(Next(::deliver)) { m, next -> Next { event -> m.intercept(event, next) } }\n\n// [logging, dedupe]: yes. logging runs first, then dedupe returns 0.",
   "alt": {
    "lang": "java",
    "src": "private int deliver(PaymentEvent event) {\n    int called = 0;\n    for (Class<?> key : dispatchKeys(event.getClass())) {\n        for (Handler<PaymentEvent> handler : registry.getOrDefault(key, List.of())) {\n            called++;\n            try {\n                handler.handle(event);\n            } catch (Exception e) {\n                onError.onError(event, e);\n            }\n        }\n    }\n    return called;\n}\n\nNext next = this::deliver;\nfor (int i = middleware.size() - 1; i >= 0; i--) {\n    Middleware m = middleware.get(i);\n    Next rest = next;\n    next = event -> m.intercept(event, rest);\n}\nthis.pipeline = next;\n\n// [logging, dedupe]: yes. logging runs first, then dedupe returns 0."
   }
  }
 },
 "recap": [
  "Keying handlers by the exact class misses subscriptions to `MoneyMovement` and `PaymentEvent`. Walk the event's supertypes, nearest first, cache the walk per class, and look up each key.",
  "A handler only consumes events, so it is `Handler<in E>`. A `Handler<PaymentEvent>` then fits any subscription, and Java sees `Handler<? super E>` without writing it.",
  "Store each handler behind an adapter that takes any event and casts with `type.cast`. The keys guarantee the type, so a failed cast is a loud bus bug.",
  "Return a handle from `subscribe`, catch `Exception` per handler and report it to an injected `ErrorHandler`, and iterate a copy-on-write list so a handler can unsubscribe itself.",
  "What applies to every event once (logging, dedupe) is middleware: a chain built once by a fold, where order is behavior. What applies to one handler (timing) is a decorator.",
  "Test timing with a fake `Ticker` that steps on every read: exact numbers, no sleeps."
 ],
 "quiz": [
  {
   "q": "From *Contravariance with in: consumers*: with `fun interface Handler<in E : PaymentEvent>`, `audit: Handler<PaymentEvent>` and `ledger: Handler<PaymentCaptured>`, which line compiles?",
   "options": [
    "`val h: Handler<PaymentEvent> = ledger`",
    "`val h: Handler<MoneyMovement> = ledger`",
    "`val h: Handler<PaymentCaptured> = audit`",
    "`val h: Handler<PaymentRefunded> = ledger`"
   ],
   "answer": 2,
   "why": "For a consumer the arrow flips: something that takes any event can stand in for something that takes captures. The other three ask a capture-only handler to accept events it can't handle, a refund or any movement, so the compiler refuses them.",
   "from": "gen-05"
  },
  {
   "q": "From *Observer and Command*: a request-scoped bean subscribes to the bus in its constructor and never closes the `Subscription`. What happens after a few thousand requests?",
   "options": [
    "Nothing: the garbage collector removes the beans when the requests end",
    "Every old bean is still in the registry, can't be collected, and still reacts to each event",
    "The bus throws when the registry grows past a limit",
    "Only the newest bean receives events"
   ],
   "answer": 1,
   "why": "The registry holds a reference to each adapter, and each adapter holds the bean's handler. That's the lapsed listener: memory grows with every request, and every capture now runs thousands of stale handlers. Closing the handle in the bean's `@PreDestroy` method removes it.",
   "from": "pat-08"
  },
  {
   "q": "From *State and Chain of Responsibility*: the bus is built with `middleware = [dedupe, logging]`. Kafka redelivers a capture the bus has already seen. What does the log show for the redelivery?",
   "options": [
    "Nothing: dedupe returns 0 before logging runs",
    "A log line with 0 handlers",
    "A log line with 1 handler, then dedupe drops it",
    "Two log lines, one per delivery"
   ],
   "answer": 0,
   "why": "The first middleware in the list wraps all the others. Dedupe answers 0 without calling `next`, so logging never sees the event. With `[logging, dedupe]` you'd get a log line ending in 0 handlers, which is the order to choose if you want to count redeliveries.",
   "from": "pat-09"
  },
  {
   "q": "From *Inline functions: noinline, crossinline and non-local returns*: `inline fun <reified E : PaymentEvent> subscribe(handler: Handler<E>) = subscribe(E::class, handler)` stores the handler in the registry. Why does it compile without `noinline`?",
   "options": [
    "Because `reified` makes every parameter noinline",
    "Because members of a class are never inlined",
    "Because the compiler adds `noinline` automatically when a lambda is stored",
    "Because only parameters of function type are inlined, and `Handler` is a fun interface"
   ],
   "answer": 3,
   "why": "`inline` pastes the bodies of lambdas passed to function-type parameters. A `Handler` argument is an ordinary object, even when the caller writes it as a lambda, so there is nothing to inline and nothing that needs `noinline`. With `handler: (E) -> Unit` it would need `noinline`, as the generics workshop showed.",
   "from": "kt-01"
  },
  {
   "q": "Subscriptions, in this order: `audit` under `PaymentEvent`, then `movements` under `MoneyMovement`, then `ledger` under `PaymentCaptured`. You publish a `PaymentRefunded`. Which handlers run, in what order?",
   "options": [
    "audit, movements",
    "movements, audit",
    "audit, movements, ledger",
    "movements only"
   ],
   "answer": 1,
   "why": "The keys for a refund are `[PaymentRefunded, MoneyMovement, PaymentEvent]`, visited nearest first. Nobody subscribed under `PaymentRefunded`, so `movements` runs, then `audit`. Subscription order matters only within one key, and `ledger` is under a sibling type the walk never visits."
  }
 ],
 "flashcards": [
  {"front": "Why does a bus keyed by `event::class` never call a handler subscribed under `PaymentEvent::class`?", "back": "No event's run-time class is the interface itself. Delivery must also look up each supertype of the event's class."},
  {"front": "In what order does this bus call handlers?", "back": "The event's own class first, then each event supertype, nearest first. Within one key, in subscription order."},
  {"front": "Why is the handler type `Handler<in E>`?", "back": "A handler only consumes events. With `in`, a `Handler<PaymentEvent>` can stand in for a `Handler<PaymentCaptured>`."},
  {"front": "What Java signature does kotlinc give `fun <E : PaymentEvent> subscribe(type: KClass<E>, handler: Handler<E>)` when `Handler` is `in`?", "back": "`subscribe(KClass<E>, Handler<? super E>)`: kotlinc turns declaration-site `in` into a `? super` wildcard in parameters."},
  {"front": "Why a `CopyOnWriteArrayList` for each key's handlers?", "back": "Delivery iterates a snapshot, so a handler can unsubscribe itself, and publishers need no lock. Each subscribe copies the array, which is fine because subscriptions rarely change."},
  {"front": "Middleware or decorator: per-handler timing?", "back": "Decorator. Middleware wraps one delivery to all of an event's handlers; a decorator wraps one handler and implements its interface."},
  {"front": "Why does `DropDuplicates` test `seen.add(event)` instead of `seen.contains(event)`?", "back": "`add` checks and inserts in one atomic step. Contains-then-add lets two threads pass the same event."}
 ],
 "terms": [
  {"term": "Dispatch keys", "plain": "The list of types a bus looks up for one event: its class, then its event supertypes, nearest first."},
  {"term": "Adapter", "plain": "A small wrapper that lets a Handler<PaymentCaptured> be stored as a Handler<PaymentEvent>, by casting each event on the way in."},
  {"term": "Failure isolation", "plain": "Catching each handler's exception so that the other handlers still run."},
  {"term": "Lapsed listener", "plain": "A handler that was never unsubscribed, so the bus keeps it alive and keeps calling it."},
  {"term": "Middleware", "plain": "A link in a chain around publish that can pass an event on, change it or stop it."},
  {"term": "Virtual time", "plain": "A fake clock that tests move forward by hand, so timing can be checked exactly."}
 ],
 "explain_back": {
  "prompt": "Walk a colleague through one `publish(PaymentCaptured)` in your bus, from the first middleware to the count that comes back, and say why each step is there.",
  "answer": "The call enters the middleware chain that the constructor built once by folding a copy of the list. Each middleware runs its code on the way in and calls `next`; dedupe stops a redelivery here by returning 0, using `seen.add` so the check and the insert are one step. At the end of the chain, `deliver` gets the dispatch keys for `PaymentCaptured` from a per-class cache: `PaymentCaptured`, `MoneyMovement`, `PaymentEvent`. For each key it iterates a copy-on-write snapshot of the adapters stored there, so a handler can unsubscribe itself. Each adapter casts the event with `type.cast` and calls the real handler. Every call is wrapped in a `try`, so one failing handler is reported to the error handler and the rest still run. The number of calls comes back out through the chain, where logging can record it. A handler for any event fits under any key because `Handler` is declared `in`."
 },
 "deeper": {
  "minutes": 10,
  "body": """Three extensions come up as soon as this bus meets real traffic.

Asynchronous delivery. Give the bus an `Executor` and let `deliver` submit each handler call instead of making it. Two things change. Errors no longer come back to the publisher, so the `ErrorHandler` becomes the only place they surface. And ordering is gone: two captures for the same payment can run in either order on two pool threads. If order per payment matters, and in a ledger it does, route each payment id to one single-threaded lane, for example `lanes[abs(id.hashCode() % lanes.size)]`, which is what a Kafka partition does for you between services. Bound the executor's queue, or a slow handler turns into an `OutOfMemoryError`.

Generic events. This bus keys by `KClass`, which is enough because no event has a type parameter. If you ever publish an `Envelope<PaymentCaptured>`, the class key collapses every envelope into one, the problem from *KClass, Class and type tokens*. Key by `KType` from `typeOf<T>()` then, and know that the supertype walk gets harder: `KType` has no cheap "all supertypes" answer without kotlin-reflect.

Guava's own verdict. Guava's `EventBus` Javadoc now opens with "We recommend against using EventBus", and its list of reasons reads like a review of any in-process bus: cross-references between producer and subscriber are hard to find, it gives little control of threading, it has no backpressure, and it doesn't propagate exceptions. Lesson 3's design review starts from that list. An in-process bus is still the right tool for decoupling modules inside one service, as long as handlers stay fast and the events that must survive a crash also go to an outbox."""
 },
 "sources": [
  {"title": "Guava EventBus source and Javadoc", "url": "https://raw.githubusercontent.com/google/guava/master/guava/src/com/google/common/eventbus/EventBus.java"},
  {"title": "Generics: in, out, where (Kotlin docs)", "url": "https://kotlinlang.org/docs/generics.html"},
  {"title": "Calling Kotlin from Java (Kotlin docs)", "url": "https://kotlinlang.org/docs/java-to-kotlin-interop.html"},
  {"title": "Functional (SAM) interfaces (Kotlin docs)", "url": "https://kotlinlang.org/docs/fun-interfaces.html"},
  {"title": "CopyOnWriteArrayList (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CopyOnWriteArrayList.html"}
 ]
}
out = ROOT / "content/lessons/cap3-02.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
