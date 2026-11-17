import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/performance/src"
P = "java/workbench/performance/l01"
K = "kotlin/workbench/performance/l01"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :performance:demo -Pmain=workbench.performance.l01."

def demo(name, kname=None):
    kname = kname or name
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": DEMO + name, "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{kname}.kt", "src": read(f"{lab}/demo/{K}/{kname}.kt"),
                    "run": DEMO + kname + "Kt", "file": f"{lab}/demo/{K}/{kname}.kt"}}

def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"

FIG = """<svg viewBox="0 0 680 230" role="img" aria-label="One PrintCompilation line split into its columns: time, compile id, OSR flag, tier, method, loop bytecode index and bytecode size">
<rect class="box" x="30" y="92" width="56" height="38" rx="8"/><text class="t t-code" x="58" y="116" text-anchor="middle">56</text>
<rect class="box" x="96" y="92" width="56" height="38" rx="8"/><text class="t t-code" x="124" y="116" text-anchor="middle">13</text>
<rect class="box-b" x="162" y="92" width="44" height="38" rx="8"/><text class="t t-code" x="184" y="116" text-anchor="middle">%</text>
<rect class="box-a" x="216" y="92" width="44" height="38" rx="8"/><text class="t t-code" x="238" y="116" text-anchor="middle">4</text>
<rect class="box" x="270" y="92" width="136" height="38" rx="8"/><text class="t t-code" x="338" y="116" text-anchor="middle">Hot::longLoop</text>
<rect class="box-b" x="416" y="92" width="56" height="38" rx="8"/><text class="t t-code" x="444" y="116" text-anchor="middle">@ 4</text>
<rect class="box" x="482" y="92" width="112" height="38" rx="8"/><text class="t t-code" x="538" y="116" text-anchor="middle">(27 bytes)</text>
<line class="ln-d" x1="58" y1="62" x2="58" y2="92"/><text class="t-s" x="58" y="56" text-anchor="middle">ms since start</text>
<line class="ln-d" x1="124" y1="130" x2="124" y2="166"/><text class="t-s" x="124" y="182" text-anchor="middle">compile id</text>
<line class="ln-d" x1="184" y1="62" x2="184" y2="92"/><text class="t-s t-b" x="184" y="56" text-anchor="middle">OSR</text>
<line class="ln-d" x1="238" y1="130" x2="238" y2="166"/><text class="t-s t-a" x="238" y="182" text-anchor="middle">tier 4 = C2</text>
<line class="ln-d" x1="338" y1="62" x2="338" y2="92"/><text class="t-s" x="338" y="56" text-anchor="middle">Class::method</text>
<line class="ln-d" x1="444" y1="130" x2="444" y2="166"/><text class="t-s t-b" x="444" y="182" text-anchor="middle">enters at bytecode 4</text>
<line class="ln-d" x1="538" y1="62" x2="538" y2="92"/><text class="t-s" x="538" y="56" text-anchor="middle">bytecode size</text>
<text class="t-s t-m" x="340" y="214" text-anchor="middle">a message such as "made not entrant: not used" can follow the size</text>
</svg>"""

OPENING = """Picture a new cook in a busy restaurant. On the first day, every dish is cooked from its recipe card, one line at a time. Dishes that get ordered often earn a quick cheat sheet. The house favourites get practised until the cook can make them without looking, with a few shortcuts based on what customers usually order.

The JVM, the program that runs your compiled Java and Kotlin, learns your code the same way. In this lesson's first demo, the fifth batch of identical work ran thirteen times faster than the first. Nobody changed a line.

That makes an easy trap. Time a piece of code once, right after the program starts, and you measure the cook's first day, with a number that looks perfectly precise. The memory track ended by hunting memory a program holds on to for no reason; this track asks where the time goes. In this lesson, we'll watch a method climb from the interpreter to C1 to C2, read the compile log, catch a loop compiled mid-run, and see why every new JVM starts cold. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_READ = """// seconds to read a document at 238 words a minute, rounded up
static long readingSeconds(long words) {
    return (words * 60 + 237) / 238;
}"""
K_READ = """// seconds to read a document at 238 words a minute, rounded up
fun readingSeconds(words: Long): Long = (words * 60 + 237) / 238"""

S0 = """Let's meet the program we'll follow through this track. It's a small **report service**: a program that takes a document, such as an article or a chapter of a book, and writes a short report about it. How many words does it have? How long does it take to read? Is it made of paragraphs, headings or quotes?

One of its jobs is the reading time. At 238 words a minute, rounded up to the next second, it's one line:

""" + pair(J_READ, K_READ) + """

`WarmupDemo`, in the Try it below, fills an array with the word counts of 20,000 documents. Then it times the same batch of 20,000 calls twelve times in a row: same code, same data. One run on JDK 25 printed:

```text
batch  1:  1,002 us
batch  2:    713 us
batch  3:    682 us
batch  4:    482 us
batch  5:     78 us
batch  6:  2,406 us
batch  7:     77 us
batch  8:     77 us
batch  9:     76 us
batch 10:    118 us
batch 11:     76 us
batch 12:     76 us
```

The course machine was busy, with more than 20 programs sharing its four cores, so treat every number as rough. The shape is what matters: four slow batches, then a drop to about 78 µs. Batch 6 is an odd one. A slow batch showed up there in most runs, even with the compiler switched off, so blame the busy machine. Lesson 3 teaches you to distrust a single strange number.

The speed-up comes from how the JVM runs code. `javac` and `kotlinc` don't produce machine code for your processor. They produce **bytecode**: compact instructions for the JVM, stored in `.class` files, such as `lload` (push a local `long` onto a stack) or `lmul` (multiply two longs). HotSpot, the JVM in every OpenJDK build, starts every method in the **interpreter**, a loop inside the JVM that reads one bytecode instruction at a time and carries it out. That's the cook on day one, reading the card line by line.

While it reads, the JVM keeps tally marks: how often each method is called, and how often each loop jumps back to its start (a **back-edge**). When the marks pass a threshold, a compiler thread turns the method into machine code in the background, and the next call runs that instead. This is the **JIT** (just-in-time) compiler. It compiles while the program runs, so it can see what your code really does.

HotSpot has two JIT compilers. **C1** compiles quickly and optimizes a little: the cheat sheet. **C2** compiles slowly and optimizes hard, using a **profile**, notes on what the code really did: which branches ran, which types turned up at each call. That's the dish practised until it's automatic, with shortcuts that bet on the usual orders. Tiered compilation, on by default, uses all of them in five levels:

| Tier | Runs the code | Notes |
|---|---|---|
| 0 | interpreter | counts calls and back-edges |
| 1 | C1, no profiling | for trivial methods such as getters |
| 2 | C1 with counters only | used in some cases, for example while C2 has a backlog |
| 3 | C1 with full profiling | records branch counts and the types seen at each call |
| 4 | C2 | compiles with the profile that tier 3 collected |

The normal path is 0, then 3, then 4. On JDK 25 a method reaches tier 3 after about 200 calls (`Tier3InvocationThreshold`) and tier 4 after about 5,000 more (`Tier4InvocationThreshold`). Loop laps count too. `-XX:+PrintFlagsFinal` lists these defaults, and they're the same from JDK 21 to JDK 27. When the compile queues are long, the JVM raises the bar on the fly, so treat them as rough sizes.

You may have read that a method is compiled after 10,000 calls. That's `CompileThreshold`, which only applies with `-XX:-TieredCompilation`. The blog posts weren't wrong, just old: tiered compilation has been the default since JDK 8.

Let's check the tiers by taking some away. With `-Xint`, interpreter only, every batch stayed between 630 and 920 µs, apart from one 2.7 ms batch. With `-XX:TieredStopAtLevel=1`, C1 only, the batches fell to 69 µs from batch 6 on, a touch faster than the default run. On a one-line method, the cheat sheet is already about as good as it gets. C2 earns its slow compile on bigger code, where its bets pay off, as lesson 2 shows.

**The same code runs at different speeds depending on how long the JVM has watched it. Never trust the first lap.**

So something compiled our loop around batch 5. But which compiler, and when? The JVM will tell us, if we ask."""

# ---------------------------------------------------------------- section 1
J_HOT = """interface Block { long millis(); }   // one piece of a document: how long to read it?
record Paragraph(long words) implements Block { public long millis() { return words * 250; } }

static long readingMillis(Block[] blocks) {
    long sum = 0;
    for (Block b : blocks) sum += b.millis();
    return sum;
}"""
K_HOT = """interface KBlock { fun millis(): Long }   // one piece of a document: how long to read it?
class KParagraph(private val words: Long) : KBlock { override fun millis() = words * 250 }

fun readingMillis(blocks: Array<KBlock>): Long {
    var sum = 0L
    for (b in blocks) sum += b.millis()
    return sum
}"""

S1 = """`-XX:+PrintCompilation` makes the JVM print one line each time a compile finishes, and another when it stops using compiled code. To read the log, we need a program with a story. The `Hot` demo is a slice of the report service. A document is a list of blocks, and each kind of block knows how long it takes to read:

""" + pair(J_HOT, K_HOT) + """

`Hot` does three things. It runs `longLoop`, one method whose loop makes 50 million laps, like one pass over a huge book. Then it adds up the reading time of an article of 1,000 paragraphs, 20,000 times. Finally it switches to a document that mixes paragraphs, headings and quotes. These are real lines from its log on JDK 25, picked from about fifty:

```text
55   11 %     3       workbench.performance.l01.Hot::longLoop @ 4 (27 bytes)
56   13 %     4       workbench.performance.l01.Hot::longLoop @ 4 (27 bytes)
67   11 %     3       workbench.performance.l01.Hot::longLoop @ 4 (27 bytes)   made not entrant: OSR invalidation of lower level
252   19       2       workbench.performance.l01.Hot$Paragraph::millis (9 bytes)
252   20       4       workbench.performance.l01.Hot$Paragraph::millis (9 bytes)
271   24       4       workbench.performance.l01.Hot::readingMillis (42 bytes)
309   24       4       workbench.performance.l01.Hot::readingMillis (42 bytes)   made not entrant: uncommon trap
```

Read the second line from left to right, with the figure beside you. It finished 56 ms after the JVM started, and its compile id is 13. The `%` says it's an OSR compile, a loop compiled while it runs, which is the next section's topic. The `4` says C2 did it. `@ 4` says the compiled code is entered at bytecode index 4. And `(27 bytes)` is the size of the method's bytecode, not of the machine code. Lesson 2 shows why that number matters: C2 counts these bytes when it decides what to copy into a caller.

The five characters after the id are flags. `%` marks OSR, `s` a `synchronized` method and `!` a method with a `try`/`catch`. `b` marks a compile the program had to wait for, and `n` a wrapper around a native method, one written in C outside Java. A line for a synchronized method looks like `58   25  s    3       Flags::syncInc (9 bytes)`.

The compile id ties lines together. Id 11 shows up twice: once as a compile, and once with `made not entrant`. That means the JVM stopped using that code, and new calls won't enter it. Most of these lines are housekeeping, because lower-tier code retires as soon as better code takes over. Since JDK 25, the JVM prints the reason after a colon. All three of these came from the same run:

```text
made not entrant: OSR invalidation of lower level   // C2's OSR code replaced C1's
made not entrant: not used                          // a newer compile of the method took over
made not entrant: uncommon trap                     // one of C2's bets failed (lesson 2)
```

JDK 21 prints a bare `made not entrant`, with no reason.

Now look at id 24 again. C2 compiled `readingMillis` at 271 ms and threw its work away at 309 ms, just after the headings and quotes arrived. Keep that line in mind; the next section starts to explain it, and lesson 2 finishes the job.

Two warnings before you go hunting in logs. First, times and ids change from run to run. In three runs of `Hot` on JDK 25, the first compile of `longLoop` landed at 55, 63 and 165 ms. When the JVM compiles depends on how busy its compiler threads are, so never compare two logs line by line. Second, the JDK compiles its own methods too, such as `String::hashCode`, so filter the log by your package.

The `%` lines are the strangest ones. `longLoop` is called exactly once, so how did it get compiled at all?"""

# ---------------------------------------------------------------- section 2
S2 = """`longLoop` never gets near 200 calls, yet it was the first of our methods to be compiled. If the JVM only counted calls, a method stuck in one long loop would stay in the interpreter forever. So it counts back-edges too.

Picture the cook making one enormous pot of soup for a wedding, adding the stock one ladle at a time. Halfway through, they work out a faster way to do it. They don't pour the pot away and start again. They switch technique mid-pot, and the soup carries on.

The JVM does the same. When one loop has jumped back about 60,000 times (`Tier3BackEdgeThreshold` on JDK 25), it compiles a version of the method that starts at the top of the loop. Then it moves the running call, with its local variables, into that code. This is **on-stack replacement** (OSR): the call's stack frame, the record of its local variables, is swapped for a compiled one while the call is still running. C2 does the same at tier 4 after about 40,000 more back-edges (`Tier4BackEdgeThreshold`).

The `@ 4` points at the loop. `javap -c`, the JDK's class-file printer, shows the bytecode:

```text
static long longLoop();
   0: lconst_0
   1: lstore_0
   2: iconst_0
   3: istore_2
   4: iload_2                 // top of the loop: the OSR code is entered here
   5: ldc     #13             // int 50000000
   7: if_icmpge 25            // the exit test: leave when i reaches 50 million
  ...
  22: goto    4               // the back-edge the JVM counts
```

Here is the rest of `longLoop`'s story, from the same JDK 25 run:

```text
55   11 %     3       ...Hot::longLoop @ 4 (27 bytes)
55   12       3       ...Hot::longLoop (27 bytes)
56   13 %     4       ...Hot::longLoop @ 4 (27 bytes)
67   11 %     3       ...Hot::longLoop @ 4 (27 bytes)   made not entrant: OSR invalidation of lower level
246   13 %     4       ...Hot::longLoop @ 4 (27 bytes)   made not entrant: uncommon trap
```

The first retirement is housekeeping: once the C2 OSR code exists, the JVM retires C1's. The second is more interesting. When the loop finishes at 246 ms, the C2 code throws itself away. Running the same program with `-Xlog:deoptimization=debug` says why:

```text
cid=13 osr level=4 workbench.performance.l01.Hot.longLoop()J trap_bci=7 osr_bci=4 unstable_if reinterpret
```

`trap_bci=7` is the exit test. While C1 watched the loop, it never saw the loop end, so C2 didn't compile the exit at all. It put an **uncommon trap** there instead: a small stub that hands the running call back to the interpreter if a branch C2 never saw ever runs. C2 bet that this loop would never end. It lost exactly once, at the very end, and it cost nothing. That's the JIT's betting habit in miniature, and lesson 2 is all about those bets.

The same log has lines for `readingMillis` with `trap_bci=27 class_check`, printed the moment the headings and quotes arrived. Bytecode 27 is the `b.millis()` call. That's id 24 from the last section, thrown away when a new kind of block showed up, and lesson 2 picks it up from there.

OSR matters to you for one practical reason. A benchmark written as one long loop in `main` measures OSR code and its quirks, which may not be the code your program runs after warm-up. JMH, the benchmarking tool in lesson 3, avoids that trap.

So the JVM compiles loops and methods, and retires code it no longer trusts. All that machine code has to live somewhere, and it doesn't survive a restart."""

# ---------------------------------------------------------------- section 3
S3 = """Machine code needs a place to live. HotSpot keeps it in the **code cache**, a memory area outside the heap, where your objects live. It's the cook's shelf of cheat sheets. With tiered compilation the JVM sets aside 240 MB for it (`ReservedCodeCacheSize`), split into three parts. `java -XX:+PrintCodeCache -version` on JDK 25 prints them as the JVM exits:

```text
CodeHeap 'non-profiled nmethods': size=120032Kb used=2Kb max_used=2Kb free=120029Kb
CodeHeap 'profiled nmethods': size=120032Kb used=4Kb max_used=4Kb free=120027Kb
CodeHeap 'non-nmethods': size=5700Kb used=1256Kb max_used=1256Kb free=4443Kb
CodeCache: size=245764Kb, used=1262Kb, max_used=1262Kb, free=244499Kb
```

An nmethod is HotSpot's name for one compiled method. Tier 2 and tier 3 code, which still counts and records, goes in 'profiled nmethods'. Tier 1 and tier 4 code goes in 'non-profiled nmethods'. The third part holds small pieces of glue that the interpreter and compiled code need. After `Hot` has run, the two method parts hold 10 KB and 18 KB. It's a big shelf.

A large program can still fill it. Then the JVM warns `CodeHeap 'non-profiled nmethods' is full. Compiler has been disabled.`, stops starting new compiles and schedules a clean-up so it can start again later. Until then, methods that aren't compiled yet stay in the interpreter. `jcmd <pid> Compiler.codecache` shows the parts on a running JVM. `jcmd` is a JDK tool that sends commands to a running JVM, and `<pid>` is the process id, the number the operating system gives each running program. Look there before you raise the size.

The bigger cost for a service is that every JVM starts from scratch, and here the picture breaks. A real cook remembers yesterday's dishes. A JVM forgets everything when its process ends, so every restart is the cook's first day again.

After the report service restarts, its first thousands of requests (a request is one user asking for one report) run in the interpreter and in C1. The busy paths reach C2 only after thousands of calls each, and the compiler threads share the machine's cores with the threads serving those requests. So a freshly started service answers more slowly for a while, and a test run against it in its first minute measures day one.

There are two usual answers. You can send it made-up warm-up requests before it takes real ones. Or, on JDK 25, you can hand the cook notes from a training day: an **AOT cache** (ahead-of-time cache), a file recorded during a training run. JEP 514 makes the cache easy to create, and JEP 515 adds method profiles to it:

```bash
java -XX:AOTCacheOutput=warm.aot -cp warm.jar workbench.performance.l01.WarmupDemo   # training run
java -XX:AOTCache=warm.aot -cp warm.jar workbench.performance.l01.WarmupDemo         # later runs
```

On the course machine, the training run wrote an 11 MB cache. `WarmupDemo` had to be packed into a jar first: given a folder of classes, the JVM refused with `Cannot have non-empty directory in paths`. In the next two runs, the batches were fast from batch 2; without the cache, from batch 5. The startup track covers the AOT cache properly.

**A number from the first seconds of a JVM measures the cook's first day. Measure after warm-up, or say it's a cold start.**

That rule will follow us through the whole track. Lesson 3 turns it into a tool that does the warm-up for you."""

L = {
 "id": "perf-01",
 "title": "From bytecode to machine code: interpreter, C1, C2",
 "minutes": 36,
 "goal": "By the end you can say which tier is running a method, read every column of a `-XX:+PrintCompilation` line, and explain OSR and why a freshly started JVM is slow.",
 "opening": OPENING,
 "warmup": {
  "q": "The report service has a method `scanBook()`. It is called once, and its loop runs over 3 million lines of a long book. When does HotSpot, the JVM in every OpenJDK build, compile it to machine code?",
  "options": [
   "Never: it is called once, far below any call threshold",
   "After 10,000 calls, so never on this run",
   "While the loop is still running: the JVM counts loop laps too, and moves the running call into compiled code",
   "Before it starts, when the class is loaded"
  ],
  "answer": 2,
  "why": "HotSpot counts the times a loop jumps back to its start (its back-edges) as well as calls. After about 60,000 back-edges it compiles a version of the method that starts at the loop and moves the running call into it, mid-loop. That's on-stack replacement (OSR), and the section on loops shows it happening. The 10,000-call figure is `CompileThreshold`, which only applies when tiered compilation is switched off."
 },
 "sections": [
  {
   "h": "Every method starts in the interpreter and climbs to C2",
   "body": S0,
   "try": {
    "title": "Watch the same batch get faster",
    "minutes": 4,
    "steps": [
     "Predict: `WarmupDemo` times the same batch of 20,000 reading-time calculations 12 times. Will batch 12 take as long as batch 1? Write your guess down.",
     "Run it from the `labs/` folder with the command below, and note the batch where the time drops.",
     "Run it again with `-Pargs=int`, which restarts it with `-Xint` (interpreter only), then with `-Pargs=c1` (`-XX:TieredStopAtLevel=1`, C1 only). Compare the last few batches of the three runs."
    ],
    "code": demo("WarmupDemo"),
    "expect": "With the defaults, the first four batches take several hundred microseconds each, then the time falls below 100 µs once compiled code takes over the loop. On the busy course machine (JDK 25) it went from about 1,000 µs to 78 µs. With `int`, every batch stays near 700 µs. With `c1` it gets fast too, here 69 µs. The drop comes around batch 5, not batch 2: `batch()` is called only 12 times, so it's the loop inside it that gets compiled, as the section on OSR explains. Your numbers will differ; the shape won't. The Gradle command runs the demo on the JDK that runs Gradle, so `java -version` tells you which one you measured."
   }
  },
  {
   "h": "Reading -XX:+PrintCompilation, one column at a time",
   "body": S1,
   "figure": {"svg": FIG, "caption": "One OSR line from PrintCompilation, column by column. The size is bytecode, not machine code."},
   "try": {
    "title": "Read the log of a running program",
    "minutes": 5,
    "steps": [
     "Read `Hot`. Predict which of `longLoop`, `readingMillis` and `Paragraph::millis` will reach tier 4, and which will get a `%` line.",
     "Run it. The demo starts a second JVM with `-XX:+PrintCompilation` and keeps only the lines for this lesson's classes.",
     "Find the first tier 4 compile of `readingMillis` without a `%`. Then find the later line where its id is made not entrant. What did the program do just before?",
     "Run the Kotlin twin and compare the `(N bytes)` sizes. Add `-Pargs=all` to either one to see every line the JVM prints."
    ],
    "code": demo("Hot"),
    "expect": "`longLoop` gets `%` lines at tier 3 and tier 4 before the program prints 1251976370825152. `Paragraph::millis` reaches tier 4 (through tier 2 on JDK 25, through tier 3 on JDK 21). `readingMillis` reaches tier 4, then that compile is made not entrant right after the headings and quotes arrive, and a new tier 4 compile with a higher id follows. On JDK 25 each retirement carries its reason. The Kotlin twin compiles to almost the same bytecode: 27 bytes for `longLoop` and 43 for `readingMillis`, against 42 in Java, and its OSR entry is `@ 14` instead of `@ 11`."
   }
  },
  {
   "h": "OSR: compiling a loop while it is still running",
   "body": S2,
   "try": {
    "title": "Find the loop and the trap",
    "minutes": 4,
    "steps": [
     "Run the `Hot` demo once, so Gradle compiles it.",
     "From `labs/`, print the bytecode of `longLoop` with the first command below. Find index 4 and index 7.",
     "Run the second command. It starts `Hot` directly with the deoptimization log on. Find the `longLoop` line and the `readingMillis` lines."
    ],
    "code": {"lang": "bash", "title": "terminal", "src": "javap -c -p -cp performance/build/classes/java/demo workbench.performance.l01.Hot | grep -A 20 'long longLoop'\n\njava -Xlog:deoptimization=debug -cp performance/build/classes/java/demo workbench.performance.l01.Hot child", "run": ""},
    "expect": "Index 4 is `iload_2`, the top of the loop, and index 7 is `if_icmpge 25`, the exit test. The log has one line for `longLoop` with `trap_bci=7 osr_bci=4 unstable_if`, printed when the loop ends, and several lines for `readingMillis` with `trap_bci=27 class_check maybe_recompile`. Bytecode 27 in `readingMillis` is the `millis()` call. That second kind of trap is where lesson 2 begins."
   }
  },
  {
   "h": "The code cache, and why every new JVM starts cold",
   "body": S3,
   "try": {
    "title": "Look inside the code cache",
    "minutes": 3,
    "steps": [
     "Run the first command from `labs/`. It starts a JVM that does nothing and prints the code cache as it exits.",
     "Run the second one, which prints the code cache after `Hot` has run. Compare the `used=` numbers.",
     "Optional: start any demo that runs for a while, find its pid with `jcmd -l`, and run `jcmd <pid> Compiler.codecache` against it."
    ],
    "code": {"lang": "bash", "title": "terminal", "src": "java -XX:+PrintCodeCache -version\n\njava -XX:+PrintCodeCache -cp performance/build/classes/java/demo workbench.performance.l01.Hot child", "run": ""},
    "expect": "Three parts of about 117 MB, 117 MB and 5.6 MB, 240 MB in all. With `-version`, only a few KB of compiled methods are used. After `Hot`, the two method parts hold more (10 KB and 18 KB on the course machine), because `Hot` and the JDK methods it called were compiled. That's still a tiny part of 240 MB."
   },
   "refs": [
    {"title": "JEP 515: Ahead-of-Time Method Profiling", "url": "https://openjdk.org/jeps/515", "kind": "read"}
   ]
  }
 ],
 "compare": {
  "title": "The JIT sees bytecode, not Java or Kotlin",
  "java": {"title": "Hot.java", "src": "static long readingMillis(Block[] blocks) {\n    long sum = 0;\n    for (Block b : blocks) sum += b.millis();\n    return sum;\n}\n// PrintCompilation: Hot::readingMillis (42 bytes)\n// OSR entry: @ 11"},
  "kotlin": {"title": "Hot.kt", "src": "fun readingMillis(blocks: Array<KBlock>): Long {\n    var sum = 0L\n    for (b in blocks) sum += b.millis()\n    return sum\n}\n// PrintCompilation: HotKt::readingMillis (43 bytes)\n// OSR entry: @ 14"},
  "note": "Both loops compile to an indexed loop over the array with one `invokeinterface`, a call through an interface that is resolved at run time. So HotSpot treats them the same way: same tiers, same OSR, same throw-away when headings and quotes arrive. The only visible differences are one byte of bytecode and a different loop index. A Kotlin top-level function lives in a class named after its file (`HotKt`), and that's the name to search for in logs. Where Kotlin really changes what the JIT sees is in `inline` functions, which come up in lesson 2."
 },
 "worked": {
  "title": "Follow one method through a PrintCompilation log",
  "steps": [
   {"say": "Start by filtering. The JVM compiles hundreds of its own methods, so keep only the lines for your package and the program's own output.", "code": "java -XX:+PrintCompilation -cp performance/build/classes/java/demo workbench.performance.l01.Hot child | grep 'workbench.performance'", "lang": "bash"},
   {"say": "Find the OSR lines first. A `%` means a loop got hot enough to compile while it ran. Here `readingMillis` got C1 OSR code (tier 3) and then C2 OSR code (tier 4) within a few milliseconds, and the C1 version retired.", "code": "254   21 %     3       workbench.performance.l01.Hot::readingMillis @ 11 (42 bytes)\n257   23 %     4       workbench.performance.l01.Hot::readingMillis @ 11 (42 bytes)\n260   21 %     3       workbench.performance.l01.Hot::readingMillis @ 11 (42 bytes)   made not entrant: OSR invalidation of lower level", "lang": "text"},
   {"say": "Follow one compile id from birth to retirement. Id 24 is the first normal C2 version of `readingMillis`. It's made not entrant at 309 ms, a tier 3 compile follows at once, and tier 4 comes back with id 35. Ask what the program did just before 309 ms: that's when the headings and quotes appeared.", "code": "271   24       4       workbench.performance.l01.Hot::readingMillis (42 bytes)\n309   24       4       workbench.performance.l01.Hot::readingMillis (42 bytes)   made not entrant: uncommon trap\n314   33       3       workbench.performance.l01.Hot::readingMillis (42 bytes)\n327   35       4       workbench.performance.l01.Hot::readingMillis (42 bytes)", "lang": "text"},
   {"say": "Self-check: which compile of `readingMillis` is running at the end of the log? Answer: id 35, the last tier 4 compile without a `%` whose id never shows up again with `made not entrant`. That's the rule the lab asks you to code.", "code": "", "lang": ""},
   {"say": "On JDK 25, read the reason. `not used` and `OSR invalidation of lower level` are routine. `uncommon trap` on a tier 4 line means C2 made a bet and lost. A few of those while a program warms up are normal. The same method trapping again and again, hours after start, is worth a closer look.", "code": "309   24       4       workbench.performance.l01.Hot::readingMillis (42 bytes)   made not entrant: uncommon trap", "lang": "text"}
  ]
 },
 "lab": {
  "title": "Parse PrintCompilation output",
  "minutes": 14,
  "files": [f"{lab}/main/{K}/PrintCompilation.kt"],
  "run": "./gradlew :performance:test --tests 'workbench.performance.l01.*'",
  "steps": [
   "Run the tests once. All eight fail with `NotImplementedError`. The fixtures in `PrintCompilationTest` are real JDK 21 and JDK 25 output from `Hot`, trimmed to the interesting lines.",
   "Write `parse(line)`. Return `null` when the line isn't a compile line. Otherwise fill every field of `CompileEvent`: time, id, the five flag characters, tier, method, OSR index, bytes and the message.",
   "Make it handle `(native)` instead of `(N bytes)`, a missing tier column (`-XX:-TieredCompilation`), and both `made not entrant` and `made not entrant: <reason>`.",
   "Write `parseAll`, then `deoptimizedFromC2` (tier 4 lines that were made not entrant) and `runningInC2` (normal tier 4 compiles whose id never shows up as made not entrant).",
   "Run the tests until all eight pass. Then run the `Hot` demo with `-Pargs=all`, paste a few lines into a test of your own, and check your parser on them."
  ],
  "hints": [
   "The layout is fixed: time, spaces, id, one space, exactly five flag characters, one space, then the tier digit and a space only when tiered compilation is on. A regex such as `^\\s*(\\d+)\\s+(\\d+) ([%s!bn ]{5}) (?:([0-4-]) )?\\s*(\\S+)...` gets you most of the way.",
   "Kotlin's `MatchResult.destructured` gives you the groups as strings. `toIntOrNull()` turns an empty optional group into `null` for free.",
   "For the reason, take what follows `made not entrant`, drop a leading colon and spaces, and use `null` when nothing is left.",
   "`runningInC2` needs two passes: first collect every compile id that was made not entrant, then keep the tier 4, non-OSR lines whose id isn't in that set."
  ],
  "done_when": "All eight tests in `PrintCompilationTest` pass."
 },
 "drill": {
  "title": "Label a PrintCompilation line from memory",
  "minutes": 4,
  "prompt": "Close this page. On paper, label every part of this line, then write one sentence for each of tiers 0 to 4. Then check the answer.\n\n```text\n56   13 %     4       Hot::longLoop @ 4 (27 bytes)\n```",
  "answer": {"lang": "text", "src": "56            ms since the JVM started\n13            compile id (the same id appears again if this code is retired)\n%             OSR compile (other flags: s synchronized, ! exception handler, b blocking, n native)\n4             tier 4 = C2\nHot::longLoop class and method\n@ 4           OSR entry: bytecode index 4, the top of the loop\n(27 bytes)    size of the method's bytecode, not machine code\n\ntier 0  interpreter, counts calls and back-edges\ntier 1  C1 without profiling, for trivial methods\ntier 2  C1 with counters only, used in some cases such as a C2 backlog\ntier 3  C1 with full profiling (the usual step before C2)\ntier 4  C2, optimized with the tier 3 profile"}
 },
 "recap": [
  "HotSpot runs every method in the interpreter first, then compiles the busy ones: C1 with profiling (tier 3) after about 200 calls, C2 (tier 4) after about 5,000 more. The thresholds are the same from JDK 21 to 27 and rise when the compile queues are long.",
  "A `-XX:+PrintCompilation` line reads: time, compile id, flags (`%` OSR, `s`, `!`, `b`, `n`), tier, method, `@ bci` for OSR, bytecode size, then an optional message.",
  "OSR compiles a loop while it runs and enters it at the top of the loop, so a method called once can still end up in C2.",
  "`made not entrant` means the JVM retired that compiled code. JDK 25 adds a reason: `not used` and `OSR invalidation of lower level` are routine, `uncommon trap` means a C2 bet failed.",
  "Compiled code lives in a 240 MB code cache split into three parts. Every new JVM starts cold, so measure after warm-up; on JDK 25 an AOT cache can carry profiles from a training run.",
  "The limit: PrintCompilation tells you when and at which tier, not why C2 chose what it did. That takes the inlining and deoptimization logs of lesson 2."
 ],
 "closing": "We started with a new cook who reads every recipe card on day one and knows the house favourites by heart a week later. The JVM learns the same way: the interpreter reads bytecode, C1 writes the cheat sheet and takes notes, C2 practises with shortcuts, and OSR switches technique in the middle of the pot. Every restart is day one again.\n\nNow find a test or script of yours that wraps one call in `System.nanoTime()` or `System.currentTimeMillis()` and prints the difference. That number measured the first day.\n\nNext, we'll open C2's book of shortcuts: which methods does it copy into their callers, and what happens when one of its bets, an uncommon trap, finally goes off?",
 "quiz": [
  {"q": "The report service's `rebuildIndex()` is called once, and it loops over 3 million lines. What does `-XX:+PrintCompilation` most likely show for it?",
   "options": ["Nothing, since it is called only once", "One tier 4 line after 10,000 calls", "Lines with `%` and `@ <bci>`: OSR compiles of its loop at tier 3, then tier 4", "A single tier 1 line, because it is called rarely"],
   "answer": 2,
   "why": "The JVM counts loop back-edges as well as calls. After about 60,000 back-edges it compiles an OSR version of the method at tier 3, and C2 follows at tier 4. \"Called once\" only rules out the normal compiles that calls trigger."},
  {"q": "On JDK 25, which line says that C2 code was thrown away because one of its assumptions failed?",
   "options": ["`252   19       2       Hot$Paragraph::millis (9 bytes)   made not entrant: not used`", "`67   11 %     3       Hot::longLoop @ 4 (27 bytes)   made not entrant: OSR invalidation of lower level`", "`271   24       4       Hot::readingMillis (42 bytes)`", "`309   24       4       Hot::readingMillis (42 bytes)   made not entrant: uncommon trap`"],
   "answer": 3,
   "why": "Tier 4 plus `uncommon trap` means C2 hit a case it had compiled as \"never happens\" and handed the call back to the interpreter. `not used` and `OSR invalidation of lower level` are housekeeping: newer or better code replaced older code. The third line is a compile, not a retirement."},
  {"q": "What does `(42 bytes)` at the end of a PrintCompilation line measure?",
   "options": ["The size of the machine code C2 produced", "The size of the method's bytecode", "The stack frame size of the method", "How much memory one call allocates"],
   "answer": 1,
   "why": "The JVM prints the length of the method's bytecode. Machine code is usually much larger. The number matters because the inlining limits in lesson 2 are measured in bytecode bytes."},
  {"q": "A teammate's warm-up script calls the report endpoint exactly 10,000 times \"because HotSpot compiles after 10,000 calls\". On JDK 25 with default flags, what's wrong with that reasoning?",
   "options": ["Tiered compilation uses about 200 calls for tier 3 and about 5,000 more for tier 4, loops count too, and the thresholds rise when compile queues are long, so no fixed call count guarantees C2", "Nothing, 10,000 is the default threshold", "HotSpot only compiles methods marked `final`", "C2 has been off by default since JDK 21"],
   "answer": 0,
   "why": "10,000 is `CompileThreshold`, which is used only with `-XX:-TieredCompilation`. With tiered compilation the triggers are different, and they grow with compiler load. Warm up until the timings settle, not to a magic number."},
  {"q": "In the memory model track, a loop on a plain `stop` field spun forever, but it stopped when the program ran with `-Xint`. In this lesson's terms, why?",
   "options": ["`-Xint` makes every field volatile", "`-Xint` turns off the CPU caches", "The interpreter re-reads the field on every lap. The hang appears only once C2 (often through OSR) compiles the loop and keeps the value in a register", "The interpreter runs every thread on one core"],
   "answer": 2,
   "why": "Under `-Xint` the method never leaves tier 0, and the interpreter loads the field each time. The JIT is allowed to read a non-volatile field once and lift it out of the loop. A busy loop reaches C2 through OSR even when its method is called once, which is exactly when the hang starts.",
   "from": "jmm-01"}
 ],
 "flashcards": [
  {"front": "Which compiler runs a method at tier 3, and what does it add?", "back": "C1, with full profiling: call and loop counters plus branch counts and the types seen at each call. C2 uses that profile."},
  {"front": "Which compiler runs a method at tier 4?", "back": "C2, compiling with the profile that tier 3 collected."},
  {"front": "In a PrintCompilation line, what do `%` and `@ 4` mean?", "back": "`%` marks an OSR compile. `@ 4` is the bytecode index of the loop where the compiled code is entered."},
  {"front": "What is the number in `(27 bytes)` on a PrintCompilation line?", "back": "The method's bytecode size. Inlining limits are measured in these bytes."},
  {"front": "Roughly when does a method reach tier 3 and tier 4 on JDK 21 to 27?", "back": "About 200 calls for tier 3, then about 5,000 more for tier 4. Loop laps count too, and the bar rises when compile queues are long."},
  {"front": "What does `made not entrant` mean?", "back": "The JVM stopped using that compiled version; new calls won't enter it. JDK 25 prints the reason, such as `not used` or `uncommon trap`."},
  {"front": "How big is the code cache by default, and how do you inspect it on a running JVM?", "back": "240 MB reserved with tiered compilation, in three parts. `jcmd <pid> Compiler.codecache`."}
 ],
 "terms": [
  {"term": "Bytecode", "plain": "The JVM's instructions, written by javac or kotlinc into `.class` files."},
  {"term": "Interpreter", "plain": "Tier 0. Runs bytecode one instruction at a time and counts calls and loops."},
  {"term": "C1", "plain": "The fast, lightly optimizing JIT compiler. At tier 3 it also collects the profile."},
  {"term": "C2", "plain": "The slow, heavily optimizing JIT compiler (tier 4). It uses the profile to make bets."},
  {"term": "Tiered compilation", "plain": "Using the interpreter, C1 and C2 one after another, on by default."},
  {"term": "OSR (on-stack replacement)", "plain": "Compiling a running loop and moving the live call into the new code mid-loop."},
  {"term": "Code cache", "plain": "Memory outside the heap that holds compiled code, 240 MB reserved by default."},
  {"term": "Made not entrant", "plain": "Compiled code the JVM has retired: new calls no longer enter it."}
 ],
 "explain_back": {
  "prompt": "A teammate asks why the first test run against a freshly started report service gave much worse numbers than a second run five minutes later, with no code change. Explain it in your own words, using the tiers.",
  "answer": "A new JVM runs every method in the interpreter first. As methods get called and their loops run, the JVM compiles them, first with C1 while it collects a profile, then with C2 using that profile. That takes thousands of calls per busy method, and the compiler threads use the same cores as the threads serving requests while they work. During the first test run, most of the request path was still interpreted or in C1 code. Five minutes later the busy paths were running C2 code. Nothing carries over from one JVM to the next, so every restart goes through this again. Warm the service up before it takes real requests, try the JDK 25 AOT cache, and only compare measurements taken after warm-up."
 },
 "deeper": {
  "minutes": 10,
  "body": "PrintCompilation is the summary. For the full story, run with `-XX:+UnlockDiagnosticVMOptions -XX:+LogCompilation`, which writes an XML log of every compile decision, and open it in JITWatch, a log viewer for HotSpot's JIT. Its wiki says to add `-Xlog:class+load=info` so it can build its class model. To see the machine code too, add `-XX:+PrintAssembly`, which needs the hsdis disassembler library.\n\nA few `jcmd` commands help on a running JVM: `Compiler.queue` shows what's waiting to be compiled, `Compiler.codelist` lists the compiled methods, and `Compiler.codecache` shows the parts of the code cache. The JVM picks the number of compiler threads from the CPU count: `-XX:+PrintFlagsFinal` showed `CICompilerCount = 3` on the 4-core course machine.\n\n`-XX:TieredStopAtLevel=1` (C1 only) compiles less and peaks lower on most real code. The HotSpot source describes it as mostly for testing, so keep it out of production.\n\nJDK 25 added two JEPs aimed at warm-up, both used in the last section. JEP 514 makes the AOT cache easier to create, with `-XX:AOTCacheOutput=app.aot` on a training run and `-XX:AOTCache=app.aot` on later runs. JEP 515 stores method profiles in that cache, so a new JVM can start compiling busy methods with C2 sooner. Compiling the code itself ahead of time is a separate, later step: JEP 544 is in the mainline for JDK 28, which isn't released yet. The startup track goes through all of this.\n\nOne more thing you may read about: \"made zombie\". Older JDKs printed that when retired code was finally freed. JDK 25 doesn't print it, so treat articles that show it as describing an older JVM."
 },
 "sources": [
  {"title": "compilationPolicy.hpp: the tiered policy explained in HotSpot's own comments (JDK 25)", "url": "https://github.com/openjdk/jdk/blob/jdk-25-ga/src/hotspot/share/compiler/compilationPolicy.hpp"},
  {"title": "compiler_globals.hpp: tier thresholds and their defaults (JDK 25)", "url": "https://github.com/openjdk/jdk/blob/jdk-25-ga/src/hotspot/share/compiler/compiler_globals.hpp"},
  {"title": "compileTask.cpp: the code that prints each PrintCompilation line (JDK 25)", "url": "https://github.com/openjdk/jdk/blob/jdk-25-ga/src/hotspot/share/compiler/compileTask.cpp"},
  {"title": "The java command, JDK 25 man page", "url": "https://docs.oracle.com/en/java/javase/25/docs/specs/man/java.html"},
  {"title": "JITWatch, a log analyser and visualiser for the HotSpot JIT", "url": "https://github.com/AdoptOpenJDK/jitwatch"}
 ]
}
out = ROOT / "content/lessons/perf-01.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
