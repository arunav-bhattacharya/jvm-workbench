import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/concurrency/src"
P = "java/workbench/concurrency/l04"
K = "kotlin/workbench/concurrency/l04"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"./gradlew :concurrency:demo -Pmain=workbench.concurrency.l04.{name}"
def kt(name):
    """The Kotlin twin of a Java demo: Foo.kt with a top-level main, class FooKt."""
    return {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
            "run": demo(f"{name}Kt"), "file": f"{lab}/demo/{K}/{name}.kt"}

SIM = {
 "title": "A transfer under a lock, and two auditors",
 "intro": "T1 moves 50 from a to b while holding the lock. T2 audits without the lock, T3 with it. Make T2 see a total of 150. Then try to make T3 see anything but 200.",
 "vars": {"a": 100, "b": 100},
 "locks": ["lock"],
 "threads": [
  {"name": "T1 transfer", "steps": [
   {"op": "lock", "lock": "lock", "code": "synchronized (lock) {"},
   {"op": "read", "var": "a", "reg": "r", "code": "    long r = a;"},
   {"op": "add", "reg": "r", "n": -50, "code": "    r = r - 50;"},
   {"op": "write", "var": "a", "reg": "r", "code": "    a = r;"},
   {"op": "read", "var": "b", "reg": "r", "code": "    r = b;"},
   {"op": "add", "reg": "r", "n": 50, "code": "    r = r + 50;"},
   {"op": "write", "var": "b", "reg": "r", "code": "    b = r;"},
   {"op": "unlock", "lock": "lock", "code": "}"}]},
  {"name": "T2 audit, no lock", "steps": [
   {"op": "read", "var": "a", "reg": "x", "code": "long x = a;"},
   {"op": "read", "var": "b", "reg": "y", "code": "long y = b;"},
   {"op": "note", "code": "report(x + y);"}]},
  {"name": "T3 audit, locked", "steps": [
   {"op": "lock", "lock": "lock", "code": "synchronized (lock) {"},
   {"op": "read", "var": "a", "reg": "x", "code": "    long x = a;"},
   {"op": "read", "var": "b", "reg": "y", "code": "    long y = b;"},
   {"op": "unlock", "lock": "lock", "code": "}"},
   {"op": "note", "code": "report(x + y);"}]}
 ]
}

L = {
 "id": "conc-04",
 "title": "synchronized and intrinsic locks",
 "minutes": 35,
 "goal": "By the end you can protect shared state with `synchronized`, choose a safe lock object, and keep slow or foreign code out of your critical sections.",
 "warmup": {
  "q": "`transfer()` is `synchronized` and moves money between two balances. `total()` adds the balances and is not synchronized. Can `total()` return a wrong number while transfers run?",
  "options": ["No, because transfer() is synchronized, so it is atomic for everyone", "Yes, because total() does not take the lock, so it can read between the debit and the credit", "Only on machines with more than one core", "No, because reading a long is atomic"],
  "answer": 1,
  "why": "A lock only excludes threads that take the same lock. `total()` walks straight past it and can read after the debit but before the credit. Reading one `long` may be atomic, but reading two of them is still two steps. Readers need the lock as much as writers do."
 },
 "sections": [
  {
   "h": "synchronized lets one thread in at a time, and shows it what the last one wrote",
   "body": "In lesson 3 of this track, `count++` lost updates because two threads could run its read and its write at the same moment. A transfer that does `a -= cents` and then `b += cents` has the same problem, and the warm-up showed a second one: a reader that looks between the two lines. Both go away if only one thread at a time can run the code that touches the balances.\n\nEvery Java object has a built-in lock called its **monitor** (or intrinsic lock). `synchronized` takes it on the way in and releases it on the way out, even if the block throws.\n\n```java\nprivate final Object lock = new Object();\n\nvoid transfer(long cents) {\n    synchronized (lock) {     // take lock's monitor, or wait until it is free\n        a -= cents;\n        b += cents;\n    }                         // release it\n}\n```\n\n```kotlin\nprivate val lock = Any()\n\nfun transfer(cents: Long) {\n    synchronized(lock) {      // take lock's monitor, or wait until it is free\n        a -= cents\n        b += cents\n    }                         // release it\n}\n```\n\nA `synchronized` instance method is shorthand for `synchronized (this)` around the whole body. A `static synchronized` method locks the `Class` object, such as `Ledger.class`.\n\nYou get two guarantees, and you need both.\n\n**Mutual exclusion.** While one thread holds a monitor, any other thread that tries to enter a block guarded by the same monitor waits, in the BLOCKED state from lesson 2 of this track. So the debit and the credit happen as one step, from the point of view of everyone else who takes that lock.\n\n**Visibility.** When a thread releases a monitor, everything it wrote before that becomes visible to the next thread that takes the same monitor. The memory model calls this a happens-before edge from the release to the next lock. Without it, a thread could keep reading an old balance from a register or a CPU cache.\n\nBoth guarantees work only between threads that use the same monitor. A thread that reads `a` and `b` with no lock is not excluded and gets no visibility promise. It can read `a` after the debit and `b` before the credit, and report a total that is short by the amount in flight. Two auditors in the simulator below show the difference. Step T1 halfway through its transfer, then let T2 read. Then try the same trick on T3.",
   "sim": SIM,
   "try": {
    "title": "Audit with and without the lock",
    "minutes": 4,
    "steps": [
     "Run `AuditDemo`. A transfer thread moves 50 back and forth 200,000 times, always under the lock. The auditor adds `a + b` without it.",
     "Predict the count of wrong totals, then run it again with `-Pargs=locked`, where the auditor takes the lock too."
    ],
    "code": {"lang": "java", "title": "AuditDemo.java", "src": read(f"{lab}/demo/{P}/AuditDemo.java"),
             "run": demo("AuditDemo"), "file": f"{lab}/demo/{P}/AuditDemo.java", "alt": kt("AuditDemo")},
    "expect": "Without the lock, millions of audits see a total that is not 2,000 (one run here: 3,410,195 of 28,311,835). With the lock, zero, every run. The writer was correct all along. The reader was the bug."
   }
  },
  {
   "h": "A thread can take a lock it already holds",
   "body": "`synchronized` is **reentrant**: a thread that holds a monitor can enter another block on the same monitor without waiting. The JVM keeps a hold count per monitor. It goes up on each entry and down on each exit, and the monitor is free again when it reaches zero.\n\nYou rely on this all the time without noticing:\n\n```java\npublic synchronized void withdraw(long cents) {\n    if (canCover(cents)) balanceCents -= cents;   // canCover is synchronized too\n}\n\npublic synchronized boolean canCover(long cents) {\n    return balanceCents >= cents;\n}\n```\n\n```kotlin\n@Synchronized fun withdraw(cents: Long) {\n    if (canCover(cents)) balanceCents -= cents    // canCover is synchronized too\n}\n\n@Synchronized fun canCover(cents: Long): Boolean = balanceCents >= cents\n```\n\nWithout reentrancy, `withdraw` would wait forever for a lock it already holds. The same goes for a subclass whose `synchronized` override calls `super.withdraw(...)`, which is also `synchronized` on the same object.\n\nReentrancy has a side effect worth knowing. It lets the same thread back in while your object is halfway through a change. Say a `synchronized publish()` method loops over its listeners, and one listener calls `subscribe()`, which is also `synchronized`. The lock lets it straight in, because it is the same thread. `subscribe()` adds to the list that `publish()` is iterating, and the loop dies with `ConcurrentModificationException`. The lock did its job. It just isn't designed to stop the thread that already holds it. You'll fix exactly this in the lab.",
   "try": {
    "title": "Enter the same lock three times",
    "minutes": 2,
    "steps": [
     "Read `ReentrancyDemo`. `AuditedAccount.withdraw` calls `super.withdraw`, which calls `canCover`. All three are `synchronized` on the same object.",
     "Predict whether it finishes, then run it."
    ],
    "code": {"lang": "java", "title": "ReentrancyDemo.java", "src": read(f"{lab}/demo/{P}/ReentrancyDemo.java"),
             "run": demo("ReentrancyDemo"), "file": f"{lab}/demo/{P}/ReentrancyDemo.java", "alt": kt("ReentrancyDemo")},
    "expect": "It prints `holds the lock? true` at each level and finishes. The thread entered one monitor three deep, and the hold count went 1, 2, 3 and back to 0."
   }
  },
  {
   "h": "Lock on a private final object that only you can reach",
   "body": "A lock protects state only if every thread that touches the state uses the same lock, and no unrelated code uses it for something else. The safest choice is boring:\n\n```java\nprivate final Object lock = new Object();\n```\n\n```kotlin\nprivate val lock = Any()\n```\n\nIt is `private`, so no other class can lock it and stall you. It is `final`, so it can never change under you. Here are the choices that go wrong, roughly in the order I've seen them in code reviews.\n\nA boxed number, like `synchronized (count)` on an `Integer`. `count++` on an `Integer` field creates a new `Integer` object and points the field at it. So each thread may lock a different object, and nothing is excluded. Small values are also cached: `Integer.valueOf(42)` returns the same object everywhere in the JVM. javac knows, and prints `warning: [synchronization] attempt to synchronize on an instance of a value-based class`.\n\nA string literal, like `synchronized (\"lock\")`. Literals are interned, so every class in the JVM that writes `\"lock\"` gets the same object. Your token cache and someone's metrics library now share a lock.\n\nA field that is not `final`. If anyone reassigns it, threads before and after the change lock different objects.\n\n`this`, on a public class. It works, and `synchronized` methods do exactly this. But any caller can also write `synchronized (account) { ... }` and hold your lock for as long as they like. A private lock keeps that decision inside your class.\n\nOne more, which is always wrong: `synchronized (new Object())`. Every thread creates its own object, so nobody ever waits and nothing is visible to anyone. It's a lock that protects nothing.",
   "try": {
    "title": "Share a lock by accident",
    "minutes": 3,
    "steps": [
     "Read `SharedLiteralLock`. `TokenCache` and `Metrics` are unrelated and each lock on `\"lock\"`.",
     "Run it and read the metrics thread's state and how long it waited.",
     "In the lab you'll compile `DeclineCounter`, which locks on an `Integer`. Look for javac's `[synchronization]` warning in the Gradle output when you do."
    ],
    "code": {"lang": "java", "title": "SharedLiteralLock.java", "src": read(f"{lab}/demo/{P}/SharedLiteralLock.java"),
             "run": demo("SharedLiteralLock"), "file": f"{lab}/demo/{P}/SharedLiteralLock.java", "alt": kt("SharedLiteralLock")},
    "expect": "The metrics thread is `BLOCKED` after 200 ms and waits about 900 ms, the rest of the token refresh. Two classes that never mention each other contend on one lock, because both literals are the same interned `String`."
   }
  },
  {
   "h": "Keep critical sections short, and never call alien code inside one",
   "body": "Everything inside a `synchronized` block runs one thread at a time. So anything slow in there turns your thread pool into a queue of one. The demo below makes it concrete: eight threads each authorize five payments, and each card-issuer call takes 40 ms. With the call inside the lock, the 40 calls run one after another: about 1,600 ms. With only the bookkeeping inside the lock, the calls overlap: about 200 ms.\n\nThe rule: put only the reads and writes of shared state inside the lock. Do the I/O, the parsing and the computing before or after.\n\nThe worse version of the same mistake is calling **alien code** while you hold a lock. Alien means code you don't control: a listener, a callback, a method a subclass can override, a lambda someone passed in. You can't know what it does. It might make a 2-second HTTP call. It might hand work to another thread and wait for it, and if that thread needs your lock, you've built a deadlock. It might call back into your object on the same thread, where reentrancy lets it in halfway through your update.\n\nThis bug is common enough that the JDK has fixed instances of it in itself. JDK 25 carries a fix titled \"j.u.l.Handler classes create deadlock risk via synchronized publish() method\".\n\nThe fix has the same shape every time. Under the lock, change your own state and take a copy of whatever you need. Release the lock. Then call out.\n\n```java\nList<Listener> toNotify;\nsynchronized (lock) {\n    rates.put(pair, rate);               // 1. our state, under the lock\n    toNotify = List.copyOf(listeners);   // 2. a snapshot to work from\n}\nfor (Listener l : toNotify) l.onRate(pair, rate);   // 3. alien code, no lock held\n```\n\n```kotlin\nval toNotify = synchronized(lock) {\n    rates[pair] = rate                   // 1. our state, under the lock\n    listeners.toList()                   // 2. a snapshot to work from (the block's value)\n}\nfor (l in toNotify) l.onRate(pair, rate) // 3. alien code, no lock held\n```\n\nThe cost is that a listener may now hear about rates in a slightly different order than another thread published them. That is almost always a price worth paying.",
   "try": {
    "title": "Move the slow call out of the lock",
    "minutes": 3,
    "steps": [
     "Read `SlowCallUnderLock`. Both versions update `approvedCents` under the lock. Only one also holds the lock during the 40 ms issuer call.",
     "Predict both times (8 threads x 5 calls x 40 ms), then run it."
    ],
    "code": {"lang": "java", "title": "SlowCallUnderLock.java", "src": read(f"{lab}/demo/{P}/SlowCallUnderLock.java"),
             "run": demo("SlowCallUnderLock"), "file": f"{lab}/demo/{P}/SlowCallUnderLock.java", "alt": kt("SlowCallUnderLock")},
    "expect": "About 1,600 ms with the call inside the lock (40 calls in a row) and about 200 ms outside (5 rounds of 8 calls at once). Both versions get the total right. Only one of them can serve traffic."
   }
  }
 ],
 "analogy": "A monitor is a meeting room with one key on a hook. Whoever holds the key is inside, and everyone else waits in the corridor, which is the BLOCKED state. Before leaving, you write your results on the whiteboard, and the next person to take the key reads them: that is the visibility half. A string-literal lock is a key that several departments share without knowing it. Calling alien code under the lock is inviting a stranger into the room and waiting while they make a phone call. The analogy breaks at reentrancy: a thread that holds the key can walk back into the same room through another door, another synchronized method, without queuing. No real room works like that.",
 "in_your_world": "An `@ApplicationScoped` bean in Quarkus is one instance shared by every request thread, so any mutable field on it, such as an in-memory rate limiter or a cached OAuth token for the card issuer, needs a lock or an atomic. The same holds for a Temporal activity implementation: you register one object and the worker calls it from many threads at once. When you do lock, look at what runs inside: a `synchronized` method that calls Oracle or the issuer turns 200 worker threads into a queue of one. One version note for later: on JDK 21 to 23, a virtual thread that blocks inside `synchronized` pins its carrier thread. JDK 24 removed most of that (JEP 491), and the virtual threads track covers it.",
 "mistake": "The most common real mistake is guarding one piece of state with two different locks. The classic case is a `static` field updated in a `synchronized` instance method: each instance locks itself (`this`), but all instances share the static field, so two instances update it at the same time with no exclusion at all. The same thing happens when one class guards a shared map with its own lock and another class touches the map with no lock or a different one. Fix it by giving the state exactly one lock object, declared next to the state, `private static final Object LOCK` for static state, and taking it everywhere the state is read or written.",
 "compare": {
  "title": "Locking in Java and Kotlin",
  "java": {"title": "Java", "src": "public class DeclineCounter {\n    private final Object lock = new Object();\n    private int declines;\n\n    public void recordDecline() {\n        synchronized (lock) {        // a keyword\n            declines++;\n        }\n    }\n\n    public int total() {\n        synchronized (lock) {\n            return declines;\n        }\n    }\n}\n\npublic class HitCounter {\n    private int hits;\n    public synchronized void hit() { hits++; }      // locks this\n    public synchronized int total() { return hits; }\n}"},
  "kotlin": {"title": "KotlinLocks.kt", "src": read(f"{lab}/demo/{K}/KotlinLocks.kt")},
  "note": "Kotlin has no `synchronized` keyword. `synchronized(lock) { ... }` is an inline standard-library function, and the compiler emits the same `monitorenter`/`monitorexit` bytecode as a Java block. Because it is a function, it returns the value of its block, so `total()` can be one expression. `@Synchronized` on a function sets the same `ACC_SYNCHRONIZED` flag as Java's modifier, so it locks `this` (or, in an `object`, the object itself). `Any()` makes a fine private lock. One gap shows up in the next lesson: `Any` has no `wait()` or `notify()`, so Kotlin code that needs them must use a `java.lang.Object` or, better, the explicit locks from lesson 7 of this track."
 },
 "worked": {
  "title": "Fix a refund limiter with the wrong lock and a slow call inside",
  "steps": [
   {"say": "A refund service caps total refunds per process. It runs as two bean instances behind a router. Find every lock problem before reading on.",
    "code": "public class RefundLimiter {\n    private static long refundedCents;                     // shared by every instance\n    private static final long LIMIT_CENTS = 5_000_000;\n\n    public synchronized boolean tryRefund(long cents) {    // locks `this`\n        if (refundedCents + cents > LIMIT_CENTS) return false;\n        riskTeam.notifyLargeRefund(cents);                 // HTTP call, about 300 ms\n        refundedCents += cents;\n        return true;\n    }\n}", "lang": "java",
    "alt_code": "class RefundLimiter {\n    companion object {\n        private var refundedCents = 0L                    // shared by every instance\n        private const val LIMIT_CENTS = 5_000_000L\n    }\n\n    @Synchronized fun tryRefund(cents: Long): Boolean {   // locks `this`\n        if (refundedCents + cents > LIMIT_CENTS) return false\n        riskTeam.notifyLargeRefund(cents)                 // HTTP call, about 300 ms\n        refundedCents += cents\n        return true\n    }\n}", "alt_lang": "kotlin"},
   {"say": "Two problems. First, the method locks `this`, but the state is `static`. Two instances lock two different monitors and can both pass the limit check at once. Second, a 300 ms HTTP call runs inside the lock, so every refund waits for the previous one's call. Fix the lock first: one lock object for the one piece of state.",
    "code": "private static final Object LOCK = new Object();   // 1. one lock for the static state", "lang": "java",
    "alt_code": "private val LOCK = Any()        // 1. one lock for the shared state, in the companion object", "alt_lang": "kotlin"},
   {"say": "Now shrink the critical section. Reserve the amount under the lock, so the check and the update are one step. Then release the lock and make the call. If the call fails and the refund should not go ahead, give the reservation back, under the lock again. Ask yourself: why must the check and the `+=` stay inside the same block?",
    "code": "public boolean tryRefund(long cents) {\n    synchronized (LOCK) {                                  // 2. check and reserve as one step\n        if (refundedCents + cents > LIMIT_CENTS) return false;\n        refundedCents += cents;\n    }\n    try {\n        riskTeam.notifyLargeRefund(cents);                 // 3. slow call, no lock held\n        return true;\n    } catch (RuntimeException e) {\n        synchronized (LOCK) { refundedCents -= cents; }    // 4. undo the reservation\n        throw e;\n    }\n}", "lang": "java",
    "alt_code": "fun tryRefund(cents: Long): Boolean {\n    synchronized(LOCK) {                              // 2. check and reserve as one step\n        if (refundedCents + cents > LIMIT_CENTS) return false\n        refundedCents += cents\n    }\n    try {\n        riskTeam.notifyLargeRefund(cents)             // 3. slow call, no lock held\n        return true\n    } catch (e: RuntimeException) {\n        synchronized(LOCK) { refundedCents -= cents } // 4. undo the reservation\n        throw e\n    }\n}", "alt_lang": "kotlin"},
   {"say": "Split the check from the `+=` and you're back to lesson 3 of this track: check-then-act, with two threads both passing the check. The lock has to cover the whole compound action. What it must not cover is the 300 ms call, and now it doesn't. If the limit must hold across pods, the reservation belongs in the database, but the shape stays the same.",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Pick the right lock, then get alien code out of it",
  "minutes": 14,
  "files": [f"{lab}/main/{P}/DeclineCounter.java", f"{lab}/main/{P}/FxRateBoard.java"],
  "run": "./gradlew :concurrency:test --tests 'workbench.concurrency.l04.*'",
  "steps": [
   "Run the tests. Three of the four fail. The fourth checks that listeners still hear every rate, so keep it green while you fix the others. Look for the `[synchronization]` warning javac prints for `DeclineCounter`.",
   "Fix `DeclineCounter`: lock on a `private final Object` and store the count in a plain `int`. Guard `total()` with the same lock.",
   "Read the two `FxRateBoard` failures. One is a listener that waits for another thread to read the board. The other is a listener that subscribes a new listener and hits `ConcurrentModificationException`.",
   "Fix `FxRateBoard.publish`: update the map and copy the listener list under the lock, then notify the copy with no lock held.",
   "Run the tests until all four pass, then run them twice more."
  ],
  "hints": [
   "`declines++` on an `Integer` field is `declines = Integer.valueOf(declines.intValue() + 1)`. Which object does the next thread lock?",
   "`List.copyOf(listeners)` gives you an immutable snapshot. A listener that subscribes during the loop changes the real list, not the copy you're iterating.",
   "The cross-thread test fails after 2 seconds, not with a hang: the listener gives up waiting for its helper. If it fails, your listener is still being called while `lock` is held."
  ],
  "done_when": "All four tests in `SynchronizedTest` pass, three runs in a row, and the `[synchronization]` warning is gone."
 },
 "drill": {
  "title": "Copy under the lock, call outside it",
  "minutes": 4,
  "prompt": "Close this page. Write a class `StatusBoard` with a `String status`, a list of `Consumer<String>` listeners, `subscribe(listener)` and `update(newStatus)`. `update` must store the status and notify every listener, without ever calling a listener while holding the lock.",
  "answer": {"lang": "java", "src": "public class StatusBoard {\n    private final Object lock = new Object();\n    private final List<Consumer<String>> listeners = new ArrayList<>();\n    private String status;\n\n    public void subscribe(Consumer<String> l) {\n        synchronized (lock) { listeners.add(l); }\n    }\n\n    public void update(String newStatus) {\n        List<Consumer<String>> toNotify;\n        synchronized (lock) {\n            status = newStatus;\n            toNotify = List.copyOf(listeners);\n        }\n        for (Consumer<String> l : toNotify) l.accept(newStatus);\n    }\n}", "alt": {"lang": "kotlin", "title": "Kotlin", "src": "class StatusBoard {\n    private val lock = Any()\n    private val listeners = mutableListOf<(String) -> Unit>()\n    private var status: String? = null\n\n    fun subscribe(l: (String) -> Unit) {\n        synchronized(lock) { listeners += l }\n    }\n\n    fun update(newStatus: String) {\n        val toNotify = synchronized(lock) {\n            status = newStatus\n            listeners.toList()\n        }\n        for (l in toNotify) l(newStatus)\n    }\n}"}}
 },
 "recap": [
  "`synchronized` gives mutual exclusion and visibility, but only between threads that use the same monitor. Readers need the lock too.",
  "A synchronized instance method locks `this`, a static one locks the `Class` object, and a block locks the object you name.",
  "Monitors are reentrant: the thread that holds one can enter it again, which also lets callbacks on that thread back in mid-update.",
  "Lock on a `private final Object`. Never on boxed numbers, string literals, non-final fields or `new Object()`.",
  "Keep only shared-state reads and writes inside the lock. Copy what you need, release, then do I/O or call alien code."
 ],
 "quiz": [
  {"q": "Which line is the bug?\n\n```java\nclass FeeCounter {\n    private static long feesCents;                    // line 2\n    public synchronized void add(long cents) {        // line 3\n        feesCents += cents;                           // line 4\n    }\n}\n```\nThe service creates one `FeeCounter` per Kafka partition.",
   "options": ["Line 2: static fields cannot be locked", "Line 4: `+=` is not allowed inside synchronized", "Line 3: it locks `this`, but the state is static, so different instances don't exclude each other", "There is no bug, because the method is synchronized"],
   "answer": 2, "why": "Each instance locks its own monitor, while all instances share `feesCents`. Two partitions' counters run `+=` at the same time and lose updates. Static state needs one static lock: `private static final Object LOCK`, or a `static synchronized` method."},
  {"q": "A thread inside `synchronized void withdraw()` calls `canCover()`, which is also `synchronized` on the same object. What happens?",
   "options": ["It enters at once, because the monitor is reentrant", "It deadlocks waiting for itself", "It throws IllegalMonitorStateException", "It waits until withdraw() returns"],
   "answer": 0, "why": "Java monitors are reentrant. The JVM sees that the current thread already owns the monitor and increments the hold count. Without reentrancy every synchronized method that calls another one on the same object would hang."},
  {"q": "Which of these is the safest object to lock on for a class's internal state?",
   "options": ["`\"ledger-lock\"`, a string literal", "`Integer.valueOf(1)`", "`this`, on a public class that callers also hold references to", "`private final Object lock = new Object()`"],
   "answer": 3, "why": "A private final object can't be locked by anyone else and can't change. String literals are interned and shared JVM-wide. Small `Integer` values are cached and shared, and javac warns about locking on them. `this` works, but any caller can lock it too and stall your methods."},
  {"q": "`publish()` is `synchronized` and calls each listener inside the lock. One listener makes a 2-second HTTP call. What do other threads notice?",
   "options": ["Nothing, since each listener runs on its own thread", "Every thread that needs the same lock, even just to read a rate, waits up to 2 seconds", "The HTTP call is cancelled because of the lock", "The JVM detects the slow call and releases the lock"],
   "answer": 1, "why": "Listeners run on the publishing thread, inside its critical section. Anyone who needs that monitor queues behind the HTTP call. Copy the listener list under the lock, release it, then notify."},
  {"q": "From Race conditions: why count++ lies: `setBalance()` is `synchronized`, but `getBalance()` is a plain getter with no lock. Is the class thread-safe?",
   "options": ["Yes: only writes need a lock", "Yes, if the field is a `long`", "No: a reader that skips the lock gets no visibility promise and can see a stale value", "No, but only on 32-bit JVMs"],
   "answer": 2, "why": "Visibility comes from unlocking and locking the same monitor. A reader that never takes the lock has no happens-before edge to the writer, so it may keep seeing an old balance. Guard reads with the same lock, or use a `volatile` field or an atomic for a single value.",
   "from": "conc-03"}
 ],
 "flashcards": [
  {"front": "What two guarantees does `synchronized` give?", "back": "Mutual exclusion (one thread at a time per monitor) and visibility (writes made before releasing a monitor are seen by the next thread that locks it)."},
  {"front": "What does a `synchronized` instance method lock? A `static synchronized` method?", "back": "The instance, `this`. The static one locks the class object, for example `Ledger.class`."},
  {"front": "What does it mean that Java monitors are reentrant?", "back": "A thread that already holds a monitor can enter it again without waiting. The JVM counts the holds and frees the monitor when the count is back to zero."},
  {"front": "Why is `synchronized (count)` on an `Integer` field broken?", "back": "`count++` replaces the field with a new `Integer`, so threads lock different objects. Small values are also cached and shared JVM-wide. javac warns `[synchronization]`."},
  {"front": "Why never lock on a string literal?", "back": "Literals are interned: every `\"lock\"` in the JVM is the same object, so unrelated code shares your lock."},
  {"front": "What does `synchronized (new Object()) { ... }` protect?", "back": "Nothing. Each call locks a fresh object no other thread can see, so there is no exclusion and no visibility."},
  {"front": "What should you do before calling listeners or callbacks from a locked method?", "back": "Update your state and copy what you need (for example `List.copyOf(listeners)`) under the lock, release it, then call them."}
 ],
 "terms": [
  {"term": "Monitor (intrinsic lock)", "plain": "The lock every Java object has, taken and released by `synchronized`."},
  {"term": "Mutual exclusion", "plain": "Only one thread at a time can run the code guarded by a lock."},
  {"term": "Visibility", "plain": "Whether one thread is guaranteed to see what another thread wrote."},
  {"term": "Reentrant", "plain": "A thread can take a lock it already holds without waiting for itself."},
  {"term": "Critical section", "plain": "The code that runs while a lock is held."},
  {"term": "Alien method", "plain": "Code you don't control, such as a listener or callback, which can block or call back in."},
  {"term": "Value-based class", "plain": "A class like `Integer` whose instances may be shared or cached, so its identity is not yours to lock on."}
 ],
 "explain_back": {
  "prompt": "A colleague's PR adds `synchronized` to a `publish()` method that loops over listeners, \"to make it thread-safe\". Explain what can go wrong with that and what you would suggest instead.",
  "answer": "Making `publish()` synchronized protects the board's own state, but it also means every listener now runs while the lock is held. A slow listener makes every other thread that needs the board wait. A listener that hands work to another thread and waits for it can deadlock, because that thread may need the same lock. And because the lock is reentrant, a listener that calls back into the board on the same thread gets straight in, for example adding a listener while we iterate, which throws ConcurrentModificationException. I'd keep the lock only around updating the map and copying the listener list, then release it and notify the copy."
 },
 "deeper": {
  "minutes": 8,
  "body": "How does HotSpot make `synchronized` cheap when there is no contention? It doesn't create a full monitor object for every lock. An uncontended lock is a small change in the object's header (lightweight locking). Only when threads really fight over it, or one calls `wait()`, does the JVM inflate it into a full `ObjectMonitor` with an entry queue and a wait set.\n\nThe details keep changing between releases, which is a good reason not to depend on them. The `LockingMode` default became lightweight locking in JDK 23, the option was deprecated in JDK 24 and its code removed in JDK 26. JDK 27 switched on a separate table that maps objects to their monitors by default, and made compact object headers the default too. None of this changes what `synchronized` means. It only changes what it costs.\n\nIf you want to see contention rather than guess at it, Java Flight Recorder records a `jdk.JavaMonitorEnter` event when a thread has to wait for a monitor, with the monitor's class and the previous owner. JDK 25 added `jdk.JavaMonitorNotify` and `jdk.JavaMonitorStatistics`. Lesson 13 of this track uses them.\n\nFor virtual threads, JEP 491 in JDK 24 is the change to know: before it, a virtual thread blocked inside `synchronized` held on to its carrier thread, and since JDK 24 it doesn't in most cases."
 },
 "sources": [
  {"title": "Intrinsic locks and synchronization (The Java Tutorials)", "url": "https://docs.oracle.com/javase/tutorial/essential/concurrency/locksync.html"},
  {"title": "Java Language Specification, chapter 17: Threads and Locks", "url": "https://docs.oracle.com/javase/specs/jls/se25/html/jls-17.html"},
  {"title": "java.util.concurrent package summary, Memory Consistency Properties (source at jdk-25-ga)", "url": "https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/package-info.java"},
  {"title": "JEP 491: Synchronize Virtual Threads without Pinning", "url": "https://openjdk.org/jeps/491"},
  {"title": "Java Concurrency in Practice, Goetz et al., chapters 2 and 10", "url": "https://jcip.net/"}
 ]
}
out = ROOT / "content/lessons/conc-04.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
