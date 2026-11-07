import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/performance/src"
P = "java/workbench/performance/l06"
K = "kotlin/workbench/performance/l06"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :performance:demo -Pmain=workbench.performance.l06."

def demo(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": DEMO + name, "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
                    "run": DEMO + name + "Kt", "file": f"{lab}/demo/{K}/{name}.kt"}}

# Flame graph of PaymentSim.feeSlow, from the research notes' async-profiler 4.6 CPU profile
# (cpu-slow.collapsed: 8,005 samples, 5,747 of them inside feeSlow). Children in alphabetical
# order of their full frame names, as flamegraph.pl draws them; small frames grouped as "other".
X0, W, TOTAL = 20, 640, 5747
LEVEL1 = [("java/lang/String.format", 1864, "String.format"), ("java/math/BigDecimal.<init>", 634, "BigDec()"),
          ("java/math/BigDecimal.setScale", 186, ""), ("java/math/BigDecimal.toPlainString", 919, "toPlainString"),
          ("java/util/regex/Pattern.compile", 1409, "Pattern.compile"), ("java/util/regex/Pattern.matcher", 347, ""),
          ("other", 388, "other")]
LEVEL2 = {"java/lang/String.format": [(1730, "Formatter.format", "box-b")],
          "java/math/BigDecimal.<init>": [(143, "", "box"), (481, "", "box")],
          "java/math/BigDecimal.toPlainString": [(319, "", "box"), (573, "", "box")],
          "java/util/regex/Pattern.compile": [(1381, "Pattern.<init>", "box-b")],
          "java/util/regex/Pattern.matcher": [(329, "", "box")]}

def fig():
    s = ['<svg viewBox="0 0 680 200" role="img" aria-label="Flame graph of feeSlow from a real CPU profile: String.format is the widest child, then Pattern.compile, BigDecimal.toPlainString and the BigDecimal constructor. Boxes are ordered alphabetically, not by time.">',
         '<text class="t-s t-m" x="340" y="22" text-anchor="middle">width = samples in that frame or above it; left to right = alphabetical, not time</text>']
    sc = W / TOTAL
    s.append(f'<rect class="box-a" x="{X0}" y="110" width="{W}" height="28" rx="4"/>'
             f'<text class="t" x="{X0 + W / 2:.0f}" y="129" text-anchor="middle">PaymentSim.feeSlow: 5,747 of 8,005 samples</text>')
    x = X0
    for full, n, label in LEVEL1:
        w = n * sc
        cls = "box-dim" if full == "other" else "box"
        s.append(f'<rect class="{cls}" x="{x:.1f}" y="80" width="{w - 1:.1f}" height="28" rx="4"/>')
        if label:
            s.append(f'<text class="t-s" x="{x + w / 2:.1f}" y="98" text-anchor="middle">{label}</text>')
        x2 = x
        for m, l2, c2 in LEVEL2.get(full, []):
            w2 = m * sc
            s.append(f'<rect class="{c2}" x="{x2:.1f}" y="50" width="{w2 - 1:.1f}" height="28" rx="4"/>')
            if l2:
                esc = l2.replace("<", "&lt;").replace(">", "&gt;")
                s.append(f'<text class="t-s" x="{x2 + w2 / 2:.1f}" y="68" text-anchor="middle">{esc}</text>')
            x2 += w2
        x += w
    s.append('<text class="t-s t-m" x="340" y="160" text-anchor="middle">String.format 1,864 · Pattern.compile 1,409 · toPlainString 919 · BigDecimal.&lt;init&gt; 634</text>')
    s.append('<text class="t-s t-m" x="340" y="180" text-anchor="middle">small unlabeled boxes: setScale, Pattern.matcher and their callees</text>')
    s.append('</svg>')
    return "\n".join(s)

SAMPLER_J = """Map<String, Long> stacks = new HashMap<>();
while (worker.isAlive()) {
    Thread.sleep(10);                                       // 1. wait one sampling interval
    StackTraceElement[] st = worker.getStackTrace();        // 2. snapshot the thread's stack
    List<String> frames = new ArrayList<>();
    for (int i = st.length - 1; i >= 0; i--)                // 3. root first
        frames.add(st[i].getClassName() + "." + st[i].getMethodName());
    stacks.merge(String.join(";", frames), 1L, Long::sum);  // 4. count identical stacks
}"""
SAMPLER_K = """val stacks = HashMap<String, Long>()
while (worker.isAlive) {
    Thread.sleep(10)                                        // 1. wait one sampling interval
    val st = worker.stackTrace                              // 2. snapshot the thread's stack
    val key = st.reversed()                                 // 3. root first
        .joinToString(";") { "${it.className}.${it.methodName}" }
    stacks.merge(key, 1L, Long::plus)                       // 4. count identical stacks
}"""

L = {
 "id": "perf-06",
 "title": "async-profiler and flame graphs",
 "minutes": 38,
 "goal": "By the end you can explain how a sampling profiler works and why safepoint bias misleads simple ones, profile a JVM with async-profiler in cpu, wall, alloc and lock modes, and read a flame graph correctly.",
 "warmup": {
  "q": "In a flame graph, the box for `Pattern.compile` sits to the left of `String.format` at the same height. What does that tell you?",
  "options": [
   "`Pattern.compile` ran before `String.format`",
   "Nothing about time: boxes at the same level are sorted alphabetically by frame name",
   "`Pattern.compile` is slower than `String.format`",
   "`Pattern.compile` was called by `String.format`"
  ],
  "answer": 1,
  "why": "The x-axis of a flame graph isn't a timeline. Brendan Gregg's flamegraph.pl says the ordering \"has no meaning\" and sorts frames alphabetically. Width says how many samples had that frame; height says how deep the stack was. A caller is drawn below its callees, never beside them."
 },
 "sections": [
  {
   "h": "A sampling profiler is a loop that counts stacks",
   "body": "Take `SlowFees.feeSlow`, the fee calculation lesson 7 investigates. You want to know where its CPU time goes, call by call, without changing its code. You could add timers around every call, but timers change what they measure, and you'd need to know where to put them.\n\nA **sampling profiler** does something simpler. Every few milliseconds it looks at what each thread is executing, records the whole call stack, and counts how often each stack shows up. If a method is on top of the stack in 20% of the samples, the thread spent about 20% of its time there. You can build one in a dozen lines:\n\n```java\n" + SAMPLER_J + "\n```\n\n```kotlin\n" + SAMPLER_K + "\n```\n\nThe output is the format every flame graph tool reads, **collapsed stacks**: one line per distinct stack, frames from the root to the top separated by `;`, then the number of samples.\n\n```text\njava.lang.Thread.run;...SlowFees.feeSlow;java.math.BigDecimal.toPlainString;java.lang.Long.toString;java.lang.Long.getChars 45\n```\n\nTwo words come up constantly. A frame's **self** time is the samples where it was on top of the stack, doing the work itself. Its **inclusive** time adds everything it called. `feeSlow` has almost no self time and a huge inclusive time: it does little itself and calls expensive things.\n\n`PoorMansProfiler` runs `feeSlow` on two threads for 4 seconds and samples them like this. One run took 702 samples. Its top frames were `BigDecimal.<init>` 15.0%, `BigDecimal.toPlainString` 15.0%, `AbstractStringBuilder.ensureCapacityInternal` 10.5% and `Formatter.parse` 9.5%. That looks like a usable answer. The next section shows why it isn't quite.",
   "try": {
    "title": "Run a profiler you can read in one screen",
    "minutes": 4,
    "steps": [
     "Read `PoorMansProfiler` and `SlowFees.feeSlow`. Predict the three methods that will be on top most often.",
     "Run it. It prints the top frames and writes `build/poor-man.collapsed` (relative to `labs/performance`).",
     "Open the collapsed file and find the line with the biggest count. Run the Kotlin twin and compare its top frames."
    ],
    "code": demo("PoorMansProfiler"),
    "expect": "About 700 samples in 4 seconds (2 threads, every 10 ms). The top frames are spread over `BigDecimal`, `StringBuilder`, `Formatter` and regex methods. The Kotlin twin put 13.8% on its own `kFeeSlow` frame in one run, which is odd for a method that only calls other methods. Remember that oddity for the next section."
   }
  },
  {
   "h": "Safepoint bias: the hand-made profiler only sees threads where they can stop",
   "body": "`Thread.getStackTrace()` on another thread can't read that thread's stack at an arbitrary instruction. Compiled code keeps values in registers and has inlined frames, so the JVM can only describe a thread's stack at a **safepoint**: a point where it has recorded the full state of the frames. Compiled code checks for a request to stop at safepoint polls, which sit mostly at method returns and loop back-edges. So when the sampler asks, the thread runs on to the next poll and reports its stack there.\n\nThe samples pile up on polls instead of where the CPU spends its time. A tight inlined loop without a poll looks free, and the method that contains the next poll gets the blame. That's why the Kotlin twin charged 13.8% to `kFeeSlow` itself. This is **safepoint bias**, and every profiler built on `getStackTrace` or the JVMTI `GetAllStackTraces` call has it.\n\nThe same workload under **async-profiler 4.6** gave a different picture. Its top frames were `Formatter.format` 17.7%, `Long.getChars` 14.9%, `Pattern.compile` 12.4% and `BigDecimal.<init>` 10.3%. `Formatter.format` didn't appear in the hand-made top six at all. And where the hand-made profiler charged 15% to `toPlainString` itself, async-profiler charged 14.9% to `Long.getChars`, a method `toPlainString` calls.\n\nasync-profiler avoids the bias by interrupting each thread with a signal, driven by Linux `perf_events` or a timer, and walking the stack at the exact instruction where the signal landed. To make sense of JIT-compiled frames there, it reads HotSpot's internal structures: originally through `AsyncGetCallTrace`, a HotSpot-only function the profiler is named after, and since version 4.2 with its own walker by default. Because it works below the JVM, it also shows native frames, JVM frames (GC, JIT compiler threads) and kernel frames, which no Java-level profiler can see.\n\nJFR, from lesson 5, doesn't have the bias in its classic form either. In JDK 25 its sampler records where the thread was at the sampling moment and lets the thread finish the stack walk at its next safepoint (cooperative sampling, JEP 518).\n\nCheck yourself: a method has one hot inlined loop and returns once at the end. Which method would a `getStackTrace` profiler blame for the loop's time? (Whichever frame reaches the next safepoint poll, often the loop's own back-edge or the caller after the return, not the instructions that burned the CPU.)",
   "try": {
    "title": "Profile the same code with async-profiler",
    "minutes": 6,
    "steps": [
     "Download async-profiler from its GitHub releases page (Linux x64 or arm64, or macOS) and unpack it. `bin/asprof` is the launcher.",
     "Run `ProfileMe`. It prints its pid and keeps four threads busy for 8 seconds.",
     "In a second terminal, within those 8 seconds: `asprof -d 5 -f cpu.html <pid>`. Open `cpu.html` in a browser.",
     "Compare its widest top frames with `PoorMansProfiler`'s list."
    ],
    "code": demo("ProfileMe"),
    "expect": "A flame graph with `feeSlow` covering almost the whole width of the worker threads, and `String.format`, `Pattern.compile`, `toPlainString` and `BigDecimal.<init>` as its widest children. On Linux you may also see GC and JIT compiler threads as separate towers. If `asprof` reports that perf_events are unavailable (common in containers), add `-e ctimer`, which works without them."
   },
   "refs": [
    {"title": "async-profiler (README and releases)", "url": "https://github.com/async-profiler/async-profiler", "kind": "docs"}
   ]
  },
  {
   "h": "Reading a flame graph: width is samples, the x-axis is the alphabet",
   "body": "A flame graph is the collapsed stacks drawn as boxes. Each box is one frame. The root sits at the bottom, and each frame's callees are stacked on top of it. Three rules make it readable.\n\nWidth is samples. A box's width is the number of samples with that frame on the stack at that position, which is its inclusive time there. Identical frames at the same depth under the same parent are merged into one box.\n\nThe x-axis is not time. Boxes at the same level are sorted alphabetically. flamegraph.pl's own header says \"The ordering on the x-axis has no meaning\", and async-profiler's guide says a flame graph \"does not preserve information on when a particular stack trace was taken\". A box on the left didn't run first.\n\nLook at the tops. The part of a box with nothing above it is self time: the CPU was in that frame's own code. Wide tops are where to start. A wide box covered by its children is a caller, and the fix is usually in one of them.\n\nThe figure is drawn from a real async-profiler CPU profile of the same fee code (its class was called `PaymentSim` in that run): 8,005 samples over 10 seconds, of which `feeSlow` covered 5,747 (71.8%). Its widest children are `String.format` (23.3% of all samples), `Pattern.compile` (17.6%), `BigDecimal.toPlainString` (11.5%) and the `BigDecimal` constructor (7.9%). Outside `feeSlow`, about 8% of the samples were G1 garbage collector threads and about 9% C2 compiler threads, and 608 samples were in `__vdso_clock_gettime`: the test harness calling `System.nanoTime()` around every request. A profiler shows its own observers too.\n\nasync-profiler's HTML colours frames by type: green for compiled Java, aqua for inlined Java, light green for interpreted, yellow for JVM (C++) code, red for native and orange for kernel. Clicking a box zooms in, and the search field highlights every frame that matches. The same tools draw two useful variants: a reversed graph (`--reverse`) that merges stacks from the top frame down, which groups all callers of a hot leaf, and an icicle graph (`--inverted`) that hangs from the top.",
   "figure": {"svg": fig(), "caption": "The feeSlow part of a real 8,005-sample CPU profile. Widths are sample counts; small frames are grouped as \"other\" in this drawing."},
   "try": {
    "title": "Read your flame graph like a profile",
    "minutes": 4,
    "steps": [
     "Open `cpu.html` from the previous Try it. Type `Pattern` into the search field: what share of the samples matches?",
     "Click `feeSlow` to zoom in. Find the widest box that has nothing above it.",
     "Predict before checking: if you moved `Pattern.compile(...)` into a `static final` field, which boxes would disappear, and roughly how much narrower would `feeSlow` get?"
    ],
    "expect": "The search shows a match share in the bottom-right corner; in the profile the figure comes from, `Pattern.compile` and `Pattern.matcher` alone came to about 22% of all samples. The widest exposed tops sit inside `Formatter`, `Pattern` and `BigDecimal`. Hoisting the pattern removes the `Pattern.compile` tower (about 18% of samples) but keeps `Pattern.matcher`, which still allocates a `Matcher` per call. That's exactly what lesson 7 finds."
   },
   "refs": [
    {"title": "Interpreting a flame graph (async-profiler docs)", "url": "https://github.com/async-profiler/async-profiler/blob/master/docs/FlamegraphInterpretation.md", "kind": "read"}
   ]
  },
  {
   "h": "Pick the mode: cpu, wall, alloc or lock",
   "body": "A flame graph shows samples of something. The mode decides what. async-profiler's main modes:\n\n| Mode | A sample means | Use it for |\n|---|---|---|\n| `cpu` (default) | the thread was running on a CPU | where CPU time goes |\n| `wall` | the thread existed, running or not | latency: where a request waits (I/O, locks, sleep) |\n| `alloc` | the thread allocated memory | who creates the garbage |\n| `lock` | the thread waited to enter a lock | contention |\n\n`cpu` mode takes stacks from Linux `perf_events`. Those can be blocked, for example when `/proc/sys/kernel/perf_event_paranoid` is 2 or higher or in some containers. Then `-e ctimer` gives similar results from a timer, without kernel frames. `wall` samples every thread equally whether it runs, sleeps or blocks, and the docs recommend it per thread: `asprof -e wall -t -i 50ms -f wall.html <pid>`. For a payment API that is slow because it waits on an issuer, `wall` is the right mode and `cpu` is nearly empty.\n\nIn `alloc` mode, \"the top frame of every call trace is the class of the allocated object, and the counter is the heap pressure\". It hooks into HotSpot when an object is allocated in a new TLAB (a thread's private allocation buffer) or outside one, and it doesn't disturb escape analysis: objects the JIT scalar-replaced never show up. On the slow fee code, an alloc profile here put 37.4% of the allocated bytes under `Pattern.compile`, 27.9% under `String.format` and 12.3% under `toPlainString`. The top frames were `byte[]`, `int[]` and `boolean[]`: regex internals and string building. (The class names carry a short suffix in brackets; ignore it for now.)\n\n`lock` mode puts the class of the lock or monitor on top, and the counter is the nanoseconds spent waiting to enter it: `asprof -e lock -t -i 5ms -f lock.html <pid>`.\n\nYou can also load the profiler at start-up instead of attaching later, which is handy in a container: `-agentpath:/path/to/libasyncProfiler.so=start,event=cpu,file=cpu.collapsed,collapsed`. `-o collapsed` writes collapsed stacks instead of HTML, which is what the lab reads. `--all` turns on every mode at once; the docs say it's not recommended for production.",
   "try": {
    "title": "Who allocates, and who waits",
    "minutes": 4,
    "steps": [
     "Start `ProfileMe` again. Attach in alloc mode: `asprof -e alloc -d 5 -f alloc.html <pid>`.",
     "Before opening it, predict the three widest children of `feeSlow` in the allocation graph.",
     "Start `ProfileMe` once more and attach with `asprof -e wall -t -d 5 -f wall.html <pid>`. How does it differ from `cpu.html`?"
    ],
    "code": {"lang": "bash", "title": "terminal", "src": "asprof -e alloc -d 5 -f alloc.html <pid>\nasprof -e alloc -d 5 -o collapsed -f alloc.collapsed <pid>   # the same, as text\nasprof -e wall -t -d 5 -f wall.html <pid>", "run": ""},
    "expect": "In the allocation graph, `Pattern.compile` and `String.format` are the widest children of `feeSlow`, followed by `toPlainString`, and the top frames are array classes such as `byte[]` and `int[]`. The wall graph splits by thread (`-t`): the four `fees-` threads look much like the CPU profile because they never wait, while `main` sits in `Thread.join` the whole time. In a 3-second run here, `main` got 61 samples, exactly as many as each worker: wall mode samples every thread equally, and a CPU profile would ignore `main` completely."
   }
  }
 ],
 "analogy": "A sampling profiler is a manager who walks past the team's desks every ten seconds and notes what each person is working on. After a day, the tally says where the time went, without anyone filling in a timesheet. Safepoint bias is a manager who only looks up when someone stands up from their desk: they see people at the coffee machine and the printer, and they never see the long stretches of typing. async-profiler is a camera that takes a snapshot at a random moment, wherever people are. The analogy breaks at the end: the camera also sees the cleaners and the building's machinery, the GC and JIT threads, which a real manager would ignore.",
 "in_your_world": "Your Quarkus authorization service shows high CPU at peak. Attach async-profiler to one pod for 30 seconds in `cpu` mode and look for wide tops in your own packages: per-request `Pattern.compile` in a validator, `String.format` in a log statement that's disabled, JSON mapping you didn't expect. If the complaint is latency rather than CPU, use `wall -t` instead: a request thread waiting on the card issuer or a JDBC pool shows up there and not in `cpu`. In Kubernetes, `perf_events` is often blocked, so start with `-e ctimer`. Keep the HTML file with the incident notes. And since the profiler sees GC and JIT threads too, a wide G1 tower is a hint to go back to `alloc` mode.",
 "mistake": "The most common mistake is reading a flame graph as a timeline: \"first it validated the currency, then it formatted the log line\". Boxes at the same level are in alphabetical order, so left and right say nothing about when or in which order. The second mistake is optimizing the widest box at the bottom of the graph. A wide box covered by its children (`feeSlow` here) spends its time in those children, and making it faster on its own changes nothing. Look for wide exposed tops, then follow them down to the first frame in your own code: that's the line to change.\n\n```java\n// what the profile points at: the frame in your code under the wide top\nif (!Pattern.compile(\"^[A-Z]{3}$\").matcher(currency).matches()) { ... }\n```\n\n```kotlin\n// what the profile points at: the frame in your code under the wide top\nrequire(Regex(\"^[A-Z]{3}$\").matches(currency)) { \"bad currency\" }\n```",
 "compare": {
  "title": "The hand-made sampler in Java and Kotlin",
  "java": {"title": "PoorMansProfiler.java", "src": SAMPLER_J},
  "kotlin": {"title": "PoorMansProfiler.kt", "src": SAMPLER_K},
  "note": "Both versions call the same JVM method, `Thread.getStackTrace()`, so both share its safepoint bias and its cost: each call stops the target thread briefly. The Kotlin twin's workload uses `Regex`, `BigDecimal` operators and the `format` extension, which call the same JDK classes, so its profile has the same hot spots with slightly different frame names, such as `kotlin.text.Regex.<init>` below `Pattern.compile`. Kotlin's frame names in profiles follow the compiled classes: top-level functions appear under the file class, such as `ProfileMeKt.kFeeSlow`."
 },
 "worked": {
  "title": "From a profile to the line to change",
  "steps": [
   {"say": "The authorization pods run hot. Attach to one for 30 seconds in CPU mode, as collapsed stacks so you can also grep them.", "code": "asprof -d 30 -e cpu -o collapsed -f /tmp/auth-cpu.collapsed <pid>\nasprof -d 30 -e cpu -f /tmp/auth-cpu.html <pid>", "lang": "bash"},
   {"say": "Find the widest self frames first: sort the collapsed lines by top frame. Here `Pattern.compile` and `Formatter.format` lead.", "code": "awk '{n=$NF; $NF=\"\"; k=split($0,f,\";\"); s[f[k]]+=n} END {for (x in s) print s[x], x}' /tmp/auth-cpu.collapsed | sort -rn | head -5", "lang": "bash"},
   {"say": "A JDK frame on top is rarely the thing to fix. Walk down each hot stack to the first frame in your own package. Self-check: why stop at your own frame and not at the JDK one? (You can't make `Pattern.compile` faster, but you can stop calling it per request.)", "code": "java/util/regex/Pattern.<init>   <- top, JDK\njava/util/regex/Pattern.compile  <- JDK\ncom.acme.pay.FeeService.fee      <- first frame you own: the line to change", "lang": "text"},
   {"say": "Fix one thing, profile again, and compare widths. Lesson 7 does exactly this and finds that the next hot spot only becomes visible after the first fix.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Build a flame graph from collapsed stacks",
  "minutes": 13,
  "files": [f"{lab}/main/{K}/FlameGraph.kt", f"{lab}/main/{K}/FlameNode.kt"],
  "run": "./gradlew :performance:test --tests 'workbench.performance.l06.*'",
  "steps": [
   "Run the tests. All five fail. The fixture is seven lines from a real async-profiler profile of the slow fee code.",
   "Write `parse`. Frame names can contain spaces (`itable stub`), so split on the last space.",
   "Write `selfTime` (count goes to the last frame) and `inclusiveTime` (count goes to every distinct frame in the stack, once).",
   "Write `build` with the `FlameNode` class provided: walk each stack from the root, adding the count to every node on the way. `FlameNode` keeps children sorted by name, like flamegraph.pl.",
   "Write `hottestPath`, then run the tests until all five pass. Optional: run your code on `build/poor-man.collapsed` from the first Try it."
  ],
  "hints": [
   "`line.lastIndexOf(' ')` splits the count off. `split(';')` gives the frames, root first.",
   "In the fixture, `Pattern.compile` appears twice in one stack (the public `compile(String)` and the private `compile()`). Counting it twice gives 1,290 instead of 645: use `frames.toSet()`.",
   "In `build`, start with `root.total += count`, then `node = node.child(frame); node.total += count` for each frame. Equal prefixes merge by themselves because `child` returns the existing node.",
   "`FlameNode.self` is already there: total minus the children's totals. You don't store it."
  ],
  "done_when": "All five tests in `FlameGraphTest` pass."
 },
 "drill": {
  "title": "Collapse and count from memory",
  "minutes": 4,
  "prompt": "Close this page. Given these collapsed lines, write down the self time and the inclusive time of `b`, and draw the flame graph as boxes with widths:\n\n```text\na;b;c 3\na;b 2\na;d;b 1\n```\n\nThen write the code that computes inclusive time from a list of samples.",
  "answer": {"lang": "java", "src": "// self(b) = 2 (only \"a;b\" ends in b); inclusive(b) = 3 + 2 + 1 = 6\n// flame graph, root at the bottom, children in alphabetical order:\n//   [c 3]          [b 1]\n//   [b    5     ][d  1 ]\n//   [a        6        ]\nstatic Map<String, Long> inclusive(List<Sample> samples) {\n    Map<String, Long> result = new HashMap<>();\n    for (Sample s : samples) {\n        for (String frame : new HashSet<>(s.frames())) {   // once per sample\n            result.merge(frame, s.count(), Long::sum);\n        }\n    }\n    return result;\n}",
             "alt": {"lang": "kotlin", "src": "// self(b) = 2 (only \"a;b\" ends in b); inclusive(b) = 3 + 2 + 1 = 6\n// flame graph, root at the bottom, children in alphabetical order:\n//   [c 3]          [b 1]\n//   [b    5     ][d  1 ]\n//   [a        6        ]\nfun inclusive(samples: List<Sample>): Map<String, Long> {\n    val result = HashMap<String, Long>()\n    for (s in samples) {\n        for (frame in s.frames.toSet()) result.merge(frame, s.count, Long::plus)   // once per sample\n    }\n    return result\n}"}}
 },
 "recap": [
  "A sampling profiler records thread stacks every few milliseconds and counts them. Collapsed stacks (`a;b;c 42`) are the common text format.",
  "Profilers built on `Thread.getStackTrace` or JVMTI only see threads at safepoint polls, so samples land on the next poll: safepoint bias.",
  "async-profiler interrupts threads with signals and walks the stack where the signal landed, and it also sees native, JVM, GC, JIT and kernel frames.",
  "In a flame graph, width is samples, the root is at the bottom and the x-axis is alphabetical, not time. Wide exposed tops are self time; follow them down to your own code.",
  "Pick the mode for the question: `cpu` for CPU time, `wall -t` for waiting, `alloc` for who allocates, `lock` for contention. Use `-e ctimer` when perf_events is blocked."
 ],
 "quiz": [
  {"q": "A request is slow because each one waits 120 ms for the card issuer. The CPU flame graph of the service barely shows the request path. Which mode shows the wait?",
   "options": ["`-e cpu` with a shorter interval", "`-e wall -t`", "`-e alloc`", "`-e lock`"],
   "answer": 1,
   "why": "`wall` samples every thread at the same rate whether it runs, sleeps or blocks, so a thread waiting on a socket shows up. CPU sampling only sees threads that are running, and the issuer wait isn't a Java lock, so `lock` won't show it either."},
  {"q": "In a flame graph, `FeeService.fee` is a very wide box, completely covered by `String.format` and `Pattern.compile` above it. Where is the time?",
   "options": ["In `FeeService.fee`'s own code", "In the frames above it: `fee` has no self time, so its callees do the work", "Spread evenly over the graph", "In the frames below it"],
   "answer": 1,
   "why": "Width is inclusive. A box with no exposed top has no self time. The fix is still in `fee`, because it's the frame in your code that calls `String.format` and `Pattern.compile`, but the CPU is in those callees."},
  {"q": "A profiler built on `Thread.getStackTrace()` blames 14% of the CPU on a method that only calls other methods. What's the most likely explanation?",
   "options": ["The method really does 14% of the work", "Safepoint bias: samples are taken where threads reach a safepoint poll, so time gets charged to wherever the next poll is", "Inlining makes the method slower", "The JIT removed the callees"],
   "answer": 1,
   "why": "`getStackTrace` on another thread needs that thread at a safepoint, and polls sit at method returns and loop back-edges. Time spent between polls is charged to the frame where the thread stopped. async-profiler samples at the exact instruction instead."},
  {"q": "You profile with `asprof -e alloc` and see no `Money` objects, although the code creates one per payment. What could explain it?",
   "options": ["The alloc mode only shows arrays", "The JIT scalar-replaced the `Money` objects after escape analysis, so they were never allocated on the heap", "Allocation profiles only cover the main thread", "async-profiler can't see application classes"],
   "answer": 1,
   "why": "async-profiler's docs say alloc mode doesn't disturb escape analysis and measures only real heap allocations. An object that never escapes its compiled method can be replaced by its fields in registers, so there's nothing to sample."},
  {"q": "From lesson 5: you need to know which methods allocate the most in a production pod, but you can't install async-profiler there. What's the closest built-in answer?",
   "options": ["`jfr view allocation-by-site` on a recording dumped with `jcmd <pid> JFR.dump`", "`-XX:+PrintCompilation`", "`jcmd <pid> Thread.print`", "A JMH benchmark with `-prof gc`"],
   "answer": 0,
   "why": "JFR samples allocations as `jdk.ObjectAllocationSample` events with stack traces, and the `allocation-by-site` view groups them by top frame. It's built into the JDK, so nothing needs installing. JMH measures code in isolation, not the pod.",
   "from": "perf-05"}
 ],
 "flashcards": [
  {"front": "What does a line of collapsed stacks look like?", "back": "`root;caller;callee 42`: frames from the root to the top separated by `;`, then the number of samples."},
  {"front": "Self time vs inclusive time of a frame?", "back": "Self: samples with the frame on top of the stack. Inclusive: samples with the frame anywhere on the stack."},
  {"front": "What is safepoint bias?", "back": "Profilers that use `getStackTrace`/JVMTI only see threads at safepoint polls, so samples land on the next poll instead of where the CPU was."},
  {"front": "In a flame graph, what does the x-axis order mean?", "back": "Nothing about time: frames at the same level are sorted alphabetically. Width is the number of samples."},
  {"front": "Which async-profiler mode shows where requests wait on I/O?", "back": "`wall` (ideally with `-t`), which samples threads whether they run, sleep or block."},
  {"front": "What's on top of each stack in async-profiler's alloc mode?", "back": "The class of the allocated object; the counter is the heap pressure."},
  {"front": "What do you do when async-profiler can't use perf_events (containers, perf_event_paranoid ≥ 2)?", "back": "Use `-e ctimer`, which samples CPU with a timer, without kernel frames."}
 ],
 "terms": [
  {"term": "Sampling profiler", "plain": "A profiler that records stacks at intervals and counts them, instead of timing every call."},
  {"term": "Collapsed stacks", "plain": "Text format: one line per distinct stack, frames joined by `;`, then a count."},
  {"term": "Self time", "plain": "Samples where a frame was on top of the stack, running its own code."},
  {"term": "Inclusive time", "plain": "Samples where a frame was anywhere on the stack, including its callees."},
  {"term": "Safepoint", "plain": "A point where the JVM knows a thread's full state and can stop it or read its stack."},
  {"term": "Safepoint bias", "plain": "Profiling error from only seeing threads at safepoint polls."},
  {"term": "Flame graph", "plain": "Stacks drawn as boxes: root at the bottom, width = samples, alphabetical left to right."}
 ],
 "explain_back": {
  "prompt": "Explain to a teammate how to read the flame graph of a slow service: what width, height and left-to-right position mean, and how you get from the picture to the line of code to change.",
  "answer": "Each box is a frame from the sampled stacks. Its width is how many samples had that frame there, so wide means a lot of time in it or in what it calls. Height is stack depth: callers below, callees above. Left to right means nothing, because frames at each level are just sorted alphabetically, so it's not a timeline. I look for wide tops, the parts of boxes with nothing above them: that's where the CPU really was. Then I follow that tower down to the first frame in our own code, because I usually can't make a JDK method faster, but I can stop calling it per request. Then I fix that one thing and profile again."
 },
 "deeper": {
  "minutes": 10,
  "body": "Before version 4.2, async-profiler took Java stacks with `AsyncGetCallTrace`, a HotSpot function that isn't part of any standard API. Its docs note that it \"was broken several times even in minor JDK updates\" and could crash the JVM, which is why 4.2 made its own walker over HotSpot's internal structures the default (`--cstack vm`). `vmx` mode goes further and interleaves Java and native frames in one stack.\n\n`-a` (or `--ann`) annotates frames by how they were compiled: `_[j]` for JIT-compiled methods, `_[i]` for inlined ones, `_[0]` for interpreted and `_[1]` for C1-compiled. That connects a profile back to lessons 1 and 2: a hot method stuck at `_[0]` or `_[1]` deserves a look with PrintCompilation.\n\nDifferential flame graphs compare two profiles. Brendan Gregg's FlameGraph tools colour frames \"red for more, and blue for less\", which is a quick way to see what a change did. Make both profiles the same length and under the same load, or the comparison measures traffic, not code.\n\nasync-profiler can also write JFR files (`-o jfr`) that JDK Mission Control opens, and convert them later with `jfrconv`. For CI, JMH's `-prof async:libPath=<path to libasyncProfiler.so>` runs it around a benchmark, so you get a flame graph of exactly the code you measured."
 },
 "sources": [
  {"title": "async-profiler: README, releases and docs", "url": "https://github.com/async-profiler/async-profiler"},
  {"title": "Profiling modes (async-profiler docs)", "url": "https://github.com/async-profiler/async-profiler/blob/master/docs/ProfilingModes.md"},
  {"title": "Interpreting a flame graph (async-profiler docs)", "url": "https://github.com/async-profiler/async-profiler/blob/master/docs/FlamegraphInterpretation.md"},
  {"title": "FlameGraph (Brendan Gregg's tools)", "url": "https://github.com/brendangregg/FlameGraph"}
 ]
}
out = ROOT / "content/lessons/perf-06.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
