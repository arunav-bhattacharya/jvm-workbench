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


FIGURE = """<svg viewBox="0 0 680 250" role="img" aria-label="A pod with a 1 GiB memory limit. With -Xmx1g the heap alone fills the limit and native memory sticks out past it, so the kernel kills the process. With MaxRAMPercentage=75 the heap, native memory and some headroom fit under the limit">
<text class="t t-m" x="320" y="24" text-anchor="middle">one pod with a 1 GiB memory limit</text>
<line class="ln-bad" x1="520" y1="36" x2="520" y2="214"/>
<text class="t-s t-bad" x="520" y="232" text-anchor="middle">the limit: 1 GiB</text>
<text class="t" x="60" y="77" text-anchor="middle">-Xmx1g</text>
<rect class="box-a" x="120" y="55" width="400" height="36" rx="8"/>
<text class="t-s" x="320" y="77" text-anchor="middle">heap: 1,024 MB</text>
<rect class="box-bad" x="520" y="55" width="70" height="36" rx="8"/>
<text class="t-s" x="555" y="77" text-anchor="middle">+native</text>
<text class="t-s t-bad" x="320" y="112" text-anchor="middle">native memory goes past the limit: the kernel kills the process</text>
<text class="t" x="60" y="162" text-anchor="middle">75%</text>
<rect class="box-a" x="120" y="140" width="300" height="36" rx="8"/>
<text class="t-s" x="270" y="162" text-anchor="middle">heap: 768 MB</text>
<rect class="box-ok" x="420" y="140" width="66" height="36" rx="8"/>
<text class="t-s" x="453" y="162" text-anchor="middle">native</text>
<rect class="box-dim" x="486" y="140" width="34" height="36" rx="8"/>
<text class="t-s" x="320" y="198" text-anchor="middle">-XX:MaxRAMPercentage=75: heap, native memory and headroom fit</text>
</svg>"""

S1 = """One flag makes every collection print a line. Since JDK 9 the flag is `-Xlog:gc`, part of the unified logging system (older guides show `-XX:+PrintGCDetails`, which JDK 9 replaced). Here's a G1 young pause:

```text
[0.128s][info][gc] GC(0) Pause Young (Normal) (G1 Evacuation Pause) 14M->1M(256M) 12.723ms
```

Read it left to right. `[0.128s]` is the time since the JVM started, `[info]` the log level, `[gc]` the tag. `GC(0)` numbers the collection; a concurrent cycle gets a number of its own, and the pauses inside it reuse that number. `Pause Young` is the event. `(Normal)` says it's young-only; `Concurrent Start`, `Prepare Mixed` and `Mixed` are the other kinds from lesson 4. `(G1 Evacuation Pause)` is the cause: eden was full. You'll also see `G1 Humongous Allocation` and `System.gc()` there. `14M->1M(256M)` is the heap used before the pause, used after it, and the committed heap size. Last, `12.723ms` is how long every application thread was stopped.

`-Xlog:gc*`, with the star, turns on every GC tag: phases, region counts, metaspace and CPU time. That's ten to fifteen lines per pause, the detail lessons 4 and 5 used.

For a service, write the log to rotating files with wall-clock times, so it survives restarts and can't fill the disk:

```text
-Xlog:gc*:file=/var/log/app/gc.log:time,uptime,level,tags:filecount=5,filesize=20m
```

The colons separate the parts: what to log, where to write it, the decorations at the start of each line (`time` adds the date and time of day), and the rotation, here at most 5 files of 20 MB. When the current `gc.log` is full, the JVM moves it to a numbered file such as `gc.log.0` and starts a new one. Leave it on in production. It's a few lines per collection, and in an incident it's the first thing you'll want."""

S2 = """Three hundred log lines are hard to judge by eye. A few numbers say most of it:

- the number of pauses and their total time; divided by the elapsed time, that's the share of time your threads were stopped;
- the longest pause, which is what your p99 latency feels;
- the number of full GCs and evacuation failures, which should be zero in a healthy G1 service;
- the heap after the last full GC, the live set at that moment, which is the number you size a heap from;
- the trend of the after-values of young pauses: a floor that keeps rising means the live set is growing.

Computing them has two traps. Not every line with a duration is a pause. `Concurrent Mark Cycle 53.866ms` ran beside the application, and G1's `Evacuate Collection Set: 15.51ms` is a phase inside a pause you've already counted. ZGC's `Minor Collection ... 0.052s` is a whole concurrent cycle. One rule works for every HotSpot collector: a pause line has `Pause` right after `GC(id)` (ZGC puts `y:`, `Y:` or `O:` in between) and ends with a duration in `ms`. The second trap is `(System.gc())`, which has parentheses inside its parentheses and breaks the obvious regular expression.

The lab builds a parser with that rule and tests it on lines copied from real JDK 21 runs of all five collectors.

Check yourself on the G1 cycle from lesson 4: seven lines, starting with `Pause Young (Concurrent Start)` and ending with `Pause Full (System.gc()) 974M->1M(1024M)`. How many of them are pauses, and what does the last one tell you? (Six are pauses: Concurrent Start, Remark, Cleanup, Prepare Mixed, Mixed and the full GC. The two `Concurrent Mark Cycle` lines are not. The full GC's after-value, 1 MB, is the live set at that moment, because the program had finished its work and called `System.gc()`.)"""

S3 = """On Linux the JVM reads the container's limits: the cgroup memory limit and the CPU quota. `UseContainerSupport` is on by default in every JDK from 21 to 27. Without heap flags, the max heap is 25% of the memory limit (`MaxRAMPercentage`, default 25). A pod with a 1 GiB limit gets a 256 MB heap. That's a cautious default: three quarters of the pod stays free unless your service uses it outside the heap.

`-XX:MaxRAMPercentage` changes the share. With 75, the same pod gets 768 MB. Prefer it over a fixed `-Xmx`, because the heap then follows the limit when someone resizes the pod. Watch the top end: in a 64 GB pod, 75% is 48 GB, and compressed oops switch off (lesson 1). `-XX:InitialRAMPercentage` sets the starting heap. It was 1.5625% on JDK 21 to 25, and per the JDK source it is 0 on JDK 26, where the JVM starts from a small minimum and grows.

To see what the JVM detected, run `java -XshowSettings:system -version` inside the container. On the machine used for this course's research it printed `Provider: cgroupv1`, `Effective CPU Count: 4` and `Memory Limit: 13.35G`. `-Xlog:os+container=debug` shows the detection step by step, which helps when the numbers look wrong.

The demo can't create a container, so it uses `-XX:MaxRAM`, which tells the JVM how much memory to plan for, as a stand-in for a limit. That works on JDK 21 to 25. JDK 26 deprecated `MaxRAM`, and per the JDK source JDK 27 removed it; there, try the same flags in a real container (`docker run --memory=1g`)."""

S4 = """Here's the configuration that looks right and fails: a pod with a 1 GiB limit and `-Xmx1g`. Lesson 1 already showed why it can't work: the heap is only part of the process. In the demo below, a JVM with a 256 MB heap, a 64 MB direct buffer and 56 threads had 378 MB resident in RAM. Scale that to `-Xmx1g`, and the process needs well over 1 GiB once its heap is in use.

The failure doesn't look like a Java error. When a process goes over its cgroup limit, the Linux kernel's OOM killer ends it with SIGKILL. There's no `OutOfMemoryError`, no heap dump and nothing in the application log. Kubernetes reports `OOMKilled` and exit code 137 (128 plus signal 9). The pod can run fine for hours first, because Linux counts only the pages a process has touched, and the heap touches its pages bit by bit as it fills. The demo uses `-XX:+AlwaysPreTouch` to touch the whole heap at startup; without it, the same process showed 113 MB resident.

So budget the whole process: the heap, plus direct buffers, plus metaspace and code cache, plus a stack for each thread, plus GC bookkeeping, plus headroom.

Direct buffers need an explicit cap. Unless you set `-XX:MaxDirectMemorySize`, the JDK allows direct buffers up to the max heap size, so a service could in theory ask for twice its heap. Netty-based stacks such as Quarkus use direct memory for network I/O.

My starting point for a payments pod is `-XX:MaxRAMPercentage` between 50 and 75, a `-XX:MaxDirectMemorySize` that fits what the I/O layer needs, and a bounded number of threads. Then measure under load with Native Memory Tracking, which lesson 7 covers, and adjust."""

L = {
 "id": "mem-06",
 "title": "Reading GC logs and sizing the heap in containers",
 "minutes": 37,
 "goal": "By the end you can read a unified GC log line field by field, turn a log into pause numbers with a small parser, and size the heap of a service in a container so it is not OOM-killed.",
 "warmup": {
  "q": "A Quarkus service runs in a pod with a 2 GiB memory limit and `-Xmx2g`. Under load it disappears and Kubernetes shows `OOMKilled`, exit code 137. What do you expect in the application log?",
  "options": ["A `java.lang.OutOfMemoryError: Java heap space`", "A heap dump, if `-XX:+HeapDumpOnOutOfMemoryError` is set", "Nothing about memory: the kernel killed the process from outside", "A `Pause Full` line followed by a JVM crash report"],
  "answer": 2,
  "why": "Exit code 137 is 128 plus signal 9, SIGKILL. The Linux OOM killer ended the process because the whole process (heap plus native memory) went over the cgroup limit. The JVM never got a chance to throw anything, write a heap dump or log a line. A Java `OutOfMemoryError` only happens when the heap itself is full, inside the limit."
 },
 "sections": [
  {
   "h": "-Xlog:gc prints one line per collection",
   "body": S1,
   "try": {
    "title": "Write a GC log the production way",
    "minutes": 4,
    "steps": [
     "Read `GcLogFileDemo`. It runs two seconds of the lesson 4 service load in a child JVM with a 256 MB heap and the rotating-file setting from this section, at 200 KB per file.",
     "Predict: how many files will there be, and will the last young pause leave more or less heap than the first?",
     "Run it, then open `labs/memory/build/gc-logs/gc.log` and find a `Pause Young` line with its date and time."
    ],
    "code": demo("GcLogFileDemo"),
    "expect": "Two files: `gc.log.0` (full, about 200 KB, the older lines) and `gc.log` (the newest lines). Dozens of `(Evacuation Failure)` lines and often a few `Pause Full`, because this heap is too small for its cache on purpose. The first young pause goes `14M->1M`, the last ones stay near 200 MB after the pause: the floor rose as the cache filled. The counts change from run to run."
   },
   "refs": [
    {"title": "The java command, JDK 25 man page source: -Xlog", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/man/java.md", "kind": "docs"}
   ]
  },
  {
   "h": "Turn a log into a few numbers",
   "body": S2
  },
  {
   "h": "The JVM sizes its heap from the container limit",
   "body": S3,
   "figure": {"svg": FIGURE, "caption": "-Xmx equal to the limit leaves no room for native memory. A percentage leaves room for it and for headroom."},
   "try": {
    "title": "Watch the heap follow the limit",
    "minutes": 3,
    "steps": [
     "Predict the max heap for limits of 1, 2 and 4 GiB, with defaults and with `-XX:MaxRAMPercentage=75`.",
     "Run `HeapSizingDemo` (JDK 21 to 25). Each line comes from a child JVM started with `-XX:MaxRAM` as the limit.",
     "If you have Docker, run `docker run --rm --memory=1g eclipse-temurin:25 java -XshowSettings:system -version` and find the memory limit it reports."
    ],
    "code": demo("HeapSizingDemo"),
    "expect": "256, 512 and 1,024 MB with defaults (25%), and 768, 1,536 and 3,072 MB with 75%. In a container, `-XshowSettings:system` reports the limit you gave it, for example `Memory Limit: 1.00G`."
   },
   "refs": [
    {"title": "arguments.cpp at jdk-25-ga: heap sizing from available memory", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/runtime/arguments.cpp", "kind": "read"}
   ]
  },
  {
   "h": "-Xmx equal to the limit gets the pod killed",
   "body": S4,
   "try": {
    "title": "Compare the heap with the whole process",
    "minutes": 3,
    "steps": [
     "Read `FootprintDemo`. Its child JVM has `-Xmx256m -Xms256m -XX:+AlwaysPreTouch`, allocates a 64 MiB direct buffer and starts 50 threads, then prints what the JVM reports next to what Linux says is resident.",
     "Predict the resident number before you run it.",
     "Run it. Then remove `-XX:+AlwaysPreTouch` from the demo and run it again."
    ],
    "code": demo("FootprintDemo"),
    "expect": "On Linux: heap 256 MB, non-heap about 8 MB, direct buffers 64 MB, 56 threads, and about 378 MB resident, roughly 120 MB more than the heap. Without `AlwaysPreTouch` the resident number drops to about 113 MB, because the heap's pages aren't touched yet; a running service gets there anyway as its heap fills. On macOS the demo can't read the resident size and says so."
   }
  }
 ],
 "analogy": "A container's memory limit is a moving truck of fixed size. The heap is the big wardrobe, and `-Xmx` decides how big a wardrobe you buy. But the truck also has to carry the boxes nobody counts: metaspace, thread stacks, direct buffers, the GC's own bookkeeping. Buy a wardrobe as long as the truck and the boxes don't fit, and the driver (the kernel) refuses to drive and throws everything out, with no note left behind. Where it breaks: a truck is loaded once. A JVM keeps loading boxes while it runs, so the overflow can come hours after it started.",
 "in_your_world": "Before a payment service moves to Kubernetes, check three things. Its JVM flags: a hard-coded `-Xmx` that equals the pod limit is a time bomb, and the absence of any flag means a 25% heap that may be far too small. Its GC log: it should go to rotating files with `time` decorations, so an incident at 3 a.m. has a log to read. And its exit codes: a pod that restarts with 137 and nothing in the log was killed by the kernel for native memory, not by a heap problem, and a heap dump won't explain it. For a Quarkus service with Netty's direct buffers, set `-XX:MaxDirectMemorySize` on purpose instead of inheriting the heap size.",
 "mistake": "Setting `-Xmx` to the container's memory limit, or `-XX:MaxRAMPercentage=100`, because \"the heap should get all the memory\". The heap is the only part of the process `-Xmx` caps. Metaspace, code cache, thread stacks, GC bookkeeping and direct buffers all come on top, so the process outgrows the limit and the kernel kills it, often hours after a deploy, with no Java error at all. People make the mistake because the heap is the only memory the JVM's error messages talk about. The fix: size with a percentage, between 50 and 75 for most services, cap direct memory, and confirm with Native Memory Tracking under real load.",
 "compare": {
  "title": "Log what memory the JVM thinks it has, at startup",
  "java": {"title": "MemoryBanner.java", "src": "var os = (com.sun.management.OperatingSystemMXBean) ManagementFactory.getOperatingSystemMXBean();\nlog.infof(\"memory seen %d MB, CPUs %d, max heap %d MB\",\n        os.getTotalMemorySize() >> 20,\n        Runtime.getRuntime().availableProcessors(),\n        Runtime.getRuntime().maxMemory() >> 20);"},
  "kotlin": {"title": "MemoryBanner.kt", "src": "val os = ManagementFactory.getOperatingSystemMXBean() as com.sun.management.OperatingSystemMXBean\nlog.infof(\"memory seen %d MB, CPUs %d, max heap %d MB\",\n    os.totalMemorySize shr 20,\n    Runtime.getRuntime().availableProcessors(),\n    Runtime.getRuntime().maxMemory() shr 20)"},
  "note": "Both versions call the same JDK API; Kotlin reads `getTotalMemorySize()` as a property and writes `>>` as `shr`. The value of the line is in what it reports. `getTotalMemorySize()` follows the container: on the research machine it said 14,337,576,960 bytes, the 13.35 GiB limit, while the host had 16 GB. `availableProcessors()` follows the CPU limit too. One line like this at startup tells you, in every environment, whether the JVM sees the limit you think you gave it and what heap it chose from it."
 },
 "worked": {
  "title": "Size a payment service's pod from measurements",
  "steps": [
   {"say": "Start from numbers you measured, not from defaults. These are for an invented Quarkus authorization service under a realistic load test: the after-value of its full GCs, and Native Memory Tracking's summary of everything outside the heap.",
    "code": "GC log, full GCs during the test:   ... Pause Full (G1 Compaction Pause) 1180M->310M(1536M) ...\nNMT committed outside the heap:     metaspace + class 95 MB, code 45 MB, threads 35 MB (140 threads),\n                                    GC 40 MB, other 70 MB (Netty direct buffers)",
    "lang": "text"},
   {"say": "1. Size the heap from the live set. 310 MB stays live after a full GC. G1 needs free regions to copy into, so give it two to three times the live set: about 768 MB.",
    "code": "", "lang": ""},
   {"say": "2. Add up the whole process and leave headroom for what the test didn't hit: a traffic peak, a burst of threads, a bigger JIT code cache later in the day.",
    "code": "heap                    768 MB\noutside the heap        285 MB   (95 + 45 + 35 + 40 + 70)\nheadroom, about 15%     160 MB\n                       ------\nprocess               ~1,213 MB  -> ask for a 1.25 GiB (1,280 MB) limit\nheap share            768 / 1,280 = 60%",
    "lang": "text"},
   {"say": "3. Write the flags so they follow the limit, cap direct memory a bit above what NMT showed, and keep the GC log. Then run the load test again and check two things: no `Pause Full` in the log, and resident memory well under the limit.",
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
   "Run the tests. All ten fail. Open `GcLogTest.kt`: every line in it comes from a real JDK 21 run.",
   "Write `parsePause` with one regular expression: `GC(id)`, an optional `y: `, `Y: ` or `O: `, then `Pause` and the capitalized words after it, then zero or more `( ... )` labels, then optional `14M->1M(256M)`, then the duration in `ms` at the end of the line.",
   "Pull the labels out of their group with a second, smaller regex, and turn missing heap numbers into `null`.",
   "Write `summarize`: count, total, longest, full GCs, evacuation failures, and the after-value of the last full GC.",
   "Run the tests until all ten pass. Then point the parser at the log the first demo wrote, in `labs/memory/build/gc-logs`."
  ],
  "hints": [
   "A raw string (`\"\"\"...\"\"\"`) saves you from doubling every backslash in a Kotlin regex.",
   "A label is `\\((?:[^()]|\\(\\))*\\)`: an opening parenthesis, then any characters that are not parentheses or the exact pair `()`, then the closing one. That's what lets `(System.gc())` through.",
   "Anchor the duration with `ms$`, so ZGC's `0.052s` and the start lines without a duration don't match. Call `trimEnd()` on the line first.",
   "`m.destructured` gives you the groups as `val (id, kind, labels, before, after, committed, ms) = ...`; an empty optional group comes back as \"\", and `toIntOrNull()` turns that into `null`."
  ],
  "done_when": "All 10 tests in `GcLogTest` pass."
 },
 "drill": {
  "title": "Read a line without the lesson",
  "minutes": 4,
  "prompt": "Close the page. For `[3.112s][info][gc] GC(87) Pause Young (Mixed) (G1 Evacuation Pause) (Evacuation Failure) 1490M->1210M(1536M) 38.204ms`, write down what each part means and whether this service is healthy. Then write the pause-line regex from memory.",
  "answer": {
   "lang": "java",
   "src": "// 3.112 s after start; collection 87; a mixed pause (young + some old regions); eden was full;\n// copying failed for lack of free regions; 1,490 MB used before, 1,210 after, 1,536 MB committed; 38 ms stopped.\n// Not healthy: an evacuation failure with 1.2 GB still used means the live set barely fits.\nstatic final Pattern PAUSE = Pattern.compile(\n        \"GC\\\\((\\\\d+)\\\\) (?:[yYO]: )?(Pause(?: [A-Z]\\\\w*)+)\"   // id, ZGC prefix, kind\n        + \"((?: \\\\((?:[^()]|\\\\(\\\\))*\\\\))*)\"                     // labels, (System.gc()) included\n        + \"(?: (\\\\d+)M->(\\\\d+)M\\\\((\\\\d+)M\\\\))?\"                 // heap before -> after (committed)\n        + \" ([\\\\d.]+)ms$\");                                     // the pause",
   "alt": {
    "lang": "kotlin",
    "src": "// 3.112 s after start; collection 87; a mixed pause (young + some old regions); eden was full;\n// copying failed for lack of free regions; 1,490 MB used before, 1,210 after, 1,536 MB committed; 38 ms stopped.\n// Not healthy: an evacuation failure with 1.2 GB still used means the live set barely fits.\nval PAUSE = Regex(\n    \"\"\"GC\\((\\d+)\\) (?:[yYO]: )?(Pause(?: [A-Z]\\w*)+)\"\"\" +     // id, ZGC prefix, kind\n    \"\"\"((?: \\((?:[^()]|\\(\\))*\\))*)\"\"\" +                         // labels, (System.gc()) included\n    \"\"\"(?: (\\d+)M->(\\d+)M\\((\\d+)M\\))?\"\"\" +                       // heap before -> after (committed)\n    \"\"\" ([\\d.]+)ms$\"\"\"                                           // the pause\n)"
   }
  }
 },
 "recap": [
  "`-Xlog:gc` prints one line per collection: uptime, level, tag, `GC(id)`, the event and its cause, heap before -> after (committed), and the pause length. `-Xlog:gc*` adds the details.",
  "In production, log to rotating files with wall-clock times: `-Xlog:gc*:file=gc.log:time,uptime,level,tags:filecount=5,filesize=20m`.",
  "A pause line has `Pause` right after `GC(id)` and ends in `ms`. Concurrent phases, G1's phase timings and ZGC's `Collection` lines are not pauses.",
  "Check full GCs and evacuation failures (or ZGC allocation stalls), the longest pause, and the floor of the young pauses' after-values. The heap after a full GC is the live set.",
  "In a container the max heap defaults to 25% of the limit. Size it with `-XX:MaxRAMPercentage`, usually 50 to 75, never 100.",
  "Heap plus native memory over the limit means a kernel OOM kill: exit code 137, no `OutOfMemoryError`, no heap dump. Cap direct memory and measure with NMT."
 ],
 "quiz": [
  {
   "q": "Which of these log lines is a stop-the-world pause?",
   "options": [
    "`GC(21) Concurrent Mark Cycle 53.866ms`",
    "`GC(21) Pause Remark 583M->583M(1024M) 0.835ms`",
    "`GC(4) Minor Collection (Allocation Rate) 582M(57%)->226M(22%) 0.052s`",
    "`GC(3)   Evacuate Collection Set: 15.51ms`"
   ],
   "answer": 1,
   "why": "Remark is one of the two short pauses that finish G1's concurrent marking. The mark cycle itself ran beside the application. ZGC's `Minor Collection` duration is the concurrent cycle. `Evacuate Collection Set` is a phase inside a young pause, whose own `Pause Young` line already counts it."
  },
  {
   "q": "A JDK 21 service runs in a pod with a 2 GiB memory limit and no heap flags. What max heap does the JVM pick?",
   "options": ["2 GB", "1.5 GB", "1 GB", "512 MB"],
   "answer": 3,
   "why": "With container support on, the JVM bases the heap on the memory limit and takes `MaxRAMPercentage`, 25% by default: 512 MB. The demo showed the same arithmetic for 1, 2 and 4 GiB. To use more, set `-XX:MaxRAMPercentage`, for example 60 or 75."
  },
  {
   "q": "Over ten minutes, a service's young pauses end at `310M`, `355M`, `402M`, `447M` and `495M`, and a full GC finally goes `1490M->1210M(1536M)`. What is going on?",
   "options": [
    "The young generation is too small; raise it",
    "The live set keeps growing, which points to a leak or an unbounded cache",
    "G1's pause goal is too strict",
    "Nothing: G1 always lets the heap fill before collecting"
   ],
   "answer": 1,
   "why": "The after-values of young pauses are what survives, and their floor rises about 45 MB a pass. Even a full GC can only free 280 MB of 1,490 MB: 1.2 GB is really live. A bigger heap only delays the moment it fills; lesson 7 finds what's holding the memory."
  },
  {
   "q": "A pod has a 1 GiB limit. The service runs with `-XX:MaxRAMPercentage=75` and Netty-based I/O, with no other memory flags. Which flag should you add first?",
   "options": ["`-Xmx1g`", "`-XX:MaxDirectMemorySize` with a value that fits the I/O layer", "`-XX:MaxRAMPercentage=100`", "`-XX:+HeapDumpOnOutOfMemoryError`, to catch the OOM kill"],
   "answer": 1,
   "why": "Without `MaxDirectMemorySize`, direct buffers may grow up to the max heap size, here 768 MB on top of a 768 MB heap in a 1 GiB pod. Capping it makes the budget real. `-Xmx1g` and 100% make the pod's problem worse, and a heap dump is never written when the kernel kills the process."
  },
  {
   "q": "From lesson 5: a ZGC service logs `Allocation Stall (http-worker-12) 41.210ms` lines during peaks. What do they mean?",
   "options": [
    "Normal ZGC pauses, which are always about 40 ms",
    "Application threads waited for memory because the heap filled before the concurrent collection finished",
    "The JIT stopped to compile a method",
    "A full GC ran"
   ],
   "answer": 1,
   "why": "ZGC's pauses stay well under a millisecond. A stall means a thread asked for memory and had to wait, because the application allocated faster than ZGC could reclaim. The fixes are more heap headroom or more CPU for the GC threads, or less allocation.",
   "from": "mem-05"
  }
 ],
 "flashcards": [
  {"front": "In `GC(0) Pause Young (Normal) (G1 Evacuation Pause) 14M->1M(256M) 12.723ms`, what are 14M, 1M and 256M?", "back": "Heap used before the pause, heap used after it, and the committed heap size."},
  {"front": "How do you recognize a pause line in any HotSpot GC log?", "back": "`Pause` right after `GC(id)` (ZGC adds `y:`, `Y:` or `O:` in between), and a duration in `ms` at the end."},
  {"front": "What GC logging setting suits production?", "back": "`-Xlog:gc*:file=gc.log:time,uptime,level,tags:filecount=5,filesize=20m`: rotating files with wall-clock times."},
  {"front": "What max heap does a JVM pick in a container by default?", "back": "25% of the container's memory limit (`MaxRAMPercentage` = 25)."},
  {"front": "Why does `-Xmx` equal to the container limit get the pod killed?", "back": "Metaspace, code cache, thread stacks, GC data and direct buffers come on top of the heap, so the process goes over the cgroup limit and the kernel kills it."},
  {"front": "What does exit code 137 with `OOMKilled` mean for a JVM pod?", "back": "The kernel's OOM killer sent SIGKILL. No `OutOfMemoryError`, no heap dump, nothing in the log."},
  {"front": "What is the default limit for direct buffers?", "back": "The max heap size, unless you set `-XX:MaxDirectMemorySize`."}
 ],
 "terms": [
  {"term": "Unified logging", "plain": "The JVM's logging system since JDK 9, configured with -Xlog."},
  {"term": "Decorations", "plain": "The bracketed fields at the start of each log line: time, uptime, level, tags."},
  {"term": "Live set", "plain": "The objects that are really still in use. A full GC's after-value shows it."},
  {"term": "Container support", "plain": "The JVM reading cgroup limits so it sizes itself to the container, not the host."},
  {"term": "MaxRAMPercentage", "plain": "The share of the memory limit the JVM uses as its max heap. Default 25."},
  {"term": "Resident memory (RSS)", "plain": "The pages of a process that are really in RAM: what a container limit counts."},
  {"term": "OOM killer", "plain": "The Linux kernel feature that kills a process that goes over its memory limit."}
 ],
 "explain_back": {
  "prompt": "A colleague sets `-Xmx2g` in a 2 GiB pod \"so the service can use all its memory\". The pod gets OOM-killed a few hours after each deploy. Explain in your own words what happens and how you'd size it instead.",
  "answer": "`-Xmx` only caps the heap. The process also needs metaspace for classes, a code cache for compiled code, a stack per thread, memory for the GC's own data and direct buffers for network I/O, all outside the heap. With the heap allowed to fill the whole pod, those extra hundreds of megabytes push the process over the cgroup limit. It takes hours because Linux only counts pages the process has touched, and the heap touches its pages gradually as it fills. Then the kernel kills it with SIGKILL, so there's no Java error and no heap dump, only exit code 137. I'd use `-XX:MaxRAMPercentage` around 60 to 75, cap `-XX:MaxDirectMemorySize`, keep the thread count bounded, and check resident memory and NMT under a load test."
 },
 "deeper": {
  "minutes": 8,
  "body": "Three settings change around the JDK versions this course covers, all read from the JDK source.\n\n`InitialRAMPercentage` was 1.5625 on JDK 21 to 25 and is 0 on JDK 26, where the JVM computes the initial heap from a minimum size instead. A service that used to start with a heap of 1/64 of its limit now starts smaller and grows, so expect a few more young pauses in the first seconds unless you set `-Xms` or `-XX:InitialRAMPercentage` yourself.\n\n`MaxRAM` is deprecated on JDK 26 and obsolete on JDK 27, together with the switches that forced or blocked \"server-class\" behaviour. On 27, test heap sizing in a real container.\n\n`-XX:+UseContainerSupport` is on in every version from 21 to 27, and `-XX:ActiveProcessorCount=N` overrides the CPU count the JVM detects. That count matters more than it looks: lesson 5 showed that on JDK 21 to 26 a single CPU silently means Serial GC, and the number of GC worker threads follows it too.\n\nTwo flags help with Java's own `OutOfMemoryError`, the one that happens inside the limit: `-XX:+HeapDumpOnOutOfMemoryError` writes a heap dump (lesson 7 reads one), and `-XX:+ExitOnOutOfMemoryError` makes the JVM exit, so Kubernetes restarts a pod that would otherwise limp on with threads that died halfway through their work. Both are off by default, and neither helps with a kernel OOM kill."
 },
 "sources": [
  {"title": "The java command, JDK 25 man page source: -Xlog, MaxRAMPercentage, UseContainerSupport", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/man/java.md"},
  {"title": "gc_globals.hpp at jdk-26-ga: InitialRAMPercentage and MaxRAM", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-26-ga/src/hotspot/share/gc/shared/gc_globals.hpp"},
  {"title": "VM.java at jdk-25-ga: the default direct memory limit", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/jdk/internal/misc/VM.java"},
  {"title": "gcCause.cpp at jdk-25-ga: the cause strings in GC logs", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/shared/gcCause.cpp"}
 ]
}

(ROOT / "content/lessons/mem-06.json").write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print("wrote mem-06")
