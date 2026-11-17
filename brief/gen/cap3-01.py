import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/events/src"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :events:demo -Pmain=workbench.events.l01.demo."


def demo(pkg, name):
    """A Kotlin demo with its Java twin, both in workbench.events.l01.demo.<pkg>."""
    k = f"{lab}/demo/kotlin/workbench/events/l01/demo/{pkg}/{name}.kt"
    j = f"{lab}/demo/java/workbench/events/l01/demo/{pkg}/{name}Java.java"
    return {"lang": "kotlin", "title": f"{name}.kt", "src": read(k),
            "run": f"{DEMO}{pkg}.{name}Kt", "file": k,
            "alt": {"lang": "java", "title": f"{name}Java.java", "src": read(j),
                    "run": f"{DEMO}{pkg}.{name}Java", "file": j}}


FIG_PLAN = (
    '<svg viewBox="0 0 680 250" role="img" aria-label="The library we will build: a raw scan from a rider\'s scanner goes through parseEvent at the door, '
    'which either produces a ParcelEvent from the sealed model or a Rejected note that is set aside. Events go to the EventBus '
    'of lesson 2 and on to the handlers: tracking, the load board, texts. Lesson 3 adds the API that Kotlin and Java callers use to reach the bus.">'
    '<text class="t-s t-m" x="270" y="80" text-anchor="middle">lesson 1: the model and its door</text>'
    '<rect class="box" x="10" y="95" width="110" height="54" rx="8"/>'
    '<text class="t" x="65" y="118" text-anchor="middle">scan</text>'
    '<text class="t-s t-m" x="65" y="137" text-anchor="middle">raw fields</text>'
    '<line class="ln" x1="120" y1="122" x2="148" y2="122" marker-end="url(#arr)"/>'
    '<rect class="box-a" x="150" y="95" width="110" height="54" rx="8"/>'
    '<text class="t t-code" x="205" y="118" text-anchor="middle">parseEvent</text>'
    '<text class="t-s" x="205" y="137" text-anchor="middle">the door</text>'
    '<line class="ln" x1="260" y1="122" x2="288" y2="122" marker-end="url(#arr)"/>'
    '<rect class="box-ok" x="290" y="95" width="120" height="54" rx="8"/>'
    '<text class="t t-code" x="350" y="118" text-anchor="middle">ParcelEvent</text>'
    '<text class="t-s" x="350" y="137" text-anchor="middle">sealed model</text>'
    '<line class="ln" x1="410" y1="122" x2="438" y2="122" marker-end="url(#arr)"/>'
    '<rect class="box-b" x="440" y="95" width="110" height="54" rx="8"/>'
    '<text class="t t-code" x="495" y="118" text-anchor="middle">EventBus</text>'
    '<text class="t-s" x="495" y="137" text-anchor="middle">lesson 2</text>'
    '<line class="ln" x1="550" y1="122" x2="578" y2="122" marker-end="url(#arr)"/>'
    '<rect class="box" x="580" y="95" width="90" height="54" rx="8"/>'
    '<text class="t" x="625" y="118" text-anchor="middle">handlers</text>'
    '<text class="t-s t-m" x="625" y="137" text-anchor="middle">tracking, load</text>'
    '<line class="ln-bad" x1="205" y1="149" x2="205" y2="183" marker-end="url(#arr)"/>'
    '<rect class="box-bad" x="150" y="185" width="110" height="50" rx="8"/>'
    '<text class="t" x="205" y="206" text-anchor="middle">Rejected</text>'
    '<text class="t-s" x="205" y="224" text-anchor="middle">a note, set aside</text>'
    '<rect class="box-dim" x="420" y="10" width="150" height="50" rx="8"/>'
    '<text class="t" x="495" y="31" text-anchor="middle">API for callers</text>'
    '<text class="t-s" x="495" y="50" text-anchor="middle">lesson 3: Kotlin, Java</text>'
    '<line class="ln-d" x1="495" y1="60" x2="495" y2="93" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="350" y="175" text-anchor="middle">no raw fields past this point</text>'
    '</svg>'
)

FIG_TREE = (
    '<svg viewBox="0 0 680 240" role="img" aria-label="The sealed hierarchy: ParcelEvent has three direct subtypes, ParcelBooked, '
    'DeliveryFailed and the sealed Handover. Handover has two, ParcelCollected and ParcelDelivered. One branch for '
    'Handover covers both of its leaves.">'
    '<rect class="box-a" x="250" y="12" width="180" height="46" rx="8"/>'
    '<text class="t t-code" x="340" y="33" text-anchor="middle">ParcelEvent</text>'
    '<text class="t-s t-m" x="340" y="50" text-anchor="middle">sealed interface</text>'
    '<line class="ln" x1="340" y1="58" x2="95" y2="98"/>'
    '<line class="ln" x1="340" y1="58" x2="265" y2="98"/>'
    '<line class="ln" x1="340" y1="58" x2="515" y2="98"/>'
    '<rect class="box" x="20" y="98" width="150" height="46" rx="8"/>'
    '<text class="t-s t-code" x="95" y="118" text-anchor="middle">ParcelBooked</text>'
    '<text class="t-s t-m" x="95" y="135" text-anchor="middle">data class</text>'
    '<rect class="box" x="190" y="98" width="150" height="46" rx="8"/>'
    '<text class="t-s t-code" x="265" y="118" text-anchor="middle">DeliveryFailed</text>'
    '<text class="t-s t-m" x="265" y="135" text-anchor="middle">data class</text>'
    '<rect class="box-b" x="430" y="98" width="170" height="46" rx="8"/>'
    '<text class="t-s t-code" x="515" y="118" text-anchor="middle">Handover</text>'
    '<text class="t-s t-m" x="515" y="135" text-anchor="middle">sealed interface</text>'
    '<line class="ln" x1="515" y1="144" x2="425" y2="184"/>'
    '<line class="ln" x1="515" y1="144" x2="595" y2="184"/>'
    '<rect class="box" x="350" y="184" width="150" height="46" rx="8"/>'
    '<text class="t-s t-code" x="425" y="204" text-anchor="middle">ParcelCollected</text>'
    '<text class="t-s t-m" x="425" y="221" text-anchor="middle">data class</text>'
    '<rect class="box" x="520" y="184" width="150" height="46" rx="8"/>'
    '<text class="t-s t-code" x="595" y="204" text-anchor="middle">ParcelDelivered</text>'
    '<text class="t-s t-m" x="595" y="221" text-anchor="middle">data class</text>'
    '<text class="t-s t-a" x="175" y="200" text-anchor="middle">is Handover covers</text>'
    '<text class="t-s t-a" x="175" y="217" text-anchor="middle">both of its leaves</text>'
    '</svg>'
)

OPENING = """Remember Pedal Post, the bike courier in the small town of the Design patterns track? Its riders carry parcels across town on cargo bikes, each with a handheld scanner. Scan a parcel at a door, and the scanner sends a short message to Pedal Post's program: parcel PP-7781, collected, 2,500 grams. Three parts of the program want to hear it. The tracking page adds a line, the load board adds the weight to the bike, and the sender gets a text.

That message is an event, a note that something already happened. The easy trap is to hand the scanner's raw text to every listener, so that each one reads and checks it for itself. The first test never notices: test scans are always tidy.

The Advanced Kotlin track ended with compiler plugins. Now Part 3 goes to work on one small library, in three sittings. In this one, we'll list every kind of parcel event as a closed set of types and give ids and weights types of their own. Then we'll check each scan once, at the door. Before we start, make a guess, and keep it in mind."""

S1 = """Over three sittings, we'll build one small library, a piece of code that other parts of a program call. It's an event library. One part of a program announces that something happened, and other parts react, without the announcer knowing who is listening. The scanner code says "PP-7781 was collected" once. The tracking page, the load board and the text sender each hear it and do their own job. "Typed" means the compiler knows exactly which kind of event each one is, so a handler written for deliveries can never be handed a failed delivery by mistake. And everything happens inside one running program, with no network in between.

The three sittings build the library from the inside out. This one writes the model: the types for every event Pedal Post's program can see. The next one builds the bus, the part that carries each event to everyone who signed up for it. It's the board of bells from Generics workshop: a type-safe container and event bus, grown up. The last one gives the library an API, the set of functions its callers use, that reads well from Kotlin and from Java. Each lab starts from the previous lab's solution, so you can pick up at any sitting.

Let's start with what goes wrong without a model. The demo has three handlers, small functions that each react to a scan, and each one reads the scanner's raw fields for itself. Here is the heart of the load board:

```java
static void loadBoard(Map<String, String> fields) {
    if ("collected".equals(fields.get("type"))) {
        long grams = Long.parseLong(fields.get("grams"));     // parsing, deep inside a handler
        onTheBikeGrams += grams;
    }
    // ... and the same for "delivered", with a minus
}
```

```kotlin
fun loadBoard(fields: Map<String, String>) {
    if (fields["type"] == "collected") {
        val grams = fields.getValue("grams").toLong()          // parsing, deep inside a handler
        onTheBikeGrams += grams
    }
    // ... and the same for "delivered", with a minus
}
```

Three scans go in, and the demo printed:

```text
tracking collected PP-7781
load     +2500 g, on the bike: 2500 g
tracking delivered PP-7781
load     -2500 g, on the bike: 0 g
tracking collected PP-7782
FAILED   java.lang.NumberFormatException: For input string: "2.5"
texts sent: 0
```

Two bugs came out of three scans. The third scan says `"grams": "2.5"`, because the rider weighed that parcel in kilograms. The scanner sent it exactly as typed. It always does; the scanner has no opinions. So the load board threw `NumberFormatException` halfway through its job, and by then the tracking page had already told the world that PP-7782 was on a bike. And no text went out at all, because the text handler compares the type with `"deliver"`, one letter short, and nothing ever complains. Each handler parses and checks for itself, so each one can fail in its own way, and the compiler can't see any of it.

The fix comes in three pieces, one per section, and Part 3 has already given us each one. A closed list of event types, so the compiler knows every case: the form with a fixed set of boxes to tick, from Sealed types: hierarchies the compiler can check. Small types for ids and weights, so a bad value can't even be built: the units on numbers from Value classes and what they compile to. And one function at the door that copies each scan onto the right form, or hands back a note saying what was wrong: the clerk at the door from Data-oriented programming, and Project Valhalla. Behind that door, no handler ever reads a raw field again.

Before you run the demo, predict which scan fails, in which handler, and how many texts go out."""

S2 = """Here is the model. Each event is a fact about one parcel, named in the past tense, and that naming is a decision. Observer and Command put requests on order slips, "restock rye bread, 12 loaves", which can wait, be done or be crossed out. An event is a different kind of paper. It says something already happened, so a handler can't refuse it, only react to it.

```java
sealed interface ParcelEvent permits ParcelBooked, DeliveryFailed, Handover {
    ParcelId parcelId();
}
record ParcelBooked(ParcelId parcelId, Weight weight) implements ParcelEvent {}
record DeliveryFailed(ParcelId parcelId, FailReason reason) implements ParcelEvent {}

sealed interface Handover extends ParcelEvent permits ParcelCollected, ParcelDelivered {
    Weight weight();
}
record ParcelCollected(ParcelId parcelId, Weight weight) implements Handover {}
record ParcelDelivered(ParcelId parcelId, Weight weight) implements Handover {}
```

```kotlin
sealed interface ParcelEvent { val parcelId: ParcelId }
data class ParcelBooked(override val parcelId: ParcelId, val weight: Weight) : ParcelEvent
data class DeliveryFailed(override val parcelId: ParcelId, val reason: FailReason) : ParcelEvent

sealed interface Handover : ParcelEvent { val weight: Weight }
data class ParcelCollected(override val parcelId: ParcelId, override val weight: Weight) : Handover
data class ParcelDelivered(override val parcelId: ParcelId, override val weight: Weight) : Handover
```

Read it from the top. A sender booked a pickup, and nothing has moved yet. A delivery failed, with a reason such as `NOBODY_HOME`. And a handover is the moment a parcel passes from one pair of hands to another: collected from the sender, or delivered at the door.

`sealed` closes the list of direct subtypes, the types that implement an interface or extend a class directly. Sealed types: hierarchies the compiler can check pictured it as a request form with a fixed set of boxes to tick. In Kotlin, the subtypes must sit in the same package and the same module, the set of files the compiler builds together; Java names them after `permits`. Each leaf is a data class in Kotlin and a record in Java: a final class that holds its values and compares by them. Its properties are `val`s of types that never change, so an event is like a page in the printed recipe book of Immutable data and a functional core: a correction is a new edition, made with `copy()`, never a crossing-out. That matters in lesson 2, where every handler gets the very same object. So every branch of the tree ends at a leaf, except `Handover`, which is sealed again one level down. That middle level is a decision we'll use in lesson 2: a handler for `Handover` will hear about collections and deliveries, and nothing else.

The payoff is the exhaustive `when`: a `when`, or a Java `switch`, with a branch for every subtype and no `else`. The compiler checks it against the list, the way the clerk in Pattern matching with switch and record patterns worked down a printed sheet with one line per box:

```java
static boolean changesHands(ParcelEvent e) {
    return switch (e) {
        case Handover h -> true;                  // one case covers both leaves
        case ParcelBooked b -> false;
        case DeliveryFailed f -> false;
    };
}
```

```kotlin
fun changesHands(e: ParcelEvent): Boolean = when (e) {
    is Handover -> true                           // one branch covers both leaves
    is ParcelBooked, is DeliveryFailed -> false
}
```

Now a new kind of event arrives. Parcels get lost now and then, and nobody plans for it, which is exactly why the compiler should. Add `ParcelLost` to `ParcelEvent`, and every such `when` stops compiling: `'when' expression must be exhaustive. Add the 'is ParcelLost' branch or an 'else' branch.` State and Chain of Responsibility said it about an order's states: the compiler writes your to-do list. An `else` throws that list away. The new event quietly takes the `else` branch wherever nobody went back to look, and the demo's `label` function files every lost parcel under "other".

**A sealed type with no `else` turns a new case into a list of compile errors. Leave the `else` out.**

One gap stays open when the program runs. Exhaustiveness is checked when a file is compiled. If code compiled against the old model meets a `ParcelLost` built by newer code, Kotlin throws `NoWhenBranchMatchedException` and Java throws `MatchException`. In our library that can't happen by surprise, because events arrive as raw fields and pass the door first. An old program refuses the unknown type there, as the last section shows.

In the demo, uncomment `ParcelLost` and predict which of the three functions stop compiling."""

S3 = """Look at this parcel: `RawParcel("PP-7781", 40, 2500)`. Is it 40 grams and 2,500 centimetres long, or the other way round? The demo's `RawParcel` takes two `Long`s, so a swapped call compiles, and the program believes in a 40-gram parcel 25 metres long. Value classes and what they compile to started at the print shop's parcel desk, where every number carries its unit: 500 sheets, 2,500 grams. A value class, a class that wraps exactly one value and is a type of its own to the compiler, puts that unit into code:

```java
record ParcelId(String value) {
    ParcelId {
        if (!value.matches("PP-[0-9]{4,12}"))
            throw new IllegalArgumentException("invalid parcel id: '" + value + "'");
    }
}
record Weight(long grams) {
    Weight {
        if (grams < 0) throw new IllegalArgumentException("weight must not be negative: " + grams);
    }
}
```

```kotlin
@JvmInline
value class ParcelId(val value: String) {
    init { require(PATTERN.matches(value)) { "invalid parcel id: '$value'" } }
    override fun toString(): String = value
    companion object { private val PATTERN = Regex("PP-[0-9]{4,12}") }
}

@JvmInline
value class Weight(val grams: Long) {
    init { require(grams >= 0) { "weight must not be negative: $grams" } }
    override fun toString(): String = BigDecimal.valueOf(grams, 3).stripTrailingZeros().toPlainString() + " kg"
}
```

Now `ParcelCollected(Weight(2_500), ParcelId("PP-7781"))` fails with `Argument type mismatch: actual type is 'Weight', but 'ParcelId' was expected.` And because `init` runs on every construction, a `ParcelId` that exists is a valid one: `PP-` and 4 to 12 digits. Nothing downstream needs to check it again.

You may wonder what all these small types cost. Very little, for the reason that lesson gave. Where a value class is used as itself, the compiler erases it to its one field. That's the print shop's back room, where the units are gone and the machines see plain numbers. The demo prints the fields of `ParcelCollected` through Java reflection, the JDK's way of asking a class about itself, and they are a `java.lang.String` and a `long`. The Java records are separate objects on the heap, the memory where objects live: one for each id and one for each weight. The Kotlin ones become objects too in the places that lesson listed, such as a `List<ParcelId>`, a nullable `Weight?` or a generic `T`.

The one-field rule made a decision for this model. A value class holds one field until Project Valhalla arrives, so a `Weight` is whole grams, and the unit lives in the type's name. That suits Pedal Post, which weighs everything in grams. If a partner courier ever reports pounds, the door converts them, and nothing behind it sees a pound. Lesson 3's design review comes back to that choice.

`Weight` also adds and subtracts, which the load board in lesson 2 will need. `plus` uses `Math.addExact`, which throws `ArithmeticException` instead of wrapping round to a negative number. `minus` needs no check of its own: a result below zero is a negative `Weight`, and the constructor already refuses those.

In the demo, uncomment the swapped constructor call and read both errors. Then compare the field types the Kotlin and Java versions print."""

S4 = """The model refuses bad values, but bad values still arrive. The scanner sends what the rider typed, a partner's program sends what it likes, and a row in a database may have been fixed by hand. So one function turns raw input into the model, in one place, at the edge of the program: the line where outside data comes in. Data-oriented programming, and Project Valhalla pictured it as a clerk at the door who copies each letter onto the right form, or sends it back. Our clerk never throws:

```java
static Parsed parse(Map<String, String> fields) {
    try {
        String type = field(fields, "type");
        return switch (type) {
            case "collected" -> new Ok(new ParcelCollected(new ParcelId(field(fields, "parcelId")), weight(fields)));
            // ... one case per type
            default -> new Rejected("unknown event type: '" + type + "'");
        };
    } catch (IllegalArgumentException e) {
        return new Rejected(e.getMessage());     // a reader or a constructor said no
    }
}
```

```kotlin
fun parseEvent(fields: Map<String, String>): Parsed {
    // field(name) and weight() are small local readers that throw IllegalArgumentException
    return try {
        when (val type = field("type")) {
            "collected" -> Parsed.Ok(ParcelCollected(ParcelId(field("parcelId")), weight()))
            // ... one branch per type
            else -> Parsed.Rejected("unknown event type: '$type'")
        }
    } catch (e: IllegalArgumentException) {
        Parsed.Rejected(e.message ?: "invalid event")  // a reader or a constructor said no
    }
}
```

`Parsed` is a small sealed type of its own, with two cases: `Ok` holds a valid event, and `Rejected` holds the reason a scan was refused. Notice what `parse` does not do. It doesn't check the tracking number's format or the sign of the weight. It calls `ParcelId(...)` and `Weight(...)` and turns their refusal into a `Rejected`. The rules live in the constructors, once. A second copy of them in the parser would drift the first time someone edits one and not the other. And `parseEvent` is a recipe card in the sense of Pure functions: the idea everything else builds on: the same fields always give the same result, and nothing outside it changes, so the lab tests it with plain maps and no setup at all.

Why return a result instead of throwing? Errors as values: sealed results, Result and Either had two cooks. One hands back a note, "the custard split, let's serve cream", and the other throws the pan across the room. An exception is the thrown pan. The code that reads scans has to decide what a bad scan means, and an exception decides for it: it flies out of the reading loop, and the loop stops at the first bad scan. A `Rejected` is the note. The loop can set the scan aside with its reason, count it, and carry on with the next one. Don't retry it, though: a malformed scan stays malformed, however often you read it.

Behind the door, code trusts the types. A function that takes a `ParcelCollected` has a valid tracking number and a positive weight, because no other kind of `ParcelCollected` can exist. There is no `!!`, no `toLong()` and no `if (type == ...)` in any handler you'll write in lesson 2.

The door protects us from the future too. When Pedal Post adds `ParcelLost`, a program that hasn't been updated yet still parses raw fields with its old parser. A `lost` scan lands in its `else` branch and becomes `Rejected("unknown event type: 'lost'")`, and nothing crashes. That's why the edge is the one `when` that keeps its `else`. It's a `when` over strings, and strings can never be listed in full, so the lab's tests do the checking there instead.

**Parse once, at the door, into an event or a note. Behind the door, trust the types.**

The demo's parser knows only collections and deliveries. Predict which of its six scans are rejected, and for what reason, before you run it."""

ASIDE = {
    "title": "What if the scans come through a message broker?",
    "body": "Real programs often get their events from a message broker, a separate program that keeps messages until other programs read them; Kafka and RabbitMQ are well-known ones. The edge is then the loop that reads each message, and it calls `parseEvent` once per message. A `Rejected` goes to a separate queue kept for refused messages, often called a dead-letter queue, with its reason attached, and the loop moves on. Webhooks, calls that another company's program makes into yours, and rows read back from a database are edges too. Each gets one parse function, and nothing behind it handles raw fields.",
}

CLOSING = """We started with a rider's scanner and three handlers that each read its raw text, one of which tripped over 2.5. Now every kind of event is a box on one closed form, and ids and weights carry their units. One clerk at the door turns each scan into a typed event, or a note saying why not.

Now look in your own code for a `Map<String, String>` of raw fields handed to more than one function. Each of those functions is a handler reading raw fields.

Next, we'll build the bus that carries these events to the tracking page, the load board and the text sender. How does one handler sign up for every kind of event at once?"""

L = {
 "id": "cap3-01",
 "title": "A sealed event model",
 "minutes": 40,
 "goal": "By the end you can model a courier's parcel events as a sealed hierarchy of data classes with value-class ids and weights, parse untrusted fields into that model at the door without throwing, and write operations as exhaustive `when` expressions that turn a new event type into a list of compile errors.",
 "opening": OPENING,
 "warmup": {
  "q": "A label helper reads `when (event) { is ParcelCollected -> \"pickup\"; is ParcelDelivered -> \"drop-off\"; else -> \"other\" }`. A teammate adds `ParcelLost` to the sealed `ParcelEvent` interface and ships. What happens to lost parcels?",
  "options": [
   "The build fails until the helper handles ParcelLost",
   "They are labelled \"other\", and nothing tells anyone",
   "The helper throws NoWhenBranchMatchedException when the program runs",
   "Kotlin adds a branch for the new type automatically"
  ],
  "answer": 1,
  "why": "The `else` branch matches anything, including types that didn't exist when it was written, so the compiler has nothing to report. Without the `else`, the same change is a compile error at this very line. `NoWhenBranchMatchedException` only appears when a subtype compiled later reaches a `when` that was exhaustive when it was compiled."
 },
 "sections": [
  {
   "h": "What we'll build: an event library for a bike courier, starting with the model",
   "body": S1,
   "figure": {"svg": FIG_PLAN, "caption": "The whole library. This lesson builds the model and the door in front of it; lessons 2 and 3 add the bus and the API."},
   "try": {
    "title": "Watch the raw-fields version fail",
    "minutes": 4,
    "steps": [
     "Read `StringlyDemo.kt` (or `StringlyDemoJava.java`). Write down which scan fails, in which handler, and how many texts go out.",
     "Run it with the command below.",
     "Find the line that shows the tracking page listed the bad scan before the load board failed.",
     "Fix the typo in `texts` and run again. Then answer: where would a check have to go so that PP-7782 never reaches `tracking` at all?"
    ],
    "code": demo("stringly", "StringlyDemo"),
    "expect": "The third scan prints `tracking collected PP-7782` and then `FAILED   java.lang.NumberFormatException: For input string: \"2.5\"`, so the tracking page already shows a collection that the load board never added. `texts sent: 0`, because of the typo; after the fix it's 1. The only place a check can stop PP-7782 before every handler is in front of all of them: the door this lesson builds."
   }
  },
  {
   "h": "A sealed interface lists every kind of parcel event",
   "body": S2,
   "figure": {"svg": FIG_TREE, "caption": "Five types, four leaves. Sealing Handover keeps the list closed one level down, so one branch can stand for collections and deliveries."},
   "try": {
    "title": "Add an event and read the to-do list",
    "minutes": 5,
    "steps": [
     "Run `ExhaustiveDemo` and look at the `label` column: `other` for the booking and the failed delivery.",
     "Uncomment `ParcelLost` in `ExhaustiveDemo.kt`. Predict which of `summary`, `changesHands` and `label` will fail to compile. Run the demo again to compile it.",
     "In `ExhaustiveDemoJava.java`, uncomment the record and add `ParcelLost` to the `permits` list of `ParcelEvent`. Run the Java twin.",
     "Put both files back the way they were."
    ],
    "code": demo("exhaustive", "ExhaustiveDemo"),
    "expect": "kotlinc reports `'when' expression must be exhaustive. Add the 'is ParcelLost' branch or an 'else' branch.` twice, for `summary` and `changesHands`. `label` compiles without a word, and every lost parcel would be labelled `other`. javac reports `the switch expression does not cover all possible input values` for the same two methods."
   }
  },
  {
   "h": "Value classes give every number its unit",
   "body": S3,
   "try": {
    "title": "Swap two arguments, then look at the fields",
    "minutes": 4,
    "steps": [
     "Run `ValuesDemo`. Read the `RawParcel` line: which number is the weight?",
     "Uncomment the swapped `ParcelCollected(Weight(2_500), ParcelId(\"PP-7781\"))` line and run again. Read the errors.",
     "Comment it out again and run `ValuesDemoJava`. Compare its two `field` lines with the Kotlin output."
    ],
    "code": demo("values", "ValuesDemo"),
    "expect": "Kotlin gives two errors, `Argument type mismatch: actual type is 'Weight', but 'ParcelId' was expected.` and its mirror; Java gives `incompatible types: Weight cannot be converted to ParcelId`. Both versions print `refused: invalid parcel id: '7781'` and `refused: weight must not be negative: -500`. Kotlin's fields are `java.lang.String` and `long`; Java's are the nested `ParcelId` and `Weight` record classes, each a separate object."
   }
  },
  {
   "h": "Check each scan once, at the door, then trust the types",
   "body": S4,
   "aside": ASIDE,
   "try": {
    "title": "Run six scans through the door",
    "minutes": 5,
    "steps": [
     "Read the six scans in `EdgeDemo`'s `main`. For each, predict OK or REJECTED, and the reason.",
     "Run it.",
     "Add a `failed` branch: a `DeliveryFailed(parcelId, reason: String)` data class (a record in Java), and a branch that reads the `reason` field. Run it again and check the count line."
    ],
    "code": demo("edge", "EdgeDemo"),
    "expect": "One scan passes and five are rejected: `grams is not a whole number: '2.5'`, `invalid parcel id: '7781'`, `weight must not be negative: -500`, `missing field 'grams'` and `unknown event type: 'failed'`. The tracking number and the sign were refused by the constructors, not by the parser. With your `failed` branch the last line reads `2 accepted, 4 rejected`."
   }
  }
 ],
 "compare": {
  "title": "The event model in Java and Kotlin",
  "java": {
   "title": "Model.java (Java 21)",
   "src": "record ParcelId(String value) {\n    ParcelId {\n        if (!value.matches(\"PP-[0-9]{4,12}\"))\n            throw new IllegalArgumentException(\"invalid parcel id: '\" + value + \"'\");\n    }\n    @Override public String toString() { return value; }\n}\n\nrecord Weight(long grams) {\n    Weight { if (grams < 0) throw new IllegalArgumentException(\"weight must not be negative: \" + grams); }\n    @Override public String toString() {\n        return BigDecimal.valueOf(grams, 3).stripTrailingZeros().toPlainString() + \" kg\";\n    }\n}\n\nsealed interface ParcelEvent permits ParcelBooked, DeliveryFailed, Handover {\n    ParcelId parcelId();\n}\nrecord ParcelBooked(ParcelId parcelId, Weight weight) implements ParcelEvent {\n    ParcelBooked { if (weight.grams() <= 0) throw new IllegalArgumentException(\"booked weight must be positive: \" + weight); }\n}\nrecord DeliveryFailed(ParcelId parcelId, FailReason reason) implements ParcelEvent {}\n\nsealed interface Handover extends ParcelEvent permits ParcelCollected, ParcelDelivered {\n    Weight weight();\n}\nrecord ParcelCollected(ParcelId parcelId, Weight weight) implements Handover { /* same check */ }\nrecord ParcelDelivered(ParcelId parcelId, Weight weight) implements Handover { /* same check */ }\n\nstatic String summary(ParcelEvent e) {\n    return switch (e) {                                   // no default\n        case ParcelBooked(var id, var weight) -> id + \" booked, \" + weight;\n        case DeliveryFailed(var id, var reason) -> id + \" not delivered: \" + reason;\n        case ParcelCollected(var id, var weight) -> id + \" collected, \" + weight;\n        case ParcelDelivered(var id, var weight) -> id + \" delivered, \" + weight;\n    };\n}"
  },
  "kotlin": {
   "title": "Model.kt",
   "src": "@JvmInline\nvalue class ParcelId(val value: String) {\n    init { require(PATTERN.matches(value)) { \"invalid parcel id: '$value'\" } }\n    override fun toString(): String = value\n    companion object { private val PATTERN = Regex(\"PP-[0-9]{4,12}\") }\n}\n\n@JvmInline\nvalue class Weight(val grams: Long) {\n    init { require(grams >= 0) { \"weight must not be negative: $grams\" } }\n    override fun toString(): String = BigDecimal.valueOf(grams, 3).stripTrailingZeros().toPlainString() + \" kg\"\n}\n\nsealed interface ParcelEvent { val parcelId: ParcelId }\ndata class ParcelBooked(override val parcelId: ParcelId, val weight: Weight) : ParcelEvent {\n    init { require(weight.grams > 0) { \"booked weight must be positive: $weight\" } }\n}\ndata class DeliveryFailed(override val parcelId: ParcelId, val reason: FailReason) : ParcelEvent\n\nsealed interface Handover : ParcelEvent { val weight: Weight }\ndata class ParcelCollected(override val parcelId: ParcelId, override val weight: Weight) : Handover { /* same check */ }\ndata class ParcelDelivered(override val parcelId: ParcelId, override val weight: Weight) : Handover { /* same check */ }\n\nfun summary(event: ParcelEvent): String = when (event) {   // no else\n    is ParcelBooked -> \"${event.parcelId} booked, ${event.weight}\"\n    is DeliveryFailed -> \"${event.parcelId} not delivered: ${event.reason}\"\n    is ParcelCollected -> \"${event.parcelId} collected, ${event.weight}\"\n    is ParcelDelivered -> \"${event.parcelId} delivered, ${event.weight}\"\n}"
  },
  "note": "Both versions have the same shape: sealed interfaces for the kinds, final carriers for the leaves, the checks in the constructor, and one exhaustive switch per operation. Three things differ. Kotlin's value classes compile to a `String` and a `long` wherever they're used as themselves, while Java's `ParcelId` and `Weight` records are separate objects until value records arrive with Valhalla. Java names the subtypes in `permits` (or infers them within one file), while Kotlin requires them to share the package and module. And a data class's `copy()` runs `init`, so `collected.copy(weight = Weight.ZERO)` throws: a new edition of the form goes past the clerk again, and records have no `copy` at all. kotlinc also writes the same `PermittedSubclasses` attribute that javac does, so Java code can switch exhaustively over this Kotlin model, which lesson 3 relies on."
 },
 "worked": {
  "title": "Add a new event type, end to end",
  "steps": [
   {
    "say": "A parcel goes missing: PP-7781 never reaches its door, and Pedal Post wants a record of it, with its weight, for the insurance claim. First decide where the event goes. Nobody handed the parcel to anyone, so it isn't a `Handover`. It's a direct subtype of `ParcelEvent`, with the same positive-weight rule as the others.",
    "code": "data class ParcelLost(override val parcelId: ParcelId, val weight: Weight) : ParcelEvent {\n    init { require(weight.grams > 0) { \"lost weight must be positive: $weight\" } }\n}",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "// and add ParcelLost to the permits list of ParcelEvent\nrecord ParcelLost(ParcelId parcelId, Weight weight) implements ParcelEvent {\n    ParcelLost {\n        if (weight.grams() <= 0) throw new IllegalArgumentException(\"lost weight must be positive: \" + weight);\n    }\n}"
   },
   {
    "say": "Compile before you write anything else. Every exhaustive `when` over `ParcelEvent` fails with `'when' expression must be exhaustive. Add the 'is ParcelLost' branch or an 'else' branch.` That list is your to-do list. Anything written against `Handover` still compiles, because its list of subtypes didn't change. Add the branch to `summary`:",
    "code": "is ParcelLost -> \"${event.parcelId} lost, ${event.weight}\"",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "case ParcelLost(var id, var weight) -> id + \" lost, \" + weight;"
   },
   {
    "say": "Now the door. Its `when` is over a string, which can't be exhaustive, so it keeps its `else` and the compiler says nothing. A test has to do that job. The lab's `every event type has a summary line` test compares its samples with `ParcelEvent::class.sealedSubclasses`, so it fails until someone adds a lost sample, which reminds them to add the parser branch and its test:",
    "code": "\"lost\" -> ParcelLost(ParcelId(field(\"parcelId\")), weight())",
    "lang": "kotlin",
    "alt_lang": "java",
    "alt_code": "case \"lost\" -> new Ok(new ParcelLost(new ParcelId(field(fields, \"parcelId\")), weight(fields)));"
   },
   {
    "say": "Last, the order of updates. Programs that haven't been updated still parse raw fields with the old parser, so a `lost` scan lands in their `else` branch and becomes `Rejected(\"unknown event type: 'lost'\")`. Nothing crashes. Update the programs that read scans first, then the one that sends them, and look through the rejected scans for any that arrived in between.",
    "code": "",
    "lang": ""
   }
  ]
 },
 "lab": {
  "title": "Build the event model and its door",
  "minutes": 15,
  "files": [
   "labs/events/src/main/kotlin/workbench/events/l01/Values.kt",
   "labs/events/src/main/kotlin/workbench/events/l01/Model.kt",
   "labs/events/src/main/kotlin/workbench/events/l01/Parsing.kt",
   "labs/events/src/main/kotlin/workbench/events/l01/Summary.kt"
  ],
  "run": "./gradlew :events:test --tests 'workbench.events.l01.*'",
  "steps": [
   "Run the tests. Eleven of the twelve fail; the one that passes checks `toString`, which is given.",
   "`Values.kt` (TODOs 1 and 2): add a `require` to each `init` block, and write `plus` and `minus` with `Math.addExact` and `Math.subtractExact`. Why does `minus` need no check of its own for a result below zero?",
   "`Model.kt` (TODO 3): give the three events that carry a weight an `init` block that refuses zero.",
   "`Parsing.kt` (TODO 4): write `parseEvent`. Read the KDoc for the exact messages. It must never throw.",
   "`Summary.kt` (TODO 5): delete the `else` branch, run the tests to compile, and add the branches the error asks for.",
   "Run until all twelve pass. Then add a stray `else -> \"?\"` to `summary` and run again: the build stays green, and the only sign is the warning `'when' is exhaustive so 'else' is redundant here.` Delete it again."
  ],
  "hints": [
   "`require(condition) { \"message\" }` throws `IllegalArgumentException` with that message when the condition is false.",
   "`minus` builds a new `Weight`, and the constructor already refuses a negative value.",
   "Inside `parseEvent`, write two local helpers: `field(name)`, which throws `IllegalArgumentException(\"missing field '$name'\")`, and `weight()`, which uses `toLongOrNull()` and throws when it gets `null`. Then wrap the whole `when` in one `try`/`catch (e: IllegalArgumentException)`.",
   "Inside the `try`, `else -> return Parsed.Rejected(\"unknown event type: '$type'\")` returns from `parseEvent` directly.",
   "`FailReason.entries.find { it.name == raw }` gives `null` for an unknown reason."
  ],
  "done_when": "All twelve tests in `ModelTest` pass."
 },
 "drill": {
  "title": "Write the hierarchy from memory",
  "minutes": 5,
  "prompt": "Close the lab. In a blank file, write the sealed hierarchy from memory: `ParcelEvent`, the sealed `Handover` and the four leaves (plain `String` ids and `Long` grams are fine). Then write `changesHands(e)` with no `else`, using one branch for `Handover`. Finally, add `ParcelLost` and say which of your functions must change.",
  "answer": {
   "lang": "kotlin",
   "src": "sealed interface ParcelEvent { val parcelId: String }\ndata class ParcelBooked(override val parcelId: String, val grams: Long) : ParcelEvent\ndata class DeliveryFailed(override val parcelId: String, val reason: String) : ParcelEvent\n\nsealed interface Handover : ParcelEvent { val grams: Long }\ndata class ParcelCollected(override val parcelId: String, override val grams: Long) : Handover\ndata class ParcelDelivered(override val parcelId: String, override val grams: Long) : Handover\n\nfun changesHands(e: ParcelEvent): Boolean = when (e) {\n    is Handover -> true\n    is ParcelBooked, is DeliveryFailed -> false\n}\n\n// ParcelLost : ParcelEvent breaks changesHands (add `is ParcelLost -> false`).\n// A when over Handover alone would still compile.",
   "alt": {
    "lang": "java",
    "src": "sealed interface ParcelEvent permits ParcelBooked, DeliveryFailed, Handover { String parcelId(); }\nrecord ParcelBooked(String parcelId, long grams) implements ParcelEvent {}\nrecord DeliveryFailed(String parcelId, String reason) implements ParcelEvent {}\n\nsealed interface Handover extends ParcelEvent permits ParcelCollected, ParcelDelivered { long grams(); }\nrecord ParcelCollected(String parcelId, long grams) implements Handover {}\nrecord ParcelDelivered(String parcelId, long grams) implements Handover {}\n\nstatic boolean changesHands(ParcelEvent e) {\n    return switch (e) {\n        case Handover h -> true;\n        case ParcelBooked b -> false;\n        case DeliveryFailed f -> false;\n    };\n}\n\n// ParcelLost (added to permits) breaks changesHands: add `case ParcelLost l -> false;`."
   }
  }
 },
 "closing": CLOSING,
 "recap": [
  "Handlers that read raw fields each parse and check for themselves, so a bad scan fails deep inside one of them after others have already acted on it.",
  "A sealed interface closes the list of event types: Kotlin subtypes share its package and module, and Java names them in `permits`. A sealed middle level such as `Handover` lets one branch stand for its leaves.",
  "Write every operation as a `when` or `switch` with no `else`, so a new event type becomes a compile error at each place that must handle it.",
  "Value classes give ids and weights their own types at no cost where they're used as themselves, and their `init` blocks make every instance valid. One field only, so a `Weight` is whole grams.",
  "Parse once, at the door, into the model. Return `Ok` or `Rejected`, never throw, and let the constructors make the checks. Behind the door, trust the types.",
  "Where today's model stops: it describes events, and nothing delivers them yet. The tracking page, the load board and the texts still can't hear a scan; lesson 2 builds the bus."
 ],
 "quiz": [
  {
   "q": "From *Sealed types: hierarchies the compiler can check*: you move `ParcelDelivered` into a new package, `workbench.events.deliveries`, in the same module. It still implements the sealed `Handover`. What happens?",
   "options": [
    "It compiles: the same module is enough",
    "kotlinc reports an error: a direct subtype of a sealed interface must be in the same package and module",
    "It compiles with a warning, and `when` over Handover loses its exhaustiveness check",
    "It compiles as long as the file is listed in `permits`"
   ],
   "answer": 1,
   "why": "Kotlin's rule is the same package and the same module, with no `permits` clause at all. The closed list is what makes the `when` checkable, so the compiler refuses a subtype elsewhere instead of quietly opening the form to new boxes. The first option is the tempting one, because Java's rule for named modules is the module alone.",
   "from": "dop-02"
  },
  {
   "q": "From *Value classes and what they compile to*: a `val recent: List<ParcelId>` holds 10,000 tracking numbers. What does the list hold when the program runs?",
   "options": [
    "10,000 `ParcelId` boxes, each wrapping a `String`",
    "10,000 plain `String`s, because value classes are always erased",
    "One shared `ParcelId` object",
    "10,000 `ParcelId` objects, but only on JDK 25 and later"
   ],
   "answer": 0,
   "why": "A value class is boxed whenever it's used as another type, and a generic type argument is one of those places. So `List<ParcelId>` costs one object per element, the same as a list of any other wrapper. The erasure to a plain `String` happens for fields, parameters and return values typed `ParcelId`, which is why the second option is so tempting.",
   "from": "kt-02"
  },
  {
   "q": "`fun loadChange(e: Handover): Long = when (e) { is ParcelCollected -> e.weight.grams; is ParcelDelivered -> -e.weight.grams }`. Someone adds `data class ParcelLost(...) : ParcelEvent`. Does `loadChange` still compile?",
   "options": [
    "No: every `when` over the hierarchy must handle the new type",
    "Only after adding an `else` branch",
    "Yes, but it throws for lost parcels",
    "Yes: the list of `Handover` subtypes didn't change"
   ],
   "answer": 3,
   "why": "`loadChange` switches over `Handover`, and a lost parcel isn't a handover. Only `when`s over `ParcelEvent` itself get the new error. That's the benefit of a sealed middle level: code written against it is shielded from changes elsewhere in the tree. And a lost parcel can't even reach `loadChange`, because the parameter type won't accept it."
  },
  {
   "q": "From *Data-oriented programming, and Project Valhalla*: `parseEvent` receives `grams = \"-500\"` for a delivery. Which code should notice?",
   "options": [
    "`parseEvent`, with its own `if (grams < 0)` check before building the event",
    "The load board, before it subtracts the weight",
    "`Weight`'s `init` block, and `parseEvent` turns its exception into `Rejected`",
    "Nobody: a negative delivery is a valid way to write a collection"
   ],
   "answer": 2,
   "why": "The rule lives in the constructor, once, so every path that builds a `Weight` obeys it. The parser only turns the refusal into a value. A second check in the parser drifts from the first, and a check in the load board means an invalid event already got past the door.",
   "from": "dop-04"
  },
  {
   "q": "From *State and Chain of Responsibility*: your program was compiled against version 1.4 of the model. Someone swaps in the 1.5 jar, the library file, which adds `ParcelLost`, without recompiling the program. A component built against 1.5 hands a lost parcel to the program's `summary`, which has no `else`. What happens?",
   "options": [
    "`summary` returns an empty string",
    "`summary` throws `NoWhenBranchMatchedException`",
    "The JVM refuses to load `ParcelLost`",
    "`summary` falls through to its last branch"
   ],
   "answer": 1,
   "why": "Exhaustiveness is checked at compile time. For an exhaustive `when` with no `else`, kotlinc adds a hidden throw for the remainder: a subtype it never saw. Java's switch throws `MatchException` in the same situation. Events that arrive as raw fields avoid this, because the old parser rejects the unknown type at the door.",
   "from": "pat-09"
  }
 ],
 "flashcards": [
  {"front": "Why no `else` in a `when` over your own sealed type?", "back": "Without it, a new subtype is a compile error at every `when` that must handle it. With it, the new subtype silently takes the `else` branch."},
  {"front": "What does a sealed middle level like `Handover` give you?", "back": "One branch, `is Handover`, covers its leaves (collections and deliveries), and code written against it doesn't break when siblings are added elsewhere."},
  {"front": "`@JvmInline value class ParcelId(val value: String)`: what is a `ParcelId` field when the program runs?", "back": "A plain `String` field. It is boxed only when used as another type: generic, nullable, an interface or `Any`."},
  {"front": "Why does `Weight` hold only grams, with no unit field?", "back": "A JVM value class holds exactly one field. Pedal Post weighs in grams, so the unit is in the type's name, and any other unit is converted at the door."},
  {"front": "What does the edge function return for a malformed scan?", "back": "`Parsed.Rejected(reason)`, never an exception. The caller decides what to do with it: set it aside, count it, and carry on."},
  {"front": "Where does `parseEvent` check that a tracking number is well formed?", "back": "It doesn't. It calls `ParcelId(raw)`, whose `init` checks, and turns the `IllegalArgumentException` into `Rejected`."},
  {"front": "A program that hasn't been updated gets a scan of a new event type as raw fields. What happens?", "back": "Its parser's `else` branch returns `Rejected(\"unknown event type\")`. Nothing crashes, so update the programs that read events before the ones that send them."}
 ],
 "terms": [
  {"term": "Event", "plain": "A value that says something already happened, such as a parcel being collected."},
  {"term": "Sealed hierarchy", "plain": "A type whose list of direct subtypes is closed and known to the compiler."},
  {"term": "Exhaustive when", "plain": "A `when` or `switch` with a branch for every possible subtype and no `else`, checked at compile time."},
  {"term": "Value class", "plain": "A one-field wrapper that is its own type in Kotlin and compiles to its field where it can."},
  {"term": "Edge", "plain": "The one place where raw input from outside the program becomes model values, or is refused."},
  {"term": "Remainder", "plain": "The cases an exhaustive switch can still meet when the program runs: null, and subtypes compiled after it."}
 ],
 "explain_back": {
  "prompt": "A teammate asks why handlers take a `ParcelCollected` instead of the scanner's `Map<String, String>`: \"the map has everything, and it's one less type to maintain.\" Explain what the sealed model and the door buy you, using a bug you could get with the map.",
  "answer": "With the map, every handler parses and checks for itself. A scan that says \"2.5\" grams throws inside the load board after the tracking page already listed it, and a typo like \"deliver\" silently never matches. The model closes the list of event types, so a `when` without `else` lists every place that must change when a type is added. Value classes make a swapped id and weight a compile error, and their constructors make every instance valid. The door parses each scan once and returns `Ok` or `Rejected`, so a bad scan is set aside, with its reason, before any handler acts. Behind it, a handler that takes a `ParcelCollected` knows it has a valid tracking number and a positive weight. The extra types cost a few lines, and they remove a whole family of bugs that only show up on the day a rider types kilograms."
 },
 "deeper": {
  "minutes": 10,
  "body": """Three questions come up once a model like this runs for real.

How do events change over time? Adding a field with a default is safe for programs that parse at the door: old scans lack the field and get the default. Renaming a type or a field is not. Keep the old name in the parser for as long as old scans can arrive, and map it to the new type there, so the model itself never carries the history. If you turn the model into JSON with kotlinx.serialization, as *Compiler plugins: all-open, no-arg and kotlinx.serialization* showed, pin each type's name with `@SerialName` for the same reason.

Should the door return `Either` instead of a sealed `Parsed`? The `Either<String, ParcelEvent>` from *Generics workshop: a type-safe container and event bus* works, and it composes with `map` and `flatMap`. A dedicated `Parsed` reads better where it's used (`is Parsed.Rejected`), and it leaves room for a third case later, such as `Ignored` for event types a program deliberately doesn't handle. Kotlin's `Result<T>` is the wrong fit: its failure side is a `Throwable`, and a rejected scan is not an exception, as *Errors as values: sealed results, Result and Either* argued.

What about the database? Rows you read back are untrusted input too. A column holding `'collected'` and a nullable `grams` column are a raw map with a schema, and a migration or a fix made by hand can break them. Read rows through the same kind of edge function, or reuse `parseEvent` by turning each row into its map of fields.

Java has one tool here that Kotlin doesn't need: since JDK 21, a pattern switch can take `case null` explicitly. Kotlin rules null out at compile time by declaring the parameter non-nullable. Both end up with the same guarantee behind the door."""
 },
 "sources": [
  {"title": "Sealed classes and interfaces (Kotlin docs)", "url": "https://kotlinlang.org/docs/sealed-classes.html"},
  {"title": "Inline value classes (Kotlin docs)", "url": "https://kotlinlang.org/docs/inline-classes.html"},
  {"title": "JEP 409: Sealed Classes", "url": "https://openjdk.org/jeps/409"},
  {"title": "Brian Goetz, Data Oriented Programming in Java (InfoQ, 2022)", "url": "https://www.infoq.com/articles/data-oriented-programming-java/"},
  {"title": "Preparing for Change: Safe Switching over Sealed APIs (Bimpoudis, Buckley, Goetz, 2026)", "url": "https://github.com/openjdk/amber-docs/blob/master/site/guides/exhaustiveness-guide.md"}
 ]
}
out = ROOT / "content/lessons/cap3-01.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
