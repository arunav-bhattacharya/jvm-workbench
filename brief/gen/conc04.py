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
def jv(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": demo(name), "file": f"{lab}/demo/{P}/{name}.java", "alt": kt(name)}
def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"

SIM = {
 "title": "A transfer under a lock, and two auditors",
 "intro": "T1 moves 50 from a to b while holding the lock. T2 checks the total (a + b) without the lock, T3 with it. Make T2 see a total of 150. Then try to make T3 see anything but 200.",
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

OPENING = """Picture a bank with two accounts, A and B, and 1,000 in each. A transfer takes 50 out of A, then adds 50 to B. One thread runs the transfers. (A thread is a line of work that runs side by side with others in one program.) Another thread, the checker, adds up both balances now and then. Transfers only move money, so the total should always be 2,000.

Race conditions: why count++ lies ended on this job. The usual fix is one word, `synchronized`, which makes threads take turns at the transfer. That's a fair instinct. The keyword has been part of Java since 1.0, and for the transfer itself it works.

The checker doesn't use the word, because it only reads, and reading never hurt anyone. Yet now and then it finds 50 missing, while the transfer code is perfect.

In this lesson, we'll put the transfer under a lock and see what `synchronized` promises, and to whom. Then we'll choose what to lock on, and keep slow calls out of the locked code. Before we start, make a guess, and keep it in mind."""

S0 = """We'll start where the last lesson stopped. Left alone, a transfer is two read-modify-write steps in a row (read a balance, change it, write it back), and we saw there how two threads lose updates in steps like those. So let's make the pair one step, with a lock. A **lock** is a guard on a piece of code. A thread takes the lock before it runs the code and gives it back after, and only one thread can hold it at a time.

Every Java object carries a built-in lock, and `synchronized` takes it on the way in and gives it back on the way out:

""" + pair('''private final Object lock = new Object();
private long a = 1_000, b = 1_000;   // the two balances

void transfer(long amount) {
    synchronized (lock) {        // take lock's monitor, or wait until it is free
        a -= amount;
        b += amount;
    }                            // give it back, even if the block throws
}''', '''private val lock = Any()
private var a = 1_000L               // the two balances
private var b = 1_000L

fun transfer(amount: Long) {
    synchronized(lock) {         // take lock's monitor, or wait until it is free
        a -= amount
        b += amount
    }                            // give it back, even if the block throws
}''') + """

Both versions say the same thing. In Java `synchronized` is a keyword, and in Kotlin it's a library function that compiles to the same bytecode, the instructions the JVM runs. The JDK's `javap` tool prints them: a `monitorenter` before the two lines, a `monitorexit` after them, and a second `monitorexit` on the path an exception takes.

The lock every object carries is called its **monitor**, or intrinsic lock. The code that runs while a thread holds it is called the **critical section**.

Here's a picture from the bank itself. The bank's vault is a room with one door and one key. A thread takes the key and goes in. Every other thread that wants the same key waits outside the door, in the state Java calls `BLOCKED`: alive, but not allowed to run yet. Inside, the thread updates the balance book. When it hands the key on, the next thread to take it sees every change in the book. The monitor is the key, and the vault is the code that `synchronized` guards.

That picture holds both guarantees that `synchronized` gives you.

**Mutual exclusion**: while one thread holds a monitor, no other thread can enter a block guarded by the same monitor. So the debit (taking money out) and the credit (putting it in) happen as one step.

**Visibility**: everything a thread wrote before it released a monitor is visible to the next thread that takes the same monitor. The memory model, Java's rules for which writes a thread is sure to see, calls that link a happens-before edge from the release to the next lock.

A `synchronized` instance method is shorthand for `synchronized (this)` around the whole body. A `static synchronized` method locks the class object, such as `Bank.class`.

Notice the words both guarantees share: the same monitor. The monitor is strict, and very literal. It keeps out every thread that asks for its key, and it pays no attention to threads that don't ask.

The checker from the opening is one of those threads. In `AuditDemo` it's called the auditor. A transfer thread moves 50 from `a` to `b` and back again, 200,000 times, always under the lock. Meanwhile the auditor adds up `a + b` as fast as it can. Both balances start at 1,000, so every audit should say 2,000.

Here are two runs, without and with the lock in the auditor:

```text
auditor skipped the lock: 41,004,159 audits, 2,813,398 saw a total other than 2,000
auditor took the lock: 905,017 audits, 0 saw a total other than 2,000
```

The transfer was correct all along. Without the lock, about one audit in fifteen caught the 50 in flight, in neither account. With the lock, not one of 905,017 audits was wrong. The price shows in the other number: the locked auditor got through far fewer audits, because each one now waits its turn for the key.

**A lock protects only the threads that take it. Readers take it too.**

You can play the auditor by hand in the simulator below, where you pick which thread runs next. Step T1 halfway through its transfer, then let T2 read. Then try the same trick on T3.

Real classes have more than one synchronized method, though, and the methods call each other. So what happens when a thread that already holds the key asks for it again?"""

S1 = """Here's that question in the bank. An account must never go below zero, so its `withdraw` method first asks `canCover`: is there enough money? Both methods are `synchronized` on the same account:

""" + pair('''public synchronized void withdraw(long cents) {
    if (canCover(cents)) balanceCents -= cents;   // canCover takes the same lock
}

public synchronized boolean canCover(long cents) {
    return balanceCents >= cents;
}''', '''@Synchronized fun withdraw(cents: Long) {
    if (canCover(cents)) balanceCents -= cents    // canCover takes the same lock
}

@Synchronized fun canCover(cents: Long): Boolean = balanceCents >= cents''') + """

This is check-then-act, the shape from the last lesson: check the balance, then act on what you saw. Here it's safe, because the check and the debit sit inside one locked method, so no other withdrawal can get in between. But look at what `withdraw` does while it holds the account's monitor: it calls `canCover`, which asks for that same monitor. If a thread had to wait for a key it already holds, it would wait forever.

It doesn't wait, because Java monitors are **reentrant**: a thread that holds a monitor can enter any block guarded by the same monitor without waiting. The JVM keeps a hold count for each monitor. Each entry adds one, each exit takes one away, and the monitor is free again at zero.

In the vault picture, the thread with the key can walk back in through a second door. In code, a synchronized method that calls another one on the same object never waits for itself.

Subclasses rely on the same rule. In `ReentrancyDemo`, `AuditedAccount` is an account that prints a line before each withdrawal. It overrides `withdraw` with a `synchronized` method that prints its line and calls `super.withdraw`, which then calls `canCover`. One thread enters one monitor three deep, and `Thread.holdsLock(this)` prints `true` at every level.

Reentrancy has a side effect worth knowing now, because the lab is built on it. The lock lets the same thread back in while your object is halfway through a change.

Many classes let other code sign up to hear about changes. Each piece of code that signs up is a **listener**, and the class calls every listener when something changes. Say a `synchronized` method `publish` loops over the listeners, and one listener calls `subscribe`, which is `synchronized` too. The lock lets it straight in, because it's the same thread. `subscribe` adds to the list that `publish` is walking through, and the loop dies with `ConcurrentModificationException`, Java's complaint when a list changes under a running loop.

The lock did its job. It was never meant to stop the thread that already holds it.

So far, every lock in this lesson has been an object we picked without much thought. Which object should hold the key, then? Any object can, and that's the trouble."""

S2 = """A lock protects state, the fields your threads share. It works only if every thread that touches the state uses the same lock, and no unrelated code uses that lock for something else. The safest choice is the boring one:

""" + pair('''private final Object lock = new Object();''', '''private val lock = Any()''') + """

The lock is `private`, so no other class can take it and stall you. It's `final` (a `val` in Kotlin), so it never changes under you. The other choices go wrong in ways that look harmless when you read the code.

A boxed number, an object such as `Integer` that wraps a plain `int`, is broken twice. Say the bank counts refused card payments in an `Integer` field, and locks on that field with `synchronized (declines)`. Then `declines++` creates a new `Integer` and points the field at it, so the next thread locks a different object and nothing is excluded.

Small values are also cached and shared: `Integer.valueOf(42)` returns the same object everywhere in the JVM. javac, the Java compiler, knows this, and prints `warning: [synchronization] attempt to synchronize on an instance of a value-based class`. The lab's `DeclineCounter` makes exactly this mistake.

A string literal, like `synchronized ("lock")`, is shared by design. Java keeps one copy of each literal (it interns them), so every class in the JVM that writes `"lock"` gets the same object. `SharedLiteralLock` has two classes that know nothing of each other. `TokenCache` keeps some saved data and takes a second to refresh it, and `Metrics` records a count for a report. Each one locks on `"lock"`. While the cache spends its second refreshing, the metrics thread sits `BLOCKED`. The demo reports that it `waited about 900 ms for a lock it never shared on purpose`.

A field that isn't `final` can be reassigned, and then threads before and after the change lock different objects.

`this` on a public class works, and a `synchronized` method does exactly that. But any caller can also write `synchronized (account) { ... }` and hold your key for as long as it likes. A private lock keeps that decision inside your class.

`synchronized (new Object())` is always wrong. Every thread locks its own fresh object, so nobody ever waits and nobody is promised anything. It's a lock that protects nothing.

The opposite mistake is two keys for one piece of state. The classic case is a `static` field (one copy, shared by every object of the class) updated in a `synchronized` instance method. Each object locks itself, so two objects update the shared field at the same time. The worked example below fixes one.

**Give each piece of state one private final lock. Take it everywhere the state is touched.**

The key is right now, and every reader takes it. A good lock can still make a program slow, though. It depends on what runs while the key is held."""

S3 = """Before a bank moves money, it often asks a fraud-check service whether the transfer looks suspicious. That service is a web service, a program on another computer, so each question travels over the network. In our demo each answer takes 40 ms, which is slow next to the transfer itself.

Everything inside a `synchronized` block runs one thread at a time, so anything slow in there makes every other thread wait in line. `SlowCallUnderLock` shows it. Eight threads each make five transfers, and each transfer asks the fraud checker first. Both versions add to the bank's total, `movedCents`, under the lock. Only one of them also holds the lock while it waits for the fraud checker.

My guess before running it: with the check inside the lock, the 40 checks run one after another, about 1,600 ms. With the check outside, they overlap in 5 rounds of 8, about 200 ms. It printed:

```text
fraud check inside the lock:  1,618 ms
fraud check outside the lock:   201 ms
```

The guess held, and both versions got the total right (the demo checks it). With the check inside the lock, eight threads, forty checks and one key made a very orderly line. The fraud checker takes its 40 ms either way. The only question is whether everyone else waits while it does.

So put only the reads and writes of shared state inside the lock. Do the slow work before it or after it: network calls, reading and writing files (together called I/O, for input and output), and heavy computing.

A worse form of the same mistake is calling **alien code** while you hold a lock. Alien code is code you don't control: a listener, a callback (a function someone gave you to call later), a method a subclass can override. It might call a web service that takes 2 seconds to answer.

Alien code might also hand work to another thread and wait for it. If that thread needs your lock, the two wait for each other forever. That's a **deadlock**, the subject of lesson 6 of this track. Or alien code might call back into your object on the same thread, where reentrancy lets it in halfway through your update.

The JDK has shipped this bug itself. JDK 25 carries a fix to its logging classes (`java.util.logging`, or `j.u.l`) titled "j.u.l.Handler classes create deadlock risk via synchronized publish() method".

The fix has the same shape every time. Under the lock, change your own state and take a copy of what you need. Release the lock. Then call out.

Here it is in the bank. Say the bank tells a list of listeners, such as a phone app's balance screen, about every new balance. Both versions copy the listeners under the lock and call them outside it:

""" + pair('''List<Listener> toNotify;
synchronized (lock) {
    balances.put(accountId, newBalance);   // 1. our state, under the lock
    toNotify = List.copyOf(listeners);     // 2. a snapshot to work from
}
for (Listener l : toNotify) l.onBalance(accountId, newBalance);   // 3. alien code, no lock held''', '''val toNotify = synchronized(lock) {
    balances[accountId] = newBalance       // 1. our state, under the lock
    listeners.toList()                     // 2. a snapshot to work from (the block's value)
}
for (l in toNotify) l.onBalance(accountId, newBalance)            // 3. alien code, no lock held''') + """

The Kotlin version is one variable shorter, because `synchronized` is a function and returns its block's value. The cost of the pattern is small: a listener may hear about two balances in a different order than two threads set them. That's almost always a price worth paying.

**Hold a lock only for your own reads and writes. Call out after you let go.**

That's the whole toolkit of this lesson, so let's be honest about where it stops. Our bank has one lock for every balance, so two transfers between four different accounts still wait for each other.

Give each account its own lock and a transfer must hold two, which is how lesson 6 of this track gets its deadlock. And a transfer that finds too little money can only refuse. While it holds the key, it can't wait for a deposit, because the deposit needs the key too."""

ASIDE = {
 "title": "The demo's balances are volatile. Why isn't that enough?",
 "body": "A `volatile` field is one where every read sees the latest write to it, from any thread. `AuditDemo` uses it for that reason: without it, the JIT (the part of the JVM that turns busy code into machine code while the program runs) could read the balances once and never again. But the auditor reads two fields, one after the other, and a transfer can run between the two reads. Each read is fresh, and the pair still doesn't match. To make two fields change together, you need a lock, or one immutable object (an object that never changes after it's built) that you swap in a single step, which lesson 8 of this track does with `AtomicReference`."
}

L = {
 "id": "conc-04",
 "title": "synchronized and intrinsic locks",
 "minutes": 35,
 "goal": "By the end you can protect shared state with `synchronized`, choose a safe lock object, and keep slow or foreign code out of your critical sections.",
 "opening": OPENING,
 "warmup": {
  "q": "`transfer()` is `synchronized` and moves money between two balances. `total()` adds the balances and is not synchronized. Can `total()` return a wrong number while transfers run?",
  "options": ["No, because transfer() is synchronized, so it is atomic for everyone", "Yes, because total() does not take the lock, so it can read between the debit and the credit", "Only on machines with more than one core", "No, because reading a long is atomic"],
  "answer": 1,
  "why": "A lock only keeps out threads that ask for the same lock. `total()` walks straight past it and can read after the money left one account but before it reached the other. Reading one `long` may be atomic (done in one step), but reading two of them is still two steps. Readers need the lock as much as writers do, and the first section measures how often the unlocked reader gets it wrong."
 },
 "sections": [
  {
   "h": "Locking the transfer: what synchronized promises, and to whom",
   "body": S0,
   "aside": ASIDE,
   "sim": SIM,
   "try": {
    "title": "Audit with and without the lock",
    "minutes": 4,
    "steps": [
     "Read `AuditDemo`. A transfer thread moves 50 back and forth 200,000 times, always under the lock. The auditor, the thread that checks the total, adds `a + b` without it.",
     "Run it with the command below and note how many audits were wrong.",
     "Predict the count of wrong totals when the auditor takes the lock too. Then run it again with `-Pargs=locked`."
    ],
    "code": jv("AuditDemo"),
    "expect": "Without the lock, millions of audits see a total other than 2,000 (one run here: 2,813,398 of 41,004,159). With the lock, zero, every run, though the auditor gets through far fewer audits because it waits for the key. The writer was correct all along. The reader was the bug."
   }
  },
  {
   "h": "Calling one locked method from another: reentrancy",
   "body": S1,
   "try": {
    "title": "Enter the same lock three times",
    "minutes": 2,
    "steps": [
     "Read `ReentrancyDemo`. `AuditedAccount.withdraw` prints a line and calls `super.withdraw`, which calls `canCover`. All three are `synchronized` on the same object.",
     "Predict whether it finishes or hangs, then run it."
    ],
    "code": jv("ReentrancyDemo"),
    "expect": "It prints `holds the lock? true` at each level and finishes. One thread entered one monitor three deep, and the hold count went 1, 2, 3 and back to 0."
   }
  },
  {
   "h": "Choosing the key: lock on a private final object",
   "body": S2,
   "try": {
    "title": "Share a lock by accident",
    "minutes": 3,
    "steps": [
     "Read `SharedLiteralLock`. `TokenCache` and `Metrics` never mention each other, and each one locks on `\"lock\"`.",
     "Predict the metrics thread's state after 200 ms, then run it and read how long it waited.",
     "In the lab you'll compile `DeclineCounter`, which locks on an `Integer`. Look for javac's `[synchronization]` warning in the Gradle output when you do."
    ],
    "code": jv("SharedLiteralLock"),
    "expect": "The metrics thread is `BLOCKED` after 200 ms, and it waits about 900 ms in all, the rest of the refresh. Two classes that never mention each other wait on one lock, because both literals are the same interned `String`."
   }
  },
  {
   "h": "Keeping slow calls and alien code out of the lock",
   "body": S3,
   "try": {
    "title": "Move the slow call out of the lock",
    "minutes": 3,
    "steps": [
     "Read `SlowCallUnderLock`. Both versions add to `movedCents` under the lock. Only one also holds the lock during the 40 ms fraud check.",
     "Predict both times (8 threads x 5 transfers x 40 ms), then run it."
    ],
    "code": jv("SlowCallUnderLock"),
    "expect": "About 1,600 ms with the check inside the lock (40 checks in a row) and about 200 ms with it outside (5 rounds of 8 checks at once). Both versions get the total right. Only one of them could keep up with a busy bank."
   }
  }
 ],
 "compare": {
  "title": "Locking in Java and Kotlin",
  "java": {"title": "Java", "src": "public class DeclineCounter {\n    private final Object lock = new Object();\n    private int declines;\n\n    public void recordDecline() {\n        synchronized (lock) {        // a keyword\n            declines++;\n        }\n    }\n\n    public int total() {\n        synchronized (lock) {\n            return declines;\n        }\n    }\n}\n\npublic class HitCounter {\n    private int hits;\n    public synchronized void hit() { hits++; }      // locks this\n    public synchronized int total() { return hits; }\n}"},
  "kotlin": {"title": "KotlinLocks.kt", "src": read(f"{lab}/demo/{K}/KotlinLocks.kt")},
  "note": "Both files lock the same way and compile to the same monitor instructions. Three things differ. Kotlin has no `synchronized` keyword: `synchronized(lock) { ... }` is an inline standard-library function, and the compiler emits the same `monitorenter` and `monitorexit` as a Java block. Because it's a function, it returns its block's value, so `total()` is one expression. And `@Synchronized` on a function marks the compiled method as synchronized, exactly like Java's modifier, so it locks `this` (or, in an `object`, the object itself). `Any()` makes a fine private lock. One gap shows up in the next lesson: `Any` has no `wait()` or `notify()`, so Kotlin code that needs them locks on a `java.lang.Object` or, better, uses the explicit locks from lesson 7 of this track."
 },
 "worked": {
  "title": "Fix a cash limit with the wrong lock and a slow call inside",
  "steps": [
   {"say": "One program runs all of a bank's cash machines. The bank caps how much cash the machines may pay out in one day, all of them together. The program creates one `PayoutLimit` object per machine, and the running total is a `static` field that all of them share. Before each payout, the code asks the fraud-check service, which takes about 300 ms and throws an exception if it refuses. Find every lock problem before you read on.",
    "code": "public class PayoutLimit {\n    private static long paidOutCents;                      // shared by every instance\n    private static final long LIMIT_CENTS = 5_000_000;\n\n    public synchronized boolean tryPayOut(long cents) {    // locks `this`\n        if (paidOutCents + cents > LIMIT_CENTS) return false;\n        fraudCheck.verify(cents);                          // web service call, about 300 ms\n        paidOutCents += cents;\n        return true;\n    }\n}", "lang": "java",
    "alt_code": "class PayoutLimit {\n    companion object {\n        private var paidOutCents = 0L                     // shared by every instance\n        private const val LIMIT_CENTS = 5_000_000L\n    }\n\n    @Synchronized fun tryPayOut(cents: Long): Boolean {   // locks `this`\n        if (paidOutCents + cents > LIMIT_CENTS) return false\n        fraudCheck.verify(cents)                          // web service call, about 300 ms\n        paidOutCents += cents\n        return true\n    }\n}", "alt_lang": "kotlin"},
   {"say": "There are two problems. First, the method locks `this`, but the state is `static`: two keys for one piece of state. Two machines' objects lock two different monitors and can both pass the limit check at once. Second, a 300 ms web service call runs while the key is held, so every payout waits for the previous one's fraud check. Fix the lock first: one lock object for the one piece of state.",
    "code": "private static final Object LOCK = new Object();   // 1. one lock for the static state", "lang": "java",
    "alt_code": "private val LOCK = Any()        // 1. one lock for the shared state, in the companion object", "alt_lang": "kotlin"},
   {"say": "Now shrink the critical section, the code that runs under the lock. Reserve the amount under the lock, so the check and the update are one step. Then release the lock and make the call. If the fraud check refuses the payout, give the reservation back, under the lock again. Before you read the last step, ask yourself why the check and the `+=` must stay inside the same block.",
    "code": "public boolean tryPayOut(long cents) {\n    synchronized (LOCK) {                                  // 2. check and reserve as one step\n        if (paidOutCents + cents > LIMIT_CENTS) return false;\n        paidOutCents += cents;\n    }\n    try {\n        fraudCheck.verify(cents);                          // 3. slow call, no lock held\n        return true;\n    } catch (RuntimeException e) {\n        synchronized (LOCK) { paidOutCents -= cents; }     // 4. undo the reservation\n        throw e;\n    }\n}", "lang": "java",
    "alt_code": "fun tryPayOut(cents: Long): Boolean {\n    synchronized(LOCK) {                              // 2. check and reserve as one step\n        if (paidOutCents + cents > LIMIT_CENTS) return false\n        paidOutCents += cents\n    }\n    try {\n        fraudCheck.verify(cents)                      // 3. slow call, no lock held\n        return true\n    } catch (e: RuntimeException) {\n        synchronized(LOCK) { paidOutCents -= cents }  // 4. undo the reservation\n        throw e\n    }\n}", "alt_lang": "kotlin"},
   {"say": "Split the check from the `+=` and you're back in Race conditions: why count++ lies, with check-then-act and two threads that both pass the check. The lock has to cover the whole compound action, the check and the update together. What it must not cover is the 300 ms call, and now it doesn't. If the bank ran several copies of this program on different computers, a static field couldn't hold the shared total any more: it would have to live somewhere they all share, such as a database. The shape of the fix would stay the same.",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Pick the right lock, then get alien code out of it",
  "minutes": 14,
  "files": [f"{lab}/main/{P}/DeclineCounter.java", f"{lab}/main/{P}/FxRateBoard.java"],
  "run": "./gradlew :concurrency:test --tests 'workbench.concurrency.l04.*'",
  "steps": [
   "Meet the two classes. `DeclineCounter` counts card payments that the bank refused (a refused payment is called a decline). `FxRateBoard` is the bank's board of exchange rates (FX is short for foreign exchange). It keeps the latest rate for each currency pair, such as `EURUSD`, the price of one euro in dollars, and tells its listeners about every new rate.",
   "Run the tests. Three of the four fail. The fourth checks that listeners still hear every rate, so keep it green while you fix the others. Look for the `[synchronization]` warning that javac prints for `DeclineCounter`.",
   "Fix `DeclineCounter`: lock on a `private final Object` and keep the count in a plain `int`. Guard `total()` with the same lock.",
   "Read the two `FxRateBoard` failures. In one, a listener waits for another thread to read the board. In the other, a listener subscribes a new listener and hits `ConcurrentModificationException`, the reentrancy side effect from the second section.",
   "Fix `FxRateBoard.publish`: update the map and copy the listener list under the lock, then call the listeners in the copy with no lock held. It's the balance-listener pattern from the last section.",
   "Run the tests until all four pass, then run them twice more."
  ],
  "hints": [
   "`declines++` on an `Integer` field is `declines = Integer.valueOf(declines.intValue() + 1)`. Which object does the next thread lock?",
   "`List.copyOf(listeners)` gives you a snapshot that can't change. A listener that subscribes during the loop changes the real list, not the copy you're walking through.",
   "The cross-thread test fails after 2 seconds rather than hanging: the listener gives up waiting for its helper thread. If it fails, your listener is still being called while `lock` is held."
  ],
  "done_when": "All four tests in `SynchronizedTest` pass, three runs in a row, and the `[synchronization]` warning is gone."
 },
 "drill": {
  "title": "Copy under the lock, call outside it",
  "minutes": 4,
  "prompt": "Close this page. Write a class `StatusBoard` with a `String status`, a list of `Consumer<String>` listeners, `subscribe(listener)` and `update(newStatus)`. `update` must store the status and tell every listener, without ever calling a listener while it holds the lock.",
  "answer": {"lang": "java", "src": "public class StatusBoard {\n    private final Object lock = new Object();\n    private final List<Consumer<String>> listeners = new ArrayList<>();\n    private String status;\n\n    public void subscribe(Consumer<String> l) {\n        synchronized (lock) { listeners.add(l); }\n    }\n\n    public void update(String newStatus) {\n        List<Consumer<String>> toNotify;\n        synchronized (lock) {\n            status = newStatus;\n            toNotify = List.copyOf(listeners);\n        }\n        for (Consumer<String> l : toNotify) l.accept(newStatus);\n    }\n}", "alt": {"lang": "kotlin", "title": "Kotlin", "src": "class StatusBoard {\n    private val lock = Any()\n    private val listeners = mutableListOf<(String) -> Unit>()\n    private var status: String? = null\n\n    fun subscribe(l: (String) -> Unit) {\n        synchronized(lock) { listeners += l }\n    }\n\n    fun update(newStatus: String) {\n        val toNotify = synchronized(lock) {\n            status = newStatus\n            listeners.toList()\n        }\n        for (l in toNotify) l(newStatus)\n    }\n}"}}
 },
 "recap": [
  "`synchronized` gives mutual exclusion and visibility, but only between threads that use the same monitor. Readers need the lock too.",
  "A synchronized instance method locks `this`, a static one locks the `Class` object, and a block locks the object you name.",
  "Monitors are reentrant: the thread that holds one can enter it again, which also lets a callback on that thread back in mid-update.",
  "Lock on a `private final Object`, one lock per piece of state. Never on boxed numbers, string literals, non-final fields or `new Object()`.",
  "Keep only shared-state reads and writes inside the lock. Copy what you need, release it, then make slow calls or call alien code.",
  "The limit: one lock makes everything it guards wait in a single line, two locks can deadlock, and a thread holding a lock can't wait for another thread to change the state."
 ],
 "closing": "We started with a bank checker that found money missing while the transfer code was perfect. The lock had kept its promise to every thread that asked for the key, and the checker never asked. Then we let a thread back into its own lock, chose a key nobody can borrow, and moved the fraud check out of the vault.\n\nNow search your own code for `synchronized` and read what runs inside each block. A web service call or a listener in there makes every other thread wait.\n\nNext, we'll visit a restaurant kitchen where a cook waits for the next order, and answer the question this lesson left open: how can a thread wait inside a lock without keeping the key?",
 "quiz": [
  {"q": "Which line is the bug?\n\n```java\nclass FeeCounter {\n    private static long feesCents;                    // line 2\n    public synchronized void add(long cents) {        // line 3\n        feesCents += cents;                           // line 4\n    }\n}\n```\nThe program creates one `FeeCounter` for each branch of the bank.",
   "options": ["Line 2: static fields cannot be locked", "Line 4: `+=` is not allowed inside synchronized", "Line 3: it locks `this`, but the state is static, so different instances don't exclude each other", "There is no bug, because the method is synchronized"],
   "answer": 2, "why": "Each instance locks its own monitor, while all instances share `feesCents`. Two branches' counters run `+=` at the same time and lose updates. That's two keys for one piece of state. Static state needs one static lock: `private static final Object LOCK`, or a `static synchronized` method."},
  {"q": "A thread inside `synchronized void withdraw()` calls `canCover()`, which is also `synchronized` on the same object. What happens?",
   "options": ["It enters at once, because the monitor is reentrant", "It deadlocks waiting for itself", "It throws IllegalMonitorStateException", "It waits until withdraw() returns"],
   "answer": 0, "why": "Java monitors are reentrant. The JVM sees that the current thread already owns the monitor and raises the hold count by one. Without reentrancy, every synchronized method that calls another one on the same object would hang."},
  {"q": "Which of these is the safest object to lock on for a class's internal state?",
   "options": ["`\"bank-lock\"`, a string literal", "`Integer.valueOf(1)`", "`this`, on a public class that callers also hold references to", "`private final Object lock = new Object()`"],
   "answer": 3, "why": "A private final object can't be locked by anyone else and can't change. String literals are interned and shared across the whole JVM. Small `Integer` values are cached and shared, and javac warns about locking on them. `this` works, but any caller can lock it too and stall your methods."},
  {"q": "`publish()` is `synchronized` and calls each listener inside the lock. One listener calls a web service that takes 2 seconds to answer. What do other threads notice?",
   "options": ["Nothing, since each listener runs on its own thread", "Every thread that needs the same lock, even just to read a value, waits up to 2 seconds", "The web service call is cancelled because of the lock", "The JVM detects the slow call and releases the lock"],
   "answer": 1, "why": "Listeners run on the publishing thread, inside its critical section. Anyone who needs that monitor waits in line behind the web service call. Copy the listener list under the lock, release it, then call the listeners."},
  {"q": "From Race conditions: why count++ lies: `setBalance()` is `synchronized`, but `getBalance()` is a plain getter with no lock. Is the class safe to use from many threads?",
   "options": ["Yes: only writes need a lock", "Yes, if the field is a `long`", "No: a reader that skips the lock gets no visibility promise and can see an old value", "No, but only on 32-bit JVMs"],
   "answer": 2, "why": "Visibility comes from unlocking and then locking the same monitor. A reader that never takes the lock has no happens-before edge to the writer, so it may keep seeing an old balance. Guard reads with the same lock, or, for a single value, use a `volatile` field or an atomic class such as `AtomicLong`.",
   "from": "conc-03"}
 ],
 "flashcards": [
  {"front": "What two guarantees does `synchronized` give?", "back": "Mutual exclusion (one thread at a time per monitor) and visibility (writes made before releasing a monitor are seen by the next thread that locks it)."},
  {"front": "What does a `synchronized` instance method lock? A `static synchronized` method?", "back": "The instance, `this`. The static one locks the class object, for example `Bank.class`."},
  {"front": "What does it mean that Java monitors are reentrant?", "back": "A thread that already holds a monitor can enter it again without waiting. The JVM counts the holds and frees the monitor when the count is back to zero."},
  {"front": "Why is `synchronized (count)` on an `Integer` field broken?", "back": "`count++` replaces the field with a new `Integer`, so threads lock different objects. Small values are also cached and shared JVM-wide. javac warns `[synchronization]`."},
  {"front": "Why never lock on a string literal?", "back": "Literals are interned: every `\"lock\"` in the JVM is the same object, so unrelated code shares your lock."},
  {"front": "What does `synchronized (new Object()) { ... }` protect?", "back": "Nothing. Each call locks a fresh object no other thread can see, so there is no exclusion and no visibility."},
  {"front": "What should you do before calling listeners or callbacks from a locked method?", "back": "Update your state and copy what you need (for example `List.copyOf(listeners)`) under the lock, release it, then call them."}
 ],
 "terms": [
  {"term": "Lock", "plain": "A guard on a piece of code: a thread must take it to run the code, and only one thread can hold it at a time."},
  {"term": "Monitor (intrinsic lock)", "plain": "The lock every Java object has, taken and released by `synchronized`."},
  {"term": "Mutual exclusion", "plain": "Only one thread at a time can run the code guarded by a lock."},
  {"term": "Visibility", "plain": "Whether one thread is guaranteed to see what another thread wrote."},
  {"term": "Reentrant", "plain": "A thread can take a lock it already holds without waiting for itself."},
  {"term": "Critical section", "plain": "The code that runs while a lock is held."},
  {"term": "Alien code", "plain": "Code you don't control, such as a listener or callback, which can be slow or call back in."},
  {"term": "Value-based class", "plain": "A class like `Integer` whose instances may be shared or cached, so its objects are not yours to lock on."}
 ],
 "explain_back": {
  "prompt": "A friend adds `synchronized` to a `publish()` method that loops over listeners, \"so it's safe with many threads\". Explain what can go wrong with that, and what you would suggest instead.",
  "answer": "Making `publish()` synchronized protects the board's own state, but it also means every listener now runs while the lock is held. A slow listener makes every other thread that needs the board wait. A listener that hands work to another thread and waits for it can deadlock, because that thread may need the same lock. And because the lock is reentrant, a listener that calls back into the board on the same thread gets straight in, for example adding a listener while we loop over the list, which throws ConcurrentModificationException. I'd keep the lock only around updating the state and copying the listener list, then release it and call the listeners in the copy."
 },
 "deeper": {
  "minutes": 8,
  "body": "How does HotSpot, the standard JVM, make `synchronized` cheap when nobody else wants the lock? It doesn't build a full monitor object for every lock. A lock that no other thread wants at that moment (an uncontended lock) is a small change in the object's header, the few bytes at the start of every object that the JVM uses for bookkeeping. This is called lightweight locking. Only when threads really fight over the lock, or one calls `wait()`, does the JVM inflate it into a full `ObjectMonitor`, with a queue of threads waiting to get in and a wait set (the next lesson explains both).\n\nThe details keep changing between releases, which is a good reason not to depend on them. Lightweight locking became the default `LockingMode` in JDK 23, the option was deprecated in JDK 24, and its code was removed in JDK 26. JDK 27 switched on, by default, a separate table that maps objects to their monitors, and made compact object headers the default too. None of this changes what `synchronized` means. It only changes what it costs.\n\nIf you want to see contention (threads waiting for each other's locks) rather than guess at it, Java Flight Recorder (JFR), an event recorder built into the JVM, records a `jdk.JavaMonitorEnter` event when a thread has to wait for a monitor, with the monitor's class and the previous owner. JDK 25 added `jdk.JavaMonitorNotify` and `jdk.JavaMonitorStatistics`. Lesson 13 of this track uses them.\n\nFor virtual threads (very light threads that the JVM runs on top of a few ordinary threads, called carrier threads), JEP 491 in JDK 24 is the change to know. Before it, a virtual thread blocked inside `synchronized` held on to its carrier thread. Since JDK 24 it doesn't, in most cases."
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
