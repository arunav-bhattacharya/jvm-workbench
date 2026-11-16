import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/jmm/src"
P = "java/workbench/jmm/l06"
K = "kotlin/workbench/jmm/l06"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"{lab}/demo/{P}/{name}.java"
kdemo = lambda name: f"{lab}/demo/{K}/{name}.kt"
run = lambda name: f"./gradlew :jmm:demo -Pmain=workbench.jmm.l06.{name}"


def code(name, java_run=None, kotlin_run=None):
    """A Java demo with its Kotlin twin (Foo.kt with a top-level main, class FooKt)."""
    return {"lang": "java", "title": f"{name}.java", "src": read(demo(name)), "run": java_run or run(name), "file": demo(name),
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(kdemo(name)), "run": kotlin_run or run(name + "Kt"), "file": kdemo(name)}}


def rung(y, cls, name, methods, adds):
    return (
        f'<rect class="{cls}" x="50" y="{y}" width="200" height="54" rx="8"/>'
        f'<text class="t" x="150" y="{y + 23}" text-anchor="middle">{name}</text>'
        f'<text class="t-s t-code" x="150" y="{y + 42}" text-anchor="middle">{methods}</text>'
        f'<rect class="box" x="266" y="{y}" width="394" height="54" rx="8"/>'
        f'<text class="t-s" x="463" y="{y + 32}" text-anchor="middle">{adds}</text>'
    )


FIG = (
    '<svg viewBox="0 0 680 300" role="img" aria-label="A ladder of four access modes, weakest at the bottom. '
    'Plain: a normal field, no promise about other threads. Opaque: each access really happens, in one piece, even for long and double. '
    'Acquire and release: writes before a release are seen after the matching acquire. '
    'Volatile: one order of all volatile accesses, which forbids the store-buffering result.">'
    '<text class="t-s t-m" x="26" y="18" text-anchor="middle">stronger</text>'
    '<line class="ln-a" x1="26" y1="282" x2="26" y2="30" marker-end="url(#arr)"/>'
    + rung(26, "box-a", "volatile", "getVolatile, setVolatile", "+ one order of all volatile accesses: no store-buffering 0, 0")
    + rung(94, "box-b", "acquire / release", "getAcquire, setRelease", "+ writes before a release are seen after the acquire")
    + rung(162, "box", "opaque", "getOpaque, setOpaque", "+ each access really happens, in one piece, even long")
    + rung(230, "box-dim", "plain", "get, set", "a normal field: no promise about other threads")
    + '</svg>'
)

OPENING = """A shop sends its parcels through a courier. Most parcels have no label, and the courier handles them however is quickest: it may bundle them, hold some back, or deliver them out of order. A few carry labels, such as "signature required". Each label costs the courier time, so a sensible shop uses the lightest label that keeps the parcel safe.

Java's `volatile`, which makes every read of a field see the latest write, is a label too: the heaviest one, on every read and write of that field. Since JDK 9, Java has also offered lighter labels, one access at a time. The trap is to think they're "volatile, only cheaper". They're weaker, and a test on your laptop can't tell the difference.

The last lesson built every lazy value on volatile's release write and acquire read. In this lesson, we'll meet VarHandles, line up the four labels, and use the middle one to hand data between threads, the paths of work that run side by side in a program. Then we'll see why only jcstress, a tool that runs tests millions of times, can check it. Before we start, make a guess, and keep it in mind."""

S0 = """First, the parcels in Java terms. A thread is one path of work running beside others in the same program, and each read or write of a shared field is a parcel that one thread sends another. The courier is everything in between. It's the JIT, the compiler inside the JVM that turns busy code into machine code and may move or skip accesses. It's also the processor, whose cores, the parts that each run one thread, may hold writes back for a while. The label on one read or write is called its access mode, and it says what the courier must do for that access.

A `volatile` field puts one label on the field itself: every read and every write of it gets the strongest handling, whether it needs it or not. That's usually right, and it's simple. But some code needs less. Picture a one-item mailbox between two threads that hand over millions of payments a second. The producer, the thread that fills the mailbox, only needs its data to arrive with the item for the consumer, the thread that empties it. Yet on x86, the Intel and AMD kind of processor, every volatile write also waits for the core's store buffer to drain. The store buffer, met in Why your loop never stops, is a small queue where a core parks its writes before other cores can see them. Millions of times a second, that wait adds up.

A **VarHandle** puts the label on each access instead. VarHandles came in JDK 9, with JEP 193. (A JEP, or JDK Enhancement Proposal, is the public design document for one JDK feature.) A VarHandle is a typed handle to one field or array element, with one method per label: `get` and `set` (plain), `getOpaque` and `setOpaque`, `getAcquire` and `setRelease`, `getVolatile` and `setVolatile`. It also has atomic updates such as `compareAndSet`, `getAndAdd` and `getAndSet`. Here's one for the lab's `SettlementSlot`, a one-item mailbox whose `item` field holds a payment record:

```java
final class SettlementSlot {
    private static final VarHandle ITEM;              // 1. one handle per field, static final
    static {
        try {
            ITEM = MethodHandles.lookup()              // 2. a lookup that can see the private field
                    .findVarHandle(SettlementSlot.class, "item", Settlement.class);
        } catch (ReflectiveOperationException e) {
            throw new ExceptionInInitializerError(e);
        }
    }

    private Settlement item;                           // 3. a plain field: the label goes on each access

    Settlement peek() {
        return (Settlement) ITEM.getAcquire(this);     // 4. the object first, then cast the result
    }
}
```

```kotlin
class SettlementSlot {
    private var item: Settlement? = null               // 3. a plain field: the label goes on each access

    fun peek(): Settlement? = ITEM.getAcquire(this) as Settlement?   // 4. the object first, then cast the result

    companion object {
        // 1. one handle per field; 2. looked up inside the class, so it can see the private field
        private val ITEM: VarHandle = MethodHandles.lookup()
            .findVarHandle(SettlementSlot::class.java, "item", Settlement::class.java)
    }
}
```

Both versions follow the same four steps. First we look up a handle, once, through `MethodHandles.lookup()`, which can see the class's private fields. We keep it in a `static final` field; in Kotlin, a `private val` in the companion object compiles to exactly that. The field itself stays plain. Every access goes through the handle, which takes the object first and needs a cast on its result.

Three details make this work.

Keep the handle in a `static final` field. The JIT treats a static final as a constant, so it can compile `ITEM.getAcquire(this)` down to one load plus whatever barrier the label needs. A barrier is an instruction that stops the processor from reordering around it.

The access methods are signature-polymorphic: the compiler takes the call's real types from the arguments you pass and the cast on the result, and the VarHandle checks them when the call runs. Kotlin does the same and takes the return type from the `as` cast. Wrong types fail at runtime, with `WrongMethodTypeException` or `ClassCastException`. The compiler, usually so keen to complain early, waves these calls straight through.

The label at the access wins over the field's declaration. The Javadoc says a plain `get` reads a field as plain "even if that field is declared volatile", and it warns that mixing modes on one field needs "extreme care". So keep the field plain, and send every access through the handle.

You don't need all this setup to use the labels. Since JDK 9, `AtomicInteger`, `AtomicLong` and `AtomicReference` have `getPlain`, `getOpaque`, `getAcquire`, `setRelease` and friends. The old `lazySet`, from JDK 6, is `setRelease` under another name. What a VarHandle saves is the extra object: the label works on a plain field of your own class.

Check yourself: a field is declared `volatile`, and a hot loop reads it through `ITEM.get(this)`. Is that read volatile? No. The label at the access wins, so it's a plain read, and the JIT may lift it out of the loop, exactly as in Why your loop never stops.

**A VarHandle access gets the label you name, whatever the field says. Keep the field plain, and always go through the handle.**

We have four labels to choose from. Next, we'll line them up and see what each one promises."""

S1 = """The VarHandle Javadoc defines the modes as a ladder. Each label keeps every promise of the ones below it and adds one more.

Plain (`get`, `set`) is no label at all: an ordinary field access. It's atomic for references and for values of 32 bits or less, which means a read never sees half of one write and half of another. It promises nothing about what other threads see, or when. The JIT may read it once for a whole loop, which was the hang in Why your loop never stops.

Opaque (`getOpaque`, `setOpaque`) means "deliver for sure, in order, in one piece". It's atomic for `long` and `double` too. And it's coherent for that one variable: the JIT must really perform each read and write, in order, so a thread spinning on it eventually sees a new value. It orders nothing else. Writes to other fields can still show up in any order.

Acquire and release (`getAcquire`, `setRelease`) add a one-way order. Nothing before a release write may move after it, and nothing after an acquire read may move before it. When an acquire read sees the value that a release write stored, the reader also sees everything the writer did before the release. In parcel terms, a release label says "deliver everything I sent before this one first", and a receiver who signs for it with an acquire has all of it. It's a happens-before edge, the link that guarantees one thread sees another's writes, built from one variable, as in Happens-before, the rules that matter.

Volatile (`getVolatile`, `setVolatile`, or a `volatile` field) adds a single total order: every thread agrees on one order of all volatile accesses, like registered mail logged in one central book. That's what forbids the store-buffering result, where each thread writes its own variable, then reads the other's and still gets 0.

| Label | What can still go wrong |
|---|---|
| plain | a loop never sees the new value; a `long` arrives in two halves |
| opaque | a reader sees the flag before the data it guards |
| acquire/release | two threads each write, then both read the other's old value |
| volatile | nothing on this list |

The jcstress samples show each step. (jcstress is the OpenJDK tool that runs tiny tests on several threads at once, millions of times, and counts every result.) In `BasicJMM_04_Progress`, a plain spin loop, one that checks a field over and over until it changes, is allowed to hang, and an opaque one is not. In `BasicJMM_06_Causality`, a reader may see the flag without the data when both sides use opaque (0.68% of samples on AArch64, 0 on x86_64), and never with acquire and release. In `BasicJMM_07_Consensus`, acquire and release still let both threads read 0 (6.18% of samples in the recorded run), and volatile forbids it.

Here the parcel picture breaks. Real labels cost the courier more as they get stronger. On x86, plain, opaque, acquire and release accesses all compile to ordinary loads and stores, so those labels mostly hold back the JIT. Only the volatile write adds an instruction, the one that drains the store buffer. The Try it shows what that instruction buys.

**Each label adds one promise. Pick the lightest label whose promise your code needs, and never a lighter one.**

The middle label is the one with a job of its own. Next, we'll use it to hand data from one thread to another."""

S2 = """Release and acquire have one job: handing data from one thread to another. The writer makes plain writes, then one release write. The reader makes one acquire read, and if it sees the new value, it reads the data. Here a day's report goes from one thread to another:

```java
// writer thread
report.total = 1_250_000;                         // 1. plain writes of the data
report.count = 42;
READY.setRelease(report, true);                   // 2. release: the data can't move after this

// reader thread
if ((boolean) READY.getAcquire(report)) {         // 3. acquire: nothing below moves above this
    publish(report.total, report.count);          // 4. sees the data, because it saw the release
}
```

```kotlin
// writer thread
report.total = 1_250_000                          // 1. plain writes of the data
report.count = 42
READY.setRelease(report, true)                    // 2. release: the data can't move after this

// reader thread
if (READY.getAcquire(report) as Boolean) {        // 3. acquire: nothing below moves above this
    publish(report.total, report.count)           // 4. sees the data, because it saw the release
}
```

Picture the writer filling a box and then putting the release label on the lid. The reader checks the lid with an acquire. If the label is there, everything that went into the box is there too.

Four rules keep it correct.

Pair them on the same variable. A release of `ready` and an acquire of `done` give you nothing. For the same reason, a volatile write and a volatile read of two different fields gave you nothing in Happens-before, the rules that matter.

The promise only holds when the acquire reads the released value, or a later one. A reader that still sees `false` learns nothing, which is fine: it tries again later.

Release and acquire don't make a read-modify-write atomic, that is, an update that reads a value and writes a new one based on it, such as `count++`. When several threads may write and only the first should win, use `compareAndSet`, the "update it only if nobody beat me to it" call from Atomics and compare-and-set. The Javadoc says it behaves like volatile: it reads the current value as `getVolatile` and, if that's the expected value, writes as `setVolatile`. Weaker variants exist, such as `compareAndExchangeAcquire` and `weakCompareAndSetRelease`. The `weak` ones may fail even when the value matches, so they belong inside retry loops. The lab's `KillSwitch` uses plain `compareAndSet`.

Don't use them for "I write my flag, then I check yours". That's the store-buffering shape from the last section, and it needs volatile, or better, a lock or one `compareAndSet` on one shared variable.

The Try it runs a one-item mailbox for three seconds, with three kinds of access, and checks every transfer it hands over. Here's a run on an x86 machine:

```text
plain: stuck after 3 handoffs. A spinning thread stopped seeing the slot change.
opaque: 3,303,358 transfers handed over in 3 s, 0 with wrong fields
release: 891,845 transfers handed over in 3 s, 0 with wrong fields
```

The plain slot doesn't crash, and it doesn't complain. Its consumer stands at the mailbox forever, looking at the copy of the slot it read once, because the JIT compiled its spin loop to read the field one time only. The opaque slot kept going, since every opaque read really happens, and on x86 its transfers arrived whole. Nothing promises that, though. Opaque orders nothing but the slot itself, so on ARM a transfer is allowed to arrive with its fields still 0. Only release and acquire promise whole transfers everywhere. The counts also show that a three-second demo is no benchmark: here the opaque run handed over more transfers, and your numbers will differ.

Why bother, when a volatile field does all this? Because the write side is cheaper. On x86, a release write is a plain store, while a volatile write also drains the store buffer. For a queue that hands over millions of messages a second from one producer, that difference shows up when you measure it. That's the whole case for this label.

**Release and acquire hand data from one writer through one variable. Pair them on the same field.**

You've now seen the labels work. The harder questions are when you should use them, and how you would ever know they're right."""

S3 = """Almost never in application code. Prefer, in this order: a `java.util.concurrent` class, such as a `BlockingQueue` for hand-overs or a `ConcurrentHashMap`; then a `volatile` field or an `Atomic` class such as `AtomicLong`; then a lock. Reach for VarHandle labels only when three things are true. You're writing a low-level building block, such as a queue. A measurement shows that the cost of volatile, or of an extra `Atomic` object, matters. And you will test it with jcstress.

That describes the people who write `java.util.concurrent` itself (`FutureTask` and `ConcurrentLinkedQueue` both keep their state behind VarHandles), the authors of fast queue libraries, and almost nobody writing an everyday web service. VarHandles are also the supported way out of `sun.misc.Unsafe`, an internal JDK class that libraries used for years to reach memory directly. JDK 23 deprecated its memory-access methods for removal (JEP 471), and JDK 24 prints a warning the first time code uses them (JEP 498). A library that still uses them is a library you'll be upgrading soon.

The bigger problem is testing. A JUnit test, the kind these labs use, can't prove any of this. Your test ran on one kind of processor, after one JIT warm-up, under one load. A green run says that machine didn't produce the bad result that time. The lab's tests check behavior that is the same on every run once the code is right; they can't catch a missing release on x86.

jcstress, which Testing and debugging concurrent code introduced, is the honest test. You write a `@State` class, two or more `@Actor` methods that run against each other, and an `@Outcome` for each result, marked `ACCEPTABLE`, `ACCEPTABLE_INTERESTING` or `FORBIDDEN`. jcstress runs the actors on fresh state objects many millions of times, in several JVM configurations, and prints how often each result happened. A forbidden result that appears even once fails the test.

Two habits make its results worth having. Read the results table, not just pass or fail: an interesting result at 0.01% is a real bug in a busy program. And run it on ARM if you can, on an Apple Silicon laptop or an ARM cloud server. x86 never lets one store pass another, so many ordering bugs simply can't show there. The Try it puts your lab slot under jcstress and shows exactly that.

**In application code, use java.util.concurrent, volatile, atomics and locks. Leave the lighter labels to building blocks that jcstress has tested.**

The labels are the bottom of the stack: below them there's only the hardware. From here, the course climbs back up, to tools that run your tasks on threads you never create yourself."""

L = {
 "id": "jmm-06",
 "title": "VarHandles and memory ordering modes",
 "minutes": 35,
 "goal": "By the end you can name the four access modes and what each one promises, write a release/acquire hand-over and a compareAndSet flag with a VarHandle, and explain why application code almost never needs them and why only jcstress can test them.",
 "opening": OPENING,
 "warmup": {
  "q": "Two threads run the store-buffering test from Why your loop never stops, through a VarHandle. Thread A: `X.setRelease(p, 1); r1 = (int) Y.getAcquire(p);`. Thread B: `Y.setRelease(p, 1); r2 = (int) X.getAcquire(p);`. Can both `r1` and `r2` end up 0?",
  "options": [
   "No: release plus acquire is everything volatile does",
   "Yes, even on x86",
   "Only on ARM, because x86 never reorders",
   "Only if the fields are long or double"
  ],
  "answer": 1,
  "why": "Release keeps the earlier accesses before the write, and acquire keeps the later accesses after the read. Neither stops a thread's read from overtaking its own earlier write, and that's exactly what an x86 store buffer does: each write waits in its own core while the read goes ahead. Volatile adds one order of all volatile accesses that every thread agrees on, and that forbids both reading 0. The jcstress sample BasicJMM_07_Consensus recorded both reading 0 in 6.18% of samples with acquire and release, and never with volatile."
 },
 "sections": [
  {
   "h": "A VarHandle puts the memory mode on each access, not on the field",
   "body": S0,
   "refs": [
    {"title": "JEP 193: Variable Handles", "url": "https://openjdk.org/jeps/193", "kind": "read"},
    {"title": "VarHandle (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/invoke/VarHandle.html", "kind": "docs"}
   ]
  },
  {
   "h": "Four access modes, from weakest to strongest: plain, opaque, acquire/release, volatile",
   "body": S1,
   "figure": {"svg": FIG, "caption": "Each mode keeps every promise of the modes below it and adds one more."},
   "try": {
    "title": "Store buffering with four labels",
    "minutes": 4,
    "steps": [
     "Read `ModesDemo`. It runs the store-buffering test from Why your loop never stops once per access mode, 262,144 trials each: thread A writes `x` and reads `y`, thread B writes `y` and reads `x`.",
     "Predict, for each mode, whether any trial ends with both threads reading 0.",
     "Run it (Java or Kotlin). Then explain the opaque line: opaque stops the JIT from reordering, so who is reordering?"
    ],
    "code": code("ModesDemo"),
    "expect": "Plain, opaque and release/acquire all show trials where both threads read 0: tens of thousands, between about 66,000 and 126,000 of 262,144 in runs here, and different every time. Volatile shows 0 on every run. Opaque and release/acquire keep the JIT honest, so what you see is the processor's store buffer: each thread's write is still parked in its own core while it reads the other field. Only the volatile write makes HotSpot, the JVM most people run, drain the buffer before the next read."
   },
   "refs": [
    {"title": "jcstress sample BasicJMM_07_Consensus: plain, volatile and acquire/release Dekker", "url": "https://github.com/openjdk/jcstress/blob/master/jcstress-samples/src/main/java/org/openjdk/jcstress/samples/jmm/basic/BasicJMM_07_Consensus.java", "kind": "read"},
    {"title": "jcstress sample BasicJMM_06_Causality: plain, opaque, volatile and acquire/release", "url": "https://github.com/openjdk/jcstress/blob/master/jcstress-samples/src/main/java/org/openjdk/jcstress/samples/jmm/basic/BasicJMM_06_Causality.java", "kind": "read"}
   ]
  },
  {
   "h": "Handing data to another thread with release and acquire",
   "body": S2,
   "try": {
    "title": "Hand over transfers three ways",
    "minutes": 5,
    "steps": [
     "Read `HandoffDemo`. One producer hands bank transfers to one consumer through a one-item slot, for three seconds. There are three slots: ordinary field access, opaque, and release/acquire.",
     "Predict for each one: does it keep going, and does the consumer ever see a transfer with the wrong fields?",
     "Run it three times: with `-Pargs=plain` as below, then with `-Pargs=opaque`, then with no argument (release/acquire). Try the Kotlin twin too."
    ],
    "code": code("HandoffDemo", java_run=run("HandoffDemo") + " -Pargs=plain", kotlin_run=run("HandoffDemoKt") + " -Pargs=plain"),
    "expect": "Release/acquire hands over around a million transfers with 0 wrong. Opaque usually does the same on x86, but nothing orders the transfer's fields before the slot write, so on ARM it is allowed to deliver a transfer whose fields are still 0. The plain slot usually gets stuck within a second: once the JIT compiles a spin loop, it may read the field once and never again. In runs here, the Java version got stuck after 3 hand-overs and the Kotlin version after 32. A plain run that keeps going is allowed too, which is the point: a plain run that works tells you nothing."
   }
  },
  {
   "h": "When you need access modes, and why only jcstress can test them",
   "body": S3,
   "try": {
    "title": "Put your slot under jcstress",
    "minutes": 6,
    "steps": [
     "Optional, and it needs Maven (a Java build tool, like the Gradle that runs these labs) and network access. Finish the lab first. Then create a jcstress project with the template command from the jcstress README:\n\n```bash\nmvn archetype:generate -DinteractiveMode=false -DarchetypeGroupId=org.openjdk.jcstress -DarchetypeArtifactId=jcstress-java-test-archetype -DgroupId=org.sample -DartifactId=test -Dversion=1.0\n```",
     "In `test/pom.xml`, change `<javac.target>1.8</javac.target>` to `21`. The template targets Java 8, and VarHandle needs JDK 9 or later.",
     "Copy `Settlement.java` and your `SettlementSlot.java` into `test/src/main/java/org/sample/` and change their package line to `package org.sample;`. Replace `ConcurrencyTest.java` with the test below.",
     "Run `mvn clean verify`, then `java -jar target/jcstress.jar -t SlotHandoffTest -m quick -v`. Read the results table.",
     "Change your slot's `setRelease` and `getAcquire` to `setOpaque` and `getOpaque`. Predict, rebuild and run again."
    ],
    "code": {"lang": "java", "solo": True, "title": "SlotHandoffTest.java", "src": "package org.sample;\n\nimport org.openjdk.jcstress.annotations.*;\nimport org.openjdk.jcstress.infra.results.J_Result;\n\nimport static org.openjdk.jcstress.annotations.Expect.*;\n\n@JCStressTest\n@Outcome(id = \"-1\",   expect = ACCEPTABLE, desc = \"The slot was still empty\")\n@Outcome(id = \"8400\", expect = ACCEPTABLE, desc = \"Saw the whole settlement\")\n@Outcome(id = \"0\",    expect = FORBIDDEN,  desc = \"Saw the settlement but not its amount\")\n@State\npublic class SlotHandoffTest {\n    final SettlementSlot slot = new SettlementSlot();\n\n    @Actor\n    public void producer() {\n        Settlement s = new Settlement();\n        s.amountCents = 8400;                 // a plain write...\n        slot.offer(s);                        // ...then the release\n    }\n\n    @Actor\n    public void consumer(J_Result r) {\n        Settlement s = slot.poll();           // the acquire\n        r.r1 = (s == null) ? -1 : s.amountCents;\n    }\n}\n", "run": "java -jar target/jcstress.jar -t SlotHandoffTest -m quick -v"},
    "expect": "jcstress prints a table like the ones in its samples. On an x86_64 machine in quick mode, a run here showed `-1` (empty) in about 65% of 199 million samples, `8400` in the other 35%, and `0` (forbidden) in none: the test is OK. The all-opaque version also showed 0 forbidden samples on x86_64, in about 133 million. That doesn't make it correct. x86 never lets one store pass another; ARM does, and there the opaque slot is allowed to fail. jcstress is the tool that would show it, if you run it on the right machine. jcstress tests are written in Java, so this step has no Kotlin twin."
   },
   "refs": [
    {"title": "jcstress: the OpenJDK concurrency stress tests (README and samples)", "url": "https://github.com/openjdk/jcstress", "kind": "read"},
    {"title": "JEP 498: Warn upon Use of Memory-Access Methods in sun.misc.Unsafe", "url": "https://openjdk.org/jeps/498", "kind": "read"}
   ]
  }
 ],
 "compare": {
  "title": "The same release/acquire hand-over with AtomicReference, in Java and Kotlin",
  "java": {"title": "LatestBatch.java", "src": "final class LatestBatch {\n    private final AtomicReference<Batch> latest = new AtomicReference<>();\n\n    // writer: build the batch with plain writes, then release it\n    void publish(Batch b) { latest.setRelease(b); }\n\n    // readers: an acquire read sees the batch's fields as the writer left them\n    Batch current() { return latest.getAcquire(); }\n\n    // several writers racing to set the first batch: compareAndSet, volatile semantics\n    boolean publishFirst(Batch b) { return latest.compareAndSet(null, b); }\n}"},
  "kotlin": {"title": "LatestBatch.kt", "src": "class LatestBatch {\n    private val latest = AtomicReference<Batch?>(null)\n\n    // writer: build the batch with plain writes, then release it\n    fun publish(b: Batch) = latest.setRelease(b)\n\n    // readers: an acquire read sees the batch's fields as the writer left them\n    fun current(): Batch? = latest.getAcquire()\n\n    // several writers racing to set the first batch: compareAndSet, volatile semantics\n    fun publishFirst(b: Batch): Boolean = latest.compareAndSet(null, b)\n}"},
  "note": "A batch here is any group of records that one thread builds and others read. Both versions are the same three calls on the same JDK class. Kotlin has no syntax of its own for memory modes on the JVM: `@Volatile` gives you volatile, and for every other mode you call the same JDK classes as Java. `AtomicReference` and friends have had `getAcquire`, `setRelease`, `getOpaque` and `getPlain` since JDK 9, so this is the readable way to use the modes: no lookup, no casts, one extra object per field. VarHandle calls also work from Kotlin, because the Kotlin compiler (2.4 in these labs) treats VarHandle methods as signature-polymorphic and takes the return type from the `as` cast. Use a VarHandle only when that extra object per instance matters, as it does for the nodes of a queue with millions of entries."
 },
 "worked": {
  "title": "Choose the lightest label for a worker's payment counter, then decide whether it's worth it",
  "steps": [
   {"say": "A worker thread counts the payments it has processed. A dashboard thread reads the count every 15 seconds to draw a chart. Right now the count is an `AtomicLong`. Before reading on, list what the reader actually needs.",
    "code": "final class WorkerStats {\n    private final AtomicLong processed = new AtomicLong();\n\n    void onPayment() { processed.incrementAndGet(); }   // the worker thread, once per payment\n    long processed() { return processed.get(); }         // the dashboard thread, every 15 s\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "class WorkerStats {\n    private val processed = AtomicLong()\n\n    fun onPayment() { processed.incrementAndGet() }    // the worker thread, once per payment\n    fun processed(): Long = processed.get()            // the dashboard thread, every 15 s\n}"},
   {"say": "Only one thread writes, so the increment doesn't have to be one atomic read-modify-write; that was the single-writer case in volatile: what it gives you and what it doesn't. The reader needs a `long` that never arrives in two halves and that moves on eventually. It reads no other data based on the count, so it needs no acquire. That's exactly opaque: atomic for 64 bits, really performed, eventually visible.", "code": "", "lang": ""},
   {"say": "The lightest correct version uses the modes `AtomicLong` already has, with a label on each step.",
    "code": "final class WorkerStats {\n    private final AtomicLong processed = new AtomicLong();\n\n    void onPayment() {\n        long next = processed.getPlain() + 1;      // 1. the only writer can read its own value plainly\n        processed.setOpaque(next);                 // 2. opaque: in one piece, and eventually visible\n    }\n\n    long processed() {\n        return processed.getOpaque();              // 3. a recent value, in one piece; orders nothing else\n    }\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "class WorkerStats {\n    private val processed = AtomicLong()\n\n    fun onPayment() {\n        val next = processed.getPlain() + 1        // 1. the only writer can read its own value plainly\n        processed.setOpaque(next)                  // 2. opaque: in one piece, and eventually visible\n    }\n\n    fun processed(): Long = processed.getOpaque()  // 3. a recent value, in one piece; orders nothing else\n}"},
   {"say": "Now decide. On x86 this swaps one atomic processor instruction per payment for a plain store. At 5,000 payments a second you will never see the difference; in a loop doing tens of millions a second, you might. The price is a rule nobody can see in the code: the moment a second thread calls `onPayment()`, counts are quietly lost. Keep `incrementAndGet()` until a measurement points at it, and if many threads count, use `LongAdder` instead.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "A payment slot and a kill switch with acquire and release",
  "minutes": 14,
  "files": [
   "labs/jmm/src/main/java/workbench/jmm/l06/SettlementSlot.java",
   "labs/jmm/src/main/java/workbench/jmm/l06/KillSwitch.java"
  ],
  "run": "./gradlew :jmm:test --tests 'workbench.jmm.l06.*'",
  "steps": [
   "Meet the classes. `Settlement` is a payment record with an id, an amount and a currency, in plain fields; it's given and needs no changes. `SettlementSlot` is a one-item mailbox between one producer thread and one consumer thread. `KillSwitch` is a one-way switch that stops new card payments: any thread may trip it, and only the first reason counts.",
   "Run the tests once. All seven fail: the TODOs throw, and `KillSwitch` has no VarHandle yet.",
   "Write `SettlementSlot.offer` and `poll` with the given `ITEM` handle: an acquire read to look at the slot, and a release write to fill it or empty it.",
   "In `KillSwitch`, add a `private static final VarHandle` for the `reason` field, the same way `SettlementSlot` does.",
   "Write `trip` with `compareAndSet`, and `isTripped` and `reason` with acquire reads.",
   "Run the tests until all seven pass, then twice more. Then ask yourself which of these tests would still pass on x86 if `offer` used `setOpaque`, and what that means."
  ],
  "hints": [
   "VarHandle methods take the object first and need a cast on the result: `(Settlement) ITEM.getAcquire(this)`, `ITEM.setRelease(this, s)`.",
   "Why does `offer` check the slot with an acquire read and not a plain one? A plain read in the producer's spin loop may be read once and never again. The acquire also pairs with the consumer's release of null.",
   "`REASON.compareAndSet(this, null, why)` returns true only for the caller that found null. It behaves like a volatile read and write, so a later acquire read of the reason sees the winner's string."
  ],
  "done_when": "All seven tests in `VarHandleModesTest` pass, three runs in a row."
 },
 "drill": {
  "title": "A release/acquire hand-over from memory",
  "minutes": 5,
  "prompt": "Close this page. Write `ReportBox`: plain fields `total` and `count`, a plain `ready` flag reached only through a VarHandle, a writer method `publish(total, count)` and a reader method `tryRead()` that returns null until the report is ready. Number the four steps. Then compare. Did you pair the release and the acquire on the same field?",
  "answer": {"lang": "java", "src": "final class ReportBox {\n    private static final VarHandle READY;\n    static {\n        try {\n            READY = MethodHandles.lookup().findVarHandle(ReportBox.class, \"ready\", boolean.class);\n        } catch (ReflectiveOperationException e) {\n            throw new ExceptionInInitializerError(e);\n        }\n    }\n\n    private long total;          // plain: carried by the release below\n    private int count;\n    private boolean ready;       // plain field, reached only through READY\n\n    void publish(long total, int count) {      // one writer, once\n        this.total = total;                     // 1. plain writes of the data\n        this.count = count;\n        READY.setRelease(this, true);           // 2. release: the data can't move after this\n    }\n\n    String tryRead() {\n        if (!(boolean) READY.getAcquire(this)) return null;   // 3. acquire\n        return count + \" payments, \" + total + \" cents\";       // 4. sees the data\n    }\n}",
             "alt": {"lang": "kotlin", "src": "class ReportBox {\n    private var total = 0L       // plain: carried by the release below\n    private var count = 0\n    private var ready = false    // plain field, reached only through READY\n\n    fun publish(total: Long, count: Int) {      // one writer, once\n        this.total = total                      // 1. plain writes of the data\n        this.count = count\n        READY.setRelease(this, true)            // 2. release: the data can't move after this\n    }\n\n    fun tryRead(): String? {\n        if (!(READY.getAcquire(this) as Boolean)) return null   // 3. acquire\n        return \"$count payments, $total cents\"                   // 4. sees the data\n    }\n\n    companion object {\n        private val READY: VarHandle = MethodHandles.lookup()\n            .findVarHandle(ReportBox::class.java, \"ready\", Boolean::class.javaPrimitiveType)\n    }\n}"}}
 },
 "recap": [
  "A VarHandle (JDK 9, JEP 193) is a static final handle to a plain field, and each call picks its own access mode.",
  "The modes form a ladder: plain (no promise), opaque (each access happens, in one piece, eventually visible), acquire/release (data written before a release is seen after the matching acquire), volatile (plus one total order).",
  "Release and acquire hand data from one writer through one variable. They don't forbid the store-buffering result; only volatile does.",
  "`compareAndSet` behaves like a volatile read and write, and it is the tool when several threads race to write first.",
  "In application code, prefer `java.util.concurrent` classes, then volatile or the `Atomic` classes (which offer the same modes), then locks. VarHandles are for building blocks, after a measurement asks for them.",
  "The limit: no ordinary test can show that the lighter labels are enough. Only jcstress tests ordering honestly, and an x86 run can't show bugs that ARM allows."
 ],
 "closing": "We started with parcel labels, and the rule to use the lightest one that keeps the parcel safe. Plain is no label, opaque says deliver for sure, release and acquire keep a box's contents with its lid, and volatile logs everything in one book. We used the middle label to hand payments between threads, and saw why a green test on x86 proves little.\n\nNow search your own code for `lazySet`, `setRelease`, `getOpaque` or `VarHandle`. Each one needs a comment that says why the lighter label is enough, and a jcstress test.\n\nThat ends this track. Next, we'll stop creating threads by hand: why do programs keep a pool of threads, and how do you shut one down without losing work?",
 "quiz": [
  {
   "q": "When the program shuts down, one thread sets a flag, once. A busy loop on another thread checks the flag and only needs to stop eventually; the flag guards no other data. What is the weakest mode that is guaranteed to work?",
   "options": [
    "Plain",
    "Opaque",
    "Acquire/release",
    "Volatile"
   ],
   "answer": 1,
   "why": "Opaque guarantees that each read really happens, so the loop eventually sees the write (jcstress BasicJMM_04 forbids a stuck opaque spin). Plain may be read once for the whole loop. Acquire/release and volatile also work, but promise more than this loop needs. In application code you'd still write volatile, because it's one keyword and costs nothing extra on an x86 read."
  },
  {
   "q": "Writer: `report.total = t; READY.setRelease(this, true);`. Reader: `if ((boolean) READY.getOpaque(this)) use(report.total);`. What can the reader see?",
   "options": [
    "The flag as true, but an old `total`: a release only helps a reader that acquires",
    "Always the new total, because the writer used release",
    "A WrongMethodTypeException, because the modes don't match",
    "Never the flag as true, because opaque reads can't see release writes"
   ],
   "answer": 0,
   "why": "The ordering is a pair: release on the writer's side, acquire on the reader's. An opaque read does see the flag eventually, but nothing stops the reader's read of `total` from happening before it. Modes may be mixed without an exception (option 3), and opaque reads do see the value (option 4)."
  },
  {
   "q": "Two worker threads decide which of them runs the nightly report: each does `MINE.setRelease(this, true)`, then reads the other's flag with `getAcquire`, and runs the report if it reads false. What's wrong?",
   "options": [
    "Nothing: release/acquire orders the write before the read",
    "It only fails on ARM",
    "It throws, because each VarHandle may only be used by one thread",
    "Both workers can read false and both run the report, even on x86; this shape needs volatile, or better, one compareAndSet or a lock"
   ],
   "answer": 3,
   "why": "This is store buffering. Release keeps earlier accesses before the write, but it doesn't stop the later read of a different variable from passing it, and an x86 store buffer does exactly that. Volatile forbids it through its single total order. Simpler still: let both workers try one `compareAndSet` on one shared variable, or take the same lock."
  },
  {
   "q": "Where do VarHandle access modes belong?",
   "options": [
    "On every busy volatile field in a web service",
    "Instead of synchronized in code that handles requests",
    "In low-level building blocks like queues, after a measurement shows the cost, with jcstress tests",
    "Nowhere: they were deprecated along with sun.misc.Unsafe"
   ],
   "answer": 2,
   "why": "VarHandles are the supported replacement for Unsafe, not deprecated with it (option 4). They only pay off in code that hands over millions of values a second, and they need jcstress because ordinary tests can't see reorderings. Code that handles requests gets nothing from them that volatile, an Atomic class or a lock doesn't give it more clearly."
  },
  {
   "q": "From volatile: what it gives you and what it doesn't: many threads run `balance += amount` on a `volatile long balance`. Someone suggests `BALANCE.getAndAdd(this, amount)` through a VarHandle instead. Does that fix it?",
   "options": [
    "No, a VarHandle has the same problem as volatile",
    "Yes: getAndAdd is one atomic read-modify-write, like AtomicLong.getAndAdd",
    "Only if a setRelease follows it",
    "Only on 64-bit JVMs"
   ],
   "answer": 1,
   "why": "Volatile makes each read and each write visible, but `+=` is still a read and a write with a gap between them, so updates get lost. `getAndAdd` is a single atomic update that behaves like volatile. In application code, an `AtomicLong` or a `LongAdder` says the same thing more plainly.",
   "from": "jmm-03"
  }
 ],
 "flashcards": [
  {"front": "What does a VarHandle let you choose that a volatile field doesn't?", "back": "The access mode of each read and write (plain, opaque, acquire/release, volatile) on a plain field, plus atomic updates such as compareAndSet."},
  {"front": "What does opaque mode add over plain?", "back": "Each access really happens, in one piece and in order for that variable, so a spinning reader eventually sees a new value. It orders no other variables."},
  {"front": "A release write and an acquire read of the same variable: what does the reader get?", "back": "If its acquire read sees the released value, it also sees every write the writer made before the release."},
  {"front": "What does volatile add on top of acquire/release?", "back": "One total order of all volatile accesses. That forbids the store-buffering result where two threads both read the other's variable as 0."},
  {"front": "Which access mode does `VarHandle.compareAndSet` behave like?", "back": "Volatile: it reads the current value as getVolatile and, on success, writes as setVolatile."},
  {"front": "Why keep a VarHandle in a `static final` field?", "back": "The JIT treats a static final as a constant, so each call compiles down to a load or store plus the barrier its mode needs."},
  {"front": "Why can't a passing JUnit test show that release/acquire code is correct?", "back": "It only shows one machine didn't produce a bad result that time. jcstress runs the actors millions of times and fails on any forbidden result; x86 can't show many ARM bugs."}
 ],
 "terms": [
  {"term": "VarHandle", "plain": "A typed handle to a field or array element whose methods read and write it in a chosen access mode (JDK 9)."},
  {"term": "Access mode", "plain": "The memory rules for one read or write: plain, opaque, acquire/release or volatile. This lesson calls it the label."},
  {"term": "Opaque", "plain": "A mode where each access really happens, in one piece and in order for that variable, with no ordering of other variables."},
  {"term": "Acquire and release", "plain": "A paired mode: writes before the release are visible to a thread whose acquire read sees the released value."},
  {"term": "Signature-polymorphic method", "plain": "A method whose real signature comes from the argument types and the result cast at each call, like VarHandle.get."},
  {"term": "Store buffering", "plain": "Each thread writes one variable, then reads the other's; both may read the old value unless the accesses are volatile."},
  {"term": "jcstress", "plain": "The OpenJDK tool that runs concurrent actors millions of times and checks every result against acceptable and forbidden ones."}
 ],
 "explain_back": {
  "prompt": "A teammate wants to replace every `volatile` field in the shop's program with VarHandle acquire/release \"because it's faster\". Explain what they would gain, what they would risk, and what you'd do instead.",
  "answer": "On x86 the reads gain nothing, because a volatile read already compiles to an ordinary load. Only the writes get cheaper, since a release store skips the instruction that drains the store buffer. In a program that writes these fields a few thousand times a second, that saving is invisible. The risk is real: release/acquire is weaker than volatile. It's enough for one writer handing data through one variable. But code that relies on the single total order would break, like two flags where each thread writes its own and reads the other's, and our x86 tests might never show it. On top of that, every field gets a lookup, casts and a rule that every access must go through the handle. I'd keep volatile and the Atomic classes, and only consider lighter modes for one busy path that a measurement points at, with a jcstress test, ideally run on ARM too."
 },
 "deeper": {
  "minutes": 10,
  "body": "The VarHandle Javadoc maps the modes onto the memory model of C and C++, which helps when you read papers or C++ and Rust code: volatile is compatible with `memory_order_seq_cst`, acquire with `memory_order_acquire`, and release with `memory_order_release`. There are also static fence methods, `VarHandle.fullFence()`, `acquireFence()` and `releaseFence()`, documented as the matching `atomic_thread_fence` calls, plus `loadLoadFence()` and `storeStoreFence()`. A fence orders a thread's accesses around one point in the code, without tying the order to one variable. Fences are even easier to misuse than modes. The jcstress samples `AdvancedJMM_14_SynchronizedAreNotFences` and `AdvancedJMM_15_VolatilesAreNotFences` show that synchronized blocks and volatile accesses don't work as fences either. Their promises hold only between threads that take the same lock, or when a volatile read actually sees the volatile write; you can't use them as free-standing barriers.\n\nVarHandles aren't only for fields. `MethodHandles.arrayElementVarHandle(String[].class)` gives you the modes on array elements, which a `volatile` array never could, because volatile there applies only to the reference to the array. `MethodHandles.byteArrayViewVarHandle` reads and writes an `int` or a `long` inside a `byte[]`, with a chosen byte order and a chosen mode.\n\nIf you want the model behind the modes in one sitting, Doug Lea's \"Using JDK 9 Memory Order Modes\" is the short guide, by the lead author of `java.util.concurrent`. Aleksey Shipilëv's \"Java Memory Model Pragmatics\" is the long version."
 },
 "sources": [
  {"title": "VarHandle (Java SE 25 API): access modes and memory ordering", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/invoke/VarHandle.html"},
  {"title": "JEP 193: Variable Handles", "url": "https://openjdk.org/jeps/193"},
  {"title": "jcstress sample BasicJMM_07_Consensus", "url": "https://github.com/openjdk/jcstress/blob/master/jcstress-samples/src/main/java/org/openjdk/jcstress/samples/jmm/basic/BasicJMM_07_Consensus.java"},
  {"title": "jcstress: the OpenJDK concurrency stress harness", "url": "https://github.com/openjdk/jcstress"},
  {"title": "Doug Lea, Using JDK 9 Memory Order Modes", "url": "https://gee.cs.oswego.edu/dl/html/j9mm.html"}
 ]
}
out = ROOT / "content/lessons/jmm-06.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
