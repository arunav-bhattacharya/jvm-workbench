import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/performance/src"
P = "java/workbench/performance/l01"
K = "kotlin/workbench/performance/l01"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :performance:demo -Pmain=workbench.performance.l01."

def demo(name, kname=None, title=None):
    kname = kname or name
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": DEMO + name, "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{kname}.kt", "src": read(f"{lab}/demo/{K}/{kname}.kt"),
                    "run": DEMO + kname + "Kt", "file": f"{lab}/demo/{K}/{kname}.kt"}}

FIG = """<svg viewBox="0 0 680 230" role="img" aria-label="One PrintCompilation line split into its columns: time, compile id, OSR flag, tier, method, loop bytecode index and bytecode size">
<text class="t-s t-m" x="20" y="22">40   10 %     4       Hot::longLoop @ 4 (27 bytes)</text>
<rect class="box" x="30" y="92" width="56" height="38" rx="8"/><text class="t t-code" x="58" y="116" text-anchor="middle">40</text>
<rect class="box" x="96" y="92" width="56" height="38" rx="8"/><text class="t t-code" x="124" y="116" text-anchor="middle">10</text>
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
<line class="ln-d" x1="538" y1="62" x2="538" y2="92"/><text class="t-s" x="560" y="56" text-anchor="middle">bytecode size</text>
<text class="t-s t-m" x="340" y="214" text-anchor="middle">a trailing message such as "made not entrant" can follow the size</text>
</svg>"""

L = {
 "id": "perf-01",
 "title": "From bytecode to machine code: interpreter, C1, C2",
 "minutes": 35,
 "goal": "By the end you can say which tier is running a method, read every column of a `-XX:+PrintCompilation` line, and explain OSR and why a fresh JVM is slow.",
 "warmup": {
  "q": "A `reconcileNight()` method is called once and loops over 3 million ledger rows. When does HotSpot compile it to machine code?",
  "options": [
   "Never: it is called once, far below any call threshold",
   "After 10,000 calls, so never on this run",
   "While the loop is still running: the JVM counts loop iterations too, and swaps compiled code into the running method",
   "Before it starts, when the class is loaded"
  ],
  "answer": 2,
  "why": "HotSpot counts loop back-edges as well as calls. A loop that has jumped back tens of thousands of times gets an on-stack replacement (OSR) compile, and the running frame moves into it mid-loop. The 10,000-call figure is `CompileThreshold`, which only applies with tiered compilation switched off."
 },
 "sections": [
  {
   "h": "Every method starts in the interpreter and earns its way to C2",
   "body": "HotSpot does not compile your code when a class loads. Every method starts in the **interpreter**, which runs the bytecode one instruction at a time. While it runs, the JVM counts how often the method is called and how often its loops jump back to the top (the back-edges). When the counts are high enough, a compiler thread turns the method into machine code in the background. The next call runs that code instead.\n\nThere are two compilers. C1 compiles quickly and optimizes a little. C2 compiles slowly and optimizes hard, using a profile of what the code really did. Tiered compilation, on by default, uses both, in five levels:\n\n| Tier | Runs the code | Notes |\n|---|---|---|\n| 0 | interpreter | counts calls and loop back-edges |\n| 1 | C1, no profiling | for trivial methods such as getters |\n| 2 | C1 with counters only | used when C2 has a backlog |\n| 3 | C1 with full profiling | records branch counts and the receiver types at each call |\n| 4 | C2 | compiles with the profile that tier 3 collected |\n\nThe normal path is 0, then 3, then 4. A method gets C1 with profiling after about 200 calls (`Tier3InvocationThreshold`) and C2 after about 5,000 more calls at tier 3 (`Tier4InvocationThreshold`). Loop iterations add to the count. When the compile queues are long, the JVM raises these thresholds on the fly, so treat them as orders of magnitude. The defaults are the same in every release from JDK 21 to JDK 27.\n\nTier 1 and tier 2 are side roads. A trivial method goes to tier 1 and stays there, because the HotSpot source says C2 would \"yield the same code\". Tier 2 skips most of the profiling, and the same source says it runs about 30% faster than tier 3, so the JVM uses it while C2 is busy.\n\nOld blog posts say a method is compiled after 10,000 calls. That is `CompileThreshold`, and it applies only when you turn tiered compilation off with `-XX:-TieredCompilation`.\n\nHere is a function that the JVM will run at three different speeds during one short program:\n\n```java\nstatic long feeCents(long amountCents) {\n    return (amountCents * 29 + 500) / 1000 + 30;   // 2.9% + 30 cents, rounded\n}\n```\n\n```kotlin\nfun feeCents(amountCents: Long): Long =\n    (amountCents * 29 + 500) / 1000 + 30           // 2.9% + 30 cents, rounded\n```",
   "try": {
    "title": "Watch the same batch get faster",
    "minutes": 4,
    "steps": [
     "Predict: `WarmupDemo` times the same batch of 20,000 fee calculations 12 times. Will batch 12 take as long as batch 1?",
     "Run it with the command below and note when the time drops.",
     "Run it again with `-Pargs=int`, which restarts it with `-Xint` (interpreter only), then with `-Pargs=c1` (`-XX:TieredStopAtLevel=1`, C1 only)."
    ],
    "code": demo("WarmupDemo"),
    "expect": "With the defaults, the first four or so batches take a few hundred microseconds each, then the time falls to tens of microseconds once compiled code takes over the loop. One run here went from about 500 us to 60 us. With `int` every batch stays near 500 us. With `c1` it also gets fast, a little behind the default on this tiny function. The drop comes around batch 4 or 5, not batch 2: `batch()` is called only 12 times, so it's the loop that gets compiled, as the OSR section explains. Your numbers will differ, the shape won't."
   }
  },
  {
   "h": "Reading -XX:+PrintCompilation line by line",
   "body": "`-XX:+PrintCompilation` prints one line each time a compile finishes, and another when the JVM stops using compiled code. These are real lines from the small program `Hot` (in the Try it below) on JDK 21:\n\n```text\n40    8 %     3       Hot::longLoop @ 4 (27 bytes)\n40    9       3       Hot::longLoop (27 bytes)\n40   10 %     4       Hot::longLoop @ 4 (27 bytes)\n42    8 %     3       Hot::longLoop @ 4 (27 bytes)   made not entrant\n79   14       2       Hot$Square::area (10 bytes)\n88   18       4       Hot::total (42 bytes)\n```\n\nRead the third line from left to right. It finished 40 ms after the JVM started. Its compile id is 10. The `%` says it's an OSR compile, the `4` says C2 did it, and `@ 4` says the compiled code is entered at bytecode index 4. The last number, `(27 bytes)`, is the size of the method's **bytecode**, not of the machine code. Lesson 2 shows why that number matters: inlining limits are counted in these bytes.\n\nThe five characters after the id are attribute flags: `%` for OSR, `s` for a synchronized method, `!` for a method with an exception handler, `b` for a blocking compile and `n` for a native wrapper. A real `s` line looks like `58   25  s    3       Flags::syncInc (9 bytes)`.\n\nThe compile id ties lines together. The fourth line repeats id 8 with `made not entrant`: the JVM stopped using that code, and new calls won't enter it. Most of these lines are routine. Tier 3 code is retired as soon as a tier 4 version takes over. On JDK 25 the JVM also prints the reason, after a colon:\n\n```text\nmade not entrant: OSR invalidation of lower levels   // C2 OSR code replaced the C1 OSR code\nmade not entrant: not used                           // a newer compile of the method replaced it\nmade not entrant: uncommon trap                      // a C2 assumption failed (lesson 2)\n```\n\nTwo warnings before you go hunting in logs. First, the timestamps and ids change from run to run: in three identical runs, the first OSR compile of `longLoop` landed at 40, 47 and 60 ms. The compile policy depends on queue lengths, so never diff two logs line by line. Second, the JDK's own methods (`String::hashCode`, `Object::<init>`) are compiled too, so filter by your package.",
   "figure": {"svg": FIG, "caption": "One OSR line from PrintCompilation, column by column. The size is bytecode, not machine code."},
   "try": {
    "title": "Read the log of a running program",
    "minutes": 5,
    "steps": [
     "Read `Hot`. Predict which of `longLoop`, `total` and `Square::area` will reach tier 4, and which will be compiled with `%`.",
     "Run it. The demo starts a second JVM with `-XX:+PrintCompilation` and keeps only the lines for this lesson's classes.",
     "Find the compile id of the first tier 4 compile of `total`, then the later line where that id is made not entrant. What did the program do just before?",
     "Run the Kotlin twin and compare the `(N bytes)` sizes. Add `-Pargs=all` to either one to see every line the JVM prints."
    ],
    "code": demo("Hot"),
    "expect": "`longLoop` gets `%` lines at tier 3 and then tier 4 before the program prints 1251976370825152. `total` reaches tier 4, then that compile is made not entrant right after the `Circle` and `Tri` objects appear, and a new tier 4 compile with a higher id follows. On JDK 25 you also see the reasons. The Kotlin twin compiles to almost the same bytecode: 27 bytes for `longLoop` and 43 for `total`, against 42 in Java."
   }
  },
  {
   "h": "OSR compiles a loop while it is still running",
   "body": "`longLoop` is called once. It never gets near 200 calls, yet it was the first method compiled. If the JVM only counted calls, a method stuck in a long loop would stay in the interpreter forever. So it also counts back-edges. When one loop has jumped back about 60,000 times (`Tier3BackEdgeThreshold`), the JVM compiles a version of the method that starts at the loop. It then moves the running frame, with its local variables, into that code. This is **on-stack replacement** (OSR). C2 does the same at tier 4 after about 40,000 more back-edges (`Tier4BackEdgeThreshold`).\n\nThe `@ 4` points at the loop header. `javap -c` shows it:\n\n```text\nstatic long longLoop();\n   0: lconst_0\n   1: lstore_0\n   2: iconst_0\n   3: istore_2\n   4: iload_2                 // loop header: the OSR code is entered here\n   5: ldc     #13             // int 50000000\n   7: if_icmpge 25            // loop exit test\n  ...\n  22: goto    4\n```\n\nJDK 25 tells the rest of the story. These are real lines for the same method:\n\n```text\n23   14 %     3       workbench.performance.l01.Hot::longLoop @ 4 (27 bytes)\n23   16 %     4       workbench.performance.l01.Hot::longLoop @ 4 (27 bytes)\n25   14 %     3       workbench.performance.l01.Hot::longLoop @ 4 (27 bytes)   made not entrant: OSR invalidation of lower levels\n40   16 %     4       workbench.performance.l01.Hot::longLoop @ 4 (27 bytes)   made not entrant: uncommon trap\n```\n\nThe first `made not entrant` is housekeeping: once the C2 OSR code exists, the JVM retires the C1 one. The second is more interesting. When the loop ends at 40 ms, the C2 code throws itself away. `-Xlog:deoptimization=debug` says why: `trap_bci=7 osr_bci=4 unstable_if reinterpret`. Bytecode 7 is the exit test. While C1 profiled the loop, the exit branch had never been taken, so C2 didn't compile the exit at all. It put an **uncommon trap** there instead: a small stub that sends the frame back to the interpreter if the branch it never saw ever runs. It ran once, at the very end. That cost nothing here, and it's the JIT's betting habit in miniature. Lesson 2 is about those bets.\n\nOSR matters to you for one practical reason. A benchmark written as one long loop in `main` measures OSR code and its quirks, not the code your service runs after warm-up. JMH, in lesson 3, avoids that trap.",
   "try": {
    "title": "Find the loop and the trap",
    "minutes": 4,
    "steps": [
     "Run the `Hot` demo once so Gradle compiles it.",
     "From `labs/`, print the bytecode of `longLoop` with the first command below. Find index 4 and index 7.",
     "Run the second command. It starts `Hot` directly with the deoptimization log on. Find the `longLoop` line and the `total` lines."
    ],
    "code": {"lang": "bash", "title": "terminal", "src": "javap -c -p -cp performance/build/classes/java/demo workbench.performance.l01.Hot | grep -A 20 'long longLoop'\n\njava -Xlog:deoptimization=debug -cp performance/build/classes/java/demo workbench.performance.l01.Hot child", "run": ""},
    "expect": "Index 4 is `iload_2`, the top of the loop, and index 7 is `if_icmpge 25`, the exit test. The log has one line for `longLoop` with `trap_bci=7 osr_bci=4 unstable_if`, printed when the loop ends, and several lines for `total` with `trap_bci=27 class_check maybe_recompile`. Bytecode 27 in `total` is the `area()` call. That second kind of trap is the topic of lesson 2."
   }
  },
  {
   "h": "Compiled code lives in the code cache, and every new JVM starts cold",
   "body": "Machine code needs somewhere to live. HotSpot keeps it in the **code cache**, a memory region outside the Java heap. With tiered compilation the default is 240 MB reserved (`ReservedCodeCacheSize`), split into three heaps. `-XX:+PrintCodeCache` on JDK 25 shows them:\n\n```text\nCodeHeap 'non-profiled nmethods': size=120036Kb used=2Kb max_used=2Kb free=120033Kb\nCodeHeap 'profiled nmethods': size=120028Kb used=5Kb max_used=5Kb free=120022Kb\nCodeHeap 'non-nmethods': size=5696Kb used=1253Kb max_used=1267Kb free=4442Kb\nCodeCache: size=245760Kb, used=1260Kb, max_used=1274Kb, free=244497Kb\n```\n\nTier 2 and tier 3 code goes into 'profiled nmethods'. Tier 1 and tier 4 code goes into 'non-profiled nmethods'. Stubs and adapters, the glue the interpreter and compiled code need, live in 'non-nmethods'. If one heap fills, the JVM warns `CodeHeap 'non-profiled nmethods' is full. Compiler has been disabled.`, stops starting new compiles and schedules a clean-up so it can start again later. Until then, methods that aren't compiled stay in the interpreter. You can check a live JVM with `jcmd <pid> Compiler.codecache`. Do that before you raise the size.\n\nThe bigger cost for a service is that every JVM learns from scratch. Nothing from yesterday's process survives a restart. After a deploy, the first thousands of requests to a new pod run in the interpreter and in C1, and the hot paths reach C2 only after they've been called thousands of times. The compiler threads also share the pod's CPUs with your request threads. So a new pod is slower for a while after it starts, and a rolling deploy shows up as a bump in p99 latency.\n\nThere are two usual fixes. You can send synthetic warm-up traffic to the pod before its readiness probe passes, so real users never hit the cold code. Or, on JDK 25, you can record a training run into an AOT cache: JEP 515 adds method profiles to that cache, so the next JVM starts with the profiles from the training run instead of an empty one. The startup track covers the AOT cache.\n\nOne rule follows for every measurement in this track. A number taken in the first seconds of a JVM measures the interpreter and C1, plus the compiler's own work. Measure after warm-up, or say clearly that you measured a cold start.",
   "try": {
    "title": "Look inside the code cache",
    "minutes": 3,
    "steps": [
     "Run the first command. It starts a JVM that does nothing and prints the code cache at exit.",
     "Run the second one, which prints the code cache after `Hot` has run. Compare the `used=` numbers.",
     "Optional: start any demo that runs for a while, find its pid with `jcmd -l`, and run `jcmd <pid> Compiler.codecache` against it."
    ],
    "code": {"lang": "bash", "title": "terminal", "src": "java -XX:+PrintCodeCache -version\n\njava -XX:+PrintCodeCache -cp performance/build/classes/java/demo workbench.performance.l01.Hot child", "run": ""},
    "expect": "Three heaps of about 117 MB, 117 MB and 5.6 MB, 240 MB in total. With `-version`, only a few KB of compiled methods are used. After `Hot`, the two method heaps hold more, because `Hot` and the JDK methods it called were compiled. Even then it's a tiny part of 240 MB."
   },
   "refs": [
    {"title": "JEP 515: Ahead-of-Time Method Profiling", "url": "https://openjdk.org/jeps/515", "kind": "read"}
   ]
  }
 ],
 "analogy": "Think of a card-payment risk engine. A new merchant starts in manual review: every transaction is checked by hand, slowly (the interpreter). After a couple of hundred transactions the merchant moves to automatic approval with full logging, so the team can see what normal looks like (C1 at tier 3, collecting the profile). After a few thousand, a tuned fast path takes over that trusts the merchant's history (C2). If something the history never showed happens, the merchant goes back to review and a new model gets built (an uncommon trap, then a recompile). The analogy breaks in two places. A risk team keeps its history across restarts, while a JVM forgets everything when the process ends. And the JIT doesn't weigh risk at all: it bets that what it saw is all there is.",
 "in_your_world": "Your authorization endpoint on Quarkus has a p99 target of 150 ms. Every deploy, the dashboard shows a short bump: new pods answer their first requests slower than old ones did. That's the interpreter and C1 running code that the old pods ran in C2, plus the compiler threads competing with request threads for the pod's CPUs. Before you tune anything, check that the bump goes away within a minute or two. If it matters, warm the pod with synthetic authorizations before the readiness probe passes, or try the JDK 25 AOT cache in a staging environment. Don't load-test a pod that has just started and compare it to one that has been running for an hour.",
 "mistake": "The common mistake is timing code once, cold, and trusting the number. Someone writes a unit test that calls `formatAmount` with `System.nanoTime()` around it, sees 2 ms, and rewrites the method. They measured the interpreter, class loading and the compiler's own startup. The same call takes nanoseconds after warm-up. The fix is to measure after warm-up, with many iterations, and in a separate JVM from the one that ran other tests. Doing that by hand is full of traps, which is why lesson 3 uses JMH.\n\n```java\nlong t0 = System.nanoTime();\nformat(amount);                       // first call: interpreter, class loading\nlong coldNanos = System.nanoTime() - t0;\n```\n\n```kotlin\nval t0 = System.nanoTime()\nformat(amount)                        // first call: interpreter, class loading\nval coldNanos = System.nanoTime() - t0\n```",
 "compare": {
  "title": "The JIT sees bytecode, not Java or Kotlin",
  "java": {"title": "Hot.java", "src": "static double total(Shape[] shapes) {\n    double sum = 0;\n    for (Shape s : shapes) sum += s.area();\n    return sum;\n}\n// PrintCompilation: Hot::total (42 bytes)\n// OSR entry: @ 11"},
  "kotlin": {"title": "Hot.kt", "src": "fun total(shapes: Array<KShape>): Double {\n    var sum = 0.0\n    for (s in shapes) sum += s.area()\n    return sum\n}\n// PrintCompilation: HotKt::total (43 bytes)\n// OSR entry: @ 14"},
  "note": "Both loops compile to an indexed loop over the array with one `invokeinterface` call, so HotSpot treats them the same way: same tiers, same OSR, same throw-away when new shape types arrive. The only visible difference is a byte of bytecode and a different loop index. A Kotlin top-level function lives in a class named after the file (`HotKt`), and that's the name you'll grep for in logs. Where Kotlin really changes what the JIT sees is in `inline` functions and boxing, which come up in lesson 2."
 },
 "worked": {
  "title": "Read a PrintCompilation log for one method",
  "steps": [
   {"say": "Start by filtering. The JVM compiles hundreds of its own methods, so keep only the lines for your package and the program's own output.", "code": "java -XX:+PrintCompilation -cp app.jar com.acme.pay.Main | grep 'com.acme'", "lang": "bash"},
   {"say": "Find the OSR lines first. A `%` means a loop was hot enough to compile while it ran. Here `Hot::longLoop` got C1 OSR code (tier 3) and then C2 OSR code (tier 4) within the same millisecond.", "code": "40    8 %     3       Hot::longLoop @ 4 (27 bytes)\n40   10 %     4       Hot::longLoop @ 4 (27 bytes)\n42    8 %     3       Hot::longLoop @ 4 (27 bytes)   made not entrant", "lang": "text"},
   {"say": "Follow one compile id from birth to retirement. Id 18 is the first C2 version of `total`. It's made not entrant at 106 ms, and id 25 replaces it at the same moment. Ask what the program did just before: that's when the new shapes appeared.", "code": "88   18       4       Hot::total (42 bytes)\n106   18       4       Hot::total (42 bytes)   made not entrant\n106   25       4       Hot::total (42 bytes)", "lang": "text"},
   {"say": "Self-check: which compile of `total` is running at the end of the log? Answer: id 25, the last tier 4 compile whose id never appears again with `made not entrant`. That's the rule the lab asks you to code.", "code": "", "lang": ""},
   {"say": "On JDK 25, read the reason. `not used` and `OSR invalidation of lower levels` are routine. `uncommon trap` on a tier 4 line means C2 made a bet and lost. A few of those during warm-up are normal. The same method trapping again and again in a long-running service is worth a look.", "code": "60   27       4       Hot::total (42 bytes)   made not entrant: uncommon trap", "lang": "text"}
  ]
 },
 "lab": {
  "title": "Parse PrintCompilation output",
  "minutes": 14,
  "files": [f"{lab}/main/{K}/PrintCompilation.kt"],
  "run": "./gradlew :performance:test --tests 'workbench.performance.l01.*'",
  "steps": [
   "Run the tests once. All eight fail with `NotImplementedError`. The fixtures in `PrintCompilationTest` are real JDK 21 and JDK 25 output from `Hot`.",
   "Write `parse(line)`. Return `null` when the line isn't a compile line. Otherwise fill every field of `CompileEvent`: time, id, the five flag characters, tier, method, OSR index, bytes, and the message.",
   "Make it handle `(native)` instead of `(N bytes)`, a missing tier column (`-XX:-TieredCompilation`), and both `made not entrant` and `made not entrant: <reason>`.",
   "Write `parseAll`, then `deoptimizedFromC2` (tier 4 lines that were made not entrant) and `runningInC2` (normal tier 4 compiles whose id never shows up as made not entrant).",
   "Run the tests until all eight pass. Then run the `Hot` demo with `-Pargs=all`, paste a few lines into a test of your own, and check your parser on them."
  ],
  "hints": [
   "The layout is fixed: time, spaces, id, one space, exactly five flag characters, one space, then the tier digit and a space only when tiered compilation is on. A regex such as `^\\s*(\\d+)\\s+(\\d+) ([%s!bn ]{5}) (?:([0-4-]) )?\\s*(\\S+)...` gets you most of the way.",
   "Kotlin's `MatchResult.destructured` gives you the groups as strings. `toIntOrNull()` turns an empty optional group into `null` for free.",
   "For the reason, take what follows `made not entrant`, drop a leading colon and spaces, and use `null` when nothing is left.",
   "`runningInC2` needs two passes: first collect every compile id that was made not entrant, then keep tier 4, non-OSR lines whose id isn't in that set."
  ],
  "done_when": "All eight tests in `PrintCompilationTest` pass."
 },
 "drill": {
  "title": "Label a PrintCompilation line from memory",
  "minutes": 4,
  "prompt": "Close this page. On paper, label every part of this line, then write one sentence for each of tiers 0 to 4. Then check the answer.\n\n```text\n45   10 %     4       Hot::longLoop @ 4 (27 bytes)\n```",
  "answer": {"lang": "text", "src": "45            ms since the JVM started\n10            compile id (the same id appears again if this code is retired)\n%             OSR compile (other flags: s synchronized, ! exception handler, b blocking, n native)\n4             tier 4 = C2\nHot::longLoop class and method\n@ 4           OSR entry: bytecode index 4, the loop header\n(27 bytes)    size of the method's bytecode, not machine code\n\ntier 0  interpreter, counts calls and back-edges\ntier 1  C1 without profiling, for trivial methods\ntier 2  C1 with counters only, used while C2 is busy\ntier 3  C1 with full profiling (the usual step before C2)\ntier 4  C2, optimized with the tier 3 profile"}
 },
 "recap": [
  "HotSpot runs every method in the interpreter first, then compiles the hot ones: C1 with profiling (tier 3) after about 200 calls, C2 (tier 4) after about 5,000 more. The thresholds are the same from JDK 21 to 27 and grow when compile queues are long.",
  "A `-XX:+PrintCompilation` line reads: time, compile id, flags (`%` OSR, `s`, `!`, `b`, `n`), tier, method, `@ bci` for OSR, bytecode size, then an optional message.",
  "OSR compiles a loop while it runs and enters it at the loop header, so a method called once can still end up in C2.",
  "`made not entrant` means the JVM retired that compiled code. JDK 25 adds a reason: `not used` and `OSR invalidation of lower levels` are routine, `uncommon trap` means a C2 bet failed.",
  "Compiled code lives in a 240 MB code cache split into three heaps. Every new JVM starts cold, so measure after warm-up and warm services before they take traffic."
 ],
 "quiz": [
  {"q": "A batch job calls `rebuildBalances()` once, and it loops over 3 million ledger rows. What does `-XX:+PrintCompilation` most likely show for it?",
   "options": ["Nothing, since it is called only once", "One tier 4 line after 10,000 calls", "Lines with `%` and `@ <bci>`: OSR compiles of its loop at tier 3, then tier 4", "A single tier 1 line, because it is called rarely"],
   "answer": 2,
   "why": "The JVM counts loop back-edges as well as calls. After about 60,000 back-edges it compiles an OSR version of the method at tier 3, and C2 follows at tier 4. \"Called once\" only rules out normal, call-triggered compiles."},
  {"q": "On JDK 25, which line says that C2 code was thrown away because one of its assumptions failed?",
   "options": ["`42   22       2       Hot$Square::area (10 bytes)   made not entrant: not used`", "`25   14 %     3       Hot::longLoop @ 4 (27 bytes)   made not entrant: OSR invalidation of lower levels`", "`47   27       4       Hot::total (42 bytes)`", "`60   27       4       Hot::total (42 bytes)   made not entrant: uncommon trap`"],
   "answer": 3,
   "why": "Tier 4 plus `uncommon trap` means C2 hit a case it had compiled as \"never happens\" and handed the frame back to the interpreter. `not used` and `OSR invalidation of lower levels` are housekeeping: a newer or better compile replaced older code. The last line is a compile, not a retirement."},
  {"q": "What does `(42 bytes)` at the end of a PrintCompilation line measure?",
   "options": ["The size of the machine code C2 produced", "The size of the method's bytecode", "The stack frame size of the method", "How much memory one call allocates"],
   "answer": 1,
   "why": "The JVM prints `method->code_size()`, the bytecode length. Machine code is usually much larger. It matters because the inlining limits in lesson 2 are measured in bytecode bytes."},
  {"q": "A teammate's warm-up script calls the authorization endpoint exactly 10,000 times \"because HotSpot compiles after 10,000 calls\". On JDK 25 with default flags, what's wrong with that reasoning?",
   "options": ["Nothing, 10,000 is the default threshold", "Tiered compilation uses about 200 calls for tier 3 and about 5,000 more for tier 4, loops count too, and the thresholds grow when compile queues are long, so no fixed call count guarantees C2", "HotSpot only compiles methods marked `final`", "C2 is off by default since JDK 21"],
   "answer": 1,
   "why": "10,000 is `CompileThreshold`, used only with `-XX:-TieredCompilation`. With tiered compilation the triggers are different, and they scale with compiler load. Warm up until latency settles, not to a magic number."},
  {"q": "In the memory model track, a loop on a plain `boolean running` field spun forever, but it stopped when run with `-Xint`. In this lesson's terms, why?",
   "options": ["The interpreter re-reads the field on every iteration. The hang appears only after C2 (often via OSR) compiles the loop and keeps the value in a register", "`-Xint` makes every field volatile", "`-Xint` turns off the CPU caches", "The interpreter runs every thread on one core"],
   "answer": 0,
   "why": "Under `-Xint` the method never leaves tier 0, and the interpreter loads the field each time. The JIT is allowed to read a non-volatile field once and hoist it out of the loop. A hot loop reaches C2 through OSR even when the method is called once, which is exactly when the hang starts.",
   "from": "jmm-01"}
 ],
 "flashcards": [
  {"front": "Which compiler runs a method at tier 3, and what does it add?", "back": "C1, with full profiling: call and loop counters plus branch counts and receiver types at each call site. C2 uses that profile."},
  {"front": "Which compiler runs a method at tier 4?", "back": "C2, compiling with the profile that tier 3 collected."},
  {"front": "In a PrintCompilation line, what do `%` and `@ 4` mean?", "back": "`%` marks an OSR compile. `@ 4` is the bytecode index of the loop where the compiled code is entered."},
  {"front": "What is the number in `(27 bytes)` on a PrintCompilation line?", "back": "The method's bytecode size. Inlining limits are measured in these bytes."},
  {"front": "Roughly when does a method reach tier 3 and tier 4 on JDK 21 to 27?", "back": "About 200 calls for tier 3, then about 5,000 calls at tier 3 for tier 4. Loop iterations count too, and the bar rises when compile queues are long."},
  {"front": "What does `made not entrant` mean?", "back": "The JVM stopped using that compiled version; new calls won't enter it. JDK 25 prints the reason, such as `not used` or `uncommon trap`."},
  {"front": "How big is the code cache by default, and how do you inspect it on a live JVM?", "back": "240 MB reserved with tiered compilation, in three heaps. `jcmd <pid> Compiler.codecache`."}
 ],
 "terms": [
  {"term": "Interpreter", "plain": "Tier 0. Runs bytecode one instruction at a time and counts calls and loops."},
  {"term": "C1", "plain": "The fast, lightly optimizing JIT compiler. At tier 3 it also collects the profile."},
  {"term": "C2", "plain": "The slow, heavily optimizing JIT compiler (tier 4). It uses the profile to make bets."},
  {"term": "Tiered compilation", "plain": "Using the interpreter, C1 and C2 in sequence, on by default."},
  {"term": "OSR (on-stack replacement)", "plain": "Compiling a running loop and moving the live frame into the new code mid-loop."},
  {"term": "Profile (MDO)", "plain": "Per-method data the JVM records while profiling: branch counts, types seen at calls."},
  {"term": "Code cache", "plain": "Memory outside the heap that holds compiled code, 240 MB reserved by default."},
  {"term": "Made not entrant", "plain": "Compiled code the JVM has retired: new calls no longer enter it."}
 ],
 "explain_back": {
  "prompt": "A teammate asks why the first load test against a freshly deployed pod gave much worse numbers than the second one, five minutes later, with no code change. Explain it in your own words, using the tiers.",
  "answer": "A new JVM runs every method in the interpreter first. As methods get called and their loops run, the JVM compiles them, first with C1 while collecting a profile, then with C2 using that profile. That takes thousands of calls per hot method, and the compiler threads use the same CPUs as the request threads while they work. During the first load test most of the request path was still interpreted or in C1 code. Five minutes later the hot paths were running C2 code. Nothing carries over between JVMs, so every new pod goes through this again. Warm the pod before it takes traffic, and only compare measurements taken after warm-up."
 },
 "deeper": {
  "minutes": 10,
  "body": "PrintCompilation is the summary. For the full story, run with `-XX:+UnlockDiagnosticVMOptions -XX:+LogCompilation`, which writes an XML log of every compile decision, and open it in JITWatch, a log viewer for HotSpot's JIT. Its wiki says to add `-Xlog:class+load=info` so it can build its class model. To see the machine code too, add `-XX:+PrintAssembly`, which needs the hsdis disassembler library.\n\nA few `jcmd` commands help on a live JVM: `Compiler.queue` shows what's waiting to be compiled, `Compiler.codelist` lists the compiled methods, and `Compiler.codecache` shows the heaps. The number of compiler threads is chosen from the CPU count: `-XX:+PrintFlagsFinal` showed `CICompilerCount = 3` on a 4-CPU machine.\n\n`-XX:TieredStopAtLevel=1` (C1 only) compiles less and peaks lower. The HotSpot source describes it as mostly for testing. Keep it out of production.\n\nJDK 25 added two JEPs aimed at warm-up. JEP 514 makes the AOT cache easier to create, with `-XX:AOTCacheOutput=app.aot` on a training run and `-XX:AOTCache=app.aot` on later runs. JEP 515 stores method profiles in that cache, so a new JVM can start compiling hot methods with C2 sooner. I tried it on `WarmupDemo` packed into a jar (the cache refuses a directory on the classpath): the training run wrote an 11 MB cache, and in the next run the batches were fast from batch 3 instead of batch 5. That's one run on one machine, but the direction is the point. Compiling the code ahead of time is a separate, later step: JEP 544 is in the mainline for JDK 28, which isn't released yet. The startup track goes through all of this.\n\nOne more thing you may read about: \"made zombie\". Older JDKs printed that when retired code was finally freed. JDK 25 doesn't print it, so treat articles that show it as describing an older JVM."
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
