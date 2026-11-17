import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")

INTRO = """In three sittings, you build one working library: a small, typed event library for Pedal Post, the bike courier in the small town of the Design patterns track. An event library lets one part of a program announce that something happened, and lets other parts react without the announcer knowing who is listening. A rider's scanner announces "PP-7781 collected, 2.5 kg"; the tracking page, the load board and the text sender each hear it and do their own job. Typed means the compiler knows the kind of every event, so a handler written for deliveries can never be handed anything else. Lesson 1 builds a sealed model of parcel events, with value classes for tracking numbers and weights, behind one parse function at the door that turns raw scanner fields into an event or a note saying why not. Lesson 2 builds the bus: it routes each event to the handlers of its kind and every wider kind, takes one general handler for any subscription, survives a failing handler, and runs a middleware chain and a timing decorator. Lesson 3 adds an API that reads well from both sides, a subscription DSL for Kotlin and overloads, statics and a facade for Java, and ends Part 3 with a design review.

The capstone draws on the whole of Part 3 and calls back its pictures as it goes: the fruit shop's storeroom from the Generics track, the recipe book from Functional programming, the small town and its corner shop from Design patterns, the town library's forms from Modern Java data modeling, and the print shop from Advanced Kotlin. There is little new theory. Each design choice names the lesson that taught it, so you can go back when a step doesn't stick.

The labs live in `labs/events`, one package per lesson (`workbench.events.l01` to `l03`), and each lab starts from the previous lab's solution, so you can begin at any sitting. Lessons 1 and 2 are written in Kotlin; lesson 3 adds a Java class, `SupportDesk`, and a Java test that uses the library the way a Java team would. From `labs/`, run `./gradlew :events:test --tests 'workbench.events.lNN.*'` until it passes, `./gradlew :events:solutionTest` to check the reference answers, and `./gradlew :events:demo -Pmain=<class>` for the Try-it programs, each in Kotlin and in Java. The tests use kotlin-reflect for two checks (`sealedSubclasses` and the variance of `Handler`); the library itself doesn't need it. Install JDK 25; the labs compile with release 21 and Kotlin 2.4.21."""

CHEATSHEET = """## The library in one picture

A rider's scanner sends raw fields: `type=collected, parcelId=PP-7781, grams=2500`. At the door, `parseEvent` turns them into `Parsed.Ok(ParcelCollected(PP-7781, 2.5 kg))`, or into a note such as `Parsed.Rejected("grams is not a whole number: '2.5'")`. Then `bus.publish(event)` calls the handlers of `ParcelCollected` first, then those of `Handover`, then those of `ParcelEvent`, each key in subscription order, and returns how many it called.

## Picture it: the pictures behind the design

| Picture it | Where it came from | What it became in the library |
|---|---|---|
| a form with a fixed set of boxes to tick | Sealed types: hierarchies the compiler can check | `sealed interface ParcelEvent`, with `Handover` sealed one level down |
| the clerk working down a printed sheet, one line per box | Pattern matching with switch and record patterns | a `when` or `switch` with no `else` |
| order slips on a spike, and a note that something happened | Observer and Command | events named in the past tense: handlers react, never refuse |
| a printed recipe book: new editions, never crossings-out | Immutable data and a functional core | data classes of `val`s; `copy()` runs `init` again |
| units on numbers at the print shop's parcel desk | Value classes and what they compile to | `ParcelId` and `Weight`: a swapped argument doesn't compile |
| the clerk at the door who copies each letter onto the right form | Data-oriented programming, and Project Valhalla | `parseEvent(fields): Parsed`, the only place raw fields are read |
| a note saying what went wrong, not a thrown pan | Errors as values: sealed results, Result and Either | `Parsed.Rejected(reason)`: the door never throws |
| a recipe card: same ingredients, same pancakes | Pure functions: the idea everything else builds on | `parseEvent` and `summary`, tested with plain values |
| the board of delivery bells by the back door | Generics workshop: a type-safe container and event bus | `EventBus`, keyed by class, walking each event's supertypes |
| the labelled box "Box of ___" | Generics from zero: type parameters | `Handler<E>`, `KClass<E>`, `Subscription` |
| the compost bin, a fine apple bin | Contravariance with in: consumers | `Handler<in E>`; Java sees `Handler<? super E>` |
| the travel plug, and the receptionist who checks each call | Adapter and Facade; Decorator and Proxy | the adapter that stores a narrow handler and casts each event with `type.cast` |
| the "ring me when the bread arrives" sheet | Observer and Command | `Subscription` handles, one `try` per handler, a copy-on-write snapshot |
| a complaint passed along a line of people | State and Chain of Responsibility | middleware folded into one chain; order is behavior |
| gift paper around a teapot | Decorator and Proxy | `timed(...)`: the same `Handler<E>`, plus timing |
| the print shop's order form, section by section | Type-safe DSLs with lambdas with receivers | `bus.subscriptions { on<E> { }; timed("load") { } }` |
| each section offers only its own boxes | the same lesson | `@DslMarker` on both builder classes |
| the box whose label wore off | Star projection: when you don't know the type | `List<Pending<*>>` inside the builder |
| the clerk who copies the label onto a note before it's torn off | Type erasure and reified type parameters | `subscribe<E>` and `on<E>`; Java gets a `Class<E>` overload instead |
| steps sealed in an envelope for the night shift | Inline functions: noinline, crossinline and non-local returns | `crossinline handler: (E) -> Unit` in `on<E>` |
| the hotel reception desk | Adapter and Facade | `Events.collected(String, long)`: Java's side door, with every check still run |

Where the pictures break: a paper form can be filled in later, but an event is a fact that already happened. A real clerk at the door may guess what a messy letter meant; `parseEvent` must never guess, so a missing weight is a rejection, not a zero. And a bell board rings everyone at once, while this bus calls one handler after another on the publisher's thread.

## The model (lesson 1)

- [ ] Every event is a past-tense fact in one sealed hierarchy: `ParcelEvent`, with a sealed `Handover` in the middle for collections and deliveries.
- [ ] Leaves are data classes (records in Java): final, compared by value, checked in `init`.
- [ ] Ids and weights are value classes with `init` checks: `ParcelId` (`PP-` and 4 to 12 digits) and `Weight` (whole grams).
- [ ] Every operation is a `when` or `switch` with **no `else`** over your own sealed type.
- [ ] One edge function, `parseEvent(fields): Parsed`, returns `Ok` or `Rejected` and never throws. The rules live in the constructors; the parser turns their `IllegalArgumentException` into `Rejected`.
- [ ] A `Rejected` scan is set aside with its reason, and never retried.

```java
sealed interface ParcelEvent permits ParcelBooked, DeliveryFailed, Handover { ParcelId parcelId(); }
sealed interface Handover extends ParcelEvent permits ParcelCollected, ParcelDelivered { Weight weight(); }
record ParcelCollected(ParcelId parcelId, Weight weight) implements Handover {}
```

```kotlin
sealed interface ParcelEvent { val parcelId: ParcelId }
sealed interface Handover : ParcelEvent { val weight: Weight }
data class ParcelCollected(override val parcelId: ParcelId, override val weight: Weight) : Handover
```

## The bus (lesson 2)

- [ ] Registry keyed by `KClass`. Dispatch keys are the event's class, then its event supertypes, nearest first, cached per class with `computeIfAbsent`. Java reflection (`getInterfaces`, `getSuperclass`) is enough: no kotlin-reflect.
- [ ] Delivery order is a promise: the most specific key first, then wider ones; within a key, subscription order. Test it.
- [ ] `fun interface Handler<in E : ParcelEvent>`: a consumer, so `in`. Java sees `Handler<? super E>`.
- [ ] Store each handler behind an adapter: `Handler<ParcelEvent> { e -> handler.handle(type.cast(e)) }`.
- [ ] `subscribe` returns a `Subscription : AutoCloseable` that removes exactly that adapter. Closing twice is harmless.
- [ ] `catch (e: Exception)` around each handler, reported to an injected `ErrorHandler` with the event.
- [ ] Each key's handlers in a `CopyOnWriteArrayList`: delivery loops over a snapshot, a handler may unsubscribe itself, and publishers need no lock.
- [ ] Work for every event once (logging, dropping repeats) is middleware: a chain built once by `foldRight` over a copy of the list. Order is behavior.
- [ ] Work for one handler (timing) is a decorator: the same `Handler<E>`, recorded in `finally`, with the clock injected as a `Ticker`.

```java
<E extends ParcelEvent> AutoCloseable subscribe(Class<E> type, Handler<? super E> handler) {
    Handler<ParcelEvent> adapter = event -> handler.handle(type.cast(event));
    List<Handler<ParcelEvent>> list = registry.computeIfAbsent(type, t -> new CopyOnWriteArrayList<>());
    list.add(adapter);
    return () -> list.remove(adapter);
}
```

```kotlin
fun <E : ParcelEvent> subscribe(type: KClass<E>, handler: Handler<E>): Subscription {
    val adapter = Handler<ParcelEvent> { event -> handler.handle(type.cast(event)) }
    val list = registry.computeIfAbsent(type) { CopyOnWriteArrayList() }
    list += adapter
    return Subscription { list.remove(adapter) }
}
```

## The API (lesson 3)

- [ ] The DSL collects in `on` and subscribes in `commit`, after the block: a block that throws subscribes nothing, and one handle closes everything, in reverse.
- [ ] `inline fun <reified E> on(crossinline handler: (E) -> Unit)`: `crossinline` because the lambda runs inside a `Handler` object.
- [ ] `@DslMarker` on the builder classes, and a `check(!committed)` for calls from inside handlers, which the marker can't see.
- [ ] Every reified or `KClass` function has a `Class<E>` overload that delegates with `type.kotlin`.
- [ ] `@JvmOverloads` on constructors with defaults, `@JvmStatic` on object members, `@JvmField` on companion constants, `@file:JvmName` on files of top-level functions.
- [ ] A facade (`Events.collected(String, long)`) that builds the value classes, so Java input is checked. Never `@JvmName` straight past `init`.
- [ ] Callbacks are `fun interface`s with `void` or `int` methods, and the Java DSL entry takes a `Consumer`: no `return Unit.INSTANCE`.
- [ ] One Java test in the Kotlin module's own build.

| Kotlin as written | What Java gets | Fix |
|---|---|---|
| a reified function | invisible (synthetic) | a `Class<E>` overload |
| a `KClass<E>` parameter | `JvmClassMappingKt.getKotlinClass(X.class)` | a `Class<E>` overload |
| default arguments | the all-defaults and full constructors only | `@JvmOverloads` |
| an `object` member, a companion `val` | `INSTANCE.f()`, `Companion.getX()` | `@JvmStatic`, `@JvmField` |
| value classes in a data class | a private constructor, mangled getters such as `getWeight-RqKWbHU()` | a facade with plain types |

## Design review questions

| Question | Forced, or a judgment call? |
|---|---|
| No `else` on sealed `when`s? | forced: *Sealed types: hierarchies the compiler can check* |
| `Handler<in E>`? | forced: *Contravariance with in: consumers* |
| `Class<E>` overloads? | forced: *Type erasure and reified type parameters* |
| Value classes plus a Java facade? | judgment: undo if most callers are Java |
| `Weight` in whole grams, no unit field? | judgment: keep, and convert any other unit at the door |
| Synchronous delivery, in memory? | judgment: keep inside one program; events that must survive a crash need storage of their own |
| An unbounded `DropDuplicates`? | judgment: undo; bound it, or let the handler keep its own record |"""

RECAP = [
 "Parse raw input once, at the door, into a sealed model; return `Ok` or `Rejected` and never throw. Behind the door, handlers trust the types.",
 "A `when` with no `else` over your own sealed type turns a new event type into a list of compile errors. A sealed middle level lets one branch, or one handler, stand for its leaves.",
 "Value classes give ids and weights their own types at no cost where they're used as themselves, and their `init` blocks make every instance valid. One field only, so a `Weight` is whole grams, and other units are converted at the door.",
 "Route each event to its class and then to its event supertypes, nearest first, from a per-class cache. Declare handlers `in`, and store them behind casting adapters.",
 "The sign-up sheet's rules hold: return a handle, catch and report each handler's exception, and loop over a copy-on-write snapshot. Delivery stays synchronous, so keep handlers fast.",
 "Work for every event once is a middleware chain built by a fold, where order is behavior. Work for one handler is a decorator. Test time with a fake ticker.",
 "The subscription DSL collects and then commits, uses a reified `on<E>` with `crossinline`, and marks its builders with `@DslMarker` so nested blocks can't reach the wrong one.",
 "Give Java `Class<E>` overloads, `@JvmOverloads`, `@JvmStatic`, `@JvmField`, `@file:JvmName` and a facade that builds the value classes, and test it all from Java.",
 "In the design review, defend forced choices by their mechanism, and write down each judgment call with the condition that would undo it. The bus lives in memory: anything that must survive a crash needs storage of its own."
]

QUIZ = [
 {
  "q": "A collection arrives as raw fields with `grams = \"0\"`. Where is it refused, and what does the code that reads scans see?",
  "options": [
   "In the load board, which throws, and the reading loop stops",
   "In `ParcelCollected`'s `init`; `parseEvent` returns `Rejected` with that message",
   "In `parseEvent`, by its own `grams > 0` check, which returns `null`",
   "Nowhere: a zero-gram collection is valid"
  ],
  "answer": 1,
  "why": "The rule lives in the constructor, once. `Weight(0)` is a valid weight, but a collection must weigh something, so `ParcelCollected`'s `init` refuses it. The door calls the constructor and turns its `IllegalArgumentException` into a `Rejected`, which is set aside before any handler acts."
 },
 {
  "q": "`summary`, `changesHands` and a label for the tracking page are `when`s over `ParcelEvent` with no `else`. Someone adds `ParcelLost : ParcelEvent`. What finds every place that must change?",
  "options": [
   "A `NoWhenBranchMatchedException` the first time a lost parcel is published",
   "A code search for `ParcelCollected`",
   "The compiler: each of those `when`s fails until it handles lost parcels",
   "Nothing: `when` falls through to the last branch"
  ],
  "answer": 2,
  "why": "Exhaustiveness is checked at compile time, and with no `else` the new subtype is missing from each `when`. An `else` anywhere would swallow it silently. The exception only happens when code compiled against the old model meets the new type."
 },
 {
  "q": "Why is `Weight` a value class of whole grams with no unit field?",
  "options": [
   "Because a JVM value class can hold exactly one field, and Pedal Post weighs in grams; other units are converted at the door",
   "Because value classes can't hold a `String`",
   "Because Java callers can't read two fields",
   "Because data classes can't check their values in `init`"
  ],
  "answer": 0,
  "why": "Until Valhalla, Kotlin's `@JvmInline value class` has one property. A weight plus a unit would be a data class, one object per weight. The design review keeps the choice, because the parser can turn pounds into grams once, and nothing behind the door ever sees a pound."
 },
 {
  "q": "Subscribed in this order: `tracking` under `ParcelEvent`, `handovers` under `Handover`, `load` then `texts` under `ParcelCollected`. You publish a collection. In what order do they run?",
  "options": [
   "tracking, handovers, load, texts",
   "load, texts, handovers, tracking",
   "texts, load, handovers, tracking",
   "load, handovers, tracking, texts"
  ],
  "answer": 1,
  "why": "Keys are visited nearest first: `ParcelCollected`, then `Handover`, then `ParcelEvent`. Within one key, handlers run in subscription order, so `load` comes before `texts`. The first option is subscription order across keys, which the bus doesn't use."
 },
 {
  "q": "In a Java class, `Handler<ParcelEvent> tracking = e -> ...;` and then `bus.subscribe(ParcelCollected.class, tracking);` compiles. Why?",
  "options": [
   "Because Java generics are covariant",
   "Because `subscribe` casts its argument",
   "Because `ParcelCollected.class` is a `Class<ParcelEvent>`",
   "Because `Handler` is declared `in`, so kotlinc writes `Handler<? super E>` into the Java signature"
  ],
  "answer": 3,
  "why": "Declaration-site `in` becomes a `? super` wildcard in parameter types. A handler of any event can then stand in for a handler of collections, in Java as in Kotlin, like the compost bin that makes a fine apple bin. Java generics are invariant without a wildcard."
 },
 {
  "q": "Of three handlers for a collection, the second throws `IllegalStateException`. What does `publish` return, and what happens to the error?",
  "options": [
   "3; the bus reports it, with the event, to its `ErrorHandler`, and the third handler still runs",
   "1; `publish` stops at the failure and rethrows",
   "2; the failing handler isn't counted and the error is dropped",
   "It throws, after running all three"
  ],
  "answer": 0,
  "why": "Each call is wrapped in its own `try`, so one failure can't starve the rest, and `publish` counts the handlers it called. The bus doesn't decide what an error means: the injected `ErrorHandler` does."
 },
 {
  "q": "You want to know how long the texts handler takes per event. Where does the timing go?",
  "options": [
   "A middleware, first in the list",
   "Inside `publish`, around `deliver`",
   "A decorator around the texts handler: the same `Handler<E>`, timed in `finally`",
   "In the `ErrorHandler`"
  ],
  "answer": 2,
  "why": "Middleware and `publish` see one delivery to all of an event's handlers, so they'd add the load board's time to the texts' time. A decorator wraps exactly one handler, and with an injected `Ticker` its numbers are testable."
 },
 {
  "q": "A `bus.subscriptions { ... }` block declares two handlers and then throws because a setting is missing. How many handlers are subscribed afterwards?",
  "options": [
   "Two, and the caller has no handle to remove them",
   "One",
   "Two, removed again by a `finally` in the block",
   "None: the builder only subscribes after the block returns"
  ],
  "answer": 3,
  "why": "`on` only records a pending subscription, and `commit` runs after the block. So a failing block leaves the bus untouched, and a successful one returns a single handle for everything it declared."
 },
 {
  "q": "Java code needs a delivery event for 2.5 kg on `PP-7781`. Which line compiles and checks its values?",
  "options": [
   "`new ParcelDelivered(new ParcelId(\"PP-7781\"), new Weight(2500))`",
   "`Events.delivered(\"PP-7781\", 2_500)`",
   "`new ParcelDelivered(\"PP-7781\", 2500L)`",
   "`ParcelDelivered.Companion.of(\"PP-7781\", 2500)`"
  ],
  "answer": 1,
  "why": "The value classes' constructors and the data class's constructor are private to Java: javac reports `cannot find symbol` or `has private access`. The `@JvmStatic` facade takes plain values and builds the value classes, so their `init` checks run. There is no `Companion.of` in this library."
 },
 {
  "q": "Pedal Post starts taking parcels from a partner courier whose scanners report weights in pounds. Which change comes first?",
  "options": [
   "Convert pounds to grams in the parser at the door, and leave `Weight` as it is",
   "Make `Weight` a data class of an amount and a unit",
   "Add an `else` branch to every `when`, so the new unit can't break the build",
   "Key the bus by unit as well as by class"
  ],
  "answer": 0,
  "why": "The door is where outside data is turned into the model, so a foreign unit is converted there, once. Every handler behind it keeps working in grams. A unit field would cost an object per weight and push the conversion into every handler, and an `else` or a new bus key has nothing to do with units."
 }
]

T = {"id": "cap3", "intro": INTRO, "cheatsheet": CHEATSHEET, "recap": RECAP, "quiz": QUIZ}
out = ROOT / "content/tracks/cap3.json"
out.write_text(json.dumps(T, indent=1, ensure_ascii=False) + "\n")
print(out)
