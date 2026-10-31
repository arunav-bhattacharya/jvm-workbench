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


SIM = {
 "title": "Capture once, with every field volatile",
 "intro": "Both fields are volatile. status 1 means AUTHORIZED and 2 means CAPTURED, and a payment may be captured once. You are the scheduler: can you capture it twice?",
 "vars": {"status": 1, "captured": 0},
 "threads": [
  {"name": "T1", "steps": [
   {"op": "check", "var": "status", "eq": 1, "code": "if (status != AUTHORIZED) return false;"},
   {"op": "read", "var": "captured", "reg": "r", "code": "long r = captured;"},
   {"op": "add", "reg": "r", "n": 60, "code": "r = r + 60;"},
   {"op": "write", "var": "captured", "reg": "r", "code": "captured = r;"},
   {"op": "set", "var": "status", "n": 2, "code": "status = CAPTURED;"}]},
  {"name": "T2", "steps": [
   {"op": "check", "var": "status", "eq": 1, "code": "if (status != AUTHORIZED) return false;"},
   {"op": "read", "var": "captured", "reg": "r", "code": "long r = captured;"},
   {"op": "add", "reg": "r", "n": 70, "code": "r = r + 70;"},
   {"op": "write", "var": "captured", "reg": "r", "code": "captured = r;"},
   {"op": "set", "var": "status", "n": 2, "code": "status = CAPTURED;"}]}
 ],
 "goal": {"var": "captured", "eq": 130, "say": "Both threads passed the check before either set CAPTURED: 130 captured on a 100 authorization. Every read and write was volatile and visible at once. The check and the act were still two steps."}
}

L = {
 "id": "jmm-03",
 "title": "volatile: what it gives you and what it doesn't",
 "minutes": 35,
 "goal": "By the end you can say exactly what volatile guarantees, show why it doesn't make count++ safe, and choose between volatile, an atomic and a lock for any shared field.",
 "warmup": {
  "q": "A payment service counts retries with `private volatile int retries;` and `retries++` from 8 request threads. After 800,000 retries, what does `retries` hold?",
  "options": [
   "Exactly 800,000, because volatile makes every access go straight to memory",
   "Usually less than 800,000",
   "Exactly 800,000 on x86, less on ARM",
   "It won't compile: `++` isn't allowed on a volatile field"
  ],
  "answer": 1,
  "why": "`retries++` is a read, an add and a write. `volatile` makes each of those visible and ordered, but two threads can still read the same value and both write value + 1. The first option is the classic belief: \"goes to memory\" is true, and it doesn't make the three steps one."
 },
 "sections": [
  {
   "h": "volatile gives you visibility and ordering",
   "body": "Declaring a field `volatile` gets you three things, and you've already used two of them in this track.\n\n**Visibility.** A volatile read sees the latest volatile write to that field. The JIT can't keep the value in a register or hoist the read out of a loop. That was the stop flag in lesson 1 of this track.\n\n**Ordering.** A volatile write is a release: plain writes that come before it in program order can't move after it. A volatile read is an acquire: plain reads after it can't move before it. That's the piggybacking from lesson 2 of this track.\n\n```java\nconfig = load();        // plain write: stays before the volatile write\nversion = 42;           // volatile write (release)\n\nif (version == 42) {    // volatile read (acquire), in another thread\n    use(config);        // plain read: stays after it, and sees the config\n}\n```\n\n```kotlin\nconfig = load()         // plain write: stays before the volatile write\nversion = 42            // @Volatile write (release)\n\nif (version == 42) {    // @Volatile read (acquire), in another thread\n    use(config)         // plain read: stays after it, and sees the config\n}\n```\n\n**One order for all volatile accesses.** Every thread agrees on a single order of all volatile reads and writes. That's what forbids the store-buffering outcome from lesson 1 of this track, where both threads read 0. Acquire and release alone don't forbid it; lesson 6 of this track shows the difference.\n\nThe ordering only helps threads that both use the volatile. If thread A writes a volatile `x` and thread B writes a plain `y`, B's write can still sit in its store buffer while B reads `x`. The try-it below measures this.\n\nThe cost is lower than people fear. On x86 a volatile read compiles to an ordinary load; the only cost is that the JIT can't optimize around it. A volatile write costs more, because HotSpot follows it with an instruction that drains the store buffer. On ARM, HotSpot uses dedicated load-acquire and store-release instructions. For a flag read on every request, the price is noise next to one database call.",
   "try": {
    "title": "Make only one side volatile",
    "minutes": 4,
    "steps": [
     "Read `HalfVolatileDemo`. It runs the store-buffering test three ways: no volatile, only `x` volatile, and both volatile.",
     "Predict the middle column before you run: does one volatile field save both threads?",
     "Run it with the command below."
    ],
    "code": code("HalfVolatileDemo"),
    "expect": "Plain fields show both threads reading 0 in a large share of trials. With only `x` volatile the count drops but stays well above zero (tens of thousands here): thread B's write to plain `y` can still wait in its store buffer while it reads `x`. Only when both fields are volatile does the count go to 0."
   }
  },
  {
   "h": "volatile does not make count++ atomic",
   "body": "Here's the bug from the warm-up:\n\n```java\nprivate volatile int retries;\n\nvoid onRetry() {\n    retries++;   // read, add one, write: three steps\n}\n```\n\n```kotlin\n@Volatile private var retries = 0\n\nfun onRetry() {\n    retries++    // read, add one, write: three steps\n}\n```\n\n`volatile` makes the read fresh and the write visible. It does nothing about the gap between them. Two threads read 41, both add one, both write 42. Each of those six accesses was perfectly volatile.\n\nThe research for this track measured it: 4 threads each ran `v++` a million times on a `static volatile int`, and the total came out at 3,681,731 instead of 4,000,000. The same run with a plain `int` came out at 3,997,394. The plain counter looked less wrong in that run, and that proves nothing: the JIT can batch plain increments in a register, which changes how many get lost. Runs for this lesson saw the order flip. Both are broken.\n\nThe fix is a single step that reads and writes as one:\n\n```java\nprivate final AtomicInteger retries = new AtomicInteger();\n\nvoid onRetry() {\n    retries.incrementAndGet();   // one atomic read-modify-write\n}\n```\n\n```kotlin\nprivate val retries = AtomicInteger()\n\nfun onRetry() {\n    retries.incrementAndGet()    // one atomic read-modify-write\n}\n```\n\nFor a counter that many threads hit hard and that you only read now and then (metrics), `LongAdder` is faster still. A lock works too, and it's the only choice once the update touches more than one field.\n\nThe same trap hides in any compound action on a volatile: `if (balance >= amount) balance -= amount`, `max = Math.max(max, x)`, `if (state == OPEN) state = CLOSED`. Every one of them reads, decides and writes as separate steps.",
   "try": {
    "title": "Count four ways",
    "minutes": 4,
    "steps": [
     "Read `VolatileCounterDemo`. Four threads each add 1,000,000 to a plain counter, a volatile counter, an `AtomicInteger` and a `LongAdder`.",
     "Predict which of the four reach 4,000,000, and whether volatile loses fewer updates than plain.",
     "Run it twice with the command below and compare the runs."
    ],
    "code": code("VolatileCounterDemo"),
    "expect": "The atomic and the adder print exactly 4,000,000 every time. Plain and volatile both come out short, often by hundreds of thousands, and which of the two loses more changes from run to run. The volatile counter is not \"more correct\"; it's wrong in a different pattern."
   }
  },
  {
   "h": "When volatile is enough, and when you need more",
   "body": "Volatile is the right tool when all of these hold:\n\n- Only one thread writes the field, or every write sets a value that doesn't depend on the current one.\n- The field isn't part of a rule that involves other fields.\n- Readers need the latest value, nothing more.\n\nThat covers more fields than you'd think: a shutdown flag, a status that one callback thread moves forward, a last-heartbeat timestamp, a Kafka lag gauge that one poller updates. It also covers a reference to an immutable object that one thread replaces whole, such as a rate table refreshed every minute. Readers grab the current table with one volatile read, and the table itself never changes.\n\nThe moment a decision needs a read, then a write based on what you read, volatile stops being enough. One variable with many writers takes an atomic class (`incrementAndGet`, `compareAndSet`, `updateAndGet`). Several variables that must change together, or a check that spans them, take a lock.\n\n| Shape of the field | Tool |\n|---|---|\n| One writer, readers need the latest value | `volatile` |\n| Many writers, one variable, read-modify-write | `AtomicInteger`, `AtomicLong`, `LongAdder` |\n| Two or more fields under one rule | a lock around every read and write |\n| A whole immutable object, replaced now and then | a `volatile` reference or `AtomicReference` |\n\nOne mixed pattern is worth knowing. If writes are rare and reads are hot, make the writes `synchronized` and the field `volatile`. Writers exclude each other through the lock, so `+=` is safe, and readers pay only for one volatile read.\n\n```java\nprivate volatile long balance;\n\npublic long balance() { return balance; }                          // readers: one volatile read\npublic synchronized void apply(long delta) { balance += delta; }   // writers: the lock makes += safe\n```\n\n```kotlin\n@Volatile private var balance = 0L\n\nfun balance(): Long = balance                                 // readers: one volatile read\n@Synchronized fun apply(delta: Long) { balance += delta }     // writers: the lock makes += safe\n```\n\nThe simulator shows the limit. Both fields are volatile, yet the capture-once rule fails.",
   "sim": SIM,
   "try": {
    "title": "Pick the tool",
    "minutes": 3,
    "steps": [
     "Choose `volatile`, an atomic or a lock for each field, and say why in one line.",
     "(a) `boolean maintenanceMode`, flipped by an admin endpoint, read by every request.",
     "(b) `int inFlight`, incremented when a request starts and decremented when it ends, by request threads.",
     "(c) `long dailyLimitCents` and `long spentTodayCents`, checked together before each authorization.",
     "(d) `Map<String, Rule> rules`, replaced every minute by a refresher thread with a new map that nobody modifies."
    ],
    "expect": "(a) `volatile`: writes don't depend on the old value. (b) An atomic (`AtomicInteger` or `LongAdder`): many writers doing read-modify-write. (c) A lock: one rule spans two fields and needs check-then-act. (d) A `volatile` reference to an immutable map, built with `Map.copyOf` before it is published."
   }
  },
  {
   "h": "What volatile covers: one variable, all 64 bits, and nothing behind it",
   "body": "Three details trip people up once the basics are clear.\n\nFirst, `long` and `double`. The JLS (section 17.7) lets the JVM treat a write to a non-volatile `long` or `double` as two separate 32-bit writes. A racing reader could then see the high half of one value and the low half of another. Writes and reads of volatile `long` and `double` are always atomic, and so are references and every type of 32 bits or less. The jcstress suite shows torn longs on a 32-bit x86 JVM: a reader saw `-4294967296` and `4294967295` when the only values ever written were 0 and -1. 64-bit HotSpot writes a `long` in one instruction, so you won't see tearing there, but the spec doesn't promise it. In practice this rarely matters on its own: a `long` that two threads share needs `volatile` for visibility anyway, and you get atomicity with it.\n\nSecond, a volatile reference covers the reference and nothing inside the object. Writing `fees.add(f)` to a `volatile List<Fee> fees` is not a volatile write. It's a call on whatever list the field points to, with no edge for readers and no protection for the list. Replace the whole object instead:\n\n```java\nprivate volatile List<Fee> fees = List.of();   // volatile covers the reference only\n\nvoid replaceFees(List<Fee> fresh) {\n    fees = List.copyOf(fresh);                 // one volatile write of an immutable list\n}\n```\n\n```kotlin\n@Volatile private var fees: List<Fee> = emptyList()   // @Volatile covers the reference only\n\nfun replaceFees(fresh: List<Fee>) {\n    fees = fresh.toList()                              // one write of a copy nobody else holds\n}\n```\n\nThe jcstress sample `AdvancedJMM_05_MisplacedVolatile` shows the cost of getting this wrong. A volatile field held a holder object, but the new value went into a plain field inside the holder. On AArch64 a reader saw the new object's field still at 0 in 553 samples.\n\nThird, arrays. A `volatile long[]` makes the array reference volatile and leaves every element plain. For volatile elements, use `AtomicLongArray`, `AtomicIntegerArray` or `AtomicReferenceArray`:\n\n```java\nclass BalanceBoard {\n    private volatile long[] balances = new long[16];               // volatile reference, plain elements\n    private final AtomicLongArray safe = new AtomicLongArray(16);   // each element acts like a volatile\n\n    void post(int account, long cents) {\n        balances[account] = cents;   // plain element write: no edge for readers\n        safe.set(account, cents);    // volatile element write: readers of safe.get() see it\n    }\n}\n```\n\n```kotlin\nclass BalanceBoard {\n    @Volatile private var balances = LongArray(16)   // volatile reference, plain elements\n    private val safe = AtomicLongArray(16)           // each element acts like a volatile\n\n    fun post(account: Int, cents: Long) {\n        balances[account] = cents   // plain element write: no edge for readers\n        safe.set(account, cents)    // volatile element write: readers of safe.get() see it\n    }\n}\n```"
  }
 ],
 "analogy": "A volatile field is a number on the office whiteboard instead of in someone's notebook. Everyone reads the board directly, nobody copies it to a private note, and everyone sees the changes in the same order. But two people can still walk up, both read 41, both go back to their desks to add one, and both write 42. The board was always current; the update just wasn't one step. The analogy is weak in one place: a real whiteboard has no rule about the notes you wrote before updating it. A volatile write does: everything you wrote before it becomes visible to whoever reads the new value.",
 "in_your_world": "Look at hand-rolled circuit breakers and rate limiters in your services. A common shape is `volatile int failures` with `failures++` on every issuer timeout and `if (failures > 5) open()` right after. Under a burst of timeouts from the card issuer, increments get lost and the breaker opens late, exactly when it should be fastest. Libraries such as SmallRye Fault Tolerance use proper atomics or locks for this; copy them, or use them. The good uses of volatile are just as common: a `volatile RateTable current` that a scheduler replaces every minute, a `volatile boolean draining` that a Quarkus shutdown observer sets, a `volatile long lastPollMillis` for a Kafka liveness check.",
 "mistake": "The most common mistake is reaching for `volatile` as the general fix for \"thread-safety\": a field is shared, so it gets the keyword. That works for flags and single-writer values, and quietly fails for counters, check-then-act and any rule that spans two fields, because volatile makes each access visible and ordered without joining them into one step. Before adding `volatile`, ask who writes the field and whether the new value depends on the old one. If several threads write, or the write depends on a read, use an atomic or a lock.",
 "compare": {
  "title": "A volatile snapshot reference in Java and Kotlin",
  "java": {"title": "FraudRules.java", "src": "public class FraudRules {\n    // replaced whole, never mutated: one volatile read gives a consistent snapshot\n    private volatile Map<String, Rule> rules = Map.of();\n\n    // one refresher thread\n    public void refresh(Map<String, Rule> fresh) {\n        rules = Map.copyOf(fresh);   // build first, then publish with one volatile write\n    }\n\n    // many request threads\n    public Rule ruleFor(String merchantCategory) {\n        return rules.get(merchantCategory);\n    }\n}"},
  "kotlin": {"title": "FraudRules.kt", "src": "class FraudRules {\n    // replaced whole, never mutated: one volatile read gives a consistent snapshot\n    @Volatile\n    private var rules: Map<String, Rule> = emptyMap()\n\n    // one refresher thread\n    fun refresh(fresh: Map<String, Rule>) {\n        rules = fresh.toMap()   // a private copy, then publish with one volatile write\n    }\n\n    // many request threads\n    fun ruleFor(merchantCategory: String): Rule? = rules[merchantCategory]\n}"},
  "note": "The pattern is identical: build a new map, publish it with one volatile write, and never touch it again. The difference is in the copy. Java's `Map.copyOf` returns a truly unmodifiable map (and rejects nulls). Kotlin's `Map` type is only a read-only view, so the safety comes from `toMap()` making a fresh `LinkedHashMap` that no other code holds. If you passed the caller's map straight through, someone with a `MutableMap` reference could still change it under the readers."
 },
 "worked": {
  "title": "Choose the tools for a circuit breaker",
  "steps": [
   {"say": "A breaker in front of a card issuer opens after 5 failures in a row. Request threads call `onFailure` and `onSuccess`, and check `allowRequest` before each call. Every field is volatile. For each field, ask: who writes it, and does the write depend on a read?", "code": "class IssuerBreaker {\n    private volatile int consecutiveFailures;   // written by request threads\n    private volatile long openedAtMillis;       // 0 means closed\n\n    void onFailure(long now) {\n        consecutiveFailures++;                                             // 1. read-modify-write\n        if (consecutiveFailures >= 5 && openedAtMillis == 0) openedAtMillis = now;   // 2. check-then-act\n    }\n\n    void onSuccess() { consecutiveFailures = 0; }\n\n    boolean allowRequest(long now) {\n        long opened = openedAtMillis;\n        return opened == 0 || now - opened > 30_000;\n    }\n}", "lang": "java", "alt_lang": "kotlin", "alt_code": "class IssuerBreaker {\n    @Volatile private var consecutiveFailures = 0   // written by request threads\n    @Volatile private var openedAtMillis = 0L       // 0 means closed\n\n    fun onFailure(now: Long) {\n        consecutiveFailures++                                                  // 1. read-modify-write\n        if (consecutiveFailures >= 5 && openedAtMillis == 0L) openedAtMillis = now   // 2. check-then-act\n    }\n\n    fun onSuccess() { consecutiveFailures = 0 }\n\n    fun allowRequest(now: Long): Boolean {\n        val opened = openedAtMillis\n        return opened == 0L || now - opened > 30_000\n    }\n}"},
   {"say": "`consecutiveFailures` has many writers, and `++` depends on a read, so increments get lost and the breaker opens late. Line 2 reads the counter again, separately, and then reads and writes `openedAtMillis`: two threads can both see 5 and both set the time. `openedAtMillis` itself is fine as volatile for the readers in `allowRequest`, which need one value and nothing else.", "code": "", "lang": ""},
   {"say": "Make the counter atomic and decide on the value it returns. Each `incrementAndGet` returns a different number, so only one thread sees exactly 5 for each run of failures, and only that thread opens the breaker.", "code": "class IssuerBreaker {\n    private final AtomicInteger consecutiveFailures = new AtomicInteger();   // 1. many writers: atomic\n    private volatile long openedAtMillis;                                    // 2. readers need one value: volatile\n\n    void onFailure(long now) {\n        int n = consecutiveFailures.incrementAndGet();   // 3. one atomic step, and keep the result\n        if (n == 5) openedAtMillis = now;                // 4. only one thread sees n == 5\n    }\n\n    void onSuccess() { consecutiveFailures.set(0); }\n\n    boolean allowRequest(long now) {\n        long opened = openedAtMillis;                    // 5. read the volatile once\n        return opened == 0 || now - opened > 30_000;\n    }\n}", "lang": "java", "alt_lang": "kotlin", "alt_code": "class IssuerBreaker {\n    private val consecutiveFailures = AtomicInteger()   // 1. many writers: atomic\n    @Volatile private var openedAtMillis = 0L           // 2. readers need one value: @Volatile\n\n    fun onFailure(now: Long) {\n        val n = consecutiveFailures.incrementAndGet()   // 3. one atomic step, and keep the result\n        if (n == 5) openedAtMillis = now                // 4. only one thread sees n == 5\n    }\n\n    fun onSuccess() { consecutiveFailures.set(0) }\n\n    fun allowRequest(now: Long): Boolean {\n        val opened = openedAtMillis                     // 5. read the volatile once\n        return opened == 0L || now - opened > 30_000\n    }\n}"},
   {"say": "Two habits made this work. Use the value the atomic call returns: calling `incrementAndGet()` and then `get()` would bring the check-then-act gap back. And read a volatile into a local once when you use it twice, as `allowRequest` does, so both uses see the same value. When the breaker grows a half-open state that must let exactly one trial request through while it also resets the counter, two fields change together, and that is the point to switch to a lock.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Choose volatile, atomic or lock for a payment session",
  "minutes": 13,
  "files": ["labs/jmm/src/main/java/workbench/jmm/l03/PaymentSession.java"],
  "run": "./gradlew :jmm:test --tests 'workbench.jmm.l03.*'",
  "steps": [
   "Run the tests once. Four of the five fail: two waiters never see a write, the attempt counter comes up short, and the money invariant breaks.",
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
  "prompt": "Close this page. Write two small classes. `KafkaLagGauge`: one poller thread calls `update(long)`, metrics threads call `lag()`. `RetryCounter`: many threads call `onRetry()`, a metrics thread calls `retries()`. Use the lightest correct tool for each, and say in a comment why.",
  "answer": {"lang": "java", "src": "// one writer, readers need the latest value: volatile is enough\npublic final class KafkaLagGauge {\n    private volatile long lag;   // volatile also keeps the 64-bit write in one piece\n\n    public void update(long newLag) { lag = newLag; }\n    public long lag() { return lag; }\n}\n\n// many writers doing read-modify-write: atomic (LongAdder if it is very hot)\npublic final class RetryCounter {\n    private final AtomicLong count = new AtomicLong();\n\n    public void onRetry() { count.incrementAndGet(); }\n    public long retries() { return count.get(); }\n}",
             "alt": {"lang": "kotlin", "src": "// one writer, readers need the latest value: @Volatile is enough\nclass KafkaLagGauge {\n    @Volatile private var current = 0L   // also keeps the 64-bit write in one piece\n\n    fun update(newLag: Long) { current = newLag }\n    fun lag(): Long = current\n}\n\n// many writers doing read-modify-write: atomic (LongAdder if it is very hot)\nclass RetryCounter {\n    private val count = AtomicLong()\n\n    fun onRetry() { count.incrementAndGet() }\n    fun retries(): Long = count.get()\n}"}}
 },
 "recap": [
  "volatile gives visibility (fresh reads, visible writes), ordering (release on write, acquire on read) and one global order of all volatile accesses.",
  "It does not join a read and a write into one step: `count++`, check-then-act and `max = Math.max(max, x)` all still race.",
  "Use volatile for one-writer values, flags, timestamps and references to immutable snapshots. Use atomics for one variable with many writers, and a lock when a rule spans several fields.",
  "Ordering only helps threads that both use the volatile: one volatile field doesn't fix a two-thread protocol.",
  "Non-volatile `long` and `double` may tear under the JLS; volatile ones never do.",
  "A volatile reference or array covers the reference only, not the object or the elements behind it."
 ],
 "quiz": [
  {
   "q": "Many request threads run `balance += amount` on a `volatile long balance`. What can go wrong?",
   "options": [
    "Two threads can read the same balance and both write, so one amount is lost",
    "Nothing: volatile makes the whole statement atomic",
    "The 64-bit write can tear into two halves",
    "Readers may never see the new balance"
   ],
   "answer": 0,
   "why": "`+=` is read, add, write. Volatile makes each step visible and ordered but leaves the gap between them. Tearing is ruled out because the field is volatile, and visibility is fine, which is what makes the bug easy to miss."
  },
  {
   "q": "Which of these fields is correctly protected by `volatile` alone?",
   "options": [
    "A request counter that every request thread increments",
    "A reference to an immutable `RateTable` that one scheduler thread replaces every minute",
    "`limit` and `spent`, which are checked together before every authorization",
    "A `volatile ArrayList<Fee>` that several threads add fees to"
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
   "why": "Each thread's write-then-read must be ordered for the outcome to be ruled out. Thread A's volatile write is followed by a store-buffer drain, but thread B wrote a plain field, so nothing stops B's read from passing its own write. Make both fields volatile and the count drops to 0."
  },
  {
   "q": "A class has `private volatile long[] balances`. Thread A runs `balances[3] = 500`. Thread B later reads `balances[3]`. What is guaranteed?",
   "options": [
    "B sees 500, because the array is volatile",
    "B sees 500 or 0, but never a torn value",
    "B sees 500 once A releases the array",
    "Nothing about the element: only the array reference is volatile, so this is a plain write and a plain read"
   ],
   "answer": 3,
   "why": "Element accesses of a volatile array are plain accesses. There's no edge from A's write to B's read, and a plain `long` element may even tear under the JLS. Use `AtomicLongArray` when elements are shared."
  },
  {
   "q": "From lesson 2 of this track: T1 sets a plain `fee = 25` and then the volatile `ready = true`. T2 sees `ready == true` and then reads `fee`. Why must T2 see 25?",
   "options": [
    "Because `fee` is an `int`, and int writes are atomic",
    "Program order, then the volatile write-to-read edge, then program order again: the edges chain, so the write of `fee` happens-before its read",
    "Because volatile writes flush all CPU caches",
    "It doesn't have to; T2 may see 0"
   ],
   "answer": 1,
   "why": "This is piggybacking on the volatile. The write of `fee` comes before the release in T1's program order, and the read comes after the acquire in T2's. Atomicity only rules out half-written values; it says nothing about which value you see.",
   "from": "jmm-02"
  }
 ],
 "flashcards": [
  {"front": "What does a volatile field guarantee?", "back": "Visibility of the latest write, release/acquire ordering around each access, and a single order of all volatile accesses that every thread agrees on."},
  {"front": "Is `count++` on a volatile int atomic?", "back": "No. It's still a read, an add and a write. Use `AtomicInteger.incrementAndGet()` or `LongAdder`."},
  {"front": "When is volatile alone enough for a field?", "back": "When one thread writes it (or writes don't depend on the current value), and the field isn't part of a rule with other fields."},
  {"front": "Two fields must change together under one rule. Volatile, atomic or lock?", "back": "A lock, taken around every read and write of both fields."},
  {"front": "Can a write to a non-volatile `long` tear?", "back": "The JLS allows it to be split into two 32-bit writes. A volatile `long` or `double` is always written and read atomically."},
  {"front": "`volatile List<Fee> fees;` Is `fees.add(f)` from two threads safe?", "back": "No. Volatile covers the reference only. Replace the whole list with an immutable copy instead, or use a concurrent collection."},
  {"front": "Are the elements of a `volatile long[]` volatile?", "back": "No, only the array reference. Use `AtomicLongArray` for volatile element access."}
 ],
 "terms": [
  {"term": "Visibility", "plain": "Whether a read in one thread sees a write from another."},
  {"term": "Atomicity", "plain": "An operation happens as one indivisible step that no other thread can split."},
  {"term": "Read-modify-write", "plain": "Read a value, compute a new one from it, write it back. Needs an atomic or a lock when shared."},
  {"term": "Torn read", "plain": "Seeing half of one write and half of another, possible for non-volatile long and double under the JLS."},
  {"term": "Single writer", "plain": "A field that only one thread ever writes. Volatile is enough for it."},
  {"term": "Snapshot publication", "plain": "Building a new immutable object and publishing it with one volatile write, instead of mutating the old one."},
  {"term": "LongAdder", "plain": "A counter that spreads increments over several cells. Fast under contention; its sum is not a snapshot."}
 ],
 "explain_back": {
  "prompt": "A teammate asks: \"If volatile makes every read and write go to memory, why does `volatile int retries; retries++` still lose updates?\" Explain in your own words, and say what you would use instead.",
  "answer": "Volatile makes each read see the latest value and each write visible, but `retries++` is still three steps: read, add one, write. Two threads can both read 41 before either writes, and both write 42. Each access was perfectly volatile; the problem is the gap between them, which volatile doesn't close. For one counter with many writers I'd use `AtomicInteger.incrementAndGet()`, which does the read and the write as one atomic step, or `LongAdder` if it's a hot metrics counter. If the update had to touch more than one field, I'd use a lock."
 },
 "deeper": {
  "minutes": 8,
  "body": "Atomic classes are volatile fields with extra operations. `AtomicInteger.get()` and `set()` have the same memory effects as reading and writing a volatile `int`. What the class adds is atomic read-modify-write: `incrementAndGet`, `compareAndSet`, `getAndUpdate`, `accumulateAndGet`. The functional ones (`updateAndGet` and friends) retry a compare-and-set in a loop, so the function you pass may run more than once and must have no side effects.\n\nWhy is the JLS rule for `long` and `double` still there, when 64-bit JVMs never tear? Because the JLS is written for every JVM, including 32-bit ones, and dropping the rule would force those JVMs to use more expensive instructions for every 64-bit access. The VarHandle Javadoc states the same rule for its plain mode: plain reads and writes are guaranteed bitwise atomic only for references and for primitive values of 32 bits or less.\n\nA related term you may meet is word tearing: a write to one field or array element changing a neighbor, as some CPUs would do for single bytes. Java forbids it outright. Every field and every array element is its own variable, so a `byte[]` shared between threads never corrupts the byte next to the one you wrote. Races on that array are still races, of course."
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
