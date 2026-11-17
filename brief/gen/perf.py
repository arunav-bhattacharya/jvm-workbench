import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")

INTRO = """By the end of this track you can say what the JVM does with your code after `javac` or `kotlinc` is done with it: which tier runs a method, what C2 copies into its callers and bets on, and why it sometimes throws compiled code away. You can write a JMH benchmark that measures your code instead of the optimizer, spot false sharing and fix it with padding or `LongAdder`, record a running JVM with JDK Flight Recorder, read a flame graph from async-profiler without being fooled by it, run an investigation from "it's slow, sometimes" to a fix you can prove to the byte, and read a thread dump to tell a stuck thread from a busy one.

You don't need to know anything about compilers or profilers to start: lesson 1 begins with bytecode. The whole track follows one picture, a new cook learning a restaurant's menu, and one program, a small report service that reads documents and reports their word count and reading time. You do need the memory model track's first lesson (why a loop on a plain field can hang) and the first track's lesson on atomics and `LongAdder`; the memory track's lessons on the garbage collector help in lesson 7. Install JDK 25, the current LTS. The JIT's thresholds and inlining limits are the same from JDK 21 to JDK 27, and every lesson says which JDK a newer feature needs (JFR method timing and CPU-time sampling arrived in JDK 25; compact object headers are on by default in JDK 27). async-profiler is a separate download for lesson 6; this track used version 4.6.

The labs live in `labs/performance`, one package per lesson (`workbench.performance.l01` to `l08`). Lessons 1, 6 and 8 have Kotlin labs; the rest are Java, because JMH benchmarks are Java classes here. The tests never time anything: they parse real JVM output, read class files and object layouts, record and read JFR files, count allocated bytes and read real thread dumps. Run `./gradlew :performance:test --tests 'workbench.performance.lNN.*'` from `labs/` until it passes, and `./gradlew :performance:solutionTest` to check the reference answers. Demos run with `./gradlew :performance:demo -Pmain=...`. Many start a second JVM with the flags the lesson is about, so you see real `-XX:+PrintCompilation`, `-XX:+PrintInlining` and JFR output."""

CHEAT = r"""## Picture it: the kitchen behind each idea

| Idea | Picture it | Lesson |
|---|---|---|
| Bytecode, the interpreter | the recipe card, read line by line by a new cook | 1 |
| C1 at tier 3, and its profile | a quick cheat sheet, plus notes on every order | 1 |
| C2 | the dish practised by heart, with bets on the usual orders | 1, 2 |
| OSR | switching technique halfway through a huge pot of soup | 1 |
| A restart | every new JVM is the cook's first day again | 1 |
| Inlining | copying the sauce recipe from page 12 into the main recipe | 2 |
| Type profile | the tally of side dishes; fries kept ready by the stove | 2 |
| Uncommon trap, deoptimization | the customer who asks for rice | 2 |
| Intrinsic | the apple corer: one gadget, one job, done in one push | 2 |
| JMH | a fair taste test: a warm kitchen, a fresh kitchen for each fork, a judge who eats every dish | 3 |
| Dead-code elimination | the cook who stops making the test bowls nobody eats | 3 |
| Cache line, false sharing | two cooks sharing one cutting board | 4 |
| `LongAdder` | a tally slip per cook, added up at closing time | 4 |
| JFR | the kitchen's log on one clock, cheap enough to keep all night | 5 |
| Your own JFR events | the cook's own notes in the same log | 5 |
| Sampling profiler | the manager's glance through the door every few seconds | 6 |
| Safepoint bias | a manager who only looks up when a cook puts the knife down | 6 |
| Flame graph | the tally drawn as towers of blocks, sorted by name, not by time | 6 |
| Allocation and GC pauses | clean plates, and the whole kitchen stopping to wash up | 7 |
| Thread dump | a photo of every cook; three photos tell stuck from busy | 8 |
| A blocked chain | waiters queued for the order book that a cook holds at the back door | 8 |

## How HotSpot runs your code (JDK 21 to 27)

| Tier | Runs the code | Reached after |
|---|---|---|
| 0 | interpreter, counts calls and loop back-edges | start |
| 3 | C1 with full profiling (branches, receiver types) | about 200 calls (`Tier3InvocationThreshold`) |
| 4 | C2, optimized with the profile | about 5,000 more calls (`Tier4InvocationThreshold`) |
| OSR | a running loop compiled and entered mid-loop | about 60,000 back-edges (tier 3), 40,000 more (tier 4) |

Tier 1 is C1 for trivial methods; tier 2 is C1 with counters only, used when C2 has a backlog. Thresholds grow when the compile queues are long. `CompileThreshold` (10,000) applies only with `-XX:-TieredCompilation`. Code cache: 240 MB reserved, three parts; check it with `jcmd <pid> Compiler.codecache`. On JDK 25 an AOT cache (`-XX:AOTCacheOutput`, then `-XX:AOTCache`) can carry profiles from a training run.

```text
56   13 %     4       workbench.performance.l01.Hot::longLoop @ 4 (27 bytes)
ms   id flags tier    method                                  OSR bci  bytecode size
```

Flags: `%` OSR, `s` synchronized, `!` exception handler, `b` blocking, `n` native. On JDK 25, `made not entrant` gets a reason: `not used` and `OSR invalidation of lower level` are routine; `uncommon trap` means a C2 bet failed. Times and ids change on every run.

## What C2 bets on

| Rule | Value |
|---|---|
| Inline at a call site that isn't hot | callee at most 35 bytes of bytecode (`MaxInlineSize`) |
| Inline at a hot site (25% or more of the caller's calls) | at most 325 bytes (`FreqInlineSize`) |
| Types inlined per call site | 2 (`TypeProfileWidth`); with more, only a type with 90% or more |
| Uncommon trap kinds | `unstable_if` (a branch never taken), `class_check` (a type never seen) |

See the decisions with `-XX:+UnlockDiagnosticVMOptions -XX:+PrintInlining` and `-Xlog:deoptimization=debug`. Keep cold paths out of hot methods:

```java
static long requireWordCount(long words) {
    if (words <= 0 || words > MAX_WORDS) throw badWordCount(words);   // 21 bytes: inlines anywhere
    return words;
}
```

```kotlin
fun requireWordCount(words: Long): Long {
    if (words <= 0 || words > MAX_WORDS) throw badWordCount(words)    // 21 bytes: inlines anywhere
    return words
}
```

`final` doesn't make calls faster; the number of receiver types at the call does. Prefer JDK intrinsics (`Math.addExact`, `Arrays.equals`, `Long.bitCount`) over hand-written loops.

## JMH rules

```java
@State(Scope.Thread) @BenchmarkMode(Mode.AverageTime) @OutputTimeUnit(TimeUnit.NANOSECONDS)
@Warmup(iterations = 5, time = 1) @Measurement(iterations = 5, time = 1) @Fork(2)
public class ReadingBench {
    long words = 1_234;                                                  // non-final input
    @Benchmark public long seconds() { return ReadingMath.readingSeconds(words); }   // result returned
    @Benchmark public void baseline() { }                                // the floor
}
```

```kotlin
@State(Scope.Thread) @BenchmarkMode(Mode.AverageTime) @OutputTimeUnit(TimeUnit.NANOSECONDS)
@Warmup(iterations = 5, time = 1) @Measurement(iterations = 5, time = 1) @Fork(2)
open class ReadingBench {                                                // JMH subclasses it
    var words = 1_234L                                                   // non-final input
    @Benchmark fun seconds(): Long = ReadingMath.readingSeconds(words)   // result returned
    @Benchmark fun baseline() {}                                         // the floor
}
```

Return results or `Blackhole.consume` them; never read inputs from `final` constant fields; never `@Fork(0)`; compare with a baseline. `-prof gc` gives `gc.alloc.rate.norm` (B/op): steady enough for an automatic check once the code is warm, unlike ns/op. Defaults in JMH 1.37: 5 forks, 5 + 5 iterations of 10 s.

## Caches and false sharing

Cache lines are 64 bytes. Two threads writing fields on one line slow each other down (false sharing); how much depends on the hardware and on whether the threads really run at once. Pad hot fields at least 64 bytes apart with a chain of classes, check with JOL (`ClassLayout.parseClass(X.class)`), and assert distances, not offsets. `@Contended` needs `-XX:-RestrictContended` and `--add-exports` for your own classes. For counters with many writers and rare readers, use `LongAdder`; when the value drives a decision, use `AtomicLong`.

## JFR

```bash
java -XX:StartFlightRecording:filename=rec.jfr,settings=profile -jar app.jar
jcmd <pid> JFR.start name=x settings=profile     # on a running JVM
jcmd <pid> JFR.dump name=x filename=x.jfr        # copies the data, stops nothing
jfr summary rec.jfr                              # always first
jfr view contention-by-site | allocation-by-site | gc-pauses | deoptimizations-by-reason rec.jfr
jfr print --events workbench.StoreCall --stack-depth 3 rec.jfr
```

`default.jfc` stays on ("typically less than 1 % overhead"); `profile.jfc` for short investigations. Set `maxage` or `maxsize`, or the JVM keeps 250 MB. Your own events extend `jdk.jfr.Event` (`begin`, `end`, `shouldCommit`, `commit`); fill their fields inside `shouldCommit()`. Read files with `RecordingFile`, live events with `RecordingStream`. A setting for your own event on the command line needs a `+`: `+workbench.StoreCall#threshold=30ms`. JDK 25: `method-timing=`, `report-on-exit=`, experimental `jdk.CPUTimeSample` on Linux. Recordings hold environment variables and the command line; JDK 27 can redact them.

## async-profiler and flame graphs

```bash
asprof -d 30 -f cpu.html <pid>                    # CPU (add -e ctimer if perf_events is blocked)
asprof -e wall -t -d 30 -f wall.html <pid>        # waiting: network, locks, sleep, per thread
asprof -e alloc -d 30 -f alloc.html <pid>         # who allocates
asprof -e lock -d 30 -f lock.html <pid>           # contended locks
asprof -d 30 -o collapsed -f out.collapsed <pid>  # text: "a;b;c 42"
```

Width = samples (inclusive), root at the bottom, left to right is alphabetical, never time. Wide bare tops are self time; follow them down to the first frame in your own code. Profilers built on `getStackTrace` suffer from safepoint bias; async-profiler doesn't.

## The investigation loop

1. Symptom: p99.9 and p99.99 and the GC count, per call, not the average.
2. JFR: `gc-pauses`, then allocation grouped by the first frame in your own code and its line.
3. Flame graph: who calls it.
4. Fix one thing; profile again, because the order of costs changes.
5. Prove it with JMH `-prof gc`; keep it with an allocation budget test (`getCurrentThreadAllocatedBytes`) with a margin, looked at again on JDK upgrades.

## Thread dumps

```bash
jcmd <pid> Thread.print -l > dump-1.txt          # platform threads, with java.util.concurrent lock owners
for i in 1 2 3; do jcmd $PID Thread.print -l > dump-$i.txt; sleep 5; done
jcmd <pid> Thread.dump_to_file -format=json /tmp/threads.json   # includes virtual threads
```

| Same frames in every dump? | CPU grew? | Your code in the stack? | What it is |
|---|---|---|---|
| yes | no | yes | stuck: follow its lock line to the owner, and fix the owner |
| yes | yes | yes | hot: a loop that never leaves that frame |
| no | either | yes | working |
| yes | no | no | idle: a pool or JVM thread waiting for work |

RUNNABLE only means "not waiting for a Java lock": a thread in a socket read is RUNNABLE with flat `cpu=`. `nid` is the PID column of `top -H` (decimal since JDK 18). A `ReentrantLock`'s owner shows only under `Locked ownable synchronizers`, with `-l`.
"""

T = {
 "id": "perf",
 "intro": INTRO,
 "cheatsheet": CHEAT,
 "recap": [
  "HotSpot runs every method in the interpreter first, then C1 with profiling (about 200 calls) and C2 (about 5,000 more). OSR compiles long loops while they run. Every new JVM starts cold, so measure after warm-up.",
  "C2 inlines within a bytecode budget (35 bytes at sites that aren't hot, 325 at hot ones) and only for one or two receiver types per call site. What it never saw becomes an uncommon trap; when one fires, the code is thrown away and compiled again.",
  "A `nanoTime` loop measures the optimizer. JMH, with returned results, non-final `@State` inputs, warm-up, forks and a baseline, measures your code. `-prof gc` B/op is steady once warm; time isn't.",
  "Caches move 64-byte lines. Threads writing neighbouring fields can slow each other down (false sharing); pad with a chain of classes, check with JOL, or count with `LongAdder`.",
  "JFR records GC, JIT, locks, samples and your own events on one clock, cheaply enough to leave on. Start it with `-XX:StartFlightRecording` or `jcmd`, ask with `jfr summary` and `jfr view`, read with `RecordingFile`, stream with `RecordingStream`.",
  "async-profiler samples stacks without safepoint bias, in cpu, wall, alloc and lock modes. In a flame graph width is samples and left to right is alphabetical; wide bare tops are where the time goes.",
  "An investigation goes: the tail and the GC count, allocation by your own line, a flame graph of the callers, one fix, profile again, a JMH proof, and an allocation budget test.",
  "A thread dump is a photo of every thread at one safepoint. RUNNABLE doesn't mean busy: compare `cpu=` across three dumps, follow each wait to its owner, and use `Thread.dump_to_file` for virtual threads.",
  "Every tool here has a blind spot: logs explain one method, benchmarks one piece of code, profiles the seconds you recorded, dumps one moment. Use the one that answers the question in front of you, and check surprising answers with a second."
 ],
 "quiz": [
  {"q": "Which compiler produced this line, and why is there an `@ 4`?\n\n```text\n56   13 %     4       workbench.performance.l01.Hot::longLoop @ 4 (27 bytes)\n```",
   "options": ["C1, because `%` marks a profiled compile", "C2, compiling a running loop (OSR) that is entered at bytecode index 4", "The interpreter, at line 4 of the source", "C2, inlining 4 callees"],
   "answer": 1,
   "why": "Tier 4 is C2. `%` marks on-stack replacement: the loop got hot while the method was still running, so C2 compiled a version that is entered at the top of the loop, bytecode index 4. Bytecode indexes aren't source lines."},
  {"q": "A 49-byte word-count check, most of it the code that builds its error message, is called on 1 in 8 invocations of its caller. Will C2 inline it there?",
   "options": ["Yes, everything under 325 bytes is inlined", "No: below 25% of the caller's calls the limit is 35 bytes, so it's \"too big\"", "Only if the method is `final`", "Only in the interpreter"],
   "answer": 1,
   "why": "C2 uses the 325-byte limit only when the call runs on at least 25% of the caller's invocations. Otherwise `MaxInlineSize` (35) applies, and the error path counts too. Moving the cold path into its own method shrank lesson 2's check to 21 bytes."},
  {"q": "A JMH benchmark reads its input from `private final long words = 1_234;` and scores the same as an empty benchmark. Why?",
   "options": ["JMH can't read private fields", "javac copies the constant into the method, and C2 folds the whole calculation into one number", "The benchmark forgot `@Fork`", "Private fields are always kept in registers"],
   "answer": 1,
   "why": "A `final` field with a constant initializer is a compile-time constant in Java, so the method contains `ldc2_w 1234`, and C2 can compute the result once. Read inputs from a non-final `@State` field."},
  {"q": "Two worker threads each update their own `volatile long` counter in one small object, and the job runs slower with two threads than with one. JOL shows the fields at offsets 16 and 24. What's the first thing to try?",
   "options": ["Make the fields non-volatile", "Put the counters at least 64 bytes apart (a chain of classes), or use a `LongAdder` per counter, then measure", "Add `synchronized` to both updates", "Use `AtomicLong` for both fields in the same object"],
   "answer": 1,
   "why": "8 bytes apart is one cache line, so every write takes the line from the other core: false sharing. Padding or `LongAdder`'s padded cells separate them. Removing `volatile` changes visibility, not layout, and how much padding helps depends on the machine, so measure."},
  {"q": "The report service has slow spikes right now, you can't restart it, and you can't install anything on its machine. Which first step gives you GC pauses, lock waits and allocation for the last few minutes?",
   "options": ["`jcmd <pid> JFR.dump` from a recording that's always on, then `jfr view gc-pauses`, `contention-by-site` and `allocation-by-site`", "Restart it with `-XX:+PrintCompilation`", "Attach async-profiler", "Run JMH on the machine"],
   "answer": 0,
   "why": "JFR is built into the JDK, and a running recording can be dumped without stopping the JVM. Its views answer all three questions from one file. A restart throws away the minutes you wanted, and the other tools need installing or answer other questions."},
  {"q": "In a flame graph, `String.format` is drawn to the left of `Pattern.compile` at the same level. Which statement is true?",
   "options": ["`String.format` ran first", "`String.format` is the slower of the two", "Their order is alphabetical; only the widths carry information", "`String.format` called `Pattern.compile`"],
   "answer": 2,
   "why": "Flame graphs sort frames alphabetically at each level (`java/lang/...` before `java/util/...`); left to right is not a timeline. Width is the number of samples, and a callee is drawn above its caller, never beside it."},
  {"q": "A profiler built on `Thread.getStackTrace()` charges 29% of the CPU to `String.split` itself, with nothing ever above it. async-profiler charges most of that time to methods `split` calls. What's going on?",
   "options": ["async-profiler skips small methods", "The JIT inlined `split` away", "`getStackTrace` uses wall-clock time", "Safepoint bias: `getStackTrace` sees a thread only at a safepoint poll, after its inlined callees have returned, so their time is charged to `split`"],
   "answer": 3,
   "why": "Reading another thread's stack needs that thread at a safepoint, and polls sit at method returns and loop back-edges. async-profiler interrupts the thread with a signal and walks the stack at the exact instruction, inlined frames included."},
  {"q": "After hoisting a regex into a `static final` field and guarding a debug log line, the report step's allocation drops from about 2,460 to 832 bytes per call. What does the investigation loop say to do next?",
   "options": ["Stop: a threefold improvement is enough", "Give the JVM a bigger heap so the GC runs less", "Profile again: the remaining bytes have a new top line (here `split`, then the `Matcher`), fix the next one if the budget needs it, and stop when what's left fits", "Rewrite the method in Kotlin"],
   "answer": 2,
   "why": "Each fix changes the order of costs. In lesson 7, `split` filled 92% of the profile after round 1, and the `Matcher` 99.6% after round 2, which left 56 bytes on JDK 25, under the 300-byte budget."},
  {"q": "In a pull request you must show that a new way of counting words allocates less than the old one, and keep it that way in the automatic build. Which tools fit?",
   "options": ["A unit test that times 1,000 calls with `System.nanoTime()`", "`-XX:+PrintCompilation`", "async-profiler in wall mode", "A JMH benchmark with `-prof gc`, then an allocation budget test with a margin"],
   "answer": 3,
   "why": "JMH with `-prof gc` gives bytes per operation with an error near zero once warm, and a test using the per-thread allocation counter keeps the number from growing. A hand-made timing loop measures the optimizer, and wall mode answers a different question."},
  {"q": "Three thread dumps, 5 seconds apart. `catalog-refresh` is RUNNABLE in `SocketDispatcher.read0` with `cpu=25.09ms` in all three, and four other threads are BLOCKED waiting for a lock it holds. What do you fix?",
   "options": ["The four BLOCKED threads, by giving them a bigger pool", "`catalog-refresh`: it holds the lock while it waits for the network, so make the slow call outside the lock, with a timeout", "Nothing: RUNNABLE means it's working, so it will finish", "The JIT, because the thread is stuck in native code"],
   "answer": 1,
   "why": "RUNNABLE in a native socket read with flat CPU means it's waiting for bytes, not working. Every thread that needs its lock queues behind it. Fix the owner, not the queue: call the store without the lock and take the lock only to swap in the result."}
 ]
}
# spread the correct answers over the four positions
for q, target in zip(T["quiz"], [1, 0, 2, 3, 2, 0, 1, 2, 3, 1]):
    correct = q["options"].pop(q["answer"])
    q["options"].insert(target, correct)
    q["answer"] = target

out = ROOT / "content/tracks/perf.json"
out.write_text(json.dumps(T, indent=1, ensure_ascii=False) + "\n")
print(out)
