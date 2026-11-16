import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/jmm/src"
P = "java/workbench/jmm/l02"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"{lab}/demo/{P}/{name}.java"
K = "kotlin/workbench/jmm/l02"
kdemo = lambda name: f"{lab}/demo/{K}/{name}.kt"
run = lambda name: f"./gradlew :jmm:demo -Pmain=workbench.jmm.l02.{name}"


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


def text(t):
    return f"```text\n{t}\n```"


def para(*parts):
    return "\n\n".join(parts)


FIG = (
    '<svg viewBox="0 0 700 360" role="img" aria-label="Two threads. T1, the day cashier, writes balance and entries, then leaves a synchronized block on LEDGER_LOCK. '
    'T2, the night manager, enters a synchronized block on the same lock, then reads entries and balance. The release pairs with the acquire of the same lock, so by chaining the write of balance happens-before the read of balance.">'
    '<text class="t" x="130" y="34" text-anchor="middle">T1: day cashier</text>'
    '<text class="t" x="570" y="34" text-anchor="middle">T2: night manager</text>'
    # T1
    '<rect class="box-ok" x="20" y="52" width="220" height="34" rx="8"/>'
    '<text class="t-s t-code" x="130" y="74" text-anchor="middle">balance = 12000;</text>'
    '<rect class="box" x="20" y="112" width="220" height="34" rx="8"/>'
    '<text class="t-s t-code" x="130" y="134" text-anchor="middle">entries = 41;</text>'
    '<rect class="box-a" x="20" y="172" width="220" height="34" rx="8"/>'
    '<text class="t-s t-code" x="130" y="194" text-anchor="middle">exit synchronized (LEDGER_LOCK)</text>'
    '<line class="ln" x1="130" y1="86" x2="130" y2="110" marker-end="url(#arr)"/>'
    '<line class="ln" x1="130" y1="146" x2="130" y2="170" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="138" y="103">program order</text>'
    # T2
    '<rect class="box-a" x="460" y="172" width="220" height="34" rx="8"/>'
    '<text class="t-s t-code" x="570" y="194" text-anchor="middle">enter synchronized (LEDGER_LOCK)</text>'
    '<rect class="box" x="460" y="232" width="220" height="34" rx="8"/>'
    '<text class="t-s t-code" x="570" y="254" text-anchor="middle">read entries: 41</text>'
    '<rect class="box-ok" x="460" y="292" width="220" height="34" rx="8"/>'
    '<text class="t-s t-code" x="570" y="314" text-anchor="middle">read balance: 12000</text>'
    '<line class="ln" x1="570" y1="206" x2="570" y2="230" marker-end="url(#arr)"/>'
    '<line class="ln" x1="570" y1="266" x2="570" y2="290" marker-end="url(#arr)"/>'
    # edges
    '<line class="ln-a" x1="240" y1="189" x2="458" y2="189" marker-end="url(#arr)"/>'
    '<text class="t-s t-a" x="250" y="212">same lock: release, then acquire</text>'
    '<line class="ln-d" x1="240" y1="86" x2="458" y2="292" marker-end="url(#arr)"/>'
    '<text class="t-s t-ok" x="290" y="118">happens-before, by chaining</text>'
    '<text class="t-s t-m" x="350" y="350" text-anchor="middle">Same lock, so T2 must see balance = 12000. A different lock gives no promise at all.</text>'
    '</svg>'
)

OPENING = """At the end of the day, the cashier at a small bank writes the closing balance in the ledger, the book where the bank keeps its accounts. She puts the ledger in its cabinet, locks it, and leaves the key for the night manager. When the night manager opens that cabinet with that key, she can trust what she reads: everything written before the cabinet was locked is there.

Threads need the same kind of handover, and the clock isn't one. In the last lesson, `main` set the stop flag, and seconds later the worker still saw the old value. Waiting longer didn't help. The trap is to think in time order: "my read ran later, so it sees the write." The memory model makes no such promise.

The promise it makes instead is called happens-before. In this lesson, we'll see what that promise means and meet the few handovers that create it: the same lock, the same volatile field, starting a thread and waiting for it to end. We'll watch `sleep` fail to be one, and chain promises so one handover covers many fields. Before we start, make a guess, and keep it in mind."""

S0 = para(
    "Remember the stop flag. `main` wrote `true` one second into the run, and three seconds later the worker was still reading `false`. On the clock, the write came first by a wide margin, and it made no difference.",
    "The memory model answers one question: when is a read in one thread sure to see a write from another? The documentation of `java.util.concurrent`, the JDK's package of concurrency tools, gives the answer in one sentence: \"The results of a write by one thread are guaranteed to be visible to a read by another thread only if the write operation happens-before the read operation.\"",
    "**Happens-before** is a relation between two actions, such as a write of a field and a read of it. If the write happens-before the read, and no other write to that field races in, the read sees that value. If nothing orders the two, the read may see the new value, an old one, or, as with the stop flag, never the new one at all. Whether a thread sees another thread's write is called **visibility**, and happens-before is the only thing that promises it.",
    "In the bank, happens-before is the promise of the locked cabinet. The cashier's writes come before she locks it, and the night manager's reads come after she opens it with the same key. Locking and opening link the two. The picture breaks in one place: nothing is carried anywhere. Both threads look at the same memory all the time, and without a handover a reader often does see the write. It just has no promise that it will, and the JIT, the part of the JVM that compiles busy code while it runs, is free to make sure it doesn't.",
    "The name misleads people, so let's be clear: happens-before is not about the clock. A write can run a full second before a read and still not happen-before it. That was the stop flag.",
    "The first rule is one you've always relied on. Inside one thread, each action happens-before every later action of that same thread. This is **program order**, and it's why code on one thread reads as written.",
    "The other rules link different threads, and the next sections take them one at a time. Chain them together and you have a proof that a particular read sees a particular write. When two threads use the same field, at least one of them writes it, and no chain of happens-before orders the two, the program has a **data race**.",
    "Data races are what the JMM, the Java Memory Model, is really about. Its main promise has a clumsy name, DRF-SC, short for \"data-race-free programs are sequentially consistent\". A program with no data races behaves as if its threads' lines were shuffled together like two decks of cards, each deck keeping its own order: the shuffled-decks order from the last lesson. You can reason about it the way you did in the simulator in Race conditions. A program with a data race gets very few promises beyond that.",
    "So the working method is short. For every field that two threads share, name the handover between the write and the read. If you can't name one, you have a race.",
    "**A later read is not a promised read. Name the handover, or call it a race.**",
    "Check yourself: T1 sets a plain `balance = 12_000` at 10:00:00. T2 reads `balance` a full second later, with no lock and no volatile on either side. Is T2 sure to see 12,000? No. A second on the clock is not a handover, and you can't name a rule that links the write to the read. That makes it a data race, and the old balance is a legal result.",
    "So the promise comes from handovers. The two you'll use most are a lock and a volatile field, and both come with one word in the fine print: same.",
)

ASIDE = {
    "title": "If happens-before isn't about the clock, may the JVM still swap two lines it orders?",
    "body": "Yes, as long as no thread can tell. The JLS, the official rulebook of the language, says so directly: two actions linked by happens-before don't have to take place in that order, if the result is one the rules allow anyway. Say a thread writes `a`, then `b`, and nobody reads either one until after a handover. The JVM may write `b` first, because no reader could ever tell. Happens-before is a promise about what reads see, so any order that keeps that promise is allowed. It's the cook's rule from the last lesson, stretched across threads.",
}

S1 = para(
    "A lock links threads, and so does a volatile field. Both come with a condition.",
    "The lock rule first. Every Java object carries a lock, called its monitor, which `synchronized` takes and releases. The rule: releasing a lock happens-before every later acquisition of the same lock. Leaving a `synchronized` block or method releases the monitor, and entering one acquires it. Add program order on both sides, and everything T1 did before leaving `synchronized (lock)` is visible to T2 once it enters `synchronized (lock)`. That's the bank's cabinet: lock it, and whoever opens it with the same key finds everything inside.",
    "Now the volatile rule. A `volatile` field is one whose every read sees the latest write, as the stop flag showed. The rule: a write to a volatile field happens-before every later read of that same field, where \"later\" means the read sees that write or a newer one. Picture a sign the cashier hangs on the cabinet when she's done: \"ledger closed\". Anyone who reads the sign and sees \"closed\" is promised everything she wrote before hanging it. Unlike the key, the sign makes nobody wait, and any number of people can read it at once. A volatile field works like a lock without the waiting.",
    "The Java Language Specification (JLS), the official rulebook of the language, calls the start of such a link a **release** and the end of it an **acquire**. Leaving a monitor and writing a volatile are releases. Entering a monitor and reading a volatile are acquires. Every class in `java.util.concurrent` is built on the same pair.",
    "Both rules contain the word *same*, and that's where the bugs are:",
    pair('''synchronized (ledgerLock) { balance = 12_000; }   // T1 releases ledgerLock
synchronized (reportLock) { seen = balance; }     // T2 acquires reportLock: no link''', '''synchronized(ledgerLock) { balance = 12_000 }     // T1 releases ledgerLock
synchronized(reportLock) { seen = balance }       // T2 acquires reportLock: no link'''),
    "Two different locks each keep two threads out of the same block, and give no link between those threads. Volatile fields work the same way: a write to a volatile `version` and a read of a volatile `checksum` link nothing. That's a sign on one cabinet and a reader looking at another.",
    "The most common shape of this bug is the half-locked class: a `synchronized` setter and a plain getter. The writer releases the lock, and the reader never acquires it, so there's nothing to pair with. `LedgerTotals` in the lab is that class.",
    "One more: `synchronized (new Object())` does nothing for other threads. No other thread can ever get hold of that object, so no other thread can take its lock, and no link can form. HotSpot notices too. Its escape analysis, a check that proves an object never leaves the code that made it, removes the lock entirely, and the read inside becomes a plain read. A lock nobody else can take is just ceremony.",
    "`LockScopeDemo` puts both kinds of reader to the test. A writer sets `balance` inside `synchronized (LEDGER_LOCK)`. By default, the reader locks a brand-new object on every pass; with `-Pargs=shared`, it locks `LEDGER_LOCK`, the same lock the writer used. The two runs printed:",
    text("writer set balance = 12000 inside synchronized (LEDGER_LOCK)\nreader still spinning 3 s later? true"),
    text("writer set balance = 12000 inside synchronized (LEDGER_LOCK)\nreader (LEDGER_LOCK) saw balance = 12000\nreader still spinning 3 s later? false"),
    "The reader with its own lock spun forever, just like the stop flag. The reader with the shared lock saw the balance at once. Same field, same loop, and only the lock changed.",
    "**A lock or a volatile field links only the threads that use the same one. Check both sides.**",
    "Locks and volatile fields link threads that are already running. Two more handovers link a thread to the thread that started it.",
)

S2 = para(
    "Picture the bank hiring a helper for one evening. Everything the manager tells the helper before the shift starts, the helper knows. And when the manager waits at the door until the helper finishes and walks out, she knows everything the helper did. Threads have the same two handovers.",
    "`Thread.start()` happens-before every action in the started thread. Whatever the parent wrote before calling `start()` (settings, a list of work, the variables a lambda captured) the new thread sees.",
    "Every action in a thread happens-before another thread returns from `join()` on it. The same holds when another thread sees `isAlive()` return `false`. After `join()` returns, the parent sees every result the worker wrote, even into plain fields and plain arrays. That's why the threads track could read results after `join()` without a second thought.",
    "A third rule matters for stopping threads. When T1 calls `t2.interrupt()`, that call happens-before any thread notices the interrupt through `isInterrupted()`, `Thread.interrupted()` or an `InterruptedException`.",
    "`Thread.sleep()` has none of this. `SleepIsNotJoinDemo` starts a worker that adds up the day's sales of 20 shops, one slow call of about 10 ms per shop, and then writes the total. `main` sleeps 50 ms and reads it:",
    text("after sleep(50): total = 0 (expected 2,000,000)"),
    "Fifty milliseconds felt like plenty to `main`. The worker needed two hundred. So the sleep didn't wait for the worker to finish. Even if the worker had finished in time, the sleep would create no link, so an old value would still be a legal read. A sleep long enough to \"always work\" passes on your laptop and fails on a busy build server, the shared machine that runs everyone's tests.",
    "The fix is to wait for the worker itself:",
    pair('''Thread worker = new Thread(() -> { /* adds up the 20 shops */ });
worker.start();
worker.join();                 // waits for the worker to end, and links its writes to us
System.out.println(total);     // 2,000,000, every time''', '''val worker = thread { /* adds up the 20 shops */ }   // thread {} calls start() for you
worker.join()                  // waits for the worker to end, and links its writes to us
println(total)                 // 2,000,000, every time'''),
    "The start link covers only the writes made before `start()`. Here a printer thread reads settings that are loaded one line too late:",
    pair('''Thread printer = new Thread(() -> print(settings.paperSize()));
printer.start();
settings = loadSettings();   // after start(): no link to the printer thread''', '''val printer = thread { print(settings.paperSize) }   // thread {} calls start() for you
settings = loadSettings()                            // after start(): no link to the printer thread'''),
    "The printer thread may see `settings` as `null` or as the old value. This case comes back in lesson 4 of this track, where a constructor starts a thread before it has finished setting its own fields.",
    "**A sleep passes time and promises nothing. Wait with `join()`, or with another handover.**",
    "Each handover so far links one write to one read, or so it seems. In fact, one handover can carry a whole bundle of writes.",
)

S3 = para(
    "The cashier writes many pages before she locks the cabinet, and the night manager can trust every one of them. Happens-before works the same way, because its links chain. If A happens-before B, and B happens-before C, then A happens-before C. That property is called **transitivity**, and it's why one lock or one volatile field can protect many plain fields.",
    "Here's the board of exchange rates from the last lesson's lab, with each step labeled:",
    pair('''// loader thread                     // request thread
rates = Map.copyOf(loaded);  // A     while (!ready) { }          // C: sees true
ready = true;                // B     Map<String, Long> r = rates; // D''', '''// loader thread                     // request thread
rates = loaded.toMap()       // A     while (!ready) { }          // C: sees true
ready = true                 // B     val r = rates               // D'''),
    "`ready` is volatile and `rates` is plain. A comes before B in program order. B is a volatile write, and C is a volatile read that sees it. C comes before D in program order. So A happens-before D, and the request thread sees the whole map, though `rates` is a plain field. This is often called **piggybacking**: the plain write rides along on the volatile one.",
    "Two conditions are easy to miss. The plain writes must come before the release. If the loader wrote `rates` after setting `ready`, no link would cover it, just as a page written after the cabinet is locked isn't promised to anyone. And the reader gets the link only when its acquire actually sees the release. If C reads `false` and the code goes on to read `rates` anyway, nothing is promised.",
    "You rarely need to build these chains by hand. `java.util.concurrent` writes down its own handovers in its documentation, under \"Memory Consistency Properties\". Among them:",
    "- putting an object into any concurrent collection (one built for many threads, such as `ConcurrentHashMap` or a `BlockingQueue`) happens-before another thread gets or removes it;\n- handing a task to an executor, an object that runs tasks on threads of its own, happens-before the task starts;\n- whatever a task does happens-before `Future.get()` returns its result in another thread (a `Future` stands for the result of a task that may not have finished yet);\n- `countDown()`, `release()` and `unlock()` happen-before a successful `await()`, `acquire()` or `lock()` on the same object in another thread.",
    "The kitchen in Don't share relied on the first of these. Everything a waiter wrote on a ticket before `put` was visible to the cook after `take`. The ticket needed no volatile fields, as long as the waiter stopped writing on it after `put`. Prefer these ready-made handovers to flags of your own. A `CountDownLatch`, the gate from Synchronizers that opens when its count reaches zero, waits without spinning, answers interrupts, and its handover is written down in its documentation.",
    "**Write everything before the handover, and read it after. Then one handover covers it all.**",
    "Every handover we've met either makes someone wait (a lock, `join()`, a latch) or uses a volatile field, which makes nobody wait. That makes volatile look like the cheap tool for every job. How far it really goes is a question for the next lesson.",
)

L = {
 "id": "jmm-02",
 "title": "Happens-before, the rules that matter",
 "minutes": 35,
 "goal": "By the end you can name the happens-before handover that makes a read see a write, spot a data race where no handover exists, and fix it with the right lock, volatile field, join or java.util.concurrent tool.",
 "opening": OPENING,
 "warmup": {
  "q": "A bank's `deposit` method is `synchronized` and adds to `balance`. A report thread reads the balance through a plain getter, `balance()`, that takes no lock. Is the report sure to see the latest balance?",
  "options": [
   "Yes, because the write happened inside a lock",
   "Yes, as long as the getter runs after the deposit on the clock",
   "No, because the reader never takes the lock, so nothing links the two threads",
   "No, because a synchronized method can't run while another thread reads the field"
  ],
  "answer": 2,
  "why": "A lock links threads only when both sides use it: the writer's release pairs with the reader's acquire of the same lock. The getter takes no lock, so its read races with the write. The answer about the clock is the tempting one, and the clock is exactly what happens-before is not about."
 },
 "sections": [
  {
   "h": "Happens-before: a promise about what a read will see, not about when",
   "body": S0,
   "aside": ASIDE
  },
  {
   "h": "The same lock or the same field: the two handovers you'll use most",
   "body": S1,
   "figure": {"svg": FIG, "caption": "The cashier's release of the lock pairs with the night manager's acquire of the same lock. Program order on both sides stretches the promise to every write before the release and every read after the acquire."},
   "try": {
    "title": "Same lock or own lock",
    "minutes": 4,
    "steps": [
     "Read `LockScopeDemo` (either language). The writer sets `balance` inside `synchronized (LEDGER_LOCK)`. By default, the reader locks a fresh `new Object()` (`Any()` in Kotlin) on every pass.",
     "Run it with the Gradle command below, and check that you get the first output above.",
     "Run it again with `-Pargs=shared` added to the command, so the reader locks `LEDGER_LOCK` too.",
     "Now go back to the default reader, but make `balance` a `volatile` field (`@Volatile` in Kotlin). Predict first: will the reader with its own useless lock see the balance now?"
    ],
    "code": {"lang": "java", "title": "LockScopeDemo.java", "src": read(demo("LockScopeDemo")), "run": run("LockScopeDemo"), "file": demo("LockScopeDemo"),
             "alt": {"lang": "kotlin", "title": "LockScopeDemo.kt", "src": read(kdemo("LockScopeDemo")), "run": run("LockScopeDemoKt"), "file": kdemo("LockScopeDemo")}},
    "expect": "With its own lock, the reader is still spinning 3 seconds later: there's no link, the JIT removes the useless lock and reads `balance` once. With `-Pargs=shared`, the reader prints `balance = 12000` right after the writer, because the writer releases and the reader acquires the same monitor. With a volatile `balance`, the own-lock reader sees 12000 too. The lock still links nothing, but the volatile write and read of the same field are a handover of their own."
   }
  },
  {
   "h": "Starting and joining a thread are handovers; sleeping is not",
   "body": S2,
   "try": {
    "title": "Replace a sleep with a join",
    "minutes": 4,
    "steps": [
     "Read `SleepIsNotJoinDemo` (either language). The worker makes 20 calls of about 10 ms each, then writes `total`. Predict what `main` prints.",
     "Run it with the Gradle command below.",
     "Replace `Thread.sleep(50)` with `worker.join()` and run it again.",
     "Think it through: would `Thread.sleep(5_000)` be a correct fix? Which rule would it be missing?"
    ],
    "code": {"lang": "java", "title": "SleepIsNotJoinDemo.java", "src": read(demo("SleepIsNotJoinDemo")), "run": run("SleepIsNotJoinDemo"), "file": demo("SleepIsNotJoinDemo"),
             "alt": {"lang": "kotlin", "title": "SleepIsNotJoinDemo.kt", "src": read(kdemo("SleepIsNotJoinDemo")), "run": run("SleepIsNotJoinDemoKt"), "file": kdemo("SleepIsNotJoinDemo")}},
    "expect": "The first run prints `total = 0`: the worker is only about a quarter of the way through. With `join()` it prints `2,000,000` every time, because `join()` waits for the worker to end, and its handover makes the write visible. A 5-second sleep would print the right number on a quiet machine, but it's still a data race: no rule links the worker's write to the read in `main`."
   }
  },
  {
   "h": "Promises chain: one handover carries every write made before it",
   "body": S3,
   "try": {
    "title": "Name the handover",
    "minutes": 4,
    "steps": [
     "For each snippet, name the happens-before handover that makes the last read safe, or write \"none\".",
     "(a) `order.setTotal(500); executor.submit(() -> pack(order));` and the task reads `order.total()`.",
     "(b) `queue.put(ticket); ticket.setNote(\"no onions\");` and the cook calls `queue.take().note()`.",
     "(c) T1: `x = 1; v = 1;` T2: `if (w == 1) print(x);` where `v` and `w` are two different volatile fields.",
     "(d) T1: `synchronized (ledger) { total += 5; }` T2: `synchronized (ledger) { print(total); }`."
    ],
    "expect": "(a) Handing the task to the executor: writes before `submit` happen-before the task starts. (b) None for the note: `setNote` runs after `put`, so the cook may see the old value. (c) None: the volatile write and the volatile read are on different fields. (d) The lock rule on `ledger`, as long as T1's block ran first."
   },
   "refs": [
    {"title": "java.util.concurrent package docs, \"Memory Consistency Properties\" (JDK 25 source)", "url": "https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/package-info.java", "kind": "docs"}
   ]
  }
 ],
 "compare": {
  "title": "The same lock on both sides, in Java and Kotlin",
  "java": {"title": "LedgerTotals.java", "src": "public class LedgerTotals {\n    private long total;   // guarded by this\n\n    public synchronized void add(long cents) {\n        total += cents;\n    }\n\n    // hb: the release at the end of add() pairs with the acquire here\n    public synchronized long total() {\n        return total;\n    }\n}"},
  "kotlin": {"title": "LedgerTotals.kt", "src": "class LedgerTotals {\n    private val lock = Any()\n    private var totalCents = 0L   // guarded by lock\n\n    fun add(cents: Long) {\n        synchronized(lock) { totalCents += cents }\n    }\n\n    // hb: same lock object on both sides\n    fun total(): Long = synchronized(lock) { totalCents }\n}"},
  "note": "Both classes take the same lock to write and to read, so every `total()` sees every `add()` that came before it. Kotlin's `synchronized(lock) { }` is a function from the standard library, not a keyword. It is inlined, which means its body is copied into the caller, and it compiles to the same monitor enter and exit bytecode as a Java `synchronized` block, so it creates exactly the same links. Kotlin code often locks a private `val lock = Any()` instead of `this`, which keeps outside code from taking your lock. Both languages offer locked methods on `this` too: Java's `synchronized` modifier and Kotlin's `@Synchronized`. `CountDownLatch`, executors and `Future.get()` give the same handovers from either language."
 },
 "worked": {
  "title": "Find the missing handover when an order goes to a pool",
  "steps": [
   {"say": "A shop's website takes orders. A receiving thread builds an `Order` object for each one and hands it to a pool of packing threads through an executor, an object that runs tasks on threads of its own. Then, for timing, it notes when the order arrived. The packers log how long each order waited, and about one log line in a thousand says `receivedAt=null`. List each write, each read, and the thread that makes it.", "code": "void onOrder(String text) {                       // the receiving thread\n    Order order = Order.parse(text);              // 1. build a changeable object\n    packers.submit(() -> pack(order));            // 2. hand it to a pool thread\n    order.setReceivedAt(Instant.now());           // 3. one more write, after the handover\n}", "lang": "java", "alt_lang": "kotlin", "alt_code": "fun onOrder(text: String) {                       // the receiving thread\n    val order = Order.parse(text)                 // 1. build a changeable object\n    packers.execute { pack(order) }               // 2. hand it to a pool thread\n    order.receivedAt = Instant.now()              // 3. one more write, after the handover\n}"},
   {"say": "Draw the links. The writes in step 1 come before `submit` in program order, and `submit` happens-before the task starts, so the packer sees them. The write in step 3 comes after `submit`, and nothing links it to the packer. The packer's read of `receivedAt` is a data race. It usually reads the new value, because the task starts a little later, which is why it fails only now and then.", "code": "", "lang": ""},
   {"say": "Put every write before the release, and stop touching the object after it. Then the one handover covers all of it.", "code": "void onOrder(String text) {\n    Order order = Order.parse(text);\n    order.setReceivedAt(Instant.now());          // 1. every write happens before the release\n    packers.submit(() -> pack(order));           // 2. submit carries them all to the packer\n    // 3. no writes to order after this line\n}", "lang": "java", "alt_lang": "kotlin", "alt_code": "fun onOrder(text: String) {\n    val order = Order.parse(text)\n    order.receivedAt = Instant.now()             // 1. every write happens before the release\n    packers.execute { pack(order) }              // 2. the handover carries them all to the packer\n    // 3. no writes to order after this line\n}"},
   {"say": "If the receiving thread needs the packer's answer, `Future.get()` is the handover back: everything the task did happens-before `get()` returns. No field in `Order` or in the answer needs to be `volatile`. Better still, make the order a record (Java's class for plain data that never changes, or a Kotlin `data class` with only `val` properties) built once with all its fields, and the question of later writes can't come up.", "code": "Future<Label> f = packers.submit(() -> pack(order));\nLabel label = f.get(2, TimeUnit.SECONDS);   // hb: the task's actions happen-before get() returns", "lang": "java", "alt_lang": "kotlin", "alt_code": "val f: Future<Label> = packers.submit(Callable { pack(order) })\nval label = f.get(2, TimeUnit.SECONDS)   // hb: the task's actions happen-before get() returns"}
  ]
 },
 "lab": {
  "title": "Name the handover, then fix three of them",
  "minutes": 13,
  "files": [
   "labs/jmm/src/main/java/workbench/jmm/l02/LedgerTotals.java",
   "labs/jmm/src/main/java/workbench/jmm/l02/IssuerReply.java",
   "labs/jmm/src/main/java/workbench/jmm/l02/PartitionReconciler.java"
  ],
  "run": "./gradlew :jmm:test --tests 'workbench.jmm.l02.*'",
  "steps": [
   "Meet the three classes. `LedgerTotals` keeps a bank's running total: many threads call `add`, and a report thread waits in `awaitAtLeast` until the day's entries are in. `IssuerReply` carries one answer from the thread that talks to the card company (the issuer, the bank that gave out the card) to the thread that waits for it. `PartitionReconciler` splits a big sum into parts, adds up each part on its own thread, then adds the parts together.",
   "Run the tests once. Three of the five fail. The two \"still waiting\" tests each wait 5 seconds for a stuck thread.",
   "`LedgerTotals`: give `total()` a handover from `add()`. Add a `// hb:` comment that names the rule.",
   "`IssuerReply`: replace the `boolean done` with a `CountDownLatch` of 1. Count it down after writing the fields, and `await()` it before reading them. Add the `// hb:` comment.",
   "`PartitionReconciler`: keep one thread per part, but replace the sleep with a wait that is also a handover. Add `// hb:` comments for the handover that lets the workers see `sums` and the one that lets the caller see their results.",
   "Run the tests until all five pass, then twice more."
  ],
  "hints": [
   "`LedgerTotals` has two correct fixes: make `total()` synchronized, or make the field `volatile`. Either way `add` stays synchronized, because `+=` is a read and a write.",
   "`CountDownLatch.await()` throws `InterruptedException`. That's why `awaitReply()` already declares it.",
   "In `PartitionReconciler`, collect the threads in a list as you start them, and join them in a second loop. Joining inside the first loop would add up the parts one after another."
  ],
  "done_when": "All five tests in `HappensBeforeTest` pass, three runs in a row."
 },
 "drill": {
  "title": "A one-shot result slot from memory",
  "minutes": 5,
  "prompt": "Close this page. Write `OneShot<T>` with `void set(T value)`, called once by a producer thread, and `T get()`, which blocks until the value is set. Use a `CountDownLatch` and no `volatile`. Mark the happens-before handover in a comment. Then compare.",
  "answer": {"lang": "java", "src": "public final class OneShot<T> {\n    private final CountDownLatch done = new CountDownLatch(1);\n    private T value;   // plain: the latch orders it\n\n    public void set(T v) {\n        value = v;          // 1. write\n        done.countDown();   // 2. release\n    }\n\n    // hb: actions before countDown() happen-before actions after await() returns\n    public T get() throws InterruptedException {\n        done.await();       // 3. acquire\n        return value;       // 4. sees the write from step 1\n    }\n}", "alt": {"lang": "kotlin", "src": "class OneShot<T> {\n    private val done = CountDownLatch(1)\n    private var value: T? = null   // plain: the latch orders it\n\n    fun set(v: T) {\n        value = v          // 1. write\n        done.countDown()   // 2. release\n    }\n\n    // hb: actions before countDown() happen-before actions after await() returns\n    fun get(): T {\n        done.await()       // 3. acquire\n        @Suppress(\"UNCHECKED_CAST\")\n        return value as T  // 4. sees the write from step 1\n    }\n}"}}
 },
 "recap": [
  "A write is sure to be seen by a read in another thread only if the write happens-before the read.",
  "Happens-before is a promise about what a read sees, not about which line ran first on the clock.",
  "The handovers to know: program order, releasing and then acquiring the same lock, a volatile write and a read of the same field that sees it, `start()`, `join()`, and the `java.util.concurrent` handoffs.",
  "Promises chain, so plain writes made before a release are visible after the matching acquire.",
  "`sleep`, a different lock or a different volatile field links nothing. No link between a write and a read of shared data means a data race.",
  "The limit: happens-before says what a read sees, not that a group of steps runs as one. Volatile gives a handover with no waiting, and the next lesson asks what that buys."
 ],
 "closing": "We started with a cashier who locked the ledger in its cabinet and left the key for the night manager. Threads get the same promise from the same kind of handover: the same lock, the same volatile field, `start()` and `join()`, or a tool from `java.util.concurrent`. A later time on the clock gives no promise at all.\n\nNow pick a class in your own code that two threads share. Next to each field, write a `// hb:` comment that names the handover linking its writes to its reads. Any field where you can't finish the comment is a data race.\n\nNext, we'll take the handover that makes nobody wait, `volatile`, and ask what exactly it gives you, and what it doesn't.",
 "quiz": [
  {
   "q": "`setBalance` writes inside `synchronized (ledgerLock)`. `getBalance` reads inside `synchronized (reportLock)`. Is the getter sure to see the latest balance?",
   "options": [
    "Yes, because both methods are synchronized",
    "No: the link exists only between releasing a lock and a later acquire of the same lock",
    "Yes, because entering any synchronized block refreshes all fields from memory",
    "No, because a field can't be read inside a synchronized block"
   ],
   "answer": 1,
   "why": "Two different locks give no link. The idea that any `synchronized` block refreshes everything comes from picturing locks as memory barriers, instructions that stop reordering across them. The JMM promises the link only for the same lock, and the JIT is allowed to optimize with that in mind."
  },
  {
   "q": "T1 runs `x = 1; v = 1;` where `v` is volatile and `x` is plain. T2 reads `v` and gets 0, then reads `x`. What can T2 see for `x`?",
   "options": [
    "Always 0, because T1 hasn't written `v` yet",
    "Always 1, because volatile flushes every earlier write",
    "Either 0 or 1: T2's read of `v` didn't see the write, so no handover covers `x`",
    "It throws, because reading a plain field next to a volatile is illegal"
   ],
   "answer": 2,
   "why": "The volatile handover forms only when the read sees the write. T2 saw 0, so it has no link to T1's writes, and its read of `x` races with `x = 1`. T1 may well have written `x` already, which is why \"always 0\" is wrong too."
  },
  {
   "q": "`main` fills a plain `HashMap` with 10,000 entries, then calls `executor.submit(() -> lookup(map))` and never touches the map again. Is the task's read safe?",
   "options": [
    "Yes: handing a task to an executor happens-before the task starts, and nobody writes after that",
    "No, because `HashMap` is not thread-safe",
    "Only if the map field is volatile",
    "Only if you switch to `ConcurrentHashMap`"
   ],
   "answer": 0,
   "why": "`HashMap` is unsafe when threads write to it at the same time, but here every write comes before the handover and none after. The submit handover makes them visible to the task. Volatile or `ConcurrentHashMap` would add cost and no safety."
  },
  {
   "q": "A worker thread writes `result`. Which of these does NOT give `main` a happens-before link to that write?",
   "options": [
    "`worker.join()` returns",
    "`future.get()` returns, where the worker is the future's task",
    "`latch.await()` returns, after the worker wrote and then called `latch.countDown()`",
    "`Thread.sleep(1_000)` returns"
   ],
   "answer": 3,
   "why": "`join`, `Future.get` and the latch all document their handovers. `sleep` only passes time. The worker may not be done, and even if it is, a read after a sleep still races with its write."
  },
  {
   "q": "From lesson 1 of this track: you add `Thread.onSpinWait()` to a spin loop on a plain flag, and the loop starts noticing the flag. In memory model terms, what changed?",
   "options": [
    "The loop now has a happens-before link to the writer",
    "Nothing: there is still no link, HotSpot just happens to read the field again",
    "`onSpinWait` makes the next read volatile",
    "`onSpinWait` empties the writer's store buffer"
   ],
   "answer": 1,
   "why": "`onSpinWait` is a hint to the processor, with no synchronization effect in the JMM. HotSpot happens to read the field again after it today. The program still has a data race on the flag, and only a volatile, a lock or another real handover fixes it.",
   "from": "jmm-01"
  }
 ],
 "flashcards": [
  {"front": "When is a write in one thread sure to be visible to a read in another?", "back": "Only when the write happens-before the read."},
  {"front": "State the lock rule of happens-before.", "back": "Releasing a lock happens-before every later acquisition of the same lock."},
  {"front": "T1 writes inside `synchronized (a)`. T2 reads inside `synchronized (b)`. Is there a link?", "back": "No. The link needs the same lock on both sides."},
  {"front": "State the volatile rule of happens-before.", "back": "A write to a volatile field happens-before every read of that same field that sees it (or a later write)."},
  {"front": "What does `Thread.start()` promise the new thread?", "back": "Everything the parent did before calling `start()` is visible to the new thread. Writes after `start()` are not covered."},
  {"front": "Is `Thread.sleep(100)` a happens-before link?", "back": "No. Use `join()`, `Future.get()` or a latch."},
  {"front": "What is a data race?", "back": "Two threads access the same variable, at least one access is a write, and no happens-before link orders them."}
 ],
 "terms": [
  {"term": "Happens-before", "plain": "The memory model's ordering between two actions. If a write happens-before a read, the read sees it."},
  {"term": "Program order", "plain": "The order of actions within one thread, as the code is written."},
  {"term": "Release", "plain": "The sending end of a handover: leaving a lock, writing a volatile, `countDown()`, `put` into a concurrent queue."},
  {"term": "Acquire", "plain": "The receiving end of a handover: entering a lock, reading a volatile, `await()`, `take` from a concurrent queue."},
  {"term": "Data race", "plain": "Conflicting accesses to one variable from two threads with no happens-before link between them."},
  {"term": "DRF-SC", "plain": "The JMM promise: a program free of data races behaves as if its threads were shuffled together one action at a time."},
  {"term": "Piggybacking", "plain": "Relying on transitivity, so one volatile or lock handover also publishes the plain writes made before it."}
 ],
 "explain_back": {
  "prompt": "In lesson 1 of this track, `FxRateBoard` kept `rates` as a plain field and made only `ready` volatile. Explain in your own words why the reader is sure to see the map. Use the words release, acquire and program order.",
  "answer": "The loader writes `rates` and then writes `ready`, so by program order the write of `rates` happens-before the write of `ready`. The write of the volatile `ready` is a release. The reader's read of `ready` is an acquire, and when it sees `true` it pairs with that release, so the write of `ready` happens-before the read. After the loop, the reader reads `rates`, which comes later in its program order. Chaining the three links, the write of `rates` happens-before the read of `rates`, so the reader sees the map. It only works because `rates` is written before `ready`, and read after the loop sees `true`."
 },
 "deeper": {
  "minutes": 10,
  "body": "Two refinements are worth knowing once the basic rules feel natural.\n\nFirst, the JLS builds happens-before from a smaller relation called **synchronizes-with**. Each synchronizes-with link joins a release in one thread to an acquire in another: releasing a monitor to a later acquire of the same monitor, a volatile write to a read that sees it, `start()` to the first action of the new thread, a thread's last action to a `join()` that returns. Happens-before is then program order plus synchronizes-with, chained by transitivity. Apart from a link into finalizers, that's the whole construction. All the synchronization actions in a run also fall into one total order, which is why every thread sees two volatile writes in the same order.\n\nSecond, a lock is not a memory fence, an instruction that stops the processor and the compiler from moving memory operations across it. It's tempting to picture `synchronized` as \"flush everything on exit, reload everything on entry\". The JMM promises less, and the JIT uses the difference. The jcstress sample `AdvancedJMM_01_SynchronizedBarriers` writes `x` and `y` in two back-to-back `synchronized (this)` blocks, and an observer that takes no lock reads them with volatile reads. On x86 the observer saw the new `y` with the old `x` in 207,479 of about four billion samples. The JIT had merged the two blocks into one (lock coarsening) and reordered the writes inside it. That's legal: only a thread that also locks `this` is owed the order.\n\nAleksey Shipilëv's \"Close Encounters of The Java Memory Model Kind\" walks through more misreadings like these, each with a jcstress test."
 },
 "sources": [
  {"title": "java.util.concurrent package summary (Java SE 25 API), Memory Consistency Properties", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/package-summary.html"},
  {"title": "Java Language Specification, chapter 17: Threads and Locks", "url": "https://docs.oracle.com/javase/specs/jls/se25/html/jls-17.html"},
  {"title": "Aleksey Shipilëv, Close Encounters of The Java Memory Model Kind", "url": "https://shipilev.net/blog/2016/close-encounters-of-jmm-kind/"},
  {"title": "jcstress samples (AdvancedJMM_01_SynchronizedBarriers)", "url": "https://github.com/openjdk/jcstress/tree/master/jcstress-samples"}
 ]
}
out = ROOT / "content/lessons/jmm-02.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
