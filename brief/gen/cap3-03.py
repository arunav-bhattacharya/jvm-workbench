import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/events/src"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :events:demo -Pmain=workbench.events.l03.demo."
DK = f"{lab}/demo/kotlin/workbench/events/l03/demo"
DJ = f"{lab}/demo/java/workbench/events/l03/demo"


def kotlin_first(pkg, name):
    """A Kotlin demo (NameKt) with a Java twin NameJava, in workbench.events.l03.demo.<pkg>."""
    k, j = f"{DK}/{pkg}/{name}.kt", f"{DJ}/{pkg}/{name}Java.java"
    return {"lang": "kotlin", "title": f"{name}.kt", "src": read(k), "run": f"{DEMO}{pkg}.{name}Kt", "file": k,
            "alt": {"lang": "java", "title": f"{name}Java.java", "src": read(j), "run": f"{DEMO}{pkg}.{name}Java", "file": j}}


def java_first(pkg, name):
    """A Java demo (Name) with a Kotlin twin Name.kt (class NameKt)."""
    j, k = f"{DJ}/{pkg}/{name}.java", f"{DK}/{pkg}/{name}.kt"
    return {"lang": "java", "title": f"{name}.java", "src": read(j), "run": f"{DEMO}{pkg}.{name}", "file": j,
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(k), "run": f"{DEMO}{pkg}.{name}Kt", "file": k}}


FIG = (
    '<svg viewBox="0 0 680 260" role="img" aria-label="Two doors into one core. Kotlin callers come in at the front door, the DSL with reified on functions. '
    'Java callers come in at the side door, Events.subscriptions with a Consumer, backed by Class overloads, JvmOverloads, JvmStatic and JvmField, '
    'the Events facade over the value classes, and Handlers.timed. Both reach the same EventBus and sealed model.">'
    '<rect class="box-a" x="10" y="20" width="160" height="40" rx="8"/>'
    '<text class="t" x="90" y="45" text-anchor="middle">Kotlin callers</text>'
    '<line class="ln" x1="170" y1="40" x2="216" y2="40" marker-end="url(#arr)"/>'
    '<rect class="box" x="220" y="20" width="270" height="40" rx="8"/>'
    '<text class="t-s t-code" x="355" y="45" text-anchor="middle">bus.subscriptions { on&lt;E&gt; { } }</text>'
    '<rect class="box-dim" x="220" y="78" width="270" height="104" rx="8"/>'
    '<text class="t-s t-b" x="355" y="98" text-anchor="middle">the side door for Java</text>'
    '<text class="t-s" x="355" y="118" text-anchor="middle">Class&lt;E&gt; overloads</text>'
    '<text class="t-s" x="355" y="136" text-anchor="middle">@JvmOverloads, @JvmStatic, @JvmField</text>'
    '<text class="t-s" x="355" y="154" text-anchor="middle">Events facade: String and long</text>'
    '<text class="t-s" x="355" y="172" text-anchor="middle">@file:JvmName("Handlers")</text>'
    '<rect class="box-b" x="10" y="200" width="160" height="40" rx="8"/>'
    '<text class="t" x="90" y="225" text-anchor="middle">Java callers</text>'
    '<line class="ln" x1="170" y1="220" x2="216" y2="220" marker-end="url(#arr)"/>'
    '<rect class="box" x="220" y="200" width="270" height="40" rx="8"/>'
    '<text class="t-s t-code" x="355" y="225" text-anchor="middle">Events.subscriptions(bus, b -&gt; ...)</text>'
    '<line class="ln-d" x1="355" y1="200" x2="355" y2="184" />'
    '<rect class="box-ok" x="520" y="95" width="150" height="70" rx="8"/>'
    '<text class="t t-code" x="595" y="123" text-anchor="middle">EventBus</text>'
    '<text class="t-s" x="595" y="145" text-anchor="middle">sealed model</text>'
    '<line class="ln" x1="490" y1="40" x2="540" y2="93" marker-end="url(#arr)"/>'
    '<line class="ln" x1="490" y1="220" x2="540" y2="167" marker-end="url(#arr)"/>'
    '</svg>'
)

OPENING = """Pedal Post's depot has two doors. Riders who work there every day come in at the front and speak the house shorthand: "PP-7781, collected, two and a half." Drivers from a partner courier use the side door, where a clerk hands them the standard printed form. Both doors lead to the same sorting room, under the same rules.

Our library needs both doors. The Kotlin team wants to wire a dozen handlers in a few lines it can read at a glance. The support team writes Java, and Java sees our Kotlin only through the compiled class files, where a reified function vanishes and a getter is called `getWeight-RqKWbHU`. The easy trap is to build the side door by loosening the rules, so that Java can pass in raw numbers nobody checks.

A typed event bus gave us delivery. In this last sitting of Part 3, we'll write a small subscription language for Kotlin and keep its nested blocks in their place. Then we'll give Java a door that still checks everything, and finish with a design review. Before we start, make a guess, and keep it in mind."""

S1 = """Wiring by hand looks like this: five `subscribe` calls, five handles to keep, and a lookup in the program's settings between the third and the fourth. If that lookup throws, three handlers are already live, nobody holds their handles, and the program starts half wired. Type-safe DSLs with lambdas with receivers built the fix at the print shop. A DSL, a small language made for one job, is an order form in code: each section is a block in braces, and inside a block you fill in boxes by name. Behind the form sits a builder that collects what the block declares, and an entry function that runs the block and then acts on all of it at once. Inside a block, the builder is the receiver, the object whose functions the block can call without naming it:

```java
// Java, through the Consumer entry point
Subscription handle = Events.subscriptions(bus, timings, b -> {
    b.on(ParcelEvent.class, e -> tracking.add(e));
    b.on(ParcelCollected.class, Handlers.timed(c -> loadBoard.add(c), "load", timings));
    b.on(ParcelDelivered.class, Handlers.timed(d -> loadBoard.remove(d), "load", timings));
});
```

```kotlin
val handle = bus.subscriptions(timings) {
    on<ParcelEvent> { tracking.add(it) }
    timed("load") {
        on<ParcelCollected> { loadBoard.add(it) }
        on<ParcelDelivered> { loadBoard.remove(it) }
    }
}
```

Each piece of it is a decision. `on` only adds a `Pending(type, handler)` to a list, and `commit` subscribes them all after the block has returned. So a block that throws subscribes nothing, and the caller gets back one `Subscription` that closes everything, in reverse order, the way nested try-with-resources blocks close. `Pending<E>` keeps a type and its handler together, so the builder can hold a `List<Pending<*>>` and still subscribe each entry without a cast. That star is the box whose label wore off, from Star projection: when you don't know the type. We don't know which event type each entry holds, and we don't need to, because each `Pending` knows its own.

`on<ParcelCollected> { ... }` is `inline` with a `reified E`, so it can pass `E::class` on: the clerk's note from Type erasure and reified type parameters again. Its body is `on(E::class, Handler { handler(it) })`, and the compiler stops us right there: `Cannot inline 'handler: (E) -> Unit' here: it might contain non-local returns. Add 'crossinline' modifier to parameter declaration 'handler: (E) -> Unit'.` The lambda is called from inside another object, the `Handler`, which runs later, long after the function that built it has returned. Inline functions: noinline, crossinline and non-local returns pictured that as steps sealed in an envelope for the print shop's night shift: nobody may write "stop the whole job" inside, because the clerk has gone home. `crossinline` is that seal. `noinline` would compile too, but it keeps a lambda object inside each `Handler`; `crossinline` pastes the body into the `Handler` class the compiler generates.

One mistake the DSL can't catch at compile time is calling `on` from inside a handler. The handler lambda has no receiver of its own, so the builder is still in scope, and the call compiles. When the program runs, it would add to a builder that has already committed, and that subscription would silently never exist. A `check(!committed)` in `on` turns the mistake into an `IllegalStateException` at the first event, which the bus's `try` catches and reports.

Before you run the demo, predict the handler count it prints after the block that fails."""

S2 = """Inside `timed("load") { ... }`, two builders are in scope: the `TimedGroup` nearest to us, and the `SubscriptionsBuilder` around it. For a call that names no receiver, Kotlin tries each one in turn, nearest first. `TimedGroup` has no `timed` function, so this compiles:

```java
// Java has no implicit receivers: the same mistake must name the outer builder, b
b.timed("load", g -> {
    g.on(ParcelCollected.class, c -> loadBoard.add(c));
    b.timed("deliveries", d -> { d.on(ParcelDelivered.class, e -> loadBoard.remove(e)); return Unit.INSTANCE; });
    return Unit.INSTANCE;
});
```

```kotlin
timed("load") {
    on<ParcelCollected> { loadBoard.add(it) }
    timed("deliveries") { on<ParcelDelivered> { loadBoard.remove(it) } }   // reaches the OUTER builder
}
```

You meant "time the deliveries inside the load group". What you got is a sibling group: deliveries are timed under `deliveries` only, and the load group's numbers silently miss them. The demo prints `{load=1, deliveries=1}`, where you expected the load group to count two.

The fix is the one that DSL lesson used to keep each section of the form offering only its own boxes. Mark both builder classes with an annotation, a label in the source that tools can read, which is itself annotated `@DslMarker`, and the nested call stops compiling: `'fun timed(name: String, block: TimedGroup.() -> Unit): Unit' cannot be called in this context with an implicit receiver. Use an explicit receiver if necessary.` If you really want a sibling group, say so with a label, `this@subscriptions.timed("deliveries") { ... }`, which nobody types by accident. The marker counts on classes, or on a common superclass, and has no effect on functions.

**A nested block that can reach an outer builder will one day do it by accident. Mark the builders.**

Java never had this problem. Every Java lambda names its parameter, so reaching the outer builder takes `b.timed`, and a reviewer can see it. Java pays elsewhere. `timed` takes a `TimedGroup.() -> Unit`, which Java sees as a `Function1<TimedGroup, Unit>`, so each Java block must end with `return Unit.INSTANCE`. That cost is why the Java entry point, `Events.subscriptions`, takes a `java.util.function.Consumer` instead, and why the lab's Java code times a handler with `Handlers.timed(...)` rather than a group.

In the demo, uncomment the nested `timed`, run it, then delete `@DslMarker` and predict the printed map."""

S3 = """javac, the Java compiler, never reads our Kotlin source. It reads the class files kotlinc wrote, and it reads them very literally. Here is what it finds when Java code meets the API as Kotlin developers usually write it. Every error below comes from the demo:

| Kotlin as written | What Java gets | The fix |
|---|---|---|
| `inline fun <reified E> subscribe(h)` | invisible: `no suitable method found for subscribe((e)->{ })` | a `Class<E>` overload |
| `fun <E> subscribe(type: KClass<E>, h)` | callable through `JvmClassMappingKt.getKotlinClass(X.class)` | the same overload |
| a constructor with default arguments | `new PlainBus()` and the full one only: `no suitable constructor found for PlainBus(String)` | `@JvmOverloads` |
| a member of an `object` | `Registry.INSTANCE.publish(...)` | `@JvmStatic` |
| a companion `val SYSTEM` | `Ticker.Companion.getSYSTEM()` | `@JvmField` |
| top-level functions in `Timing.kt` | `TimingKt.timed(...)` | `@file:JvmName("Handlers")` |
| a data class with value-class properties | `ParcelCollected(String,long) has private access in ParcelCollected`, getters such as `getWeight-RqKWbHU()` | a facade |

Read the table one row at a time with the earlier tracks in mind. A reified function is the clerk's note, and javac can't write one: it can't paste Kotlin code into a Java caller, so kotlinc marks the function synthetic, made by the compiler and hidden from Java source. Type erasure and reified type parameters gave the answer: Java hands over the class itself, `ParcelCollected.class`, so the bus needs an overload, a second `subscribe` with the same name that takes Java's `Class<E>`. The annotations each ask kotlinc for one small thing. `@JvmOverloads` asks for one Java constructor per default argument. `@JvmStatic` makes an `object`'s member a real static method. `@JvmField` exposes a constant as a plain field, and `@file:JvmName` names the class that holds a file's top-level functions.

The facade is the decision that matters, because it touches the checks. A facade, the hotel reception desk from Adapter and Facade, is one small object that gives outsiders a simple way in. Value classes and what they compile to warned that `@JvmName` on a function that takes a value class lets Java pass a raw `long` straight past `init`. Our facade does the opposite. It takes plain values and builds the value classes itself, so every `init` block runs:

```java
ParcelCollected c = Events.collected("PP-7781", 2_500);    // validates: "7781" throws
long grams = Events.grams(c);
bus.subscribe(ParcelCollected.class, e -> loadBoard.add(Events.parcelId(e), Events.grams(e)));
```

```kotlin
object Events {
    @JvmStatic
    fun collected(parcelId: String, grams: Long): ParcelCollected =
        ParcelCollected(ParcelId(parcelId), Weight(grams))          // the init blocks run

    @JvmStatic
    fun grams(event: Handover): Long = event.weight.grams
}
```

`@JvmExposeBoxed`, Experimental in Kotlin 2.4 and switched on with an opt-in, would give Java `new ParcelCollected(new ParcelId(...), new Weight(...))` and a boxed getter. In a quick test with its module-wide flag, the getter on the event interface itself stayed mangled, so Java code that knows only `ParcelEvent` would still need `Events.parcelId(e)`. Keep the facade until that changes.

Some of the Java surface came free from earlier decisions. Lesson 2's `Handler<in E>` shows up as `Handler<? super E>`, so a Java `Handler<ParcelEvent>` fits any subscription, and the lab's Java support desk counts failed deliveries with one. kotlinc writes `PermittedSubclasses` for the sealed model, so a Java `switch` over a `ParcelEvent` with one case per leaf compiles with no `default`. `Subscription.close()` declares no checked exception, the kind Java forces every caller to catch, so try-with-resources needs no `catch`. And because handlers and middleware are `fun interface`s with `void` and `int` methods, no Java lambda ever returns `Unit.INSTANCE`.

Uncomment the four lines at the end of `JavaViewDemo.java` one at a time, and predict javac's complaint before each run."""

S4 = """A design review is a meeting where you explain each choice in a design while someone sceptical asks why. It's where you find out which decisions you can defend. Here are the questions I'd expect about this library, with the answer I'd give. Disagree where your program differs.

"Why value classes, if Java needs a facade?" Keep them. In the Kotlin model, a swapped id and weight don't compile, and an invalid tracking number can't exist. The facade costs one file. If most callers were Java, I'd undo it and use plain records with compact constructors.

"A `Weight` has no unit." Keep it. The one-field rule made that choice cheap, and the door is the right place for any other unit: a partner's pounds become grams in the parser, once. A unit field inside `Weight` would cost an object per weight and buy nothing.

"Supertype dispatch will surprise people." Keep it, and write it down. The sealed hierarchy keeps the set of keys small, fixed and testable, and the order is a tested promise. The surprise to warn about is the other side of that promise: a `ParcelEvent` handler also hears every event type added next year.

"`in`, adapters, casts: isn't that a lot of machinery?" Keep `in`: it's what lets one tracking handler serve every subscription, from Kotlin and from Java. The single cast is checked by `type.cast` and guaranteed by the keys.

"Delivery is synchronous and lives in memory." Keep it for connecting the parts of one program. Undo it for anything that must survive a crash or reach another program, because the bus forgets everything when the program stops. Those events need storage that survives a restart, such as a database table written in the same step as the change, or a message broker. Guava's documentation for its own `EventBus` lists no way to slow a fast publisher, little control over threads and no exception passing among its reasons to look elsewhere. This bus fixes the last one with an `ErrorHandler`, and not the first two.

"`DropDuplicates` remembers every event for ever." Undo it as written. Bound it to a window of recent events, or let the handler keep its own record of the scans it has seen, which also survives a restart.

"The DSL commits after the block. What if `commit` fails halfway?" Today `subscribe` can't fail. If it ever can, `commit` must close what it already opened before it rethrows.

Notice the pattern in the answers. A choice is safe when an earlier lesson's mechanism forces it: `in` for a consumer, no `else` on a sealed `when`, a `Class<E>` overload because Java can't call a reified function. It's a judgment call when it trades cost for safety: value classes with a facade, synchronous delivery, a memory with no limit. Those are the ones to write down, with the condition that would make you undo them."""

CLOSING = """We started at a depot with two doors. Now Kotlin callers wire a block with `bus.subscriptions { }`, and Java callers get a facade that still checks everything.

That's Part 3 in one library. The storeroom's labels became `Handler<in E>` and the clerk's note, and the cook's note became `Rejected`. The sign-up sheet became the bus, and the town library's forms and the print shop's units became the model.

Now search your Kotlin code for public `reified` functions: what does a Java caller see?

Next, we'll start Part 4, Inside the JVM, with a theatre company that fetches each prop only when a scene needs it. Java read our Kotlin as class files. Who loads them, and when does their code first run?"""

L = {
 "id": "cap3-03",
 "title": "An API for Kotlin and Java callers",
 "minutes": 40,
 "goal": "By the end you can put a subscription DSL on top of the bus with `@DslMarker` and reified inline helpers, give Java callers a surface that reads like ordinary Java (`Class<T>` overloads, `@JvmOverloads`, `@JvmStatic`, a facade over the value classes) that still validates, and defend each generics and patterns choice in the library to a sceptical reviewer.",
 "opening": OPENING,
 "warmup": {
  "q": "A Java class needs a handler for `ParcelCollected`. The Kotlin bus offers `fun <E : ParcelEvent> subscribe(type: KClass<E>, handler: Handler<E>)` and `inline fun <reified E : ParcelEvent> subscribe(handler: Handler<E>)`. What can the Java team write?",
  "options": [
   "`bus.subscribe(ParcelCollected.class, h)`",
   "`bus.<ParcelCollected>subscribe(h)`",
   "`bus.subscribe(JvmClassMappingKt.getKotlinClass(ParcelCollected.class), h)`",
   "Nothing: Java can't call either function"
  ],
  "answer": 2,
  "why": "A `Class` is not a `KClass`, so the first call doesn't match, however natural it looks. The reified function is compiled as a synthetic method, and javac ignores synthetic methods, so the second finds nothing. The `KClass` version works once Java converts the class by hand, which reads badly. This lesson adds a `Class<E>` overload so Java can write the first line."
 },
 "sections": [
  {
   "h": "A subscription DSL: one block declares the wiring, one handle undoes it",
   "body": S1,
   "try": {
    "title": "Wire, close, and fail halfway",
    "minutes": 5,
    "steps": [
     "Read `DslDemo.kt`: a compact copy of the library, then a `main` that wires a tracking handler and a timed load group, publishes three events, closes the handle, and runs a block that fails.",
     "Predict the `load:` line (the fake clock moves 2 ms per read) and the handler count after the failed block. Run it.",
     "In `SubscriptionsBuilder`, make `on` subscribe at once: replace its body with `bus.subscribe(type, handler)` and keep nothing. Predict the last two lines, and run.",
     "Undo that. Run `DslDemoJava` and find the one place where the Java code has to write `return Unit.INSTANCE`."
    ],
    "code": kotlin_first("dsl", "DslDemo"),
    "expect": "`load: 2 calls, 4 ms; handlers: 3`, then `after close: 0 handlers` and `block failed (missing configuration: load limit); handlers: 0`. With your eager `on`, the handle has nothing to close, so you get `after close: 3 handlers`, and the failed block leaves one more behind: `handlers: 4`. In the Java twin, `Unit.INSTANCE` appears only inside `b.timed(...)`, which takes a Kotlin receiver lambda; the `Consumer` entry point needs none."
   }
  },
  {
   "h": "@DslMarker keeps each block inside its own section of the form",
   "body": S2,
   "try": {
    "title": "Reach the outer builder by accident",
    "minutes": 4,
    "steps": [
     "Run `MarkerDemo` once as it is: `timed groups: {load=1}`.",
     "Uncomment the nested `timed(\"deliveries\")` line (Step 2) and run. Read the error.",
     "Delete `@DslMarker` above `annotation class EventsDsl` in `DslDemo.kt`. Predict the printed map, then run.",
     "Put `@DslMarker` back, comment Step 2 out again and try Step 4, the labelled call. Then run `MarkerDemoJava`, where the same mistake has to be written out as `b.timed`."
    ],
    "code": kotlin_first("dsl", "MarkerDemo"),
    "expect": "With the marker: `'fun timed(name: String, block: TimedGroup.() -> Unit): Unit' cannot be called in this context with an implicit receiver. Use an explicit receiver if necessary.` Without it, the demo compiles and prints `timed groups: {load=1, deliveries=1}`: deliveries became a sibling group, and the load group counts one call where you meant two. The labelled call compiles with the marker and gives the same map, now on purpose. The Java twin prints the same map."
   }
  },
  {
   "h": "What Java sees, and a side door that still checks everything",
   "body": S3,
   "figure": {"svg": FIG, "caption": "One core, two doors. Kotlin callers get the DSL; Java callers get overloads, statics and a facade that still runs every check."},
   "try": {
    "title": "Read javac's complaints",
    "minutes": 5,
    "steps": [
     "Run `JavaViewDemo` (Java) and then its Kotlin twin. Both print a handler line, the KClass line and a refusal.",
     "Uncomment the four lines at the end of `JavaViewDemo.java` one at a time. Before each run, predict the error.",
     "After a demo run, list the class from `labs/` with `javap -p -cp events/build/classes/kotlin/demo workbench.events.l03.demo.javaview.Registry`. Find the mangled `describe` and the reified `subscribe`."
    ],
    "code": java_first("javaview", "JavaViewDemo"),
    "expect": "`no suitable constructor found for PlainBus(String)`; `no suitable method found for subscribe((e)->{ })`, because the reified one is synthetic; `cannot find symbol` with `symbol: constructor ParcelId(String)`, because a value class's constructor is private to Java; and `cannot find symbol` with `symbol: method describe(String)`. javap shows `describe-l8x0xus(java.lang.String)` and a `subscribe(Handler<? super E>)` that javac skips. The Kotlin twin makes all four calls without trouble."
   },
   "refs": [{"title": "Calling Kotlin from Java (Kotlin docs)", "url": "https://kotlinlang.org/docs/java-to-kotlin-interop.html", "kind": "docs"}]
  },
  {
   "h": "Design review: defend each choice, or say when you'd undo it",
   "body": S4,
   "try": {
    "title": "Write your own review notes",
    "minutes": 5,
    "steps": [
     "Without looking back, list five design choices in the library you built across the three labs.",
     "For each, write one line: keep or undo, the earlier lesson whose mechanism decides it, and the condition that would change your answer.",
     "Pick the choice you're least sure about and write the test that would tell you that you were wrong."
    ],
    "expect": "A strong list mixes forced choices (no `else` on the sealed `when`, `Handler<in E>`, a `Class<E>` overload because Java can't call reified functions) with judgment calls (value classes plus a facade, synchronous delivery in memory, an unbounded `DropDuplicates`). The forced ones cite a mechanism. The judgment calls cite a condition, such as \"undo when most callers are Java\" or \"undo when an event must survive a restart\"."
   },
   "refs": [{"title": "Guava EventBus Javadoc: why Guava recommends against it", "url": "https://raw.githubusercontent.com/google/guava/master/guava/src/com/google/common/eventbus/EventBus.java", "kind": "read"}]
  }
 ],
 "compare": {
  "title": "The same wiring from Kotlin and from Java",
  "java": {
   "title": "LoadBoardWiring.java",
   "src": "EventBus bus = new EventBus(List.of(new DropDuplicates()));            // @JvmOverloads\nTimings timings = new Timings();\n\nHandler<ParcelEvent> tracking = e -> trackingPage.add(Events.parcelId(e));\n\nSubscription handle = Events.subscriptions(bus, timings, b -> {          // a Consumer: no Unit.INSTANCE\n    b.on(ParcelEvent.class, tracking);\n    b.on(ParcelCollected.class,\n         Handlers.timed(c -> loadBoard.add(Events.parcelId(c), Events.grams(c)), \"load\", timings));\n    b.on(ParcelDelivered.class,\n         Handlers.timed(d -> loadBoard.remove(Events.parcelId(d), Events.grams(d)), \"load\", timings));\n});\n\nbus.publish(Events.collected(\"PP-7781\", 2_500));                       // validated by the value classes\nhandle.close();                                                         // close() throws nothing"
  },
  "kotlin": {
   "title": "LoadBoardWiring.kt",
   "src": "val bus = EventBus(listOf(DropDuplicates()))\nval timings = Timings()\n\nval tracking = Handler<ParcelEvent> { trackingPage += it.parcelId.value }\n\nval handle = bus.subscriptions(timings) {\n    on(ParcelEvent::class, tracking)\n    timed(\"load\") {\n        on<ParcelCollected> { loadBoard.add(it.parcelId, it.weight) }\n        on<ParcelDelivered> { loadBoard.remove(it.parcelId, it.weight) }\n    }\n}\n\nbus.publish(ParcelCollected(ParcelId(\"PP-7781\"), Weight(2_500)))\nhandle.close()"
  },
  "note": "Both wire the same three subscriptions on the same bus, and both get one handle back. The Kotlin version reads the domain types directly (`it.parcelId`, `it.weight`) and uses `on<E>` with a reified type, inside a `timed` group whose handlers can't reach the outer builder by accident. The Java version passes `Class` tokens, gets plain `String` and `long` through the `Events` facade, and times handlers one by one with `Handlers.timed`, because a Kotlin receiver lambda would cost it a `return Unit.INSTANCE`. What doesn't differ is the safety: the same `init` blocks check events built from Java, `Handler<? super E>` lets the Java tracking handler fit any subscription, and javac can switch exhaustively over the Kotlin sealed model."
 },
 "worked": {
  "title": "Add subscribeOnce, with its Kotlin sugar and its Java door",
  "steps": [
   {
    "say": "A welcome text must go out for a new sender's first collection only. Start with the core, in Kotlin, taking a `KClass`. The handle closes itself, and `compareAndSet` makes sure only one of eight publishing threads runs the handler, the balking idea from *Concurrency patterns that tie it all together*. One race needs care: an event can arrive before `handle.set` has run, so the code closes again after setting it.",
    "code": "fun <E : ParcelEvent> subscribeOnce(type: KClass<E>, handler: Handler<E>): Subscription {\n    val fired = AtomicBoolean()\n    val handle = AtomicReference<Subscription>()\n    handle.set(subscribe(type) { event ->\n        if (fired.compareAndSet(false, true)) {          // 1. only the first event wins\n            try { handler.handle(event) }                // 2. do the work\n            finally { handle.get()?.close() }            // 3. stop further deliveries\n        }\n    })\n    if (fired.get()) handle.get().close()                // an event won before the handle was set\n    return handle.get()\n}",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "// What Java sees for the core: a KClass parameter it can only reach the long way round.\nbus.subscribeOnce(JvmClassMappingKt.getKotlinClass(ParcelCollected.class), c -> sendWelcome(c));"
   },
   {
    "say": "Add the Kotlin sugar: a one-line reified wrapper. It needs no `noinline` or `crossinline`: its parameter is a `Handler`, not a function type, so there is nothing to inline.",
    "code": "inline fun <reified E : ParcelEvent> subscribeOnce(handler: Handler<E>): Subscription =\n    subscribeOnce(E::class, handler)\n\nbus.subscribeOnce<ParcelCollected> { sendWelcome(it) }",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "// Java can't see the reified wrapper: javac reports \"no suitable method found for subscribeOnce\"\nbus.subscribeOnce(c -> sendWelcome(c));"
   },
   {
    "say": "Add the Java door: a `Class<E>` overload that converts and delegates. Because `Handler` is declared `in`, Java sees `Handler<? super E>`, so a general handler fits too.",
    "code": "fun <E : ParcelEvent> subscribeOnce(type: Class<E>, handler: Handler<E>): Subscription =\n    subscribeOnce(type.kotlin, handler)",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "bus.subscribeOnce(ParcelCollected.class, c -> sendWelcome(Events.parcelId(c)));"
   },
   {
    "say": "Last, pin it from both sides. A Kotlin test publishes the same collection from eight threads and checks that one text went out. A Java test makes the Java call above, so a Kotlin-side change that breaks Java callers fails in this module's own build.",
    "code": "val sent = AtomicInteger()\nbus.subscribeOnce<ParcelCollected> { sent.incrementAndGet() }\ncollide(8) { bus.publish(collection) }\nassertThat(sent.get()).isEqualTo(1)",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "AtomicInteger sent = new AtomicInteger();\nbus.subscribeOnce(ParcelCollected.class, c -> sent.incrementAndGet());\nbus.publish(Events.collected(\"PP-7781\", 2_500));\nbus.publish(Events.collected(\"PP-7781\", 2_500));\nassertThat(sent.get()).isEqualTo(1);"
   }
  ]
 },
 "lab": {
  "title": "Put a DSL and a Java door on the bus",
  "minutes": 16,
  "files": [
   "labs/events/src/main/kotlin/workbench/events/l03/Bus.kt",
   "labs/events/src/main/kotlin/workbench/events/l03/Dsl.kt",
   "labs/events/src/main/kotlin/workbench/events/l03/JavaApi.kt",
   "labs/events/src/main/java/workbench/events/l03/SupportDesk.java"
  ],
  "run": "./gradlew :events:test --tests 'workbench.events.l03.*'",
  "steps": [
   "The package starts with lesson 2's solution, already given its Java-facing annotations: `@JvmOverloads` on the bus constructor, `@JvmField` on `ErrorHandler.PRINT` and `Ticker.SYSTEM`, `@file:JvmName(\"Handlers\")` on `Timing.kt`. Read them first. Don't edit `Callers.kt`. Run the tests: all thirteen fail, six Kotlin and seven Java.",
   "`Bus.kt` TODO 1: the `Class<E>` overload of `subscribe`, in one line.",
   "`Dsl.kt` TODO 2: add `@DslMarker` to `EventsDsl`, and `@EventsDsl` to both builder classes. TODO 3: `on` adds a `Pending`; `commit` sets `committed`, subscribes every entry and returns one handle that closes them in reverse.",
   "TODO 4: the reified `on<E>`. Write `on(E::class, Handler { handler(it) })`, compile, and add the modifier the error asks for. TODO 5: `TimedGroup`'s two `on` functions.",
   "`JavaApi.kt` TODO 6: `collected`, `parcelId`, `grams` and the `Consumer` entry point.",
   "`SupportDesk.java` TODO 7: one `Events.subscriptions` block with two `b.on(...)` calls.",
   "Run until all thirteen pass. Then delete `@JvmStatic` from `Events.collected` and run once more: read what javac says about `FromJavaTest`, and put it back."
  ],
  "hints": [
   "`type.kotlin` turns a `Class<E>` into a `KClass<E>`.",
   "In `commit`: `val handles = pending.map { it.subscribeTo(bus) }`, then `Subscription { handles.asReversed().forEach(Subscription::close) }`.",
   "`Events.subscriptions` is `SubscriptionsBuilder.build(bus, timings) { block.accept(this) }`: inside the receiver lambda, `this` is the builder.",
   "In `SupportDesk`, `failedAttempts.merge(Events.parcelId(event), 1, Integer::sum)` adds one to the parcel's running count, and `deliveredGrams.addAndGet(Events.grams(d))` adds a delivery's weight.",
   "The `Handler<ParcelEvent>` for failed deliveries compiles in `b.on(DeliveryFailed.class, ...)` because Java sees `Handler<? super E>`."
  ],
  "done_when": "All thirteen tests in `DslTest` and `FromJavaTest` pass."
 },
 "drill": {
  "title": "The DSL skeleton and the Java door from memory",
  "minutes": 5,
  "prompt": "Close the lab. From memory, write the Kotlin entry function `subscriptions`, the builder's `on(type, handler)`, `commit()` and the reified `on<E>` (with the right modifier). Then, below it, write the Java call that wires one delivery handler through `Events.subscriptions`, and name the annotation or overload behind each part of that Java line.",
  "answer": {
   "lang": "kotlin",
   "src": "@DslMarker\n@Target(AnnotationTarget.CLASS)\nannotation class EventsDsl\n\n@EventsDsl\nclass SubscriptionsBuilder private constructor(private val bus: EventBus) {\n    private val pending = mutableListOf<Pending<*>>()\n\n    fun <E : ParcelEvent> on(type: KClass<E>, handler: Handler<E>) { pending += Pending(type, handler) }\n    fun <E : ParcelEvent> on(type: Class<E>, handler: Handler<E>) = on(type.kotlin, handler)\n    inline fun <reified E : ParcelEvent> on(crossinline handler: (E) -> Unit) = on(E::class, Handler { handler(it) })\n\n    private fun commit(): Subscription {\n        val handles = pending.map { it.subscribeTo(bus) }\n        return Subscription { handles.asReversed().forEach(Subscription::close) }\n    }\n\n    private class Pending<E : ParcelEvent>(val type: KClass<E>, val handler: Handler<E>) {\n        fun subscribeTo(bus: EventBus) = bus.subscribe(type, handler)\n    }\n\n    companion object {\n        fun build(bus: EventBus, block: SubscriptionsBuilder.() -> Unit) = SubscriptionsBuilder(bus).apply(block).commit()\n    }\n}\n\nfun EventBus.subscriptions(block: SubscriptionsBuilder.() -> Unit): Subscription = SubscriptionsBuilder.build(this, block)",
   "alt": {
    "lang": "java",
    "src": "Subscription handle = Events.subscriptions(bus, b ->        // @JvmStatic + a Consumer parameter\n        b.on(ParcelDelivered.class,                          // the Class<E> overload\n             d -> delivered.add(Events.grams(d))));           // the facade over Weight; Handler<? super E>\nhandle.close();                                               // Subscription.close() throws nothing"
   }
  }
 },
 "closing": CLOSING,
 "recap": [
  "A subscription DSL collects what the block declares and subscribes it all at the end: a block that throws subscribes nothing, and one handle closes everything, in reverse order.",
  "`on<E>` is inline and reified. Its lambda is called from inside a `Handler` object, so it must be `crossinline`. A `check` in `on` catches subscriptions made from inside a handler, which `@DslMarker` can't see.",
  "`@DslMarker` on the builder classes makes only the nearest builder implicit, so `timed` inside `timed` stops compiling instead of quietly creating a sibling group.",
  "Java can't call reified functions and stumbles over `KClass`, defaults, objects, companions and value classes. Add `Class<E>` overloads, `@JvmOverloads`, `@JvmStatic`, `@JvmField`, `@file:JvmName`, and a facade that builds the value classes so every check still runs.",
  "In a design review, a choice that an earlier mechanism forces is easy to defend. Write down the judgment calls, and the condition that would make you undo each one.",
  "Where the library stops: it lives in one program's memory, so events that must survive a crash or reach another program need storage of their own, and a slow handler still slows every publish."
 ],
 "quiz": [
  {
   "q": "From *Type-safe DSLs with lambdas with receivers*: inside `timed(\"load\") { ... }` you call `timed(\"deliveries\") { ... }`. `TimedGroup` has no `timed`; both builder classes carry `@EventsDsl`, which is annotated `@DslMarker`. What happens?",
   "options": [
    "It compiles and creates a sibling group under the outer builder",
    "It compiles and nests deliveries inside the load group",
    "It fails to compile: `timed` can't be called with an implicit outer receiver",
    "It compiles, and throws when the block runs"
   ],
   "answer": 2,
   "why": "With the marker, only the nearest marked receiver, the `TimedGroup`, is implicit, and it has no `timed`. Without the marker, the first option is exactly what happens, silently, which is why it's tempting. If you do want the sibling, write `this@subscriptions.timed(...)`.",
   "from": "kt-04"
  },
  {
   "q": "From *Inline functions: noinline, crossinline and non-local returns*: `inline fun <reified E : ParcelEvent> on(handler: (E) -> Unit) = on(E::class, Handler { handler(it) })` doesn't compile. Which fix fits best?",
   "options": [
    "Mark `handler` `crossinline`: it's called from inside the `Handler` object, and its body can still be inlined there",
    "Remove `inline`: the function then works without changes",
    "Mark the function `@PublishedApi`",
    "Change `Handler { handler(it) }` to `handler as Handler<E>`"
   ],
   "answer": 0,
   "why": "The lambda runs later, from another object, so a non-local `return` inside it couldn't work, and the compiler asks you to rule it out. `noinline` would compile too, but it keeps a lambda object inside each Handler. Removing `inline` breaks `reified`. The cast doesn't compile either: an inlined lambda parameter can't be used as a value, and even with `noinline` a Kotlin function object is not a `Handler`.",
   "from": "kt-01"
  },
  {
   "q": "From *Value classes and what they compile to*: Java code writes `new ParcelCollected(\"PP-7781\", 2_500L)`, where `ParcelCollected` is a data class with `ParcelId` and `Weight` value-class properties. What happens?",
   "options": [
    "It compiles and checks both values",
    "It compiles and skips the `init` blocks",
    "It throws `NoSuchMethodError` when the program runs",
    "javac refuses: `ParcelCollected(String,long) has private access in ParcelCollected`"
   ],
   "answer": 3,
   "why": "kotlinc makes that constructor private and adds a public synthetic one with a `DefaultConstructorMarker`, which javac won't call. That's what keeps Java from building an unchecked `ParcelCollected`. The way in is a facade such as `Events.collected(String, long)`, which builds the value classes so their checks run.",
   "from": "kt-02"
  },
  {
   "q": "From *Type erasure and reified type parameters*: why does the bus keep `subscribe(type: KClass<E>, ...)` and add `subscribe(type: Class<E>, ...)`, rather than offering only the reified `subscribe<E>`?",
   "options": [
    "Because reified functions are slower than ones that take a token",
    "Because Java can't call a reified function, so the work must live in a version that takes a class token",
    "Because `KClass` needs kotlin-reflect when the program runs",
    "Because a reified function can't be a member of a class"
   ],
   "answer": 1,
   "why": "javac can't inline Kotlin code, so it can't supply `E`, and kotlinc marks the reified function synthetic. The token versions do the work, and the reified one is a one-line wrapper for Kotlin. `KClass` itself needs no kotlin-reflect for `isInstance` and `cast`, and members can be reified.",
   "from": "gen-08"
  },
  {
   "q": "`class EventBus(middleware: List<Middleware> = emptyList(), onError: ErrorHandler = ErrorHandler.PRINT)`, with no `@JvmOverloads`. Which Java calls compile?",
   "options": [
    "Only `new EventBus(list, onError)`",
    "`new EventBus()`, `new EventBus(list)` and `new EventBus(list, onError)`",
    "`new EventBus()` and `new EventBus(list, onError)`, but not `new EventBus(list)`",
    "None: Java can't call constructors with default arguments"
   ],
   "answer": 2,
   "why": "When every constructor parameter has a default, kotlinc adds a constructor with no arguments, so Java gets that one and the full one. The ones in between exist only with `@JvmOverloads`, and javac reports `no suitable constructor found` for `new EventBus(list)`. The second option is what the lab's bus offers, because it carries the annotation."
  }
 ],
 "flashcards": [
  {"front": "Why does the subscriptions builder collect first and subscribe at the end?", "back": "A block that throws halfway then subscribes nothing, and the caller gets one handle that closes everything the block declared."},
  {"front": "Why must the lambda of `inline fun <reified E> on(handler: (E) -> Unit)` be `crossinline`?", "back": "The body calls it from inside another object, the `Handler`, which runs later. `crossinline` forbids non-local returns so it can still be inlined there."},
  {"front": "What does `@DslMarker` stop, and what can't it stop?", "back": "It stops implicit calls to an outer marked builder from an inner block. It can't stop a call from inside a handler lambda, which has no receiver: use a runtime check."},
  {"front": "Java can't call your reified `subscribe<E>`. What do you add?", "back": "A `Class<E>` overload that delegates with `type.kotlin`. The reified function stays a one-line wrapper for Kotlin."},
  {"front": "A Kotlin constructor where every parameter has a default: what does Java get without `@JvmOverloads`?", "back": "A constructor with no arguments and the full one. `@JvmOverloads` adds the ones in between."},
  {"front": "Why a facade like `Events.collected(String, long)` instead of `@JvmName` on functions that take value classes?", "back": "The facade builds the value classes, so their `init` checks run. `@JvmName` lets Java pass raw values straight past them."},
  {"front": "What does a Java caller get for free from `Handler<in E>` and a Kotlin sealed model?", "back": "`Handler<? super E>` in every signature, and an exhaustive `switch` over the sealed types with no `default`."}
 ],
 "terms": [
  {"term": "DSL", "plain": "A small language made for one job, written as ordinary Kotlin calls and blocks."},
  {"term": "Entry function", "plain": "The function that creates a builder, runs your block on it and returns the result, such as `bus.subscriptions { }`."},
  {"term": "@DslMarker", "plain": "An annotation for your own DSL marker annotation: inside a block, only the nearest marked receiver can be called implicitly."},
  {"term": "crossinline", "plain": "A modifier for a lambda parameter of an inline function that is called from another object or lambda; it forbids non-local returns."},
  {"term": "Facade for Java", "plain": "A small object of static functions that takes and returns plain Java types and builds the Kotlin types inside."},
  {"term": "@JvmOverloads", "plain": "Makes kotlinc generate one Java overload per trailing default parameter."},
  {"term": "@JvmStatic", "plain": "Makes a member of an object or companion a real static method, so Java needs no INSTANCE or Companion."},
  {"term": "Design review", "plain": "A meeting where you defend each design choice, say what forces it, and say what would make you undo it."}
 ],
 "explain_back": {
  "prompt": "A sceptical reviewer says: \"This is a lot of type machinery for an event bus. Why not a `Map<String, MutableList<(Any) -> Unit>>` and a JSON string per event?\" Defend your design: name the bugs each choice prevents, and the one or two choices you'd undo.",
  "answer": "With strings and `Any`, every handler parses and casts for itself: a scan that says \"2.5\" grams throws inside the load board after the tracking page listed it, a typo in an event name never matches, and a new event type is ignored everywhere without a word. The sealed model and the door stop all three: bad input is rejected once, and a `when` without `else` breaks the build wherever a new type needs handling. Value classes make a swapped id and weight a compile error. The bus walks supertypes, so one tracking handler sees every event, and `Handler<in E>` lets that handler fit any subscription, from Kotlin and from Java. Isolation, handles and a copy-on-write list keep one bad or self-removing handler from hurting the rest. The DSL commits a block all at once, and `@DslMarker` keeps nested blocks from reaching the wrong builder. For Java, the overloads and the facade make it read like a Java library without skipping a check. What I'd undo: the unbounded `DropDuplicates`, which should become a bounded window or a record kept by the handler. And anything that must survive a crash goes to storage that outlives the program, not to this bus."
 },
 "deeper": {
  "minutes": 10,
  "body": """A production version of this library would add, roughly in this order:

- Asynchronous lanes. An executor per group of handlers, with one single-threaded lane per tracking number so the events for one parcel keep their order, and a bounded queue in front of each lane. That's also where backpressure lives, the idea of a slow receiver slowing a fast sender: when a lane is full, the publisher waits, or the event is kept to try again later.
- Real metrics. Replace `Timings` with timers from a metrics library such as Micrometer, named after each subscription, so a slow handler shows up on the same dashboards as the rest of the program.
- Durability. Events that must survive a crash, or reach other programs, go into a database table in the same transaction as the change that caused them (a pattern often called an outbox), and a separate job sends them on to a message broker. The in-process bus stays for connecting the parts of one program.
- A shelf for refused scans. `Parsed.Rejected` goes to a store with its reason, a counter, and a small tool to replay the scans once the bug behind them is fixed.
- Versioned events. Stable type names with `@SerialName` if you serialize with kotlinx.serialization, and parser branches that map old names to new types.
- A checked public API. `on<E>` and `subscribe<E>` are public inline functions, so their bodies are compiled into every caller, and the `@JvmOverloads` overloads are part of what Java callers link against. A binary-compatibility check in the build catches a change that would break callers compiled against the previous version.
- `@JvmExposeBoxed`, once it is stable, if it also covers interface members. Until then, the `Events` facade is the Java door.

One thing it should not add is registration by scanning for annotations, Guava style (`@Subscribe` on methods, found through reflection). Guava's own documentation lists the costs: subscribers are hard to find from the publisher, and reflection breaks under the tools that shrink and rename code for release. Explicit `on<E>` calls keep every subscription visible in the code that owns it."""
 },
 "sources": [
  {"title": "Calling Kotlin from Java (Kotlin docs)", "url": "https://kotlinlang.org/docs/java-to-kotlin-interop.html"},
  {"title": "Type-safe builders (Kotlin docs)", "url": "https://kotlinlang.org/docs/type-safe-builders.html"},
  {"title": "Inline functions (Kotlin docs)", "url": "https://kotlinlang.org/docs/inline-functions.html"},
  {"title": "KEEP-0394: @JvmExposeBoxed", "url": "https://github.com/Kotlin/KEEP/blob/main/proposals/KEEP-0394-jvm-expose-boxed.md"},
  {"title": "Guava EventBus source and Javadoc", "url": "https://raw.githubusercontent.com/google/guava/master/guava/src/com/google/common/eventbus/EventBus.java"}
 ]
}
out = ROOT / "content/lessons/cap3-03.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
