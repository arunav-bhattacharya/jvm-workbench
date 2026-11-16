import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/concurrency/src"
P = "java/workbench/concurrency/l08"
K = "kotlin/workbench/concurrency/l08"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"./gradlew :concurrency:demo -Pmain=workbench.concurrency.l08.{name}"
def code(name):
    """A Java demo with its Kotlin twin (Foo.kt with a top-level main, class FooKt)."""
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": demo(name), "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
                    "run": demo(f"{name}Kt"), "file": f"{lab}/demo/{K}/{name}.kt"}}
def pair(java, kotlin):
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"

J_BASIC = """private final AtomicLong balanceCents = new AtomicLong();   // no lock needed

void deposit(long cents) {
    balanceCents.addAndGet(cents);        // read, add, write: one step nobody can split
}

long balance() {
    return balanceCents.get();            // like a volatile read: sees the latest value
}"""
K_BASIC = """private val balanceCents = AtomicLong()      // no lock needed

fun deposit(cents: Long) {
    balanceCents.addAndGet(cents)            // read, add, write: one step nobody can split
}

fun balance(): Long = balanceCents.get()     // like a volatile read: sees the latest value"""

J_NAIVE = """// Naive: read, decide, then write blindly
private volatile long max = Long.MIN_VALUE;

void offer(long amount) {
    if (amount > max) max = amount;      // another thread may have raised max since the read
}"""
K_NAIVE = """// Naive: read, decide, then write blindly
@Volatile private var max = Long.MIN_VALUE

fun offer(amount: Long) {
    if (amount > max) max = amount       // another thread may have raised max since the read
}"""

J_LOOP = """// Fixed: max is now an AtomicLong, and the write happens only if max is still prev
long prev;
do {
    prev = max.get();                       // 1. read
    if (amount <= prev) return;             // 2. decide: nothing to do
} while (!max.compareAndSet(prev, amount)); // 3. write only if max is still prev; else retry"""
K_LOOP = """// Fixed: max is now an AtomicLong, and the write happens only if max is still prev
var prev: Long
do {
    prev = max.get()                        // 1. read
    if (amount <= prev) return              // 2. decide: nothing to do
} while (!max.compareAndSet(prev, amount))  // 3. write only if max is still prev; else retry"""

J_LIB = """max.accumulateAndGet(amount, Math::max);          // the max tracker's loop, written for you
balanceCents.updateAndGet(b -> b + 100);          // any pure function of the old value"""
K_LIB = """max.accumulateAndGet(amount, Math::max)           // the max tracker's loop, written for you
balanceCents.updateAndGet { b -> b + 100 }        // any pure function of the old value"""

J_ADDER = """private final LongAdder depositsToday = new LongAdder();

void onDeposit() { depositsToday.increment(); }          // threads mostly hit different cells
long depositsSoFar() { return depositsToday.sum(); }     // adds the cells up: not a snapshot"""
K_ADDER = """private val depositsToday = LongAdder()

fun onDeposit() = depositsToday.increment()               // threads mostly hit different cells
fun depositsSoFar(): Long = depositsToday.sum()           // adds the cells up: not a snapshot"""

J_PAIR = """record Balances(long a, long b) {}           // immutable: a transfer builds a new one

private final AtomicReference<Balances> balances =
        new AtomicReference<>(new Balances(1_000, 1_000));

void transfer(long amount) {
    balances.updateAndGet(x -> new Balances(x.a() - amount, x.b() + amount));   // both change in one swap
}

long total() {
    Balances x = balances.get();             // one read: both balances from the same moment
    return x.a() + x.b();                    // always 2,000
}"""
K_PAIR = """data class Balances(val a: Long, val b: Long)   // immutable: a transfer builds a new one

private val balances = AtomicReference(Balances(1_000, 1_000))

fun transfer(amount: Long) {
    balances.updateAndGet { x -> Balances(x.a - amount, x.b + amount) }   // both change in one swap
}

fun total(): Long {
    val x = balances.get()                   // one read: both balances from the same moment
    return x.a + x.b                         // always 2,000
}"""

J_PUSH = """void push(T item) {
    Node<T> top, node;
    do {
        top = head.get();
        node = new Node<>(item, top);           // build the new node off to the side
    } while (!head.compareAndSet(top, node));   // publish it only if head is still top
}"""
K_PUSH = """fun push(item: T) {
    var top: Node<T>?
    var node: Node<T>
    do {
        top = head.get()
        node = Node(item, top)                  // build the new node off to the side
    } while (!head.compareAndSet(top, node))    // publish it only if head is still top
}"""

J_W1 = """private final AtomicLong balanceCents = new AtomicLong(10_000);

boolean tryWithdraw(long cents) {
    if (balanceCents.get() >= cents) {        // check
        balanceCents.addAndGet(-cents);       // act
        return true;
    }
    return false;
}"""
K_W1 = """private val balanceCents = AtomicLong(10_000)

fun tryWithdraw(cents: Long): Boolean {
    if (balanceCents.get() >= cents) {        // check
        balanceCents.addAndGet(-cents)        // act
        return true
    }
    return false
}"""
J_W2 = """boolean tryWithdraw(long cents) {
    while (true) {
        long before = balanceCents.get();                     // 1. read the balance
        if (before < cents) return false;                     // 2. decide on that value
        if (balanceCents.compareAndSet(before, before - cents)) return true;   // 3. commit, if unchanged
    }                                                         // 4. lost the race: read again, decide again
}"""
K_W2 = """fun tryWithdraw(cents: Long): Boolean {
    while (true) {
        val before = balanceCents.get()                       // 1. read the balance
        if (before < cents) return false                      // 2. decide on that value
        if (balanceCents.compareAndSet(before, before - cents)) return true   // 3. commit, if unchanged
    }                                                         // 4. lost the race: read again, decide again
}"""
J_W3 = """boolean tryWithdraw(long cents) {
    long before = balanceCents.getAndUpdate(b -> b >= cents ? b - cents : b);
    return before >= cents;                                   // did OUR withdrawal apply?
}"""
K_W3 = """fun tryWithdraw(cents: Long): Boolean {
    val before = balanceCents.getAndUpdate { b -> if (b >= cents) b - cents else b }
    return before >= cents                                    // did OUR withdrawal apply?
}"""

J_DRILL = """static boolean tryTake(AtomicInteger tokens) {
    while (true) {
        int left = tokens.get();
        if (left == 0) return false;                       // nothing left: no write
        if (tokens.compareAndSet(left, left - 1)) return true;
    }                                                      // someone else took one: retry
}"""
K_DRILL = """fun tryTake(tokens: AtomicInteger): Boolean {
    while (true) {
        val left = tokens.get()
        if (left == 0) return false                        // nothing left: no write
        if (tokens.compareAndSet(left, left - 1)) return true
    }                                                      // someone else took one: retry
}"""

FIG = (
    '<svg viewBox="0 0 720 230" role="img" aria-label="Timeline: T1 and T2 both read 41. T1 compare-and-set to 42 succeeds. T2 compare-and-set fails, it reads 42 and retries, writing 43">'
    '<text class="t-s t-m" x="20" y="28">time</text>'
    '<line class="ln-d" x1="60" y1="24" x2="700" y2="24" marker-end="url(#arr)"/>'
    '<text class="t" x="20" y="79">T1</text>'
    '<text class="t" x="20" y="154">T2</text>'
    '<rect class="box" x="60" y="56" width="110" height="36" rx="8"/>'
    '<text class="t t-code" x="115" y="79" text-anchor="middle">get() = 41</text>'
    '<rect class="box-ok" x="200" y="56" width="130" height="36" rx="8"/>'
    '<text class="t t-code" x="265" y="79" text-anchor="middle">CAS(41, 42)</text>'
    '<text class="t-s t-ok" x="265" y="110" text-anchor="middle">true: now 42</text>'
    '<rect class="box" x="90" y="131" width="110" height="36" rx="8"/>'
    '<text class="t t-code" x="145" y="154" text-anchor="middle">get() = 41</text>'
    '<rect class="box-bad" x="350" y="131" width="130" height="36" rx="8"/>'
    '<text class="t t-code" x="415" y="154" text-anchor="middle">CAS(41, 42)</text>'
    '<text class="t-s t-bad" x="415" y="185" text-anchor="middle">false: it is 42</text>'
    '<line class="ln-d" x1="480" y1="149" x2="496" y2="149" marker-end="url(#arr)"/>'
    '<rect class="box" x="500" y="131" width="100" height="36" rx="8"/>'
    '<text class="t t-code" x="550" y="154" text-anchor="middle">get() = 42</text>'
    '<rect class="box-ok" x="610" y="131" width="100" height="36" rx="8"/>'
    '<text class="t-s t-code" x="660" y="153" text-anchor="middle">CAS(42, 43)</text>'
    '<text class="t-s t-ok" x="660" y="185" text-anchor="middle">true: now 43</text>'
    '<text class="t-s t-m" x="555" y="214" text-anchor="middle">retry with the fresh value</text>'
    '</svg>'
)

OPENING = """Picture the bank's busiest account on payday. Eight tellers, each a thread (one line of work among several in the program), add deposits to its balance at once. In Race conditions: why count++ lies, a plain `long` field lost more than two thirds of those deposits. That lesson fixed a counter with an `AtomicInteger`, a number whose updates happen in one step that no other thread can split. It promised to open the atomic up later, and this lesson keeps that promise.

Every lock in the last lesson made threads wait in line for a key, even the ones that could give up. An atomic number keeps no line at all. A thread that loses a race shrugs and tries again, a few nanoseconds (billionths of a second) later.

That speed is easy to mistake for safety. A withdrawal that checks `balance.get()` and then calls `balance.addAndGet(-cents)` uses two perfectly atomic calls, and it can still take the account below zero.

In this lesson, we'll open the atomic up, build any update from one instruction and a loop, count a busy day's deposits, and move money between two balances at once. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
S0 = """Let's start with the balance itself. Here it is as an `AtomicLong`, with a deposit and a read:

""" + pair(J_BASIC, K_BASIC) + """

An **atomic variable** holds one value and offers read-modify-write operations (read the value, change it, write it back, as `count++` does) that no other thread can split. `addAndGet` reads, adds and writes as one step. Its `get()` and `set()` behave like reads and writes of a `volatile` field, a field whose reads always see the latest write from any thread.

The method names tell you what comes back. `incrementAndGet()` returns the new value, and `getAndIncrement()` returns the old one. The same pairs exist for add, update and accumulate. `AtomicInteger`, `AtomicLong`, `AtomicBoolean` and `AtomicReference` cover most needs.

How does a library turn three steps into one without a lock? It asks the processor. On x86 processors, the kind in most laptops and servers, HotSpot (the standard JVM) compiles `addAndGet` to a single `lock xadd` instruction, and `compareAndSet` to `lock cmpxchg`. ARM64 processors have their own equivalents. While that instruction runs, the core keeps the variable's cache line to itself. A cache line is the small block of memory that a core copies into its own fast memory, its cache. A core must own the line before it can write to it. So no other core can get in between the read and the write.

No thread ever waits for another. If the operating system pauses a thread, that thread is never in the middle of an atomic update: the instruction either happened or it didn't. So some thread always makes progress, which is what **lock-free** means. A lock, the guard that lets one thread in at a time, is different. A thread that is paused while it holds a lock stops every thread that needs it, just as the interest job stopped the cash machine in the last lesson.

Predict from the mechanism. In the middle of payday, the operating system pauses teller 3 for 50 ms. With the `AtomicLong`, what do the other seven tellers do in those 50 ms? And with a lock that teller 3 held at that moment? (With the atomic, they keep depositing: teller 3 was paused before or after its instruction, never inside it. With the lock, all seven wait the full 50 ms.)

Atomics have one hard limit, and it's the one from the opening. Each atomic protects one variable, one call at a time. Two calls in a row are two steps with a gap between them, and the warm-up's withdrawal lives in that gap. It checks, then acts on what it saw, a shape called check-then-act. To close it, we need the operation underneath all the others."""

# ---------------------------------------------------------------- section 1
S1 = """Here's a job that no single method does. The bank's fraud team, the people who look for suspicious payments, watches a screen that shows the largest payment of the day. Many threads report payments, and each one raises the maximum if its payment is bigger. The first version, the lab's `MaxTracker`, uses a `volatile` field:

""" + pair(J_NAIVE, K_NAIVE) + """

Let's trace the smallest case. The maximum is 500. Thread 1 reports 900 and thread 2 reports 700, at the same moment. Both read 500, and both decide to raise it. Thread 1 writes 900. A moment later, thread 2 writes 700 over it. The day's biggest payment has vanished from the screen, and `volatile` made sure every thread saw the wrong answer promptly.

The trouble is the blind write at the end. **Compare-and-set** (CAS) makes it a careful one. `compareAndSet(expected, next)` does this as one step: if the current value equals `expected`, store `next` and return `true`; otherwise change nothing and return `false`. Read it as "update it only if nobody beat me to it".

Picture a clerk who keeps a tally on a board behind the bank's counter. You may ask her to change it, but you must say what it shows now: "It says 41, please make it 42." If the board still says 41, she writes 42. If someone got there first and it already says 42, she refuses, and you look again. She never makes anyone wait in a line: she either writes the new number or says no. `compareAndSet(41, 42)` is that request, and the clerk is the processor's compare-and-set instruction.

With that one careful step, we can build any read-modify-write. Here's the max tracker again:

""" + pair(J_LOOP, K_LOOP) + """

First we read the maximum. Then we decide: if our amount isn't bigger, there's nothing to do. Finally we try the CAS. If another thread changed the maximum since we read it, the CAS fails. Our decision was based on old data, so we start again with the fresh value. The figure shows two threads, T1 and T2, that both read 41. T1's CAS wins. T2's fails, so T2 reads 42 and writes 43. Nothing is lost.

A failed CAS costs a retry, not a wait. `CasRetries` counts the retries. It runs a hand-written CAS increment a million times per thread, on 1, 2, 4 and then 8 threads. One run printed:

```text
threads: 1  counter:  1,000,000  failed CAS:          0  (0.00 per increment)
threads: 2  counter:  2,000,000  failed CAS:    536,415  (0.27 per increment)
threads: 4  counter:  4,000,000  failed CAS:  2,043,130  (0.51 per increment)
threads: 8  counter:  8,000,000  failed CAS:  2,805,059  (0.35 per increment)
```

The counter is exact every time. One thread never fails, because nobody else changes the value. With more threads, millions of CAS calls fail and retry. The rate jumps around from run to run: the Kotlin twin gave 0.30 per increment for 4 threads and 0.34 for 8. It stays below one, because a core tends to finish a run of increments before another core takes the cache line away.

**A CAS loop reads, decides, and writes only if nothing changed. When it fails, it decides again.**

You'll rarely write that loop by hand, though. The library has it built in, and that brings a surprise of its own."""

# ---------------------------------------------------------------- section 2
S2 = """`updateAndGet(f)` and `accumulateAndGet(x, f)` contain the loop:

""" + pair(J_LIB, K_LIB) + """

Inside, they read the value, call your function, and try the CAS. When the CAS fails, they call your function again with the new value. So your function can run more than once for one update, and the results of the extra runs are thrown away.

Let's count them. `UpdateTwice` starts four threads together, and each makes 250,000 one-cent deposits with `updateAndGet`. The function also counts how often it runs. Guess before you look: exactly 1,000,000 times?

```text
updates: 1,000,000   times the function ran: 1,294,839
```

The balance is exact, and the function ran 294,839 more times than there were deposits. Each extra run was a lost race whose result was thrown away. In six runs here, the extra runs came to between 29 and 99 percent of the deposits, so the number depends on how hard the threads collide. If that function had texted the customer, the bank would have sent close to 300,000 extra texts, for deposits that each happened once.

So the function must be **pure**: it looks only at its input and returns a result. No logging, no counters, no messages, no reads of other shared data that might change. Do any side effects after the call returns, using the value it returned.

**The update function may run more than once. Keep it pure, and act on the value it returns.**

The `get` variants, `getAndUpdate` and `getAndAccumulate`, return the value from before the update. Use them when the caller needs to know whether its own update applied. The worked example uses exactly that to build a withdrawal that never overdraws.

Every CAS so far fought over one variable. On a busy day, that fight is the cost."""

# ---------------------------------------------------------------- section 3
S3 = """The fight has a name: **contention**, many threads trying to change the same thing at the same moment. Here's a place it bites. The manager's screen shows how many deposits the bank has taken today. Eight threads add to that count all day, and someone glances at it now and then. On one `AtomicLong`, that's one cache line that every core wants at once. Each increment pulls the line over to its own core, and the cores spend their time passing it around.

`LongAdder` (JDK 8) spreads the count over several cells, small counters of their own. When threads collide on one cell, it moves them to different cells, so they mostly write to different cache lines. `sum()` adds the base value and all the cells together:

""" + pair(J_ADDER, K_ADDER) + """

`AdderVsAtomic` races the two. Eight threads count 2,000,000 deposits each, first on one `AtomicLong`, then on a `LongAdder`. I guessed the adder would win by a few times. One run printed:

```text
round 1: AtomicLong 16,000,000 in  669 ms   LongAdder 16,000,000 in   92 ms
round 2: AtomicLong 16,000,000 in  482 ms   LongAdder 16,000,000 in   71 ms
round 3: AtomicLong 16,000,000 in  578 ms   LongAdder 16,000,000 in   53 ms
```

Correctness first: both counted all 16,000,000. Then speed: the `LongAdder` was 7 to 11 times faster, more than I guessed. With a single thread the gap shrinks or disappears, because there's no contention for the adder to avoid.

The price is in `sum()`. It reads the cells one by one while other threads keep adding. Its Javadoc (the official API documentation) says plainly that the result is not an atomic snapshot: increments made during the sum might not be counted. The adder also uses more memory than one `long`.

That gives a clean rule. Use `LongAdder` for statistics that many threads update and someone reads now and then: deposits taken, requests served, payments refused. Use `AtomicLong` when the value drives a decision, such as a balance that must not go below zero, a sequence number, or a limit. A decision needs the exact current value and a compare-and-set against it, and `LongAdder` has neither. `LongAccumulator` does the same trick for other functions, such as a maximum, with the same caveat on reads.

**Count with a LongAdder. Decide with an AtomicLong.**

One number at a time, then. A transfer changes two."""

# ---------------------------------------------------------------- section 4
S4 = """Remember the checker from synchronized and intrinsic locks? A transfer moved 50 from account A to account B, and a checker that skipped the lock caught the 50 in flight, in neither account. Two `AtomicLong`s wouldn't help. Each is atomic, but the pair isn't, so the checker could still read A after the transfer and B before it. That lesson promised another way: one object that never changes, swapped in a single step.

`AtomicReference<V>` does compare-and-set on a reference. So put both balances in an immutable record, an object that can't change after it's built. A transfer builds a new record from the old one and swaps the reference:

""" + pair(J_PAIR, K_PAIR) + """

The checker reads one reference and gets both balances from the same moment, so the total is always 2,000, with no lock anywhere. In a quick check here, a checker read the total millions of times while 200,000 transfers ran, and it never saw anything else. `updateAndGet` runs the loop from the last two sections, so the function may run twice. It's pure, so that's fine. The CAS compares references with `==`, which asks "is it the same object?", not with `equals`. That's what we want, because every transfer builds a new object.

The lab's `TreiberStack`, named after R. Kent Treiber, who described it in 1986, uses the same idea on a linked list. A stack is a pile, like a pile of plates: the last item put on (pushed) is the first taken off (popped). Each node holds an item and a link to the node below, and it never changes after it's built. To push, we build a node that points at the current top, then CAS the top from that old node to the new one:

""" + pair(J_PUSH, K_PUSH) + """

CAS has one blind spot, called **ABA**. It checks that the value is the same as when you read it, not that it never changed in between. Let's trace it on a stack of A, B and C whose nodes get reused. Thread 1 starts a pop. It reads top = A and next = B, then the operating system pauses it. Thread 2 pops A, pops B, and pushes A back. Thread 1 wakes up and sees A on top, so its CAS from A to B succeeds. But B was already taken off, and the stack now starts with a node that thread 2 owns.

In Java, ABA needs reuse: a pool of recycled nodes, array indices, or plain numbers. With freshly built nodes, the garbage collector (the part of the JVM that frees memory nobody uses) never reuses A's memory while thread 1 still holds a reference to A. So the lab's stack is safe. When you do recycle, `AtomicStampedReference` pairs the reference with an `int` stamp that you bump on every change, so A with stamp 0 and A with stamp 3 no longer match.

That's the honest limit of atomics. One CAS covers one variable. For more, you swap a whole object, and under heavy traffic the retries add up. A whole map of accounts needs something built from these same pieces, and the JDK already has it."""

ASIDE0 = {
    "title": "If atomics need no lock, why is the instruction called lock xadd?",
    "body": "The `lock` there is a prefix on one processor instruction, not a Java lock. It tells the core to hold on to the variable's cache line until that one instruction is done. No thread ever joins a line for it, the way threads wait for a `ReentrantLock`, and the hold ends a few nanoseconds later. Other cores that want the same line do stall for those nanoseconds, though. That small stall, repeated millions of times, is the cost the `LongAdder` section measures."
}

L = {
 "id": "conc-08",
 "title": "Atomics and compare-and-set",
 "minutes": 37,
 "goal": "By the end you can write a compare-and-set retry loop, choose between `AtomicLong`, `LongAdder` and `AtomicReference`, and explain why two atomic calls in a row are not atomic.",
 "opening": OPENING,
 "warmup": {
  "q": "`balance` is an `AtomicLong` holding 100. Two threads run `if (balance.get() >= 80) balance.addAndGet(-80);` at the same moment. What can the balance end at?",
  "options": ["Only 20: `AtomicLong` makes the whole line thread-safe", "20 or 100, because one of the two updates can be lost", "20 or -60: both threads can pass the check before either takes the money", "Only -60, because both checks always run first"],
  "answer": 2,
  "why": "Each call is atomic on its own, so no update is lost: whatever `addAndGet` does, it does completely. But the check and the withdrawal are two calls with a gap between them. Both threads can see 100, both decide there's enough, and both take 80. That's check-then-act from Race conditions: why count++ lies, built out of atomic parts. The worked example puts the check inside one compare-and-set."
 },
 "sections": [
  {
   "h": "One step nobody can split: what an atomic variable does",
   "body": S0,
   "aside": ASIDE0
  },
  {
   "h": "Update it only if nobody beat me to it: compare-and-set and the retry loop",
   "body": S1,
   "figure": {"svg": FIG, "caption": "Both threads read 41. Only one CAS can succeed. The loser reads the new value and tries again, so no update is lost."},
   "try": {
    "title": "Watch CAS fail and retry",
    "minutes": 3,
    "steps": [
     "Read `CasRetries`. Its `increment()` is a hand-written CAS loop that counts its own failures.",
     "Predict the failure count for 1 thread, then for 8 threads.",
     "Run it twice. Check that `counter` is exact every time."
    ],
    "code": code("CasRetries"),
    "expect": "One thread never fails: nobody else changes the value. With more threads, failures climb into the hundreds of thousands or millions, and the number changes a lot from run to run (2,805,059 for 8 threads in one run here). The counter is exact every time. Failures stay below one per increment, because a core tends to get a run of increments done before another core takes the cache line away."
   }
  },
  {
   "h": "Letting the library write the loop: updateAndGet, and a function that runs twice",
   "body": S2,
   "try": {
    "title": "Count the calls",
    "minutes": 3,
    "steps": [
     "Read `UpdateTwice`. Four threads make 250,000 one-cent deposits each with `updateAndGet`, and the function counts how often it runs.",
     "Predict: will the function run exactly 1,000,000 times?",
     "Run it two or three times."
    ],
    "code": code("UpdateTwice"),
    "expect": "The balance is exactly 1,000,000 every time. The function runs more often than that, and how much more changes from run to run (between 1,294,839 and 1,991,780 times in six runs here). Each extra call is a lost compare-and-set whose result was thrown away. If the function had texted the customer, every one of those extra calls would have been an extra text."
   }
  },
  {
   "h": "Counting on a busy day: LongAdder for statistics, AtomicLong for decisions",
   "body": S3,
   "try": {
    "title": "Race an AtomicLong against a LongAdder",
    "minutes": 3,
    "steps": [
     "Read `AdderVsAtomic`: 8 threads each count 2,000,000 deposits, first on one `AtomicLong`, then on a `LongAdder`.",
     "Predict which is faster, and by roughly how much.",
     "Run it. Then change the thread count in `time` to 1 and run it again."
    ],
    "code": code("AdderVsAtomic"),
    "expect": "Both totals are exactly 16,000,000. With 8 threads, the `LongAdder` was 7 to 11 times faster in runs here (for example 669 ms against 92 ms). With 1 thread the gap shrinks or disappears, because there's no contention for the adder to avoid."
   },
   "refs": [
    {"title": "LongAdder.java at jdk-25-ga (when to prefer it over AtomicLong)", "url": "https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/atomic/LongAdder.java", "kind": "read"}
   ]
  },
  {
   "h": "Two balances in one swap: AtomicReference, and the ABA trap",
   "body": S4,
   "try": {
    "title": "Play out ABA by hand",
    "minutes": 3,
    "steps": [
     "Read `AbaDemo`. It plays both threads on one thread, step by step, so the bad order of events happens every time. Nodes are recycled.",
     "Before you run it, predict the stack after T1's `compareAndSet`.",
     "Run it and compare the plain `AtomicReference` with the `AtomicStampedReference`."
    ],
    "code": code("AbaDemo"),
    "expect": "With the plain reference, T1's `compareAndSet(A, B)` returns `true` and the stack becomes `B -> C`, although T2 had already popped B: the stack is corrupted. With the stamp, the same CAS returns `false`, because the stamp moved from 0 to 3, so T1 reads again and retries."
   }
  }
 ],
 "compare": {
  "title": "A max tracker with Java's atomics and Kotlin's",
  "java": {"title": "Java (java.util.concurrent.atomic)", "src": """class MaxTracker {
    private final AtomicLong max = new AtomicLong(Long.MIN_VALUE);

    void offer(long amount) {
        max.accumulateAndGet(amount, Math::max);   // CAS loop inside
    }

    long max() { return max.get(); }
}"""},
  "kotlin": {"title": "Kotlin (kotlin.concurrent.atomics)", "src": """@OptIn(ExperimentalAtomicApi::class)
class MaxTracker {
    private val max = AtomicLong(Long.MIN_VALUE)   // kotlin.concurrent.atomics, not java.util

    fun offer(amount: Long) {
        max.update { prev -> maxOf(prev, amount) }  // a CAS loop inside, like updateAndGet
    }

    fun max(): Long = max.load()
}"""},
  "note": "On the JVM, most Kotlin code simply uses `java.util.concurrent.atomic`, and everything in this lesson works the same from Kotlin. Kotlin 2.1 added its own atomics in `kotlin.concurrent.atomics`, mainly for code that must also run outside the JVM. The names differ (`load`, `fetchAndAdd`, `update`), and in the Kotlin 2.4 standard library they are still marked experimental, so they need `@OptIn(ExperimentalAtomicApi::class)`. Underneath, on the JVM, they are the same compare-and-set. One thing doesn't change between the languages: `@Volatile var count = 0` followed by `count++` compiles happily in Kotlin and loses updates exactly like the Java version."
 },
 "worked": {
  "title": "A withdrawal that never overdraws, without a lock",
  "steps": [
   {"say": "An account must never go below zero. `tryWithdraw` should take the money only if there's enough, and many threads call it at once. Here's a first attempt with an `AtomicLong`. Look for the race before reading on.",
    "code": J_W1, "lang": "java", "alt_code": K_W1, "alt_lang": "kotlin"},
   {"say": "Each call on `balanceCents` is atomic. The pair isn't: with 100 in the account, two threads can both pass the check for 80, and both take it, ending at -60. Making the variable atomic didn't make the logic atomic. The check has to happen inside the compare-and-set.", "code": "", "lang": ""},
   {"say": "The CAS loop checks the very value it is about to replace. If another thread changes the balance in between, the CAS fails and the loop decides again on fresh data.",
    "code": J_W2, "lang": "java", "alt_code": K_W2, "alt_lang": "kotlin"},
   {"say": "The same thing with `getAndUpdate`. The function is pure: it looks only at `b`. Before reading the next step, explain to yourself why the second line checks `before >= cents`, instead of checking whether the value changed.",
    "code": J_W3, "lang": "java", "alt_code": K_W3, "alt_lang": "kotlin"},
   {"say": "`getAndUpdate` returns the value that its last, successful run of the function saw. If that value covered `cents`, the function took the money, so this caller's withdrawal went through. If it didn't, the function returned `b` unchanged and nothing was taken. Checking whether the value changed tells you nothing, because other threads change it all the time. This is also why `LongAdder` is the wrong tool for a balance: it has no compare-and-set, and its `sum()` isn't exact while others add. If you keep balances in a database, the same idea becomes one statement, `UPDATE account SET balance = balance - ? WHERE id = ? AND balance >= ?`, followed by a check that one row changed.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "A lock-free max tracker and a Treiber stack",
  "minutes": 14,
  "files": [f"{lab}/main/{P}/MaxTracker.java", f"{lab}/main/{P}/TreiberStack.java"],
  "run": "./gradlew :concurrency:test --tests 'workbench.concurrency.l08.*'",
  "steps": [
   "Run the tests. `MaxTracker`, the fraud screen's largest-payment tracker from the second section, passes the single-thread test and fails the 8-thread one. Several raises started from the same old maximum, which means two threads both replaced it and one update was lost. The three stack tests fail with `UnsupportedOperationException`.",
   "Fix `MaxTracker` without `synchronized` or locks. Replace the `volatile long` with an `AtomicLong` and write the CAS loop from the second section. `offer` still returns the maximum from before your update.",
   "Write `TreiberStack.push`: read the head (the top node), build a new `Node` that points at it, `compareAndSet` the head, and retry on failure. Reject `null` with a `NullPointerException`.",
   "Write `pop` and `isEmpty`. `pop` returns `null` on an empty stack.",
   "Run the tests until all five pass, then twice more."
  ],
  "hints": [
   "The loop in `offer` has two exits, and both return `prev`: when `amount <= prev` (no write needed) and when the CAS succeeds.",
   "`getAndAccumulate(amount, Math::max)` is a one-line answer for `offer`. Write the loop first, then compare.",
   "In `pop`, take `next` from the node you read (`top.next`), never from a second `head.get()`. The head may have moved since."
  ],
  "done_when": "All five tests in `AtomicsTest` pass, three runs in a row."
 },
 "drill": {
  "title": "A CAS loop from memory",
  "minutes": 4,
  "prompt": "Close this page. Each account gets five free cash withdrawals a month, counted as tokens in an `AtomicInteger`. Write `tryTake(AtomicInteger tokens)`: take one token if any are left and return `true`, or return `false` when none are left. Use a `compareAndSet` loop, no locks. Then check: can the count ever go below zero?",
  "answer": {"lang": "java", "src": J_DRILL, "alt": {"lang": "kotlin", "title": "Kotlin", "src": K_DRILL}}
 },
 "recap": [
  "An atomic variable does one read-modify-write as a single step that no thread can split, with `volatile` visibility, and no thread ever waits for another.",
  "`compareAndSet(expected, next)` writes only if the value is still `expected`. Read, decide, CAS, and retry on failure: that loop builds any update.",
  "`updateAndGet` and its relatives contain the loop, so your function may run more than once. Keep it pure.",
  "`LongAdder` beats `AtomicLong` for busy counters, but `sum()` is not a snapshot. Use `AtomicLong` when the value drives a decision.",
  "`AtomicReference` and an immutable object change several fields in one swap. ABA needs reuse; `AtomicStampedReference` catches it.",
  "The limit: one CAS covers one variable, and two atomic calls in a row are not atomic. Put the check inside the CAS."
 ],
 "closing": "We started with eight tellers on one balance and an `AtomicLong` we had taken on trust. Underneath, it was one processor instruction, and for anything bigger, a loop: read, decide, compare-and-set, and decide again on failure. We counted a busy day with a `LongAdder`, and moved money between two balances in one swap.\n\nNow search your own code for an atomic's `get()` followed by another call on the same atomic. An `if (x.get() ...)` before an `x.addAndGet(...)` is check-then-act, built from atomic parts.\n\nNext, we'll open the collections built from these same pieces. What does a `ConcurrentHashMap` really promise when eight tellers write to it at once?",
 "quiz": [
  {"q": "Sixteen threads count every deposit the bank takes. The manager's screen reads the count once a minute. Which is the best fit?",
   "options": ["A `volatile long` with `count++`", "A `synchronized` increment method", "An `AtomicLong` with `incrementAndGet()`", "A `LongAdder` with `increment()` and `sum()`"],
   "answer": 3, "why": "Many writers and a rare read that may be a little behind is exactly what `LongAdder` is for: threads mostly update different cells, so they don't fight over one cache line. `AtomicLong` is correct, but slower under this much contention. `synchronized` is correct and slower still. `volatile` with `++` loses deposits."},
  {"q": "What does this print?\n\n```java\nAtomicInteger n = new AtomicInteger(5);\nint a = n.getAndIncrement();\nint b = n.incrementAndGet();\nSystem.out.println(a + \" \" + b + \" \" + n.get());\n```\n\n```kotlin\nval n = AtomicInteger(5)\nval a = n.getAndIncrement()\nval b = n.incrementAndGet()\nprintln(\"$a $b ${n.get()}\")\n```",
   "options": ["5 7 7", "6 7 7", "5 6 7", "6 6 6"],
   "answer": 0, "why": "`getAndIncrement` returns the old value (5) and leaves 6. `incrementAndGet` makes it 7 and returns the new value (7). The final `get()` is 7. The name says the order: get, then increment, or increment, then get."},
  {"q": "`balance.updateAndGet(b -> { long next = b - cents; sms.send(\"New balance: \" + next); return next; })` runs on many threads. What can go wrong?",
   "options": ["Nothing: `updateAndGet` runs the function exactly once per call", "The balance can lose a withdrawal", "Customers can get texts about balances their account never had, because the function runs again whenever its compare-and-set fails", "It throws `IllegalStateException` when threads collide"],
   "answer": 2, "why": "When a compare-and-set fails, `updateAndGet` calls the function again with the fresh value. The failed attempt has already sent its text, with a balance that was never stored. The balance itself is correct, which is why this bug is easy to miss. Keep the function pure, and send the text after the call, with the value it returned."},
  {"q": "From synchronized and intrinsic locks: to show the average deposit, the bank keeps `count` and `totalCents` for today's deposits, and both must always change together. Which is a correct choice?",
   "options": ["Two `AtomicLong` fields, each updated with `addAndGet`", "One `AtomicReference` to an immutable record holding both values, or a `synchronized` method that updates both", "Two `volatile long` fields", "Two `LongAdder` fields"],
   "answer": 1, "why": "Each atomic protects one variable. With two of them, a reader can see the new count with the old total. One lock around both updates, or one compare-and-set on a reference to an immutable pair, makes the two fields change as one step.",
   "from": "conc-04"},
  {"q": "When is ABA a real risk for a compare-and-set in Java?",
   "options": ["On every `AtomicReference` CAS, even with freshly built nodes", "Only on ARM processors", "Never: the JVM prevents it", "When the same value can come back after changes: recycled nodes, object pools, array indices, plain counters"],
   "answer": 3, "why": "CAS only checks that the value equals what you read, so it's fooled only if the value can return to an earlier one. With new nodes, the garbage collector won't reuse a node's memory while any thread still holds a reference to it, so it can't come back. Pools, indices and numbers can, and `AtomicStampedReference` adds a version number to catch it."}
 ],
 "flashcards": [
  {"front": "What does `ref.compareAndSet(expected, next)` do?", "back": "As one indivisible step: if the current value equals `expected`, it stores `next` and returns `true`. Otherwise it changes nothing and returns `false`."},
  {"front": "`incrementAndGet()` vs `getAndIncrement()`: what does each return?", "back": "`incrementAndGet()` returns the new value. `getAndIncrement()` returns the old value. Both add one atomically."},
  {"front": "Why must the function passed to `updateAndGet` have no side effects?", "back": "When its compare-and-set loses a race, `updateAndGet` calls the function again with the new value. It can run several times for one update."},
  {"front": "Busy counter, read rarely: `AtomicLong` or `LongAdder`?", "back": "`LongAdder`: threads update separate cells, so there is far less contention. Use `AtomicLong` when the exact value drives a decision."},
  {"front": "Is `LongAdder.sum()` an exact snapshot while other threads add?", "back": "No. It reads the cells one at a time, so increments made during the sum may be missed."},
  {"front": "What is the ABA problem?", "back": "A CAS succeeds because the value is back to what you read (A, then B, then A again), though it changed in between. Fix it with a version stamp: `AtomicStampedReference`."},
  {"front": "`if (n.get() < limit) n.incrementAndGet();` on an `AtomicInteger`: safe?", "back": "No. Two atomic calls with a gap between them is check-then-act. Do the check inside a CAS loop or `updateAndGet`."}
 ],
 "terms": [
  {"term": "Atomic variable", "plain": "A variable whose read-modify-write operations happen as one step that no other thread can split."},
  {"term": "Compare-and-set (CAS)", "plain": "Write a new value only if the current value is still the one you expected, and report whether it worked."},
  {"term": "CAS loop", "plain": "Read, decide, try a CAS, and start over if another thread changed the value first."},
  {"term": "Lock-free", "plain": "Some thread always makes progress, even if others are paused, because nobody holds a lock."},
  {"term": "Contention", "plain": "Many threads trying to change the same thing at the same moment."},
  {"term": "Pure function", "plain": "A function that only reads its input and returns a result, with no side effects, so running it twice does no harm."},
  {"term": "LongAdder", "plain": "A counter spread over several cells so threads rarely collide; its sum is not a snapshot."},
  {"term": "ABA problem", "plain": "A CAS that succeeds because a value changed and then changed back."}
 ],
 "explain_back": {
  "prompt": "Explain, in your own words, how a compare-and-set loop can update a shared balance correctly without any thread ever waiting for a lock.",
  "answer": "Each thread reads the current balance, works out the balance it wants, and then asks the processor to store it only if the variable still holds what it read. That compare-and-set is a single instruction, so no other thread can slip in between the compare and the store. If another thread changed the balance first, the CAS fails and nothing is written, so the thread reads again and decides again from the fresh value. A thread never waits for another; it just retries. Every failed CAS means some other thread succeeded, so the program as a whole always makes progress. The catch is that the work inside the loop may run several times, so it must have no side effects."
 },
 "deeper": {
  "minutes": 10,
  "body": "An `AtomicLong` is a separate object. If you have a million `Account` objects that each need an atomic balance, that's a million extra objects, each with its own header, the few bytes the JVM keeps at the start of every object. The JDK's own classes avoid this by putting a `volatile long` field in the class and doing CAS on the field in place. Two tools do that. `AtomicLongFieldUpdater` (and its `Integer` and `Reference` siblings) is the older one. `VarHandle`, since JDK 9, is the general one:\n\n```java\nprivate volatile long balanceCents;\nprivate static final VarHandle BALANCE;\nstatic {\n    try {\n        BALANCE = MethodHandles.lookup().findVarHandle(Account.class, \"balanceCents\", long.class);\n    } catch (ReflectiveOperationException e) {\n        throw new ExceptionInInitializerError(e);\n    }\n}\n\nboolean swap(long expected, long next) {\n    return BALANCE.compareAndSet(this, expected, next);   // CAS on this object's field\n}\n```\n\n```kotlin\nclass Account {\n    @Volatile private var balanceCents = 0L\n\n    fun swap(expected: Long, next: Long): Boolean =\n        BALANCE.compareAndSet(this, expected, next)        // CAS on this object's field\n\n    companion object {\n        private val BALANCE: VarHandle = MethodHandles.privateLookupIn(Account::class.java, MethodHandles.lookup())\n            .findVarHandle(Account::class.java, \"balanceCents\", Long::class.java)\n    }\n}\n```\n\n`VarHandle` also offers weaker memory orderings (`getAcquire`, `setRelease`, plain and opaque access), which the memory model track covers in its last lesson.\n\nTwo more details. The `weakCompareAndSet` family may fail even when the value matches. Inside a retry loop that doesn't matter, and on some ARM processors it can be cheaper. And a CAS loop is lock-free but not wait-free: one unlucky thread could, in theory, lose every race forever while others succeed. In practice that almost never happens, but it's why a busy CAS loop under extreme contention can be slower than a lock, which queues threads instead of letting them all retry at once. `LongAdder` exists because of exactly that case."
 },
 "sources": [
  {"title": "java.util.concurrent.atomic package summary (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/atomic/package-summary.html"},
  {"title": "LongAdder.java at jdk-25-ga", "url": "https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/atomic/LongAdder.java"},
  {"title": "Kotlin standard library: kotlin.concurrent.atomics", "url": "https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.concurrent.atomics/"},
  {"title": "Java Concurrency in Practice, Goetz et al., chapter 15", "url": "https://jcip.net/"}
 ]
}
out = ROOT / "content/lessons/conc-08.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
