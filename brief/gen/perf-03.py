import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/performance/src"
P = "java/workbench/performance/l03"
K = "kotlin/workbench/performance/l03"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :performance:demo -Pmain=workbench.performance.l03."

def demo(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": DEMO + name, "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
                    "run": DEMO + name + "Kt", "file": f"{lab}/demo/{K}/{name}.kt"}}

def row(y, label):
    s = f'<text class="t-s" x="20" y="{y + 23}">{label}</text>\n'
    s += f'<rect class="box-dim" x="70" y="{y}" width="86" height="36" rx="8"/><text class="t-s" x="113" y="{y + 23}" text-anchor="middle">new JVM</text>\n'
    for i in range(3):
        x = 166 + i * 44
        s += f'<rect class="box-b" x="{x}" y="{y}" width="36" height="36" rx="8"/><text class="t-s" x="{x + 18}" y="{y + 23}" text-anchor="middle">W</text>\n'
    for i in range(5):
        x = 306 + i * 44
        s += f'<rect class="box-a" x="{x}" y="{y}" width="36" height="36" rx="8"/><text class="t-s" x="{x + 18}" y="{y + 23}" text-anchor="middle">M</text>\n'
    s += f'<line class="ln-a" x1="528" y1="{y + 18}" x2="562" y2="{y + 18}" marker-end="url(#arr)"/>\n'
    return s

FIG = ('<svg viewBox="0 0 680 230" role="img" aria-label="A JMH run: each fork starts a new JVM, runs warm-up iterations whose results are thrown away, then measurement iterations whose results from all forks are combined into a score and error">\n'
       '<text class="t-s t-m" x="113" y="30" text-anchor="middle">clean profile</text>\n'
       '<text class="t-s t-b" x="232" y="30" text-anchor="middle">warm-up: thrown away</text>\n'
       '<text class="t-s t-a" x="412" y="30" text-anchor="middle">measurement: kept</text>\n'
       + row(48, "fork 1") + row(120, "fork 2") +
       '<rect class="box-ok" x="566" y="52" width="104" height="100" rx="8"/>\n'
       '<text class="t" x="618" y="98" text-anchor="middle">score</text>\n'
       '<text class="t-s" x="618" y="120" text-anchor="middle">± error</text>\n'
       '<text class="t-s t-m" x="340" y="200" text-anchor="middle">JMH 1.37 defaults: 5 forks, 5 warm-up and 5 measurement iterations of 10 s each</text>\n'
       '</svg>')

BENCH_J = """@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@Warmup(iterations = 5, time = 1)          // 5 x 1 s, results thrown away
@Measurement(iterations = 5, time = 1)     // 5 x 1 s, results kept
@Fork(2)                                   // two fresh JVMs
public class FeeBench {
    long amountCents = 123_456;            // input: a non-final field of the state object

    @Benchmark
    public long fee() {
        return FeeMath.feeCents(amountCents);   // returned: JMH consumes it
    }
}"""
BENCH_K = """@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@Warmup(iterations = 5, time = 1)
@Measurement(iterations = 5, time = 1)
@Fork(2)
open class FeeBench {                      // JMH's generated code extends it, so it can't be final
    var amountCents = 123_456L             // var: an input nobody can predict

    @Benchmark
    fun fee(): Long = FeeMath.feeCents(amountCents)
}"""

L = {
 "id": "perf-03",
 "title": "Benchmarking with JMH, and the traps it saves you from",
 "minutes": 38,
 "goal": "By the end you can explain why a `System.nanoTime()` loop lies, write a JMH benchmark that returns its result and reads real inputs, and use `-prof gc` to get a number stable enough to trust.",
 "warmup": {
  "q": "You time 100 million calls of `Math.sqrt(x)` in a loop with `System.nanoTime()` and throw each result away. After a few rounds the loop reports 0.0000 ns per call. What is the best explanation?",
  "options": [
   "Your CPU computes square roots in well under a nanosecond",
   "The JIT saw that the results were never used and removed the work from the loop",
   "`System.nanoTime()` is too coarse to measure such short calls",
   "The JVM cached the result of the first call"
  ],
  "answer": 1,
  "why": "No CPU does a square root in 0.0000 ns. Once C2 compiled the loop, it proved that nothing used the result of `Math.sqrt(x)` and deleted the call: dead-code elimination. `nanoTime()` resolution is fine for a 100-million-iteration loop, and the JVM has no result cache for `Math.sqrt`."
 },
 "sections": [
  {
   "h": "A nanoTime loop measures the optimizer, not your code",
   "body": "Here is the benchmark almost everyone writes first:\n\n```java\nlong t0 = System.nanoTime();\nfor (int i = 0; i < 100_000_000; i++) {\n    Math.sqrt(x);                      // result discarded\n}\nlong t1 = System.nanoTime();\nSystem.out.printf(\"%.4f ns/op%n\", (t1 - t0) / 1e8);\n```\n\n```kotlin\nval t0 = System.nanoTime()\nfor (i in 0 until 100_000_000) {\n    sqrt(x)                            // result discarded\n}\nval t1 = System.nanoTime()\nprintln(\"%.4f ns/op\".format((t1 - t0) / 1e8))\n```\n\nIt printed `0.0301`, then `0.1299`, then `0.0000` for every later round. A second loop that adds each result to a sum and prints the sum settled at about 1.9 ns per call. The JIT measured nothing in the first loop because, once C2 had compiled it, there was nothing left to measure. That is **dead-code elimination**: a computation whose result nobody uses can go.\n\nDead code is one of several ways a hand-made loop lies:\n\n- **Constant folding.** If the input is a constant, C2 can compute the answer at compile time and measure a constant load.\n- **Warm-up.** The first rounds run in the interpreter and in OSR code, as lesson 1 showed, and a benchmark that is one long loop in `main` keeps measuring OSR code.\n- **Loop effects.** JMH's own sample on loops reports the measured cost of an addition falling \"up to the point we do each addition with 1/20 ns, well beyond what hardware can actually do\", because the loop gets unrolled and work gets hoisted out of it.\n\nA wrong benchmark can also print a believable number, which is worse. On JDK 21, the same discarded loop with `Math.log` instead of `Math.sqrt` was not eliminated: it reported 7 to 9 ns per call, drifting upward from round to round. It looks plausible and still measures an accident of how C2 compiles `Math.log`. Whether the JIT can remove a call depends on what it can prove, and you can't see that from the outside.",
   "try": {
    "title": "Watch the work disappear",
    "minutes": 3,
    "steps": [
     "Read `NanoLoop`. Predict both columns for round 1 and round 5.",
     "Run it. Then run the Kotlin twin.",
     "Change the discarded loop to `Math.log(x)` in either version and run it again."
    ],
    "code": demo("NanoLoop"),
    "expect": "The discarded column starts near 0.03 ns and becomes 0.0000 by round 3; the used column stays near 2 ns. Kotlin does the same. With `Math.log`, the discarded loop typically reports several nanoseconds per call instead of zero: on JDK 21 x86_64 C2 doesn't remove that call. Neither loop tells you the real cost of the method."
   }
  },
  {
   "h": "JMH builds the measuring loop for you",
   "body": "JMH is the OpenJDK project's microbenchmark harness. Version 1.37, from August 2023, is still the latest release. You write a method annotated `@Benchmark`. JMH's annotation processor generates the measuring loop around it at compile time, written to defeat the tricks above, and a runner executes it in fresh JVMs.\n\nA complete benchmark:\n\n```java\n" + BENCH_J + "\n```\n\n```kotlin\n" + BENCH_K + "\n```\n\nThe Kotlin class has to be `open` because JMH's generated classes extend it, and the build needs a plugin such as kotlinx-benchmark to generate the JMH code for Kotlin classes. This course keeps its benchmarks in Java.\n\nWhat each piece does:\n\n- `@State(Scope.Thread)`: one instance per benchmark thread. Its fields are your inputs.\n- `@Setup`: prepares state outside the measured time. `Level.Trial`, the default, runs it once per fork.\n- `@Warmup` and `@Measurement`: iterations and their length. Warm-up results are thrown away.\n- `@Fork`: how many fresh JVMs to run in. A new JVM has a clean profile, so one benchmark can't skew the next. `@Fork(0)` runs inside the JVM that launched it, which brings back every problem of the hand-made loop.\n- `@BenchmarkMode`: `Throughput` (the default, operations per time), `AverageTime`, `SampleTime` or `SingleShotTime`.\n- `@Param`: runs the benchmark once per value, as lesson 2's `MegamorphicBench` did with `types`.\n\nThe JMH 1.37 defaults are 5 forks, each with 5 warm-up and 5 measurement iterations of 10 seconds: more than eight minutes per benchmark method. That's on purpose. The demos in this track use 100 to 300 ms iterations so they finish quickly. That's fine for seeing a trap and too short for deciding anything.\n\nYou can run benchmarks from a `main` method with JMH's `Runner` and `OptionsBuilder`, as the demos do, or from a JMH uber-jar with command-line flags such as `-f 2 -wi 5 -i 5 -prof gc`.",
   "figure": {"svg": FIG, "caption": "Each fork is a new JVM. Warm-up iterations are discarded; measurement iterations from every fork are combined into one score with an error."},
   "try": {
    "title": "Five ways to measure one square root",
    "minutes": 5,
    "steps": [
     "Read `TrapsBench`. Predict which of the five benchmarks will score about the same as `baseline`.",
     "Run it (under 10 seconds). Then run the Kotlin twin, which runs two of the five with JMH's full output so you can see the warm-up and measurement iterations go by.",
     "Change `double x = 2.0;` to `final double x = 2.0;` and run the Java version again. Which benchmark changes?"
    ],
    "code": demo("TrapsBench"),
    "expect": "`sqrtDiscarded` and `sqrtOfConstant` land on top of `baseline`, around 0.3 to 0.5 ns on the course VM. `sqrtReturned` and `sqrtBlackhole` are around 2 ns. With `final double x = 2.0`, javac copies `2.0` into every method, so `sqrtReturned` drops to the baseline as well. The Kotlin twin's log shows `# Blackhole mode: compiler (auto-detected ...)` and ends with JMH's \"REMEMBER: The numbers below are just data\" warning."
   }
  },
  {
   "h": "Consume every result and read inputs from non-final fields",
   "body": "Two rules fix most broken benchmarks.\n\nFirst, every result must reach JMH. The simplest way is to return it: JMH consumes return values. When there are two results, either combine them or pass each one to a `Blackhole`:\n\n```java\n@Benchmark\npublic void feeAndTax(Blackhole bh) {\n    bh.consume(FeeMath.feeCents(amountCents));\n    bh.consume(FeeMath.taxCents(amountCents));\n}\n```\n\n```kotlin\n@Benchmark\nfun feeAndTax(bh: Blackhole) {\n    bh.consume(FeeMath.feeCents(amountCents))\n    bh.consume(FeeMath.taxCents(amountCents))\n}\n```\n\nJMH's sample on Blackholes also says: if you have one result, return it, and \"Do not make your benchmark code less readable with explicit Blackholes!\" On JDK 17 and later JMH detects **compiler blackholes**, where the JIT itself treats `consume` as \"used, and nothing else\". The log says so in its header, and JMH warns that results from different Blackhole modes aren't comparable.\n\nSecond, inputs must come from non-final instance fields of the `@State` object. A `final` field with a constant initializer is a compile-time constant in Java, so javac copies the value into your method. `javap` on the lab's broken benchmark shows it:\n\n```text\npublic long fee();\n   0: ldc2_w  #7      // long 123456l   <- the field is gone, the number is baked in\n   3: invokestatic    FeeMath.feeCents:(J)J\n   6: lreturn\n```\n\nFrom there C2 can fold the whole fee calculation into one number. JMH's constant-folding sample puts it bluntly: \"IDEs will say 'Look, this field could be final'. Don't. Trust. Them.\" A `static final` input has the same problem, which is what `sqrtOfConstant` shows.\n\nYou can check both rules against a baseline. An empty `@Benchmark` method measures the harness alone (about 0.4 ns on the course VM). A benchmark that scores like the baseline is measuring nothing, whatever its name says. In a longer run on the same VM (2 forks of 5 one-second iterations), the empty baseline scored 0.365 ns/op, the discarded square root 1.09 and the constant one 0.545, while the returned square root and the Blackhole version took 3 to 6 ns. Short, noisy runs give different absolute numbers. Which benchmarks sit on the baseline stays the same.",
   "refs": [
    {"title": "JMHSample_08_DeadCode", "url": "https://github.com/openjdk/jmh/blob/master/jmh-samples/src/main/java/org/openjdk/jmh/samples/JMHSample_08_DeadCode.java", "kind": "read"},
    {"title": "JMHSample_10_ConstantFold", "url": "https://github.com/openjdk/jmh/blob/master/jmh-samples/src/main/java/org/openjdk/jmh/samples/JMHSample_10_ConstantFold.java", "kind": "read"}
   ]
  },
  {
   "h": "Measure allocation with -prof gc, because it doesn't wobble",
   "body": "Time is the noisiest thing you can measure. On a shared VM, the error bar on a short JMH run is often bigger than the score. Allocation is different: for the same code and input, a method allocates the same number of bytes every time. JMH's GC profiler (`-prof gc`, or `addProfiler(GCProfiler.class)` in code) reports it as `gc.alloc.rate.norm`, in bytes per operation.\n\n`MoneyBench` sums 2.9% fees over 100 card payments, once with `BigDecimal` and once with `long` cents. One run on the course VM:\n\n```text\nBenchmark            ns/op      error           B/op    error\nfeeBigDecimal       3551.2     7675.7      15200.082    0.200\nfeeLongCents         106.2      271.4          0.002    0.006\n```\n\nThe time error is more than twice the score. The allocation is exact: 15,200 bytes per call, 152 bytes per line, every time. `BigDecimal` is right for money, and every `multiply`, `setScale` and `add` returns a new object. The `long` version allocates nothing. A separate, longer run got the same 15,200 B/op, and with 10,000 lines it was 1,520,003 B/op: allocation grows exactly with the number of line items.\n\nThat makes B/op the number to put in CI. A test can't assert \"under 2 µs\" without failing on a busy build agent, but it can assert \"under 300 bytes per call\", and lesson 7's lab does exactly that. Keep time measurements for quiet, dedicated machines, with several forks.\n\nJMH has more profilers. `-lprof` lists the ones your machine supports. `-prof stack` samples thread stacks: on the `BigDecimal` benchmark it put 48.4% of samples in `BigDecimal.<init>`. The `perf` family (`perfnorm`, `perfasm`) needs Linux `perf` and shows hardware counters and the generated assembly. Every JMH run ends with a reminder worth reading once: \"The numbers below are just data. To gain reusable insights, you need to follow up on why the numbers are the way they are.\"",
   "try": {
    "title": "Count the bytes",
    "minutes": 4,
    "steps": [
     "Predict the B/op of each benchmark in `MoneyBench`, roughly.",
     "Run it (about 7 seconds). Compare the error columns for time and for bytes.",
     "Run the Kotlin twin. It writes the same two calculations in Kotlin (with `*` and `+=` on `BigDecimal`) and counts bytes with the JVM's per-thread allocation counter instead of JMH."
    ],
    "code": demo("MoneyBench"),
    "expect": "`feeBigDecimal` allocates about 15,200 bytes per call with an error under 1 byte, while its time error is huge on a busy machine. `feeLongCents` allocates 0. The Kotlin twin prints exactly 15200.000 and 0.000 B/op: Kotlin's `BigDecimal` operators call the same methods and allocate the same objects."
   }
  }
 ],
 "analogy": "Benchmarking with a `nanoTime` loop is like timing a cashier by asking them to ring up the same item a million times while you watch. After the third time they stop scanning and type the total from memory, so you measure their memory. JMH is the mystery shopper: different baskets they can't predict (non-final inputs), every receipt checked (consumed results), a few practice rounds first (warm-up) and different shops on different days (forks). The analogy breaks because a cashier who stops scanning knows they're cutting corners. The JIT isn't cheating. Deleting unused work is its job, and your benchmark gave it permission.",
 "in_your_world": "Before you swap Jackson for another JSON library in the payment API, or `BigDecimal` for `long` cents in the ledger, someone will write a quick test with `System.nanoTime()` and paste a number in the pull request. Ask for a JMH benchmark instead, kept in the repository: `@State` with realistic payloads read from fields, results returned, `-prof gc` on, several forks. Put the B/op number in the PR description, since it will mean the same thing on your laptop and in CI. Treat the ns/op number as a rough guide unless it came from a quiet machine. For a Quarkus service, benchmark the plain Java code (the mapper, the fee rule, the validator), not the HTTP endpoint, which is load testing and a different tool.",
 "mistake": "The most common mistake is a JMH benchmark that looks right and still measures nothing: a `void` method that discards its result, or an input in a `final` field with a constant initializer. Both compile, run and print a confident number, usually close to the baseline. The JIT removed or folded the work. The fix is mechanical. Return the result, or `consume` it in a `Blackhole`. Read inputs from non-final `@State` fields. Then add an empty `baseline()` benchmark and check that your real ones score clearly above it.\n\n```java\nprivate final long amountCents = 123_456;          // javac copies 123456 into fee()\n@Benchmark public void fee() { FeeMath.feeCents(amountCents); }   // and the result is dropped\n```\n\n```kotlin\nconst val AMOUNT_CENTS = 123_456L                  // kotlinc copies it too\n@Benchmark fun fee() { FeeMath.feeCents(AMOUNT_CENTS) }            // and the result is dropped\n```",
 "compare": {
  "title": "Constants that get baked into the bytecode",
  "java": {"title": "Java", "src": "class Inputs {\n    private final long amount = 123_456;       // constant initializer: javac copies the value\n    private final long fromCtor;                // assigned in the constructor: a real field read\n    long plain = 123_456;                       // what a benchmark input should be\n    static final long RATE_BPS = 290;           // copied by javac, and known to the JIT\n\n    Inputs(long v) { fromCtor = v; }\n}"},
  "kotlin": {"title": "Kotlin", "src": "const val RATE_BPS = 290L                      // copied by kotlinc; RATE_BPS * 2 even becomes 580\n\nopen class Inputs(val fromCtor: Long) {         // a real field read\n    val amount = 123_456L                       // NOT copied: kotlinc reads the field\n    var plain = 123_456L                        // what a benchmark input should be\n}"},
  "note": "Java copies any `final` field with a constant initializer into the code that uses it, instance fields included. Kotlin copies only `const val`. A Kotlin `val amount = 123_456L` compiles to `getfield`, as `javap` shows, so it isn't folded by kotlinc. Use `var` in a Kotlin benchmark anyway, because it says \"input\" to the next reader. Kotlin also folds arithmetic on constants at compile time: `RATE_BPS * 2` compiled to `ldc2_w 580`. In either language, a benchmark that reads only constants measures the JIT's arithmetic, not yours."
 },
 "worked": {
  "title": "Turn a nanoTime test into a benchmark you can trust",
  "steps": [
   {"say": "A pull request claims the new fee rule is \"3x faster\", based on this test. Spot the problems before reading on.", "code": "@Test\nvoid newRuleIsFaster() {\n    long t0 = System.nanoTime();\n    for (int i = 0; i < 1_000_000; i++) NewFeeRule.fee(12_345);   // constant input, result dropped\n    long newNs = System.nanoTime() - t0;\n    t0 = System.nanoTime();\n    for (int i = 0; i < 1_000_000; i++) OldFeeRule.fee(12_345);\n    long oldNs = System.nanoTime() - t0;\n    assertTrue(newNs * 3 < oldNs);\n}", "lang": "java", "alt_lang": "kotlin", "alt_code": "@Test\nfun `new rule is faster`() {\n    var t0 = System.nanoTime()\n    repeat(1_000_000) { NewFeeRule.fee(12_345) }            // constant input, result dropped\n    val newNs = System.nanoTime() - t0\n    t0 = System.nanoTime()\n    repeat(1_000_000) { OldFeeRule.fee(12_345) }\n    val oldNs = System.nanoTime() - t0\n    assertTrue(newNs * 3 < oldNs)\n}"},
   {"say": "Four problems: the results are dropped (dead code), the input is a constant (folding), the first loop warms up the JVM and the second inherits a warm JVM and a mixed profile, and a timing assertion in a unit test fails on a busy CI agent. Move the comparison to JMH, with the input in a non-final field.", "code": "@State(Scope.Thread)\n@BenchmarkMode(Mode.AverageTime)\n@OutputTimeUnit(TimeUnit.NANOSECONDS)\n@Fork(3)\npublic class FeeRuleBench {\n    long amountCents = 12_345;                       // 1. a non-final input\n\n    @Benchmark public long oldRule() { return OldFeeRule.fee(amountCents); }   // 2. returned\n    @Benchmark public long newRule() { return NewFeeRule.fee(amountCents); }\n    @Benchmark public void baseline() { }            // 3. the floor to compare with\n}", "lang": "java", "alt_lang": "kotlin", "alt_code": "@State(Scope.Thread)\n@BenchmarkMode(Mode.AverageTime)\n@OutputTimeUnit(TimeUnit.NANOSECONDS)\n@Fork(3)\nopen class FeeRuleBench {\n    var amountCents = 12_345L                        // 1. a non-final input\n\n    @Benchmark fun oldRule(): Long = OldFeeRule.fee(amountCents)   // 2. returned\n    @Benchmark fun newRule(): Long = NewFeeRule.fee(amountCents)\n    @Benchmark fun baseline() {}                     // 3. the floor to compare with\n}"},
   {"say": "Add a `@Param` so the amount isn't one magic number, and turn on `-prof gc` so you get a stable second number. Self-check: why does `@Param` take strings? (Answer: JMH sets the field from text, one fork per value, so the values also show up in the results table.)", "code": "@Param({\"99\", \"12345\", \"9999999\"})\nlong amountCents;", "lang": "java", "alt_lang": "kotlin", "alt_code": "@Param(\"99\", \"12345\", \"9999999\")\nvar amountCents = 0L"},
   {"say": "Read the result with the error column, and check the baseline first. If `newRule` sits on the baseline, it measures nothing. If the error bars of the two rules overlap, \"3x faster\" isn't proven. And if `newRule` allocates 0 B/op where `oldRule` allocates 48, that's a result you can put in the PR whatever the timer says.", "code": "Benchmark                              (amountCents)  Mode  Cnt   Score   Error   Units\nFeeRuleBench.newRule                           12345  avgt   15   ...     ...   ns/op\nFeeRuleBench.newRule:gc.alloc.rate.norm        12345  avgt   15   ...     ...    B/op", "lang": "text"}
  ]
 },
 "lab": {
  "title": "Fix three broken benchmarks",
  "minutes": 14,
  "files": [f"{lab}/main/{P}/DeadFeeBench.java", f"{lab}/main/{P}/ConstantFeeBench.java", f"{lab}/main/{P}/ColdBatchBench.java"],
  "run": "./gradlew :performance:test --tests 'workbench.performance.l03.*'",
  "steps": [
   "Run the tests. Five of six fail; the sixth only checks that the classes are still JMH benchmarks. The tests never time anything: they call your benchmark methods and inspect them with reflection.",
   "`DeadFeeBench`: make `fee()` hand its result to JMH.",
   "`ConstantFeeBench`: make `amountCents` an input the compiler can't know. Keep the field name, because the test sets it to other values and expects `fee()` to follow.",
   "`ColdBatchBench`: move building the batch into a `@Setup` method that runs once per fork, and keep only the summing in `totalFees()`. Then give it real warm-up (at least 3 iterations) and at least one fork.",
   "Run the tests until all six pass. Optional: copy one fixed class into `src/demo/.../l03`, give it a `main` like `TrapsBench`'s, and run it before and after your fix."
  ],
  "hints": [
   "For `DeadFeeBench`, changing `void` to `long` and adding `return` is the whole fix. A `Blackhole` parameter also passes, but one result reads better as a return value.",
   "For `ConstantFeeBench`, look at `javap -c -p` on the compiled class before and after. Before: `ldc2_w 123456`. After: `getfield amountCents`.",
   "In `ColdBatchBench`, add a `long[] batch` field and a `@Setup(Level.Trial) public void buildBatch()` method. Don't use `Level.Invocation`: it runs setup around every single call and distorts short benchmarks.",
   "`@Fork(0)` runs the benchmark inside the JVM that launched it, with that JVM's profile and garbage. Use at least 1, ideally 2 or more."
  ],
  "done_when": "All six tests in `BrokenBenchmarksTest` pass."
 },
 "drill": {
  "title": "Write a correct benchmark from memory",
  "minutes": 5,
  "prompt": "Close this page. Write a JMH benchmark that measures `FeeMath.feeCents(amount)` for a 1,000-payment batch built by `Fixtures.batch(1000)`. Include the state, setup, warm-up, measurement, forks and mode. Then check it against the answer: is the batch built outside the measurement, is the result consumed, and are the inputs non-final fields?",
  "answer": {"lang": "java", "src": "@State(Scope.Thread)\n@BenchmarkMode(Mode.AverageTime)\n@OutputTimeUnit(TimeUnit.MICROSECONDS)\n@Warmup(iterations = 5, time = 1)\n@Measurement(iterations = 5, time = 1)\n@Fork(2)\npublic class BatchFeeBench {\n    int size = 1_000;\n    long[] batch;                          // non-final input\n\n    @Setup(Level.Trial)                    // once per fork, not measured\n    public void build() {\n        batch = Fixtures.batch(size);\n    }\n\n    @Benchmark\n    public long totalFees() {\n        long total = 0;\n        for (long cents : batch) total += FeeMath.feeCents(cents);\n        return total;                      // consumed by JMH\n    }\n}",
             "alt": {"lang": "kotlin", "src": "@State(Scope.Thread)\n@BenchmarkMode(Mode.AverageTime)\n@OutputTimeUnit(TimeUnit.MICROSECONDS)\n@Warmup(iterations = 5, time = 1)\n@Measurement(iterations = 5, time = 1)\n@Fork(2)\nopen class BatchFeeBench {\n    var size = 1_000\n    lateinit var batch: LongArray          // non-final input\n\n    @Setup(Level.Trial)                    // once per fork, not measured\n    fun build() {\n        batch = Fixtures.batch(size)\n    }\n\n    @Benchmark\n    fun totalFees(): Long {\n        var total = 0L\n        for (cents in batch) total += FeeMath.feeCents(cents)\n        return total                       // consumed by JMH\n    }\n}"}}
 },
 "recap": [
  "A hand-made `nanoTime` loop measures the optimizer: dead code is removed (0.0000 ns/op), constants are folded, the first rounds run cold, and loops get unrolled and hoisted.",
  "JMH generates the measuring loop, runs warm-up iterations it throws away, then measurement iterations in fresh JVMs (`@Fork`), and reports a score with an error.",
  "Return every result or `consume` it in a `Blackhole`, and read inputs from non-final `@State` fields. A `final` constant field is copied into your method by javac.",
  "Compare against an empty `baseline()` benchmark: anything that scores like it is measuring nothing.",
  "`-prof gc` gives `gc.alloc.rate.norm` in bytes per operation. It is steady enough to gate in CI; time is not."
 ],
 "quiz": [
  {"q": "A benchmark method is `public void fee() { FeeMath.feeCents(amountCents); }`. It scores 0.4 ns/op, the same as an empty benchmark. What is the most likely reason?",
   "options": ["The fee calculation really takes 0.4 ns", "The result is discarded, so the JIT removed the calculation", "JMH's timer can't resolve anything under 1 ns", "The benchmark didn't fork"],
   "answer": 1,
   "why": "A result nobody uses is dead code, and C2 deletes it. Return the value (JMH consumes return values) or pass it to a `Blackhole`. Matching the empty baseline is the giveaway."},
  {"q": "Which input declaration lets C2 fold `FeeMath.feeCents(amountCents)` into a constant in a Java benchmark?",
   "options": ["`long amountCents = 123_456;` in the `@State` class", "`@Param(\"123456\") long amountCents;`", "`private final long amountCents = 123_456;`", "`long amountCents;` assigned in a `@Setup` method"],
   "answer": 2,
   "why": "A `final` field with a constant initializer is a compile-time constant in Java, so javac writes `ldc2_w 123456` into the method and C2 can compute the result once. The other three are real field reads that C2 can't predict."},
  {"q": "You must compare two JSON mappers in CI and fail the build on a regression. Which JMH number should the check use?",
   "options": ["The ns/op score", "`gc.alloc.rate.norm` (bytes per operation)", "The error column", "The number of warm-up iterations"],
   "answer": 1,
   "why": "Allocation per operation is deterministic for the same code and input, with error bars near zero. Time on a shared CI agent has error bars that can exceed the score, so a time threshold fails at random."},
  {"q": "A colleague's benchmark uses `@Fork(0)` \"to make it faster to run\". What do they lose?",
   "options": ["Nothing, forks only matter for multi-threaded benchmarks", "A fresh JVM: the benchmark now shares the launcher's profile, heap and JIT state, so earlier code can change its result", "The warm-up iterations", "The ability to use `@Setup`"],
   "answer": 1,
   "why": "With 0 forks the benchmark runs inside the JVM that started JMH. Its type profiles and compiled code are shared with whatever ran before, as lesson 2's `MegamorphicBench` showed by running each case in its own fork."},
  {"q": "From lesson 2: `MegamorphicBench` ran each `@Param` value (1, 2 and 3 types) in its own fork. What would likely happen to the 1-type result if all three ran in the same JVM, 3 types first?",
   "options": ["Nothing, each @Param value gets fresh compiled code", "The 1-type case would likely look slow too, because the call site's profile already holds three types", "It would get faster, because the JIT is already warm", "JMH would refuse to run"],
   "answer": 1,
   "why": "The type profile belongs to the call site in the bytecode, not to the @Param value. After three types have been seen there, C2 compiles a virtual call, and the 1-type run inherits it. Forks give every case a clean profile.",
   "from": "perf-02"}
 ],
 "flashcards": [
  {"front": "Why did a `nanoTime` loop around a discarded `Math.sqrt(x)` report 0.0000 ns/op?", "back": "Dead-code elimination: C2 proved the result was unused and removed the call."},
  {"front": "How do you make sure JMH can't throw a benchmark's result away?", "back": "Return it from the `@Benchmark` method, or pass it to `Blackhole.consume` (for several results)."},
  {"front": "Why must JMH inputs be non-final `@State` fields?", "back": "A `final` field with a constant initializer is copied into the method by javac (and `static final` values are known to the JIT), so C2 can fold the computation."},
  {"front": "What does `@Fork(2)` give you?", "back": "Two fresh JVMs per benchmark, each with a clean profile and heap. `@Fork(0)` runs in the launcher's JVM."},
  {"front": "What does `gc.alloc.rate.norm` measure, and why is it useful in CI?", "back": "Bytes allocated per benchmark operation (`-prof gc`). It is deterministic for the same code and input, so its error is near zero."},
  {"front": "In Kotlin, which property is copied into callers as a constant: `val x = 5L` or `const val X = 5L`?", "back": "Only `const val`. A plain `val` in a class compiles to a field read."}
 ],
 "terms": [
  {"term": "Dead-code elimination", "plain": "The JIT removing work whose result nothing uses."},
  {"term": "Constant folding", "plain": "Computing a result at compile time because the inputs are known constants."},
  {"term": "JMH", "plain": "The OpenJDK Microbenchmark Harness: generates and runs correct measuring loops."},
  {"term": "@State", "plain": "A JMH class whose fields hold benchmark inputs, with a scope such as one instance per thread."},
  {"term": "Fork", "plain": "A fresh JVM that JMH starts to run a benchmark in."},
  {"term": "Blackhole", "plain": "A JMH object that consumes values so the JIT must compute them."},
  {"term": "gc.alloc.rate.norm", "plain": "Bytes allocated per operation, reported by JMH's GC profiler."}
 ],
 "explain_back": {
  "prompt": "A teammate pastes \"new mapper: 12 ns/op, old mapper: 40 ns/op\" from a loop timed with `System.nanoTime()`. Explain, in your own words, why you don't trust it yet and what you'd ask for instead.",
  "answer": "A hand-made loop measures whatever the JIT left behind. If the mapper's result isn't used, C2 can delete the work; if the input is a constant, it can fold it; the first loop runs partly in the interpreter while the second runs in a warmed-up JVM with a profile the first one shaped. So 12 versus 40 might measure dead code, warm-up order or OSR. I'd ask for a JMH benchmark with the payload in a non-final @State field, the mapped result returned, an empty baseline to compare with, a few forks so each run gets a fresh JVM, and `-prof gc` so we also get bytes per operation, which is stable enough to trust and to check in CI."
 },
 "deeper": {
  "minutes": 10,
  "body": "Three more JMH features are worth knowing before you need them.\n\n`@State(Scope.Benchmark)` shares one state object across all benchmark threads, and `@Threads(4)` or `@Group` runs several threads at once. That is how you measure contention, for example 4 threads incrementing one `AtomicLong` against a `LongAdder`. Lesson 4 talks about why those differ.\n\n`Mode.SampleTime` records a distribution of individual call times and prints percentiles (p50, p99, p99.9), which fits latency questions better than an average. `Mode.SingleShotTime` measures one call per iteration, which suits cold-start questions.\n\nJMH's padding is automatic for `@State` objects: the JMH false-sharing sample says \"@States are automatically padded\", but \"This padding does not extend to the State internals\". Fields inside your state object can still share a cache line, which is lesson 4's topic.\n\nIf you want to see what C2 really did to a benchmark, `-prof perfasm` prints the hottest generated assembly next to the counters. It needs Linux `perf` and the hsdis disassembler. Without it, the cheap check is the one you already know: put an empty baseline next to every benchmark and be suspicious of anything that scores like it."
 },
 "sources": [
  {"title": "JMH, the OpenJDK Microbenchmark Harness (repository and samples)", "url": "https://github.com/openjdk/jmh"},
  {"title": "JMHSample_09_Blackholes", "url": "https://github.com/openjdk/jmh/blob/master/jmh-samples/src/main/java/org/openjdk/jmh/samples/JMHSample_09_Blackholes.java"},
  {"title": "JMHSample_11_Loops", "url": "https://github.com/openjdk/jmh/blob/master/jmh-samples/src/main/java/org/openjdk/jmh/samples/JMHSample_11_Loops.java"},
  {"title": "JMHSample_35_Profilers", "url": "https://github.com/openjdk/jmh/blob/master/jmh-samples/src/main/java/org/openjdk/jmh/samples/JMHSample_35_Profilers.java"}
 ]
}
out = ROOT / "content/lessons/perf-03.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
