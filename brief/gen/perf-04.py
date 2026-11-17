import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/performance/src"
P = "java/workbench/performance/l04"
K = "kotlin/workbench/performance/l04"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :performance:demo -Pmain=workbench.performance.l04."

def demo(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": DEMO + name, "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
                    "run": DEMO + name + "Kt", "file": f"{lab}/demo/{K}/{name}.kt"}}

def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"

def line(x, y, marks):
    s = ""
    for i in range(8):
        cls = marks.get(i, "box")
        s += f'<rect class="{cls}" x="{x + 28 * i}" y="{y}" width="28" height="30" rx="4"/>\n'
    return s

FIG = ('<svg viewBox="0 0 680 300" role="img" aria-label="Top: parsed and written share one 64-byte cache line, so each write by one core invalidates the other core\'s copy. Bottom: padded onto two lines, each core keeps its own line.">\n'
       '<text class="t-s t-bad" x="340" y="18" text-anchor="middle">adjacent: one line, two writers</text>\n'
       '<rect class="box" x="20" y="28" width="224" height="34" rx="8"/><text class="t" x="132" y="50" text-anchor="middle">core 1 writes parsed</text>\n'
       '<rect class="box" x="436" y="28" width="224" height="34" rx="8"/><text class="t" x="548" y="50" text-anchor="middle">core 2 writes written</text>\n'
       + line(20, 76, {0: "box-dim", 1: "box-dim", 2: "box-a", 3: "box-b"})
       + line(436, 76, {0: "box-dim", 1: "box-dim", 2: "box-a", 3: "box-b"}) +
       '<text class="t-s t-m" x="48" y="124" text-anchor="middle">header</text>\n'
       '<text class="t-s t-a" x="90" y="140" text-anchor="middle">parsed</text>\n'
       '<text class="t-s t-b" x="118" y="124" text-anchor="middle">written</text>\n'
       '<text class="t-s t-a" x="506" y="140" text-anchor="middle">parsed</text>\n'
       '<text class="t-s t-b" x="534" y="124" text-anchor="middle">written</text>\n'
       '<line class="ln-bad" x1="248" y1="84" x2="432" y2="84" marker-end="url(#arr)"/>\n'
       '<line class="ln-bad" x1="432" y1="100" x2="248" y2="100" marker-end="url(#arr)"/>\n'
       '<text class="t-s t-bad" x="340" y="78" text-anchor="middle">invalidate</text>\n'
       '<text class="t-s t-bad" x="340" y="120" text-anchor="middle">fetch it back, again and again</text>\n'
       '<text class="t-s t-ok" x="340" y="178" text-anchor="middle">padded: two lines, no fight</text>\n'
       '<rect class="box" x="20" y="188" width="224" height="34" rx="8"/><text class="t" x="132" y="210" text-anchor="middle">core 1 writes parsed</text>\n'
       '<rect class="box" x="436" y="188" width="224" height="34" rx="8"/><text class="t" x="548" y="210" text-anchor="middle">core 2 writes written</text>\n'
       + line(20, 236, {2: "box-a"}) + line(436, 236, {2: "box-b"}) +
       '<text class="t-s t-a" x="90" y="286" text-anchor="middle">parsed, line A</text>\n'
       '<text class="t-s t-b" x="506" y="286" text-anchor="middle">written, line B</text>\n'
       '<text class="t-s t-ok" x="340" y="256" text-anchor="middle">no traffic</text>\n'
       '</svg>')

ADJ_J = """static final class Adjacent {
    volatile long parsed;     // written only by the parsing thread
    volatile long written;    // written only by the writing thread
}
// JOL on JDK 21 and JDK 25: 32 bytes; parsed at offset 16, written at offset 24"""
ADJ_K = """class KAdjacent {
    @Volatile var parsed = 0L     // written only by the parsing thread
    @Volatile var written = 0L    // written only by the writing thread
}
// JOL on JDK 21 and JDK 25: 32 bytes; parsed at offset 16, written at offset 24"""

PAD_J = """abstract class ParsedCounter { volatile long parsed; }
abstract class PadAfterParsed extends ParsedCounter { long p1, p2, p3, p4, p5, p6, p7, p8; }
abstract class WrittenCounter extends PadAfterParsed { volatile long written; }

public final class StageCounters extends WrittenCounter {
    public void addParsed() { parsed++; }      // only the parsing thread calls this
    public void addWritten() { written++; }    // only the writing thread calls this
}"""
PAD_K = """abstract class ParsedCounter { @Volatile @JvmField var parsed = 0L }
abstract class PadAfterParsed : ParsedCounter() {
    @JvmField var p1 = 0L; @JvmField var p2 = 0L; @JvmField var p3 = 0L; @JvmField var p4 = 0L
    @JvmField var p5 = 0L; @JvmField var p6 = 0L; @JvmField var p7 = 0L; @JvmField var p8 = 0L
}
abstract class WrittenCounter : PadAfterParsed() { @Volatile @JvmField var written = 0L }

class StageCounters : WrittenCounter() {
    fun addParsed() { parsed++ }               // only the parsing thread calls this
    fun addWritten() { written++ }             // only the writing thread calls this
}"""
ADDER_J = """public final class RequestMetrics {
    private final LongAdder count = new LongAdder();
    private final LongAdder totalWords = new LongAdder();

    public void record(long words) {          // called by every request thread
        count.increment();
        totalWords.add(words);
    }

    public long count() { return count.sum(); }   // read by the monitoring program
}"""
ADDER_K = """class RequestMetrics {
    private val count = LongAdder()
    private val totalWords = LongAdder()

    fun record(words: Long) {                  // called by every request thread
        count.increment()
        totalWords.add(words)
    }

    fun count(): Long = count.sum()            // read by the monitoring program
}"""

OPENING = """Picture two cooks at one counter, sharing a single cutting board. One chops onions, the other chops peppers. They never touch each other's vegetables, so there's nothing to argue about. But only one knife fits on the board at a time, so each cook keeps stepping back to wait for the other.

Your processor has the same problem in miniature. Two threads, two lines of work running at the same time, can slow each other down even when each writes only its own field. The two fields share one small block of memory, and the hardware moves that block around as a unit.

It's an easy trap, because the code looks perfect: no shared data, no locks, no race. And this time the JIT isn't involved at all; the cost lives in the hardware. Lesson 3 gave us honest benchmarks on one thread; now a second thread joins. In this lesson, we'll see how caches move memory, read real field offsets, set two counters fighting over one line, pad them apart, and meet the JDK's own answer, `LongAdder`. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
S0 = """A processor never reads a single `long` from memory on its own. Main memory is far away, as distances inside a computer go. So each core, one of the processor's units that runs a thread, keeps small, fast memories close by: its **caches** (called L1 and L2). They don't hold single variables. They hold **cache lines**, blocks of 64 bytes on x86 processors. The course machine says so directly: the file `/sys/devices/system/cpu/cpu0/cache/index0/coherency_line_size` contains 64.

A cache line is the cutting board: a fixed-size surface where the work happens. The hardware moves the whole board, never a single onion.

Each core keeps its own copy of any line it uses, and the hardware keeps the copies in step. That's **cache coherence**, which the memory model track met as the reason caches don't serve stale values. Coherence has a price, though. A core that wants to write a line needs the only valid copy of it. Every other core's copy is marked invalid, and the next time one of those cores touches the line, it has to fetch it again.

Now look at an ordinary object in memory. The report service works in two stages: a parser reads each document, and a writer produces its report. It counts what each stage has done. **JOL** (Java Object Layout), a small OpenJDK library, reads the real field offsets from the running JVM. An offset is a field's distance in bytes from the start of the object:

""" + pair(ADJ_J, ADJ_K) + """

(`volatile` makes each write visible to other threads at once, as the memory model track showed.) The first 12 bytes are the object header: 8 bytes of bookkeeping and a 4-byte pointer to the object's class. Then come 4 bytes of gap, so the `long`s start on an 8-byte boundary, and then the two fields, 8 bytes apart. The whole object is 32 bytes. Unless it happens to straddle the edge of a line, both counters sit on the same 64-byte line: the same board.

For code that reads, that's good news. Reading `parsed` brings `written` along for free, and arrays of numbers are fast to scan for the same reason. For two threads that each write their own field, it's bad news, as the next section shows.

Offsets depend on the JVM and its flags. On JDK 25 with `-XX:+UseCompactObjectHeaders` (JEP 519), the header shrinks to 8 bytes, and `LayoutDemo` then shows `parsed` at 8 and `written` at 16 in a 24-byte object. JDK 27 turns compact headers on by default (JEP 534). So when you check a layout in a test, check the distance between fields, never their absolute offsets.

**Memory moves in 64-byte lines, not in fields. Fields 8 bytes apart travel together.**

Two counters on one line cost nothing while one thread reads them. Let's give each of them a writer of its own."""

# ---------------------------------------------------------------- section 1
S1 = """The parsing thread now writes only `parsed`, and the writing thread writes only `written`. They share no data, so there's nothing to lock and no race, no two threads writing the same variable. But they share a line, and the line can live in only one core's cache for writing at a time.

Trace two writes. Core 1 holds the line and adds 1 to `parsed`. Core 2 wants to add 1 to `written`, finds its copy invalid, and waits while the line travels over. Now core 1's copy is invalid, so its next `parsed++` waits for the line to travel back. Each `++` is a few nanoseconds of work wrapped in a wait. When both threads run at the same moment, the line bounces between the cores on almost every write. This is **false sharing**: the program shares nothing, and the hardware shares a lot. The figure shows the bounce.

`FalseSharingDemo` runs exactly that, 25 million increments per thread: first with the adjacent fields, then with the fields padded apart. Before you read on, decide what you expect. Here is one run on the busy course machine:

```text
round 1: adjacent   994 ms   padded   785 ms
round 2: adjacent   977 ms   padded   784 ms
round 3: adjacent 1,124 ms   padded   806 ms
```

That's a gap, but a small one, and it wasn't even steady. Across nine runs here, in Java and Kotlin, the padded version lost one round in three. Was the mechanism wrong? No. More than 20 other busy programs were sharing the machine's four cores, so our two threads were rarely running at the same moment. A line can only bounce between two cores that both want it right now. When this lesson was first written, on a quieter day, the same demo on the same machine told the textbook story: adjacent took 957 to 1,387 ms and padded 206 to 247 ms, about five times faster.

Where the threads run matters too. Two hyperthreads, two hardware threads that share one physical core, also share that core's L1 and L2 caches. Put the two writers there, and there's no line to bounce at all.

So don't promise anyone a speed-up from padding. The mechanism is certain, and the size of the effect isn't. The only way to know is to measure on the hardware you run on, under the load you run with. When it does hit, it hits code that looks perfectly innocent: a stats object with one counter per worker thread, or an array of per-thread totals whose slots sit 8 bytes apart.

**Separate fields aren't separate memory. Fields that different threads write in a hot loop need lines of their own.**

The cure, when you need it, is space between the fields. Java makes that a little harder than it sounds."""

# ---------------------------------------------------------------- section 2
S2 = """The fix is to keep at least 64 bytes between fields that different threads write: give each cook a board of their own. **Padding** means unused bytes placed between fields for exactly that reason. There are three ways to add it.

The first is padding fields inside one class: 8 or more unused `long`s between `parsed` and `written`. On today's HotSpot it works (`written` moved to offset 152), but JMH's false-sharing sample warns that this is "not versatile because JVMs can freely rearrange the field order, even of the same type".

The second is a chain of classes. The same sample notes that "superclass fields are usually laid out first". So put each hot field and each block of padding in a class of its own, and chain them, each class extending the one before:

""" + pair(PAD_J, PAD_K) + """

This is the shape the lab asks for. `@JvmField` in the Kotlin version makes each property a plain public field, which keeps the layout easy to read.

The third is `@Contended`, the JDK's own annotation, `jdk.internal.vm.annotation.Contended`, available since JDK 8. The JVM adds `ContendedPaddingWidth` bytes of padding, 128 by default, around each annotated field. On JDK 25, JOL on a class with both counters annotated showed `parsed` at offset 144, `written` at 280, and a 288-byte object. Its Javadoc warns that it "will nearly always add significant space overhead to objects".

There are two catches for your own classes. First, the JVM ignores the annotation outside the JDK unless you run with `-XX:-RestrictContended`. Without that flag, JOL showed the same 16 and 24 as no annotation at all, and the JVM printed no warning. It simply ignores you, politely. Second, the annotation lives in an internal package, so compiling needs `--add-exports java.base/jdk.internal.vm.annotation=ALL-UNNAMED`. javac refuses that together with `--release`: "exporting a package from system module java.base is not allowed with --release". This course's labs compile with `--release 21`, so they can't use it.

Every kind of padding costs memory: 160 bytes instead of 32 here, and 288 with `@Contended`. That's nothing for one counter object and a lot for a million of them.

**Padding costs memory on every object. Pad the few that several threads write in a hot loop, and check their offsets.**

Check yourself: a class declares `volatile long a;`, then seven padding `long`s, then `volatile long b;`. JOL shows `a` at 16 and `b` at 80. Can they share a line? (No: they're 64 bytes apart. But another JVM may order the fields differently, which is why the lab's test reads the real offsets instead of trusting the source.)

Hand padding is fiddly, costs memory and leans on JVM habits. For the most common case, a counter that many threads bump, the JDK has already done all of it."""

# ---------------------------------------------------------------- section 3
S3 = """Hand padding is for library authors. For a counter in your own code, use `LongAdder`. `LongAdder` (and its sibling `LongAccumulator`) extends `Striped64`, whose source explains the design. Its table entries are a "variant of AtomicLong padded (via @Contended) to reduce cache contention", because "Atomic objects residing in arrays will tend to be placed adjacent to each other, and so will most often share cache lines (with a huge negative performance impact) without this precaution". That's the `value` at offset 144 you saw in `LayoutDemo`.

In the kitchen, it's each cook keeping a tally of dishes on a slip by their own board, and the manager adding the slips up at closing time.

The slips are only handed out when needed. The source says: "When there is no contention, all updates are made to the base field." **Contention** means threads getting in each other's way. Here it's a failed compare-and-set. Compare-and-set is the "update it only if nobody beat me to it" instruction behind `AtomicLong`, the JDK's thread-safe counter, and it fails when another thread changed the value first. On the first failed compare-and-set, `LongAdder` creates a table of 2 cells, and it doubles the table under more contention. Each thread then mostly updates its own cell, on its own line. `sum()` adds up the base and the cells. As "Atomics and compare-and-set" said, `sum()` is not an atomic snapshot. So use `LongAdder` for counters you read now and then, such as metrics, and `AtomicLong` when the value drives a decision.

Here's the report service's request counter, the one the lab fixes. Every request thread calls `record` once per report, and a monitoring program reads the totals every few seconds:

""" + pair(ADDER_J, ADDER_K) + """

`AdderDemo` races the two kinds of counter: four threads count 10 million requests each, first into one `AtomicLong`, then into one `LongAdder`. On the busy course machine, the race came out backwards:

```text
round 1: AtomicLong   705 ms (40,000,000)   LongAdder 1,320 ms (40,000,000)
round 2: AtomicLong   693 ms (40,000,000)   LongAdder 1,144 ms (40,000,000)
round 3: AtomicLong   680 ms (40,000,000)   LongAdder 1,156 ms (40,000,000)
```

Both counts are exact, as they always are. The speed tells the false-sharing story again. With 20 other programs competing for four cores, our four threads mostly took turns, so their compare-and-sets rarely failed, and `LongAdder` paid for bookkeeping it didn't need. On the quieter day when this lesson was first written, the same demo gave `AtomicLong` 640 to 760 ms per round and `LongAdder` about 200 ms. With four threads really running at once, all four cores fought over the `AtomicLong`'s single line, and `LongAdder` let each of them work on its own padded cell.

This is also where the cutting-board picture breaks. A cook who waits for the board notices, and it costs seconds. A core waits nanoseconds for a line, and nobody notices until it happens a few hundred million times. That's why you measure instead of guessing.

**Many writers and rare readers: count with LongAdder. When the value drives a decision, use AtomicLong.**

We can now measure a piece of code carefully, but only a piece we already suspect. A real program has thousands of methods, so the next question is how to catch a running JVM in the act."""

L = {
 "id": "perf-04",
 "title": "CPU caches, false sharing and @Contended",
 "minutes": 36,
 "goal": "By the end you can explain why two threads writing different fields can slow each other down, check field offsets with JOL, pad hot fields apart, and know when `LongAdder` is the better answer.",
 "opening": OPENING,
 "warmup": {
  "q": "In the report service, one thread only ever writes `stats.parsed` (documents parsed), and another only ever writes `stats.written` (reports written). Both fields are `volatile long` in the same small object. What can go wrong?",
  "options": [
   "Nothing: they never touch the same field, so there's no contention",
   "Lost updates, because `++` on a volatile isn't atomic",
   "Both threads can slow down, because the two fields share a cache line that the cores keep taking from each other",
   "A deadlock between the two threads"
  ],
  "answer": 2,
  "why": "Caches move memory in 64-byte lines, and a core that writes a line needs the only copy. Two fields 8 bytes apart sit on one line, so every write by one thread invalidates the other core's copy, and the other way round. Nothing is lost: each field has a single writer, so `++` on it is safe. How much time it costs depends on the machine, as the section on false sharing shows."
 },
 "sections": [
  {
   "h": "Caches move memory in 64-byte lines",
   "body": S0,
   "try": {
    "title": "Read real layouts with JOL",
    "minutes": 4,
    "steps": [
     "Before you run anything, predict the offset of `written` in each of the three classes in `LayoutDemo`.",
     "Run `LayoutDemo`. Ignore JOL's two `# WARNING` lines about attaching to the JVM.",
     "Look at the last entry: `Striped64$Cell`, the class `LongAdder` uses inside. Where is its only field?",
     "Run the Kotlin twin and compare."
    ],
    "code": demo("LayoutDemo"),
    "expect": "On JDK 21 and JDK 25: `Adjacent` is 32 bytes with `parsed` at 16 and `written` at 24. `PaddedInOneClass` is 160 bytes with `written` at 152. `Padded`, built from a chain of classes, is 160 bytes with `written` at 88, 72 bytes after `parsed`. `Cell` is 152 bytes, and its `value` field sits at offset 144: the JDK pads it on purpose. Kotlin's `@Volatile var` fields get exactly the same layout. With `-XX:+UseCompactObjectHeaders` on JDK 25, every offset moves down by 8 and every distance stays the same. On JDK 25, JOL also prints warnings about `sun.misc.Unsafe`, which it uses internally."
   },
   "refs": [
    {"title": "JOL (Java Object Layout)", "url": "https://github.com/openjdk/jol", "kind": "docs"}
   ]
  },
  {
   "h": "False sharing: two threads, two fields, one line",
   "body": S1,
   "figure": {"svg": FIG, "caption": "Adjacent fields share a line, so every write by one core invalidates the other core's copy. Padded apart, each core keeps its own line."},
   "try": {
    "title": "Race two counters on one line",
    "minutes": 4,
    "steps": [
     "Read `FalseSharingDemo`. Predict: will the adjacent run be slower, the same, or faster than the padded one on your machine?",
     "Close other busy programs if you can. Run it, then run it again. Then run the Kotlin twin.",
     "If you see a big gap, check how many physical cores your machine has (`lscpu` on Linux, `sysctl -n hw.physicalcpu` on macOS). If you see none, check how busy the machine is (`uptime` shows the load)."
    ],
    "code": demo("FalseSharingDemo"),
    "expect": "On a laptop with several physical cores and little else running, the adjacent run is often several times slower than the padded one. On a busy machine you may see a small gap, none, or the reverse, as the course machine did (about 1,000 ms against 800 ms, with some rounds reversed). All four counts always end at exactly 25,000,000: false sharing costs time, never correctness."
   }
  },
  {
   "h": "Padding pushes hot fields onto separate lines",
   "body": S2,
   "refs": [
    {"title": "JMHSample_22_FalseSharing", "url": "https://github.com/openjdk/jmh/blob/master/jmh-samples/src/main/java/org/openjdk/jmh/samples/JMHSample_22_FalseSharing.java", "kind": "read"}
   ]
  },
  {
   "h": "LongAdder: the padding the JDK already did for you",
   "body": S3,
   "try": {
    "title": "AtomicLong against LongAdder",
    "minutes": 3,
    "steps": [
     "Predict which one finishes first with four threads, and by how much.",
     "Run `AdderDemo`, then the Kotlin twin.",
     "Change `THREADS` to 1 and run again. Does `LongAdder` still win?"
    ],
    "code": demo("AdderDemo"),
    "expect": "Both always count exactly 40,000,000. With four threads on a machine with free cores, `LongAdder` usually finishes well ahead. On a busy machine it can lose, as it did on the course machine (about 690 ms against 1,150 ms). With one thread, the counts are 10,000,000 and `AtomicLong` wins: 103 ms against 181 ms in the last round on the course machine. With no contention, `LongAdder` only touches its base field, its cells never exist, and its extra checks are pure cost."
   }
  }
 ],
 "compare": {
  "title": "A padded counter in Java and Kotlin",
  "java": {"title": "StageCounters.java", "src": PAD_J},
  "kotlin": {"title": "StageCounters.kt", "src": PAD_K},
  "note": "Both compile to the same JVM classes with the same field layout, because the JVM decides the layout, not the language. The differences are in what you write. Kotlin classes are final by default, so the padding classes need `abstract` or `open`. A Kotlin `var` property is a private field plus a getter and a setter; `@JvmField` exposes the field directly, and `@Volatile` makes it volatile. In both languages the padding fields are never read, and nothing in either language promises the order of fields within one class, which is why the chain of classes is the safer trick."
 },
 "worked": {
  "title": "Find false sharing in a stats object and fix it",
  "steps": [
   {"say": "The report service has two worker threads, and each updates its own counter in one shared stats object. A profile shows both threads spending time in `record`, which does almost nothing. Start by printing the layout.", "code": "System.out.println(ClassLayout.parseClass(WorkerStats.class).toPrintable());", "lang": "java", "alt_lang": "kotlin", "alt_code": "println(ClassLayout.parseClass(WorkerStats::class.java).toPrintable())"},
   {"say": "The two hot fields are 8 bytes apart. Worker 0 writes `done0`, worker 1 writes `done1`, and both sit on one line. This is JOL's real output on JDK 25.", "code": "OFF  SZ   TYPE DESCRIPTION               VALUE\n  0   8        (object header: mark)     N/A\n  8   4        (object header: class)    N/A\n 12   4        (alignment/padding gap)   \n 16   8   long WorkerStats.done0         N/A\n 24   8   long WorkerStats.done1         N/A\nInstance size: 32 bytes", "lang": "text"},
   {"say": "Give each worker its own object instead of padding one. Two `WorkerCounter` objects created one after the other can still end up next to each other in memory, so if the profile still shows the problem, pad the counter class or use a `LongAdder`. Self-check: why don't separate objects guarantee separate lines? (Answer: each thread gets new objects from its own stretch of the heap, one after another, so two small objects created together are often only a few bytes apart.)", "code": "final class WorkerCounter {\n    volatile long done;             // one writer: the worker's own thread\n}\nWorkerCounter[] counters = { new WorkerCounter(), new WorkerCounter() };", "lang": "java", "alt_lang": "kotlin", "alt_code": "class WorkerCounter {\n    @Volatile var done = 0L         // one writer: the worker's own thread\n}\nval counters = arrayOf(WorkerCounter(), WorkerCounter())"},
   {"say": "Verify with a forked JMH benchmark that runs two threads, on the hardware and under the load you deploy to, not on your laptop alone. Keep the version that measures faster there. If neither is clearly faster, keep the simpler code.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Pad two counters and fix a metrics counter",
  "minutes": 13,
  "files": [f"{lab}/main/{P}/StageCounters.java", f"{lab}/main/{P}/RequestMetrics.java"],
  "run": "./gradlew :performance:test --tests 'workbench.performance.l04.*'",
  "steps": [
   "Open `StageCounters`, the report service's two counters: `parsed`, written only by the parsing thread, and `written`, written only by the writing thread. Then open `RequestMetrics`, which every request thread calls once per report. Run the tests. Three of four fail: `parsed` and `written` are 8 bytes apart (at 16 and 24), and `RequestMetrics` loses updates when 8 threads record at once.",
   "Lay out `StageCounters` so `parsed` and `written` are at least 64 bytes apart. Keep both fields `volatile long` with those exact names, and keep the public methods. A chain of classes is the reliable way.",
   "Fix `RequestMetrics` so `count()` and `totalWords()` are exact under contention. Writes happen on every request and reads every few seconds, so pick the tool built for that.",
   "Run the tests until all four pass. Run them twice: the metrics tests are race tests.",
   "Optional: print `ClassLayout.parseClass(StageCounters.class).toPrintable()` in a scratch test and look at your layout."
  ],
  "hints": [
   "HotSpot lays out superclass fields before subclass fields. `abstract class ParsedCounter { volatile long parsed; }`, then a class with eight `long` padding fields extending it, then a class with `written` extending that, and `StageCounters` at the end of the chain.",
   "The fields in the superclasses can't be `private` if `StageCounters` needs to read them. Package-private works, and JOL finds fields in superclasses too.",
   "`count++` on a `volatile` is a read and a write, so two threads can both read 41 and both write 42. With many writers, `LongAdder.increment()` and `add(words)` are exact and spread the writes over padded cells.",
   "The reference solution puts `written` 72 bytes after `parsed` and passes on JDK 21 and JDK 25."
  ],
  "done_when": "All four tests in `CacheLineTest` pass, twice in a row."
 },
 "drill": {
  "title": "Explain a layout and write the fix from memory",
  "minutes": 4,
  "prompt": "Close this page. JOL prints `parsed` at offset 16 and `written` at offset 24 for a class that two threads write. Write two sentences on what goes wrong and why, then write a padded version using a chain of classes. Then write the one-line answer you'd give for a request counter written by 200 threads.",
  "answer": {"lang": "java", "src": "// parsed and written are 8 bytes apart, so they share one 64-byte cache line. Each write by one\n// core invalidates the other core's copy, so the line bounces between them (false sharing).\n\nabstract class ParsedCounter { volatile long parsed; }\nabstract class PadAfterParsed extends ParsedCounter { long p1, p2, p3, p4, p5, p6, p7, p8; }\nabstract class WrittenCounter extends PadAfterParsed { volatile long written; }\npublic final class StageCounters extends WrittenCounter { }\n\n// 200 writers, occasional reads: use a LongAdder\nprivate final LongAdder requests = new LongAdder();",
             "alt": {"lang": "kotlin", "src": "// parsed and written are 8 bytes apart, so they share one 64-byte cache line. Each write by one\n// core invalidates the other core's copy, so the line bounces between them (false sharing).\n\nabstract class ParsedCounter { @Volatile @JvmField var parsed = 0L }\nabstract class PadAfterParsed : ParsedCounter() {\n    @JvmField var p1 = 0L; @JvmField var p2 = 0L; @JvmField var p3 = 0L; @JvmField var p4 = 0L\n    @JvmField var p5 = 0L; @JvmField var p6 = 0L; @JvmField var p7 = 0L; @JvmField var p8 = 0L\n}\nabstract class WrittenCounter : PadAfterParsed() { @Volatile @JvmField var written = 0L }\nclass StageCounters : WrittenCounter()\n\n// 200 writers, occasional reads: use a LongAdder\nprivate val requests = LongAdder()"}}
 },
 "recap": [
  "Caches move memory in 64-byte lines, and a core that writes a line invalidates every other core's copy.",
  "False sharing: two threads writing different fields on the same line make it bounce between cores. It costs time, never correctness, and how much depends on the hardware and on whether the threads really run at once.",
  "Pad hot fields at least 64 bytes apart. A chain of classes is reliable; padding fields in one class may be reordered; `@Contended` needs `-XX:-RestrictContended` and an internal export for your own classes.",
  "Check layouts with JOL and assert distances, not offsets: headers differ between JDKs and flags (compact object headers are the default in JDK 27).",
  "For counters in your own code, use `LongAdder`: its cells are padded with `@Contended` and only created under contention. Without contention, `AtomicLong` is a little faster.",
  "The limit: everything here makes one known hot spot cheaper. None of it tells you where a running program actually spends its time; that's what the profilers in the next lessons are for."
 ],
 "closing": "We started with two cooks who never touch each other's vegetables and still keep waiting, because they share one cutting board. Two threads that write two fields on one cache line do the same, and padding, a chain of classes or `LongAdder`'s padded cells give each its own board. How much it costs depends on the machine, so measure where you run.\n\nNow look in your code for an array or object where each thread writes its own slot or field in a busy loop. Slots 8 bytes apart share a line.\n\nNext, we'll stop guessing where a running program spends its time: how can the JDK Flight Recorder log what the JVM was doing, on one clock, cheaply enough to leave on?",
 "quiz": [
  {"q": "JOL shows `w0` at offset 16 and `w1` at offset 24 in a stats object. Thread 0 only writes `w0`, thread 1 only writes `w1`. What is the problem, if any?",
   "options": ["A race: updates to `w0` and `w1` can be lost", "False sharing: the fields share a cache line, so the two cores keep invalidating each other's copy", "None: different fields never interact", "The object is too big to fit in a cache line"],
   "answer": 1,
   "why": "8 bytes apart means one 64-byte line. Each field has one writer, so nothing is lost, but every write takes the line away from the other core. That costs time, not correctness."},
  {"q": "You annotate two fields of your own class with `@jdk.internal.vm.annotation.Contended`, compile it, and run it normally. JOL shows them at 16 and 24. Why?",
   "options": ["`@Contended` only works on JDK 27", "JOL can't see padding", "The JVM ignores `@Contended` outside the JDK unless you run with `-XX:-RestrictContended`", "The fields must also be `final`"],
   "answer": 2,
   "why": "`RestrictContended` is true by default, so the annotation only takes effect in JDK classes. With `-XX:-RestrictContended`, the same class shows the fields at 144 and 280. The JVM prints no warning either way."},
  {"q": "A metrics counter is incremented by every request thread and read by a monitoring program every 10 seconds. Which is the best fit?",
   "options": ["A `volatile long` with `count++`", "An `AtomicLong`", "A `long` field inside a `synchronized` method", "A `LongAdder`"],
   "answer": 3,
   "why": "Many writers and rare reads is exactly what `LongAdder` is for: under contention, each thread mostly updates its own padded cell. `AtomicLong` is correct but makes all writers fight over one line. `volatile` with `++` loses updates."},
  {"q": "Your test checks that two fields are \"at offset 16 and offset 88\". It passes on JDK 21 and fails on JDK 27. What's the best fix?",
   "options": ["Assert the distance between the fields (at least 64 bytes) instead of absolute offsets", "Pin the tests to JDK 21", "Turn off JOL on JDK 27", "Add more padding until both pass"],
   "answer": 0,
   "why": "JDK 27 turns compact object headers on by default, so every field moves by a few bytes. The distance between the two fields is what decides whether they share a line, and it doesn't depend on the header size."},
  {"q": "From the first track: two threads call `counter.incrementAndGet()` on a shared `AtomicLong` 10 million times each. Then you switch to `LongAdder.increment()`. What changes in the result?",
   "options": ["`LongAdder` may lose some increments, but it's faster", "Nothing: both count exactly. Under real contention `LongAdder` usually gets there faster", "`AtomicLong` loses increments under contention", "`LongAdder.sum()` is always more up to date than `AtomicLong.get()`"],
   "answer": 1,
   "why": "Both are exact once all the writes finish. `LongAdder` spreads writes over cells so threads stop fighting over one cache line, which pays off when they really run at the same time. Its `sum()` is not an atomic snapshot while writes are still happening, which is why decisions should use `AtomicLong`.",
   "from": "conc-08"}
 ],
 "flashcards": [
  {"front": "How big is a cache line on x86?", "back": "64 bytes. Caches move whole lines, never single fields."},
  {"front": "What is false sharing?", "back": "Threads writing different fields that sit on the same cache line, so the line keeps moving between cores. It costs time, not correctness."},
  {"front": "How far apart must two hot fields be to avoid sharing a 64-byte line?", "back": "At least 64 bytes between their offsets."},
  {"front": "Why is a chain of classes better than padding fields inside one class?", "back": "HotSpot lays out superclass fields before subclass fields; within one class the JVM may reorder fields, even of the same type."},
  {"front": "What does `@Contended` need to work on your own classes?", "back": "`-XX:-RestrictContended` at run time (otherwise it's silently ignored) and `--add-exports java.base/jdk.internal.vm.annotation=ALL-UNNAMED` to compile."},
  {"front": "How does `LongAdder` avoid false sharing?", "back": "Under contention it spreads updates over `Striped64.Cell` objects, each padded with `@Contended` (JOL shows the value at offset 144). `sum()` adds them up."},
  {"front": "Why should a layout test assert distances, not offsets?", "back": "Header sizes differ between JDKs and flags: compact object headers (default in JDK 27) move every field."}
 ],
 "terms": [
  {"term": "Cache line", "plain": "The unit a CPU cache moves around: 64 bytes on x86."},
  {"term": "Cache coherence", "plain": "The hardware keeping every core's copy of a line consistent, by invalidating copies on writes."},
  {"term": "False sharing", "plain": "Different data on one cache line, written by different cores, making the line bounce between them."},
  {"term": "Padding", "plain": "Unused bytes placed between fields so they land on different cache lines."},
  {"term": "@Contended", "plain": "A JDK-internal annotation that makes the JVM pad a field or class, 128 bytes by default."},
  {"term": "JOL", "plain": "Java Object Layout, a tool that prints the real field offsets and object sizes."},
  {"term": "LongAdder", "plain": "A counter that spreads contended updates over padded cells and adds them up on read."}
 ],
 "explain_back": {
  "prompt": "Explain to a teammate why giving each worker thread its own field in a shared stats object didn't make the counters fast, and what you'd do instead.",
  "answer": "The fields are separate, so there's no race, but they sit 8 bytes apart, which puts them on the same 64-byte cache line. A core can only write a line it holds alone, so each write by one thread invalidates the other core's copy, and the line moves back and forth on almost every update. That's false sharing. One fix is to pad the fields at least 64 bytes apart, ideally with a chain of classes because the JVM may reorder fields within one class, and to check the offsets with JOL. For ordinary counters I'd use a LongAdder per counter instead: it creates padded cells only when threads contend and adds them up when we read. And I'd only believe a speed-up after measuring it on our real hardware under real load, because how much false sharing costs depends on the CPU and on whether the threads truly run at the same time."
 },
 "deeper": {
  "minutes": 10,
  "body": "JMH protects you from one source of false sharing automatically. Its false-sharing sample says \"@States are automatically padded\", but \"This padding does not extend to the State internals\". Fields inside your `@State` object can still share a line, which is exactly what that sample demonstrates, with several fixes side by side. To measure it on your own hardware, run that sample with several forks on a machine with real cores and little else running.\n\nWhy does the JDK pad with 128 bytes when lines are 64? The flag `ContendedPaddingWidth` only says how many bytes to pad. A common explanation is that some processors also fetch the neighbouring line, so a 64-byte gap can still let two hot fields interfere. This course couldn't check that against a primary source, so treat 128 as \"the JDK's safe default\" rather than a rule.\n\nTwo other tools look at the same problem from the hardware side. `perf c2c` on Linux reports cache lines that bounce between cores (JMH wraps it as `-prof perfc2c`). And a CPU profiler such as async-profiler, in lesson 6, shows the symptom: lots of samples on a trivial line such as `count++`.\n\nThere's also true sharing, which padding can't fix: many threads writing the same field, like an `AtomicLong` hit by every request. The only fixes there are to write less often or to split the value, which is what `LongAdder` does."
 },
 "sources": [
  {"title": "Striped64.java: the padded cells behind LongAdder (JDK 25)", "url": "https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/atomic/Striped64.java"},
  {"title": "Contended.java: the annotation and its Javadoc (JDK 25)", "url": "https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/jdk/internal/vm/annotation/Contended.java"},
  {"title": "JMHSample_22_FalseSharing", "url": "https://github.com/openjdk/jmh/blob/master/jmh-samples/src/main/java/org/openjdk/jmh/samples/JMHSample_22_FalseSharing.java"},
  {"title": "LongAdder (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/atomic/LongAdder.html"},
  {"title": "JOL (Java Object Layout)", "url": "https://github.com/openjdk/jol"}
 ]
}
out = ROOT / "content/lessons/perf-04.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
