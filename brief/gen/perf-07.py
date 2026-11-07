import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/performance/src"
P = "java/workbench/performance/l07"
K = "kotlin/workbench/performance/l07"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :performance:demo -Pmain=workbench.performance.l07."

def demo(name, args=""):
    a = f" -Pargs={args}" if args else ""
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": DEMO + name + a, "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
                    "run": DEMO + name + "Kt" + a, "file": f"{lab}/demo/{K}/{name}.kt"}}

def box(cls, x, y, title, sub, w=190):
    return (f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="56" rx="8"/>'
            f'<text class="t" x="{x + w // 2}" y="{y + 23}" text-anchor="middle">{title}</text>'
            f'<text class="t-s t-m" x="{x + w // 2}" y="{y + 42}" text-anchor="middle">{sub}</text>\n')

FIG = ('<svg viewBox="0 0 680 250" role="img" aria-label="The investigation loop: a symptom in p99.99 and GC leads to a JFR recording, then a flame graph, then one fix, then a JMH run with -prof gc. Re-profile and repeat until the remaining allocation is real work, then lock the result in with a budget test in CI.">\n'
       + box("box-bad", 20, 30, "1. symptom", "p99.99, GC count")
       + box("box", 245, 30, "2. JFR", "what allocates, which line")
       + box("box", 470, 30, "3. flame graph", "who calls it")
       + box("box-a", 470, 160, "4. fix one thing", "hoist, guard, simplify")
       + box("box-b", 245, 160, "5. JMH -prof gc", "B/op before and after")
       + box("box-ok", 20, 160, "6. budget test", "fails CI if it grows")
       + '<line class="ln-a" x1="210" y1="58" x2="243" y2="58" marker-end="url(#arr)"/>\n'
         '<line class="ln-a" x1="435" y1="58" x2="468" y2="58" marker-end="url(#arr)"/>\n'
         '<line class="ln-a" x1="565" y1="86" x2="565" y2="158" marker-end="url(#arr)"/>\n'
         '<line class="ln-a" x1="470" y1="188" x2="437" y2="188" marker-end="url(#arr)"/>\n'
         '<line class="ln-a" x1="245" y1="188" x2="212" y2="188" marker-end="url(#arr)"/>\n'
         '<path class="ln-d" d="M340 160 L340 88" marker-end="url(#arr)"/>\n'
         '<text class="t-s t-b" x="348" y="128">re-profile</text>\n'
         '<text class="t-s t-ok" x="228" y="236" text-anchor="middle">done when what is left is real work</text>\n'
         '</svg>')

SLOW_J = """static long feeSlow(Payment p) {
    if (!Pattern.compile("^[A-Z]{3}$").matcher(p.currency()).matches())   // line 19
        throw new IllegalArgumentException("bad currency");
    BigDecimal amount = new BigDecimal(p.amount());
    BigDecimal fee = amount.multiply(new BigDecimal("0.029")).add(new BigDecimal("0.30"))  // line 22
            .setScale(2, RoundingMode.HALF_EVEN);
    debug(String.format("payment %s merchant=%s amount=%s fee=%s",        // line 24
            p.id(), p.merchant(), amount.toPlainString(), fee.toPlainString()));
    return fee.unscaledValue().longValue();
}"""
SLOW_K = """fun ktFeeSlow(p: KtPayment): Long {
    require(Regex("^[A-Z]{3}$").matches(p.currency)) { "bad currency" }   // a regex per call
    val amount = BigDecimal(p.amount)
    val fee = (amount * BigDecimal("0.029") + BigDecimal("0.30"))         // constants per call
        .setScale(2, RoundingMode.HALF_EVEN)
    ktDebug("payment %s merchant=%s amount=%s fee=%s"                      // formatted, then dropped
        .format(p.id, p.merchant, amount.toPlainString(), fee.toPlainString()))
    return fee.unscaledValue().toLong()
}"""
FIX_J = """static final BigDecimal RATE = new BigDecimal("0.029");      // round 1: built once
static final BigDecimal FIXED = new BigDecimal("0.30");

static boolean isCurrencyCode(String s) {                     // round 2: no regex for 3 letters
    if (s.length() != 3) return false;
    for (int i = 0; i < 3; i++) {
        char c = s.charAt(i);
        if (c < 'A' || c > 'Z') return false;
    }
    return true;
}

static long feeNoRegex(Payment p) {
    if (!isCurrencyCode(p.currency())) throw new IllegalArgumentException("bad currency");
    BigDecimal amount = new BigDecimal(p.amount());           // the work that's left
    BigDecimal fee = amount.multiply(RATE).add(FIXED).setScale(2, RoundingMode.HALF_EVEN);
    if (debugEnabled) debug(String.format("payment %s merchant=%s amount=%s fee=%s",   // round 1: guarded
            p.id(), p.merchant(), amount.toPlainString(), fee.toPlainString()));
    return fee.unscaledValue().longValue();
}"""
FIX_K = """val KT_RATE = BigDecimal("0.029")                            // round 1: built once
val KT_FIXED = BigDecimal("0.30")

fun isCurrencyCodeKt(s: String) = s.length == 3 && s.all { it in 'A'..'Z' }   // round 2: no regex

fun ktFeeNoRegex(p: KtPayment): Long {
    require(isCurrencyCodeKt(p.currency)) { "bad currency" }
    val amount = BigDecimal(p.amount)                         // the work that's left
    val fee = (amount * KT_RATE + KT_FIXED).setScale(2, RoundingMode.HALF_EVEN)
    if (ktDebugEnabled) ktDebug("payment %s merchant=%s amount=%s fee=%s"   // round 1: guarded
        .format(p.id, p.merchant, amount.toPlainString(), fee.toPlainString()))
    return fee.unscaledValue().toLong()
}"""

L = {
 "id": "perf-07",
 "title": "A performance investigation, start to finish",
 "minutes": 40,
 "goal": "By the end you can take a latency complaint from symptom to proof: read the tail and GC numbers, find the allocating lines with JFR, confirm callers with a flame graph, fix one thing at a time, and lock the result in with JMH and an allocation budget test.",
 "warmup": {
  "q": "A fee endpoint's average latency is 0.6 µs and its p99 is 3.9 µs, but its p99.99 is 13.6 ms. The service runs 130 garbage collections in 15 seconds. Where do you look first?",
  "options": [
   "The database, since slow requests are usually I/O",
   "Allocation: the rare slow calls are most likely waiting for GC pauses, and the GC runs because the code allocates a lot",
   "The JIT: 13.6 ms is a compilation",
   "Nowhere: p99.99 is noise"
  ],
  "answer": 1,
  "why": "Most calls are fast, and a few are three or four orders of magnitude slower. With 130 GCs in 15 seconds, the obvious suspect is a call that happens to wait for a stop-the-world pause. Fewer allocations mean fewer collections. There's no database in a fee calculation, and while compilation can slow early calls, it doesn't happen 130 times."
 },
 "sections": [
  {
   "h": "Start from the symptom: the tail and the GC, not the average",
   "body": "Here is the complaint, measured. Four threads call a card-fee calculation as fast as they can for 15 seconds, with a 256 MB heap, and every call is timed into a histogram. These are the research run's numbers on JDK 21:\n\n```text\n604,529 calls/s   p50 < 0.7 us   p99 < 3.9 us   p99.9 < 35.3 us   p99.99 < 13.6 ms\n130 GCs, 996 ms of GC time\n```\n\nThe average is excellent. One call in ten thousand takes over 13 ms, which in a payment API is the difference between a smooth checkout and a timeout somewhere upstream. `jfr view gc-pauses` on the same run said 129 pauses, 984 ms in total, median 2.98 ms. That's the first hypothesis: the slow calls are the ones that hit a pause, and the pauses happen because the code allocates.\n\nThe code looks harmless:\n\n```java\n" + SLOW_J + "\n```\n\n```kotlin\n" + SLOW_K + "\n```\n\nIt returns the right fee. Three costs hide in it: a regex compiled on every call, two `BigDecimal` constants built on every call, and a DEBUG log line formatted on every call and then dropped because DEBUG is off.\n\nOne caution before you change anything. The maximum latency stayed between 0.37 and 0.53 seconds in every version of this code, before and after the fixes. On a shared machine with four busy threads on four vCPUs, plus GC and JIT threads, the operating system sometimes doesn't schedule a thread for a while. Don't present the max as an effect of your fix. The percentiles are the evidence.",
   "try": {
    "title": "Reproduce the symptom",
    "minutes": 5,
    "steps": [
     "Read `FeeVariants.feeSlow` and `FeeInvestigation`. The demo starts a second JVM with `-Xmx256m` and a JFR recording, runs 4 threads for 3 seconds, then reads the recording.",
     "Predict: which line of `feeSlow` allocates the most?",
     "Run it with `-Pargs=slow`. Note the p99.99, the GC count and the top lines."
    ],
    "code": demo("FeeInvestigation", "slow"),
    "expect": "Around a million to four million calls per second on a laptop-class machine, p50 well under a microsecond, and a p99.99 hundreds or thousands of times the p50. Dozens of GCs or more in 3 seconds. The allocation by line puts lines 24 and 19 (`String.format` and `Pattern.compile`) at the top with about a third each, then line 25 (the `toPlainString` arguments) and line 22 (the constants). The latency numbers move a lot from run to run on a busy machine; the allocation shares hardly move."
   }
  },
  {
   "h": "JFR names the allocation, and the first line in your code names the fix",
   "body": "`jfr view allocation-by-site` on the slow run answers \"what allocates\" in JDK terms:\n\n```text\nFormatter.parse              12.48%\nPattern.compile()            10.34%\nPaymentSim.feeSlow           10.12%\nArrays.copyOf                 7.92%\nPattern$BitClass.<init>       7.80%\nMatcher.<init>                7.44%\n```\n\nThat's real, and not yet useful: you can't change `Formatter.parse`. The view groups by the top frame, the method that did the allocating. What you want is the first frame in your own code under it. Each `jdk.ObjectAllocationSample` event carries a stack trace and a `weight` (how many bytes the sample stands for), so a few lines of `RecordingFile`, as in lesson 5's lab, can group by your file and line instead. `FeeInvestigation` does that. One run:\n\n```text\nallocation by line in FeeVariants.java (from fees-slow.jfr):\n   36.0%  feeSlow line 24      String.format(...) for the dropped log line\n   32.6%  feeSlow line 19      Pattern.compile(...)\n   19.1%  feeSlow line 25      toPlainString() arguments for the log line\n    9.2%  feeSlow line 22      new BigDecimal(\"0.029\"), new BigDecimal(\"0.30\")\n```\n\nThe research run's own parser got the same order: 34.7% on the regex line, 31.9% on `String.format`, 15.9% on the `toPlainString` arguments, 8.9% on the constants. More than half of all allocation is a log line nobody reads.\n\nA flame graph answers the next question: who calls the allocating code, and through which path. In lesson 6's allocation profile of the same code, `Pattern.compile` held 37.4% of the allocated bytes and `String.format` 27.9%. Two independent tools agree, which is the point of using both. JFR is built in and cheap enough to leave running. async-profiler gives you the full picture, native and JVM frames included, when you can attach it.\n\nThe figure shows the loop this lesson follows. The step people skip is the dashed one.",
   "figure": {"svg": FIG, "caption": "The investigation loop: measure the tail, find the allocating line, fix one thing, prove it, re-profile, and stop when what is left is real work."},
   "try": {
    "title": "Compare the JDK view with the by-line view",
    "minutes": 3,
    "steps": [
     "After the previous Try it, run the command below on the recording it wrote.",
     "Find the JDK frames from the view (`Formatter.parse`, `Pattern.compile()`, `Matcher.<init>`) in the by-line list. Which line of `feeSlow` does each one come from?"
    ],
    "code": {"lang": "bash", "title": "terminal (from labs/)", "src": "jfr view allocation-by-site performance/build/fees-slow.jfr\njfr print --events jdk.ObjectAllocationSample --stack-depth 8 performance/build/fees-slow.jfr | head -30", "run": ""},
    "expect": "The view lists JDK methods such as `Formatter.parse`, `Pattern.compile()`, `Arrays.copyOf` and `Matcher.<init>` at the top. In `jfr print`, each sample shows `objectClass`, `weight` and a stack where, a few frames down, `FeeVariants.feeSlow` appears with its line number: 24 under the `Formatter` frames, 19 under the `Pattern` and `Matcher` frames."
   }
  },
  {
   "h": "Fix one thing, then profile again",
   "body": "Round 1 fixes the three obvious costs: the pattern and the two constants become `static final` fields, and the log line is formatted only when DEBUG is on. The research run went from 604,529 to 3,355,692 calls per second, p99.99 fell from under 13.6 ms to under 35.6 µs, and the GC count from 130 to 79.\n\nThen profile again, because the picture has changed. `FeeInvestigation -Pargs=hoisted` here:\n\n```text\nallocation by line in FeeVariants.java (from fees-hoisted.jfr):\n   75.4%  feeHoisted line 35      CCY.matcher(p.currency()).matches()\n   24.0%  feeHoisted line 36      new BigDecimal(p.amount())\n```\n\nThe research run put 94.8% on the same line. A precompiled `Pattern` still creates a new `Matcher` object on every call. That cost was there from the start, hidden under bigger ones. It only became the top line after round 1. Checking three letters doesn't need a regex at all, so round 2 replaces it with a plain loop:\n\n```java\n" + FIX_J + "\n```\n\n```kotlin\n" + FIX_K + "\n```\n\nAfter round 2 the research run did 4,292,668 calls per second, p99.99 under 28.4 µs, and 37 GCs. The re-profile here shows 99.9% of what's left on one line, `new BigDecimal(p.amount())`, parsing the amount string. That's the actual job, so this is where to stop, unless a budget says otherwise. Parsing cents by hand would remove it, and would also add rounding and validation code that someone has to get right.\n\nThree habits come out of this. Fix one thing at a time, so you know what each change did. Profile after every fix, because the order of costs changes. And stop when the top of the profile is the work the code exists to do.\n\nCheck yourself: in round 1 you hoist the `Pattern` but forget the log guard. Which line will lead the next profile? (The `String.format` line: about a third of the original allocation, and now the biggest share.)",
   "try": {
    "title": "Run all three rounds",
    "minutes": 4,
    "steps": [
     "Run `FeeInvestigation` with `-Pargs=hoisted`, then with `-Pargs=noregex`.",
     "For each, write down the top line, the p99.99 and the GC count, next to your numbers for `slow`.",
     "Run the Kotlin twin with `-Pargs=noregex`. Find the one allocation site the Java version doesn't have."
    ],
    "code": demo("FeeInvestigation", "hoisted"),
    "expect": "`hoisted` puts most of the remaining allocation on line 35 (the `Matcher`) and `noregex` puts almost all of it on line 55 (`new BigDecimal(p.amount())`). Throughput goes up several times and p99.99 drops to tens of microseconds, though the exact numbers vary a lot from run to run on a busy machine. The Kotlin twin's `noregex` run also shows a site in `main`'s lambda: the call through a `(KtPayment) -> Long` function type boxes every `Long` result (22.7% of the remaining allocation in one run)."
   }
  },
  {
   "h": "Prove it with JMH, then lock it in with an allocation budget",
   "body": "The investigation found the fix. JMH, from lesson 3, proves it in isolation, with `-prof gc`. The research run (2 forks of 5 one-second iterations):\n\n```text\nBenchmark                 ns/op                   B/op\nbefore                  845.880 ± 338.287    2,032.006 ± 0.002\nafter1_hoistAndGuard    149.884 ±  50.173      200.001 ± 0.001\nafter2_noRegex           62.337 ±  16.858       72.000 ± 0.001\n```\n\n`FeeBench` reproduces it: 2,032.012, 200.002 and 72.001 bytes per call in one run, with time errors larger than some of the scores. The time column tells you the fix helped. The B/op column tells you how much, to the byte. One subtlety: another fork of the same benchmark measured `before` at 2,112.011 B/op. Each JVM is precise, but two JVMs can differ a little, because the JIT can make different inlining and escape-analysis decisions. Leave room in any threshold.\n\nA benchmark proves the fix today. A test keeps it fixed. The JVM counts the bytes each thread allocates, and `com.sun.management.ThreadMXBean.getCurrentThreadAllocatedBytes()` reads that counter:\n\n```java\nvar threads = (com.sun.management.ThreadMXBean) ManagementFactory.getThreadMXBean();\nlong before = threads.getCurrentThreadAllocatedBytes();\nfor (int i = 0; i < 100_000; i++) sink += calc.feeCents(ps[i & 1023]);\ndouble perCall = (threads.getCurrentThreadAllocatedBytes() - before) / 100_000.0;\nassertThat(perCall).isLessThan(100);         // the budget\n```\n\n```kotlin\nval threads = ManagementFactory.getThreadMXBean() as com.sun.management.ThreadMXBean\nval before = threads.currentThreadAllocatedBytes\nrepeat(100_000) { sink += calc.feeCents(ps[it and 1023]) }\nval perCall = (threads.currentThreadAllocatedBytes - before) / 100_000.0\nassertThat(perCall).isLessThan(100.0)        // the budget\n```\n\nMeasure after warm-up, because allocation only settles once C2 has compiled the method and escape analysis has done its work. Measured this way, the slow version settles at 2,131.76 bytes per call. Round 1 settles at 200 bytes on JDK 21, and at 128 on JDK 25. Round 2 is 72 on both. Allocation numbers move with the JDK, so set the budget with a margin, and re-baseline it when you upgrade.",
   "try": {
    "title": "The proof, in bytes",
    "minutes": 4,
    "steps": [
     "Predict the B/op of each benchmark in `FeeBench`, using what the investigation showed.",
     "Run it (about 10 seconds). Compare the error columns for time and for bytes.",
     "Run the Kotlin twin, which measures the Kotlin versions with the per-thread allocation counter, like the lab's test."
    ],
    "code": demo("FeeBench"),
    "expect": "About 2,000 B/op for `before`, 200 for `after1Hoisted` and 72 for `after2NoRegex`, each with an error well under one byte, while the ns/op errors are large on a busy machine. The Kotlin twin printed 2,080, 280 and 72 bytes per call in one run. The middle number is 80 bytes more than Java's round 1, which is a good reason to measure each language's version instead of assuming they match."
   }
  }
 ],
 "analogy": "A performance investigation is like finding why a warehouse's late shipments come in bursts. You don't start by timing the average packer; you look at the late ones and notice they all coincide with the moments the floor is closed for cleaning (the GC pauses). Then you find what makes so much mess: a team that unpacks every box to check one label (the regex), another that prints a report nobody reads (the dropped log line). You fix one team, check the floor again, and only then notice the next mess that was hidden behind the first. The analogy breaks at the end: in a warehouse you'd stop at \"less mess\". In code you can measure the remaining mess to the byte and fail the build if it grows.",
 "in_your_world": "Every Quarkus payment service has some version of this code: a validator that compiles a regex per request, `BigDecimal` constants created inline in fee or FX rules, a `log.debug(String.format(...))` or string concatenation in a hot path with DEBUG off in production. When p99 or p99.99 of an endpoint drifts, run the loop: a JFR recording from one pod, `gc-pauses` and allocation by your own lines, an async-profiler flame graph if you can attach, one fix, a JMH benchmark with `-prof gc` for the PR, and an allocation budget test so the next refactoring can't silently bring the cost back. Put the JDK version next to the budget: allocation numbers changed between JDK 21 and 25 in this very example.",
 "mistake": "The most common mistake is changing several things at once and declaring victory on the average. Someone hoists the pattern, switches the JSON library and bumps the heap in one PR, the mean latency drops, and nobody knows which change mattered, or whether the tail got better at all. The other mistake is stopping after the first fix: in this investigation the `Matcher` allocation only became visible after the pattern was hoisted. Fix one thing, measure the tail and the allocation, profile again, and write down each round's numbers.\n\n```java\n// \"it's precompiled now\" is not the end: matcher() still allocates on every call\nif (!CCY.matcher(p.currency()).matches()) throw new IllegalArgumentException(\"bad currency\");\n```\n\n```kotlin\n// \"it's precompiled now\" is not the end: matches() still creates a Matcher on every call\nrequire(KT_CCY.matches(p.currency)) { \"bad currency\" }\n```",
 "compare": {
  "title": "The fixed fee calculation in Java and Kotlin",
  "java": {"title": "FeeVariants.java", "src": FIX_J},
  "kotlin": {"title": "FeeInvestigation.kt", "src": FIX_K},
  "note": "After round 2 both versions allocate the same 72 bytes per call, all of it in `new BigDecimal(p.amount())`. Two Kotlin details showed up on the way. Round 1 measured 280 bytes per call in Kotlin against 200 in Java. `Regex.matches` delegates to a `Matcher` just like the Java code, and this course didn't track down the extra 80 bytes, so measure instead of assuming the two versions cost the same. And calling the fee function through a function type, `val fee: (KtPayment) -> Long`, boxed every `Long` result: `Function1.invoke` returns an object. In the `noregex` run that boxing was 22.7% of the remaining allocation. In hot Kotlin code, call the function directly, pass it to an `inline` function, or use a `fun interface` with a primitive return type, the Kotlin counterpart of Java's `ToLongFunction`."
 },
 "worked": {
  "title": "Write up the investigation for the pull request",
  "steps": [
   {"say": "Start with the symptom and how you measured it, with the conditions. Without the conditions, the numbers mean nothing to a reviewer.", "code": "Symptom: fee endpoint p99.99 < 13.6 ms (p50 < 0.7 us); 130 GCs / 15 s.\nSetup: 4 threads, 15 s, -Xmx256m, JDK 21, 4-vCPU VM, latency histogram per call.", "lang": "text"},
   {"say": "Then the evidence for the cause, from two tools, with the lines named.", "code": "JFR jdk.ObjectAllocationSample, first frame in our code:\n  34.7% Pattern.compile (regex per call)\n  31.9% String.format   (DEBUG line, DEBUG off)\n  15.9% toPlainString   (arguments of that log line)\n   8.9% new BigDecimal(\"0.029\") / (\"0.30\")\nasync-profiler alloc: Pattern.compile 37.4%, String.format 27.9% of bytes", "lang": "text"},
   {"say": "Then each round separately, with the re-profile that justified the next one. Self-check: why list round 1 even though round 2 includes it? (Because the reviewer should see that the Matcher cost was found by measuring, not guessed, and what each change bought.)", "code": "Round 1 (hoist pattern + constants, guard log): p99.99 < 35.6 us, 79 GCs.\n  Re-profile: 94.8% of allocation now at CCY.matcher(...).\nRound 2 (3-char check instead of regex): p99.99 < 28.4 us, 37 GCs.\n  Re-profile: 99.7% at new BigDecimal(p.amount()). Stopping here.", "lang": "text"},
   {"say": "End with the proof and the guard: the JMH numbers with errors, and the test that keeps it fixed.", "code": "JMH -prof gc (2 forks x 5 x 1 s): before 2,032.006 +/- 0.002 B/op, after 72.000 +/- 0.001 B/op.\nFeeCalculatorTest.allocationBudget: < 100 B/call after warm-up (JDK 21 and 25: 72).", "lang": "text"}
  ]
 },
 "lab": {
  "title": "Bring the fee calculation under its allocation budget",
  "minutes": 15,
  "files": [f"{lab}/main/{P}/FeeCalculator.java"],
  "run": "./gradlew :performance:test --tests 'workbench.performance.l07.*'",
  "steps": [
   "Run the tests. Three pass (fees, currency check, DEBUG message) and one fails: the slow version settles at about 2,130 bytes per call, against a budget of 100.",
   "Optional but worth it: run `FeeInvestigation -Pargs=slow` and read the allocation by line. Your `FeeCalculator` has the same three costs.",
   "Round 1: make the pattern and the two `BigDecimal` constants `static final`, and format the DEBUG line only when `log.isDebugEnabled()`. Run the tests. The budget test still fails, now at about 200 bytes (128 on JDK 25). The failure message lists every round it measured.",
   "Round 2: replace the regex with a check that the currency is exactly three characters from A to Z. Run the tests until all four pass.",
   "Keep the fee results, the `bad currency` message and the exact DEBUG text: the other three tests guard them."
  ],
  "hints": [
   "`Pattern.compile(...)` in a `static final` field stops the compile, but `matcher()` still creates a `Matcher` per call. That's the 128 to 200 bytes left after round 1.",
   "The budget test measures 10 rounds of 100,000 calls and judges the best one, so a slow start while the JIT warms up won't fail it.",
   "For the currency: `s.length() == 3` and each `charAt(i)` between `'A'` and `'Z'`. Null isn't part of the contract here.",
   "What's left after round 2 is `new BigDecimal(p.amount())`, about 72 bytes. That's the real work, and it fits the budget."
  ],
  "done_when": "All four tests in `FeeCalculatorTest` pass."
 },
 "drill": {
  "title": "The investigation checklist, from memory",
  "minutes": 4,
  "prompt": "Close this page. Write down, in order, the steps you take from \"p99.99 of the fee endpoint is bad\" to a merged fix, naming the tool and the exact number you look at in each step. Then write the core of an allocation budget test.",
  "answer": {"lang": "java", "src": "// 1. symptom: latency percentiles (p99.9, p99.99) and GC count/time, not the average\n// 2. JFR: jfr view gc-pauses; allocation by the first frame in our code and its line (weight)\n// 3. flame graph (async-profiler -e alloc / cpu): who calls the allocating code\n// 4. fix ONE thing, re-run 1-3: the order of costs changes after each fix\n// 5. JMH -prof gc: gc.alloc.rate.norm (B/op) before and after, with its error\n// 6. allocation budget test in CI, with margin, re-baselined on JDK upgrades\nvar threads = (com.sun.management.ThreadMXBean) ManagementFactory.getThreadMXBean();\nfor (int i = 0; i < 200_000; i++) sink += calc.feeCents(ps[i & 1023]);   // warm up first\nlong before = threads.getCurrentThreadAllocatedBytes();\nfor (int i = 0; i < 100_000; i++) sink += calc.feeCents(ps[i & 1023]);\ndouble perCall = (threads.getCurrentThreadAllocatedBytes() - before) / 100_000.0;\nassertThat(perCall).isLessThan(100);",
             "alt": {"lang": "kotlin", "src": "// 1. symptom: latency percentiles (p99.9, p99.99) and GC count/time, not the average\n// 2. JFR: jfr view gc-pauses; allocation by the first frame in our code and its line (weight)\n// 3. flame graph (async-profiler -e alloc / cpu): who calls the allocating code\n// 4. fix ONE thing, re-run 1-3: the order of costs changes after each fix\n// 5. JMH -prof gc: gc.alloc.rate.norm (B/op) before and after, with its error\n// 6. allocation budget test in CI, with margin, re-baselined on JDK upgrades\nval threads = ManagementFactory.getThreadMXBean() as com.sun.management.ThreadMXBean\nrepeat(200_000) { sink += calc.feeCents(ps[it and 1023]) }             // warm up first\nval before = threads.currentThreadAllocatedBytes\nrepeat(100_000) { sink += calc.feeCents(ps[it and 1023]) }\nval perCall = (threads.currentThreadAllocatedBytes - before) / 100_000.0\nassertThat(perCall).isLessThan(100.0)"}}
 },
 "recap": [
  "Start from the tail (p99.9, p99.99) and the GC count. An excellent average can hide calls that wait for GC pauses, and the max is often noise from the machine.",
  "JFR's `allocation-by-site` names JDK methods; group samples by the first frame in your own code and its line to find what to change. A flame graph confirms who calls it.",
  "Fix one thing at a time and profile again: the order of costs changes, and the `Matcher` behind a hoisted `Pattern` only showed up after round 1.",
  "Stop when the top of the profile is the work the code exists to do, here parsing the amount: 72 bytes per call.",
  "Prove it with JMH `-prof gc` (2,032 to 72 B/op, errors under a byte) and keep it with an allocation budget test that has a margin, because numbers shift between JVMs and JDK versions."
 ],
 "quiz": [
  {"q": "After hoisting a `Pattern` into a `static final` field, a fee method still allocates 200 bytes per call, and the profile's top line is `CCY.matcher(currency).matches()`. Why?",
   "options": ["`matcher()` creates a new `Matcher` object on every call", "The pattern is still compiled per call", "`static final` fields are copied per thread", "The JIT can't inline `matches()`"],
   "answer": 0,
   "why": "Hoisting removes the compile, not the `Matcher`. Each `matcher(...)` call allocates a fresh `Matcher` with its own arrays. For a fixed three-letter check, a plain loop allocates nothing."},
  {"q": "A PR changes three things and reports \"average latency down 40%\". What should you ask for before approving?",
   "options": ["A bigger heap for the benchmark", "The percentiles and GC numbers before and after, and the effect of each change separately", "Nothing: 40% is a clear win", "A flame graph of the test suite"],
   "answer": 1,
   "why": "The average can improve while the tail stays bad, and with three changes at once nobody knows which one helped. Per-change numbers, including p99.9 or p99.99 and the GC count, are what make the claim checkable."},
  {"q": "`jfr view allocation-by-site` shows `Formatter.parse` on top. What's the next step to find the code to change?",
   "options": ["Optimize `Formatter.parse`", "Increase the young generation", "Group the allocation samples by the first frame in your own package and its line number", "Switch to `default.jfc`"],
   "answer": 2,
   "why": "The view groups by the top frame, which is the JDK method that allocated. The stack trace of each `jdk.ObjectAllocationSample` leads down to your code; the first frame in your package, with its line, is where the decision to call `String.format` was made."},
  {"q": "Your allocation budget test passes on JDK 21 at 72 bytes per call and your team upgrades to JDK 25. Round 1 of the same fix measured 200 bytes on JDK 21 and 128 on JDK 25. What does that tell you about budgets?",
   "options": ["Budgets are useless", "JDK 25 has a bug", "Budgets only work in JMH", "Allocation per call can change with the JDK, so set the budget with a margin and re-baseline it on upgrades"],
   "answer": 3,
   "why": "Library code such as `Matcher` changes between JDK versions, and so do JIT decisions. The budget still catches a regression in your code, as long as it leaves room and gets reviewed when the JDK changes."},
  {"q": "From lesson 3: in JMH runs of these fee versions, the ns/op error was often larger than the score, while the B/op error was under one byte. Why does B/op work as a CI check and ns/op doesn't?",
   "options": ["B/op is measured in a forked JVM and ns/op isn't", "For the same code and input, the bytes allocated per operation are the same every time; time depends on everything else running on the machine", "JMH rounds B/op to whole bytes", "ns/op is only meaningful with `@Fork(0)`"],
   "answer": 1,
   "why": "Allocation is a property of the code path, so it repeats exactly once the JIT has settled. Time includes CPU contention, frequency scaling, GC timing and noisy neighbours. A time threshold on a shared CI agent fails at random.",
   "from": "perf-03"}
 ],
 "flashcards": [
  {"front": "Which latency numbers show GC pauses hurting a few calls?", "back": "The tail percentiles (p99.9, p99.99) together with the GC count and pause times, not the average."},
  {"front": "`jfr view allocation-by-site` shows JDK methods. How do you find your line?", "back": "Walk each allocation sample's stack trace to the first frame in your own package and group by its method and line number, weighted by `weight`."},
  {"front": "Why profile again after each fix?", "back": "The order of costs changes. Smaller costs, such as the `Matcher` behind a hoisted `Pattern`, only become the top line after the bigger ones are gone."},
  {"front": "When do you stop optimizing an allocation hot spot?", "back": "When what's left is the work the code exists to do (here, parsing the amount) or when it fits the agreed budget."},
  {"front": "How do you measure allocation per call in a unit test?", "back": "Warm up, then read `com.sun.management.ThreadMXBean.getCurrentThreadAllocatedBytes()` before and after N calls and divide by N."},
  {"front": "Why does a Kotlin `(T) -> Long` cost allocation in a hot loop?", "back": "A function type is a generic `Function1`, so `invoke` returns an object and every `Long` result is boxed. Call directly, use `inline`, or a `fun interface` with a primitive return."}
 ],
 "terms": [
  {"term": "Tail latency", "plain": "The slowest calls, measured by high percentiles such as p99.9 and p99.99."},
  {"term": "Allocation budget", "plain": "A test that fails if a method allocates more than an agreed number of bytes per call."},
  {"term": "Allocation sample weight", "plain": "How many bytes a JFR allocation sample stands for; summing it gives allocation pressure."},
  {"term": "Re-profile", "plain": "Measuring again after a fix, because the order of costs has changed."},
  {"term": "Hoisting", "plain": "Moving work that doesn't change, such as compiling a pattern, out of the per-call path."},
  {"term": "Boxing", "plain": "Wrapping a primitive such as a `long` in an object such as `Long`, which allocates."}
 ],
 "explain_back": {
  "prompt": "Explain to a new teammate how you'd investigate \"the fee endpoint's p99.99 is bad\", from the first measurement to the merged fix, and why each step is there.",
  "answer": "First I'd measure the tail properly: percentiles and the GC count under a realistic load, because the average can look perfect while one call in ten thousand waits for a GC pause. If GC is busy, I take a JFR recording and look at gc-pauses and at allocation, grouped by the first frame in our own code, so I get file and line instead of JDK internals. A flame graph confirms who calls the allocating code. Then I fix one thing, the biggest, and measure again, because the order changes and new hot spots appear, like the Matcher behind a hoisted Pattern. I stop when what's left is the real work. Before merging I prove the change with a JMH benchmark using -prof gc, since bytes per operation are stable and time isn't, and I add an allocation budget test with some margin so a later change can't bring the cost back unnoticed."
 },
 "deeper": {
  "minutes": 10,
  "body": "The research run also tried one thing worth knowing about latency numbers. Its histogram used fixed buckets (100 ns up to 1 ms, then 100 µs up to 1 s) in a preallocated array, so measuring added no allocation of its own. A latency recorder that allocates per sample would add exactly the garbage you're trying to measure. HdrHistogram is the usual library for this in production.\n\nThe flame graph from lesson 6 showed 608 of 8,005 CPU samples in `__vdso_clock_gettime`: the harness calling `System.nanoTime()` around every request. Instrumentation has a cost, and on a 60 ns operation it's a large one. That's another reason the final proof is a JMH benchmark rather than the load harness.\n\nFor logging in Quarkus, the cheapest disabled log call is one that does nothing before checking the level. JBoss Logging's `debugf` formats only when DEBUG is on, but the arguments are still evaluated and a varargs call still builds its array. In a hot path, the explicit `if (log.isDebugEnabled())` guard is the version you can reason about. A profile will tell you if it matters.\n\nIf you want to go below 72 bytes, the remaining cost is `BigDecimal` parsing. Amounts in cents as `long`, parsed directly from the request, allocate nothing (lesson 3's `MoneyBench` measured 0 B/op for the summing part). That trades allocation for code you must keep correct: rounding modes, scale validation, overflow with `Math.multiplyExact`. Take that trade only if the budget or the profile asks for it."
 },
 "sources": [
  {"title": "jdk.jfr.consumer.RecordingFile (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/jdk.jfr/jdk/jfr/consumer/RecordingFile.html"},
  {"title": "com.sun.management.ThreadMXBean (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/jdk.management/com/sun/management/ThreadMXBean.html"},
  {"title": "Profiling modes: allocation profiling (async-profiler docs)", "url": "https://github.com/async-profiler/async-profiler/blob/master/docs/ProfilingModes.md"},
  {"title": "JMHSample_35_Profilers", "url": "https://github.com/openjdk/jmh/blob/master/jmh-samples/src/main/java/org/openjdk/jmh/samples/JMHSample_35_Profilers.java"}
 ]
}
out = ROOT / "content/lessons/perf-07.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
