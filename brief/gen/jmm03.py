import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/jmm/src"
P = "java/workbench/jmm/l03"
K = "kotlin/workbench/jmm/l03"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"{lab}/demo/{P}/{name}.java"
kdemo = lambda name: f"{lab}/demo/{K}/{name}.kt"
run = lambda name: f"./gradlew :jmm:demo -Pmain=workbench.jmm.l03.{name}"


def code(name, title=None):
    return {"lang": "java", "title": f"{name}.java", "src": read(demo(name)), "run": run(name), "file": demo(name),
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(kdemo(name)), "run": run(name + "Kt"), "file": kdemo(name)}}


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


def text(t):
    return f"```text\n{t}\n```"


def para(*parts):
    return "\n\n".join(parts)


SIM = {
 "title": "The last seat on the tour, with every field volatile",
 "intro": "Both fields are volatile. status 1 means one seat is left and 2 means the tour is full. You are the scheduler: click a thread to run its next line. Can you sell the last seat twice?",
 "vars": {"status": 1, "sold": 0},
 "threads": [
  {"name": "T1", "steps": [
   {"op": "check", "var": "status", "eq": 1, "code": "if (status != SEAT_LEFT) return false;"},
   {"op": "read", "var": "sold", "reg": "r", "code": "int r = sold;"},
   {"op": "add", "reg": "r", "n": 1, "code": "r = r + 1;"},
   {"op": "write", "var": "sold", "reg": "r", "code": "sold = r;"},
   {"op": "set", "var": "status", "n": 2, "code": "status = FULL;"}]},
  {"name": "T2", "steps": [
   {"op": "check", "var": "status", "eq": 1, "code": "if (status != SEAT_LEFT) return false;"},
   {"op": "read", "var": "sold", "reg": "r", "code": "int r = sold;"},
   {"op": "add", "reg": "r", "n": 1, "code": "r = r + 1;"},
   {"op": "write", "var": "sold", "reg": "r", "code": "sold = r;"},
   {"op": "set", "var": "status", "n": 2, "code": "status = FULL;"}]}
 ],
 "goal": {"var": "sold", "eq": 2, "say": "Both threads passed the check before either set FULL: two tickets for one seat. Every read and write was volatile and visible at once. The check and the act were still two steps."}
}

OPENING = """A small museum has one front door and four gates behind it. On the door hangs a sign, OPEN or CLOSED, and beside it a board shows today's visitor count. The guards have one rule: never trust your memory, always read the door. When someone comes in, the guard at that gate reads the count on the board and writes the number one higher.

The museum's program works the same way. Four threads, one per gate, share the fields `open` and `visitors`, and both are `volatile`, the keyword that fixed the stop loop in lesson 1 of this track. So every thread always reads the newest value. Yet after four million visitors, the count is hundreds of thousands short. It's a very popular museum, with a very wrong count.

The trap is easy: `volatile` fixed the stop loop so neatly that it looks like the fix for anything shared. Happens-before showed what it promises. In this lesson, we'll list what `volatile` gives you and watch it lose visitors anyway. Then we'll sort fields into those where it's enough and those that need more, and find the edges of what it covers. Before we start, make a guess, and keep it in mind."""

S0 = para(
    "The museum's door shows what `volatile` does well. The sign on the door is a volatile field. Every guard reads it at the door itself, every time, and never from a note in a pocket. Declaring a field `volatile` gets you three things, and you've already used two of them in this track.",
    "The first is **visibility**: a volatile read sees the latest volatile write to that field. The JIT, the part of the JVM that compiles busy code while it runs, can't keep the value on its notepad: a register inside the core, the part of the processor that runs one thread. Nor can it move the read out of a loop. That was the stop flag in lesson 1 of this track.",
    "The second is **ordering**. Before the morning guard turns the sign to OPEN, he switches on the lights and opens the display cases. Whoever reads OPEN may walk in and find everything ready. In code, a volatile write is a release: plain writes that come before it in program order, the order of lines within one thread, can't move after it. A volatile read is an acquire: plain reads that come after it can't move before it. That's the piggybacking from Happens-before, where plain writes ride along on a volatile one:",
    pair('''config = load();        // plain write: stays before the volatile write
version = 42;           // volatile write (release)

if (version == 42) {    // volatile read (acquire), in another thread
    use(config);        // plain read: stays after it, and sees the config
}''', '''config = load()         // plain write: stays before the volatile write
version = 42            // @Volatile write (release)

if (version == 42) {    // @Volatile read (acquire), in another thread
    use(config)         // plain read: stays after it, and sees the config
}'''),
    "The third is **one order for all volatile accesses**. Every thread agrees on a single order of all the volatile reads and writes in the program, across every volatile field. That's what forbids the odd result of lesson 1's store-buffer test, in which two threads each write one field, then read the other's, and both read 0. Release and acquire alone don't forbid it, and VarHandles and memory ordering modes, the last lesson of this track, shows the difference.",
    "The ordering helps only threads that both use a volatile field. Picture two guards: one reads the door, and the other reads a note in his pocket. The first guard's care does nothing for the second. `HalfVolatileDemo` runs lesson 1's store-buffer test three ways: with no volatile field, with only `x` volatile, and with both:",
    text("run 1: both read 0 in  plain: 232,147   only x volatile:  67,837   both volatile: 0\nrun 2: both read 0 in  plain: 193,583   only x volatile:  58,514   both volatile: 0\nrun 3: both read 0 in  plain: 168,073   only x volatile:  26,353   both volatile: 0"),
    "With only `x` volatile, the count dropped and stayed well above zero. Thread A's volatile write empties its store buffer, the core's outbox of pending writes, before its read. But thread B wrote a plain `y`, and that write can still wait in B's outbox while B reads `x`. Only when both fields are volatile does the count reach 0.",
    "You may wonder what all this costs. Less than people fear. On x86 processors, a volatile read compiles to an ordinary read of memory; the only cost is that the JIT can't optimize around it. A volatile write costs more, because HotSpot follows it with an instruction that empties the store buffer. On ARM processors, HotSpot uses special load-acquire and store-release instructions instead. For a flag read on every request, the price is tiny next to a single call to a slow web service.",
    "**A volatile field gives fresh reads, ordered writes and one order that every thread agrees on. Both sides must use it.**",
    "So far the sign on the door has done everything we asked. Let's ask it to count.",
)

S1 = para(
    "Here's the museum's counter, the bug from the warm-up:",
    pair('''private volatile int visitors;

void onVisitor() {
    visitors++;   // read, add one, write: three steps
}''', '''@Volatile private var visitors = 0

fun onVisitor() {
    visitors++    // read, add one, write: three steps
}'''),
    "`volatile` makes the read fresh and the write visible. It does nothing about the gap between them. Let's trace the smallest case, with the count at 41:",
    "1. The thread for gate 1 reads `visitors`: 41.\n2. The thread for gate 2 reads `visitors`: 41.\n3. Gate 1 adds one and writes 42.\n4. Gate 2 adds one and writes 42.",
    "Two visitors came in, and the count moved by one. Each of those four accesses was perfectly volatile, and the museum still lost a visitor. A guard who comes along later reads 42 and carries on, so nothing in the program ever learns that someone went missing. That's the lost update from Race conditions, and `volatile` doesn't touch it.",
    "`VolatileCounterDemo` plays out the busy day. Four threads each add 1,000,000 to four kinds of counter: a plain `int`, a volatile `int`, an `AtomicInteger` and a `LongAdder`. One run printed:",
    text("expected 4,000,000 each\nplain 3,987,596   volatile 3,348,221   atomic 4,000,000   adder 4,000,000"),
    "Both the plain and the volatile counters came out short. The plain one looks less wrong in this run, and that proves nothing. The JIT may keep a plain counter on its notepad and add to it there for a while, which changes how often the threads collide. In a run of the Kotlin twin, the plain counter even came out exact while the `@Volatile` one lost 985,479. Both are broken, just in different patterns.",
    "The fix is a single step that reads and writes as one. An **atomic** operation is one that other threads see either not started or completely done, never halfway:",
    pair('''private final AtomicInteger visitors = new AtomicInteger();

void onVisitor() {
    visitors.incrementAndGet();   // one atomic read-modify-write
}''', '''private val visitors = AtomicInteger()

fun onVisitor() {
    visitors.incrementAndGet()    // one atomic read-modify-write
}'''),
    "For a counter that many threads hit hard and that you only read now and then, such as a statistic, `LongAdder` is faster still. It spreads the additions over several cells and adds them up when you ask, as Atomics and compare-and-set showed. A lock works too, and it's the only choice once an update touches more than one field.",
    "The same trap hides in any compound action on a volatile, any group of steps that must happen together: `if (balance >= amount) balance -= amount`, `max = Math.max(max, x)`, `if (state == OPEN) state = CLOSED`. Every one of them reads, decides and writes as separate steps.",
    "**`volatile` makes each read and each write visible. It never makes two of them one step.**",
    "So a volatile counter loses visitors. That doesn't make `volatile` useless. It means we need to know which fields it's enough for.",
)

ASIDE = {
    "title": "Is an AtomicInteger just a volatile int with extra methods?",
    "body": "Nearly. Its `get()` and `set()` have the same memory effects as reading and writing a volatile `int`, so switching loses nothing. What it adds is read-modify-write in one step: `incrementAndGet`, `compareAndSet`, `updateAndGet` and their relatives. On x86, `incrementAndGet` becomes one processor instruction, the `lock xadd` from Atomics and compare-and-set. The functional ones, such as `updateAndGet`, retry a compare-and-set in a loop, so the function you pass may run more than once and must have no side effects.",
}

S2 = para(
    "Make every field volatile, and the museum can still sell its last seat twice. The evening tour has one seat left. The sale code checks that a seat is left, adds one to `sold`, then marks the tour full. Two threads can both pass the check before either marks the tour full, and every read and write along the way is a correct volatile access. That's check-then-act, the second shape of race from Race conditions: test a condition, then act as if it still holds. `volatile` doesn't help with it either. The simulator below lets you sell the seat twice by hand.",
    "So the useful question is: which fields is `volatile` enough for? It's the right tool when all three of these hold:",
    "- Only one thread writes the field, or every write sets a value that doesn't depend on the current one.\n- The field isn't part of a rule that involves other fields.\n- Readers need the latest value, and nothing more.",
    "Those three conditions cover more fields than you'd think. The sign on the museum door is one: one guard flips it, and nobody works out OPEN from the old value. So are a stop flag, a status that one thread moves forward, and the time of the last heartbeat (a regular \"I'm still alive\" signal from one thread). So is a gauge that one thread updates, such as how many jobs wait in the printer's queue. It also covers a reference to an immutable object (one that never changes after it's built) when one thread replaces the whole object, like the shop's price board in Don't share. Readers grab the current board with one volatile read, and the board itself never changes.",
    "The moment a decision needs a read and then a write based on what was read, `volatile` stops being enough. One variable with many writers takes an atomic class: `incrementAndGet`, `compareAndSet`, `updateAndGet`. Several variables that must change together, or a check that spans them, take a lock.",
    "| Shape of the field | Tool |\n|---|---|\n| One writer, readers need the latest value | `volatile` |\n| Many writers, one variable, read-modify-write | `AtomicInteger`, `AtomicLong`, `LongAdder` |\n| Two or more fields under one rule | a lock around every read and write |\n| A whole immutable object, replaced now and then | a `volatile` reference or `AtomicReference` |",
    "One mixed pattern is worth knowing. If writes are rare and reads are frequent, make the writes `synchronized` and the field `volatile`. Writers keep each other out through the lock, so `+=` is safe, and readers pay only for one volatile read:",
    pair('''private volatile long balance;

public long balance() { return balance; }                          // readers: one volatile read
public synchronized void apply(long delta) { balance += delta; }   // writers: the lock makes += safe''', '''@Volatile private var balance = 0L

fun balance(): Long = balance                                 // readers: one volatile read
@Synchronized fun apply(delta: Long) { balance += delta }     // writers: the lock makes += safe'''),
    "**One writer, and no read before the write: `volatile` is enough. Anything more needs an atomic or a lock.**",
    "Try the simulator now: both fields are volatile, and the last seat still sells twice. After that, one question is left. How much does a single volatile field actually cover?",
)

S3 = para(
    "Three details trip people up once the basics are clear, and the museum door explains all three: a sign covers itself, and nothing behind it.",
    "First, `long` and `double`. The Java Language Specification (JLS), section 17.7, lets the JVM treat a write to a non-volatile `long` or `double` as two separate 32-bit writes, one to each half. A racing reader could then see the top half of one value and the bottom half of another: a **torn read**. Writes and reads of volatile `long` and `double` are always atomic, and so are references and every type of 32 bits or less. jcstress, the tool from Testing and debugging that runs tiny tests millions of times, shows torn longs on a 32-bit x86 JVM. A reader saw `-4294967296` and `4294967295` when the only values ever written were 0 and -1. 64-bit HotSpot writes a `long` in one instruction, so you won't see tearing there, but the JLS doesn't promise it. In practice this rarely matters on its own. A `long` that two threads share needs `volatile` for visibility anyway, and you get atomicity with it.",
    "Second, a volatile reference covers the reference, and nothing inside the object. Think of a sign on the door that says which room today's exhibition is in. Changing the sign is a volatile write. Moving the exhibits around inside the room is not, however volatile the sign. So `tours.add(t)` on a `volatile List<Tour> tours` is not a volatile write. It's a call on whatever list the field points to, with no link for readers and no protection for the list. Replace the whole object instead:",
    pair('''private volatile List<Tour> tours = List.of();   // volatile covers the reference only

void replaceTours(List<Tour> fresh) {
    tours = List.copyOf(fresh);                  // one volatile write of an unchangeable list
}''', '''@Volatile private var tours: List<Tour> = emptyList()   // @Volatile covers the reference only

fun replaceTours(fresh: List<Tour>) {
    tours = fresh.toList()                               // one write of a copy nobody else holds
}'''),
    "The jcstress sample `AdvancedJMM_05_MisplacedVolatile` shows the price of getting this wrong. A volatile field held a holder object, but the new value went into a plain field inside the holder. On a 64-bit ARM machine, a reader saw the new object's field still at 0 in 553 samples.",
    "Third, arrays. A `volatile long[]` makes the array reference volatile and leaves every element plain: a sign that names a room full of plain lockers. For volatile elements, use `AtomicLongArray`, `AtomicIntegerArray` or `AtomicReferenceArray`:",
    pair('''class GateCounts {
    private volatile long[] counts = new long[4];               // volatile reference, plain elements
    private final AtomicLongArray safe = new AtomicLongArray(4);   // each element acts like a volatile

    void record(int gate, long visitors) {
        counts[gate] = visitors;     // plain element write: no link for readers
        safe.set(gate, visitors);    // volatile element write: readers of safe.get() see it
    }
}''', '''class GateCounts {
    @Volatile private var counts = LongArray(4)     // volatile reference, plain elements
    private val safe = AtomicLongArray(4)           // each element acts like a volatile

    fun record(gate: Int, visitors: Long) {
        counts[gate] = visitors     // plain element write: no link for readers
        safe.set(gate, visitors)    // volatile element write: readers of safe.get() see it
    }
}'''),
    "Check yourself: a `volatile Map<String, Long> prices` holds a `HashMap`, and refresher threads call `prices.put(item, cents)`. Does a reader that calls `prices.get(item)` see the new price? Nothing promises it. The only volatile access is the read of the field. The `put` writes inside the map, and those writes are plain, so no link reaches the reader. Two threads calling `put` at once can also corrupt the `HashMap` itself. Use one writer that replaces the whole map with an unchangeable copy, or a `ConcurrentHashMap`.",
    "**A volatile field covers one variable. The object behind a volatile reference needs protection of its own.**",
    "One case is left: an object built in one thread and handed to others through a field, its insides and all. What are the readers promised to see inside it?",
)

L = {
 "id": "jmm-03",
 "title": "volatile: what it gives you and what it doesn't",
 "minutes": 35,
 "goal": "By the end you can say exactly what volatile promises, show why it doesn't make count++ safe, and choose between volatile, an atomic and a lock for any shared field.",
 "opening": OPENING,
 "warmup": {
  "q": "The museum counts visitors with `private volatile int visitors;` and `visitors++` on 4 threads, one per gate, each adding 1,000,000. At closing time, what does `visitors` hold?",
  "options": [
   "Exactly 4,000,000, because volatile makes every read and write go straight to memory",
   "Usually less than 4,000,000",
   "Exactly 4,000,000 on x86, less on ARM",
   "It won't compile: `++` isn't allowed on a volatile field"
  ],
  "answer": 1,
  "why": "`visitors++` is a read, an add and a write. `volatile` makes each of those fresh and visible, but two threads can still read the same count and both write the count plus one. The first option is the classic belief: \"goes to memory\" is true, and it doesn't make three steps one."
 },
 "sections": [
  {
   "h": "What volatile gives you: fresh reads, ordered writes and one order for all",
   "body": S0,
   "try": {
    "title": "Make only one side volatile",
    "minutes": 4,
    "steps": [
     "Read `HalfVolatileDemo` (either language). It runs the store-buffer test three ways: no volatile field, only `x` volatile, and both volatile.",
     "Predict the middle column before you run it: does one volatile field save both threads?",
     "Run it with the command below, twice, and compare the columns."
    ],
    "code": code("HalfVolatileDemo"),
    "expect": "Plain fields show both threads reading 0 in a large share of trials. With only `x` volatile, the count drops but stays well above zero (tens of thousands here): thread B's write to the plain `y` can still wait in its store buffer while B reads `x`. Only when both fields are volatile does the count go to 0."
   }
  },
  {
   "h": "What volatile doesn't give you: count++ is still three steps",
   "body": S1,
   "aside": ASIDE,
   "try": {
    "title": "Count visitors four ways",
    "minutes": 4,
    "steps": [
     "Read `VolatileCounterDemo` (either language). Four threads each add 1,000,000 to a plain counter, a volatile counter, an `AtomicInteger` and a `LongAdder`.",
     "Predict which of the four reach 4,000,000, and whether volatile loses fewer updates than plain.",
     "Run it twice with the command below and compare the runs. If you can, run the Kotlin twin too."
    ],
    "code": code("VolatileCounterDemo"),
    "expect": "The atomic and the adder print exactly 4,000,000 every time. Plain and volatile both come out short, often by hundreds of thousands, and which of the two loses more changes from run to run (the plain one is now and then exact). The volatile counter is not \"more correct\"; it's wrong in a different pattern."
   }
  },
  {
   "h": "When volatile is enough, and when you need an atomic or a lock",
   "body": S2,
   "sim": SIM,
   "try": {
    "title": "Pick the tool",
    "minutes": 3,
    "steps": [
     "Choose `volatile`, an atomic or a lock for each field, and say why in one line.",
     "(a) `boolean closedForCleaning`, flipped from the manager's screen, read by every gate thread.",
     "(b) `int insideNow`, one higher when someone enters and one lower when they leave, updated by the gate threads.",
     "(c) `long dailyLimitCents` and `long spentTodayCents` on a shop's card account, checked together before each payment.",
     "(d) `Map<String, Long> prices`, replaced every minute by a refresher thread with a new map that nobody changes."
    ],
    "expect": "(a) `volatile`: one writer, and the new value doesn't depend on the old one. (b) An atomic (`AtomicInteger` or `LongAdder`): many writers doing read-modify-write. (c) A lock: one rule spans two fields and needs check-then-act. (d) A `volatile` reference to an unchangeable map, built with `Map.copyOf` before it's published."
   }
  },
  {
   "h": "What volatile covers: one variable, all 64 bits, and nothing behind it",
   "body": S3
  }
 ],
 "compare": {
  "title": "A volatile snapshot reference in Java and Kotlin",
  "java": {"title": "PriceBoard.java", "src": "public class PriceBoard {\n    // replaced whole, never changed: one volatile read gives a consistent snapshot\n    private volatile Map<String, Long> prices = Map.of();\n\n    // one refresher thread\n    public void refresh(Map<String, Long> fresh) {\n        prices = Map.copyOf(fresh);   // build first, then publish with one volatile write\n    }\n\n    // many till threads\n    public Long priceOf(String item) {\n        return prices.get(item);\n    }\n}"},
  "kotlin": {"title": "PriceBoard.kt", "src": "class PriceBoard {\n    // replaced whole, never changed: one volatile read gives a consistent snapshot\n    @Volatile\n    private var prices: Map<String, Long> = emptyMap()\n\n    // one refresher thread\n    fun refresh(fresh: Map<String, Long>) {\n        prices = fresh.toMap()   // a private copy, then publish with one volatile write\n    }\n\n    // many till threads\n    fun priceOf(item: String): Long? = prices[item]\n}"},
  "note": "Both versions follow the same pattern: build a new map, publish it with one volatile write, and never touch it again. The difference is in the copy. Java's `Map.copyOf` returns a truly unmodifiable map (and rejects nulls). Kotlin's `Map` type is only a read-only view, so the safety comes from `toMap()` making a fresh map that no other code holds. If you passed the caller's map straight through, someone holding a `MutableMap` reference to it could still change it under the readers."
 },
 "worked": {
  "title": "Choose the tools for a circuit breaker",
  "steps": [
   {"say": "A program calls a slow web service, and guards each call with a circuit breaker, which works like the fuse box in a house. After 5 failures in a row, the breaker stops calls to the service, and 30 seconds later it lets them through again. Request threads call `onFailure` and `onSuccess`, and check `allowRequest` before each call. Every field is volatile. For each field, ask: who writes it, and does the write depend on a read?", "code": "class ServiceBreaker {\n    private volatile int consecutiveFailures;   // written by request threads\n    private volatile long openedAtMillis;       // 0 means closed: calls go through\n\n    void onFailure(long now) {\n        consecutiveFailures++;                                             // 1. read-modify-write\n        if (consecutiveFailures >= 5 && openedAtMillis == 0) openedAtMillis = now;   // 2. check-then-act\n    }\n\n    void onSuccess() { consecutiveFailures = 0; }\n\n    boolean allowRequest(long now) {\n        long opened = openedAtMillis;\n        return opened == 0 || now - opened > 30_000;\n    }\n}", "lang": "java", "alt_lang": "kotlin", "alt_code": "class ServiceBreaker {\n    @Volatile private var consecutiveFailures = 0   // written by request threads\n    @Volatile private var openedAtMillis = 0L       // 0 means closed: calls go through\n\n    fun onFailure(now: Long) {\n        consecutiveFailures++                                                  // 1. read-modify-write\n        if (consecutiveFailures >= 5 && openedAtMillis == 0L) openedAtMillis = now   // 2. check-then-act\n    }\n\n    fun onSuccess() { consecutiveFailures = 0 }\n\n    fun allowRequest(now: Long): Boolean {\n        val opened = openedAtMillis\n        return opened == 0L || now - opened > 30_000\n    }\n}"},
   {"say": "`consecutiveFailures` has many writers, and `++` depends on a read, so increments get lost and the breaker trips late. Line 2 reads the counter again, separately, and then reads and writes `openedAtMillis`, so two threads can both see 5 and both set the time. `openedAtMillis` itself is fine as a volatile for the readers in `allowRequest`, which need one value and nothing else.", "code": "", "lang": ""},
   {"say": "Make the counter atomic, and decide on the value it returns. Each `incrementAndGet` returns a different number, so only one thread sees exactly 5 for each run of failures, and only that thread trips the breaker.", "code": "class ServiceBreaker {\n    private final AtomicInteger consecutiveFailures = new AtomicInteger();   // 1. many writers: atomic\n    private volatile long openedAtMillis;                                    // 2. readers need one value: volatile\n\n    void onFailure(long now) {\n        int n = consecutiveFailures.incrementAndGet();   // 3. one atomic step, and keep the result\n        if (n == 5) openedAtMillis = now;                // 4. only one thread sees n == 5\n    }\n\n    void onSuccess() { consecutiveFailures.set(0); }\n\n    boolean allowRequest(long now) {\n        long opened = openedAtMillis;                    // 5. read the volatile once\n        return opened == 0 || now - opened > 30_000;\n    }\n}", "lang": "java", "alt_lang": "kotlin", "alt_code": "class ServiceBreaker {\n    private val consecutiveFailures = AtomicInteger()   // 1. many writers: atomic\n    @Volatile private var openedAtMillis = 0L           // 2. readers need one value: @Volatile\n\n    fun onFailure(now: Long) {\n        val n = consecutiveFailures.incrementAndGet()   // 3. one atomic step, and keep the result\n        if (n == 5) openedAtMillis = now                // 4. only one thread sees n == 5\n    }\n\n    fun onSuccess() { consecutiveFailures.set(0) }\n\n    fun allowRequest(now: Long): Boolean {\n        val opened = openedAtMillis                     // 5. read the volatile once\n        return opened == 0L || now - opened > 30_000\n    }\n}"},
   {"say": "Two habits made this work. Use the value the atomic call returns: calling `incrementAndGet()` and then `get()` would bring the check-then-act gap back. And read a volatile into a local variable once when you use it twice, as `allowRequest` does, so both uses see the same value. When the breaker later grows a half-open state, letting exactly one trial call through while it also resets the counter, two fields change together. That's the point to switch to a lock.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Choose volatile, atomic or lock for a card payment",
  "minutes": 13,
  "files": ["labs/jmm/src/main/java/workbench/jmm/l03/PaymentSession.java"],
  "run": "./gradlew :jmm:test --tests 'workbench.jmm.l03.*'",
  "steps": [
   "Meet `PaymentSession`. It follows one card payment through its life. First the shop reserves the money on the card (the payment is authorized). Then it takes some or all of it (it captures), and later it may give some back (it refunds). Several threads share the object, and the comment above each field says who writes it and who reads it.",
   "Run the tests once. Four of the five fail: two waiting threads never see a write, the attempt counter comes up short, and the money rule breaks.",
   "Try the quick fix first: put `volatile` on every field and run the tests. Two still fail. Before reading on, say which two and why.",
   "Now go field by field. Read the comment that says who writes it and who reads it, choose `volatile`, an atomic or a lock, and add a one-line comment saying why.",
   "Keep every public signature as it is. Run the tests until all five pass, then twice more."
  ],
  "hints": [
   "`status` and `lastHeartbeatMillis` each have one writer, and the new value doesn't depend on the old one.",
   "`attempts++` is read-modify-write with many writers. An `AtomicInteger` lets `attempts()` keep returning `int`.",
   "`tryRefund` reads `capturedCents`, which `tryCapture` writes. Guard both fields with one lock, and take it in the two getters too. A pair of `AtomicLong`s can't keep `refunded <= captured`."
  ],
  "done_when": "All five tests in `PaymentSessionTest` pass, three runs in a row."
 },
 "drill": {
  "title": "A gauge and a counter from memory",
  "minutes": 4,
  "prompt": "Close this page. Write two small classes. `PrinterQueueGauge`: one watcher thread calls `update(long)` with the number of jobs waiting, and display threads call `waiting()`. `RetryCounter`: many threads call `onRetry()`, and a statistics thread calls `retries()`. Use the lightest correct tool for each, and say why in a comment.",
  "answer": {"lang": "java", "src": "// one writer, readers need the latest value: volatile is enough\npublic final class PrinterQueueGauge {\n    private volatile long waiting;   // volatile also keeps the 64-bit write in one piece\n\n    public void update(long jobs) { waiting = jobs; }\n    public long waiting() { return waiting; }\n}\n\n// many writers doing read-modify-write: atomic (LongAdder if it is very busy)\npublic final class RetryCounter {\n    private final AtomicLong count = new AtomicLong();\n\n    public void onRetry() { count.incrementAndGet(); }\n    public long retries() { return count.get(); }\n}",
             "alt": {"lang": "kotlin", "src": "// one writer, readers need the latest value: @Volatile is enough\nclass PrinterQueueGauge {\n    @Volatile private var current = 0L   // also keeps the 64-bit write in one piece\n\n    fun update(jobs: Long) { current = jobs }\n    fun waiting(): Long = current\n}\n\n// many writers doing read-modify-write: atomic (LongAdder if it is very busy)\nclass RetryCounter {\n    private val count = AtomicLong()\n\n    fun onRetry() { count.incrementAndGet() }\n    fun retries(): Long = count.get()\n}"}}
 },
 "recap": [
  "`volatile` gives visibility (fresh reads, visible writes), ordering (release on write, acquire on read) and one order of all volatile accesses that every thread agrees on.",
  "It does not join a read and a write into one step: `count++`, check-then-act and `max = Math.max(max, x)` all still race.",
  "Use `volatile` for one-writer values, flags, timestamps and references to immutable snapshots. Use an atomic for one variable with many writers, and a lock when a rule spans several fields.",
  "Ordering helps only threads that both use the volatile: one volatile field doesn't fix a two-thread protocol.",
  "Non-volatile `long` and `double` may tear under the JLS; volatile ones never do.",
  "The limit: a volatile reference or array covers the reference only, not the object or the elements behind it."
 ],
 "closing": "We started at a museum door where every guard read the sign, and the count still came up short. `volatile` gave every read the latest value, kept the writes in order and put every thread on one timeline. It never made a read and a write one step, and it covered nothing but itself.\n\nNow search your own code for `volatile`. For each field, ask who writes it and whether the new value depends on the old one. A `++`, a `+=` or a check-then-act on it needs an atomic or a lock.\n\nNext, we'll hand a whole object to other threads and ask what they're promised to see inside it: safe publication, final fields, and the constructor that lets `this` escape.",
 "quiz": [
  {
   "q": "Many threads run `balance += amount` on a `volatile long balance`. What can go wrong?",
   "options": [
    "Two threads can read the same balance and both write, so one amount is lost",
    "Nothing: volatile makes the whole statement atomic",
    "The 64-bit write can tear into two halves",
    "Readers may never see the new balance"
   ],
   "answer": 0,
   "why": "`+=` is a read, an add and a write. Volatile makes each step visible and ordered, but it leaves the gap between them. Tearing is ruled out because the field is volatile, and visibility is fine, which is what makes this bug easy to miss."
  },
  {
   "q": "Which of these fields is correctly protected by `volatile` alone?",
   "options": [
    "A visitor counter that every gate thread increments",
    "A reference to an unchangeable `PriceList` that one refresher thread replaces every minute",
    "`limit` and `spent`, which are checked together before every card payment",
    "A `volatile ArrayList<Tour>` that several threads add tours to"
   ],
   "answer": 1,
   "why": "One writer, a whole-object replace, and readers that need only the latest reference: that's exactly volatile's job. The counter needs an atomic, the pair needs a lock, and the volatile list protects only the reference while `ArrayList.add` races."
  },
  {
   "q": "In `HalfVolatileDemo` only `x` is volatile. Why do both threads still sometimes read 0?",
   "options": [
    "The volatile write to `x` is lost",
    "Volatile only works between two volatile fields of the same object",
    "Thread B's plain write to `y` can wait in its store buffer while B reads `x`, so B's own pair of accesses is not ordered",
    "The demo's barrier lets the threads run different trials"
   ],
   "answer": 2,
   "why": "To rule the result out, each thread's write-then-read must stay in order. Thread A's volatile write is followed by an instruction that empties its store buffer, but thread B wrote a plain field, so nothing stops B's read from passing its own write. Make both fields volatile and the count drops to 0."
  },
  {
   "q": "A class has `private volatile long[] balances`. Thread A runs `balances[3] = 500`. Thread B later reads `balances[3]`. What is promised?",
   "options": [
    "B sees 500, because the array is volatile",
    "B sees 500 or 0, but never a torn value",
    "B sees 500 once A releases the array",
    "Nothing about the element: only the array reference is volatile, so this is a plain write and a plain read"
   ],
   "answer": 3,
   "why": "Element accesses of a volatile array are plain accesses. Nothing links A's write to B's read, and a plain `long` element may even tear under the JLS. Use `AtomicLongArray` when elements are shared."
  },
  {
   "q": "From lesson 2 of this track: T1 sets a plain `fee = 25` and then the volatile `ready = true`. T2 sees `ready == true` and then reads `fee`. Why must T2 see 25?",
   "options": [
    "Because `fee` is an `int`, and int writes are atomic",
    "Program order, then the volatile write-to-read handover, then program order again: the links chain, so the write of `fee` happens-before its read",
    "Because volatile writes flush all CPU caches",
    "It doesn't have to; T2 may see 0"
   ],
   "answer": 1,
   "why": "This is piggybacking on the volatile. The write of `fee` comes before the release in T1's program order, and the read comes after the acquire in T2's. Atomicity only rules out half-written values; it says nothing about which value you see.",
   "from": "jmm-02"
  }
 ],
 "flashcards": [
  {"front": "What does a volatile field promise?", "back": "Visibility of the latest write, release and acquire ordering around each access, and one order of all volatile accesses that every thread agrees on."},
  {"front": "Is `count++` on a volatile int atomic?", "back": "No. It's still a read, an add and a write. Use `AtomicInteger.incrementAndGet()` or `LongAdder`."},
  {"front": "When is volatile alone enough for a field?", "back": "When one thread writes it (or writes don't depend on the current value), and the field isn't part of a rule with other fields."},
  {"front": "Two fields must change together under one rule. Volatile, atomic or lock?", "back": "A lock, taken around every read and write of both fields."},
  {"front": "Can a write to a non-volatile `long` tear?", "back": "The JLS allows it to be split into two 32-bit writes. A volatile `long` or `double` is always written and read atomically."},
  {"front": "`volatile List<Tour> tours;` Is `tours.add(t)` from two threads safe?", "back": "No. Volatile covers the reference only. Replace the whole list with an unchangeable copy instead, or use a concurrent collection."},
  {"front": "Are the elements of a `volatile long[]` volatile?", "back": "No, only the array reference. Use `AtomicLongArray` for volatile element access."}
 ],
 "terms": [
  {"term": "Visibility", "plain": "Whether a read in one thread sees a write from another."},
  {"term": "Atomicity", "plain": "An operation happens as one indivisible step that no other thread can split."},
  {"term": "Read-modify-write", "plain": "Read a value, compute a new one from it, write it back. Needs an atomic or a lock when shared."},
  {"term": "Compound action", "plain": "A group of steps that must happen together, such as check-then-act or read-modify-write."},
  {"term": "Torn read", "plain": "Seeing half of one write and half of another, possible for non-volatile long and double under the JLS."},
  {"term": "Single writer", "plain": "A field that only one thread ever writes. Volatile is enough for it."},
  {"term": "Snapshot publication", "plain": "Building a new immutable object and publishing it with one volatile write, instead of changing the old one."},
  {"term": "LongAdder", "plain": "A counter that spreads increments over several cells. Fast when many threads add; its sum is not a snapshot."}
 ],
 "explain_back": {
  "prompt": "A friend asks: \"If volatile makes every read and write go to memory, why does `volatile int retries; retries++` still lose updates?\" Explain in your own words, and say what you would use instead.",
  "answer": "Volatile makes each read see the latest value and each write visible, but `retries++` is still three steps: read, add one, write. Two threads can both read 41 before either writes, and both write 42. Each access was perfectly volatile; the problem is the gap between them, which volatile doesn't close. For one counter with many writers I'd use `AtomicInteger.incrementAndGet()`, which does the read and the write as one atomic step, or `LongAdder` if it's a busy statistics counter. If the update had to touch more than one field, I'd use a lock."
 },
 "deeper": {
  "minutes": 8,
  "body": "Why is the JLS rule for `long` and `double` still there, when 64-bit JVMs never tear? Because the JLS is written for every JVM, including 32-bit ones, and dropping the rule would force those JVMs to use more expensive instructions for every 64-bit access. The `VarHandle` Javadoc states the same rule for its plain mode: plain reads and writes are guaranteed bitwise atomic only for references and for primitive values of at most 32 bits.\n\nA related term you may meet is word tearing: a write to one field or array element changing its neighbor, as some processors would do for single bytes. Java forbids it outright. Every field and every array element is its own variable, so a `byte[]` shared between threads never corrupts the byte next to the one you wrote. Races on that array are still races, of course.\n\nThe mixed pattern from section 3, with `synchronized` writes and volatile reads, has a name. Brian Goetz called it \"the cheap read-write lock trick\" in his article \"Managing volatility\". The same article lists other safe uses of `volatile` that this lesson met: status flags, one-time safe publication, and independent observations, such as the time of the last heartbeat. Read his list as a checklist. If a volatile field in your code fits none of those patterns, look at it twice."
 },
 "sources": [
  {"title": "Java Language Specification, chapter 17 (17.4 memory model, 17.7 long and double)", "url": "https://docs.oracle.com/javase/specs/jls/se25/html/jls-17.html"},
  {"title": "jcstress samples (BasicJMM_02_AccessAtomicity, AdvancedJMM_05_MisplacedVolatile)", "url": "https://github.com/openjdk/jcstress/tree/master/jcstress-samples"},
  {"title": "java.util.concurrent.atomic package (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/atomic/package-summary.html"},
  {"title": "Kotlin API: @Volatile", "url": "https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.concurrent/-volatile/"},
  {"title": "Java Concurrency in Practice, Goetz et al., section 3.1.4 on volatile", "url": "https://jcip.net/"}
 ]
}
out = ROOT / "content/lessons/jmm-03.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
