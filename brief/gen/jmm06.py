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
    'Plain: a normal field, no promise about other threads. Opaque: each access really happens, atomic for long and double. '
    'Acquire and release: writes before a release are seen after the matching acquire. '
    'Volatile: one order of all volatile accesses, which forbids the store-buffering result.">'
    '<text class="t-s t-m" x="26" y="18" text-anchor="middle">stronger</text>'
    '<line class="ln-a" x1="26" y1="282" x2="26" y2="30" marker-end="url(#arr)"/>'
    + rung(26, "box-a", "volatile", "getVolatile, setVolatile", "+ one order of all volatile accesses: no store-buffering 0, 0")
    + rung(94, "box-b", "acquire / release", "getAcquire, setRelease", "+ writes before a release are seen after the acquire")
    + rung(162, "box", "opaque", "getOpaque, setOpaque", "+ each access really happens; atomic for long and double")
    + rung(230, "box-dim", "plain", "get, set", "a normal field: no promise about other threads")
    + '</svg>'
)

S1 = """`volatile` puts the memory rules on the field: every read and write of it is a volatile access. A **VarHandle** puts them on each access instead. VarHandles came in JDK 9 with JEP 193. A VarHandle is a typed handle to one field or array element, with one method per mode: `get` and `set` (plain), `getOpaque` and `setOpaque`, `getAcquire` and `setRelease`, `getVolatile` and `setVolatile`. It also has atomic updates such as `compareAndSet`, `getAndAdd` and `getAndSet`.

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

    private Settlement item;                           // 3. a plain field: the mode goes on each access

    Settlement peek() {
        return (Settlement) ITEM.getAcquire(this);     // 4. receiver first, cast the result
    }
}
```

```kotlin
class SettlementSlot {
    private var item: Settlement? = null               // 3. a plain field: the mode goes on each access

    fun peek(): Settlement? = ITEM.getAcquire(this) as Settlement?   // 4. receiver first, cast the result

    companion object {
        // 1. one handle per field; 2. looked up inside the class, so it can see the private field
        private val ITEM: VarHandle = MethodHandles.lookup()
            .findVarHandle(SettlementSlot::class.java, "item", Settlement::class.java)
    }
}
```

Three details make this work.

Keep the handle in a `static final` field. The JIT treats a static final as a constant, so it can compile `ITEM.getAcquire(this)` down to one load plus whatever barrier the mode needs. In Kotlin, a `private val` in the companion object compiles to exactly that field.

The access methods are signature-polymorphic. The compiler records the argument types and the cast on the result as the call's real signature, and the VarHandle checks them when the call runs. Kotlin 2 does the same: the `as` cast sets the return type. Types that can't be converted fail at runtime, with `WrongMethodTypeException` or `ClassCastException`, not at compile time.

The mode at the access wins over the declaration. The Javadoc says a plain `get` reads a field as plain \"even if that field is declared volatile\", and warns that mixing modes on one field needs \"extreme care\". So keep the field plain, and send every access through the handle.

You don't need the boilerplate to use the modes. Since JDK 9, `AtomicInteger`, `AtomicLong` and `AtomicReference` have `getPlain`, `getOpaque`, `getAcquire`, `setRelease` and friends. The old `lazySet` (JDK 6) is `setRelease` under another name. What a VarHandle saves is the extra object: the mode works on a plain field of your own class."""

S2 = """The VarHandle Javadoc defines the modes as a ladder. Each one keeps everything below it and adds one promise.

Plain mode (`get`, `set`) is an ordinary field access. It's atomic for references and for values of 32 bits or less, and it promises nothing about what other threads see, or when. The JIT may read it once for a whole loop. That was the hang in lesson 1 of this track.

Opaque mode (`getOpaque`, `setOpaque`) adds two things. It's atomic for `long` and `double` too. And it's coherent for that one variable: the JIT must really perform each read and write, in order, so a thread spinning on it eventually sees a new value. It orders nothing else. Other fields can still appear in any order.

Acquire and release (`getAcquire`, `setRelease`) add one-way ordering. Nothing before a release write may move after it. Nothing after an acquire read may move before it. When an acquire read sees the value that a release write stored, the reader also sees everything the writer did before the release. That's the happens-before handoff from lesson 2 of this track, built from one variable.

Volatile mode (`getVolatile`, `setVolatile`, or a `volatile` field) adds a single total order: all threads agree on one order of all volatile accesses. That's what forbids the store-buffering result, where each thread writes its own variable and then reads the other's as 0.

| Mode | What can still go wrong |
|---|---|
| plain | a loop never sees the new value; a `long` tears |
| opaque | a reader sees the flag before the data it guards |
| acquire/release | two threads each write, then both read the other's old value |
| volatile | nothing on this list |

The jcstress samples show each step. In `BasicJMM_04_Progress`, a plain spin loop is allowed to hang and an opaque one is not. In `BasicJMM_06_Causality`, a reader may see the flag without the data with opaque accesses (0.68% of samples on AArch64, 0 on x86_64), and never with release/acquire. In `BasicJMM_07_Consensus`, acquire/release still lets both threads read 0 (6.18% in the recorded run), and volatile forbids it.

On x86, plain, opaque, acquire and release accesses all compile to ordinary loads and stores; the modes mostly restrain the JIT. Only the volatile write adds an instruction that drains the store buffer. The Try it measures what that buys."""

S3 = """Release/acquire has one job: handing over data from one thread to another. The writer does plain writes, then one release write. The reader does one acquire read, and if it sees the new value, it reads the data.

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

Four rules keep it correct.

Pair them on the same variable. A release of `ready` and an acquire of `done` give you nothing, just as a volatile write and a volatile read of two different fields gave you nothing in lesson 2 of this track.

The promise only holds when the acquire reads the released value, or a later one. A reader that still sees `false` learns nothing, which is fine: it tries again later.

Release/acquire doesn't make read-modify-write atomic. When several threads may write, and the first should win, use `compareAndSet`. The Javadoc gives it volatile semantics: it reads the current value as `getVolatile` and, if that value is the expected one, writes as `setVolatile`. Weaker variants exist (`compareAndExchangeAcquire`, `weakCompareAndSetRelease` and others). The `weak` ones may fail even when the value matches, so they belong inside retry loops.

Don't use it for \"I write my flag, then check yours\". That's the store-buffering shape from the previous section, and it needs volatile, or better a lock or a compareAndSet on one shared variable.

Why bother, when a volatile field does all this? Because the write side is cheaper. On x86, a release write is a plain store, while a volatile write also drains the store buffer. For a queue that hands over millions of messages a second from one producer, that difference shows up in a profile. That's the whole case for this mode."""

S4 = """Almost never in application code. Prefer, in this order: a `java.util.concurrent` class (a `BlockingQueue` for handoffs, `ConcurrentHashMap`, `CompletableFuture`); then a `volatile` field or an `Atomic` class; then a lock. Reach for VarHandle modes only when three things are true: you're writing a low-level building block, a profiler shows the cost of volatile or of the extra `Atomic` object matters, and you will test it with jcstress.

That describes the people who write `java.util.concurrent` itself (`FutureTask` and `ConcurrentLinkedQueue` both keep their state behind VarHandles), high-performance queue libraries, and almost nobody writing a Quarkus endpoint. It's also the supported way out of `sun.misc.Unsafe`. JDK 23 deprecated Unsafe's memory-access methods for removal (JEP 471), and JDK 24 prints a warning the first time code uses them (JEP 498). A library that still uses Unsafe is a library you'll be upgrading soon.

The bigger problem is testing. A JUnit test can't prove any of this. Your test ran on one CPU family, after one JIT warm-up, under one load. A green run says that machine didn't produce the bad outcome that time. The lab's tests check behavior that is deterministic once the code is right; they can't catch a missing release on x86.

**jcstress**, the OpenJDK concurrency stress harness, is the honest test. You write a `@State` class, two or more `@Actor` methods that run against each other, and an `@Outcome` for each result, marked `ACCEPTABLE`, `ACCEPTABLE_INTERESTING` or `FORBIDDEN`. jcstress runs the actors on fresh state objects many millions of times, in several JVM configurations, and prints how often each outcome happened. A forbidden outcome that appears even once fails the test.

Two habits make its results worth having. Read the outcome table, not just pass or fail: an interesting outcome at 0.01% is a real bug in production. And run it on ARM if you can, on an Apple Silicon laptop or a Graviton instance. x86 never lets one store pass another, so many ordering bugs simply can't show there. The Try it puts your lab slot under jcstress and shows exactly that."""

L = {
 "id": "jmm-06",
 "title": "VarHandles and memory ordering modes",
 "minutes": 35,
 "goal": "By the end you can name the four access modes and what each one promises, write a release/acquire handoff and a compareAndSet flag with a VarHandle, and explain why app code almost never needs them and why only jcstress can test them.",
 "warmup": {
  "q": "Two threads run the store-buffering test from lesson 1 of this track with a VarHandle. Thread A: `X.setRelease(p, 1); r1 = (int) Y.getAcquire(p);`. Thread B: `Y.setRelease(p, 1); r2 = (int) X.getAcquire(p);`. Can both `r1` and `r2` end up 0?",
  "options": [
   "No: release plus acquire is everything volatile does",
   "Yes, even on x86",
   "Only on ARM, because x86 never reorders",
   "Only if the fields are long or double"
  ],
  "answer": 1,
  "why": "Release keeps earlier accesses before the write, and acquire keeps later accesses after the read. Neither stops a thread's read from overtaking its own earlier write, and that's exactly what x86's store buffer does. Volatile adds one total order over all volatile accesses, which is what forbids both reading 0. The jcstress sample BasicJMM_07_Consensus recorded it in 6.18% of samples with acquire/release and never with volatile."
 },
 "sections": [
  {
   "h": "A VarHandle puts the memory mode on each access",
   "body": S1,
   "refs": [
    {"title": "JEP 193: Variable Handles", "url": "https://openjdk.org/jeps/193", "kind": "read"},
    {"title": "VarHandle (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/invoke/VarHandle.html", "kind": "docs"}
   ]
  },
  {
   "h": "Four modes, from weakest to strongest",
   "body": S2,
   "figure": {"svg": FIG, "caption": "Each mode keeps every promise of the modes below it and adds one more."},
   "try": {
    "title": "Store buffering in four modes",
    "minutes": 4,
    "steps": [
     "Read `ModesDemo`. It runs the store-buffering test from lesson 1 of this track once per access mode, 262,144 trials each.",
     "Predict, for each mode, whether any trial ends with both threads reading 0.",
     "Run it (Java or Kotlin). Then explain the opaque line: opaque stops the JIT from reordering, so who is reordering?"
    ],
    "code": code("ModesDemo"),
    "expect": "Plain, opaque and release/acquire all show trials where both threads read 0: usually tens of thousands, up to about 130,000 here, fewer in a cold first run, and different every time. Volatile shows 0 on every run. Opaque and release/acquire keep the JIT honest, so what you see is the CPU's store buffer: each thread's write is still queued while it reads the other field. Only the volatile write makes HotSpot drain the buffer before the next read."
   },
   "refs": [
    {"title": "jcstress sample BasicJMM_07_Consensus: plain, volatile and acquire/release Dekker", "url": "https://github.com/openjdk/jcstress/blob/master/jcstress-samples/src/main/java/org/openjdk/jcstress/samples/jmm/basic/BasicJMM_07_Consensus.java", "kind": "read"},
    {"title": "jcstress sample BasicJMM_06_Causality: plain, opaque, volatile and acquire/release", "url": "https://github.com/openjdk/jcstress/blob/master/jcstress-samples/src/main/java/org/openjdk/jcstress/samples/jmm/basic/BasicJMM_06_Causality.java", "kind": "read"}
   ]
  },
  {
   "h": "Release/acquire is for handing data to another thread",
   "body": S3,
   "try": {
    "title": "Hand over transfers three ways",
    "minutes": 5,
    "steps": [
     "Read `HandoffDemo`. One producer hands transfers to one consumer through a one-item slot for three seconds. There are three slots: ordinary field access, opaque, and release/acquire.",
     "Predict for each one: does it keep going, and does the consumer ever see a transfer with the wrong fields?",
     "Run it three times, adding `-Pargs=plain`, then `-Pargs=opaque`, then no argument (release/acquire). Try the Kotlin twin too."
    ],
    "code": code("HandoffDemo", java_run=run("HandoffDemo") + " -Pargs=plain", kotlin_run=run("HandoffDemoKt") + " -Pargs=plain"),
    "expect": "Release/acquire hands over millions of transfers with 0 wrong. Opaque usually does the same on x86, but nothing orders the transfer's fields before the slot write, so on ARM it is allowed to deliver a transfer whose fields are still 0. The plain slot usually gets stuck within a second: once the JIT compiles a spin loop, it may read the field once and never again. In my runs the Java version got stuck every time and the Kotlin version only some of the time. Both are allowed, which is the point: a plain run that works tells you nothing."
   }
  },
  {
   "h": "When you need them, and why only jcstress can test them",
   "body": S4,
   "try": {
    "title": "Put your slot under jcstress",
    "minutes": 6,
    "steps": [
     "Optional, and it needs Maven and network access. Finish the lab first. Then create a jcstress project with the archetype command from the jcstress README:\n\n```bash\nmvn archetype:generate -DinteractiveMode=false -DarchetypeGroupId=org.openjdk.jcstress -DarchetypeArtifactId=jcstress-java-test-archetype -DgroupId=org.sample -DartifactId=test -Dversion=1.0\n```",
     "In `test/pom.xml`, change `<javac.target>1.8</javac.target>` to `21`. The archetype targets Java 8, and VarHandle needs JDK 9 or later.",
     "Copy `Settlement.java` and your `SettlementSlot.java` into `test/src/main/java/org/sample/` and change their package line to `package org.sample;`. Replace `ConcurrencyTest.java` with the test below.",
     "Run `mvn clean verify`, then `java -jar target/jcstress.jar -t SlotHandoffTest -m quick -v`. Read the results table.",
     "Change your slot's `setRelease` and `getAcquire` to `setOpaque` and `getOpaque`. Predict, rebuild and run again."
    ],
    "code": {"lang": "java", "solo": True, "title": "SlotHandoffTest.java", "src": "package org.sample;\n\nimport org.openjdk.jcstress.annotations.*;\nimport org.openjdk.jcstress.infra.results.J_Result;\n\nimport static org.openjdk.jcstress.annotations.Expect.*;\n\n@JCStressTest\n@Outcome(id = \"-1\",   expect = ACCEPTABLE, desc = \"The slot was still empty\")\n@Outcome(id = \"8400\", expect = ACCEPTABLE, desc = \"Saw the whole settlement\")\n@Outcome(id = \"0\",    expect = FORBIDDEN,  desc = \"Saw the settlement but not its amount\")\n@State\npublic class SlotHandoffTest {\n    final SettlementSlot slot = new SettlementSlot();\n\n    @Actor\n    public void producer() {\n        Settlement s = new Settlement();\n        s.amountCents = 8400;                 // a plain write...\n        slot.offer(s);                        // ...then the release\n    }\n\n    @Actor\n    public void consumer(J_Result r) {\n        Settlement s = slot.poll();           // the acquire\n        r.r1 = (s == null) ? -1 : s.amountCents;\n    }\n}\n", "run": "java -jar target/jcstress.jar -t SlotHandoffTest -m quick -v"},
    "expect": "jcstress prints a table like the ones in its samples. On an x86_64 machine in quick mode, a run here showed `-1` (empty) in about 65% of 199 million samples, `8400` in the other 35%, and `0` (Forbidden) in none: the test is OK. The all-opaque version also showed 0 forbidden samples on x86_64, in about 133 million. That doesn't make it correct. x86 never lets one store pass another; ARM does, and there the opaque slot is allowed to fail. jcstress is the tool that would show it, if you run it on the right machine."
   },
   "refs": [
    {"title": "jcstress: the OpenJDK concurrency stress tests (README and samples)", "url": "https://github.com/openjdk/jcstress", "kind": "read"},
    {"title": "JEP 498: Warn upon Use of Memory-Access Methods in sun.misc.Unsafe", "url": "https://openjdk.org/jeps/498", "kind": "read"}
   ]
  }
 ],
 "analogy": "Think of a shared notice board in a busy office. Plain writes are notes you scribble on your own pad and may never pin up. Opaque writes are pinned to the board eventually, and your notes on one topic go up in the order you wrote them, but notes on different topics can go up in any order. A release write is a sealed envelope pinned to the board: everything you wrote before sealing it is inside, and whoever opens it (the acquire) reads all of it. Volatile adds a clerk who stamps every envelope with one office-wide sequence number, so everyone agrees on the order. The analogy breaks on cost: in an office the clerk is slow and the envelope is cheap; on x86 the envelope is free and only the clerk's stamp, the volatile write, costs anything.",
 "in_your_world": "In a payments service you'll almost never write a VarHandle, but you run code that does. Much of `java.util.concurrent` is built on them. Where this lesson pays off is in reviews and upgrades. When someone proposes replacing a `volatile` flag in a Kafka consumer loop with `getOpaque` to save time, you can say it saves nothing on x86 reads, and ask for a profile and a jcstress test first. When a JDK 24 or later upgrade starts printing warnings about `sun.misc.Unsafe` memory-access methods, you know the library's fix is a VarHandle (or, for off-heap memory, the foreign memory API), and that the warning comes from the dependency, not your code. And when a test suite \"proves\" some lock-free code correct on the x86 CI agents, you know to ask what happens on the Graviton nodes.",
 "mistake": "The most common mistake is using a weaker mode than the pattern needs, because \"acquire/release is what volatile does, only cheaper\". It isn't. Release/acquire is enough to hand data from one writer to its readers through one variable. It is not enough for Dekker-style code, where each thread writes its own flag and then reads the other's: both threads can read the old value, on x86 too, and both enter the critical section. If two variables are involved, or several threads write, use volatile, compareAndSet or a lock. And whichever mode you pick, write a jcstress test before you trust it.",
 "compare": {
  "title": "The same release/acquire handoff with AtomicReference, in Java and Kotlin",
  "java": {"title": "LatestBatch.java", "src": "final class LatestBatch {\n    private final AtomicReference<Batch> latest = new AtomicReference<>();\n\n    // writer: build the batch with plain writes, then release it\n    void publish(Batch b) { latest.setRelease(b); }\n\n    // readers: an acquire read sees the batch's fields as the writer left them\n    Batch current() { return latest.getAcquire(); }\n\n    // several writers racing to set the first batch: compareAndSet, volatile semantics\n    boolean publishFirst(Batch b) { return latest.compareAndSet(null, b); }\n}"},
  "kotlin": {"title": "LatestBatch.kt", "src": "class LatestBatch {\n    private val latest = AtomicReference<Batch?>(null)\n\n    // writer: build the batch with plain writes, then release it\n    fun publish(b: Batch) = latest.setRelease(b)\n\n    // readers: an acquire read sees the batch's fields as the writer left them\n    fun current(): Batch? = latest.getAcquire()\n\n    // several writers racing to set the first batch: compareAndSet, volatile semantics\n    fun publishFirst(b: Batch): Boolean = latest.compareAndSet(null, b)\n}"},
  "note": "Kotlin has no memory-mode syntax of its own on the JVM. `@Volatile` gives you volatile, and for every other mode you call the same JDK classes as Java. `AtomicReference` and friends have had `getAcquire`, `setRelease`, `getOpaque` and `getPlain` since JDK 9, so this is the readable way to use the modes: no lookup, no casts, one extra object per field. VarHandle calls also work from Kotlin, because the Kotlin compiler (2.4 in these labs) treats VarHandle methods as signature-polymorphic and takes the return type from the `as` cast. Use a VarHandle only when that extra object per instance matters, as it does for nodes in a queue with millions of entries."
 },
 "worked": {
  "title": "Choose the weakest mode for a consumer's record counter, then decide whether it's worth it",
  "steps": [
   {"say": "A Kafka consumer thread counts the records it has processed. A metrics scraper reads the count every 15 seconds on another thread. Right now it uses an `AtomicLong`. Before reading on, list what the reader actually needs.",
    "code": "final class ConsumerMetrics {\n    private final AtomicLong processed = new AtomicLong();\n\n    void onRecord() { processed.incrementAndGet(); }   // consumer thread, once per record\n    long processed() { return processed.get(); }        // scrape thread, every 15 s\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "class ConsumerMetrics {\n    private val processed = AtomicLong()\n\n    fun onRecord() { processed.incrementAndGet() }    // consumer thread, once per record\n    fun processed(): Long = processed.get()           // scrape thread, every 15 s\n}"},
   {"say": "Only one thread writes, so the increment doesn't have to be an atomic read-modify-write; that was the lesson of single-writer fields in lesson 3 of this track. The reader needs a `long` that isn't torn and that eventually moves. It doesn't read any other data based on the count, so it needs no acquire. That's exactly opaque: atomic for 64 bits, coherent, eventually visible.", "code": "", "lang": ""},
   {"say": "The weakest correct version uses the modes `AtomicLong` already has, with subgoal labels.",
    "code": "final class ConsumerMetrics {\n    private final AtomicLong processed = new AtomicLong();\n\n    void onRecord() {\n        long next = processed.getPlain() + 1;      // 1. the only writer can read its own value plainly\n        processed.setOpaque(next);                 // 2. opaque: untorn and eventually visible\n    }\n\n    long processed() {\n        return processed.getOpaque();              // 3. a recent, untorn value; orders nothing else\n    }\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "class ConsumerMetrics {\n    private val processed = AtomicLong()\n\n    fun onRecord() {\n        val next = processed.getPlain() + 1        // 1. the only writer can read its own value plainly\n        processed.setOpaque(next)                  // 2. opaque: untorn and eventually visible\n    }\n\n    fun processed(): Long = processed.getOpaque()  // 3. a recent, untorn value; orders nothing else\n}"},
   {"say": "Now decide. On x86 this replaces one locked instruction per record with a plain store. At 5,000 records a second you will never see the difference; in a loop doing tens of millions a second, you might. The price is a rule nobody can see in the code: the moment a second thread calls `onRecord()`, counts are silently lost. Keep `incrementAndGet()` until a profiler points at it, and if many threads count, use `LongAdder` instead.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "A settlement slot and a kill switch with acquire and release",
  "minutes": 14,
  "files": [
   "labs/jmm/src/main/java/workbench/jmm/l06/SettlementSlot.java",
   "labs/jmm/src/main/java/workbench/jmm/l06/KillSwitch.java"
  ],
  "run": "./gradlew :jmm:test --tests 'workbench.jmm.l06.*'",
  "steps": [
   "Run the tests once. All seven fail: the TODOs throw, and `KillSwitch` has no VarHandle yet. `Settlement` is given and needs no changes.",
   "Write `SettlementSlot.offer` and `poll` with the given `ITEM` handle: an acquire read to look at the slot, and a release write to fill it or empty it.",
   "In `KillSwitch`, add a `private static final VarHandle` for the `reason` field, the same way `SettlementSlot` does.",
   "Write `trip` with `compareAndSet`, and `isTripped` and `reason` with acquire reads.",
   "Run the tests until all seven pass, then twice more. Then ask yourself which of these tests would still pass on x86 if `offer` used `setOpaque`, and what that means."
  ],
  "hints": [
   "VarHandle methods take the receiver first and need a cast on the result: `(Settlement) ITEM.getAcquire(this)`, `ITEM.setRelease(this, s)`.",
   "Why does `offer` check the slot with an acquire read and not a plain one? A plain read in the producer's spin loop may be read once and never again. The acquire also pairs with the consumer's release of null.",
   "`REASON.compareAndSet(this, null, why)` returns true only for the caller that found null. It has volatile semantics, so a later acquire read of the reason sees the winner's string."
  ],
  "done_when": "All seven tests in `VarHandleModesTest` pass, three runs in a row."
 },
 "drill": {
  "title": "A release/acquire handoff from memory",
  "minutes": 5,
  "prompt": "Close this page. Write `ReportBox`: plain fields `total` and `count`, a plain `ready` flag reached only through a VarHandle, a writer method `publish(total, count)` and a reader method `tryRead()` that returns null until the report is ready. Number the four steps. Then compare. Did you pair the release and the acquire on the same field?",
  "answer": {"lang": "java", "src": "final class ReportBox {\n    private static final VarHandle READY;\n    static {\n        try {\n            READY = MethodHandles.lookup().findVarHandle(ReportBox.class, \"ready\", boolean.class);\n        } catch (ReflectiveOperationException e) {\n            throw new ExceptionInInitializerError(e);\n        }\n    }\n\n    private long total;          // plain: carried by the release below\n    private int count;\n    private boolean ready;       // plain field, reached only through READY\n\n    void publish(long total, int count) {      // one writer, once\n        this.total = total;                     // 1. plain writes of the data\n        this.count = count;\n        READY.setRelease(this, true);           // 2. release: the data can't move after this\n    }\n\n    String tryRead() {\n        if (!(boolean) READY.getAcquire(this)) return null;   // 3. acquire\n        return count + \" payments, \" + total + \" cents\";       // 4. sees the data\n    }\n}",
             "alt": {"lang": "kotlin", "src": "class ReportBox {\n    private var total = 0L       // plain: carried by the release below\n    private var count = 0\n    private var ready = false    // plain field, reached only through READY\n\n    fun publish(total: Long, count: Int) {      // one writer, once\n        this.total = total                      // 1. plain writes of the data\n        this.count = count\n        READY.setRelease(this, true)            // 2. release: the data can't move after this\n    }\n\n    fun tryRead(): String? {\n        if (!(READY.getAcquire(this) as Boolean)) return null   // 3. acquire\n        return \"$count payments, $total cents\"                   // 4. sees the data\n    }\n\n    companion object {\n        private val READY: VarHandle = MethodHandles.lookup()\n            .findVarHandle(ReportBox::class.java, \"ready\", Boolean::class.javaPrimitiveType)\n    }\n}"}}
 },
 "recap": [
  "A VarHandle (JDK 9, JEP 193) is a static final handle to a plain field, and each call picks its own memory mode.",
  "The modes form a ladder: plain (no promise), opaque (each access happens, untorn, eventually visible), acquire/release (data written before a release is seen after the matching acquire), volatile (plus one total order).",
  "Release/acquire is for handing data from one writer through one variable. It does not forbid the store-buffering result; only volatile does.",
  "`compareAndSet` has volatile semantics and is the tool when several threads race to write first.",
  "In app code, prefer j.u.c classes, then volatile or `Atomic*` (which offer the same modes), then locks. VarHandles are for building blocks, after a profiler asks for them.",
  "Only jcstress tests ordering honestly, and an x86 run can't show bugs that ARM allows."
 ],
 "quiz": [
  {
   "q": "A shutdown hook sets a flag once. A hot loop on another thread checks the flag and only needs to stop eventually; the flag guards no other data. What is the weakest mode that is guaranteed to work?",
   "options": [
    "Plain",
    "Opaque",
    "Acquire/release",
    "Volatile"
   ],
   "answer": 1,
   "why": "Opaque guarantees each read really happens, so the loop eventually sees the write (jcstress BasicJMM_04 forbids a stuck opaque spin). Plain may be read once for the whole loop. Acquire/release and volatile also work but promise more than this loop needs. In app code you'd still write volatile, because it's one keyword and costs nothing extra on an x86 read."
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
   "why": "The ordering is a pair: release on the writer's side, acquire on the reader's. An opaque read sees the flag eventually, but nothing stops the reader's read of `total` from happening before it. Modes may be mixed without an exception (option 3), and opaque reads do see the value (option 4)."
  },
  {
   "q": "Two settlement workers decide who runs the nightly batch: each does `MINE.setRelease(this, true)`, then reads the other's flag with `getAcquire`, and runs the batch if it reads false. What's wrong?",
   "options": [
    "Nothing: release/acquire orders the write before the read",
    "It only fails on ARM",
    "It throws, because each VarHandle may only be used by one thread",
    "Both workers can read false and both run the batch, even on x86; this shape needs volatile, or better one compareAndSet or a database lock"
   ],
   "answer": 3,
   "why": "This is store buffering. Release keeps earlier accesses before the write but doesn't stop the later read of a different variable from passing it, and x86's store buffer does exactly that. Volatile forbids it through its single total order. In a real service, use one shared variable with compareAndSet, or a lock in the database both workers share."
  },
  {
   "q": "Where do VarHandle access modes belong?",
   "options": [
    "On every hot volatile field in a Quarkus service",
    "Instead of synchronized in request handlers",
    "In low-level building blocks like queues, after a profiler shows the cost, with jcstress tests",
    "Nowhere: they were deprecated with sun.misc.Unsafe"
   ],
   "answer": 2,
   "why": "VarHandles are the supported replacement for Unsafe, not deprecated with it (option 4). They only pay off in code that hands over millions of values a second, and they need jcstress because unit tests can't see reorderings. A request handler gets nothing from them that volatile, an Atomic class or a lock doesn't give it more clearly."
  },
  {
   "q": "From lesson 3 of this track: many threads run `balance += amount` on a `volatile long balance`. Someone suggests `BALANCE.getAndAdd(this, amount)` through a VarHandle instead. Does that fix it?",
   "options": [
    "No, a VarHandle has the same problem as volatile",
    "Yes: getAndAdd is one atomic read-modify-write, like AtomicLong.getAndAdd",
    "Only if a setRelease follows it",
    "Only on 64-bit JVMs"
   ],
   "answer": 1,
   "why": "Volatile makes each read and each write visible, but `+=` is still a read and a write with a gap between them, so updates get lost. `getAndAdd` is a single atomic update with volatile semantics. In app code an `AtomicLong` or a `LongAdder` says the same thing more plainly.",
   "from": "jmm-03"
  }
 ],
 "flashcards": [
  {"front": "What does a VarHandle let you choose that a volatile field doesn't?", "back": "The memory mode of each access (plain, opaque, acquire/release, volatile) on a plain field, plus atomic updates such as compareAndSet."},
  {"front": "What does opaque mode add over plain?", "back": "Each access really happens, untorn and in order for that variable, so a spinning reader eventually sees a new value. It orders no other variables."},
  {"front": "A release write and an acquire read of the same variable: what does the reader get?", "back": "If its acquire read sees the released value, it also sees every write the writer made before the release."},
  {"front": "What does volatile add on top of acquire/release?", "back": "One total order of all volatile accesses. That forbids the store-buffering result where two threads both read the other's variable as 0."},
  {"front": "What memory semantics does `VarHandle.compareAndSet` have?", "back": "Volatile: it reads the witness value as getVolatile and, on success, writes as setVolatile."},
  {"front": "Why keep a VarHandle in a `static final` field?", "back": "The JIT treats a static final as a constant, so each call compiles down to a load or store plus the barrier its mode needs."},
  {"front": "Why can't a passing JUnit test show that release/acquire code is correct?", "back": "It shows one machine didn't produce a bad outcome that time. jcstress runs the actors millions of times and fails on any forbidden outcome; x86 can't show many ARM bugs."}
 ],
 "terms": [
  {"term": "VarHandle", "plain": "A typed handle to a field or array element whose methods read and write it in a chosen memory mode (JDK 9)."},
  {"term": "Access mode", "plain": "The memory rules for one read or write: plain, opaque, acquire/release or volatile."},
  {"term": "Opaque", "plain": "A mode where each access really happens, untorn and in order for that variable, with no ordering of other variables."},
  {"term": "Acquire and release", "plain": "A paired mode: writes before the release are visible to a thread whose acquire read sees the released value."},
  {"term": "Signature-polymorphic method", "plain": "A method whose real signature comes from the call site's argument types and result cast, like VarHandle.get."},
  {"term": "Store buffering", "plain": "Each thread writes one variable, then reads the other's; both may read the old value unless the accesses are volatile."},
  {"term": "jcstress", "plain": "The OpenJDK harness that runs concurrent actors millions of times and checks every outcome against acceptable and forbidden ones."}
 ],
 "explain_back": {
  "prompt": "A teammate wants to replace every `volatile` field in your payment service with VarHandle acquire/release \"because it's faster\". Explain what they would gain, what they would risk, and what you'd do instead.",
  "answer": "On x86 the reads gain nothing, because a volatile read already compiles to an ordinary load. Only the writes get cheaper, since a release store skips the instruction that drains the store buffer, and in a service that writes these fields a few thousand times a second that saving is invisible. The risk is real: release/acquire is weaker than volatile. It's enough for one writer handing data through one variable, but any code that relies on the single total order, like two flags where each thread writes its own and reads the other's, would break, and our x86 tests might never show it. On top of that, every field gets a lookup, casts and a rule that every access goes through the handle. I'd keep volatile and the Atomic classes, and only consider modes for a specific hot path that a profiler points at, with a jcstress test, ideally run on ARM too."
 },
 "deeper": {
  "minutes": 10,
  "body": "The VarHandle Javadoc maps the modes onto the C and C++ memory model, which helps when you read papers or Rust and C++ code: volatile is compatible with `memory_order_seq_cst`, acquire with `memory_order_acquire`, and release with `memory_order_release`. There are also static fence methods, `VarHandle.fullFence()`, `acquireFence()` and `releaseFence()`, documented as the matching `atomic_thread_fence` calls, plus `loadLoadFence()` and `storeStoreFence()`. Fences order a thread's accesses around a point without tying the order to one variable. They're even easier to misuse than modes. The jcstress samples `AdvancedJMM_14_SynchronizedAreNotFences` and `AdvancedJMM_15_VolatilesAreNotFences` show that synchronized blocks and volatile accesses don't work as fences either. Their guarantees hold only between threads that take the same lock, or when a volatile read actually sees the volatile write; you can't use them as free-standing barriers.\n\nVarHandles aren't only for fields. `MethodHandles.arrayElementVarHandle(String[].class)` gives you the modes on array elements, which a `volatile` array never could, because volatile there applies only to the array reference. `MethodHandles.byteArrayViewVarHandle` reads and writes an `int` or a `long` inside a `byte[]` with a chosen byte order and a chosen mode.\n\nIf you want the model behind the modes in one sitting, Doug Lea's \"Using JDK 9 Memory Order Modes\" is the short guide to the modes, by the lead author of `java.util.concurrent`. Aleksey Shipilëv's \"Java Memory Model Pragmatics\" is the long version."
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
