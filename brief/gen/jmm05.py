import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/jmm/src"
P = "java/workbench/jmm/l05"
K = "kotlin/workbench/jmm/l05"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"{lab}/demo/{P}/{name}.java"
kdemo = lambda name: f"{lab}/demo/{K}/{name}.kt"
run = lambda name: f"./gradlew :jmm:demo -Pmain=workbench.jmm.l05.{name}"


def code(name):
    """A Java demo with its Kotlin twin (Foo.kt with a top-level main, class FooKt)."""
    return {"lang": "java", "title": f"{name}.java", "src": read(demo(name)), "run": run(name), "file": demo(name),
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(kdemo(name)), "run": run(name + "Kt"), "file": kdemo(name)}}


def row(y, question, answer, answer_cls="box-ok", last=False):
    s = (
        f'<rect class="box" x="20" y="{y}" width="300" height="44" rx="8"/>'
        f'<text class="t" x="170" y="{y + 27}" text-anchor="middle">{question}</text>'
        f'<line class="ln" x1="320" y1="{y + 22}" x2="378" y2="{y + 22}" marker-end="url(#arr)"/>'
        f'<text class="t-s t-m" x="349" y="{y + 14}" text-anchor="middle">yes</text>'
        f'<rect class="{answer_cls}" x="380" y="{y}" width="280" height="44" rx="8"/>'
        f'<text class="t-s" x="520" y="{y + 27}" text-anchor="middle">{answer}</text>'
    )
    if not last:
        s += (f'<line class="ln-d" x1="170" y1="{y + 44}" x2="170" y2="{y + 68}" marker-end="url(#arr)"/>'
              f'<text class="t-s t-m" x="186" y="{y + 61}">no</text>')
    return s


FIG = (
    '<svg viewBox="0 0 680 300" role="img" aria-label="Decision guide. Needed by nearly every call: build it at startup. '
    'One per program and building it cannot fail: holder idiom, enum or Kotlin object. One value per key: computeIfAbsent. '
    'One per object, or must retry after a failure: volatile double-checked locking or Kotlin by lazy.">'
    + row(16, "Needed by nearly every call?", "Build it eagerly, at startup")
    + row(86, "One per program, can't fail?", "Holder idiom, enum, Kotlin object")
    + row(156, "One value per key?", "ConcurrentHashMap.computeIfAbsent")
    + row(226, "One per object, or must retry?", "volatile DCL, or Kotlin by lazy", "box-a", last=True)
    + '</svg>'
)

SIM = {
    "title": "Broken double-checked locking",
    "intro": "T1 builds the card table under the lock. Its two stores are listed in the order another thread may see them: the reference first, the table's rows second. T2 takes the fast path, with no lock. Run T1 until it has stored the reference, then switch to T2. Can T2 use a table with no rows in it?",
    "vars": {"table": 0, "rows": 0, "seenRows": -1},
    "locks": ["lock"],
    "threads": [
        {"name": "T1", "steps": [
            {"op": "lock", "lock": "lock", "code": "synchronized (CardBinTable.class) {"},
            {"op": "check", "var": "table", "eq": 0, "code": "if (table == null) {   // second check"},
            {"op": "set", "var": "table", "n": 1, "code": "table = t;   // the reference becomes visible first"},
            {"op": "set", "var": "rows", "n": 3, "code": "t.rows = 3;   // the constructor's write, seen later"},
            {"op": "unlock", "lock": "lock", "code": "}   // leave the lock"}]},
        {"name": "T2", "steps": [
            {"op": "check", "var": "table", "eq": 1, "code": "if (table != null) {   // fast path: no lock"},
            {"op": "read", "var": "rows", "reg": "r", "code": "int rows = table.rows;"},
            {"op": "write", "var": "seenRows", "reg": "r", "code": "lookUp(rows);"}]}
    ],
    "goal": {"var": "seenRows", "eq": 0, "say": "T2 used a table with 0 rows. It saw the reference but not the constructor's write, because its read on the fast path has no edge to anything T1 did under the lock. A volatile table field forbids this order."}
}

OPENING = """A small shop keeps its stockroom at the back. Opening it takes a while: find the key, switch on the lights, pull the covers off the shelves. Most days nobody needs anything from it, so the shopkeeper opens it only when the first customer asks.

Now give the shop several assistants. Two customers ask at the same moment, two assistants see the door shut, and both go to open it. Worse, the usual fix can send a customer into a room whose door is open and whose lights are still off.

Programs build things on first use too, often on several threads at once. (A thread is one path of work running beside others in the same program.) The usual fix, checking twice, looks so plainly right that it passes every test on a laptop. The last lesson showed that a reference can arrive before the fields behind it, and first use is the worst moment for that. In this lesson, we'll break the naive version, fix the double check with one word, let the JVM do the locking, and look inside Kotlin's `by lazy`. Before we start, make a guess, and keep it in mind."""

S0 = """Every payment card number starts with six digits, called the BIN, that say which bank issued the card. The shop's program keeps a `CardBinTable` from those six digits to the bank's name. Loading it means reading a big file, which takes about 50 ms, and some runs of the program never need it at all. So the program builds it on first use. That's called lazy initialization: building something the first time it's needed, instead of at startup. Here's the version most people write first:

```java
// Naive: check, then act
private static CardBinTable instance;

static CardBinTable instance() {
    if (instance == null) {              // check: is the stockroom open?
        instance = new CardBinTable();   // act: two threads can both get here
    }
    return instance;
}
```

```kotlin
// Naive: check, then act
private var instance: CardBinTable? = null

fun instance(): CardBinTable {
    if (instance == null) {              // check: is the stockroom open?
        instance = CardBinTable()        // act: two threads can both get here
    }
    return instance!!
}
```

That's the check-then-act race from Race conditions: a check, then an action, with a gap between them that another thread can use. Two threads can both see `null`, and both build a table. Here that wastes 50 ms. With something that opens a network connection, one connection leaks. There's a second bug, from Safe publication: the table is published through a plain field, so a reader can see the reference before the constructor's writes.

Marking the method `synchronized` fixes both. Its lock, the thing that lets one thread at a time into a piece of code, makes the check and the build one step. It's correct, and often good enough. In the shop, it's one key on a hook by the counter: every assistant takes the key before going near the stockroom, all day, even when the door has stood open since the morning. Every caller takes the lock on every call, for a value that never changes after the first one.

So programmers came up with **double-checked locking** (DCL for short): glance at the door first, and take the key only if it's shut.

```java
// Broken: double-checked locking without volatile
static CardBinTable instance() {
    if (instance == null) {                      // 1. first check, no lock
        synchronized (CardBinTable.class) {
            if (instance == null) {              // 2. second check, under the lock
                instance = new CardBinTable();
            }
        }
    }
    return instance;                             // a plain read on the fast path
}
```

```kotlin
// Broken: double-checked locking without @Volatile
private val lock = Any()

fun instance(): CardBinTable {
    if (instance == null) {                      // 1. first check, no lock
        synchronized(lock) {
            if (instance == null) {              // 2. second check, under the lock
                instance = CardBinTable()
            }
        }
    }
    return instance!!                            // a plain read on the fast path
}
```

The lock and the second check do stop two builds: one thread at a time gets past the lock, and whoever comes second finds the table there. The fast path, the first check that takes no lock, is the problem. A thread that finds `instance != null` never takes the lock. So no happens-before edge, the link that guarantees one thread sees another's writes, connects its read to the builder's writes. As in Safe publication, the JIT (the compiler inside the JVM that turns busy code into machine code) and the processor may let the reference out before the constructor's field writes. That thread can return a table that isn't null and is still empty. The door is open, and the lights are off.

jcstress, the OpenJDK tool that runs tiny tests on several threads at once, millions of times, has a sample of exactly this, `Singleton_07_BrokenNonVolatileDCL`. Two threads ask a non-volatile DCL for a singleton, an object meant to exist once, whose data field isn't final. Here is the run recorded in the sample, on an AArch64 machine, a 64-bit ARM one:

```text
            RESULT        SAMPLES     FREQ       EXPECT  DESCRIPTION
      data1, data1  1,470,891,960   63.17%   Acceptable  Trivial.
  data1, null-data      1,124,329    0.05%  Interesting  Data races.
      data2, data2    855,805,003   36.75%   Acceptable  Trivial.
  null-data, data2        665,052    0.03%  Interesting  Data races.
```

About 1.8 million of 2.3 billion callers got a singleton that wasn't null and carried no data. When the sample made the data field final, there were no failures at all, on x86_64 or AArch64, because final fields arrive whole through any race. That's why broken DCL so often seems to work: many such objects happen to have only final fields, and x86 machines (the Intel and AMD kind) rarely show the reordering. The simulator below lets you play the bad order by hand.

**Checking twice without volatile can hand out an object that looks finished and isn't. The fast path needs an edge.**

One word gives it one."""

S1 = """Make the field `volatile`, a field whose reads always see the latest write, and double-checked locking is correct. That has been true since Java 5. Java 5 rewrote the memory model, the rules for what one thread sees of another thread's writes (JSR-133), and gave volatile its release and acquire meaning.

In the stockroom, volatile turns the door into a sign. The assistant who opens the room hangs up the OPEN sign only after the lights are on and the covers are off. The other assistants trust the sign, not a glance through the door. Where the picture breaks: in a real shop you'd notice a dark room the moment you walked in. In the JVM, a half-built object looks exactly like a finished one. The reference isn't null, and nothing warns you that its fields are still empty.

DCL's real job is a lazy field that belongs to one object, so here is that version. For a static field, the next section has something simpler.

```java
// Fixed: double-checked locking on a volatile field
class CardBinTableProvider {
    private volatile CardBinTable table;

    CardBinTable table() {
        CardBinTable t = table;                  // 1. fast path: one volatile read
        if (t != null) return t;
        synchronized (this) {                    // 2. slow path: one thread at a time
            t = table;                           // 3. check again: another thread may have won
            if (t == null) {
                t = new CardBinTable();
                table = t;                       // 4. a volatile write publishes the finished table
            }
            return t;
        }
    }
}
```

```kotlin
// Fixed: double-checked locking on a @Volatile field
class CardBinTableProvider {
    @Volatile private var table: CardBinTable? = null

    fun table(): CardBinTable {
        table?.let { return it }                 // 1. fast path: one volatile read
        synchronized(this) {                     // 2. slow path: one thread at a time
            table?.let { return it }             // 3. check again: another thread may have won
            val t = CardBinTable()
            table = t                            // 4. a volatile write publishes the finished table
            return t
        }
    }
}
```

Let's read it in order. First we read the field once, into a local. If the table is there, we're done, and that's what nearly every call does. If not, we take the lock, read the field again, and build the table only if it's still missing. Finally, one volatile write publishes it.

The edge is the one from volatile: what it gives you and what it doesn't. The volatile write in step 4 is a release: it sends everything written before it along with it. The volatile read in step 1 is an acquire: when it sees that write, it receives all of it. So a thread whose read finds the table sees everything the builder wrote before step 4, including every field the constructor set. The sign goes up last, so whoever sees the sign finds the lights on.

Three details matter.

Read the field once, into a local. A final `return table` would be a second volatile read. That's still correct, but the local keeps the fast path to one read. Joshua Bloch's *Effective Java* (item 83) writes it the same way.

Both checks matter. Drop the first and you've rebuilt the synchronized method. Drop the second and every thread that queued at the lock waits politely for its turn, then builds a table of its own. The Try it shows that one.

Null needs care. DCL uses `null` to mean "not built yet", so an initializer that returns `null` runs again on every call. Kotlin's `lazy` uses a sentinel instead, a private marker object that only means "not built yet".

If the constructor throws, nothing is stored, so the next caller tries again. Keep that in mind, because the holder class in the next section behaves differently.

**Double-checked locking is correct only on a volatile field. Read it once, and check it twice.**

That's a lot of care for one field. For a static field, the JVM will take all of it off your hands."""

S2 = """For a static singleton, one object for the whole program, you don't need DCL at all. The JVM already has a lazy, thread-safe, run-once mechanism: class initialization.

A class is initialized right before its first active use: creating an instance, calling a static method, or reading a static field that isn't a compile-time constant (Java Language Specification, section 12.4). A compile-time constant is a value the compiler can work out on its own, such as `static final int MAX = 3`. Initializing it means running its static initializers, once: the assignments to its static fields and its `static { }` blocks. The JVM does that under a lock of its own, one per class, and every thread that uses the class afterwards sees what the initializer wrote. That's the first seal from Safe publication.

In the shop, this is the building's own rule. The landlord holds the only key to each room. The first time anyone asks for a room, the landlord opens it, and everyone else who asks meanwhile waits at the door until it's ready. The JVM is that landlord, a strict doorman: it lets one thread run the initializer and makes the others wait.

The **holder class idiom** puts the instance in a small nested class, so building it waits for the first call that touches that class:

```java
public final class CardBinTable {
    private CardBinTable() { /* read the big BIN file */ }

    private static final class Holder {        // not initialized until instance() touches it
        static final CardBinTable INSTANCE = new CardBinTable();
    }

    public static CardBinTable instance() {
        return Holder.INSTANCE;                // the first call initializes Holder, once, under the JVM's lock
    }
}
```

```kotlin
class CardBinTable private constructor() {
    private object Holder {                    // an object is initialized on first access
        val INSTANCE = CardBinTable()
    }

    companion object {
        fun instance(): CardBinTable = Holder.INSTANCE
    }
}
```

Your code has no volatile and no lock. The Kotlin version uses a private nested `object`, which is initialized on first access, like the Java holder class. The jcstress sample `Singleton_09_Holder` notes that in hot code the JIT will likely drop the initialization check altogether, so `instance()` becomes a single field read.

The holder has three limits. It only works for statics: one instance per class, never one per object. The constructor can't take arguments you only know while the program runs. And it never retries. If the initializer throws, the first caller gets `ExceptionInInitializerError`, and every later caller gets `NoClassDefFoundError: Could not initialize class CardBinTable$Holder`, until the program restarts. The doorman has a long memory: a room that failed to open once stays shut for good. So keep anything that can fail, such as a network connection, out of a holder.

An enum gives you the same guarantee: `enum CardBinTable { INSTANCE; ... }` is built by the enum's own static initializer. *Effective Java* recommends it for singletons, because serialization (turning objects into bytes and back) and reflection (code that inspects and builds objects while the program runs) can't create a second instance. In Kotlin, an `object` declaration is the same idea, and the Kotlin docs say its initialization is thread-safe and done on first access.

One surprise: lazy here means on first use of the class, not of the instance. A plain `static final INSTANCE` in a class with other static methods is built the first time any of them runs. A Kotlin companion object is initialized together with its class. The holder exists to separate the two, and the Try it shows exactly when each one is built.

**For one object per program, let class initialization do the locking. Keep anything that can fail out of it.**

Statics are covered. For a lazy field on an object, Kotlin has a one-word answer, and it turns out to be an old friend."""

S3 = """`val x by lazy { ... }` is the double-checked locking from earlier in this lesson, written once in Kotlin's standard library. The property compiles to a `private final kotlin.Lazy x$delegate` field, and its getter calls `getValue()` on that delegate, the object that does the work for the property. The default mode is `LazyThreadSafetyMode.SYNCHRONIZED`. Its implementation class, `SynchronizedLazyImpl`, has a volatile value field, a fast path that reads it once, and a `synchronized` block with a second check.

It adds three things to the version you'd write by hand. A sentinel instead of null, so a null result is kept too. A retry: the docs promise that if the initializer throws, it runs again on the next access. And it drops the initializer after the first run, so whatever the lambda captured can be cleaned up by the garbage collector, the part of the JVM that frees memory nobody uses.

Here's a `Till`, one of the shop's cash registers, which several threads share. It connects to its receipt printer on first use, which is slow and can fail, and it reads the list of public holidays, which is cheap:

```kotlin
class Till(private val shop: Shop) {
    val printer: ReceiptPrinter by lazy {                  // SYNCHRONIZED: runs once, others wait
        shop.connectPrinter()                               // slow, and it can fail
    }
    val holidays: Set<LocalDate> by lazy(LazyThreadSafetyMode.PUBLICATION) {
        parseHolidays(HOLIDAYS)                             // cheap and pure: may run twice, one result wins
    }
}
```

```java
// Java has no by lazy: a volatile double check stands in for SYNCHRONIZED, a compareAndSet for PUBLICATION
final class Till {
    private final Shop shop;
    private volatile ReceiptPrinter printer;
    private final AtomicReference<Set<LocalDate>> holidays = new AtomicReference<>();

    Till(Shop shop) { this.shop = shop; }

    ReceiptPrinter printer() {
        ReceiptPrinter p = printer;
        if (p != null) return p;
        synchronized (this) {
            if (printer == null) printer = shop.connectPrinter();
            return printer;
        }
    }

    Set<LocalDate> holidays() {
        Set<LocalDate> h = holidays.get();
        if (h != null) return h;
        holidays.compareAndSet(null, parseHolidays(HOLIDAYS));   // losers throw their result away
        return holidays.get();
    }
}
```

The Kotlin version is two properties. The Java version spells out what each mode does, and it shows that `lazy` is no magic: a volatile double check, or a compare-and-set, the "update it only if nobody beat me to it" call from Atomics and compare-and-set. There are three modes:

| Mode | The initializer runs | Use it for |
|---|---|---|
| `SYNCHRONIZED` (default) | once; other callers wait on a lock | anything slow or with side effects |
| `PUBLICATION` | maybe on several threads at once; one result wins | cheap work with no side effects |
| `NONE` | with no synchronization at all | values that never leave one thread |

Keep the default unless you have a reason. `PUBLICATION` fits a cheap, pure initializer when you'd rather waste a little work than make anyone wait. The losers' results are thrown away without any cleanup, so never use it for work with side effects, changes outside the value itself, such as opening a connection. `NONE` fits code that only one thread ever runs. Never put it on a property that several threads share: the docs call the result unspecified, and the Try it shows eight threads getting eight different values.

`SYNCHRONIZED` has two traps. The lock is held while the initializer runs, so a 120 ms call to a slow web service inside `lazy` makes every caller who arrives meanwhile wait up to 120 ms. And by default the lock is the `Lazy` object itself; the docs warn that synchronizing on it from your own code can cause a deadlock.

**Keep lazy's default mode unless you have a reason. Never share a NONE lazy between threads.**

The figure sums up the choice. The simplest answer is often not to be lazy at all: if nearly every call needs the value, build it at startup, and a failure shows up when the program starts instead of in front of a customer. And every tool in this lesson rests on the same pair from volatile: a release write and an acquire read. Next, we'll take that pair apart and see what else it can do."""

L = {
 "id": "jmm-05",
 "title": "Lazy init done right: double-checked locking and holders",
 "minutes": 35,
 "goal": "By the end you can explain why double-checked locking without volatile is broken, write a correct lazy value with a volatile double check, the holder class idiom and Kotlin's `by lazy`, and pick the simplest one that fits.",
 "opening": OPENING,
 "warmup": {
  "q": "A program builds its card table on first use: `if (table == null) { synchronized (Tables.class) { if (table == null) table = new CardBinTable(); } } return table;`. The `table` field is a plain static field, and CardBinTable has some fields that aren't final. What can go wrong when many threads call it at once?",
  "options": [
   "Nothing: the lock and the second check make it safe",
   "Two tables can be built",
   "A caller can get a table that isn't null but whose non-final fields still hold their defaults",
   "Two threads calling it at once deadlock"
  ],
  "answer": 2,
  "why": "The lock and the second check do make sure only one table is built, so option 2 is wrong. The trouble is the first check: a thread that sees `table != null` never takes the lock, so nothing links its read to the constructor's writes. It can see the reference before the fields. Making the field volatile fixes it, as the first two sections show."
 },
 "sections": [
  {
   "h": "Checking twice without volatile hands out a half-built table",
   "body": S0,
   "sim": SIM,
   "refs": [
    {"title": "jcstress sample Singleton_07_BrokenNonVolatileDCL, with its recorded results", "url": "https://github.com/openjdk/jcstress/blob/master/jcstress-samples/src/main/java/org/openjdk/jcstress/samples/primitives/singletons/Singleton_07_BrokenNonVolatileDCL.java", "kind": "read"}
   ]
  },
  {
   "h": "Making the double check correct: one volatile field",
   "body": S1,
   "try": {
    "title": "Break the double check two ways",
    "minutes": 5,
    "steps": [
     "Run `DclDemo` (Java or Kotlin) with the command below. Eight threads ask for the card table at the same moment, and loading it takes 50 ms.",
     "Delete the line marked `try deleting this line`. Predict the output, then run it.",
     "Put the line back. Remove `volatile` (`@Volatile` in Kotlin). Predict, then run."
    ],
    "code": code("DclDemo"),
    "expect": "The correct version loads the table once per round, and all eight threads get the same table. Without the second check, it loads 8 times and hands out 8 different tables: each thread that queued at the lock builds its own. Without volatile, the output doesn't change at all. On an x86 laptop the missing edge almost never shows, so no run of this program can prove the code correct. That's the trap of broken double-checked locking: you need a stress tool like jcstress, ideally on an ARM machine, to see it fail."
   }
  },
  {
   "h": "Letting the JVM lock for you: the holder class idiom",
   "body": S2,
   "try": {
    "title": "When is each singleton built?",
    "minutes": 4,
    "steps": [
     "Read `HolderIdiomDemo`. It has three versions of the card table: an eager `static final`, a holder, and an enum (an `object` in Kotlin). Each one prints a line when it's built.",
     "Before you run it, write down after which numbered step each `built` line will appear.",
     "Run it, Java first, then Kotlin."
    ],
    "code": code("HolderIdiomDemo"),
    "expect": "`EagerBins built` appears right after step 1: calling a static method initialized the class, and that built INSTANCE. `LazyBins built` appears only after step 3, the first `instance()` call, because `tableSize()` in step 2 never touched Holder, and it doesn't appear again in step 4. The enum (or the Kotlin `object`) is built in step 5, the first time anything in it runs. Class initialization is lazy per class; the holder gives the instance a class of its own."
   },
   "refs": [
    {"title": "jcstress sample Singleton_09_Holder", "url": "https://github.com/openjdk/jcstress/blob/master/jcstress-samples/src/main/java/org/openjdk/jcstress/samples/primitives/singletons/Singleton_09_Holder.java", "kind": "read"}
   ]
  },
  {
   "h": "Kotlin's by lazy: the same double check, in three modes",
   "body": S3,
   "figure": {"svg": FIG, "caption": "Pick the simplest tool that fits. Many values that are built lazily should simply be built at startup."},
   "try": {
    "title": "Race the three lazy modes",
    "minutes": 4,
    "steps": [
     "For each mode, predict how many times the 50 ms initializer runs, and how many different values eight threads see.",
     "Run the Kotlin demo with the command below, then the Java twin, which builds the three modes by hand.",
     "Change the sleep from 50 to 0 and run it a few times. Which numbers move?"
    ],
    "code": {"lang": "kotlin", "title": "LazyModesDemo.kt", "src": read(kdemo("LazyModesDemo")), "run": run("LazyModesDemoKt"), "file": kdemo("LazyModesDemo"),
             "alt": {"lang": "java", "title": "LazyModesDemoJava.java", "src": read(demo("LazyModesDemoJava")), "run": run("LazyModesDemoJava"), "file": demo("LazyModesDemoJava")}},
    "expect": "SYNCHRONIZED: 1 run, 1 value. PUBLICATION: up to 8 runs (here all 8, because every thread started before the first one finished) but 1 value, because the first compare-and-set won and everyone returns its result. NONE: 8 runs and 8 values, each thread keeping its own. With no sleep, PUBLICATION and NONE usually run fewer times, because some threads arrive after the first one has finished. The bug in NONE didn't go away. The window just got smaller."
   },
   "refs": [
    {"title": "Kotlin docs: lazy properties", "url": "https://kotlinlang.org/docs/delegated-properties.html", "kind": "docs"},
    {"title": "LazyThreadSafetyMode (Kotlin API)", "url": "https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-lazy-thread-safety-mode/", "kind": "docs"}
   ]
  }
 ],
 "compare": {
  "title": "One lazy value per key: computeIfAbsent in Java, and the getOrPut trap in Kotlin",
  "java": {"title": "IssuerClients.java", "src": "class IssuerClients {\n    private final ConcurrentMap<String, IssuerClient> clients = new ConcurrentHashMap<>();\n\n    IssuerClient clientFor(String issuerId) {\n        // connect runs at most once per missing key; other callers for that key wait for it\n        return clients.computeIfAbsent(issuerId, this::connect);\n    }\n\n    private IssuerClient connect(String issuerId) {\n        return new IssuerClient(issuerId);   // opens a connection\n    }\n}"},
  "kotlin": {"title": "IssuerClients.kt", "src": "class IssuerClients {\n    private val clients = ConcurrentHashMap<String, IssuerClient>()\n\n    // looks the same, isn't: two threads can both run connect() for one key\n    fun clientForRacy(issuerId: String): IssuerClient =\n        clients.getOrPut(issuerId) { connect(issuerId) }\n\n    // the same guarantee as Java: call the JDK method\n    fun clientFor(issuerId: String): IssuerClient =\n        clients.computeIfAbsent(issuerId) { connect(it) }\n\n    private fun connect(issuerId: String): IssuerClient = IssuerClient(issuerId)   // opens a connection\n}"},
  "note": "Sometimes you need one lazy value per key, such as one connection per card issuer, the bank that issued a card. Both versions keep the connections in a `ConcurrentHashMap`. Kotlin's `getOrPut` reads like `computeIfAbsent`, and on a concurrent map it never replaces a value that is already there. But its docs say the lambda may run even if the key is already in the map. So two threads can both connect, every caller ends up with the same client, and the losing connection is dropped without being closed. `computeIfAbsent` is the JDK's atomic version: the function runs at most once per missing key. Its Javadoc asks you to keep that function short, because other updates to the map can wait while it runs. For a slow connect, store a lazy in the map, `clients.computeIfAbsent(id) { lazy { connect(id) } }.value`, so the map is busy only while the cheap `Lazy` object is made."
 },
 "worked": {
  "title": "Make lazily downloaded discount rules safe",
  "steps": [
   {"say": "The shop's program downloads the day's discount rules from head office on first use. The download takes 300 ms, and sometimes it fails. When the shop opens, 200 payments arrive at once. Name the two bugs, then choose a tool before you read on.",
    "code": "public class DiscountRulesProvider {\n    private final RulesClient rulesClient;\n    private DiscountRules rules;                // a plain field\n\n    public DiscountRulesProvider(RulesClient rulesClient) { this.rulesClient = rulesClient; }\n\n    public DiscountRules rules() {              // called by every payment thread\n        if (rules == null) {\n            rules = rulesClient.download();     // 300 ms, and it can fail\n        }\n        return rules;\n    }\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "class DiscountRulesProvider(private val rulesClient: RulesClient) {\n    private var rules: DiscountRules? = null    // a plain field\n\n    fun rules(): DiscountRules {                // called by every payment thread\n        if (rules == null) {\n            rules = rulesClient.download()      // 300 ms, and it can fail\n        }\n        return rules!!\n    }\n}"},
   {"say": "First, check-then-act: every payment in the first 300 ms sees `null` and starts its own download. Second, a plain field: a payment thread can see the reference before the rules' fields. Now the tool. Not the holder: the field belongs to one object, and a failed download must be tried again on the next payment, not turned into `NoClassDefFoundError`. A volatile double check fits, and in Kotlin `by lazy` is that double check.", "code": "", "lang": ""},
   {"say": "Write it with a label on each step. In Kotlin the whole thing is one line, and the retry after a failure comes from the standard library.",
    "code": "public class DiscountRulesProvider {\n    private final RulesClient rulesClient;\n    private volatile DiscountRules rules;               // 1. volatile: the fast path needs the edge\n\n    public DiscountRulesProvider(RulesClient rulesClient) { this.rulesClient = rulesClient; }\n\n    public DiscountRules rules() {\n        DiscountRules r = rules;                        // 2. fast path: one volatile read\n        if (r != null) return r;\n        synchronized (this) {                           // 3. slow path: one download at a time\n            r = rules;\n            if (r == null) {                            // 4. check again: someone may have won\n                r = rulesClient.download();             //    if this throws, nothing is stored\n                rules = r;                              // 5. publish the finished rules\n            }\n            return r;\n        }\n    }\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "class DiscountRulesProvider(private val rulesClient: RulesClient) {\n    // SYNCHRONIZED by default: steps 1 to 5 of the Java version, plus a retry if download() throws\n    val rules: DiscountRules by lazy { rulesClient.download() }\n}"},
   {"say": "Ask one more question: does every payment need the rules anyway? Then lazy buys you a slow first payment, and a failure you discover on the first customer instead of at startup. Download the rules when the program starts and publish them through a volatile field, as in Safe publication. Keep lazy for values that some calls never need.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Three lazy initializers that build exactly once",
  "minutes": 13,
  "files": [
   "labs/jmm/src/main/java/workbench/jmm/l05/DoubleCheckedLazy.java",
   "labs/jmm/src/main/java/workbench/jmm/l05/CardBinTable.java",
   "labs/jmm/src/main/java/workbench/jmm/l05/IssuerClients.java"
  ],
  "run": "./gradlew :jmm:test --tests 'workbench.jmm.l05.*'",
  "steps": [
   "Meet the classes. `DoubleCheckedLazy` is a general lazy value that you'll write from scratch. `CardBinTable` is this lesson's card table, built with check-then-act. `IssuerClients` keeps one connection per card issuer, made on first use with a `get` and then a `put`.",
   "Run the tests once. All six fail: the `DoubleCheckedLazy` tests hit the TODO or find no volatile field, the card table gets built more than once, and one issuer gets connected more than once.",
   "Write `DoubleCheckedLazy`: a volatile field for the value, a field for the initializer, a fast path with one volatile read, and a `synchronized` slow path that checks again. Set the initializer to null once it has run.",
   "Rewrite `CardBinTable.instance()` with the holder class idiom. Keep `creations()` as it is: calling it must not build the table.",
   "Fix `IssuerClients.clientFor` with one map call, so each issuer is connected exactly once.",
   "Run the tests until all six pass, then twice more."
  ],
  "hints": [
   "The initializer field is only read and written inside the lock, so it doesn't need to be volatile. The value field is read outside the lock, so it does.",
   "In `CardBinTable`, delete the static `instance` field and add `private static final class Holder { static final CardBinTable INSTANCE = new CardBinTable(); }`. Ask yourself why calling `creations()` doesn't initialize Holder.",
   "`ConcurrentHashMap.computeIfAbsent` runs the function at most once per missing key. The compare block shows why Kotlin's `getOrPut` would not be enough."
  ],
  "done_when": "All six tests in `LazyInitTest` pass, three runs in a row."
 },
 "drill": {
  "title": "Holder and volatile double check from memory",
  "minutes": 5,
  "prompt": "Close this page. Write (1) a static `CardBinTable.instance()` with the holder class idiom, and (2) a `printer()` method on a `Till` that connects to the printer on first use, with double-checked locking. Mark the line that needs volatile and say why. Then compare with the answer. Did you read the volatile field only once on the fast path?",
  "answer": {"lang": "java", "src": "public final class CardBinTable {\n    private CardBinTable() { /* read the BIN file */ }\n\n    private static final class Holder {\n        static final CardBinTable INSTANCE = new CardBinTable();   // built once, under the class-init lock\n    }\n\n    public static CardBinTable instance() { return Holder.INSTANCE; }\n}\n\npublic final class Till {\n    private final Shop shop;\n    private volatile ReceiptPrinter printer;   // volatile: the fast path reads it without the lock\n\n    public Till(Shop shop) { this.shop = shop; }\n\n    public ReceiptPrinter printer() {\n        ReceiptPrinter p = printer;            // one volatile read\n        if (p != null) return p;\n        synchronized (this) {\n            p = printer;                       // check again under the lock\n            if (p == null) {\n                p = shop.connectPrinter();\n                printer = p;                   // a volatile write publishes the finished printer\n            }\n            return p;\n        }\n    }\n}",
             "alt": {"lang": "kotlin", "src": "class CardBinTable private constructor() {\n    private object Holder {\n        val INSTANCE = CardBinTable()      // built once, on first access to Holder\n    }\n\n    companion object {\n        fun instance(): CardBinTable = Holder.INSTANCE\n    }\n}\n\nclass Till(private val shop: Shop) {\n    @Volatile private var printer: ReceiptPrinter? = null   // the fast path reads it without the lock\n\n    fun printer(): ReceiptPrinter {\n        printer?.let { return it }         // one volatile read\n        synchronized(this) {\n            printer?.let { return it }     // check again under the lock\n            val p = shop.connectPrinter()\n            printer = p                    // a volatile write publishes the finished printer\n            return p\n        }\n    }\n    // in everyday Kotlin: val printer by lazy { shop.connectPrinter() }\n}"}}
 },
 "recap": [
  "Naive lazy initialization is check-then-act on a plain field: it can build twice and publish a half-built object.",
  "Double-checked locking without volatile builds once but is still broken: the fast path, which takes no lock, has no edge to the write.",
  "With a volatile field, double-checked locking is correct. Read the field once into a local, keep both checks, and use a sentinel if the value can be null.",
  "The holder class idiom rides on class initialization: lazy, locked by the JVM, free after the first call. It's for statics only, and it never retries after a failure.",
  "Kotlin's `by lazy` is a volatile double check with a sentinel and a retry on failure. PUBLICATION may run the initializer several times; NONE is for one thread only.",
  "The limit: every lazy tool makes the first caller wait and hides failures until first use. If nearly every call needs the value, build it at startup."
 ],
 "closing": "We started with a shop whose stockroom opens for the first customer, and two assistants who both went to open it. One key on a hook fixed that, at a price, and the double check got the price back. Only an OPEN sign hung last, a volatile field, kept customers out of the dark. Then the JVM opened rooms for us, and Kotlin's `lazy` did the double check in one word.\n\nNow search your own code for `== null` followed by `synchronized`. Each one is a double check, and its field must be `volatile`.\n\nNext, we'll take volatile's release and acquire apart, and label each read and write with exactly the care it needs.",
 "quiz": [
  {
   "q": "A double-checked singleton has a volatile field. A teammate removes `volatile` because \"the write already happens inside synchronized\", and the tests stay green. What do you tell them?",
   "options": [
    "That's fine: leaving the synchronized block publishes the object to every thread",
    "A thread on the fast path takes no lock, so it has no edge to that write and can get a half-built object; the test machines are x86, which rarely shows it",
    "It can now build two instances",
    "It will deadlock when many threads call it"
   ],
   "answer": 1,
   "why": "Leaving a lock creates an edge only to threads that later take the same lock. The fast path takes no lock, so only a volatile read gives it an edge. The second check still prevents two builds, so option 3 is wrong, and the bug just doesn't show on most x86 runs."
  },
  {
   "q": "Each `Till` object needs its own connection to its receipt printer, made on first use. Connecting fails when the printer is switched off, and the next sale should try again. Which tool fits?",
   "options": [
    "The holder class idiom",
    "An enum singleton",
    "Double-checked locking on a volatile field, or Kotlin `by lazy`",
    "`by lazy(LazyThreadSafetyMode.NONE)`"
   ],
   "answer": 2,
   "why": "The holder and the enum are static, one per program, and a failed class initialization is permanent: later calls get NoClassDefFoundError. A double check stores nothing when the initializer throws, so the next call tries again, and Kotlin's `lazy` promises the same retry. NONE is unsafe on a till that several threads share."
  },
  {
   "q": "`Rates` has `static final Rates INSTANCE = new Rates();`, a constructor that prints `built`, and a static method `currency()` that returns \"EUR\". `main` prints `start`, then prints `Rates.currency()`. What is the output?",
   "options": [
    "start, built, EUR",
    "start, EUR, and `built` only when INSTANCE is first read",
    "built, start, EUR, because static fields are set when the JVM starts",
    "start, EUR, built"
   ],
   "answer": 0,
   "why": "Calling a static method is an active use, so the JVM initializes `Rates` first, and that runs `new Rates()`. Class initialization is lazy per class, not per field. A holder class is how you make the instance wait for its own first use."
  },
  {
   "q": "A shared Kotlin object has `val pool by lazy(LazyThreadSafetyMode.PUBLICATION) { ConnectionPool(size = 20) }`, where `ConnectionPool` opens 20 network connections. A burst of requests arrives right after startup. What can happen?",
   "options": [
    "Nothing bad: PUBLICATION means the pool is published safely, so it's built once",
    "Different callers keep using different pools",
    "The callers deadlock",
    "Several threads can each open a pool of 20 connections; one pool is kept and the others are dropped without being closed"
   ],
   "answer": 3,
   "why": "PUBLICATION lets the initializer run on several threads at once and keeps one result, so everyone does end up with the same pool (option 2 is wrong). The extra pools were still created, and their connections leak. Anything with side effects belongs in the default SYNCHRONIZED mode."
  },
  {
   "q": "From Safe publication, final fields and escaping this: a double-checked singleton without volatile, but every field of the singleton is `final`. What can a thread on the fast path see?",
   "options": [
    "null, which sends it to the slow path, or the complete object; the code is still fragile, because one non-final field added later breaks it",
    "A half-built object, just like the non-final case",
    "Always null, so every call takes the lock",
    "Two different instances"
   ],
   "answer": 0,
   "why": "Final fields are seen as the constructor left them, even through a data race, so the race on the reference does no harm. jcstress `Singleton_07` shows no failures with a final field and failures without one. Relying on that is brittle; add volatile.",
   "from": "jmm-04"
  }
 ],
 "flashcards": [
  {"front": "Why is double-checked locking without volatile broken?", "back": "The fast path reads the field without the lock, so it has no happens-before edge to the write. A thread can see the reference before the constructor's writes and use a half-built object."},
  {"front": "What one change makes double-checked locking correct?", "back": "Declare the field `volatile` (`@Volatile` in Kotlin). The volatile write publishes the finished object; the volatile read on the fast path sees it whole."},
  {"front": "In the holder class idiom, what does the locking?", "back": "The JVM's class initialization. `Holder` is initialized once, under a JVM lock, the first time `Holder.INSTANCE` is read."},
  {"front": "A holder's initializer throws on the first call. What does the second call get?", "back": "`NoClassDefFoundError: Could not initialize class ...$Holder`. Class initialization never retries; only a restart does."},
  {"front": "What does `val x by lazy { ... }` compile to, and which mode does it use?", "back": "A `private final kotlin.Lazy x$delegate` field. The default mode is SYNCHRONIZED: double-checked locking on a volatile field."},
  {"front": "LazyThreadSafetyMode.PUBLICATION vs SYNCHRONIZED?", "back": "PUBLICATION may run the initializer on several threads at once and keeps one result. SYNCHRONIZED runs it once while the other callers wait."},
  {"front": "Kotlin `concurrentMap.getOrPut(k) { connect() }`: can `connect()` run twice for one key?", "back": "Yes. It never replaces a value, but the lambda may run on two threads. `computeIfAbsent` runs it at most once per missing key."}
 ],
 "terms": [
  {"term": "Lazy initialization", "plain": "Building a value the first time it's needed instead of at startup."},
  {"term": "Double-checked locking", "plain": "Check without a lock, then lock and check again before building. Correct only with a volatile field."},
  {"term": "Fast path", "plain": "The first check in double-checked locking, which reads the field without taking the lock."},
  {"term": "Holder class idiom", "plain": "Keep the instance in a private nested class, so the JVM builds it on the first call, once, under its class-initialization lock."},
  {"term": "Class initialization", "plain": "The JVM running a class's static initializers once, before the class's first active use."},
  {"term": "Enum singleton", "plain": "A one-constant enum used as a singleton; serialization and reflection can't make a second one."},
  {"term": "Sentinel", "plain": "A private marker object meaning \"not set yet\", so a real null result can be kept too."},
  {"term": "LazyThreadSafetyMode", "plain": "Kotlin's choice for `lazy`: SYNCHRONIZED (once, others wait), PUBLICATION (maybe many runs, one result), NONE (one thread only)."}
 ],
 "explain_back": {
  "prompt": "A teammate asks: \"In our double-checked locking, the write to `table` happens inside a synchronized block. Why does the field still need to be volatile?\" Explain it in your own words.",
  "answer": "The synchronized block only gives an edge to threads that take the same lock. The whole point of double-checked locking is that the fast path doesn't take the lock: once `table` is set, callers read it and return. That read has no edge to the write. So the JIT and the processor are free to let the reference become visible before the constructor's writes, and a caller can get a table that isn't null but isn't built either. Making the field volatile turns the write into a release and the fast-path read into an acquire, so a thread that sees the reference also sees everything written before it. The lock is still needed, for a different job: making sure only one thread builds the table."
 },
 "deeper": {
  "minutes": 10,
  "body": "A lazy object can itself reach another thread through a race, and then its own fields matter. Kotlin's `SynchronizedLazyImpl` keeps its initializer in a field that isn't final, because it sets that field to null after the first run. The jcstress sample `Lazy_01_BrokenFactory` shows what a non-final factory field costs. On AArch64, the sample handed the lazy object itself to another thread through a plain field. That thread sometimes saw the factory as null and failed with an internal error, and in one sample the factory ran twice. `by lazy` doesn't hit this in practice, because the compiler keeps the `Lazy` in a private final `x$delegate` field, and final fields are safe once the owner's constructor has finished. If you write your own lazy wrapper and also want to drop the initializer, `Lazy_05_WrapperOneShot` shows the fix: a final field pointing to a small wrapper that holds the factory.\n\nClass initialization has one more rule worth knowing. Reading a `static final` field that is a compile-time constant, such as `static final int MAX_BINS = 3`, doesn't initialize the class at all: `javac` copies the value into the caller. That's why a holder only triggers on fields like `INSTANCE`, whose value is computed while the program runs.\n\nThe JDK is growing its own answer. JDK 25 previewed stable values (JEP 502). JDK 26 renamed the idea lazy constants (JEP 526, a second preview), and JDK 27 has a third preview (JEP 531). It's a JDK type for a value that is computed at most once and that the JIT may then treat as a constant, which a volatile field never can be. It's a preview API, a feature you switch on with `--enable-preview` and that may still change, so it stays out of these labs. It's worth following if you write libraries.\n\nFinally, the history. \"The Double-Checked Locking is Broken\" declaration, signed by memory model researchers and JVM engineers before Java 5, explains why no clever trick could save double-checked locking under the old memory model. The JSR-133 memory model of Java 5 fixed it by giving volatile its acquire and release meaning, which is the fix you used today."
 },
 "sources": [
  {"title": "jcstress sample Singleton_07_BrokenNonVolatileDCL", "url": "https://github.com/openjdk/jcstress/blob/master/jcstress-samples/src/main/java/org/openjdk/jcstress/samples/primitives/singletons/Singleton_07_BrokenNonVolatileDCL.java"},
  {"title": "Java Language Specification, chapter 12 (12.4 initialization of classes and interfaces)", "url": "https://docs.oracle.com/javase/specs/jls/se25/html/jls-12.html"},
  {"title": "Kotlin docs: delegated properties, lazy properties", "url": "https://kotlinlang.org/docs/delegated-properties.html"},
  {"title": "LazyThreadSafetyMode (Kotlin API)", "url": "https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/-lazy-thread-safety-mode/"},
  {"title": "The \"Double-Checked Locking is Broken\" Declaration", "url": "https://www.cs.umd.edu/~pugh/java/memoryModel/DoubleCheckedLocking.html"}
 ]
}
out = ROOT / "content/lessons/jmm-05.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
