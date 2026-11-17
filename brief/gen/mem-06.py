import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/memory/src"
P = "java/workbench/memory/l06"
K = "kotlin/workbench/memory/l06"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :memory:demo -Pmain=workbench.memory.l06."


def demo(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": DEMO + name, "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
                    "run": DEMO + name + "Kt", "file": f"{lab}/demo/{K}/{name}.kt"}}


FIGURE = """<svg viewBox="0 0 680 250" role="img" aria-label="A container with a 1 GiB memory limit drawn as a plot with a fence. With -Xmx1g the heap alone fills the plot and the memory outside the heap sticks out past the fence, so the kernel ends the process. With MaxRAMPercentage=75 the heap, the memory outside it and some headroom all fit inside the fence">
<text class="t t-m" x="320" y="24" text-anchor="middle">one container with a 1 GiB memory limit</text>
<line class="ln-bad" x1="520" y1="36" x2="520" y2="214"/>
<text class="t-s t-bad" x="520" y="232" text-anchor="middle">the fence: 1 GiB</text>
<text class="t" x="60" y="77" text-anchor="middle">-Xmx1g</text>
<rect class="box-a" x="120" y="55" width="400" height="36" rx="8"/>
<text class="t-s" x="320" y="77" text-anchor="middle">heap: 1,024 MB</text>
<rect class="box-bad" x="520" y="55" width="80" height="36" rx="8"/>
<text class="t-s" x="560" y="77" text-anchor="middle">+ the rest</text>
<text class="t-s t-bad" x="320" y="112" text-anchor="middle">the rest of the process lands past the fence: the kernel ends it</text>
<text class="t" x="60" y="162" text-anchor="middle">75%</text>
<rect class="box-a" x="120" y="140" width="300" height="36" rx="8"/>
<text class="t-s" x="270" y="162" text-anchor="middle">heap: 768 MB</text>
<rect class="box-ok" x="420" y="140" width="66" height="36" rx="8"/>
<text class="t-s" x="453" y="162" text-anchor="middle">the rest</text>
<rect class="box-dim" x="486" y="140" width="34" height="36" rx="8"/>
<text class="t-s" x="320" y="198" text-anchor="middle">-XX:MaxRAMPercentage=75: heap, the rest and headroom fit</text>
</svg>"""

OPENING = """Every cleaning crew keeps a logbook. After each round, someone writes one line: when, what kind of round and why, how full the floor was before and after, and how long the workers waited. After a bad afternoon, that logbook is how you find out what happened.

The JVM, the program that runs your Java and Kotlin, keeps the same logbook for its garbage collector, and the last lesson read a few entries; this one reads it properly. Then it moves the warehouse onto a rented plot: a container, a fenced-off part of a shared machine with a fixed memory limit.

The surprise is at the fence. A program started with `-Xmx`, the largest heap it may use, equal to its container's memory limit looks as if it fits. It runs for hours, then vanishes, and its own log doesn't say a word. The trap is believing that `-Xmx` is the size of the program.

In this lesson, we'll read GC log lines, turn a log into a few numbers, watch the JVM size its heap from a limit, and see why the whole building must fit the plot. Before we start, make a guess, and keep it in mind."""

S1 = """One flag makes the garbage collector (GC), the part of the JVM that frees objects nothing uses any more, write a line for every collection. Since JDK 9 the flag is `-Xlog:gc`, part of the JVM's unified logging system (older guides show `-XX:+PrintGCDetails`, which JDK 9 replaced). Here's the first line from G1, the default collector, on JDK 25, running the thumbnail service's stand-in load from lesson 4:

```text
[0.440s][info][gc] GC(0) Pause Young (Normal) (G1 Evacuation Pause) 28M->2M(214M) 8.692ms
```

Read it left to right. `[0.440s]` is the time since the JVM started, `[info]` the log level and `[gc]` the tag, the topic of the line. `GC(0)` numbers the collection; a concurrent cycle, work the collector does while the program runs, gets a number of its own, and the pauses inside it reuse that number. `Pause Young` is the event. `(Normal)` says it's a young-only pause; `Concurrent Start`, `Prepare Mixed` and `Mixed` are the other kinds from lesson 4. `(G1 Evacuation Pause)` is the cause: eden, the area for new objects, was full. You'll also see `G1 Humongous Allocation` and `System.gc()` there.

Then come the numbers. `28M->2M(214M)` is the heap (the memory where objects live) in use before the pause, the heap in use after it, and the committed heap, the memory the operating system has really handed over. Last, `8.692ms` is how long every application thread, every path of work in the program, was stopped. That's the line a person waiting on a request feels.

One label changed between versions. When G1 runs out of free regions (lesson 4's equal blocks of heap) to copy into, JDK 21 writes `(Evacuation Failure)`, and JDK 25 adds the reason, as in `(Evacuation Failure: Allocation)`. Search for `Evacuation Failure` and you'll find both.

`-Xlog:gc*`, with the star, turns on every GC tag: phases, region counts, metaspace and CPU time. That's ten to fifteen lines per pause, the detail lessons 4 and 5 used.

For a service, write the log to rotating files with wall-clock times, so it survives a restart and can't fill the disk:

```text
-Xlog:gc*:file=/var/log/app/gc.log:time,uptime,level,tags:filecount=5,filesize=20m
```

The colons separate the parts: what to log, where to write it, the decorations at the start of each line (`time` adds the date and time of day), and the rotation, here at most 5 files of 20 MB. A line then looks like this, from the demo below:

```text
[2026-11-17T07:31:28.846+0000][1.214s][info][gc          ] GC(14) Pause Young (Normal) (G1 Evacuation Pause) (Evacuation Failure: Allocation) 234M->101M(256M) 15.414ms
```

Here a paper logbook and the JVM's part ways. When the current `gc.log` is full, the JVM renames it to a numbered file such as `gc.log.0` and starts a fresh one, and with `filecount=5` the oldest file is thrown away. Leave the log on in production. It costs a few lines per collection, and in an incident it's the first thing you'll want.

A logbook of three hundred lines is hard to judge by eye, though."""

S2 = """A few numbers say most of what a GC log knows:

- the number of pauses and their total time; divided by the elapsed time, that's the share of time your threads were stopped;
- the longest pause, which is what your slowest requests feel;
- the number of full GCs (collections of the whole heap, with every thread stopped) and evacuation failures, which should be zero in a healthy G1 program;
- the heap after the last full GC, which is the **live set** at that moment, the objects really still in use, and the number you size a heap from;
- the trend of the after-values of young pauses: a floor that keeps rising means the live set is growing.

Computing them has two traps. The first is that not every line with a duration is a pause. `Concurrent Mark Cycle 25.055ms` ran beside the application. G1's `Evacuate Collection Set: 21.05ms` is one phase inside a pause the log already counted on its `Pause Young` line. ZGC's `Minor Collection ... 0.071s` from lesson 5 is a whole concurrent collection. One rule works for every HotSpot collector: **a pause line has `Pause` right after `GC(id)` and ends with a duration in `ms`.** ZGC puts `y:`, `Y:` or `O:` between the two.

The second trap is `(System.gc())`, which has parentheses inside its parentheses and breaks the obvious regular expression. The lab builds a parser with that rule, and tests it on lines copied from real runs: all five collectors on JDK 21, and G1 on JDK 25.

Check yourself on a stretch of the demo's JDK 25 log, with the decorations cut off. It's a G1 cycle like the one in lesson 4:

```text
GC(16) Pause Young (Concurrent Start) (G1 Humongous Allocation) 205M->158M(256M) 8.143ms
GC(17) Concurrent Mark Cycle
GC(17) Pause Remark 185M->185M(256M) 0.447ms
GC(17) Pause Cleanup 185M->185M(256M) 0.085ms
GC(17) Concurrent Mark Cycle 25.055ms
GC(18) Pause Young (Prepare Mixed) (G1 Evacuation Pause) (Evacuation Failure: Allocation) 248M->142M(256M) 3.544ms
GC(19) Pause Young (Mixed) (G1 Evacuation Pause) (Evacuation Failure: Allocation) 248M->211M(256M) 14.287ms
```

How many pauses are there, how long did they take together, and is this heap healthy? (Five pauses: Concurrent Start, Remark, Cleanup, Prepare Mixed and Mixed, 26.5 ms in all. The two `Concurrent Mark Cycle` lines are not pauses. Two evacuation failures in a row say the heap is too small for what's live. A full GC a little later in the same log, `Pause Full (G1 Compaction Pause) 224M->84M(256M)`, puts the live set at 84 MB.)

The log tells you how full the floor gets. How big the JVM makes the floor in the first place depends on where it runs."""

S3 = """A **container** is a way to run a program in a fenced-off part of a shared machine. On Linux, the kernel (the core of the operating system) enforces the fence with a feature called cgroups: a memory limit and a CPU limit for a group of processes. In the warehouse, the container is a rented plot on a shared site. The lease says how much ground the building may cover.

The JVM reads that lease. `UseContainerSupport` is on by default in every JDK from 21 to 27, so the JVM sizes itself from the container's limits, not the whole machine's. Without heap flags, the max heap is 25% of the memory limit (`MaxRAMPercentage`, default 25). A container with a 1 GiB limit gets a 256 MB heap. That's a cautious default: three quarters of the plot stays free unless the program uses it outside the heap. Very small limits get a bigger share: with a 256 MB limit, JDK 25 picked a 126 MB heap, because `MinRAMPercentage` (50) applies there.

`-XX:MaxRAMPercentage` changes the share. With 75, the same container gets 768 MB. Prefer it over a fixed `-Xmx`, because the heap then follows the limit when someone gives the container more memory. Watch the top end: in a 64 GB container, 75% is 48 GB, and lesson 1's compressed references switch off, so every reference grows from 4 bytes to 8. `-XX:InitialRAMPercentage` sets the starting heap. It was 1.5625% on JDK 21 to 25; per the JDK source, it is 0 on JDK 26, where the JVM starts from a small minimum and grows.

To see what the JVM detected, run `java -XshowSettings:system -version` inside the container. On the machine behind this lesson, JDK 25 printed `Provider: cgroupv1`, `Effective CPU Count: 4` and `Memory Limit: 13.35G`. `-Xlog:os+container=debug` shows the detection step by step, which helps when the numbers look wrong.

The demo can't create a container, so it uses `-XX:MaxRAM`, which tells the JVM how much memory to plan for, as a stand-in for a limit. That works on JDK 21 to 25. JDK 26 deprecated `MaxRAM`, and per the JDK source, JDK 27 removed it; there, try the same flags in a real container.

Whatever share you pick, though, the heap is only part of the building."""

S4 = """Here's the setting that looks right and fails: a container with a 1 GiB limit and `-Xmx1g`. Lesson 1 already showed why it can't work. The heap is the storage floor, and the building also has desks (thread stacks), a back room with the plans (metaspace), the code cache, the crew's own records, and the yard out back (direct buffers, memory a program asks for outside the heap). In the demo below, a JDK 25 process with a 256 MB heap, one 64 MiB direct buffer and 56 threads had 379 MB in RAM. Scale that to `-Xmx1g`, and the process needs well over 1 GiB once its heap fills.

The failure doesn't look like a Java error. When a process goes over its cgroup limit, the kernel's **OOM killer**, its out-of-memory guard, ends it at once with SIGKILL, the signal no program can catch. The exit code is 137 (128 plus signal number 9). There's no `OutOfMemoryError`, no heap dump and nothing in the program's log. The kernel doesn't leave a note.

The program can run fine for hours first, because Linux counts only the pages a process has touched, its resident memory, and the heap touches its pages bit by bit as it fills. The demo uses `-XX:+AlwaysPreTouch` to touch the whole heap at startup. Without it, the same process showed 118 MB resident instead of 379.

So budget the whole building: the heap, plus direct buffers, plus metaspace and code cache, plus a stack for each thread, plus the GC's bookkeeping, plus headroom. **`-Xmx` sizes the storage floor, not the building. Leave room for the rest.**

Direct buffers need a cap of their own. Unless you set `-XX:MaxDirectMemorySize`, the JDK allows direct buffers up to the max heap size, so a program could in theory ask for twice its heap. Network libraries often keep socket data in direct buffers.

My starting point for a service is `-XX:MaxRAMPercentage` between 50 and 75, a `-XX:MaxDirectMemorySize` that fits what the program's I/O needs, and a bounded number of threads. Then measure under load with Native Memory Tracking, which lesson 7 covers, and adjust.

The limit of today's tools shows here too. The GC log sees only the heap, and the kernel's verdict comes with no explanation. To see the rest of the building, you need the JVM's own inventory of it."""

ASIDE = {
 "title": "What does my container platform show when this happens?",
 "body": "The kernel's kill is reported by whatever started the container. Docker, a common tool for running containers, shows exit code 137, and `docker inspect` reports `\"OOMKilled\": true` for that container. Kubernetes, a system that runs many containers across a group of machines, reports the reason `OOMKilled` with exit code 137 and starts the container again. In both cases, the program's own log simply stops."
}

L = {
 "id": "mem-06",
 "title": "Reading GC logs and sizing the heap in containers",
 "minutes": 37,
 "goal": "By the end you can read a unified GC log line field by field, turn a log into pause numbers with a small parser, and size the heap of a program in a container so the kernel doesn't kill it.",
 "opening": OPENING,
 "warmup": {
  "q": "A service runs in a container with a 2 GiB memory limit and `-Xmx2g`. Under load it disappears, and the container's status shows exit code 137. What do you expect in the service's own log?",
  "options": ["A `java.lang.OutOfMemoryError: Java heap space`", "A heap dump, if `-XX:+HeapDumpOnOutOfMemoryError` is set", "Nothing about memory: the kernel ended the process from outside", "A `Pause Full` line followed by a JVM crash report"],
  "answer": 2,
  "why": "Exit code 137 is 128 plus signal 9, SIGKILL. The kernel's OOM killer ended the process because the whole process, heap plus everything outside it, went over the container's limit. The JVM never got a chance to throw anything, write a heap dump or log a line. A Java `OutOfMemoryError` only happens when the heap itself is full, inside the limit."
 },
 "sections": [
  {
   "h": "The crew's logbook: one line per collection with -Xlog:gc",
   "body": S1,
   "try": {
    "title": "Write a GC log the production way",
    "minutes": 4,
    "steps": [
     "Read `GcLogFileDemo`. It runs two seconds of the stand-in load from lesson 4 in a child JVM with a 256 MB heap, using the rotating-file setting from this section, at 40 KB per file so you can watch it rotate.",
     "Predict: will there be more than one file, and will the last young pause leave more or less heap behind than the first?",
     "Run it, then open the newest file, `labs/memory/build/gc-logs/gc.log`, and find a `Pause Young` line with its date and time."
    ],
    "code": demo("GcLogFileDemo"),
    "expect": "Two or three files: `gc.log.0` (and maybe `gc.log.1`), full at about 40 KB with the older lines, and `gc.log` with the newest. On JDK 25 the run behind this lesson found 2 `Pause Full` lines and 7 to 13 lines with `Evacuation Failure`, because this heap is too small for its cache on purpose. The first young pause goes `29M->2M` (`14M->1M` on JDK 21), and the last ones leave 120 to 245 MB behind: the floor rose as the cache filled. JDK 21 shows more evacuation failures, about 20. The counts change from run to run."
   },
   "refs": [
    {"title": "The java command, JDK 25 man page source: -Xlog", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/man/java.md", "kind": "docs"}
   ]
  },
  {
   "h": "From three hundred lines to five numbers: what to check first",
   "body": S2
  },
  {
   "h": "How the JVM sizes its heap from the container's memory limit",
   "body": S3,
   "figure": {"svg": FIGURE, "caption": "-Xmx equal to the limit leaves no room for the rest of the process. A percentage leaves room for it and for headroom."},
   "try": {
    "title": "Watch the heap follow the limit",
    "minutes": 3,
    "steps": [
     "Predict the max heap for limits of 1, 2 and 4 GiB, with defaults and with `-XX:MaxRAMPercentage=75`.",
     "Run `HeapSizingDemo` (JDK 21 to 25). Each line comes from a child JVM started with `-XX:MaxRAM` as the limit.",
     "If you have Docker, a common tool for running programs in containers, run `docker run --rm --memory=1g eclipse-temurin:25 java -XshowSettings:system -version` and find the memory limit it reports."
    ],
    "code": demo("HeapSizingDemo"),
    "expect": "256, 512 and 1,024 MB with defaults (25%), and 768, 1,536 and 3,072 MB with 75%, exactly as JDK 25 printed them for this lesson. In a container, `-XshowSettings:system` reports the limit you gave it, for example `Memory Limit: 1.00G`."
   },
   "refs": [
    {"title": "arguments.cpp at jdk-25-ga: heap sizing from available memory", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/runtime/arguments.cpp", "kind": "read"}
   ]
  },
  {
   "h": "When -Xmx equals the limit, the kernel ends the whole process",
   "body": S4,
   "aside": ASIDE,
   "try": {
    "title": "Compare the heap with the whole process",
    "minutes": 3,
    "steps": [
     "Read `FootprintDemo`. Its child JVM has `-Xmx256m -Xms256m -XX:+AlwaysPreTouch`, allocates a 64 MiB direct buffer and starts 50 threads. Then it prints what the JVM reports next to what Linux says is resident in RAM.",
     "Predict the resident number before you run it.",
     "Run it. Then remove `-XX:+AlwaysPreTouch` from the demo and run it again."
    ],
    "code": demo("FootprintDemo"),
    "expect": "On Linux with JDK 25: heap committed 256 MB, non-heap 8 to 16 MB, direct buffers 64 MB, 56 live threads, and about 379 MB resident, roughly 120 MB more than the heap. Without `AlwaysPreTouch` the resident number drops to about 118 MB, because most heap pages haven't been touched yet; a running service gets there anyway as its heap fills. On macOS or Windows the demo can't read the resident size and says so."
   }
  }
 ],
 "compare": {
  "title": "Print what memory the JVM thinks it has, at startup",
  "java": {"title": "MemoryBanner.java", "src": "var os = (com.sun.management.OperatingSystemMXBean) ManagementFactory.getOperatingSystemMXBean();\nSystem.out.printf(\"memory seen %d MB, CPUs %d, max heap %d MB%n\",\n        os.getTotalMemorySize() >> 20,\n        Runtime.getRuntime().availableProcessors(),\n        Runtime.getRuntime().maxMemory() >> 20);"},
  "kotlin": {"title": "MemoryBanner.kt", "src": "val os = ManagementFactory.getOperatingSystemMXBean() as com.sun.management.OperatingSystemMXBean\nprintln(\"memory seen %d MB, CPUs %d, max heap %d MB\".format(\n    os.totalMemorySize shr 20,\n    Runtime.getRuntime().availableProcessors(),\n    Runtime.getRuntime().maxMemory() shr 20))"},
  "note": "Both versions call the same JDK API. Kotlin reads `getTotalMemorySize()` as a property and writes `>>` as `shr`. The value of the line is in what it reports. On the machine behind this lesson, JDK 25 printed `memory seen 13674 MB, CPUs 4, max heap 3420 MB`: 13,674 MB is the container's 13.35 GiB limit, while the machine itself has about 16 GB, and the max heap is a quarter of the limit. `availableProcessors()` follows the CPU limit the same way. One line like this at startup tells you, wherever the program runs, whether the JVM sees the limit you think you gave it and what heap it chose."
 },
 "worked": {
  "title": "Size the thumbnail service's container from measurements",
  "steps": [
   {"say": "Start from numbers you measured, not from defaults. Suppose a realistic load test of the thumbnail service measured these: the heap left after its full GCs, from the GC log, and everything outside the heap, from Native Memory Tracking (lesson 7).",
    "code": "live set (heap after a full GC)       310 MB\noutside the heap, from NMT:\n  metaspace and class space            95 MB\n  code cache                           45 MB\n  thread stacks (140 threads)          35 MB\n  GC bookkeeping                       40 MB\n  direct buffers (network I/O)         70 MB",
    "lang": "text"},
   {"say": "1. Size the heap from the live set. G1 copies, so it needs free regions to copy into: give it two to three times the live set, about 768 MB.",
    "code": "", "lang": ""},
   {"say": "2. Add up the whole building, and leave headroom for what the test didn't hit: a busier hour, a burst of threads, a code cache that grows later in the day.",
    "code": "heap                    768 MB\noutside the heap        285 MB   (95 + 45 + 35 + 40 + 70)\nheadroom, about 15%     160 MB\n                       ------\nprocess               ~1,213 MB  -> ask for a 1.25 GiB (1,280 MB) limit\nheap share            768 / 1,280 = 60%",
    "lang": "text"},
   {"say": "3. Write flags that follow the limit, cap direct memory a little above what NMT showed, and keep the logbook. Then run the load test again and check two things: no `Pause Full` in the log, and resident memory well under the limit.",
    "code": "-XX:MaxRAMPercentage=60\n-XX:MaxDirectMemorySize=96m\n-Xlog:gc*:file=/var/log/app/gc.log:time,uptime,level,tags:filecount=5,filesize=20m",
    "lang": "text"}
  ]
 },
 "lab": {
  "title": "Parse real GC log lines into pause numbers",
  "minutes": 14,
  "files": [
   "labs/memory/src/main/kotlin/workbench/memory/l06/GcLog.kt",
   "labs/memory/src/main/kotlin/workbench/memory/l06/GcPause.kt"
  ],
  "run": "./gradlew :memory:test --tests 'workbench.memory.l06.*'",
  "steps": [
   "Run the tests. All eleven fail. Open `GcLogTest.kt`: every line in it comes from a real JDK 21 or JDK 25 run.",
   "Write `parsePause` with one regular expression: `GC(id)`, an optional `y: `, `Y: ` or `O: `, then `Pause` and the capitalized words after it, then zero or more `( ... )` labels, then an optional `14M->1M(256M)`, then the duration in `ms` at the end of the line.",
   "Pull the labels out of their group with a second, smaller regex, and turn missing heap numbers into `null`.",
   "Write `summarize`: the count, the total, the longest, the full GCs, the evacuation failures (any label that starts with `Evacuation Failure`, so JDK 25's `Evacuation Failure: Allocation` counts too), and the after-value of the last full GC.",
   "Run the tests until all eleven pass. Then point the parser at the log the first demo wrote, in `labs/memory/build/gc-logs`."
  ],
  "hints": [
   "A raw string (`\"\"\"...\"\"\"`) saves you from doubling every backslash in a Kotlin regex.",
   "A label is `\\((?:[^()]|\\(\\))*\\)`: an opening parenthesis, then any characters that are not parentheses or the exact pair `()`, then the closing one. That's what lets `(System.gc())` through.",
   "Anchor the duration with `ms$`, so ZGC's `0.071s` and the start lines without a duration don't match. Call `trimEnd()` on the line first.",
   "`m.destructured` gives you the groups as `val (id, kind, labels, before, after, committed, ms) = ...`. An empty optional group comes back as \"\", and `toIntOrNull()` turns that into `null`.",
   "For the evacuation failures, `p.labels.any { it.startsWith(\"Evacuation Failure\") }` matches both versions of the label."
  ],
  "done_when": "All 11 tests in `GcLogTest` pass."
 },
 "drill": {
  "title": "Read a line without the lesson",
  "minutes": 4,
  "prompt": "Close the page. For `[1.399s][info][gc          ] GC(19) Pause Young (Mixed) (G1 Evacuation Pause) (Evacuation Failure: Allocation) 248M->211M(256M) 14.287ms`, a line from this lesson's JDK 25 run with its date cut off, write down what each part means and whether this program is healthy. Then write the pause-line regex from memory.",
  "answer": {
   "lang": "java",
   "src": "// 1.399 s after start; collection 19; a mixed pause (young regions + some old ones); eden was full;\n// copying failed for lack of free regions; 248 MB used before, 211 after, 256 MB committed; 14 ms stopped.\n// Not healthy: an evacuation failure that leaves 211 of 256 MB in use means the live set barely fits.\nstatic final Pattern PAUSE = Pattern.compile(\n        \"GC\\\\((\\\\d+)\\\\) (?:[yYO]: )?(Pause(?: [A-Z]\\\\w*)+)\"   // id, ZGC prefix, kind\n        + \"((?: \\\\((?:[^()]|\\\\(\\\\))*\\\\))*)\"                     // labels, (System.gc()) included\n        + \"(?: (\\\\d+)M->(\\\\d+)M\\\\((\\\\d+)M\\\\))?\"                 // heap before -> after (committed)\n        + \" ([\\\\d.]+)ms$\");                                     // the pause",
   "alt": {
    "lang": "kotlin",
    "src": "// 1.399 s after start; collection 19; a mixed pause (young regions + some old ones); eden was full;\n// copying failed for lack of free regions; 248 MB used before, 211 after, 256 MB committed; 14 ms stopped.\n// Not healthy: an evacuation failure that leaves 211 of 256 MB in use means the live set barely fits.\nval PAUSE = Regex(\n    \"\"\"GC\\((\\d+)\\) (?:[yYO]: )?(Pause(?: [A-Z]\\w*)+)\"\"\" +     // id, ZGC prefix, kind\n    \"\"\"((?: \\((?:[^()]|\\(\\))*\\))*)\"\"\" +                         // labels, (System.gc()) included\n    \"\"\"(?: (\\d+)M->(\\d+)M\\((\\d+)M\\))?\"\"\" +                       // heap before -> after (committed)\n    \"\"\" ([\\d.]+)ms$\"\"\"                                           // the pause\n)"
   }
  }
 },
 "recap": [
  "`-Xlog:gc` prints one line per collection: uptime, level, tag, `GC(id)`, the event and its cause, heap before -> after (committed), and the pause length. `-Xlog:gc*` adds the details, and JDK 25 writes `(Evacuation Failure: Allocation)` where JDK 21 wrote `(Evacuation Failure)`.",
  "In production, log to rotating files with wall-clock times: `-Xlog:gc*:file=gc.log:time,uptime,level,tags:filecount=5,filesize=20m`.",
  "A pause line has `Pause` right after `GC(id)` and ends in `ms`. Concurrent phases, G1's phase timings and ZGC's `Collection` lines are not pauses. Check full GCs, evacuation failures (or ZGC allocation stalls), the longest pause, and the floor of the young pauses' after-values.",
  "In a container the max heap defaults to 25% of the memory limit. Size it with `-XX:MaxRAMPercentage`, usually 50 to 75, never 100, and cap direct memory with `-XX:MaxDirectMemorySize`.",
  "Heap plus everything outside it over the limit means a kernel OOM kill: exit code 137, no `OutOfMemoryError`, no heap dump, nothing in the log.",
  "The limit of today's tools: the GC log sees only the heap, and the kernel's kill explains nothing. Measuring the rest of the process takes Native Memory Tracking."
 ],
 "closing": """We started with a crew's logbook and a warehouse on a rented plot. The GC log tells you how full the floor gets and how long the workers wait. The container's limit is the fence around the whole building, and the heap must leave room for everything else inside it.

Now open the start-up command of a program you run in a container. Look for `-Xmx` or `MaxRAMPercentage`, and for `-Xlog:gc`. If neither is there, the heap is a quarter of the limit, and nobody keeps the logbook.

Next, we'll hunt for boxes that should have gone. When the floor keeps filling, who still holds a note to them, and what if the growth is in the yard out back?""",
 "quiz": [
  {
   "q": "Which of these log lines is a stop-the-world pause?",
   "options": [
    "`GC(17) Concurrent Mark Cycle 25.055ms`",
    "`GC(17) Pause Remark 185M->185M(256M) 0.447ms`",
    "`GC(3) Minor Collection (Allocation Rate) 852M(83%)->176M(17%) 0.071s`",
    "`GC(2)   Evacuate Collection Set: 21.05ms`"
   ],
   "answer": 1,
   "why": "Remark is one of the two short pauses that finish G1's concurrent marking. The mark cycle itself ran beside the application. ZGC's `Minor Collection` time is the whole concurrent collection. `Evacuate Collection Set` is a phase inside a young pause, whose own `Pause Young` line already counts it."
  },
  {
   "q": "A JDK 25 program runs in a container with a 2 GiB memory limit and no heap flags. What max heap does the JVM pick?",
   "options": ["2 GB", "1.5 GB", "1 GB", "512 MB"],
   "answer": 3,
   "why": "With container support on, the JVM bases the heap on the memory limit and takes `MaxRAMPercentage`, 25% by default: 512 MB. The demo showed the same arithmetic for 1, 2 and 4 GiB. To use more, set `-XX:MaxRAMPercentage`, for example 60 or 75."
  },
  {
   "q": "Over ten minutes, a service's young pauses end at `310M`, `355M`, `402M`, `447M` and `495M`, and a full GC finally goes `1490M->1210M(1536M)`. What is going on?",
   "options": [
    "The young generation is too small; make it bigger",
    "The live set keeps growing, which points to a leak or a cache with no limit",
    "G1's pause goal is too strict",
    "Nothing: G1 always lets the heap fill before collecting"
   ],
   "answer": 1,
   "why": "The after-values of young pauses are what survives, and their floor rises about 45 MB each time. Even a full GC frees only 280 MB of 1,490 MB: 1.2 GB is really live. A bigger heap only delays the moment it fills; lesson 7 finds what's holding the memory."
  },
  {
   "q": "A container has a 1 GiB limit. The service runs with `-XX:MaxRAMPercentage=75` and a network library that keeps socket data in direct buffers, with no other memory flags. Which flag should you add first?",
   "options": ["`-Xmx1g`", "`-XX:MaxDirectMemorySize`, with a value that fits what the network code needs", "`-XX:MaxRAMPercentage=100`", "`-XX:+HeapDumpOnOutOfMemoryError`, to catch the OOM kill"],
   "answer": 1,
   "why": "Without `MaxDirectMemorySize`, direct buffers may grow up to the max heap size, here 768 MB on top of a 768 MB heap in a 1 GiB container. Capping them makes the budget real. `-Xmx1g` and 100% make the problem worse, and a heap dump is never written when the kernel kills the process."
  },
  {
   "q": "From lesson 5: a ZGC service logs `Allocation Stall (main) 0.895ms` lines whenever it gets busy. What do they mean?",
   "options": [
    "Normal ZGC pauses, which always take about a millisecond",
    "Threads waited for memory because the heap filled before the concurrent collection finished",
    "The JIT stopped to compile a method",
    "A full GC ran"
   ],
   "answer": 1,
   "why": "ZGC's pauses stay well under a millisecond. A stall means a thread asked for memory and had to wait, because the program allocated faster than ZGC could reclaim. The fixes are more heap headroom, more CPU for the GC threads, or less allocation.",
   "from": "mem-05"
  }
 ],
 "flashcards": [
  {"front": "In `GC(0) Pause Young (Normal) (G1 Evacuation Pause) 28M->2M(214M) 8.692ms`, what are 28M, 2M and 214M?", "back": "Heap in use before the pause, heap in use after it, and the committed heap size."},
  {"front": "How do you recognize a pause line in any HotSpot GC log?", "back": "`Pause` right after `GC(id)` (ZGC adds `y:`, `Y:` or `O:` in between), and a duration in `ms` at the end."},
  {"front": "What GC logging setting suits production?", "back": "`-Xlog:gc*:file=gc.log:time,uptime,level,tags:filecount=5,filesize=20m`: rotating files with wall-clock times."},
  {"front": "What max heap does a JVM pick in a container by default?", "back": "25% of the container's memory limit (`MaxRAMPercentage` = 25). Very small limits get up to 50% (`MinRAMPercentage`)."},
  {"front": "Why does `-Xmx` equal to the container limit get the process killed?", "back": "Metaspace, code cache, thread stacks, GC data and direct buffers come on top of the heap, so the process goes over the cgroup limit and the kernel kills it."},
  {"front": "What does exit code 137 mean for a JVM in a container?", "back": "The kernel's OOM killer sent SIGKILL (128 + 9). No `OutOfMemoryError`, no heap dump, nothing in the log."},
  {"front": "What is the default limit for direct buffers?", "back": "The max heap size, unless you set `-XX:MaxDirectMemorySize`."}
 ],
 "terms": [
  {"term": "Unified logging", "plain": "The JVM's logging system since JDK 9, configured with -Xlog."},
  {"term": "Decorations", "plain": "The bracketed fields at the start of each log line: time, uptime, level, tags."},
  {"term": "Live set", "plain": "The objects that are really still in use. A full GC's after-value shows it."},
  {"term": "Container", "plain": "A program running in a fenced-off part of a shared machine, with its own memory and CPU limits."},
  {"term": "MaxRAMPercentage", "plain": "The share of the memory limit the JVM uses as its max heap. Default 25."},
  {"term": "Resident memory (RSS)", "plain": "The pages of a process that are really in RAM: what a container's memory limit counts."},
  {"term": "OOM killer", "plain": "The Linux kernel's guard that kills a process that goes over its memory limit."}
 ],
 "explain_back": {
  "prompt": "A colleague sets `-Xmx2g` in a container with a 2 GiB limit \"so the service can use all its memory\". The container gets killed a few hours after each start. Explain in your own words what happens and how you'd size it instead.",
  "answer": "`-Xmx` only caps the heap. The process also needs metaspace for classes, a code cache for compiled code, a stack per thread, memory for the GC's own records and direct buffers for network I/O, all outside the heap. With the heap allowed to fill the whole container, those extra hundreds of megabytes push the process over the cgroup limit. It takes hours because Linux counts only the pages a process has touched, and the heap touches its pages gradually as it fills. Then the kernel kills it with SIGKILL, so there's no Java error and no heap dump, only exit code 137. I'd use `-XX:MaxRAMPercentage` around 60 to 75, cap `-XX:MaxDirectMemorySize`, keep the thread count bounded, and check resident memory and NMT under a load test."
 },
 "deeper": {
  "minutes": 8,
  "body": "Three settings change around the JDK versions this course covers, all read from the JDK source.\n\n`InitialRAMPercentage` was 1.5625 on JDK 21 to 25 and is 0 on JDK 26, where the JVM computes the initial heap from a minimum size instead. A program that used to start with a heap of 1/64 of its limit now starts smaller and grows, so expect a few more young pauses in the first seconds unless you set `-Xms` or `-XX:InitialRAMPercentage` yourself.\n\n`MaxRAM` is deprecated on JDK 26 and obsolete on JDK 27, together with the switches that forced or blocked \"server-class\" behaviour. On 27, test heap sizing in a real container.\n\n`-XX:+UseContainerSupport` is on in every version from 21 to 27, and `-XX:ActiveProcessorCount=N` overrides the CPU count the JVM detects. That count matters more than it looks. Lesson 5 showed that on JDK 21 to 26 a single CPU silently means Serial GC, and the number of GC worker threads follows the count too.\n\nTwo flags help with Java's own `OutOfMemoryError`, the one that happens inside the limit. `-XX:+HeapDumpOnOutOfMemoryError` writes a heap dump (lesson 7 reads one). `-XX:+ExitOnOutOfMemoryError` makes the JVM exit, so whatever started the container can start a fresh one, instead of a program that limps on with threads that died halfway through their work. Both are off by default, and neither helps with a kernel OOM kill."
 },
 "sources": [
  {"title": "The java command, JDK 25 man page source: -Xlog, MaxRAMPercentage, UseContainerSupport", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/man/java.md"},
  {"title": "gc_globals.hpp at jdk-26-ga: InitialRAMPercentage and MaxRAM", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-26-ga/src/hotspot/share/gc/shared/gc_globals.hpp"},
  {"title": "VM.java at jdk-25-ga: the default direct memory limit", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/jdk/internal/misc/VM.java"},
  {"title": "gcCause.cpp at jdk-25-ga: the cause strings in GC logs", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/shared/gcCause.cpp"}
 ]
}

def move_answer(q, to):
    """Put the correct option at index `to`, keeping the others in order."""
    right = q["options"].pop(q["answer"])
    q["options"].insert(to, right)
    q["answer"] = to


for q, to in zip(L["quiz"], [1, 3, 0, 2, 1]):
    move_answer(q, to)

(ROOT / "content/lessons/mem-06.json").write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print("wrote mem-06")
