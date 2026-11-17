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
    '<svg viewBox="0 0 680 270" role="img" aria-label="Publishing a ParcelCollected: the bus looks up three dispatch keys, nearest first: '
    'ParcelCollected, then Handover, then ParcelEvent. Under each key it calls the handlers in subscription order: the load board and texts, '
    'then the handover log, then tracking. The ParcelDelivered key is never visited.">'
    '<text class="t-s t-m" x="285" y="24" text-anchor="middle">dispatch keys, nearest first</text>'
    '<text class="t-s t-m" x="540" y="24" text-anchor="middle">handlers, in subscription order</text>'
    '<rect class="box-a" x="10" y="100" width="150" height="50" rx="8"/>'
    '<text class="t-s t-code" x="85" y="121" text-anchor="middle">ParcelCollected</text>'
    '<text class="t-s" x="85" y="139" text-anchor="middle">publish(scan)</text>'
    '<line class="ln" x1="160" y1="118" x2="206" y2="60" marker-end="url(#arr)"/>'
    '<line class="ln" x1="160" y1="125" x2="206" y2="128" marker-end="url(#arr)"/>'
    '<line class="ln" x1="160" y1="132" x2="206" y2="196" marker-end="url(#arr)"/>'
    '<rect class="box" x="210" y="40" width="150" height="36" rx="8"/>'
    '<text class="t-s t-code" x="285" y="63" text-anchor="middle">1 ParcelCollected</text>'
    '<rect class="box-b" x="210" y="110" width="150" height="36" rx="8"/>'
    '<text class="t-s t-code" x="285" y="133" text-anchor="middle">2 Handover</text>'
    '<rect class="box" x="210" y="180" width="150" height="36" rx="8"/>'
    '<text class="t-s t-code" x="285" y="203" text-anchor="middle">3 ParcelEvent</text>'
    '<line class="ln-a" x1="360" y1="58" x2="406" y2="58" marker-end="url(#arr)"/>'
    '<line class="ln-a" x1="360" y1="128" x2="406" y2="128" marker-end="url(#arr)"/>'
    '<line class="ln-a" x1="360" y1="198" x2="406" y2="198" marker-end="url(#arr)"/>'
    '<rect class="box-ok" x="410" y="40" width="260" height="36" rx="8"/>'
    '<text class="t-s" x="540" y="63" text-anchor="middle">load board, then texts</text>'
    '<rect class="box-ok" x="410" y="110" width="260" height="36" rx="8"/>'
    '<text class="t-s" x="540" y="133" text-anchor="middle">handover log</text>'
    '<rect class="box-ok" x="410" y="180" width="260" height="36" rx="8"/>'
    '<text class="t-s" x="540" y="203" text-anchor="middle">tracking</text>'
    '<rect class="box-dim" x="210" y="228" width="150" height="32" rx="8"/>'
    '<text class="t-s t-m t-code" x="285" y="249" text-anchor="middle">ParcelDelivered</text>'
    '<rect class="box-dim" x="410" y="228" width="260" height="32" rx="8"/>'
    '<text class="t-s t-m" x="540" y="249" text-anchor="middle">deliveries: not visited</text>'
    '</svg>'
)

OPENING = """The Generics workshop ended at the fruit shop's back door, with a board of bells: one bell for each kind of delivery, and everyone who asked to hear a bell came when it rang. Pedal Post needs the same board in its depot, where the bikes wait between rides. When a rider scans PP-7781 as collected, the load board and the text sender come for that bell. The tracking page wants every bell, and the handover log, kept for insurance, wants every handover.

The trap is in how the board finds its listeners. The workshop's board kept one list per exact kind of event. Sign the tracking page up for "every parcel event", and it never hears a thing, because no scan is ever just "a parcel event". It compiles, and the page stays blank.

A sealed event model gave us the events. In this lesson, we'll build the bus that carries them. It will deliver to each kind and every wider one, let general handlers sign up anywhere, survive a broken handler, and run a chain and a timer. Before we start, make a guess, and keep it in mind."""

S1 = """Let's set up the words first. The bus is the object in the middle. A handler, a small object that reacts to one kind of event, subscribes: it signs up with the bus for one type of event. Code that has news publishes an event, and the bus delivers it to every handler that signed up. Inside, the bus keeps a registry, a map from each event type to the list of handlers that signed up for it.

Generics workshop: a type-safe container and event bus keyed that registry by `event::class`, the event's class when the program runs. That has a hole, the one from the warm-up. A tracking handler subscribed under `ParcelEvent::class` never runs, because no event's class is the interface `ParcelEvent` itself. It's always one of the leaves. The same goes for a handler of `Handover`. Lesson 1 of this track made that middle level on purpose, so the bus has to honor it.

There are two honest fixes. The first keeps one flat list of (type, handler) pairs and asks `type.isInstance(event)` of each pair. It's short and correct, and every publish checks every subscription: forty handlers means forty checks per scan, almost all of them misses. The second keeps the registry keyed by class and works out, for each event class, the list of keys to visit: the class itself, then each supertype that is an event, nearest first. A supertype is a type a class extends or implements, directly or further up. We'll call that list the dispatch keys:

```java
static List<Class<?>> dispatchKeys(Class<?> type) {
    LinkedHashSet<Class<?>> found = new LinkedHashSet<>();
    ArrayDeque<Class<?>> queue = new ArrayDeque<>(List.of(type));
    while (!queue.isEmpty()) {
        Class<?> c = queue.removeFirst();
        if (!ParcelEvent.class.isAssignableFrom(c) || !found.add(c)) continue;
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
        if (!ParcelEvent::class.java.isAssignableFrom(c) || !found.add(c)) continue
        queue.addAll(c.interfaces)
        c.superclass?.let(queue::add)
    }
    found.map { it.kotlin }
}
```

Let's read it in order. The queue starts with the event's own class. Each turn takes the next class off the queue and skips it if it isn't an event or was already found. Otherwise it adds the class's interfaces and superclass to the back of the queue. For `ParcelCollected` the walk gives `[ParcelCollected, Handover, ParcelEvent]`, and publish looks up only those three keys. The order is breadth-first, one level at a time, and it's a promise to callers: the most specific handlers run first, then each wider kind, and within one key, handlers run in the order they subscribed.

The walk uses plain Java reflection, `getInterfaces()` and `getSuperclass()`, so it needs no extra library. KClass, Class and type tokens kept kotlin-reflect, the 3.8 MB library behind Kotlin's fuller reflection, in a reference book in the other room: naming and casting a class need no trip there, and describing one does. The answer never changes for a class, so `computeIfAbsent` caches it, once per class. On a `ConcurrentHashMap` that call is one atomic step, which nothing can interrupt halfway. So two threads, two paths of work running at the same time, can't both fill the cache when they publish the first collection together, as Concurrent collections showed.

Before you run the demo, predict the keys it prints for `DeliveryFailed`."""

S2 = """`Handler<E>` is the labelled box from Generics from zero: type parameters, "Handler of ___", with a blank that each subscription fills in. A handler only ever takes an event in. It never hands one back. A type that only handed events out would be the apple dispenser of Covariance with out: producers, and it would be `out`. A handler is the other kind. Contravariance with in: consumers had a compost bin behind the fruit shop: bruised fruit of any kind goes in, nothing comes out, and so the bin for any fruit makes a perfectly good bin for apples. A handler is that bin. One that takes any parcel event makes a perfectly good handler for collections. That lesson's rule says how to write it down: a type parameter that only goes in is declared `in`.

```java
@FunctionalInterface
interface Handler<E extends ParcelEvent> { void handle(E event); }    // Java: no variance on the declaration

<E extends ParcelEvent> Subscription subscribe(Class<E> type, Handler<? super E> handler) { ... }
```

```kotlin
fun interface Handler<in E : ParcelEvent> { fun handle(event: E) }

fun <E : ParcelEvent> subscribe(type: KClass<E>, handler: Handler<E>): Subscription { ... }
```

Now the tracking handler, written once for every event, fits any subscription: `bus.subscribe(ParcelCollected::class, tracking)` compiles with `tracking: Handler<ParcelEvent>`. Delete the `in`, and the clerk at the storeroom door, the compiler checking every label, turns the same line away: `Argument type mismatch: actual type is 'Handler<ParcelEvent>', but 'Handler<ParcelCollected>' was expected.` Java has no variance on declarations, so the Java version writes `? super E` at every use: the "consumer super" half of PECS, Java's rule of thumb "producer extends, consumer super". kotlinc writes that wildcard for us: the Java signature of the Kotlin `subscribe` is `subscribe(KClass<E>, Handler<? super E>)`. That's why the Java callers of lesson 3 get the same freedom without asking.

Why a `fun interface`, an interface with one abstract method that a lambda can implement, and not the function type `(E) -> Unit`? A function type is already `in` on its parameter, so variance would come free. But Java would see a `Function1<? super E, Unit>`, and every Java lambda would have to end with `return Unit.INSTANCE`. A `fun interface` with a `void` method takes a plain Java lambda. Lesson 3 is all about that Java surface.

Inside the bus, handlers for different types share one map, so each one is stored behind an adapter that takes any `ParcelEvent`:

```java
Handler<ParcelEvent> adapter = event -> handler.handle(type.cast(event));
```

```kotlin
val adapter = Handler<ParcelEvent> { event -> handler.handle(type.cast(event)) }
```

The adapter is part travel plug, part receptionist, two pictures from the Design patterns track. Like the plug, it makes a narrow handler fit a list of general ones. Like the receptionist who answers for a busy manager, it checks each call before putting it through. The workshop's receptionist was polite: with `safeCast`, a call meant for someone else was quietly not put through. Ours is strict. The dispatch keys already guarantee the type, so a wrong event here can only be a bug in the bus, and `cast` makes that bug loud. The next section makes sure loud doesn't mean fatal.

Kotlin callers also get a reified wrapper. It's `inline`, the print shop's photocopy pasted into each caller, so it can be reified: it's the clerk from Type erasure and reified type parameters who copies the label onto a note before it's torn off: `inline fun <reified E : ParcelEvent> subscribe(handler: Handler<E>) = subscribe(E::class, handler)`. It needs no `noinline`. Only parameters of a function type are inlined, as Inline functions: noinline, crossinline and non-local returns showed, and a `Handler` is an ordinary object.

In the demo, delete `in` and predict which two lines break."""

S3 = """The bus is the sign-up sheet from Observer and Command, the one by the corner shop's door that says "ring me when the fresh bread arrives". Anyone can sign up, anyone can cross their name off, and one broken phone mustn't stop the shopkeeper from ringing the rest. Those are three rules, and the lab tests each one.

First, `subscribe` returns a handle. `Subscription` extends `AutoCloseable`, the JDK interface behind try-with-resources, and closing it removes exactly the adapter that `subscribe` stored. Closing it twice is harmless. Without a handle, a handler that belongs to a short-lived object stays in the map for ever. That's a lapsed listener: a name nobody can cross off, still rung for every event. It also keeps alive an object the program has finished with, so the garbage collector, the part of the JVM that frees objects nobody uses any more, can never free it.

Second, one failing handler must not stop the others. `deliver` catches `Exception` around each call and reports it, with the event, to an `ErrorHandler`, a small callback the bus was given when it was built:

```java
for (Handler<ParcelEvent> handler : handlers) {     // a snapshot: copy-on-write
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

It catches `Exception`, not `Throwable`, because an `OutOfMemoryError` should still stop the program. And the bus doesn't decide what an error means. The program does, through its `ErrorHandler`: it can count the failure, log it, or keep the event to try again later.

**A handler that throws is one bug. Catch it per handler, and report it.**

Third, delivery walks a snapshot. Each key's handlers live in a `CopyOnWriteArrayList`, a list that copies its array on every change. A loop over it sees the list as it was when the loop began. A handler may close its own subscription while it runs, like a welcome text that should go out only once, and the loop carries on. With an `ArrayList`, the loop's next step throws `ConcurrentModificationException`. Copying the array on every `subscribe` sounds expensive, and it would be for a list that changed all day. Subscriptions change at start-up; scans arrive all day.

Those two collections also make the bus safe for many publishers without a lock of its own, the tool that lets one thread in at a time. `ConcurrentHashMap` guards the registry, and each list swaps in a new array instead of changing the old one in place, as Concurrent collections described. The lab's load test runs eight publishing threads while another thread subscribes and closes in a loop, and it counts every event.

One thing doesn't change: delivery is synchronous. Every handler runs on the publisher's thread, before `publish` returns. A text that takes 300 ms to send makes every scan 300 ms slower. Keep handlers fast; lesson 3's design review comes back to the slow ones.

The demo runs the same three handlers on three buses. Predict what each run prints before you run it."""

ASIDE = {
    "title": "Is there a ready-made bus I could use instead?",
    "body": "There are several, and knowing this one helps you read them. Guava, Google's library of Java utilities, has an `EventBus` that routes the same way, to subscribers of \"any type to which the event is assignable\". Its own documentation now opens with \"We recommend against using EventBus\", for reasons this lesson can name: it gives little control over threads, it has no way to slow a fast publisher down, and it doesn't pass handler exceptions back to the program. Web frameworks have buses too, such as CDI events in Quarkus, received by methods marked `@Observes`. For any of them, check the three things we built by hand: the delivery order, what happens when a handler throws, and which thread runs it.",
}

S4 = """Some extra work belongs to every event, once: logging each one, or dropping a scan that arrives twice. Some belongs to one handler only, such as timing the text sender. The first kind is a chain around `publish`. The second is a wrapper around one handler. They look alike, and choosing the wrong one gives the wrong numbers.

The chain is the one from State and Chain of Responsibility, where a complaint went from the shop assistant to the manager to head office. Each of them answered it or passed it on. Here, each middleware, a link in the chain around delivery, gets the event and `next`, the rest of the chain. It passes the event on, or returns 0 to stop it. The bus builds the chain once, when it's created, by folding a copy of the list from the right: combining its links one at a time, starting from the last, into a single `Next`. So the first middleware wraps all the others, and the last one wraps delivery:

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

Order is behavior. With `[dedupe, logging]`, a repeated scan is dropped before anything logs it. With `[logging, dedupe]`, it's logged and then dropped, which is what you want if you need to count repeats. Pick one and pin it in a test.

Why would a scan arrive twice? A scanner that hears no answer on a weak signal sends the scan again, to be safe. Its caution is admirable, and its arithmetic is terrible: the load board would add 2.5 kg twice. The dedupe middleware is one line, `if (seen.add(event)) next.proceed(event) else 0`. `add` is the check and the act in one step, the fix from Race conditions: why count++ lies, so eight threads can't all let the same scan through. Its idea of "the same event" is data-class equality: the same type, the same tracking number, the same weight.

The wrapper is the decorator from Decorator and Proxy, the gift paper around a teapot. It implements the same `Handler<E>`, adds one thing and passes the call on, and the bus handles the wrapped handler exactly as before:

```java
static <E extends ParcelEvent> Handler<E> timed(Handler<E> inner, String name, Timings timings) {
    return event -> {
        long start = timings.ticker().nanos();
        try { inner.handle(event); }
        finally { timings.record(name, timings.ticker().nanos() - start); }
    };
}
```

```kotlin
fun <E : ParcelEvent> Handler<E>.timed(name: String, timings: Timings): Handler<E> {
    val inner = this
    return Handler { event ->
        val start = timings.ticker.nanos()
        try { inner.handle(event) } finally { timings.record(name, timings.ticker.nanos() - start) }
    }
}
```

It records in `finally`, so a handler that throws is timed too, and the exception still reaches the bus's `try`. The clock is a `Ticker` passed in. Tests use a fake one that moves forward by a fixed step on every read, so they check exact numbers, with no sleeps and no flaky margins. A timing middleware couldn't do this job. It sees one delivery to all of an event's handlers, so it would add the load board's 2 ms to the text sender's 300 ms.

In the demo, swap the first two middleware and predict what the repeated scan prints."""

CLOSING = """We started at the depot with a board of bells and a tracking page that never heard a thing. Now one publish visits the event's own kind and every wider one, nearest first. A general handler fits any bell because `Handler` is `in`, and a broken handler stays a local problem.

Now look in your own code for an `addListener` or `subscribe` call whose result is thrown away, and for a loop over listeners with no `try` inside it.

Next, we'll give the bus a front door for Kotlin and a side door for Java. How do you wire a dozen handlers in one readable block, and close them all with one handle?"""

L = {
 "id": "cap3-02",
 "title": "A typed event bus",
 "minutes": 40,
 "goal": "By the end you can build an in-process event bus that routes each event to the handlers of its class and of every event supertype, declare its handler type `in` so one general handler fits any subscription, keep a failing or self-removing handler from hurting the others, and add a middleware chain around delivery and a timing decorator around one handler.",
 "opening": OPENING,
 "warmup": {
  "q": "The board of bells from *Generics workshop: a type-safe container and event bus* stores handlers in a map keyed by `event::class`. You subscribe a tracking handler under `ParcelEvent::class` and publish a `ParcelCollected`. How many times does the tracking handler run?",
  "options": [
   "Once: a ParcelCollected is a ParcelEvent",
   "Never: no event's class is the interface ParcelEvent itself",
   "It doesn't compile: you can't subscribe under an interface",
   "Twice: once for the class and once for the interface"
  ],
  "answer": 1,
  "why": "The lookup uses the event's exact class, `ParcelCollected`, and nobody subscribed under that key. The subscription itself compiles, because `ParcelEvent::class` is a perfectly good `KClass<ParcelEvent>`. Delivering to supertypes takes a walk up the event's type hierarchy, which this lesson adds."
 },
 "sections": [
  {
   "h": "Route each event to its own class, then up through its supertypes",
   "body": S1,
   "figure": {"svg": FIG, "caption": "One publish visits three keys, nearest first, and calls each key's handlers in the order they subscribed. Keys of sibling types are never touched."},
   "try": {
    "title": "Exact class versus supertypes",
    "minutes": 4,
    "steps": [
     "Read `DispatchDemo.kt` (or `DispatchDemoJava.java`). Three handlers subscribe under three types, and the same collection is published to a bus that looks up the exact class only, then to one that walks the supertypes.",
     "Predict both `ran` lists and the keys for `DeliveryFailed`. Run it.",
     "Add `bus.subscribe(Handover::class) { ran += \"insurance\" }` (in Java, `bus.subscribe(Handover.class, e -> ran.add(\"insurance\"))`) as the last subscription, after the load line. Predict where `insurance` appears in the second list, then run."
    ],
    "code": demo("dispatch", "DispatchDemo"),
    "expect": "`exact class only: [load]` and `walking supertypes: [load, handovers, tracking]`. The keys are `[ParcelCollected, Handover, ParcelEvent]` and `[DeliveryFailed, ParcelEvent]`. After your change the second list is `[load, handovers, insurance, tracking]`: keys go nearest first, and within the `Handover` key the handlers run in subscription order."
   },
   "refs": [{"title": "Guava EventBus source and Javadoc", "url": "https://raw.githubusercontent.com/google/guava/master/guava/src/com/google/common/eventbus/EventBus.java", "kind": "read"}]
  },
  {
   "h": "A handler only takes events in, so declare it in",
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
    "expect": "With `in`, the tracking handler runs for both collections, and the signature ends with `Handler<? super E>)`. Without it, kotlinc reports `Argument type mismatch: actual type is 'Handler<ParcelEvent>', but 'Handler<ParcelCollected>' was expected.` at the subscribe call and `Initializer type mismatch: expected 'Handler<ParcelCollected>', actual 'Handler<ParcelEvent>'.` at `forCollections`. `tooWide` fails the other way round: `Initializer type mismatch: expected 'Handler<ParcelEvent>', actual 'Handler<ParcelCollected>'.` javac, without `? super`, says `inference variable E has incompatible equality constraints ParcelEvent,ParcelCollected`."
   },
   "refs": [{"title": "Calling Kotlin from Java: variant generics (Kotlin docs)", "url": "https://kotlinlang.org/docs/java-to-kotlin-interop.html", "kind": "docs"}]
  },
  {
   "h": "The sign-up sheet's three rules: a way to leave, failures kept apart, a snapshot to walk",
   "body": S3,
   "aside": ASIDE,
   "try": {
    "title": "One bad handler, three buses",
    "minutes": 4,
    "steps": [
     "Read `IsolationDemo`. The first handler unsubscribes itself, the second always throws, the third texts the sender. Each bus gets two collections.",
     "Predict the output of each of the three runs. Run it.",
     "In the isolated run, change `catch (e: Exception)` to catch only `IllegalArgumentException` (in Java, change `RuntimeException` to `IllegalArgumentException`). Predict, then run."
    ],
    "code": demo("isolation", "IsolationDemo"),
    "expect": "The `ArrayList` bus prints the welcome text and then `publish threw java.util.ConcurrentModificationException`, because the list changed under its own loop. The copy-on-write bus without isolation gets past that and dies on `load board is down`; no text goes to the sender. The isolated bus sends both texts and reports two errors. With the narrower catch, the third run fails like the second: the `IllegalStateException` is no longer caught."
   },
   "refs": [{"title": "CopyOnWriteArrayList (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CopyOnWriteArrayList.html", "kind": "docs"}]
  },
  {
   "h": "Work for every event goes in a chain, work for one handler in a wrapper",
   "body": S4,
   "try": {
    "title": "Reorder the chain",
    "minutes": 4,
    "steps": [
     "Run `ChainDemo` and read the nesting of the `>` and `<` lines.",
     "Swap `logging(\"outer\")` and `dropDuplicates()` in the list. Predict what the repeated scan prints now, and run.",
     "Change `tick()` to add 90,000 instead of 40,000. Predict the `load took` line before you run."
    ],
    "code": demo("chain", "ChainDemo"),
    "expect": "First run: `outer >`, `inner >`, the load board lines, then `inner <` and `outer <` in reverse. The repeated scan prints `outer > PP-7781` and `outer < PP-7781: 0 handler(s)`: logged, then dropped. After the swap, the repeated scan prints nothing at all below the `--` line. With 90,000 per read, `load took 90 us`: the decorator reads the clock twice, so the time is exactly one step."
   }
  }
 ],
 "compare": {
  "title": "The bus in Java and Kotlin",
  "java": {
   "title": "EventBus.java",
   "src": "@FunctionalInterface interface Handler<E extends ParcelEvent> { void handle(E event); }\n@FunctionalInterface interface ErrorHandler { void onError(ParcelEvent event, Exception error); }\n@FunctionalInterface interface Next { int proceed(ParcelEvent event); }\n@FunctionalInterface interface Middleware { int intercept(ParcelEvent event, Next next); }\n\nfinal class EventBus {\n    private final Map<Class<?>, List<Handler<ParcelEvent>>> registry = new ConcurrentHashMap<>();\n    private final Map<Class<?>, List<Class<?>>> keyCache = new ConcurrentHashMap<>();\n    private final ErrorHandler onError;\n    private final Next pipeline;\n\n    EventBus(List<Middleware> middleware, ErrorHandler onError) {\n        this.onError = onError;\n        Next next = this::deliver;\n        for (Middleware m : List.copyOf(middleware).reversed()) {   // reversed(): JDK 21\n            Next rest = next;\n            next = event -> m.intercept(event, rest);\n        }\n        this.pipeline = next;\n    }\n\n    <E extends ParcelEvent> AutoCloseable subscribe(Class<E> type, Handler<? super E> handler) {\n        Handler<ParcelEvent> adapter = event -> handler.handle(type.cast(event));\n        List<Handler<ParcelEvent>> handlers = registry.computeIfAbsent(type, t -> new CopyOnWriteArrayList<>());\n        handlers.add(adapter);\n        return () -> handlers.remove(adapter);\n    }\n\n    int publish(ParcelEvent event) { return pipeline.proceed(event); }\n\n    private int deliver(ParcelEvent event) {\n        int called = 0;\n        for (Class<?> key : keyCache.computeIfAbsent(event.getClass(), EventBus::dispatchKeys)) {\n            for (Handler<ParcelEvent> h : registry.getOrDefault(key, List.of())) {\n                called++;\n                try { h.handle(event); } catch (Exception e) { onError.onError(event, e); }\n            }\n        }\n        return called;\n    }\n\n    private static List<Class<?>> dispatchKeys(Class<?> type) { /* breadth-first walk, as above */ }\n}"
  },
  "kotlin": {
   "title": "EventBus.kt",
   "src": "fun interface Handler<in E : ParcelEvent> { fun handle(event: E) }\nfun interface Next { fun proceed(event: ParcelEvent): Int }\nfun interface Middleware { fun intercept(event: ParcelEvent, next: Next): Int }\n\nclass EventBus(\n    middleware: List<Middleware> = emptyList(),\n    private val onError: ErrorHandler = ErrorHandler.PRINT,\n) {\n    private val registry = ConcurrentHashMap<KClass<*>, CopyOnWriteArrayList<Handler<ParcelEvent>>>()\n    private val keyCache = ConcurrentHashMap<Class<*>, List<KClass<*>>>()\n    private val pipeline: Next = middleware.toList()\n        .foldRight(Next(::deliver)) { m, next -> Next { event -> m.intercept(event, next) } }\n\n    fun <E : ParcelEvent> subscribe(type: KClass<E>, handler: Handler<E>): Subscription {\n        val adapter = Handler<ParcelEvent> { event -> handler.handle(type.cast(event)) }\n        val handlers = registry.computeIfAbsent(type) { CopyOnWriteArrayList() }\n        handlers += adapter\n        return Subscription { handlers.remove(adapter) }\n    }\n\n    inline fun <reified E : ParcelEvent> subscribe(handler: Handler<E>): Subscription = subscribe(E::class, handler)\n\n    fun publish(event: ParcelEvent): Int = pipeline.proceed(event)\n\n    private fun deliver(event: ParcelEvent): Int {\n        var called = 0\n        for (key in dispatchKeys(event.javaClass)) {\n            for (handler in registry[key] ?: continue) {\n                called++\n                try { handler.handle(event) } catch (e: Exception) { onError.onError(event, e) }\n            }\n        }\n        return called\n    }\n\n    private fun dispatchKeys(type: Class<*>): List<KClass<*>> = keyCache.computeIfAbsent(type) { /* the walk */ }\n}"
  },
  "note": "Both buses work the same way: the same registry, the same walk, the same adapter, the same fold and the same `try` around each handler. The differences are in who writes what. Java writes `Handler<? super E>` at the use site; Kotlin declares `in` once, and kotlinc puts the wildcard into the Java signature. Kotlin gets default arguments on the constructor and a reified `subscribe<E>` for its own callers; Java callers get neither until lesson 3 adds `@JvmOverloads` and a `Class<E>` overload. And Kotlin's `Next(::deliver)` turns a function reference into a `fun interface` object, where Java writes `this::deliver` against its functional interface."
 },
 "worked": {
  "title": "Wire up delivery texts, and put each concern in its place",
  "steps": [
   {
    "say": "Every delivery should send the receiver a text: \"your parcel is at your door\". That's one handler for one event type. Subscribe it under `ParcelDelivered`, the most specific key, so it never hears about a collection.",
    "code": "val texts = Handler<ParcelDelivered> { sms.send(it.parcelId, \"your parcel is at your door\") }\nval textsSubscription = bus.subscribe<ParcelDelivered>(texts)",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "// the Java bus from the comparison below\nHandler<ParcelDelivered> texts = e -> sms.send(e.parcelId(), \"your parcel is at your door\");\nAutoCloseable textsSubscription = bus.subscribe(ParcelDelivered.class, texts);"
   },
   {
    "say": "The text service fails about one call in two hundred. Isolation already keeps the load board and the tracking page running when it does. What the program still has to decide is what a failure means. Here the error handler counts it and keeps the event on a list to try again later.",
    "code": "val bus = EventBus(\n    middleware = listOf(DropDuplicates()),\n    onError = ErrorHandler { event, error ->\n        failures.incrementAndGet()\n        tryAgainLater += event to error.toString()\n    },\n)",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "ErrorHandler onError = (event, error) -> {\n    failures.incrementAndGet();\n    tryAgainLater.add(Map.entry(event, error.toString()));\n};\nEventBus bus = new EventBus(List.of(new DropDuplicates()), onError);"
   },
   {
    "say": "A scanner on a weak signal sends some scans twice, and nobody wants two texts for one parcel. Dropping repeats applies to every event once, before any handler, so it's middleware, first in the list. A wrapper around the texts handler would drop repeated texts only, and the load board would still add the weight twice.",
    "code": "middleware = listOf(DropDuplicates(), logging)     // dedupe first: repeats are never logged",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "List<Middleware> middleware = List.of(new DropDuplicates(), logging);   // dedupe first: repeats are never logged"
   },
   {
    "say": "How long does a text take? That's a question about one handler, so it's a decorator: wrap the handler, not the bus. The timings now show about 300 ms per delivery under `texts`, all of it spent on the thread that published the scan. That number is the case for handing slow work to another thread, which lesson 3's design review makes.",
    "code": "bus.subscribe<ParcelDelivered>(texts.timed(\"texts\", timings))",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "bus.subscribe(ParcelDelivered.class, timed(texts, \"texts\", timings));   // the static timed(...) from the last section"
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
   "TODO 4, `pipeline`: fold a copy of `middleware` from the right, starting from `Next(::deliver)`. TODO 5: the reified `subscribe`, in one line.",
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
  "prompt": "Close the lab. From memory, write `deliver(event)` (dispatch keys, handlers in order, a count, one `try` per handler) and the one expression that builds the middleware chain. Then answer: with `[logging, dedupe]`, does a repeated scan get logged?",
  "answer": {
   "lang": "kotlin",
   "src": "private fun deliver(event: ParcelEvent): Int {\n    var called = 0\n    for (key in dispatchKeys(event.javaClass)) {\n        for (handler in registry[key] ?: continue) {        // copy-on-write snapshot\n            called++\n            try {\n                handler.handle(event)\n            } catch (e: Exception) {\n                onError.onError(event, e)\n            }\n        }\n    }\n    return called\n}\n\nprivate val pipeline: Next = middleware.toList()\n    .foldRight(Next(::deliver)) { m, next -> Next { event -> m.intercept(event, next) } }\n\n// [logging, dedupe]: yes. logging runs first, then dedupe returns 0.",
   "alt": {
    "lang": "java",
    "src": "private int deliver(ParcelEvent event) {\n    int called = 0;\n    for (Class<?> key : dispatchKeys(event.getClass())) {\n        for (Handler<ParcelEvent> handler : registry.getOrDefault(key, List.of())) {\n            called++;\n            try {\n                handler.handle(event);\n            } catch (Exception e) {\n                onError.onError(event, e);\n            }\n        }\n    }\n    return called;\n}\n\nNext next = this::deliver;\nfor (int i = middleware.size() - 1; i >= 0; i--) {\n    Middleware m = middleware.get(i);\n    Next rest = next;\n    next = event -> m.intercept(event, rest);\n}\nthis.pipeline = next;\n\n// [logging, dedupe]: yes. logging runs first, then dedupe returns 0."
   }
  }
 },
 "closing": CLOSING,
 "recap": [
  "Keying handlers by the exact class misses subscriptions under `Handover` and `ParcelEvent`. Walk the event's supertypes, nearest first, cache the walk per class, and look up each key.",
  "A handler only consumes events, so it is `Handler<in E>`. A `Handler<ParcelEvent>` then fits any subscription, and Java sees `Handler<? super E>` without writing it.",
  "Store each handler behind an adapter that takes any event and casts with `type.cast`. The keys guarantee the type, so a failed cast is a loud bug in the bus.",
  "Return a handle from `subscribe`, catch `Exception` per handler and report it to an `ErrorHandler`, and loop over a copy-on-write list so a handler can unsubscribe itself.",
  "Work for every event once (logging, dropping repeats) is middleware: a chain built once by a fold, where order is behavior. Work for one handler (timing) is a decorator, tested with a fake `Ticker`.",
  "Where today's bus stops: Java can reach it only the long way round, wiring a dozen handlers means a dozen handles, and delivery is synchronous, so one slow handler slows every publish."
 ],
 "quiz": [
  {
   "q": "From *Contravariance with in: consumers*: with `fun interface Handler<in E : ParcelEvent>`, `tracking: Handler<ParcelEvent>` and `load: Handler<ParcelCollected>`, which line compiles?",
   "options": [
    "`val h: Handler<ParcelEvent> = load`",
    "`val h: Handler<Handover> = load`",
    "`val h: Handler<ParcelCollected> = tracking`",
    "`val h: Handler<ParcelDelivered> = load`"
   ],
   "answer": 2,
   "why": "For a consumer the arrow flips, like the compost bin that makes a fine apple bin: something that takes any event can stand in for something that takes collections. The other three ask a collections-only handler to accept events it can't handle, a delivery or any handover, so the compiler refuses them.",
   "from": "gen-05"
  },
  {
   "q": "From *Observer and Command*: a `RiderScreen` object is created each time a rider logs in, and it subscribes to the bus in its constructor. It never closes its `Subscription`. What happens after a few thousand log-ins?",
   "options": [
    "Nothing: the garbage collector removes the old screens once nobody uses them",
    "Every old screen is still in the registry, can't be collected, and still reacts to each event",
    "The bus throws when the registry grows past a limit",
    "Only the newest screen receives events"
   ],
   "answer": 1,
   "why": "The registry holds a reference to each adapter, and each adapter holds the screen's handler. That's the lapsed listener: memory grows with every log-in, and every scan now runs thousands of stale handlers. The garbage collector can't help, because the bus still reaches every old screen. Closing the handle when the screen closes removes it.",
   "from": "pat-08"
  },
  {
   "q": "From *State and Chain of Responsibility*: the bus is built with `middleware = [dedupe, logging]`. A scanner sends a scan the bus has already seen. What does the log show for the repeat?",
   "options": [
    "Nothing: dedupe returns 0 before logging runs",
    "A log line with 0 handlers",
    "A log line with 1 handler, then dedupe drops it",
    "Two log lines, one per delivery"
   ],
   "answer": 0,
   "why": "The first middleware in the list wraps all the others. Dedupe answers 0 without calling `next`, so logging never sees the event. With `[logging, dedupe]` you'd get a log line ending in 0 handlers, which is the order to choose if you want to count repeats.",
   "from": "pat-09"
  },
  {
   "q": "From *Inline functions: noinline, crossinline and non-local returns*: `inline fun <reified E : ParcelEvent> subscribe(handler: Handler<E>) = subscribe(E::class, handler)` stores the handler in the registry. Why does it compile without `noinline`?",
   "options": [
    "Because `reified` makes every parameter noinline",
    "Because members of a class are never inlined",
    "Because the compiler adds `noinline` automatically when a lambda is stored",
    "Because only parameters of a function type are inlined, and `Handler` is a fun interface"
   ],
   "answer": 3,
   "why": "`inline` pastes in the bodies of lambdas passed to parameters of a function type. A `Handler` argument is an ordinary object, even when the caller writes it as a lambda, so there is nothing to inline and nothing that needs `noinline`. With `handler: (E) -> Unit` it would need `noinline`, as the generics workshop showed.",
   "from": "kt-01"
  },
  {
   "q": "Subscriptions, in this order: `tracking` under `ParcelEvent`, then `handovers` under `Handover`, then `load` under `ParcelCollected`. You publish a `ParcelDelivered`. Which handlers run, in what order?",
   "options": [
    "tracking, handovers",
    "handovers, tracking",
    "tracking, handovers, load",
    "handovers only"
   ],
   "answer": 1,
   "why": "The keys for a delivery are `[ParcelDelivered, Handover, ParcelEvent]`, visited nearest first. Nobody subscribed under `ParcelDelivered`, so `handovers` runs, then `tracking`. Subscription order matters only within one key, which is why the first option is wrong, and `load` sits under a sibling type the walk never visits."
  }
 ],
 "flashcards": [
  {"front": "Why does a bus keyed by `event::class` never call a handler subscribed under `ParcelEvent::class`?", "back": "No event's class is the interface itself. Delivery must also look up each supertype of the event's class."},
  {"front": "In what order does this bus call handlers?", "back": "The event's own class first, then each event supertype, nearest first. Within one key, in subscription order."},
  {"front": "Why is the handler type `Handler<in E>`?", "back": "A handler only consumes events. With `in`, a `Handler<ParcelEvent>` can stand in for a `Handler<ParcelCollected>`."},
  {"front": "What Java signature does kotlinc give `fun <E : ParcelEvent> subscribe(type: KClass<E>, handler: Handler<E>)` when `Handler` is `in`?", "back": "`subscribe(KClass<E>, Handler<? super E>)`: kotlinc turns declaration-site `in` into a `? super` wildcard in parameters."},
  {"front": "Why a `CopyOnWriteArrayList` for each key's handlers?", "back": "Delivery loops over a snapshot, so a handler can unsubscribe itself, and publishers need no lock. Each subscribe copies the array, which is fine because subscriptions rarely change."},
  {"front": "Middleware or decorator: timing one handler?", "back": "Decorator. Middleware wraps one delivery to all of an event's handlers; a decorator wraps one handler and implements its interface."},
  {"front": "Why does `DropDuplicates` test `seen.add(event)` instead of `seen.contains(event)`?", "back": "`add` checks and inserts in one atomic step. Contains-then-add lets two threads pass the same event."}
 ],
 "terms": [
  {"term": "Dispatch keys", "plain": "The list of types a bus looks up for one event: its class, then its event supertypes, nearest first."},
  {"term": "Adapter", "plain": "A small wrapper that lets a Handler<ParcelCollected> be stored as a Handler<ParcelEvent>, by casting each event on the way in."},
  {"term": "Failure isolation", "plain": "Catching each handler's exception so that the other handlers still run."},
  {"term": "Lapsed listener", "plain": "A handler that was never unsubscribed, so the bus keeps it alive and keeps calling it."},
  {"term": "Middleware", "plain": "A link in a chain around publish that can pass an event on, change it or stop it."},
  {"term": "Virtual time", "plain": "A fake clock that tests move forward by hand, so timing can be checked exactly."}
 ],
 "explain_back": {
  "prompt": "Walk a colleague through one `publish(ParcelCollected)` in your bus, from the first middleware to the count that comes back, and say why each step is there.",
  "answer": "The call enters the middleware chain that the constructor built once, by folding a copy of the list. Each middleware runs its code on the way in and calls `next`; dedupe stops a repeated scan here by returning 0, using `seen.add` so the check and the insert are one step. At the end of the chain, `deliver` gets the dispatch keys for `ParcelCollected` from a per-class cache: `ParcelCollected`, `Handover`, `ParcelEvent`. For each key it loops over a copy-on-write snapshot of the adapters stored there, so a handler can unsubscribe itself. Each adapter casts the event with `type.cast` and calls the real handler. Every call is wrapped in its own `try`, so one failing handler is reported to the error handler and the rest still run. The number of calls comes back out through the chain, where logging can record it. And a handler for any event fits under any key because `Handler` is declared `in`."
 },
 "deeper": {
  "minutes": 10,
  "body": """Three extensions come up as soon as a bus like this meets real traffic.

Asynchronous delivery. Give the bus an `Executor` and let `deliver` submit each handler call instead of making it. Two things change. Errors no longer come back to the publisher, so the `ErrorHandler` becomes the only place they show up. And the order is gone: two scans for the same parcel can run in either order on two pool threads. If the order per parcel matters, and for a load board it does, send each tracking number to one single-threaded lane, for example `lanes[abs(id.hashCode() % lanes.size)]`. Bound each lane's queue too, or a slow handler turns into an `OutOfMemoryError`, the lesson of *Inside ThreadPoolExecutor: core, max, queue, rejection*.

Generic events. This bus keys by `KClass`, which is enough because no event has a type parameter. If you ever publish an `Envelope<ParcelCollected>`, the class key files every envelope under one card, the problem from *KClass, Class and type tokens*. Key by `KType` from `typeOf<T>()` then, and know that the supertype walk gets harder: `KType` has no cheap "all supertypes" answer without kotlin-reflect.

Weak listeners. Some buses hold their handlers through weak references, which *Reachability: strong, soft, weak and phantom references* covers in Part 4, so that a forgotten handler can be garbage collected. That hides the lapsed-listener bug instead of fixing it: the stale handler keeps running until the collector happens to run, which may be never in a quiet test. A handle the owner must close is the more honest design."""
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
