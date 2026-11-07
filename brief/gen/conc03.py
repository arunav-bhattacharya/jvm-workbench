import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/concurrency/src"
P = "java/workbench/concurrency/l03"
K = "kotlin/workbench/concurrency/l03"
read = lambda p: (ROOT / p).read_text()

L = {
 "id": "conc-03",
 "title": "Race conditions: why count++ lies",
 "minutes": 35,
 "goal": "By the end you can spot the two shapes of race condition (read-modify-write and check-then-act) in real code, and fix each with one atomic step.",
 "warmup": {
  "q": "Two threads each run `count++` one million times on a shared `int count = 0`. What does `count` hold at the end, most of the time?",
  "options": ["Exactly 2,000,000", "Less than 2,000,000, and a different number each run", "More than 2,000,000", "The program throws a ConcurrentModificationException"],
  "answer": 1,
  "why": "Each `count++` is a read, an add and a write. When both threads read the same old value, one of the two increments is lost. How many are lost depends on timing, so the result changes from run to run. Nothing throws: Java does not detect races for you."
 },
 "sections": [
  {
   "h": "Two threads, one counter, the wrong answer",
   "body": "Here is the smallest broken program in this course. Two threads share one counter, and each adds one to it a million times.\n\n```java\nstatic volatile int count = 0;\n\nRunnable work = () -> {\n    for (int i = 0; i < 1_000_000; i++) count++;\n};\nThread a = new Thread(work), b = new Thread(work);\na.start(); b.start();\na.join(); b.join();\nSystem.out.println(count);   // 2,000,000? Usually not.\n```\n\n```kotlin\n@Volatile var count = 0\n\nval work = { repeat(1_000_000) { count++ } }\nval a = thread { work() }\nval b = thread { work() }\na.join(); b.join()\nprintln(count)               // 2,000,000? Usually not.\n```\n\nOn my laptop five runs printed 1,851,852, then 1,633,408, then 1,920,984, then 1,599,468, then 2,000,000. Four wrong answers and one right one, from the same code.\n\nThis is a **race condition**: the result depends on how the threads happen to interleave. Nothing crashed. No exception, no warning, no log line. The program just did arithmetic wrong, and it did it differently each time.\n\nTwo details are worth knowing now.\n\nThe field is `volatile` (`@Volatile` in Kotlin) only to keep the demo honest. Without it the JIT compiler may keep `count` in a CPU register for the whole loop and write it back once at the end, which makes the lost updates disappear on some runs. That does not fix anything. It just hides the bug. `volatile` does not make `count++` safe either; the memory model track shows exactly why.\n\nThe second detail matters more. Shrink the loop to 1,000 and every run prints the right answer. The first thread finishes before the second one even starts, so they never overlap. That is why races pass unit tests and fail under production traffic. A test that never makes threads collide proves nothing about thread safety.",
   "try": {
    "title": "Watch the counter lie",
    "minutes": 4,
    "steps": [
     "Open `RaceDemo.java` (or its Kotlin twin, `RaceDemo.kt`) in the labs project. Before you run it, write down the number you expect.",
     "Run it from `labs/` with the command below. Note how many updates each run loses.",
     "Run it again with `-Pargs=1000` added. Predict first: will small loops lose updates?"
    ],
    "code": {"lang": "java", "title": "RaceDemo.java", "src": read(f"{lab}/demo/{P}/RaceDemo.java"),
             "run": "./gradlew :concurrency:demo -Pmain=workbench.concurrency.l03.RaceDemo",
             "file": f"{lab}/demo/{P}/RaceDemo.java",
             "alt": {"lang": "kotlin", "title": "RaceDemo.kt", "src": read(f"{lab}/demo/{K}/RaceDemo.kt"),
                     "run": "./gradlew :concurrency:demo -Pmain=workbench.concurrency.l03.RaceDemoKt",
                     "file": f"{lab}/demo/{K}/RaceDemo.kt"}},
    "expect": "With a million per thread, most runs lose tens or hundreds of thousands of updates, and the number changes every run. With 1,000 per thread you almost always get exactly 2,000, because each thread finishes before the other gets going. Same bug, no symptom."
   }
  },
  {
   "h": "count++ is three steps, not one",
   "body": "`count++` looks like one operation. The JVM runs it as three. Here is the bytecode `javac` produces for it:\n\n```text\ngetstatic  count   // read the current value onto the stack\niconst_1           // push 1\niadd               // add them\nputstatic  count   // write the result back\n```\n\nA thread can be paused between any two of those instructions. The operating system can move it off the CPU, or another core can run the same instructions at the same moment. So this can happen:\n\n1. T1 reads `count`: 41.\n2. T2 reads `count`: 41.\n3. T1 adds one and writes 42.\n4. T2 adds one and writes 42.\n\nTwo increments ran. The counter moved by one. This is a **lost update**, and the pattern behind it has a name: **read-modify-write**. You read a value, compute a new one from it, and write it back, while assuming nobody changed it in between.\n\nOnce you know the shape, you see it everywhere:\n\n- `balance = balance - amount;`\n- `map.put(key, map.get(key) + 1);`\n- `total += invoice.amount();`\n- `list.add(x)` on an `ArrayList`, which does `size++` inside.\n\nNone of these is safe when two threads run it on shared data. The fix is always the same idea: the read and the write must happen as one step that no other thread can split. That property is called **atomic**.\n\nThe simulator below lets you play the scheduler. You pick which thread runs its next step. Try to make two increments end with `count = 1`. Then try to get 2. Notice that you need the threads to take turns on whole increments to get the right answer.",
   "sim": {
    "title": "Two threads run count++",
    "intro": "You are the scheduler. Click a thread to run its next line. Can you end with count = 1?",
    "vars": {"count": 0},
    "threads": [
     {"name": "T1", "steps": [
      {"op": "read", "var": "count", "reg": "r", "code": "int r = count;"},
      {"op": "add", "reg": "r", "n": 1, "code": "r = r + 1;"},
      {"op": "write", "var": "count", "reg": "r", "code": "count = r;"}]},
     {"name": "T2", "steps": [
      {"op": "read", "var": "count", "reg": "r", "code": "int r = count;"},
      {"op": "add", "reg": "r", "n": 1, "code": "r = r + 1;"},
      {"op": "write", "var": "count", "reg": "r", "code": "count = r;"}]}
    ],
    "goal": {"var": "count", "eq": 1, "say": "Lost update. Both threads read 0 before either wrote, so two increments produced 1."}
   },
   "try": {
    "title": "See the three steps yourself",
    "minutes": 3,
    "steps": [
     "Run the demo once (previous Try it) so Gradle compiles it.",
     "From `labs/`, run the `javap` command below. It prints the bytecode of the class.",
     "Find the lambda method (`lambda$main$0`) and the four lines that make up `count++`."
    ],
    "code": {"lang": "bash", "title": "terminal", "src": "javap -c -p concurrency/build/classes/java/demo/workbench/concurrency/l03/RaceDemo.class", "run": ""},
    "expect": "Inside `lambda$main$0` you'll see `getstatic count`, `iconst_1`, `iadd`, `putstatic count`. A thread can be paused between any two of them."
   },
   "refs": [
    {"title": "Thread interference (The Java Tutorials)", "url": "https://docs.oracle.com/javase/tutorial/essential/concurrency/interfere.html", "kind": "read"}
   ]
  },
  {
   "h": "Check-then-act: the race inside an if",
   "body": "The second shape of race hides in an `if`. You check a condition, then act on it, assuming the condition still holds.\n\n```java\nif (!owners.containsKey(seat)) {   // check\n    owners.put(seat, passenger);   // act\n    return true;\n}\nreturn false;\n```\n\n```kotlin\nif (!owners.containsKey(seat)) {   // check\n    owners[seat] = passenger       // act\n    return true\n}\nreturn false\n```\n\n`owners` is a `ConcurrentHashMap`. Every single call on it is thread-safe. The code still sells the same seat twice, because the gap between `containsKey` and `put` belongs to nobody. Two buyers can both see the seat as free, and both go on to buy it. The second `put` silently replaces the first owner, and both callers got `true`.\n\nThis is the point most people miss: **a thread-safe class does not make your code thread-safe.** Each method is atomic. Two calls in a row are not.\n\nThe gap is often much wider than one line. Here is a version you may have written:\n\n```java\nif (!processed.contains(msg.idempotencyKey())) {\n    ledger.charge(msg);                     // 80 ms call to the card issuer\n    processed.add(msg.idempotencyKey());\n}\n```\n\n```kotlin\nif (msg.idempotencyKey !in processed) {\n    ledger.charge(msg)                      // 80 ms call to the card issuer\n    processed += msg.idempotencyKey\n}\n```\n\nKafka redelivers a message after a consumer rebalance, and two consumer threads pick up both copies. Both check the set during the same 80 ms. The customer pays twice.\n\nLazy initialization is the same shape: `if (instance == null) instance = new Expensive();` can build two instances.\n\nThe fix is to let one operation do both the check and the act, so there is no gap:\n\n```java\nreturn owners.putIfAbsent(seat, passenger) == null;   // only one caller can see null\n```\n\n```kotlin\nreturn owners.putIfAbsent(seat, passenger) == null    // same JDK call from Kotlin\n```\n\nInside, the map does the lookup and the insert as one step on that key's slot, so no other thread can get in between. Lesson 9 of this track shows how. `putIfAbsent`, `computeIfAbsent`, `merge` and `Set.add` (which returns `false` when the element was already there) all exist for this reason. Across machines, the same idea is a unique constraint in the database: insert the key first, and let the second insert fail.",
   "figure": {
    "svg": "<svg viewBox=\"0 0 640 250\" role=\"img\" aria-label=\"Timeline: two buyers both check that seat 7 is free before either writes, so both buy it\"><text class=\"t-s t-m\" x=\"20\" y=\"24\">time</text><line class=\"ln-d\" x1=\"60\" y1=\"20\" x2=\"620\" y2=\"20\" marker-end=\"url(#arr)\"/><text class=\"t\" x=\"20\" y=\"86\">A</text><text class=\"t\" x=\"20\" y=\"176\">B</text><rect class=\"box\" x=\"60\" y=\"62\" width=\"150\" height=\"36\" rx=\"8\"/><text class=\"t t-code\" x=\"135\" y=\"85\" text-anchor=\"middle\">containsKey(7)</text><rect class=\"box\" x=\"130\" y=\"152\" width=\"150\" height=\"36\" rx=\"8\"/><text class=\"t t-code\" x=\"205\" y=\"175\" text-anchor=\"middle\">containsKey(7)</text><text class=\"t-s t-ok\" x=\"135\" y=\"116\" text-anchor=\"middle\">false: free</text><text class=\"t-s t-ok\" x=\"166\" y=\"206\" text-anchor=\"middle\">false: free</text><rect class=\"box-a\" x=\"330\" y=\"62\" width=\"130\" height=\"36\" rx=\"8\"/><text class=\"t t-code\" x=\"395\" y=\"85\" text-anchor=\"middle\">put(7, A)</text><rect class=\"box-bad\" x=\"420\" y=\"152\" width=\"130\" height=\"36\" rx=\"8\"/><text class=\"t t-code\" x=\"485\" y=\"175\" text-anchor=\"middle\">put(7, B)</text><rect class=\"box-dim\" x=\"215\" y=\"40\" width=\"110\" height=\"170\" rx=\"8\"/><text class=\"t-s t-bad\" x=\"270\" y=\"132\" text-anchor=\"middle\">the gap</text><text class=\"t-s t-bad\" x=\"485\" y=\"230\" text-anchor=\"middle\">overwrites A; both got true</text></svg>",
    "caption": "Both buyers check before either one writes. The gap between check and act is where the race lives."
   },
   "try": {
    "title": "Double-book a concert",
    "minutes": 5,
    "steps": [
     "Run `DoubleBookingDemo` with the command below. Eight buyers race for 1,000 seats.",
     "Change the check and the put into one call: `if (owners.putIfAbsent(seat, me) == null) sold.incrementAndGet()` in either version (keep the spin loop before it).",
     "Run it again."
    ],
    "code": {"lang": "java", "title": "DoubleBookingDemo.java", "src": read(f"{lab}/demo/{P}/DoubleBookingDemo.java"),
             "run": "./gradlew :concurrency:demo -Pmain=workbench.concurrency.l03.DoubleBookingDemo",
             "file": f"{lab}/demo/{P}/DoubleBookingDemo.java",
             "alt": {"lang": "kotlin", "title": "DoubleBookingDemo.kt", "src": read(f"{lab}/demo/{K}/DoubleBookingDemo.kt"),
                     "run": "./gradlew :concurrency:demo -Pmain=workbench.concurrency.l03.DoubleBookingDemoKt",
                     "file": f"{lab}/demo/{K}/DoubleBookingDemo.kt"}},
    "expect": "The first run sells a few hundred tickets too many (one run here printed 1,413 tickets for 1,000 seats). After the change it sells exactly 1,000, every run, with the same slow step still inside the loop."
   }
  },
  {
   "h": "What a fix has to do",
   "body": "Every fix for a race does two jobs. It makes the compound action **atomic**, so no other thread can run in the middle of it. And it makes the result **visible**, so the next thread to look sees the new value and not an old copy. Visibility gets its own track later. For now, know that the tools below give you both.\n\nHere are your options, in the order I reach for them:\n\n1. **Don't share.** Give each thread its own counter and add them up at the end. Or keep the state inside one thread, such as one Kafka partition handled by one consumer. No sharing, no race.\n2. **Use one atomic operation the library already has.** `AtomicInteger.incrementAndGet()`, `LongAdder.increment()`, `ConcurrentHashMap.merge(key, 1, Integer::sum)`, `putIfAbsent`, `Set.add`. These are fast and hard to get wrong. Lesson 8 shows how they work.\n3. **Lock the whole compound action.** Mark the method `synchronized` so only one thread at a time can run it. This works for any code, including the slow 80 ms charge, but every caller now waits in line. Lesson 4 is about `synchronized`.\n\nThe lock must cover the read too. A `synchronized` setter with an unsynchronized getter is still broken. Taking the same lock is what makes a thread see the last owner's writes, so a reader that skips it can keep using an old value, for example a copy the JIT kept in a register, as in the first section. And it must cover the whole action. Locking `containsKey` and `put` separately just gives you two atomic steps with the same gap between them.\n\nFor the counter, the cheapest correct fix is to put `count++` inside a `static synchronized void inc()` method, or to swap the `int` for an `AtomicInteger`. Either way the demo prints 2,000,000 on every run.",
   "try": {
    "title": "Fix RaceDemo two ways",
    "minutes": 5,
    "steps": [
     "In `RaceDemo`, add `static synchronized void inc() { count++; }` and call `inc()` in the loop. Run it.",
     "Undo that. Change `count` to `static final AtomicInteger count = new AtomicInteger();`, call `count.incrementAndGet()`, reset it with `count.set(0)` and print `count.get()`. Run it.",
     "Which one felt slower? Add `long t0 = System.nanoTime();` before the threads start and print the elapsed milliseconds after the joins to check."
    ],
    "expect": "Both versions print exactly 2,000,000 on all five runs. On a typical laptop the atomic version is faster than the synchronized one when two threads fight over the counter, though both are much slower than the broken version. Correct code that does real synchronization costs something."
   }
  }
 ],
 "analogy": "Picture two cashiers sharing one paper tally sheet. Each reads the total, adds their sale on a scrap of paper, and writes the new total over the old one. If both read 41 before either writes, both write 42 and one sale disappears from the books. The fix is to pass a single pen: whoever holds it does read, add and write before handing it over. The analogy breaks in one way: cashiers would notice the sheet changed under them. A CPU never notices. It writes 42 without complaint.",
 "in_your_world": "Look for the daily spend limit check in a payment service: `if (spentToday + amount <= limit) { approve(); spentToday += amount; }`. Two authorizations for the same card arrive 3 ms apart on two Quarkus worker threads. Both read `spentToday` before either adds to it, and the card goes over its limit. The same shape appears in Kafka consumers with concurrency above 1, in in-memory metrics counters, and in Temporal activities that check \"already done?\" before doing work. Activities can be retried, so make that check a single atomic step, ideally a database insert guarded by a unique key.",
 "mistake": "The most common mistake is trusting a thread-safe collection to make compound logic safe. `ConcurrentHashMap`, `Collections.synchronizedMap` and `ConcurrentLinkedQueue` make each method call atomic. They say nothing about two calls in a row. Code like `if (!map.containsKey(k)) map.put(k, v)` or `map.put(k, map.get(k) + 1)` is still a race. Reach for the single method that does the whole job: `putIfAbsent`, `computeIfAbsent`, `merge` or `compute`.",
 "compare": {
  "title": "The same race and fix in Java and Kotlin",
  "java": {"title": "HitCounter.java", "src": "public class HitCounter {\n    private int count;\n\n    // broken: count++ is read, add, write\n    public void hitBroken() { count++; }\n\n    // fixed: one thread at a time\n    public synchronized void hit() { count++; }\n    public synchronized int total() { return count; }\n}"},
  "kotlin": {"title": "HitCounter.kt", "src": "class HitCounter {\n    private var count = 0\n\n    // broken: compiles to the same read, add, write\n    fun hitBroken() { count++ }\n\n    // fixed: Kotlin has no synchronized keyword; use the annotation\n    @Synchronized fun hit() { count++ }\n    @Synchronized fun total(): Int = count\n}"},
  "note": "Kotlin's `count++` on a `var` property compiles to the same three bytecode steps, so it races in exactly the same way. Kotlin has no `synchronized` modifier. You write `@Synchronized` on a function, or call the standard library function `synchronized(lock) { ... }` with an explicit lock object. `java.util.concurrent.atomic` works the same from both languages."
 },
 "worked": {
  "title": "Find and fix the race in an idempotency check",
  "steps": [
   {"say": "A payment handler skips messages it has already processed. It runs on four Kafka consumer threads. Read it and look for the shape before reading on.",
    "code": "class PaymentHandler {\n    private final Set<String> seen = ConcurrentHashMap.newKeySet();\n\n    void handle(PaymentMessage m) {\n        if (seen.contains(m.idempotencyKey())) return;   // check\n        ledger.charge(m);                                 // 80 ms\n        seen.add(m.idempotencyKey());                     // act\n    }\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "class PaymentHandler {\n    private val seen: MutableSet<String> = ConcurrentHashMap.newKeySet()\n\n    fun handle(m: PaymentMessage) {\n        if (m.idempotencyKey in seen) return             // check\n        ledger.charge(m)                                 // 80 ms\n        seen += m.idempotencyKey                         // act\n    }\n}"},
   {"say": "It is check-then-act. Two copies of the same message, handled by two threads within the same 80 ms, both pass the `contains` check. Both charge the card. The set being concurrent does not help, because the race is between the calls, not inside them.", "code": "", "lang": ""},
   {"say": "Claim the key first, in one atomic call. `Set.add` returns `false` if the key was already there, so only one thread gets past this line. If the charge fails, release the claim so a retry can try again.",
    "code": "void handle(PaymentMessage m) {\n    if (!seen.add(m.idempotencyKey())) return;   // check and act in one step\n    try {\n        ledger.charge(m);\n    } catch (RuntimeException e) {\n        seen.remove(m.idempotencyKey());          // let a retry have another go\n        throw e;\n    }\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "fun handle(m: PaymentMessage) {\n    // 1. claim the key: add() returns false if it was already there\n    if (!seen.add(m.idempotencyKey)) return\n    try {\n        ledger.charge(m)                         // 2. charge\n    } catch (e: RuntimeException) {\n        seen.remove(m.idempotencyKey)            // 3. release on failure\n        throw e\n    }\n}"},
   {"say": "That fixes the race inside one JVM. It does not survive a restart, and it does not cover two pods. In production the claim belongs in the database: insert the key into a table with a unique constraint before charging, and treat a duplicate-key error as \"already processed\". It is the same idea, one atomic step, moved to the place that all instances share.",
    "code": "INSERT INTO processed_payment (idempotency_key, received_at)\nVALUES (?, CURRENT_TIMESTAMP);   -- a second insert fails on the unique key", "lang": "sql"}
  ]
 },
 "lab": {
  "title": "Make threads collide, then fix two races",
  "minutes": 15,
  "files": [f"{lab}/main/{P}/Hammer.java", f"{lab}/main/{P}/HitCounter.java", f"{lab}/main/{P}/SeatMap.java"],
  "run": "./gradlew :concurrency:test --tests 'workbench.concurrency.l03.*'",
  "steps": [
   "Run the tests once. All five fail. Read the failure messages: the counter comes up short and seats are sold more than once.",
   "Write `Hammer.run`. Create a `CountDownLatch ready` of size `threads` and a `CountDownLatch go` of size 1. Each thread calls `ready.countDown()`, waits on `go.await()`, then runs the task. The caller waits on `ready`, calls `go.countDown()`, then joins every thread.",
   "Fix `HitCounter` so 8 threads x 200,000 hits always add up. Guard the read too.",
   "Fix `SeatMap.book` without `synchronized`: replace the check and the put with one map call. Keep the call to `priceTheSeat()`.",
   "Run the tests again until all five pass. Run them three more times. Race fixes must pass every time."
  ],
  "hints": [
   "Why two latches in `Hammer`? `ready` tells the caller every thread exists and is parked. `go` releases them all at the same instant. Without `ready`, the first threads could finish before the last ones are created.",
   "Inside a thread's lambda, `go.await()` throws `InterruptedException`. Catch it, restore the flag with `Thread.currentThread().interrupt()`, and return.",
   "`putIfAbsent` returns the previous value, or `null` if there was none. Only one caller can ever get `null` for a given key."
  ],
  "done_when": "All five tests in `RaceConditionsTest` pass, three runs in a row."
 },
 "drill": {
  "title": "Write the start-line harness from memory",
  "minutes": 5,
  "prompt": "Close this page and the lab. In a blank file, write a method `static void collide(int n, Runnable task)` that starts `n` threads, releases them at the same moment, and returns when all are done. Then compare with the answer. Did you remember to join?",
  "answer": {"lang": "java", "src": "static void collide(int n, Runnable task) throws InterruptedException {\n    CountDownLatch ready = new CountDownLatch(n);\n    CountDownLatch go = new CountDownLatch(1);\n    List<Thread> threads = new ArrayList<>();\n    for (int i = 0; i < n; i++) {\n        Thread t = new Thread(() -> {\n            ready.countDown();\n            try { go.await(); }\n            catch (InterruptedException e) { Thread.currentThread().interrupt(); return; }\n            task.run();\n        });\n        t.start();\n        threads.add(t);\n    }\n    ready.await();      // all parked at the start line\n    go.countDown();     // starting gun\n    for (Thread t : threads) t.join();\n}",
            "alt": {"lang": "kotlin", "src": "fun collide(n: Int, task: () -> Unit) {\n    val ready = CountDownLatch(n)\n    val go = CountDownLatch(1)\n    val threads = List(n) {\n        thread {\n            ready.countDown()\n            try { go.await() } catch (e: InterruptedException) { Thread.currentThread().interrupt(); return@thread }\n            task()\n        }\n    }\n    ready.await()      // all parked at the start line\n    go.countDown()     // starting gun\n    threads.forEach { it.join() }\n}"}}
 },
 "recap": [
  "A race condition is a bug where the result depends on how threads interleave. It gives wrong answers silently.",
  "Read-modify-write (`count++`, `balance -= x`, `put(k, get(k) + 1)`) loses updates when two threads read the same old value.",
  "Check-then-act (`if (!contains) put`, `if (x == null) x = new ...`) breaks when another thread acts in the gap.",
  "A thread-safe collection makes single calls atomic, never sequences of calls. Use `putIfAbsent`, `merge`, `computeIfAbsent` or `Set.add`.",
  "Fixes, in order of preference: don't share, use one atomic library call, or lock the whole compound action including reads.",
  "Races hide in small tests. Make threads collide on purpose, with a start latch, and run many iterations."
 ],
 "quiz": [
  {"q": "Two request threads run `account.balance = account.balance - amount;` on the same account at the same time. What can go wrong?",
   "options": ["Nothing, because one Java statement runs atomically", "One of the two debits can be lost, because both read the same starting balance", "The JVM throws an IllegalStateException", "The balance always goes negative"],
   "answer": 1, "why": "It's read-modify-write. If both threads read 100 and debit 10, both write 90. One debit vanished. Java statements are not atomic just because they fit on one line."},
  {"q": "`counts` is a `ConcurrentHashMap<String, Integer>`. Many threads run `counts.put(k, counts.getOrDefault(k, 0) + 1)`. What is the smallest correct fix?",
   "options": ["Make the map field `volatile`", "Wrap the map with `Collections.synchronizedMap`", "Use `counts.merge(k, 1, Integer::sum)`", "Switch to a `HashMap`"],
   "answer": 2, "why": "`merge` reads, computes and writes in one atomic operation on that key. `volatile` on the field only affects the reference to the map, and a synchronized wrapper still makes each call atomic on its own, leaving the gap between `get` and `put`."},
  {"q": "A test runs 2 threads that each call `hit()` 1,000 times, and checks the total is 2,000. It passed 100 runs in a row. What does that tell you?",
   "options": ["The counter is thread-safe", "Very little: the threads probably never overlapped", "The JIT fixed the race", "The test should use 1 thread instead"],
   "answer": 1, "why": "A thread can finish 1,000 increments before the second thread starts. With no overlap, a racy counter gives the right answer. Use more threads, more iterations and a start latch so they run at the same time."},
  {"q": "A cache does `if (cache.get(id) == null) cache.put(id, loadFromDb(id));` on a `ConcurrentHashMap`. Two threads ask for the same missing `id` together. What happens?",
   "options": ["Both may call `loadFromDb`, and the second `put` replaces the first value", "The second thread blocks until the first one finishes", "The map throws ConcurrentModificationException", "Only one thread can call `get` at a time, so it is safe"],
   "answer": 0, "why": "It's check-then-act. Both see `null`, both load, both put. You pay for two database calls and callers may hold different objects. `computeIfAbsent(id, this::loadFromDb)` runs the loader at most once per key."},
  {"q": "From the last lesson: `main` starts thread `t`, which sets `result = 42`. When can `main` safely read `result`?",
   "options": ["Right after `t.start()` returns", "After `t.join()` returns", "After `Thread.sleep(100)`", "Any time, because `int` writes are atomic"],
   "answer": 1, "why": "`join` waits for `t` to finish, and everything `t` wrote before it ended is visible to the thread whose `join` returned. `sleep` only makes it likely, not guaranteed. An atomic write still says nothing about when another thread sees it.",
   "from": "conc-02"}
 ],
 "flashcards": [
  {"front": "What is a race condition?", "back": "A bug where the result depends on the timing or interleaving of threads. It usually gives wrong results silently, not an exception."},
  {"front": "Why is `count++` not atomic?", "back": "It runs as three steps: read `count`, add one, write it back. Another thread can run between them, so two increments can produce one."},
  {"front": "Name the two shapes of race condition.", "back": "Read-modify-write (`count++`, `balance -= x`) and check-then-act (`if (!map.containsKey(k)) map.put(k, v)`)."},
  {"front": "Is `if (!chm.containsKey(k)) chm.put(k, v)` safe on a ConcurrentHashMap?", "back": "No. Each call is atomic, but another thread can put between them. Use `chm.putIfAbsent(k, v)`."},
  {"front": "Atomic fix for `map.put(k, map.get(k) + 1)` on a ConcurrentHashMap?", "back": "`map.merge(k, 1, Integer::sum)`"},
  {"front": "Why does a 2-thread x 1,000-iteration race test usually pass on broken code?", "back": "The first thread often finishes before the second starts, so they never overlap. Use a start latch and many iterations."}
 ],
 "terms": [
  {"term": "Race condition", "plain": "A bug where the result depends on which thread runs when."},
  {"term": "Lost update", "plain": "Two threads read the same old value and both write, so one change disappears."},
  {"term": "Read-modify-write", "plain": "Read a value, compute a new one from it, write it back. Unsafe on shared data unless done atomically."},
  {"term": "Check-then-act", "plain": "Test a condition, then act on it, assuming it still holds. Unsafe if another thread can act in between."},
  {"term": "Atomic", "plain": "Happens as one indivisible step. Other threads see it either not started or fully done."},
  {"term": "Critical section", "plain": "A piece of code that only one thread at a time may run, because it touches shared state."}
 ],
 "explain_back": {
  "prompt": "A teammate says: \"Our seat map uses ConcurrentHashMap, so the booking code is thread-safe.\" Explain to them, in your own words, why that is wrong and what you would change.",
  "answer": "ConcurrentHashMap makes each single call atomic, so `containsKey` and `put` are each safe on their own. The booking code runs them as two separate steps: check the seat, then take it. Another thread can take the seat between the two calls, so two buyers both see it free and both book it. The fix is to do the check and the act in one call, `putIfAbsent(seat, buyer) == null`, so only one caller can ever win. If many instances of the service share the seats, the same idea moves to a unique constraint in the database."
 },
 "deeper": {
  "minutes": 10,
  "body": "Two terms sound alike and mean different things.\n\nA **data race** is a precise term from the Java Language Specification, chapter 17. It happens when two threads access the same variable, at least one access is a write, and the two accesses are not ordered by a happens-before relationship. A program with a data race can see surprising values, because the compiler and CPU are allowed to reorder and cache unsynchronized accesses.\n\nA **race condition** is a logic bug: the program is wrong under some interleavings. You can have one without the other. The fixed `SeatMap` has no data race, but if the code first called `putIfAbsent` and then, in a separate step, charged a card and rolled back on failure, other threads could still observe a seat that is sold and then unsold. That is a race condition built entirely from thread-safe calls. Going the other way, `String.hashCode()` caches its result in a plain field that several threads may write at once. That is a data race, but a benign one: every thread computes the same value, and `int` writes cannot tear.\n\n`long` and `double` are the exception to that last point. JLS section 17.7 allows a write to a non-volatile `long` or `double` to happen as two separate 32-bit writes, so another thread could read half of an old value and half of a new one. 64-bit JVMs write them in one go in practice, but the spec does not promise it unless the field is `volatile`.\n\nYou'll meet happens-before properly in the memory model track. For now, the rule of thumb holds: every access to shared mutable state, reads included, goes through the same lock or the same atomic variable."
 },
 "sources": [
  {"title": "Java Language Specification, chapter 17: Threads and Locks", "url": "https://docs.oracle.com/javase/specs/jls/se25/html/jls-17.html"},
  {"title": "Thread interference (The Java Tutorials)", "url": "https://docs.oracle.com/javase/tutorial/essential/concurrency/interfere.html"},
  {"title": "ConcurrentHashMap (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ConcurrentHashMap.html"},
  {"title": "Java Concurrency in Practice, Goetz et al., chapter 2", "url": "https://jcip.net/"}
 ]
}
out = ROOT / "content/lessons/conc-03.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
