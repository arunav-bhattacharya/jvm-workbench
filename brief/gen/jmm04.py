import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/jmm/src"
P = "java/workbench/jmm/l04"
K = "kotlin/workbench/jmm/l04"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"{lab}/demo/{P}/{name}.java"
kdemo = lambda name: f"{lab}/demo/{K}/{name}.kt"
run = lambda name: f"./gradlew :jmm:demo -Pmain=workbench.jmm.l04.{name}"


def code(name):
    """A Java demo with its Kotlin twin (Foo.kt with a top-level main, class FooKt)."""
    return {"lang": "java", "title": f"{name}.java", "src": read(demo(name)), "run": run(name), "file": demo(name),
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(kdemo(name)), "run": run(name + "Kt"), "file": kdemo(name)}}


FIG = (
    '<svg viewBox="0 0 680 300" role="img" aria-label="Left: the loader thread makes a RateCard with every field null, sets its currency, '
    'then stores the reference in current. Right: a request thread may see the store to current first, read current as not null, '
    'read its currency as null, and only later see the currency write.">'
    '<text class="t" x="160" y="30" text-anchor="middle">Loader, in program order</text>'
    '<text class="t" x="520" y="30" text-anchor="middle">What a request thread may see</text>'
    '<rect class="box" x="20" y="48" width="280" height="36" rx="8"/>'
    '<text class="t-s t-code" x="160" y="71" text-anchor="middle">c = new RateCard()  // fields null</text>'
    '<rect class="box" x="20" y="108" width="280" height="36" rx="8"/>'
    '<text class="t-s t-code" x="160" y="131" text-anchor="middle">c.currency = "EUR"</text>'
    '<rect class="box-a" x="20" y="168" width="280" height="36" rx="8"/>'
    '<text class="t-s t-code" x="160" y="191" text-anchor="middle">current = c   // publish</text>'
    '<line class="ln" x1="160" y1="84" x2="160" y2="106" marker-end="url(#arr)"/>'
    '<line class="ln" x1="160" y1="144" x2="160" y2="166" marker-end="url(#arr)"/>'
    '<rect class="box-a" x="380" y="48" width="280" height="36" rx="8"/>'
    '<text class="t-s t-code" x="520" y="71" text-anchor="middle">current = c becomes visible</text>'
    '<rect class="box" x="380" y="108" width="280" height="36" rx="8"/>'
    '<text class="t-s t-code" x="520" y="131" text-anchor="middle">reader: current != null</text>'
    '<rect class="box-bad" x="380" y="168" width="280" height="36" rx="8"/>'
    '<text class="t-s t-code" x="520" y="191" text-anchor="middle">reader: currency == null</text>'
    '<rect class="box-dim" x="380" y="228" width="280" height="36" rx="8"/>'
    '<text class="t-s t-code" x="520" y="251" text-anchor="middle">currency = "EUR" visible</text>'
    '<line class="ln" x1="520" y1="84" x2="520" y2="106" marker-end="url(#arr)"/>'
    '<line class="ln" x1="520" y1="144" x2="520" y2="166" marker-end="url(#arr)"/>'
    '<line class="ln" x1="520" y1="204" x2="520" y2="226" marker-end="url(#arr)"/>'
    '<line class="ln-d" x1="300" y1="186" x2="378" y2="68" marker-end="url(#arr)"/>'
    '<text class="t-s t-ok" x="160" y="250" text-anchor="middle">a volatile current, or a final</text>'
    '<text class="t-s t-ok" x="160" y="268" text-anchor="middle">currency, rules out the red box</text>'
    '</svg>'
)

OPENING = """Picture writing a letter to a friend. You write three pages, fold them into an envelope, seal it and give it to a courier. Your friend opens it and reads all three pages. Nobody worries that the courier might deliver the envelope while page three is still on your desk.

Java programs hand objects between threads like this all day. (A thread is one path of work running beside others in the same program.) A loader thread runs `registry.current = new RateCard("EUR", fees);`. The constructor writes the pages, and the assignment hands over the envelope. Yet another thread can read `registry.current`, find a real rate card, and see `null` where its currency should be.

It's an easy trap, because the line reads in one direction: build, then store. In the thread that runs it, that's what happens. The last lesson showed how a `volatile` field makes one new value visible to other threads, but an object is many fields. In this lesson, we'll watch an object arrive half-written, seal the envelope four ways, see what `final` fields promise, and keep a constructor from showing its object too early. Before we start, make a guess, and keep it in mind."""

S0 = """When a customer pays by card, the card company charges the shop a small fee, say 1.20 euros for a VISA payment. The shop's program keeps these fees in a `RateCard`: a currency, and a fee for each card brand. A loader thread builds a new rate card whenever the fees change. The request threads, which handle the payments, read the current one.

Handing an object to another thread like this is called **publishing** it: storing a reference to it where another thread can find it, such as a shared field, a static field or a collection. (A reference is the value a variable holds to point at an object.) Here is the loader's side:

```java
// Naive: publishing through a plain field
RateCard card = new RateCard("EUR", fees);   // 1. make the object, 2. run the constructor
registry.current = card;                     // 3. publish: store the reference where others look
```

```kotlin
// Naive: publishing through a plain field
val card = RateCard("EUR", fees)             // 1. make the object, 2. run the constructor
registry.current = card                      // 3. publish: store the reference where others look
```

Three things happen. The JVM, the program that runs your Java code, makes the object with every field at its default value: 0, false or null. The constructor writes the real values. Then the reference is stored in `current`. In the loader thread, they happen in exactly that order.

A request thread that reads `current` gets no such promise. A write is guaranteed visible to a read in another thread only when a happens-before edge links them. A write to a `volatile` field, a field whose reads always see the latest write, and a later read of that field form one such edge. Happens-before, the rules that matter, lists them all. Here, nothing links the request thread's read to the loader's writes. So two layers are free to change the order. The JIT, the compiler inside the JVM that turns busy code into machine code while it runs, may move the store of the reference ahead of the constructor's stores. And the processor may show its stores to its other cores, the parts of the processor that each run one thread at a time, in a different order. ARM processors, such as the ones in Apple Silicon laptops, do this more than Intel and AMD processors. A request thread can then see `current != null` and still read a `null` currency or a fee of 0. That's called a partially constructed object, and no line you wrote creates one.

In the letter's terms, the courier delivered the envelope before all the pages were inside. The figure shows it. The picture breaks in one place: a real courier can't carry pages you haven't written yet. Here the reordering happens in layers you never see, and the code gives no hint of it.

It isn't only theory. jcstress, a tool from OpenJDK (the open-source project that builds Java), runs tiny tests on several threads at once, millions of times, and counts every result. It has a sample called `BasicJMM_08_Finals`. One thread publishes an object with four plain `int` fields, set to 1, 2, 3 and 4, through a plain field. Another thread reads the four fields. Here is the run recorded in the sample, on an x86_64 machine (the Intel and AMD kind), where -1 means the reader didn't see the object yet:

```text
          RESULT      SAMPLES     FREQ       EXPECT  DESCRIPTION
  -1, -1, -1, -1  115,042,024   52.43%   Acceptable  Object is not seen yet.
      1, 0, 3, 0        3,892   <0.01%  Interesting  Seeing partially constructed object.
      1, 0, 3, 4       14,291   <0.01%  Interesting  Seeing partially constructed object.
      1, 2, 3, 0          123   <0.01%  Interesting  Seeing partially constructed object.
      1, 2, 3, 4  104,365,974   47.56%   Acceptable  Seen the complete object.
```

About 18,000 of 219 million readers found blank pages. That's rare, but a busy shop takes a lot of card payments. On an AArch64 machine, a 64-bit ARM one, the same sample saw almost every mix of zeros and real values.

You may wonder how the x86 machine did it, when Why your loop never stops showed that x86 keeps its stores in order. The sample checks that too. When it asks the JIT to keep those accesses in order, the half-built objects vanish on x86_64 and stay on ARM. On x86, the JIT moved the stores.

Publishing through a plain field fails in a second way you met in Why your loop never stops: a reader that loops, waiting for the first card, may read the field once and never again. The lab's `RateCardRegistry` has exactly that bug.

**A reader can see a reference before the fields behind it. Never publish through a plain field.**

So the envelope can arrive with blank pages, or not at all. Next, we'll seal it, so the reference and the fields arrive together."""

S1 = """An object is **safely published** when the reference and the state the object had at that moment reach the reader together. In the letter's terms, the envelope is sealed: whoever opens it finds every page that was inside when you sealed it. *Java Concurrency in Practice*, the classic book on the subject, lists four seals:

1. Build the object in a static initializer, the code that runs once when a class is first used. The JVM runs it under a lock, and every thread that uses the class afterwards sees the result.
2. Store it in a `volatile` field or an `AtomicReference` (the holder for one reference from Atomics and compare-and-set).
3. Store it in a `final` field of an object that is itself properly built (the next section).
4. Store it in a field guarded by a lock, or hand it over through a `java.util.concurrent` class, such as a concurrent map or queue.

Each seal is an edge you have met before. Seal 1 uses the lock the JVM holds while it initializes a class. Seal 2 is a volatile write and a later read of the same field. Seal 4 is a lock released by one thread and taken by another, or a hand-over through a concurrent collection. Seal 3 is new, and it gets the next section. Everything the loader wrote before the seal reaches a reader who breaks the same seal. Here is the registry with three of them:

```java
// Fixed: three safe ways to publish, in one class
class RateCardRegistry {
    static final RateCard DEFAULT = new RateCard("EUR", Map.of("VISA", 120L));            // 1. static initializer
    private volatile RateCard current = DEFAULT;                                         // 2. volatile field
    private final ConcurrentMap<String, RateCard> byCurrency = new ConcurrentHashMap<>(); // 4. concurrent map

    void publish(RateCard card) {
        current = card;                              // a volatile write seals it
        byCurrency.put(card.currency(), card);       // and so does put
    }

    RateCard current() {
        return current;                              // a volatile read breaks the same seal
    }
}
```

```kotlin
// Fixed: three safe ways to publish, in one class
class RateCardRegistry {
    companion object {
        val DEFAULT = RateCard("EUR", mapOf("VISA" to 120L))           // 1. static initializer (companion object)
    }
    @Volatile private var current: RateCard = DEFAULT                   // 2. @Volatile property
    private val byCurrency = ConcurrentHashMap<String, RateCard>()     // 4. concurrent map

    fun publish(card: RateCard) {
        current = card                               // a volatile write seals it
        byCurrency[card.currency] = card             // and so does put
    }

    fun current(): RateCard = current                // a volatile read breaks the same seal
}
```

Both versions do the same three things. Kotlin's companion object is initialized together with its class, just like a Java static initializer, so seal 1 works the same way, and `@Volatile` is Kotlin's `volatile`.

Notice that both sides take part. The loader writes the volatile field, and the reader reads that same field. A seal only the writer uses is no seal. A `synchronized` publish method with a plain getter, for example, gives the reader no edge at all, because the reader never takes the lock.

Which seal should you pick? For something you replace while the program runs, such as the current rate card, use a `volatile` field or an `AtomicReference`. For a constant, use `static final`. Don't add `synchronized` getters only to publish: a volatile read costs less and says what you mean.

**Hand an object to another thread through a seal: a volatile field, a static initializer, a lock or a concurrent collection.**

A seal covers the pages that were inside when you sealed the envelope. If the loader changes the rate card after publishing it, each change needs a seal of its own. That's why the easiest objects to publish are the ones that never change, and Java keeps a special promise for them."""

S2 = """`final` fields get one extra promise from the Java memory model, the rules for what one thread sees of another thread's writes. The Java Language Specification (section 17.5) says, in plain words: a thread that sees a reference to an object only after the object's constructor has finished is guaranteed to see the correct values of its final fields. No volatile and no lock are needed. The promise holds even when the reference reached the reader through a data race, a write and a read of the same field with no edge between them.

The promise reaches through the field. If a final field points to a map or an array, the reader also sees its contents as they were when the constructor ended. The specification calls the end of the constructor the **freeze**: that's when the final fields are frozen.

In the letter's terms, final fields are pages glued into the envelope at the factory. However the envelope travels, sealed or not, whoever opens it finds those pages in place.

Here's a fee quote with both kinds of field:

```java
final class Quote {
    private final String scheme;            // final: correct even through a race
    private final Map<String, Long> fees;   // final: and the map's contents as of the freeze
    private long hits;                      // plain: a racing reader may see 0

    Quote(String scheme, Map<String, Long> fees) {
        this.scheme = scheme;
        this.fees = Map.copyOf(fees);
    }
}
```

```kotlin
class Quote(scheme: String, fees: Map<String, Long>) {
    private val scheme = scheme                 // val: a final field, correct even through a race
    private val fees = fees.toMap()             // val: and the map's contents as of the freeze
    private var hits = 0L                       // var: a plain field, a racing reader may see 0
}
```

The Kotlin version is the same class: a `val` compiles to a final field, and a `var` to a plain one. The Try it below checks that in the compiled classes.

Back to `BasicJMM_08_Finals`. Its last test makes all four fields final and publishes the object through the same plain field. The recorded results, on x86_64 and on AArch64 alike, show readers seeing either no object or the complete one: not one partial object. The test now marks every other result as forbidden.

How does the JVM keep this promise? When a constructor writes a final field, HotSpot, the JVM most people run, puts a barrier at the end of the constructor. Every store before the barrier must be visible before any store after it, and the store that publishes the reference always comes after. On x86 the barrier costs nothing, because the processor keeps stores in order anyway; it only stops the JIT from moving stores past it. On ARM it's a real fence instruction, one that makes the processor finish the earlier stores first.

Put the pieces together and you get the immutable object from Don't share: a final class, every field final, changing inputs copied in the constructor, nothing changeable handed out, and no `this` handed to anyone before the constructor ends. Don't share showed that such an object needs no lock. Here is the reason underneath: thanks to the final-field promise, no reader can see it half-built, however it arrived. Records and Kotlin classes with only `val` properties get you most of the way. They still keep a caller's list as it is, so copy it, for example in a record's compact constructor, the one with no parameter list: `record FeeSchedule(List<Fee> fees) { FeeSchedule { fees = List.copyOf(fees); } }`.

The promise has two limits. Final fields don't deliver the envelope: a reader that waits on a plain field may still never see the reference at all. That's why the lab's `RateCardRegistry` needs `volatile` even after `RateCard` becomes immutable. And the promise starts at the freeze, so it only holds if nobody got the reference before the constructor finished.

**Final fields arrive whole through any race, but they don't deliver the reference. Make the data final, and still publish it through a seal.**

That second limit is easy to break without noticing. Next, we'll see how a constructor hands out its object too early."""

S3 = """Picture a new house and the agent who will sell it. The builders work first: walls, floor, wiring. When they're done, the agent hands out the address and opens the door to buyers. Now picture an agent who hands out the address on the first morning. A buyer arrives while the floor is still a hole in the ground.

A constructor is the builders' work, and `this`, the reference to the object being built, is the address. Handing `this` to other code before the constructor ends is called **escaping this**. The code that receives it is the early buyer: it sees the object with some fields still at their defaults. It doesn't even need another thread.

`this` escapes when a constructor:

- registers the object as a listener (an object that other code calls when something happens);
- starts a thread, or hands over a task, that uses the object;
- creates a lambda or inner class that captures `this` and hands it out;
- calls a method that a subclass can override.

Here's the first case. An event bus is a notice board inside a program: code pins up events, and every registered listener hears each one. The lab's `EventBus` also replays its last event to each new listener the moment it registers. This listener texts the shop manager about any sale over a limit:

```java
// Naive: `this` escapes before the fields are set
class BigSaleAlert implements Consumer<SaleEvent> {
    private final long limitCents;
    private final Phone manager;

    BigSaleAlert(EventBus bus, long limitCents, Phone manager) {
        bus.register(this);                    // the bus calls accept() right here...
        this.limitCents = limitCents;          // ...before these fields are set
        this.manager = manager;
    }

    public void accept(SaleEvent e) {
        if (e.amountCents() > limitCents) manager.text("Big sale: " + e);   // manager is still null
    }
}
```

```kotlin
// Naive: `this` escapes before the properties are set
class BigSaleAlert(bus: EventBus, limitCents: Long, manager: Phone) : Consumer<SaleEvent> {
    init {
        bus.register(this)                     // the bus calls accept() right here...
    }
    private val limitCents = limitCents        // ...before these properties are set
    private val manager = manager

    override fun accept(e: SaleEvent) {
        if (e.amountCents > limitCents) manager.text("Big sale: $e")   // manager is still null
    }
}
```

`register` calls `accept` at once, to replay the last sale. At that moment `limitCents` is still 0, so every sale looks big, and `manager` is still null, so `manager.text` throws a `NullPointerException`. No second thread was involved. The buyer came in through a call the constructor made itself.

Kotlin runs `init` blocks and property initializers in the order you write them, so the same bug is one misplaced `init` away. Kotlin's null safety doesn't save you either: `manager` is declared non-null, and in the early call it still reads as null. The thread case is in the Try it: a constructor starts a heartbeat thread, which sends a regular "still running" message, and only then looks up the address to send it to. The heartbeat thread is punctual. It reports for work 50 ms before its address exists.

The picture breaks here: on a building site, someone would see the buyer and stop them. In Java, nothing does. The early call looks like any other call.

You might move `register` to the last line of the constructor. In this one-thread case it works, but it's still the wrong fix. The final-field promise starts when the constructor returns, so threads that get the object from the bus get no promise at all. And if someone writes a subclass, its constructor runs after yours, while the bus already holds the object. Instead, keep constructors to setting fields, and wire the object up once it's built, in a static factory method or a `start()` method:

```java
// Fixed: the constructor only sets fields; a factory wires it up
// (the fields and accept() stay as they were)
private BigSaleAlert(long limitCents, Phone manager) {
    this.limitCents = limitCents;
    this.manager = manager;
}

static BigSaleAlert listenOn(EventBus bus, long limitCents, Phone manager) {
    BigSaleAlert alert = new BigSaleAlert(limitCents, manager);   // 1. finish building
    bus.register(alert);                                          // 2. then show it to others
    return alert;
}
```

```kotlin
// Fixed: the constructor only sets properties; a factory wires it up
class BigSaleAlert private constructor(
    private val limitCents: Long,
    private val manager: Phone,
) : Consumer<SaleEvent> {

    override fun accept(e: SaleEvent) {
        if (e.amountCents > limitCents) manager.text("Big sale: $e")
    }

    companion object {
        fun listenOn(bus: EventBus, limitCents: Long, manager: Phone): BigSaleAlert {
            val alert = BigSaleAlert(limitCents, manager)   // 1. finish building
            bus.register(alert)                             // 2. then show it to others
            return alert
        }
    }
}
```

**A constructor sets fields and nothing else. Wire the object up after it's built.**

Every tool in this lesson hands over an object that is already built. None of them helps when several threads ask for an object that doesn't exist yet, and the first one to ask has to build it while the others wait. That's the next lesson's problem."""

ASIDE3 = {
    "title": "What if a framework builds my objects?",
    "body": "If you write web services, a framework often creates your objects for you and passes in what they need. Most frameworks can also call a setup method once the object is fully built. In Spring and in Jakarta EE, two widely used Java frameworks for web services, that's a method marked `@PostConstruct`. Put listener registration, timers and threads there, not in the constructor. The rule is the same; the framework just gives the after-it's-built step a name."
}

L = {
 "id": "jmm-04",
 "title": "Safe publication, final fields and escaping this",
 "minutes": 35,
 "goal": "By the end you can hand an object to other threads so they see it whole, build classes whose final fields survive any race, and keep `this` from escaping a constructor.",
 "opening": OPENING,
 "warmup": {
  "q": "A loader thread runs `registry.current = new RateCard(\"EUR\", fees);`. The field `current` is a plain field, and RateCard's own fields are plain too. A request thread reads `registry.current` and gets a card that isn't null. What can `card.currency()` return?",
  "options": [
   "Always \"EUR\": the constructor finished before the reference was stored",
   "\"EUR\" or null",
   "\"EUR\", or it throws ConcurrentModificationException",
   "null, until the loader thread ends"
  ],
  "answer": 1,
  "why": "Nothing links the loader's writes to the request thread's reads, so they may become visible in any order. The reader can see the reference before the write of the currency, and then it reads the field's starting value, null. The constructor did run first in the loader (option 1), but that says nothing about what another thread sees. The first section shows it happening in a real run."
 },
 "sections": [
  {
   "h": "Handing over an object is a write, and readers can see it half-built",
   "body": S0,
   "figure": {"svg": FIG, "caption": "With no edge, a request thread can see the store to current before the constructor's store, and find a real rate card with a null inside."},
   "refs": [
    {"title": "jcstress sample BasicJMM_08_Finals: plain, opaque and final publication, with recorded results", "url": "https://github.com/openjdk/jcstress/blob/master/jcstress-samples/src/main/java/org/openjdk/jcstress/samples/jmm/basic/BasicJMM_08_Finals.java", "kind": "read"}
   ]
  },
  {
   "h": "Sealing the envelope: four safe ways to publish",
   "body": S1,
   "try": {
    "title": "Sealed or not?",
    "minutes": 3,
    "steps": [
     "For each line, decide whether a request thread is guaranteed to see the whole `RateCard`. Name the seal, or the missing edge.",
     "(a) `static final RateCard DEFAULT = new RateCard(...)`, read by any thread.",
     "(b) `private RateCard current;`, set by the loader, read by request threads.",
     "(c) `private volatile RateCard current;`, set by the loader, read by request threads.",
     "(d) `cards.put(id, card)` on a `ConcurrentHashMap`, and request threads call `cards.get(id)`."
    ],
    "expect": "(a) Sealed: the static initializer runs under the JVM's class-initialization lock. (b) Not sealed: there's no edge, so a reader may see a half-built card, or never see it at all. (c) Sealed: a volatile write, then a volatile read of the same field. (d) Sealed: putting a card into a concurrent map happens-before a `get` that returns it."
   }
  },
  {
   "h": "Final fields arrive whole, even without a seal",
   "body": S2,
   "try": {
    "title": "Find final in the compiled classes",
    "minutes": 4,
    "steps": [
     "Run both demos below once (the Java one, then the Kotlin one), so Gradle compiles them.",
     "`javap` is a JDK tool that prints what's inside a compiled class. Predict first: which fields will say `final`?",
     "From `labs/`, run `javap -p 'jmm/build/classes/java/demo/workbench/jmm/l04/FinalFieldsDemo$Quote.class'`, then the same for `FinalFieldsDemo$MutableQuote.class`.",
     "Run `javap -p jmm/build/classes/kotlin/demo/workbench/jmm/l04/KQuote.class`, then the same for `KMutableQuote.class`."
    ],
    "code": code("FinalFieldsDemo"),
    "expect": "The record and `KQuote` both show `private final java.lang.String scheme;` and `private final long feeCents;`. `MutableQuote` and `KMutableQuote` show the same fields without `final`, and the Kotlin one also has setters. A Kotlin `val` and a Java record component compile to the same thing, a final field, and they get the final-field promise with it."
   }
  },
  {
   "h": "Don't open the house early: keeping this inside the constructor",
   "body": S3,
   "aside": ASIDE3,
   "try": {
    "title": "A thread that starts too early",
    "minutes": 4,
    "steps": [
     "Read `ThisEscapeDemo`. Its constructor starts a heartbeat thread, then looks up the address to send to, which takes about 50 ms.",
     "Predict both lines of output, then run it.",
     "Fix it: move the thread start out of the constructor into a `start()` method, and call `start()` from `main` after construction. Run it again."
    ],
    "code": code("ThisEscapeDemo"),
    "expect": "The first run prints `heartbeat thread sends to: null`, then `constructor finished, endpoint = https://head-office.example.com`. The heartbeat thread ran while the constructor was still looking up the address. In Kotlin, `val endpoint: String` is non-null by its type and still reads as null. After the fix, the heartbeat prints the real address: the field was set before `start()`, and `start()` happens-before everything the new thread does."
   }
  }
 ],
 "compare": {
  "title": "An immutable rate card in Java and Kotlin",
  "java": {"title": "RateCard.java", "src": "public final class RateCard {\n    private final String currency;\n    private final Map<String, Long> feesByScheme;\n\n    public RateCard(String currency, Map<String, Long> feesByScheme) {\n        this.currency = currency;\n        this.feesByScheme = Map.copyOf(feesByScheme);   // our own unmodifiable copy\n    }\n\n    public String currency() { return currency; }\n    public Map<String, Long> feesByScheme() { return feesByScheme; }   // safe to hand out\n}"},
  "kotlin": {"title": "RateCard.kt", "src": "class RateCard(val currency: String, feesByScheme: Map<String, Long>) {\n    // our own copy, behind a read-only type\n    val feesByScheme: Map<String, Long> = feesByScheme.toMap()\n}"},
  "note": "Both classes have final fields and copy the caller's map, so both get the final-field promise. Kotlin says it in three lines, because Kotlin classes are final by default and a `val` compiles to a private final field with a getter. The real difference is the map. Java's `Map.copyOf` returns a map that nobody can change. Kotlin's `Map` is a read-only interface: `toMap()` gives you a private `LinkedHashMap`, and code that casts it to `MutableMap` could still change it. Inside your own code that's usually fine. If the object travels to code you don't control, build the copy with `java.util.Map.copyOf` instead, as Don't share did."
 },
 "worked": {
  "title": "Publish the shop's delivery settings safely",
  "steps": [
   {"say": "The shop charges a delivery fee, and delivery is free for orders above a threshold. A helper thread fetches new settings from head office every minute, and every till thread reads them. Now and then a till charges the new fee with the old threshold, a pair head office never set. Find both problems.",
    "code": "public class DeliverySettingsHolder {\n    private DeliverySettings settings = new DeliverySettings();   // 1. a changeable object in a plain field\n\n    void refresh(HeadOffice office) {                              // the helper thread, every minute\n        Settings s = office.fetch();\n        settings.setFeeCents(s.feeCents());                        // 2. changed in place...\n        settings.setFreeAboveCents(s.freeAboveCents());            //    ...one field at a time\n    }\n\n    public DeliverySettings current() { return settings; }         // 3. every till reads it\n}",
    "lang": "java",
    "alt_lang": "kotlin",
    "alt_code": "class DeliverySettingsHolder {\n    private var settings = DeliverySettings()                      // 1. a changeable object in a plain property\n\n    fun refresh(office: HeadOffice) {                              // the helper thread, every minute\n        val s = office.fetch()\n        settings.feeCents = s.feeCents                             // 2. changed in place...\n        settings.freeAboveCents = s.freeAboveCents                 //    ...one field at a time\n    }\n\n    fun current(): DeliverySettings = settings                     // 3. every till reads it\n}"},
   {"say": "First, the helper changes one shared object in place, field by field, with no lock. A till can read between the two writes and get the new fee next to the old threshold. Second, nothing publishes the settings safely. Their fields are plain, and there's no edge from the helper thread to the tills, so a till may see the writes late or in any order. Even a lock around `refresh` wouldn't help tills that never take it.", "code": "", "lang": ""},
   {"say": "Make the settings immutable, build a whole new object on each refresh, and publish it with one volatile write. Each till then gets one complete version.",
    "code": "public record DeliverySettings(long feeCents, long freeAboveCents) {}   // 1. immutable: final fields, no setters\n\npublic class DeliverySettingsHolder {\n    private volatile DeliverySettings settings = new DeliverySettings(499, 5_000);\n\n    void refresh(HeadOffice office) {\n        Settings s = office.fetch();\n        settings = new DeliverySettings(s.feeCents(), s.freeAboveCents());   // 2. build a new one, 3. publish it\n    }\n\n    public DeliverySettings current() { return settings; }                  // 4. one complete version per read\n}",
    "lang": "java",
    "alt_lang": "kotlin",
    "alt_code": "data class DeliverySettings(val feeCents: Long, val freeAboveCents: Long)   // 1. immutable: vals only\n\nclass DeliverySettingsHolder {\n    @Volatile\n    private var settings = DeliverySettings(499, 5_000)\n\n    fun refresh(office: HeadOffice) {\n        val s = office.fetch()\n        settings = DeliverySettings(s.feeCents, s.freeAboveCents)   // 2. build a new one, 3. publish it\n    }\n\n    fun current(): DeliverySettings = settings                     // 4. one complete version per read\n}"},
   {"say": "Why both changes? The record alone makes each version safe to read through any race, thanks to its final fields, but a till might keep reading an old reference for a long time. The volatile field alone delivers the reference, but a changeable object behind it could still change under a till. An immutable object behind a volatile reference fixes both. One habit completes it: a till calls `current()` once per sale and keeps that version for the whole sale.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Fix an escaping constructor and an unsafe publication",
  "minutes": 13,
  "files": [
   "labs/jmm/src/main/java/workbench/jmm/l04/RateCard.java",
   "labs/jmm/src/main/java/workbench/jmm/l04/RateCardRegistry.java",
   "labs/jmm/src/main/java/workbench/jmm/l04/FraudMonitor.java"
  ],
  "run": "./gradlew :jmm:test --tests 'workbench.jmm.l04.*'",
  "steps": [
   "Meet the classes. `RateCard` holds the card fees for one currency. `RateCardRegistry` holds the current rate card: a loader thread calls `publish`, and request threads call `current()` or wait for the first card in `awaitFirst()`. `FraudMonitor` listens on an `EventBus` and flags any payment over a limit. The bus and `PaymentEvent` are given and need no changes.",
   "Run the tests once. All six fail. The two `FraudMonitor` tests fail with a `NullPointerException` thrown from inside the constructor.",
   "Make `RateCard` immutable: a final class, final fields, and `Map.copyOf` in the constructor. Keep the public constructor and methods.",
   "Publish safely in `RateCardRegistry`. Then ask yourself: once `RateCard` is immutable, why does the waiting reader still need this change?",
   "Fix `FraudMonitor` so the bus can't see the monitor before its constructor has finished. `create` stays the only way to make one.",
   "Run the tests until all six pass, then twice more."
  ],
  "hints": [
   "`Map.copyOf` makes an unmodifiable copy, so `feesByScheme()` can return the field as it is.",
   "Final fields make a RateCard safe to read once a thread has the reference. They do nothing to deliver the reference to a thread that loops on a plain field.",
   "In `FraudMonitor`, the private constructor should only set fields. Build the monitor in `create`, then register it, then return it."
  ],
  "done_when": "All six tests in `SafePublicationTest` pass, three runs in a row."
 },
 "drill": {
  "title": "An immutable fee schedule from memory",
  "minutes": 5,
  "prompt": "Close this page. Write `FeeSchedule` with a currency and a list of fees, immutable and safe to share through any race. Then write a holder that publishes the latest schedule to request threads. Check: what would break if you skipped the copy?",
  "answer": {"lang": "java", "src": "public final class FeeSchedule {              // final: no changeable subclasses\n    private final String currency;            // final fields: safe through a race\n    private final List<Fee> fees;\n\n    public FeeSchedule(String currency, List<Fee> fees) {\n        this.currency = currency;\n        this.fees = List.copyOf(fees);        // copy in: the caller can't change ours\n    }\n\n    public String currency() { return currency; }\n    public List<Fee> fees() { return fees; }  // unmodifiable: safe to hand out\n}\n\npublic final class FeeScheduleHolder {\n    private volatile FeeSchedule current;     // volatile: each new schedule is published safely\n\n    public void replace(FeeSchedule next) { current = next; }\n    public FeeSchedule current() { return current; }\n}\n\n// Without the copy, the caller still holds the list and can change it under every reader.",
             "alt": {"lang": "kotlin", "src": "class FeeSchedule(val currency: String, fees: List<Fee>) {   // final by default\n    val fees: List<Fee> = java.util.List.copyOf(fees)   // copy in: the caller can't change ours\n}\n\nclass FeeScheduleHolder {\n    @Volatile\n    var current: FeeSchedule? = null          // each new schedule is published safely\n        private set\n\n    fun replace(next: FeeSchedule) { current = next }\n}\n\n// Without the copy, the caller still holds the list and can change it under every reader."}}
 },
 "recap": [
  "Publishing an object means storing a reference to it where another thread can find it. Through a plain field, a reader can see the reference before the constructor's writes, or never see it at all.",
  "Safe publication seals the envelope: a static initializer, a volatile field or `AtomicReference`, a final field of a properly built object, or a lock or `java.util.concurrent` hand-over. The writer and the reader must use the same seal.",
  "Final fields are seen as the constructor left them, even through a data race. They don't make the reference itself visible.",
  "An immutable object (final class, final fields, copied inputs, nothing changeable handed out, no escaping `this`) is safe to share however it's published. For data you replace, publish a new immutable object with one volatile write.",
  "`this` escapes when a constructor registers it, starts a thread with it, or hands out a lambda that captures it. Set fields in the constructor, and wire the object up afterwards.",
  "The limit: these tools hand over an object that's already built. Building it on first use, while other threads ask for it too, needs more."
 ],
 "closing": "We started with a letter that arrived with blank pages, because nothing sealed the envelope. We sealed it four ways, glued the important pages in with `final`, and kept the house shut until the builders were done.\n\nNow search your own code for constructors that call `register(this)` or `addListener(this)`, start a thread, or pass `this::` to anything. Each one shows an unfinished object to someone. Then look for shared fields that hold objects and are neither `final` nor `volatile`.\n\nNext, we'll build an object only when the first thread asks for it, like a shop that opens its stockroom for the first customer, and ask why checking twice needs `volatile`.",
 "quiz": [
  {
   "q": "`registry.current` is a plain field. The loader stores a `RateCard` whose fields are all `final`. What can a request thread that reads `registry.current` see?",
   "options": [
    "null, or a RateCard with the right field values; it may also keep seeing null for a long time",
    "A RateCard whose currency is still null",
    "Always the latest RateCard, because its fields are final",
    "A ClassCastException, because the object is half-built"
   ],
   "answer": 0,
   "why": "Final fields promise that whoever sees the reference sees the values the constructor set. They don't deliver the reference, so the reader can see null, an older card, or the new one, but never a half-built one. Option 3 mixes up the two promises: final fields make the pages whole, not the delivery."
  },
  {
   "q": "Which of these publishes a new `RateCard` safely to request threads that call `current()`?",
   "options": [
    "A plain field, with `publish` marked `synchronized` and `current()` not synchronized",
    "A `volatile` field",
    "A `HashMap` field that `publish` puts the card into",
    "A plain field, written after `Thread.sleep(100)`"
   ],
   "answer": 1,
   "why": "The volatile write in `publish` pairs with the volatile read in `current()`. The half-synchronized version gives the reader no edge, because the reader never takes the lock. A plain `HashMap` creates no edge either, and a sleep is not an edge at all."
  },
  {
   "q": "A constructor sets all its final fields and then, as its last line, calls `bus.register(this)`. Is that safe?",
   "options": [
    "Yes, all the fields are already set",
    "Yes, final fields make any publication safe",
    "No: the final-field promise starts when the constructor returns, so threads that get the object from the bus get no such promise, and a subclass constructor hasn't run yet",
    "No, `register` can't accept `this` inside a constructor"
   ],
   "answer": 2,
   "why": "The freeze happens at the end of the constructor, and `this` left before that. It often works in practice, which is why the bug survives review. Build the object first, then register it from a factory method."
  },
  {
   "q": "A final class has `private final List<Fee> fees;`, set with `this.fees = fees;` from the caller's `ArrayList`, and no setters. Is it safe to share between threads?",
   "options": [
    "Yes, the field is final",
    "Yes, as long as it is published through a volatile field",
    "No, because `List` is an interface",
    "No: the caller still holds the `ArrayList` and can change it after the constructor, racing with every reader"
   ],
   "answer": 3,
   "why": "Final freezes the reference, and the list's contents as they were at the end of the constructor. Later changes through the caller's reference are ordinary unprotected writes to an `ArrayList`. Copy it with `List.copyOf` in the constructor."
  },
  {
   "q": "From volatile: what it gives you and what it doesn't: a field is `volatile Map<String, Rule> rules`. A refresher thread calls `rules.put(k, v)` on the existing `HashMap`, and request threads call `rules.get(k)`. Is it safe?",
   "options": [
    "Yes, the field is volatile",
    "No: `put` never writes the volatile field, it changes a HashMap that isn't safe to use from several threads at once",
    "Yes, if the map has fewer than 16 entries",
    "Only on x86"
   ],
   "answer": 1,
   "why": "Volatile covers the reference stored in the field. `put` never writes that field, so there's no edge, and a `HashMap` can corrupt itself when threads use it at the same time. Build a new map and assign it with one volatile write, or use a `ConcurrentHashMap`.",
   "from": "jmm-03"
  }
 ],
 "flashcards": [
  {"front": "An object is published through a plain field. What can a reader that sees the reference find inside it?", "back": "Default values (0, false, null) in its non-final fields, because the reference may become visible before the constructor's writes."},
  {"front": "What do final fields guarantee?", "back": "A thread that sees the reference after the constructor finished sees the final fields, and what they point to, as the constructor left them, even through a data race."},
  {"front": "Do final fields make the reference to the object visible to other threads?", "back": "No. You still need a safe way to publish it, such as a volatile field, for readers to see the reference at all."},
  {"front": "Name a safe way to publish that needs no volatile and no lock.", "back": "A static initializer, such as `static final RateCard DEFAULT = new RateCard(...)`. The JVM runs class initialization under a lock."},
  {"front": "A constructor calls `bus.register(this)`. What's the fix?", "back": "Let the constructor only set fields. Build the object in a static factory method, then register it, then return it."},
  {"front": "What does a Kotlin `val` compile to?", "back": "A private final field (plus a getter). A `var` gives a field that isn't final."},
  {"front": "Is `this.fees = fees;` enough for an immutable class with a list?", "back": "No. Copy it (`List.copyOf(fees)`), or the caller can still change the list under your readers."}
 ],
 "terms": [
  {"term": "Publication", "plain": "Storing a reference to an object where another thread can find it."},
  {"term": "Safe publication", "plain": "Publishing so the reader gets the reference and the object's state together, through a happens-before edge or final fields."},
  {"term": "Partially constructed object", "plain": "An object a thread can see before the constructor's writes are visible to it."},
  {"term": "Data race", "plain": "A write and a read of the same field, in different threads, with no happens-before edge between them."},
  {"term": "Freeze", "plain": "The end of a constructor, after which final fields carry the memory model's special promise."},
  {"term": "Immutable object", "plain": "Final class, final fields, copied inputs, nothing changeable handed out, no escaping this."},
  {"term": "Escaping this", "plain": "A constructor letting other code get a reference to the object before the constructor has finished."},
  {"term": "Defensive copy", "plain": "Copying a changeable input or output so outside code can't change your object through it."}
 ],
 "explain_back": {
  "prompt": "`FraudMonitor` had only final fields, yet the bus's replayed event hit a `NullPointerException` inside it. Explain why in your own words, and why moving `register` to the end of the constructor is not the right fix.",
  "answer": "The constructor handed `this` to the bus before it set its fields, and the bus called `accept` straight away to replay its last event. At that moment `flagged` and `limitCents` still held their default values, null and 0, so `flagged.add` threw. Final fields don't help, because their promise starts when the constructor returns, and the object was used before that. Moving `register` to the last line would make this one-thread case work. But threads that get the monitor from the bus would still get it before its constructor finished, with no final-field promise, and a subclass constructor would run even later. The right fix is to only set fields in the constructor and register the finished object from a factory method."
 },
 "deeper": {
  "minutes": 10,
  "body": "The final-field promise has a few edges worth knowing.\n\nIt covers what the constructor set, and what the final fields point to, as of the freeze. If you change an object that a final field points to after the constructor, those later changes get no promise. That's why \"effectively immutable\" objects, objects nobody changes after publishing although nothing stops them, still need a seal, while truly immutable objects don't.\n\nReflection can break `final`. Reflection is the part of Java that lets code look at and change classes and fields while the program runs. Some frameworks have long used it to write final fields after construction (`Field.setAccessible(true)`, then `set`), and the memory model gives such writes almost no guarantees. JDK 26 starts closing that door with JEP 500, \"Prepare to Make Final Mean Final\". By default it prints a warning when reflection changes a final field, and a later release is planned to make that an error unless you allow it. Libraries that turn objects into bytes and back, and tools that build fake objects for tests, are the usual sources of these warnings.\n\nThe static-initializer seal works because class initialization is itself a careful hand-over. The JVM initializes each class once, under a lock, and any thread that then uses the class is guaranteed to see what the static initializer wrote. The next lesson builds lazy initialization on exactly that.\n\nAleksey Shipilëv's \"Safe Publication and Safe Initialization in Java\" separates the two ideas this lesson combines: safe publication (the seal) and safe initialization (final fields). It also measures what each one costs."
 },
 "sources": [
  {"title": "Java Language Specification, chapter 17 (17.5 final field semantics)", "url": "https://docs.oracle.com/javase/specs/jls/se25/html/jls-17.html"},
  {"title": "Aleksey Shipilëv, Safe Publication and Safe Initialization in Java", "url": "https://shipilev.net/blog/2014/safe-public-construction/"},
  {"title": "jcstress sample BasicJMM_08_Finals", "url": "https://github.com/openjdk/jcstress/blob/master/jcstress-samples/src/main/java/org/openjdk/jcstress/samples/jmm/basic/BasicJMM_08_Finals.java"},
  {"title": "JEP 500: Prepare to Make Final Mean Final", "url": "https://openjdk.org/jeps/500"},
  {"title": "Java Concurrency in Practice, Goetz et al., section 3.5 on safe publication", "url": "https://jcip.net/"}
 ]
}
out = ROOT / "content/lessons/jmm-04.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
