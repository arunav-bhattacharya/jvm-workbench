import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/vthreads/src"
P = "java/workbench/vthreads/l04"
K = "kotlin/workbench/vthreads/l04"
read = lambda p: (ROOT / p).read_text()


def demo(name):
    """Try-it code for a Java demo plus its Kotlin twin."""
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": f"./gradlew :vthreads:demo -Pmain=workbench.vthreads.l04.{name}",
            "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
                    "run": f"./gradlew :vthreads:demo -Pmain=workbench.vthreads.l04.{name}Kt",
                    "file": f"{lab}/demo/{K}/{name}.kt"}}


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


FIG = (
    '<svg viewBox="0 0 680 300" role="img" aria-label="JDK 21 to 23: all four carrier threads are held by virtual threads pinned while entering a synchronized block. The virtual thread that should take the lock next sits in the ready queue and can never get a carrier.">'
    '<text class="t-s t-m" x="150" y="38" text-anchor="middle">carrier threads (4 cores)</text>'
    '<rect class="box-bad" x="20" y="50" width="260" height="44" rx="8"/>'
    '<text class="t-s" x="150" y="68" text-anchor="middle">worker-1: pinned by VT 31</text>'
    '<text class="t-s t-bad" x="150" y="86" text-anchor="middle">blocked entering synchronized</text>'
    '<rect class="box-bad" x="20" y="102" width="260" height="44" rx="8"/>'
    '<text class="t-s" x="150" y="120" text-anchor="middle">worker-2: pinned by VT 44</text>'
    '<text class="t-s t-bad" x="150" y="138" text-anchor="middle">blocked entering synchronized</text>'
    '<rect class="box-bad" x="20" y="154" width="260" height="44" rx="8"/>'
    '<text class="t-s" x="150" y="172" text-anchor="middle">worker-3: pinned by VT 58</text>'
    '<text class="t-s t-bad" x="150" y="190" text-anchor="middle">blocked entering synchronized</text>'
    '<rect class="box-bad" x="20" y="206" width="260" height="44" rx="8"/>'
    '<text class="t-s" x="150" y="224" text-anchor="middle">worker-4: pinned by VT 63</text>'
    '<text class="t-s t-bad" x="150" y="242" text-anchor="middle">blocked entering synchronized</text>'
    '<text class="t-s t-m" x="530" y="38" text-anchor="middle">ready queue</text>'
    '<rect class="box" x="400" y="50" width="260" height="200" rx="8"/>'
    '<rect class="box-b" x="415" y="78" width="230" height="60" rx="8"/>'
    '<text class="t-s" x="530" y="102" text-anchor="middle">VT 7: next to take the lock</text>'
    '<text class="t-s" x="530" y="122" text-anchor="middle">needs a carrier to run</text>'
    '<rect class="box-dim" x="415" y="160" width="230" height="60" rx="8"/>'
    '<text class="t-s" x="530" y="184" text-anchor="middle">VT 90, 91, ...: new checkouts</text>'
    '<text class="t-s" x="530" y="204" text-anchor="middle">also waiting for a carrier</text>'
    '<line class="ln-bad" x1="413" y1="108" x2="284" y2="108" marker-end="url(#arr)"/>'
    '<text class="t-s t-bad" x="345" y="98" text-anchor="middle">no free carrier</text>'
    '<text class="t-s t-bad" x="340" y="284" text-anchor="middle">JDK 21 to 23: the carriers wait for the lock, and the lock waits for a carrier</text>'
    '</svg>'
)

OPENING = """Picture the restaurant from How virtual threads work. Four waiters carry the order slips. A slip that has to wait goes on the board by the kitchen door, and its waiter picks up another one. That is how four waiters keep two hundred tables moving.

Now give one dish a hot pan. A waiter holding a hot pan can't clip his slip to the board, because he can't put the pan down. So he stands at the stove, holding both, until the dish is done. If all four waiters hold pans, every slip on the board waits, and the whole room goes still.

Java has hot pans too. On JDK 21, the most common one was `synchronized`, a keyword Java code has used since version 1.0. It sits in old, well-tested code, so the trap is easy to fall into: tests pass, and the program stalls only under load.

Lesson 3 ended at the grill tokens. In this lesson, we'll find the hot pans on JDK 21 and JDK 25, see them with the JVM's flight recorder, and fix two traps that have nothing to do with pans. Before we start, make a guess, and keep it in mind."""

S0 = """Let's start with a cache the shop really needs. The shop also sells to customers abroad, so the checkout shows each price in the customer's own money. For that it needs an **exchange rate**, such as how many dollars one euro buys. A rates service on another computer answers in about 100 ms, and rates change only a few times a day, so the shop keeps each rate after the first lookup.

This lesson's lab calls the class `FxRateCache` (FX is short for foreign exchange). Many virtual threads ask it at once, so it needs a lock. Here is the version most of us would write first:

""" + pair(
"""// Naive on JDK 21: the slow call runs while the lock is held
public synchronized BigDecimal rate(String pair) {   // pair: "EURUSD" is euros to dollars
    BigDecimal r = rates.get(pair);
    if (r == null) {
        r = ratesService.apply(pair);   // 100 ms over the network, inside the lock
        rates.put(pair, r);
    }
    return r;
}""",
"""// Naive on JDK 21: the slow call runs while the lock is held
@Synchronized                                       // the same JVM lock as Java's synchronized
fun rate(pair: String): BigDecimal =                // pair: "EURUSD" is euros to dollars
    rates.getOrPut(pair) { ratesService.apply(pair) }   // 100 ms over the network, inside the lock""") + """

`synchronized` takes the lock that every Java object has built in, called a **monitor**: one thread at a time gets in, and the others wait at the door. The code is correct. Each rate loads once, and the lab's first test passes as it stands. The trouble is what a monitor did to a virtual thread on JDK 21 to 23.

A virtual thread is a cheap Java thread that runs on a few platform threads, each backed by a thread of the operating system and called a **carrier**. When a virtual thread waits, it normally **unmounts**: its saved stack goes to the heap, the memory where Java keeps its objects, and its carrier is free for another.

Up to JDK 23, the JVM recorded the owner of a monitor as the carrier, not as the virtual thread. So a virtual thread holding a monitor could not unmount. If it had left, the lock would have seemed to belong to whichever virtual thread mounted on that carrier next. So it stayed, and its carrier blocked with it. That is **pinning**: a virtual thread reaches a blocking call but can't let go of its carrier.

Here is the hot pan, part by part. The pan is the monitor. It's in the waiter's hands, because the JVM records the carrier as its owner. The slip can't go on the board, because the virtual thread can't unmount. And the waiter stands at the stove for the whole wait, because the carrier is blocked. On JDK 21 to 23, a slip waiting to take the pan was pinned too, so the waiters in line for the pan stood still as well.

`PinningDemo`, in the Try it below, runs with one carrier, so a single pin stops everything. A small virtual thread, the ticker, has one modest job: note the time every 50 ms. Three other virtual threads each take a lock and sleep 100 ms inside it, standing in for the slow call. Predict first. If nothing pins, the ticker keeps its rhythm, and the longest gap between ticks stays near 50 ms. On JDK 21, on this busy 4-core machine, it printed:

```text
JDK 21.0.12.1, 1 carrier thread
synchronized + sleep     longest gap between ticks: 343 ms   pinned events: 3
ReentrantLock + sleep    longest gap between ticks: 102 ms   pinned events: 0
```

The ticker went quiet for 343 ms, about three sleeps in a row. Each sleeper held the only carrier for its whole 100 ms, and the JVM counted three pins. Then a `ReentrantLock`, the lock class from `java.util.concurrent`, did the same job, and the gap fell to 102 ms on this busy machine (51 ms on the next run). A `ReentrantLock` records the virtual thread as its owner and waits by parking, the JDK's way of setting a thread aside until someone wakes it, so it has always unmounted. It's a cool pan.

**On JDK 21 to 23, blocking while you hold a monitor pins the carrier. There, use a `ReentrantLock` around slow calls.**

Slow is the mild case. In 2024, engineers at Netflix described Java 21 services that stopped answering altogether. Every carrier was held by a virtual thread pinned while it waited to enter one `synchronized` block. The virtual thread that was next in line for that lock was unmounted, and it needed a free carrier to take the lock and let the others through. None was free, and none ever would be. The figure shows the shape. Four waiters stand at the stove waiting for the pan, and the slip that must take it next hangs on the board, waiting for a waiter.

That was JDK 21. What does JDK 25 make of the same demo?"""

S1 = """JDK 24 changed how monitors work (JEP 491; a JEP, a JDK Enhancement Proposal, is the design document for a change to Java). The JVM now records the virtual thread itself as the owner of a monitor. So a virtual thread can take, hold and release one on any carrier, and `synchronized` and `Object.wait()` unmount just as a `ReentrantLock` does. In the restaurant, JDK 24 hung a hook for hot pans on the board: the pan now travels with its slip. JDK 25 is the first long-term-support release with the fix, the kind of release that gets updates for years.

Here is the same demo on JDK 25, on the same busy machine:

```text
JDK 25.0.5, 1 carrier thread
synchronized + sleep     longest gap between ticks:  52 ms   pinned events: 0
ReentrantLock + sleep    longest gap between ticks:  51 ms   pinned events: 0
class init that sleeps   longest gap between ticks: 216 ms   pinned events: 1
    reason: VM call to workbench.vthreads.l04.PinningDemo$SlowPriceList.<clinit> on stack
```

The first line is the fix: no pin, and the ticker kept time. So on JDK 25, leave working `synchronized` code alone. Rewriting it buys you nothing.

The third line shows a pan JEP 491 didn't cool. `SlowPriceList` has a **static initializer**, the code that sets up a class the first time anyone uses it. This one sleeps 200 ms, like a class that loads the shop's price list over the network. The JVM runs a static initializer through frames of its own, and it can't move those to the heap. So a virtual thread that blocks inside one is pinned, on JDK 21 and on JDK 25. The ticker lost 216 ms, and the JVM even named the reason: `<clinit>`, its name for a static initializer, was on the stack.

This pin is easy to write by accident:

""" + pair(
"""class PriceList {
    // runs inside <clinit>: a network call here pins the first virtual thread that touches PriceList
    static final Map<String, BigDecimal> PRICES = loadFromPriceService();
}""",
"""object PriceList {
    // runs inside <clinit>: a network call here pins the first virtual thread that touches PriceList
    val prices: Map<String, BigDecimal> = loadFromPriceService()
}""") + """

A Kotlin `object` is set up in a static initializer too, so it pins the same way. Load slow things in a startup step, or lazily into a cache.

The other pan that stays hot is a **native frame**: a call into code written in another language, such as C, through JNI (Java's old bridge to such code) or the newer Foreign Function and Memory API. If that native code calls back into Java and the Java code blocks, the virtual thread is pinned, because the JVM can't copy native frames to the heap. File reads look similar but have a different name. They block inside the operating system, so the virtual thread keeps its carrier, and the scheduler, the part of the JDK that puts virtual threads on carriers, adds a temporary carrier to make up for it.

To find pins in a real program, ask **JFR**, the Java Flight Recorder: a recorder built into the JVM that writes down events while the program runs, cheaply enough for production. Its event `jdk.VirtualThreadPinned` is on by default for any pin longer than 20 ms, and it keeps the pinned thread's stack. On JDK 25 it also records the reason and the carrier, as the third line above shows:

```bash
java -XX:StartFlightRecording=filename=pin.jfr,settings=profile -jar shop.jar
jfr print --events jdk.VirtualThreadPinned --stack-depth 20 pin.jfr
```

In a program that is already running, `jcmd <pid> JFR.start settings=profile` does the same (`jcmd` comes with the JDK, and `<pid>` is the number the operating system gives the running program). To catch shorter pins, add `jdk.VirtualThreadPinned#threshold=5ms` to the recording options.

Older articles suggest `-Djdk.tracePinnedThreads=full` instead. That property worked on JDK 21 to 23, and JDK 24 removed it. JDK 25 ignores it without a word, like a smoke alarm with no battery: a quiet run proves nothing.

**On JDK 25, class initializers and native frames still pin. Keep JFR's pinned event on, and fix what it reports.**

Pins are about carriers. The next trap never touches a carrier, and it hides in code that was right for years: a `ThreadLocal`."""

S2 = """A `ThreadLocal` is a variable with a separate value for each thread. Each thread that reads it sees its own copy, and no other thread can touch that copy. It works on virtual threads exactly as on platform threads. The trap is one popular use: a `ThreadLocal` as a cache.

The shop prints a timestamp on every receipt. The old class for that, `SimpleDateFormat`, is not thread-safe: two threads using one formatter at once can print garbage. So for years people kept one per thread:

""" + pair(
"""// SimpleDateFormat isn't thread-safe, so keep one per thread
static final ThreadLocal<SimpleDateFormat> FORMAT =
        ThreadLocal.withInitial(() -> new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'"));""",
"""// SimpleDateFormat isn't thread-safe, so keep one per thread
val FORMAT: ThreadLocal<SimpleDateFormat> =
    ThreadLocal.withInitial { SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'") }""") + """

Picture the old restaurant from The thread-per-request wall, with its 200 waiters, each with an apron pocket. On his first order, each waiter puts a pen in his pocket and uses it all evening. That's 200 pens, bought once. The pocket is the `ThreadLocal`, the pen is the formatter, and `withInitial` buys a pen whenever a pocket is empty.

With slips, the pocket moves to the slip, because each virtual thread has its own thread-local values. Every order is a new slip with an empty pocket. So every order buys a new pen, uses it once and throws it away when the meal ends. A million orders, a million pens.

`ThreadLocalCostDemo`, in the Try it below, counts the pens. It formats 100,000 timestamps three ways. Predict the three counts before you look:

```text
ThreadLocal cache, pool of 8 platform threads  formatters built:       8   time:   610 ms
ThreadLocal cache, virtual thread per task     formatters built: 100,000   time: 1,019 ms
shared DateTimeFormatter, virtual threads      formatters built:       1   time:   633 ms
```

Eight pool threads built eight formatters. One virtual thread per task built 100,000, and nothing failed. The cache did exactly as it was told, a hundred thousand times: build, use once, throw away. It's the busiest cache in the shop, and it never caches anything. You'd only notice it as extra work for the garbage collector, the part of the JVM that frees objects nobody uses.

Per-thread buffers are worse, because they hold memory for as long as the thread lives. A 64 KB scratch buffer in a `ThreadLocal<byte[]>` was 13 MB on 200 threads. On 100,000 live virtual threads it's 6.4 GB.

The third line is the fix the lab asks for. `DateTimeFormatter`, from `java.time`, is **immutable**: once built, nothing can change it, so any number of threads can use one at the same moment. Here the picture breaks, in our favor. Two waiters can't write with one pen at once, but a thousand threads can format with one immutable formatter, because formatting changes nothing inside it.

So there are three fixes, in order of preference. Share an immutable object when one exists. If the object is costly and not thread-safe, keep a small shared pool of it, not one per thread. And if it's cheap, just create it where you need it.

A `ThreadLocal` also carries a request's details, such as the customer's id for the log. That still works within one virtual thread. But the value doesn't follow the work into threads you start, and it stays until someone calls `remove()`. Lesson 5 of this track has a better tool for that job. To list every `ThreadLocal` a program sets on virtual threads, run it with `-Djdk.traceVirtualThreadLocals=true`. It's an unsupported diagnostic property, present on JDK 21 and 25, that prints a stack trace each time a virtual thread sets one.

**A `ThreadLocal` cache builds one object per thread, and with virtual threads that means one per task. Share an immutable object instead.**

Hot pans and apron pockets are traps you can fix in code. The last trap is a limit, and no code makes it go away."""

S3 = """Virtual threads make waiting cheap. They do nothing for computing. There are as many carriers as cores, so at most that many virtual threads compute at the same moment, which is exactly what a fixed pool of that size gives you.

`CpuBoundDemo`, in the Try it below, checks it. Each of 64 tasks computes a checksum of a 1 MB buffer 20 times. A checksum is a short fingerprint of some data, and computing one is pure work for the processor, with no waiting. The tasks run on a pool of 4 platform threads, then with one virtual thread each. Predict which line wins:

```text
fixed pool of 4 platform threads   64 tasks in   655 ms
virtual thread per task            64 tasks in   563 ms
```

Nearly a tie, with the virtual line a little ahead. Is that a gain? Not really. Two more runs gave the same small lead, so we swapped the order of the two lines in a copy of the demo. Then the pool won one run and lost the next. On this busy machine, warm-up and noise decide the last 15 percent. Compare that with lesson 1 of this track, where the same switch finished 2,000 sleeping tasks eight times faster.

It's worse than no gain, because there is no time slicing: nothing takes a carrier away from a virtual thread that computes. That is the waiter from How virtual threads work who chops onions with his slip in his pocket. Say the shop resizes product photos on virtual threads, and each photo takes 3 seconds of pure computing. Four of those on a 4-core machine hold every carrier for 3 seconds. Every checkout waits behind them, even one that needs a single millisecond of processor time.

So keep heavy computing on a bounded pool of platform threads, and let the virtual thread wait for it:

""" + pair(
"""private final ExecutorService cpu = Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors());

Photo publish(Photo original) throws Exception {
    Photo small = cpu.submit(() -> resizer.resize(original)).get();   // heavy computing on a bounded pool
    return storage.save(small);                                       // blocking I/O stays on the virtual thread
}""",
"""private val cpu = Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors())

fun publish(original: Photo): Photo {
    val small = cpu.submit(Callable { resizer.resize(original) }).get()   // heavy computing on a bounded pool
    return storage.save(small)                                            // blocking I/O stays on the virtual thread
}""") + """

In the restaurant, the waiter hands the onions to the prep cooks in the back, clips his slip to the board and goes back to his tables. In code, the virtual thread parks in `get()`, so it holds no carrier while the pool computes. The operating system time-slices those pool threads against the carriers, so checkouts keep moving.

The line between waiting and computing is fuzzy for work that does a bit of both. Reading a small request is fine on a virtual thread. Anything that computes for tens of milliseconds without blocking, such as resizing images, compressing files or building a large PDF, belongs on the pool.

**Virtual threads give scale to waiting, not to computing. Give heavy computing a bounded pool of its own.**

That's the last trap. In the lab you unpin the rates cache and retire the receipt's `ThreadLocal`."""

CLOSING = """We started with four waiters and a hot pan. On JDK 21, `synchronized` was that pan: a slip that held it couldn't go on the board, and a few of them could stop the room. JDK 24 cooled it, and on JDK 25 only class initializers and native code stay hot. The apron pocket was a different trap, a new pen for every order.

Now search your own code for `ThreadLocal.withInitial`, and for slow work inside a `static {}` block or a Kotlin `object`.

Next, we'll split one checkout into helpers that work at the same time. When one of them fails, who calls the others back, and what replaces a `ThreadLocal` for the order's own details?"""

L = {
 "id": "vt-04",
 "title": "Pinning, ThreadLocals and other traps",
 "minutes": 35,
 "goal": "By the end you can say what pins a virtual thread on JDK 21 and on JDK 25, find a pin with JFR, and fix the two classic traps of a move to virtual threads: a lock held around a slow call, and a ThreadLocal used as a cache.",
 "opening": OPENING,
 "warmup": {
  "q": "On JDK 25, a virtual thread runs `synchronized (cache) { rate = ratesService.fetch(pair); }`, where `fetch` asks a web service on another computer and takes 80 ms. What happens to its carrier thread during those 80 ms?",
  "options": [
   "It is pinned: the carrier blocks for 80 ms, because `synchronized` always pins a virtual thread",
   "It is free: since JDK 24, the virtual thread unmounts while it waits, even inside `synchronized`",
   "The JVM throws, because blocking inside `synchronized` is not allowed on a virtual thread",
   "The JVM turns the virtual thread into a platform thread until the block ends"
  ],
  "answer": 1,
  "why": "JDK 24 (JEP 491) changed monitors so that a virtual thread can hold one and still unmount. \"synchronized pins\" was true on JDK 21 to 23, and many articles from that time still say so. The lock still lets one caller in at a time, though: only one virtual thread can fetch at once. The first two sections show both JDKs side by side."
 },
 "sections": [
  {
   "h": "A hot pan on JDK 21: how synchronized pinned a virtual thread",
   "body": S0,
   "figure": {"svg": FIG, "caption": "On JDK 21 to 23, pinned virtual threads can hold every carrier while they wait for a lock, and the virtual thread that must take the lock next never gets one: four waiters at the stove, and the slip they need is on the board."},
   "try": {
    "title": "Pin the only carrier",
    "minutes": 4,
    "steps": [
     "Read `PinningDemo`. It runs with one carrier. The ticker notes the time every 50 ms, while three virtual threads each block for 100 ms: inside `synchronized`, inside a `ReentrantLock`, or inside a class's static initializer.",
     "Check your JDK with `java -version`. For each of the three lines, write down the longest gap between ticks and the number of pinned events you expect on that JDK.",
     "Run it. If you have both JDK 21 and JDK 25, run it on both: Gradle uses the JDK that `JAVA_HOME` points at."
    ],
    "code": demo("PinningDemo"),
    "expect": "On JDK 21 (busy runs here): `synchronized` leaves a gap of about 300 ms between ticks (337 and 343 ms) and 3 pinned events, because the three sleepers hold the only carrier one after another. `ReentrantLock` keeps the ticker near 50 ms (51 to 102 ms on this busy machine) with 0 events. On JDK 25, `synchronized` behaves like `ReentrantLock`: about 52 ms and 0 events. The static initializer pins on both JDKs: a gap of about 200 ms (202 to 312 ms here) and 1 event, and on JDK 25 the demo prints the reason, `VM call to ...SlowPriceList.<clinit> on stack`."
   },
   "refs": [
    {"title": "JEP 491: Synchronize Virtual Threads without Pinning", "url": "https://openjdk.org/jeps/491", "kind": "read"}
   ]
  },
  {
   "h": "JDK 24 cools the pan: what still pins on JDK 25, and how JFR shows it",
   "body": S1,
   "aside": {
    "title": "What about the libraries my program uses?",
    "body": "They count too, and on JDK 21 to 23 they are where most pins hide. Drivers that talk to a database, clients that call web services and logging libraries often held a `synchronized` lock around a network read. Many have since moved to `ReentrantLock`, but a JFR recording under real load is a better witness than a list of changes. On JDK 25 that whole family of pins is gone, which is the best argument I know for upgrading before you switch to virtual threads."
   },
   "try": {
    "title": "Read a pinned event",
    "minutes": 4,
    "steps": [
     "Run `PinningDemo` once through Gradle (the previous Try it), so its classes are compiled.",
     "From `labs/`, run the static initializer scenario with a JFR recording, then print the pinned events, with the commands below.",
     "Find the frame that names `SlowPriceList`. On JDK 25, also read the `pinnedReason`, `blockingOperation` and `carrierThread` fields."
    ],
    "code": {"lang": "bash", "title": "terminal", "src": "java -XX:StartFlightRecording=filename=pin.jfr,settings=profile \\\n     -cp vthreads/build/classes/java/demo workbench.vthreads.l04.PinningDemo init\njfr print --events jdk.VirtualThreadPinned --stack-depth 10 pin.jfr", "run": ""},
    "expect": "One `jdk.VirtualThreadPinned` event of about 200 ms. On JDK 21 you get the stack, and it shows `Thread.sleep` called from `PinningDemo$SlowPriceList.<clinit>()`, which is enough. On JDK 25 the event also says `blockingOperation = \"LockSupport.park\"`, `pinnedReason = \"VM call to workbench.vthreads.l04.PinningDemo$SlowPriceList.<clinit> on stack\"` and `carrierThread = \"ForkJoinPool-1-worker-1\"`. Without `--stack-depth`, `jfr print` shows only the top 5 frames, which stop before the initializer."
   },
   "refs": [
    {"title": "jdk.jfr.Recording (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/jdk.jfr/jdk/jfr/Recording.html", "kind": "docs"}
   ]
  },
  {
   "h": "The apron pocket: a ThreadLocal cache meets a million slips",
   "body": S2,
   "try": {
    "title": "Count the formatters",
    "minutes": 3,
    "steps": [
     "Read `ThreadLocalCostDemo`. It formats 100,000 receipt timestamps with a `ThreadLocal<SimpleDateFormat>` on a pool of 8 platform threads, then with the same cache and one virtual thread per task, then with one shared `DateTimeFormatter`.",
     "Write down the three \"formatters built\" numbers you expect.",
     "Run it, and compare the times as well."
    ],
    "code": demo("ThreadLocalCostDemo"),
    "expect": "8, then 100,000, then 1. The pool built one formatter per thread and reused it, and with virtual threads every task built its own and threw it away. The shared formatter is usually the fastest line, but times swing a lot on a busy machine: runs here gave 610, 1,019 and 633 ms in Java, and 617, 1,473 and 356 ms in Kotlin. The counts never change."
   }
  },
  {
   "h": "Chopping onions: work that only computes gains nothing",
   "body": S3,
   "try": {
    "title": "Compute on virtual threads",
    "minutes": 3,
    "steps": [
     "Read `CpuBoundDemo`. Each of 64 tasks computes a checksum of a 1 MB buffer 20 times: a fixed amount of pure computing.",
     "Predict which line finishes first: a pool sized to your cores, or one virtual thread per task.",
     "Run it twice. Then run it with `-Pargs='256 20'` and predict again: four times the tasks."
    ],
    "code": demo("CpuBoundDemo"),
    "expect": "Both lines take about the same time, under a second for 64 tasks on 4 cores (655 and 563 ms, then 1,003 and 782 ms, in busy runs here). Neither is many times faster, as virtual threads were for sleeping tasks, and the small lead moves when you swap the two lines. With 256 tasks both take about four times as long or more (3,887 and 3,496 ms here). The work is limited by cores, and both setups use all of them."
   }
  }
 ],
 "compare": {
  "title": "Taking the monitor out of the slow path",
  "java": {"title": "Java: synchronized becomes ReentrantLock", "src": "// JDK 21 to 23: this pins for the whole fetch\npublic synchronized BigDecimal rate(String pair) {\n    return rates.computeIfAbsent(pair, ratesService);\n}\n\n// any JDK: a java.util.concurrent lock parks a waiting virtual thread instead\nprivate final ReentrantLock lock = new ReentrantLock();\n\npublic BigDecimal rate(String pair) {\n    lock.lock();\n    try {\n        return rates.computeIfAbsent(pair, ratesService);   // rates is a plain HashMap\n    } finally {\n        lock.unlock();\n    }\n}"},
  "kotlin": {"title": "Kotlin: @Synchronized becomes withLock", "src": "// JDK 21 to 23: @Synchronized and synchronized(lock) {} are monitors, and pin the same way\n@Synchronized\nfun rate(pair: String): BigDecimal = rates.getOrPut(pair) { ratesService.apply(pair) }\n\n// any JDK: kotlin.concurrent.withLock does lock, try, finally and unlock for you\nprivate val lock = ReentrantLock()\n\nfun rate(pair: String): BigDecimal = lock.withLock {\n    rates.getOrPut(pair) { ratesService.apply(pair) }   // rates is a plain HashMap\n}"},
  "note": "Both versions make the same change: the monitor goes, and a `ReentrantLock` takes its place around the same lines. Kotlin has no `synchronized` keyword, but `@Synchronized` and the `synchronized(lock) { }` function compile to the same JVM monitor instructions as Java, so they pin on JDK 21 to 23 in exactly the same way. The Kotlin fix is shorter, because the standard library's `withLock` writes the `lock()`, the `try` and the `finally { unlock() }` for you, and it's `inline`, so it costs nothing at run time. Notice what neither version does: it doesn't let two different rates load at the same time. That needs one lock per key, and on JDK 25 it's the only reason left to touch this code."
 },
 "worked": {
  "title": "Find and fix a pin from a JFR recording (JDK 21)",
  "steps": [
   {"say": "The shop's checkout runs on JDK 21, with one virtual thread per checkout. In a load test, the slowest checkouts jump from 200 ms to several seconds, while the processor stays mostly idle. Record two minutes of the test with JFR, then print the pinned events. (`jcmd` comes with the JDK and talks to a running JVM, and `pgrep -f checkout` finds the process number of the running checkout program.)", "code": "jcmd $(pgrep -f checkout) JFR.start name=pins settings=profile duration=120s filename=pins.jfr\njfr print --events jdk.VirtualThreadPinned --stack-depth 20 pins.jfr | head -40", "lang": "bash"},
   {"say": "Read the stack in one event. The pin lasts as long as one call to the rates service, and above the network read sits a `synchronized` method of the cache.", "code": "jdk.VirtualThreadPinned {\n  duration = 103 ms\n  stackTrace = [\n    java.lang.VirtualThread.parkOnCarrierThread(boolean, long)\n    ...\n    sun.nio.ch.NioSocketImpl.read(byte[], int, int)\n    ...\n    workbench.vthreads.l04.FxRateCache.rate(String)   <- synchronized\n  ]\n}", "lang": "text"},
   {"say": "Replace the monitor with a `ReentrantLock`, and keep the same \"load once\" behavior. The lock still lets one caller in at a time, but a waiting virtual thread now parks and frees its carrier.", "code": "private final ReentrantLock lock = new ReentrantLock();\n\npublic BigDecimal rate(String pair) {\n    lock.lock();                                 // 1. take the lock (parks, doesn't pin)\n    try {\n        BigDecimal r = rates.get(pair);\n        if (r == null) {\n            r = ratesService.apply(pair);        // 2. slow call: the thread can unmount here\n            rates.put(pair, r);\n        }\n        return r;\n    } finally {\n        lock.unlock();                           // 3. always release\n    }\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "private val lock = ReentrantLock()\n\nfun rate(pair: String): BigDecimal = lock.withLock {   // 1. take the lock (parks, doesn't pin)\n    rates[pair] ?: ratesService.apply(pair)          // 2. slow call: the thread can unmount here\n        .also { rates[pair] = it }\n}                                                    // 3. withLock always releases"},
   {"say": "Check with the same recording under the same load: no `jdk.VirtualThreadPinned` events from `FxRateCache`, and the slowest checkouts back near 200 ms. Then put the move to JDK 25 on the plan, so the next `synchronized` inside a library doesn't need the same fix."}
  ]
 },
 "lab": {
  "title": "Unpin a cache and retire a ThreadLocal",
  "minutes": 13,
  "files": [f"{lab}/main/{P}/FxRateCache.java", f"{lab}/main/{P}/ReceiptStamp.java"],
  "run": "./gradlew :vthreads:test --tests 'workbench.vthreads.l04.*'",
  "steps": [
   "Run the tests once. On JDK 21 three fail: the monitor check, the JFR pinning check and the formatter count. On JDK 24 or later the pinning check passes even now, which is JEP 491 at work.",
   "`FxRateCache` keeps exchange rates and loads each one once from a slow rates service. Remove both `synchronized` modifiers and add a `private final ReentrantLock lock`. Wrap the bodies of `rate` and `size` in `lock.lock(); try { ... } finally { lock.unlock(); }`.",
   "Read the JFR test in `TrapsTest`. It records `jdk.VirtualThreadPinned` while four virtual threads load four rates, then checks that the recording is empty. The same few lines fit in your own programs' tests.",
   "`ReceiptStamp` formats the time printed on a receipt. Replace its `ThreadLocal<SimpleDateFormat>` with one `static final DateTimeFormatter`, built once with `.withZone(ZoneOffset.UTC)`. Count it in `BUILT` when you build it, and format with `FORMAT.format(Instant.ofEpochMilli(epochMillis))`.",
   "Run the tests until all six pass."
  ],
  "hints": [
   "The monitor test calls `Thread.holdsLock(cache)` from inside the rates service. That returns true only for a `synchronized` monitor on the cache object, never for a `ReentrantLock`.",
   "Don't drop the lock entirely: the load-once test sends 100 virtual threads at the same rate and expects exactly one call to the rates service.",
   "`DateTimeFormatter.ofPattern(\"yyyy-MM-dd'T'HH:mm:ss.SSS'Z'\")` needs a time zone to format an `Instant`. Without `withZone` you get an `UnsupportedTemporalTypeException`."
  ],
  "done_when": "All six tests in `TrapsTest` pass."
 },
 "drill": {
  "title": "Unpin a method from memory",
  "minutes": 4,
  "prompt": "Close the lab. Rewrite this method for a program on JDK 21, so it never holds a monitor during the slow call, without changing what it does: `synchronized PriceList prices() { if (list.isOld()) list = priceService.fetch(); return list; }`. Then say in one sentence whether you would still change it on JDK 25.",
  "answer": {"lang": "java", "src": "private final ReentrantLock lock = new ReentrantLock();\n\nPriceList prices() {\n    lock.lock();                              // outside the try\n    try {\n        if (list.isOld()) list = priceService.fetch();   // may block: parks, doesn't pin\n        return list;\n    } finally {\n        lock.unlock();\n    }\n}\n// On JDK 25: no need. synchronized no longer pins (JEP 491), so the original is fine.",
             "alt": {"lang": "kotlin", "src": "private val lock = ReentrantLock()\n\nfun prices(): PriceList = lock.withLock {      // lock, try, finally unlock\n    if (list.isOld()) list = priceService.fetch()   // may block: parks, doesn't pin\n    list\n}\n// On JDK 25: no need. @Synchronized no longer pins (JEP 491), so the original is fine."}}
 },
 "recap": [
  "A pinned virtual thread can't unmount at a blocking call, so its carrier blocks with it.",
  "On JDK 21 to 23, blocking while holding a monitor (`synchronized`, `@Synchronized`, `Object.wait`) pins. JDK 24 (JEP 491) fixed that, and JDK 25 is the first long-term-support release with the fix.",
  "On JDK 25, blocking inside a static initializer (or a Kotlin `object`'s setup) or under a native frame still pins. File reads keep the carrier, and the scheduler adds a temporary one.",
  "Find pins with the JFR event `jdk.VirtualThreadPinned`, on by default above 20 ms. `-Djdk.tracePinnedThreads` was removed in JDK 24.",
  "A `ThreadLocal` cache builds one object per virtual thread, which means one per task. Share an immutable object such as `DateTimeFormatter` instead.",
  "The limit: work that only computes gains nothing, and with no time slicing it can hold every carrier. Run it on a bounded pool of platform threads."
 ],
 "quiz": [
  {"q": "A shop's program runs on JDK 25. Its old database code has `synchronized` blocks around each query. You are moving request handling to virtual threads. What should you do about those blocks?",
   "options": ["Replace every one with `ReentrantLock` before the switch, or the program will pin", "Nothing for pinning: on JDK 24 and later they don't pin. Keep a JFR recording to catch the pins that remain", "Run with `-Djdk.tracePinnedThreads=full` and fix what it prints", "Wrap each query in `Thread.ofPlatform().start(...)`"], "answer": 1,
   "why": "JEP 491 (JDK 24) lets a virtual thread hold a monitor without pinning, so on JDK 25 these blocks are fine. Rewriting them is the JDK 21 advice, and it's tempting because so many articles still give it. `-Djdk.tracePinnedThreads` no longer exists on JDK 24 and later, so it would print nothing and prove nothing."},
  {"q": "Which tool shows you, on JDK 25, that a virtual thread pinned its carrier for 180 ms, and why?",
   "options": ["`jstack <pid>`", "`Thread.getAllStackTraces()` from a debug page", "The JFR event `jdk.VirtualThreadPinned`, printed with `jfr print`", "`-Djdk.tracePinnedThreads=short`"], "answer": 2,
   "why": "`jdk.VirtualThreadPinned` is recorded for pins over 20 ms by default and keeps the stack, and on JDK 25 it also records the reason and the carrier. `jstack` and `getAllStackTraces()` show platform threads, not parked virtual threads, and the trace property was removed in JDK 24."},
  {"q": "The shop's checkout computes a checksum of each request with a `ThreadLocal<MessageDigest>` cache (a `MessageDigest` computes checksums). It moves from a 200-thread pool to one virtual thread per request and serves 1 million requests. About how many `MessageDigest` objects does it create?",
   "options": ["200, the same as before", "One per carrier thread, so about the number of cores", "About 1 million, one per request", "One, because virtual threads share their ThreadLocal values"], "answer": 2,
   "why": "Each virtual thread has its own thread-local values, and each request runs on a new virtual thread, so `withInitial` runs once per request. The carriers don't matter: the JDK keeps a virtual thread's thread locals apart from its carrier's. Share a thread-safe object, or create one per call on purpose."},
  {"q": "An 8-core program resizes 10,000 product photos, and each takes about 50 ms of pure computing. It runs on `newFixedThreadPool(8)`. What happens if you switch it to `newVirtualThreadPerTaskExecutor()`?",
   "options": ["It takes about the same time, about 62 s, because only 8 can compute at once either way", "It finishes in about 50 ms, because all 10,000 run at once", "It finishes about 8 times faster", "It deadlocks, because virtual threads can't run computing work"], "answer": 0,
   "why": "There are 8 carriers, so at most 8 virtual threads compute at once: 10,000 × 50 ms / 8 = 62.5 s, the same as the pool. Virtual threads help only when tasks spend their time waiting. With no time slicing, they can also hold up other virtual threads in the same program."},
  {"q": "From the lesson \"Don't share: immutability, confinement, ThreadLocal\": `SimpleDateFormat` is not thread-safe. Which fix works equally well on a platform pool and on one virtual thread per task, with no per-thread state at all?",
   "options": ["Wrap every `format` call in `synchronized`", "One shared, immutable `DateTimeFormatter`", "A `ThreadLocal<SimpleDateFormat>`", "A `volatile SimpleDateFormat` field"], "answer": 1,
   "why": "An immutable object is safe to share with any number of threads, so it needs no copies and no locking. The `ThreadLocal` works on a pool but becomes one formatter per task on virtual threads. `synchronized` is correct but makes every caller wait in line. `volatile` makes the reference visible but leaves the formatter's insides open to races.", "from": "conc-11"}
 ],
 "flashcards": [
  {"front": "What does it mean that a virtual thread is pinned?", "back": "It reaches a blocking call but can't unmount, so it stays on its carrier and the carrier blocks with it."},
  {"front": "Does blocking inside `synchronized` pin a virtual thread on JDK 25?", "back": "No. Since JDK 24 (JEP 491), monitors don't pin. On JDK 21 to 23 they do."},
  {"front": "What still pins a virtual thread on JDK 25?", "back": "Blocking while a static initializer (`<clinit>`) or a native frame (JNI, or a Foreign Function call that calls back into Java) is on its stack."},
  {"front": "How do you detect pinning on JDK 24 and later?", "back": "The JFR event `jdk.VirtualThreadPinned` (on by default, 20 ms threshold). `-Djdk.tracePinnedThreads` was removed in JDK 24."},
  {"front": "Why does a `ThreadLocal` cache stop working with one virtual thread per task?", "back": "Each task runs on a new virtual thread with empty thread-local values, so the cached object is built once per task and thrown away."},
  {"front": "Do virtual threads speed up work that only computes?", "back": "No. At most one virtual thread per carrier (per core) computes at once, and there is no time slicing."},
  {"front": "Kotlin replacement for `@Synchronized` around a slow call on JDK 21?", "back": "`private val lock = ReentrantLock()` and `lock.withLock { ... }` from `kotlin.concurrent`."}
 ],
 "terms": [
  {"term": "Pinning", "plain": "A virtual thread stuck on its carrier during a blocking call, so the carrier blocks too."},
  {"term": "Monitor", "plain": "The lock behind `synchronized` and `@Synchronized`, built into every Java object."},
  {"term": "JEP 491", "plain": "The JDK 24 change that lets virtual threads hold monitors without pinning."},
  {"term": "Static initializer", "plain": "The code that sets up a class the first time it's used (`static {}`, static fields, a Kotlin `object`). The JVM calls it `<clinit>`."},
  {"term": "JFR", "plain": "Java Flight Recorder: the JVM's built-in recorder of events, cheap enough for production."},
  {"term": "jdk.VirtualThreadPinned", "plain": "The JFR event recorded when a virtual thread blocks while pinned for longer than the threshold."},
  {"term": "ThreadLocal cache", "plain": "Keeping one copy of an object per thread to reuse it. Useless when every task gets a new thread."}
 ],
 "explain_back": {
  "prompt": "A colleague read an article from 2023 and wants to ban `synchronized` before the move to virtual threads. The program runs on JDK 25. Explain what pinning is, whether the ban helps, and what you would check instead.",
  "answer": "Pinning is when a virtual thread can't unmount at a blocking call, so it keeps its carrier and the carrier blocks with it. On JDK 21 to 23, holding a `synchronized` monitor while blocking caused it, and a few pinned threads could stop every carrier. JDK 24 fixed that with JEP 491, so on JDK 25 a ban on `synchronized` changes nothing for pinning and just churns code. What still pins on JDK 25 is blocking inside a static initializer or under native code, so I'd keep a JFR recording with `jdk.VirtualThreadPinned` running under real load and fix what it reports. I'd also check the traps that have nothing to do with pinning: `ThreadLocal` caches that now build an object per request, and heavy computing that should stay on a bounded pool of platform threads."
 },
 "deeper": {
  "minutes": 10,
  "body": "**Why monitors pinned in the first place.** Before JDK 24, HotSpot recorded the owner of a monitor as the operating system thread that held it. If a virtual thread could unmount while holding a monitor, another virtual thread mounted on the same carrier would seem to own it too. Rather than redesign monitors for JDK 21, the team behind virtual threads shipped with pinning and a warning. JEP 491 changed the JVM to record the virtual thread as the owner, so the thread can move freely.\n\n**Object.wait() on JDK 21.** A virtual thread in `Object.wait()` was pinned too, but the scheduler made up for it by adding a temporary carrier, up to `jdk.virtualThreadScheduler.maxPoolSize`. That kept wait-heavy code alive, at the cost of extra operating system threads. Blocking on monitor entry got no such help, which is why the stall in this lesson's figure was possible.\n\n**Waiting for someone else's class initializer.** On JDK 25, a virtual thread that waits for another thread to finish initializing a class is pinned while it waits. JDK 26 changed that case so the waiting thread unmounts. The thread that runs the slow initializer itself still pins, so the advice stays the same: keep slow work out of static initializers.\n\n**Testing for pins.** The lab's JFR test is a pattern you can copy into your own tests: start a `jdk.jfr.Recording` with `jdk.VirtualThreadPinned` enabled, run a realistic slice of work on virtual threads, stop and dump the recording, and check that it has no events. Warm up first, so one-time class loading doesn't show up as a pin. On JDK 24 and later, such a test catches static initializer and native pins. On JDK 21, it also catches every `synchronized` around a slow call.\n\n**Inheritable thread locals.** A new thread copies its parent's `InheritableThreadLocal` values by default, and that includes virtual threads. Creating a million virtual threads from a thread with large inheritable values copies them a million times. `Thread.ofVirtual().inheritInheritableThreadLocals(false)` turns the copy off for threads that don't need it."
 },
 "closing": CLOSING,
 "sources": [
  {"title": "JEP 491: Synchronize Virtual Threads without Pinning", "url": "https://openjdk.org/jeps/491"},
  {"title": "JEP 444: Virtual Threads", "url": "https://openjdk.org/jeps/444"},
  {"title": "ReentrantLock (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/locks/ReentrantLock.html"},
  {"title": "jdk.jfr.Recording (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/jdk.jfr/jdk/jfr/Recording.html"}
 ]
}
out = ROOT / "content/lessons/vt-04.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
