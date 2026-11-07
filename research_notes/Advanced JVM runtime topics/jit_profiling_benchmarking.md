# JIT internals, benchmarking (JMH), hardware sympathy, JFR, async-profiler — research notes (as of 2026-11-07)

Scope: source of truth for a 7-lesson track for a senior Kotlin/Java backend engineer (payments on Quarkus). Release context: JDK 25 = current LTS (GA Sept 2025), JDK 26 (GA March 2026), JDK 27 (GA Sept 2026); mainline is JDK 28 (not released).

How this was researched (read first):
- Network: openjdk.org (JEP pages, bugs.openjdk.org), docs.oracle.com, inside.java, brendangregg.com and shipilev.net were **blocked** from this machine (CONNECT 403 / DNS failure). I therefore used *primary sources mirrored on GitHub*: the OpenJDK source at the GA tags `jdk-21-ga`, `jdk-25-ga`, `jdk-26-ga`, `jdk-27-ga` (raw.githubusercontent.com), the official JDK man pages that live in the source tree as Markdown (`java.md`, `jfr.md`, `jcmd.md`), the `openjdk/jmh` samples, async-profiler's README/docs, Brendan Gregg's own `FlameGraph` repo, and GitHub commit search on `openjdk/jdk` to confirm JEP numbers/titles ("Implement JEP NNN: <title>" commits). JEP *status pages* could not be read; JEP status below is inferred from (a) the implementation commit and (b) the feature being present in the GA-tag source. That is strong evidence but is marked as such.
- Local experiments: OpenJDK **21.0.12.1** (Ubuntu build) on a **4-vCPU cloud VM (Intel Xeon @ 2.10 GHz, 15 GB RAM, shared/noisy)**; JMH **1.37**; JOL 0.17; async-profiler **4.6**. All timing numbers carry that machine caveat: error bars are wide; use them for *relative* teaching points, never as reference numbers.

---

## 1. Execution pipeline and the exact flags/defaults (JDK 21 → 25 → 27)

### Takeaway
HotSpot runs bytecode in the interpreter (tier 0), compiles warm methods with C1 (tiers 1–3, tier 3 = full profiling) and hot ones with C2 (tier 4) using the profile; long-running loops are switched mid-execution via OSR. The tiered thresholds and C2 inlining limits are **unchanged between JDK 21 and JDK 27** (Tier3InvocationThreshold 200, Tier4InvocationThreshold 5000, MaxInlineSize 35, FreqInlineSize 325 on x86_64, MaxInlineLevel 15, InlineSmallCode 2500); the code cache is 240 MB reserved and segmented by default with tiered compilation.

### Cited Findings
**Tier levels (verbatim from HotSpot, JDK 25)**
- `CompLevel_none = 0 // Interpreter`, `CompLevel_simple = 1 // C1`, `CompLevel_limited_profile = 2 // C1, invocation & backedge counters`, `CompLevel_full_profile = 3 // C1, invocation & backedge counters + mdo`, `CompLevel_full_optimization = 4 // C2 or JVMCI` — [compilerDefinitions.hpp @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/compiler/compilerDefinitions.hpp)
- Policy comment (JDK 25): "level 0 - interpreter (Profiling is tracked by a MethodData object, or MDO in short) … level 1 - C1 with full optimization (no profiling) … level 2 - C1 with invocation and backedge counters … level 3 - C1 with full profiling (level 2 + All other MDO profiling information) … level 4 - C2 with full profile guided optimization." Normal path is 0→3→4. — [compilationPolicy.hpp @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/compiler/compilationPolicy.hpp)
- Same file: "level 2 is generally faster than level 3 by about 30%"; if the C2 queue is long the policy does 0→2 first (controlled by `Tier3DelayOn`/`Tier3DelayOff`, "the number of methods in the C2 queue per compiler thread"); trivial methods are compiled at level 1 "instead of 4" because C2 would "yield the same code"; compile queues are priority queues ordered by event rate, and stale methods are removed. — [compilationPolicy.hpp @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/compiler/compilationPolicy.hpp)
- Threshold predicate (verbatim): `i > TierXInvocationThreshold * s || (i > TierXMinInvocationThreshold * s && i + b > TierXCompileThreshold * s)` where i = invocations, b = backedges, s = load-feedback scale `s = queue_size_X / (TierXLoadFeedback * compiler_count_X) + 1`. "OSR transitions are controlled simply with b > TierXBackEdgeThreshold * s predicates." "Level 2 thresholds are not used." — [compilationPolicy.hpp @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/compiler/compilationPolicy.hpp)
- `Tier0ProfilingStartPercentage` (default 200) lets the interpreter start profiling if the level-3 version is late; "We can even go directly from level 0 to 4 if c1 doesn't produce a compiled version in time." — same source.
- `TieredStopAtLevel` "is used mostly for testing … TieredStopAtLevel = 1 in order to compile everything with pure c1." — same source.

**Defaults table (JDK 25 source; identical values confirmed in JDK 21 `-XX:+PrintFlagsFinal` and in jdk-27-ga source)**

| Flag | Default | Where defined |
|---|---|---|
| TieredCompilation | true (x86_64 with C1) | c2_globals_x86.hpp |
| Tier3InvocationThreshold / Tier3MinInvocationThreshold / Tier3CompileThreshold / Tier3BackEdgeThreshold | 200 / 100 / 2000 / 60000 | compiler_globals.hpp |
| Tier4InvocationThreshold / Tier4MinInvocationThreshold / Tier4CompileThreshold / Tier4BackEdgeThreshold | 5000 / 600 / 15000 / 40000 | compiler_globals.hpp |
| Tier3DelayOn / Tier3DelayOff | 5 / 2 | compiler_globals.hpp |
| Tier0ProfilingStartPercentage | 200 | compiler_globals.hpp |
| CompileThreshold (non-tiered only) / OnStackReplacePercentage | 10000 / 140 | c2_globals_x86.hpp |
| MaxInlineSize (bytecodes, cold call site) | 35 | c2_globals.hpp |
| FreqInlineSize (bytecodes, hot call site) | 325 (x86) | c2_globals_x86.hpp |
| MaxTrivialSize | 6 | c2_globals.hpp |
| InlineSmallCode (bytes of already-compiled callee) | 2500 (x86) | c2_globals_x86.hpp / PrintFlagsFinal |
| MaxInlineLevel / MaxRecursiveInlineLevel | 15 / 1 | c2_globals.hpp |
| InlineFrequencyRatio / MinInlineFrequencyRatio (diagnostic) | 0.25 / 0.0085 | globals.hpp |
| DesiredMethodLimit (develop flag) | 8000 | compiler_globals.hpp |
| TypeProfileWidth / TypeProfileMajorReceiverPercent | 2 / 90 | PrintFlagsFinal (JDK 21) |
| LoopUnrollLimit / LoopMaxUnroll | 60 (x86_64) / 16 | c2_globals_x86.hpp / PrintFlagsFinal |
| DoEscapeAnalysis / EliminateAllocations / EliminateLocks | true / true / true | c2_globals.hpp / PrintFlagsFinal |
| RangeCheckElimination / UseLoopPredicate / UseSuperWord | true / true / true | PrintFlagsFinal (JDK 21) |
| PerMethodTrapLimit / PerBytecodeTrapLimit / PerMethodRecompilationCutoff | 100 / 4 / 400 | PrintFlagsFinal (JDK 21) |
| MaxNodeLimit | 80000 | PrintFlagsFinal (JDK 21) |
| CICompilerCount | 3 on a 4-CPU box (ergonomic) | PrintFlagsFinal (JDK 21) |
| ReservedCodeCacheSize | 48M base ×5 with tiered → 240M (251658240) | c2_globals_x86.hpp + compilerDefinitions.cpp |
| SegmentedCodeCache | true when tiered and ReservedCodeCacheSize ≥ 240M | compilerDefinitions.cpp |
| Code heaps at 240M (4-CPU box, JDK 21) | non-nmethods 5,832,780 B (~5.6 MB), profiled 122,912,730 B (~117 MB), non-profiled 122,912,730 B | PrintFlagsFinal (JDK 21) |
| InitialCodeCacheSize | 2496K (x86_64) | c2_globals_x86.hpp |

Sources: [compiler_globals.hpp @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/compiler/compiler_globals.hpp); [c2_globals.hpp @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/opto/c2_globals.hpp); [c2_globals_x86.hpp @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/cpu/x86/c2_globals_x86.hpp); [globals.hpp @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/runtime/globals.hpp); [compilerDefinitions.cpp @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/compiler/compilerDefinitions.cpp) (`FLAG_SET_ERGO(ReservedCodeCacheSize, MIN2(CODE_CACHE_DEFAULT_LIMIT, (size_t)ReservedCodeCacheSize * 5))`; "Enable SegmentedCodeCache if tiered compilation is enabled, ReservedCodeCacheSize >= 240M"); local `java -XX:+PrintFlagsFinal -version` on JDK 21.0.12.

- Local `-XX:+PrintCodeCache` (JDK 21.0.12, at exit of `java -version`): `CodeHeap 'non-profiled nmethods': size=120032Kb`, `CodeHeap 'profiled nmethods': size=120028Kb`, `CodeHeap 'non-nmethods': size=5700Kb`, `CodeCache: size=245760Kb` — local experiment.

**What changed JDK 21 → 27 in these flags (diff of GA-tag sources)**
- JDK 21→25: no change to any tier threshold or inlining limit. New in 25: diagnostic `Tier0ProfileDelayFactor` (100.0), `Tier2ProfileDelayFactor` (250.0) ("Delay profiling … of methods that were observed to be lukewarm") and `SkipTier2IfPossible` ("Compile at tier 4 instead of tier 2 in training replay mode", i.e. Leyden training data); C2 gained `TypeProfileSubTypeCheckCommonThreshold` (50). — diff of [compiler_globals.hpp @ jdk-21-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-21-ga/src/hotspot/share/compiler/compiler_globals.hpp) vs [@ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/compiler/compiler_globals.hpp)
- JDK 25→27: the two "lukewarm" delay factors are gone in jdk-27-ga (commit "8368321: Rethink compilation delay strategy for lukewarm methods", 2025-10-27, so most likely JDK 26); C2 gained **experimental `HotCodeHeap`** ("Enable the code heap for hot C2 nmethods", default false) with `HotCodeSamplePercent` (80) and `HotCodeHeapSize` (0); code-cache size flags changed type from `uintx` to `size_t` (no value change). — [c2_globals.hpp @ jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/hotspot/share/opto/c2_globals.hpp); [globals.hpp @ jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/hotspot/share/runtime/globals.hpp); [GitHub commit search openjdk/jdk "HotCodeHeap"](https://api.github.com/search/commits?q=repo:openjdk/jdk+HotCodeHeap)
- Compact object headers: `UseCompactObjectHeaders` is a product flag defaulting to **false in JDK 25** and **true in JDK 27** (JEP 450 experimental impl. commit 2024-11-08 → JDK 24; JEP 519 "Compact Object Headers" commit 2025-05-22 → JDK 25; JEP 534 "Compact Object Headers by Default" commit 2026-05-20 → JDK 27). This changes JOL output/field offsets (see section 5). — [globals.hpp @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/runtime/globals.hpp), [globals.hpp @ jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/hotspot/share/runtime/globals.hpp), [commit search "JEP 534"](https://api.github.com/search/commits?q=repo:openjdk/jdk+%22JEP+534%22)

**OSR**
- OSR compiles show `%` and `@ <bci>` in PrintCompilation (format code in section 2). In my run, `Hot::longLoop` (called once, 50M iterations) got `8 % 3 Hot::longLoop @ 4` then `10 % 4 Hot::longLoop @ 4` within ~40 ms of JVM start — local experiment (verbatim output in section 2).

### Inferences
- For teaching: "about 200 calls to get C1-with-profiling, about 5000 *profiled* calls (or loop-heavy equivalents) to get C2", scaled up automatically when compiler queues are long. Never teach "10,000 invocations" (`CompileThreshold`) as the tiered trigger; it applies only with `-XX:-TieredCompilation`.
- Because the thresholds are identical from 21 through 27, the course can teach these numbers once and mark them "JDK 21–27".

### Gaps
- Could not read the JEP pages themselves (openjdk.org blocked), nor JDK-8368321's description; the "lukewarm" change is described only from the flag diff and commit title.
- Did not run JDK 25/26/27 locally (only JDK 21 installed); values for 25/27 come from source, not from `PrintFlagsFinal`.

---

## 2. What the JIT does, and real `-XX:+PrintCompilation` output

### Takeaway
C2's big wins come from inlining (driven by bytecode size *and* profile frequency), which enables escape analysis/scalar replacement, loop opts (unrolling, range-check elimination, vectorization) and intrinsics; speculative optimizations are guarded by uncommon traps, and when a guard fails the method is deoptimized ("made not entrant") and recompiled. PrintCompilation shows this live; the columns are fixed by `CompileTask::print_impl`.

### Cited Findings
**PrintCompilation format (source of truth)**
- `CompileTask::print_impl` prints: timestamp in ms since VM start; `%4d` compile id; five attribute chars `%` (OSR), `s` (synchronized), `!` (has exception handler), `b` (blocking compile), `n` (native wrapper); the tier level (only when TieredCompilation is on, `-` if unknown); the method as `Class::name`; for OSR ` @ <osr_bci>`; then ` (N bytes)` = **bytecode size**, or ` (native)`; then an optional message. — [compileTask.cpp @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/compiler/compileTask.cpp)
- JDK 21 prints the bare message `made not entrant`; **JDK 25 prints `made not entrant: <reason>`** (`ss.print("made not entrant: %s", reason)`). Reasons found in JDK 25 source include `"uncommon trap"`, `"marked for deoptimization"`, `"OSR invalidation, back branch"`, `"OSR invalidation for compiling with C1"`, `"missing exception handler"`, `"set native function"`. — [nmethod.cpp @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/code/nmethod.cpp), [nmethod.cpp @ jdk-21-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-21-ga/src/hotspot/share/code/nmethod.cpp), [deoptimization.cpp @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/runtime/deoptimization.cpp), [compilationPolicy.cpp @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/compiler/compilationPolicy.cpp)
- No "made zombie" string exists in the JDK 25 nmethod.cpp (zombie state was removed in an earlier release; older tutorials showing `made zombie` are outdated). — [nmethod.cpp @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/code/nmethod.cpp) (absence verified by grep; the removal release itself not verified)

**Verbatim local output (JDK 21.0.12, `java -XX:+PrintCompilation Hot`)** — program: `longLoop()` called once with a 50M-iteration loop; `total(Shape[])` calls `s.area()` first only on `Square`s (20,000 calls), then on a `Square/Circle/Tri` mix.
```
32    1       3       java.lang.Object::<init> (1 bytes)
34    3     n 0       jdk.internal.misc.Unsafe::getReferenceVolatile (native)   
40    8 %     3       Hot::longLoop @ 4 (27 bytes)
40    9       3       Hot::longLoop (27 bytes)
40   10 %     4       Hot::longLoop @ 4 (27 bytes)
42    8 %     3       Hot::longLoop @ 4 (27 bytes)   made not entrant
74   10 %     4       Hot::longLoop @ 4 (27 bytes)   made not entrant
75   13       3       Hot$Square::<init> (10 bytes)
79   15 %     3       Hot::total @ 11 (42 bytes)
79   14       2       Hot$Square::area (10 bytes)
79   16       3       Hot::total (42 bytes)
79   17 %     4       Hot::total @ 11 (42 bytes)
83   15 %     3       Hot::total @ 11 (42 bytes)   made not entrant
88   18       4       Hot::total (42 bytes)
91   16       3       Hot::total (42 bytes)   made not entrant
91   19       4       Hot$Square::area (10 bytes)
92   14       2       Hot$Square::area (10 bytes)   made not entrant
105   21       3       Hot$Circle::<init> (10 bytes)
106   23       3       Hot$Circle::area (14 bytes)
106   24       3       Hot$Tri::area (14 bytes)
106   18       4       Hot::total (42 bytes)   made not entrant
106   25       4       Hot::total (42 bytes)
107   17 %     4       Hot::total @ 11 (42 bytes)   made not entrant
```
Column reading of `40   10 %     4       Hot::longLoop @ 4 (27 bytes)`: 40 ms after start; compile id 10; `%` = OSR; tier 4 = C2; OSR entry at bytecode index 4 (the loop header); method bytecode is 27 bytes. `106 18 4 Hot::total ... made not entrant` = the C2 version compiled at 88 ms (id 18) was invalidated when Circle/Tri appeared; id 25 is the recompile. `79 14 2 Hot$Square::area` is a **tier 2** compile (C1 with counters only), which the policy uses when C2 is busy (section 1). — local experiment.
- Attribute flags, verbatim (JDK 21, separate program): `58   25  s    3       Flags::syncInc (9 bytes)` (synchronized) and `59   27   !   3       Flags::parse (8 bytes)` (has try/catch). — local experiment.
- Run-to-run variation (same program, three runs): first OSR compile of `longLoop` at 40 ms, 47 ms, 60 ms; compile ids and interleaving with JDK-internal methods differ between runs. — local experiment.
- Non-tiered (`-XX:-TieredCompilation`): no tier column, e.g. `103    2 %           Hot::longLoop @ 4 (27 bytes)` — local experiment.

**Inlining and megamorphic call sites (verbatim, `-XX:+UnlockDiagnosticVMOptions -XX:+PrintInlining`)**
```
                              @ 27   Hot$Square::area (10 bytes)   inline (hot)
                               \-> TypeProfile (977323/977323 counts) = Hot$Square
...  (after the deopt, recompiled with 3 receiver types)
                              @ 27   Hot$Shape::area (0 bytes)   virtual call
```
— local experiment. Explanation: with one receiver type in the profile C2 inlines `area()` behind a class check; with three types (beyond `TypeProfileWidth=2`, no type ≥ `TypeProfileMajorReceiverPercent=90`) the site is megamorphic and becomes a virtual call (no inlining).
- Deopt log (`-Xlog:deoptimization=debug`, JDK 21): `[0.105s][debug][deoptimization] cid=  20     level=4 Hot.total([LHot$Shape;)D trap_bci=27 class_check maybe_recompile pc=0x00007ff1a82c9c30 relative_pc=0x00000000000001d0` — reason `class_check`, action `maybe_recompile`, at the call bytecode 27. — local experiment.

**Inlining rules (C2, `InlineTree` in bytecodeInfo.cpp, JDK 25)**
- Call site frequency `freq = call_site_count / invoke_count`; if `freq >= InlineFrequencyRatio` (0.25) the limit is `FreqInlineSize` (325) else `MaxInlineSize` (35); messages: `"too big"` (cold site over 35) vs `"hot method too big"` (hot site over 325). — [bytecodeInfo.cpp @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/opto/bytecodeInfo.cpp)
- A callee that is already compiled with `inline_instructions_size() > InlineSmallCode` (2500) is rejected: `"already compiled into a big method"`; at cold sites the bar is `InlineSmallCode/4`: `"already compiled into a medium method"`. — same source.
- Methods with bytecode size `<= MaxTrivialSize` (6) skip frequency-based objections; other messages: `"inlining too deep"` (MaxInlineLevel 15), `"recursive inlining is too deep"`, `"too cold to inline"`, `"low call site frequency"`, `"size > DesiredMethodLimit"` (8000 bytecodes aggregate), `"force inline by annotation"`, `"don't inline by annotation"`, `"force inline by CompileCommand"`. — same source.
- Implication: inlining limits are measured in **bytecode bytes** (the number in `(N bytes)`), not source lines.

**Escape analysis, loops, intrinsics** (flag evidence only)
- `DoEscapeAnalysis`, `EliminateAllocations` (scalar replacement), `EliminateLocks`, `UseLoopPredicate`, `RangeCheckElimination`, `UseSuperWord` (auto-vectorization) are all on by default; `LoopUnrollLimit=60`, `LoopMaxUnroll=16`. — [c2_globals.hpp @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/opto/c2_globals.hpp); local PrintFlagsFinal.
- async-profiler's allocation profiler "does not affect Escape Analysis or prevent from JIT optimizations like allocation elimination. Only actual heap allocations are measured." (i.e., scalar-replaced objects never show up in allocation profiles). — [async-profiler ProfilingModes.md](https://raw.githubusercontent.com/async-profiler/async-profiler/master/docs/ProfilingModes.md)
- Observed intrinsic behaviour (JDK 21, x86_64): an unused `Math.sqrt(x)` was eliminated like dead code (≈ baseline), but an unused `Math.log(x)` was **not** eliminated (logWrong 10.1 ns vs baseline 0.37 ns), and a naive loop of discarded `Math.log` still cost ~7–9 ns/op. Plausible explanation (not verified in source): `sqrt` is a pure IR node while `log` is implemented as a call to a generated math stub that C2 does not remove. — local JMH, section 3.

**JITWatch**
- JITWatch is a "Log analyser and visualiser for the HotSpot JIT compiler" (JavaFX UI; `mvn clean package && java -jar ui/target/jitwatch-ui-shaded.jar`); maintained by Chris Newland. — [JITWatch README](https://raw.githubusercontent.com/AdoptOpenJDK/jitwatch/master/README.md)
- Required JVM flags per the JITWatch wiki: `-XX:+UnlockDiagnosticVMOptions -XX:+LogCompilation` (optionally `-XX:LogFile=mylogfile.log`), `-XX:+PrintAssembly` (needs the hsdis disassembler or a debug JVM; "highly recommended to add `-XX:+DebugNonSafepoints`"), and `-Xlog:class+load=info` "required for JITWatch to build its class model; for Java 8 and older use `-XX:+TraceClassLoading`". — [JITWatch wiki Instructions](https://raw.githubusercontent.com/wiki/AdoptOpenJDK/jitwatch/Instructions.md); demo script flags in [makeDemoLogFile.sh](https://raw.githubusercontent.com/AdoptOpenJDK/jitwatch/master/scripts/makeDemoLogFile.sh)

### Inferences
- Lesson framing: "the JIT bets on what it has seen (profile) and pays a deopt when it loses the bet". The `Hot` program is a 2-minute live demo of mono → megamorphic → deopt → recompile.
- Kotlin relevance: Kotlin lambdas passed to non-inline higher-order functions and interface-heavy code (e.g., many `PaymentMethod` implementations through one call site) are exactly where megamorphic sites appear; `inline fun` in Kotlin is source-level inlining that sidesteps the JIT's bytecode-size limits (inference, not tested here).
- Because output timestamps and ids vary per run (observed), lab grading must never compare PrintCompilation text literally.

### Gaps
- Did not run JDK 25 to capture a real `made not entrant: <reason>` line; the format is from source only.
- No hsdis available locally, so no `PrintAssembly` sample; JITWatch not run.
- Shipilëv's "JVM Anatomy Quarks" (shipilev.net) blocked; nothing cited from it.

---

## 3. Benchmarking with JMH 1.37: why naive loops lie, what the samples teach, local numbers

### Takeaway
JMH 1.37 (released 2023-08, still the latest release in Nov 2026) exists to defeat dead-code elimination, constant folding, loop merging, OSR artifacts and missing warm-up. The official samples show each trap; my local runs reproduced DCE and constant folding (and one surprise: `Math.log` is not DCE'd on JDK 21), and `-prof gc`'s `gc.alloc.rate.norm` (B/op) was the most stable metric on a noisy VM.

### Cited Findings
**Version and defaults**
- Maven Central metadata for `org.openjdk.jmh:jmh-core`: `<latest>1.37</latest>`, `<release>1.37</release>`, lastUpdated 20230803; the GitHub master is `1.38-SNAPSHOT`. — [jmh-core maven-metadata.xml](https://maven-central.storage-download.googleapis.com/maven2/org/openjdk/jmh/jmh-core/maven-metadata.xml), [openjdk/jmh pom.xml](https://raw.githubusercontent.com/openjdk/jmh/master/pom.xml)
- JMH 1.37 defaults (`org.openjdk.jmh.runner.Defaults` + `-h`): 5 warmup iterations × 10 s, 5 measurement iterations × 10 s, 5 forks, 1 thread, mode Throughput; modes `Throughput, AverageTime, SampleTime, SingleShotTime, All`; scopes `Benchmark, Group, Thread`. — local `javap`/`-h` on [jmh-core-1.37.jar](https://maven-central.storage-download.googleapis.com/maven2/org/openjdk/jmh/jmh-core/1.37/jmh-core-1.37.jar)
- Built-in profilers in 1.37 (`-lprof` on this Linux box): `cl, comp, gc, jfr, mempool, pauses, safepoints, stack` supported; `async` (needs libasyncProfiler, `-prof async:libPath=<path>`), `perf, perfasm, perfc2c, perfnorm` (need Linux `perf`), `xperfasm`, `dtraceasm` listed as unsupported here. — local run.
- JMH auto-detected **compiler blackholes**: `# Blackhole mode: compiler (auto-detected, use -Djmh.blackhole.autoDetect=false to disable)` on JDK 21; the JVM-side `blackhole` CompileCommand first appears in JDK 17 (`compilerOracle.hpp` mentions Blackhole in jdk-17-ga, not jdk-16-ga). JMH prints a caution that results under different Blackhole modes are not comparable. — local run; [compilerOracle.hpp @ jdk-17-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-17-ga/src/hotspot/share/compiler/compilerOracle.hpp)

**What the official samples teach (verbatim quotes)**
- `JMHSample_08_DeadCode`: "The downfall of many benchmarks is Dead-Code Elimination (DCE): compilers are smart enough to deduce some computations are redundant and eliminate them completely." `measureWrong()` calls `compute(x)` and discards it ("the entire computation is optimized away"); `measureRight()` returns it ("returned results are implicitly consumed by Blackholes"). `compute` is `for (c < 10) d = d * d / 42;` on an `int x` state field. — [JMHSample_08_DeadCode.java](https://raw.githubusercontent.com/openjdk/jmh/master/jmh-samples/src/main/java/org/openjdk/jmh/samples/JMHSample_08_DeadCode.java)
- `JMHSample_09_Blackholes`: for multiple results either merge them (Option A) or "Use explicit Blackhole objects, and sink the values there" (Option B); "If you are only producing a single result, it is more readable to use the implicit return… Do not make your benchmark code less readable with explicit Blackholes!" Expected: "measureWrong() running on-par with baseline(). Both measureRight() are measuring twice the baseline". — [JMHSample_09_Blackholes.java](https://raw.githubusercontent.com/openjdk/jmh/master/jmh-samples/src/main/java/org/openjdk/jmh/samples/JMHSample_09_Blackholes.java)
- `JMHSample_10_ConstantFold`: "The flip side of dead-code elimination is constant-folding… This can be prevented by always reading the inputs from non-final instance fields of @State objects"; `private final int wrongX = 42;` with the comment "IDEs will say 'Look, this field could be final'. Don't. Trust. Them." — [JMHSample_10_ConstantFold.java](https://raw.githubusercontent.com/openjdk/jmh/master/jmh-samples/src/main/java/org/openjdk/jmh/samples/JMHSample_10_ConstantFold.java)
- `JMHSample_11_Loops`: "It would be tempting for users to do loops within the benchmarked method. (This is the bad thing Caliper taught everyone)"; "the larger the repetitions count, the lower the 'perceived' cost of the operation being measured. Up to the point we do each addition with 1/20 ns, well beyond what hardware can actually do… because the loop is heavily unrolled/pipelined, and the operation to be measured is hoisted from the loop. Moral: don't overuse loops". — [JMHSample_11_Loops.java](https://raw.githubusercontent.com/openjdk/jmh/master/jmh-samples/src/main/java/org/openjdk/jmh/samples/JMHSample_11_Loops.java)
- `JMHSample_22_FalseSharing`: "JMH helps you to alleviate this: @States are automatically padded. This padding does not extend to the State internals though"; padding is "not versatile because JVMs can freely rearrange the field order, even of the same type"; class-hierarchy trick ("superclass fields are usually laid out first"); array trick; "@Contended (since JDK 8) … Remember to flip -XX:-RestrictContended to enable." Uses `@Fork(5)`, Throughput in µs. — [JMHSample_22_FalseSharing.java](https://raw.githubusercontent.com/openjdk/jmh/master/jmh-samples/src/main/java/org/openjdk/jmh/samples/JMHSample_22_FalseSharing.java)
- `JMHSample_35_Profilers`: "Use -lprof to list the profilers… Many profilers have their own options, usually accessible via -prof <profiler-name>:help"; examples `-prof stack`, `-prof gc` (Maps), `-prof cl`/`comp` (classloader), `-prof perf/perfnorm/perfasm` (Linux), `xperfasm` (Windows), `dtraceasm` (macOS). — [JMHSample_35_Profilers.java](https://raw.githubusercontent.com/openjdk/jmh/master/jmh-samples/src/main/java/org/openjdk/jmh/samples/JMHSample_35_Profilers.java)
- Every JMH run ends with: "REMEMBER: The numbers below are just data. To gain reusable insights, you need to follow up on why the numbers are the way they are. Use profilers… perform baseline and negative tests… Do not assume the numbers tell you what you want them to tell." — local JMH 1.37 output.

**Local results (JDK 21.0.12, 4 vCPU Xeon 2.1 GHz VM; AverageTime ns/op; 2 forks × 5 × 1 s unless stated; ± = 99.9% CI)**

| Benchmark | Score | What it shows |
|---|---|---|
| baseline (empty) | 0.365 ± 0.088 | cost of the JMH harness call |
| divWrong (3 divisions, result discarded) | 0.493 ± 0.164 | ≈ baseline → DCE |
| divRight (same, returned) | 5.473 ± 3.414 | real cost |
| sqrtWrong (discarded) | 1.090 ± 1.153 | ≈ baseline → DCE |
| sqrtRight (returned) | 5.614 ± 7.140 | real cost (noisy) |
| sqrtBlackhole (`bh.consume`) | 3.084 ± 1.301 | consumed via Blackhole |
| sqrtConstFold (`Math.sqrt(static final 2.0)`) | 0.545 ± 0.184 | constant folded at JIT time |
| logWrong (discarded) | 10.139 ± 5.793 | **not** eliminated on JDK 21 x86_64 |
| logRight (returned) | 14.338 ± 5.272 | |

- Naive `System.nanoTime` loop, 100M iterations of discarded `Math.sqrt(x)`: rounds 0–4 = `0.0272, 0.1537, 0.0000, 0.0000, 0.0000 ns/op` (the loop body vanished after OSR/C2). Same loop with `Math.log`: `6.828, 7.169, 7.489, 8.093, 8.926 ns/op`. — local experiment.
- `-prof gc` example (`MoneyBench`, 1 fork × 3 × 1 s): summing 100 card fees with `BigDecimal` = 4,357 ns/op and **15,200.030 ± 0.073 B/op**; with `long` cents = 123 ns/op and 0.001 B/op; 10,000 lines: 438,724 ns/op & 1,520,003 B/op vs 14,020 ns/op & 0.096 B/op. The time error bars were ±100–250 %, the B/op error bars ≈0. `-prof stack` on the BigDecimal variant: 48.4 % of RUNNABLE samples in `java.math.BigDecimal.<init>`. — local experiment.

### Inferences
- The `Math.log` surprise is itself a lesson: DCE depends on what the JIT can prove side-effect free, so a "wrong" benchmark is wrong even when it happens to give a plausible number. For a reliable DCE demo use pure arithmetic (`divWrong`, sample 08's `compute`) or `Math.sqrt`, not `Math.log`.
- Teach `gc.alloc.rate.norm` (B/op) as the deterministic, CI-friendly signal; time-based scores need dedicated hardware, many forks, and should not be asserted in tests.
- Payments framing: `BigDecimal` is correct for money but every arithmetic op allocates; the benchmark shows cost proportional to line items (≈152 B per line here).

### Gaps
- `JMHSample_11_Loops` and `_22_FalseSharing` were read, not run as published (I ran my own false-sharing variant, section 4).
- No `perfasm` (no `perf` binary, `perf_event_paranoid=2`), so I cannot show generated assembly proving DCE; the inference rests on timing.

---

## 4. Hardware sympathy: cache lines, false sharing, @Contended, LongAdder

### Takeaway
Two threads writing different fields that share a cache line force the line to bounce between cores (false sharing). The JDK's own fix is `@jdk.internal.vm.annotation.Contended` (used on `Striped64.Cell`, the cell behind `LongAdder`), which pads by `ContendedPaddingWidth` = 128 bytes, but it only works for user classes with `-XX:-RestrictContended` plus `--add-exports`. Manual padding works but the JVM may reorder fields.

### Cited Findings
- `@Contended` Javadoc (JDK 25): "objects and/or their fields are expected to encounter memory contention, generally in the form of 'false sharing'… The effects of this annotation will nearly always add significant space overhead to objects"; supports contention-group tags; class-level use groups all un-annotated fields; "@since 1.8"; package `jdk.internal.vm.annotation`. — [Contended.java @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/jdk/internal/vm/annotation/Contended.java)
- Flags (JDK 25): `ContendedPaddingWidth` 128 ("How many bytes to pad the fields/classes marked @Contended with", range 0–8192), `EnableContended` true, `RestrictContended` true ("Restrict @Contended to trusted classes"). — [globals.hpp @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/runtime/globals.hpp)
- `Striped64` (base of `LongAdder`/`LongAccumulator`): "Table entries are of class Cell; a variant of AtomicLong padded (via @Contended) to reduce cache contention… Atomic objects residing in arrays will tend to be placed adjacent to each other, and so will most often share cache lines (with a huge negative performance impact) without this precaution"; cells are created lazily — "When there is no contention, all updates are made to the base field. Upon first contention (a failed CAS on base update), the table is initialized to size 2" and doubles under further contention; declaration `@jdk.internal.vm.annotation.Contended static final class Cell`. — [Striped64.java @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/atomic/Striped64.java)
- JOL 0.17 layouts on JDK 21 (compressed class pointers, 12-byte header):
  - `Unpadded { volatile long a; volatile long b; }` → `a` @16, `b` @24, instance 32 bytes (same 64-byte line).
  - Manually padded with 16 `long`s → `a` @16, `b` @152, instance 160 bytes.
  - Both fields `@Contended` with `-XX:-RestrictContended` → `a` @144, `b` @280, gaps of 132 and 128 bytes, instance **288 bytes**, "Space losses: 260 bytes internal". — local experiment ([jol-core 0.17](https://maven-central.storage-download.googleapis.com/maven2/org/openjdk/jol/jol-core/0.17/jol-core-0.17.jar), latest release per Maven metadata).
- JMH sample 22 states manual padding "is not versatile because JVMs can freely rearrange the field order, even of the same type". — [JMHSample_22_FalseSharing.java](https://raw.githubusercontent.com/openjdk/jmh/master/jmh-samples/src/main/java/org/openjdk/jmh/samples/JMHSample_22_FalseSharing.java)
- Local false-sharing benchmark (2 threads per @Group, each doing `s.a++` / `s.b++` on its own `volatile long`, avgt ns/op):
  - Run 1 (1 fork × 3 × 1 s): unpadded 46.97 ± 410.07 (u_a 36.4, u_b 57.6), padded 35.03 ± 226.86, contended 35.35 ± 185.03.
  - Run 2 (3 forks × 5 × 1 s): unpadded **33.43 ± 4.63** (u_a 29.17, u_b 37.68), padded **32.03 ± 21.77**, contended **52.76 ± 24.36**.
  - Conclusion: **false sharing could not be demonstrated on this VM**; run 2 contradicts run 1's ordering and all intervals overlap. Possible reasons (unverified): the two JMH threads may land on sibling hyperthreads of one physical core (shared L1/L2, so no line ping-pong), and each volatile `++` is a read + fenced write whose cost may dominate. — local experiment.
- `sun.misc.Unsafe.objectFieldOffset` is `@Deprecated(since="18", forRemoval=true)` in JDK 25, and JDK 24 added warnings on use of sun.misc.Unsafe memory-access methods ("8342380: Implement JEP 498: Warn upon Use of Memory-Access Methods in sun.misc.Unsafe", 2024-11-26). — [sun/misc/Unsafe.java @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.unsupported/share/classes/sun/misc/Unsafe.java); [commit search "JEP 498"](https://api.github.com/search/commits?q=repo:openjdk/jdk+%22JEP+498%22)
- JDK 27 turns on compact object headers by default (section 1), so absolute field offsets shift by ~4 bytes vs JDK 21/25 defaults. — [globals.hpp @ jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/hotspot/share/runtime/globals.hpp)

### Inferences
- The cache-line size of 64 bytes on x86 is common knowledge but I did not find it stated in a fetched source; the JDK pads 128 bytes, which also covers adjacent-line prefetching (rationale not verified).
- For application code (Quarkus services), the practical rule is "use `LongAdder` for hot counters/metrics instead of hand-padding"; hand padding is for library authors.
- Any JOL/offset lab must assert *relative* distance (`|off(b) − off(a)| ≥ 64`) rather than absolute offsets, because headers differ across JDK 21/25 (default) and 27 (compact headers).

### Gaps
- No clean, statistically significant false-sharing speed-up on this VM (two runs disagreed); lesson writers should present the mechanism plus layout evidence, and if they want a timing demo, run JMH sample 22 (`-f 5`, reader/writer pattern) on a bare-metal multi-core laptop and pin threads to different physical cores. Any timing is hardware-dependent.
- Did not verify perfc2c (needs `perf`).

---

## 5. JDK Flight Recorder: starting, dumping, events, the `jfr` tool, views, streaming, JMC, and JDK 24–27 changes

### Takeaway
JFR is built in and cheap enough to run continuously (`default.jfc`); `profile.jfc` doubles sampling. Start it with `-XX:StartFlightRecording` or `jcmd <pid> JFR.start`, dump with `JFR.dump`, and analyse with `jfr summary/print/view` (the `view` subcommand and built-in views arrived in **JDK 21**). JDK 25 added three profiling JEPs (CPU-time sampling on Linux, cooperative sampling, method timing/tracing); JDK 27 added in-process redaction of secrets.

### Cited Findings
**Starting/stopping**
- `-XX:StartFlightRecording:parameter=value` "is equivalent to the `JFR.start` diagnostic command"; `-XX:StartFlightRecording:help` prints options. Parameters (JDK 25 man page): `delay`, `disk` (default true), `dumponexit` (default false), `duration`, `filename` (`%p` = PID, `%t` = timestamp; may be a directory), `name`, `maxage`, `maxsize`, `path-to-gc-roots`, **`report-on-exit=<view>`** ("name of the view to display when the JVM shuts down… use the report-on-exit parameter repeatedly"), `settings` (default `default.jfc` in `JAVA_HOME/lib/jfr`; `profile.jfc` "provides more data than the default configuration, but can have more overhead… Use this configuration for short periods of time"). Event settings inline: `<event-name>#<setting-name>=<value>` ("To add a new event setting, prefix the event name with '+'"). `-Xlog:jfr+startup=warning` silences startup info. — [java.md @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/man/java.md)
- `jcmd` JFR commands (JDK 25 man page): `JFR.check`, `JFR.dump` ("Write data to a file while a flight recording is running"), `JFR.start`, `JFR.stop`, `JFR.view` ("Display event data in predefined views", Impact: Medium). — [jcmd.md @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.jcmd/share/man/jcmd.md)
- Local JDK 21 startup message: `Started recording 1. No limit specified, using maxsize=250MB as default.` and `Use jcmd 27056 JFR.dump name=1 to copy recording data to file.` — local experiment.

**`jfr` tool (JDK 25 man page)**
- Subcommands: `print`, `view`, `configure`, `metadata`, `summary`, `scrub`, `assemble`, `disassemble`. `jfr print [--xml|--json|--exact] [--categories <filters>] [--events <filters>] [--stack-depth <depth>] <file>` (stack depth default 5; example `jfr print --categories GC --events CPULoad recording.jfr`). `jfr view [--verbose] [--width <int>] [--truncate beginning|end] [--cell-height <int>] <view> <file>`; "<view> can be an event type name… `jfr view types <file>`… `jfr view all-views <file>`… `jfr view all-events <file>`"; `--verbose` "Displays the query that makes up the view". The jfr.md text is unchanged in jdk-27-ga except the copyright year. — [jfr.md @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.jfr/share/man/jfr.md), [jfr.md @ jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/jdk.jfr/share/man/jfr.md)
- `jfr view` and its `view.ini` exist in jdk-21-ga (74 views) but not in jdk-20-ga (file 404) → **introduced in JDK 21**. JDK 25 has 83 views, JDK 27 has 84. — [view.ini @ jdk-21-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-21-ga/src/jdk.jfr/share/classes/jdk/jfr/internal/query/view.ini), [view.ini @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.jfr/share/classes/jdk/jfr/internal/query/view.ini), [view.ini @ jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/jdk.jfr/share/classes/jdk/jfr/internal/query/view.ini)
- Views added JDK 21→25: `jvm.blocked-by-system-gc`, `application.deprecated-methods-for-removal`, `jvm.gc-parallel-phases`, `application.cpu-time-hot-methods`, `application.cpu-time-statistics`, `jvm.jdk-agents`, `application.method-timing`, `application.method-calls`, `environment.native-library-failures`. JDK 25→27: `jvm.classes-by-source`. — same view.ini files.
- Most useful views for this track (all in JDK 25): `hot-methods`, `cpu-time-hot-methods`, `allocation-by-site`, `allocation-by-class`, `allocation-by-thread`, `gc`, `gc-pauses`, `gc-pause-phases`, `contention-by-site`, `deoptimizations-by-reason`, `deoptimizations-by-site`, `longest-compilations`, `compiler-statistics`, `exception-by-site`, `latencies-by-type`, `pinned-threads`, `safepoints`, `thread-allocation`, `memory-leaks-by-site`, `vm-operations`. — [view.ini @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.jfr/share/classes/jdk/jfr/internal/query/view.ini)
- View definitions are JFR queries, e.g. `[application.hot-methods]` = `SELECT stackTrace.topFrame AS T, COUNT(*), COUNT(*) FROM ExecutionSample GROUP BY T LIMIT 25`; `[application.allocation-by-site]` = `SELECT stackTrace.topFrame AS S, SUM(weight) AS W FROM ObjectAllocationSample GROUP BY S ORDER BY W DESC LIMIT 25`; `[jvm.deoptimizations-by-reason]` = `SELECT reason, COUNT(reason) AS C FROM Deoptimization GROUP BY reason ORDER BY C DESC`. — same source.

**Event settings (JDK 25 `default.jfc` vs `profile.jfc`)**
- `jdk.ExecutionSample` period 20 ms vs 10 ms; `jdk.NativeMethodSample` 20 ms in both; `jdk.ObjectAllocationSample` throttle 150/s vs 300/s; `jdk.JavaMonitorEnter` and `jdk.ThreadPark` threshold 20 ms vs 10 ms; `jdk.CPUTimeSample` **disabled** in both (throttle 500/s in default, 10ms in profile); `jdk.CPUTimeSamplesLost` enabled; `jdk.MethodTiming`/`jdk.MethodTrace` enabled but with an **empty filter** (so they record nothing until you give a filter); `jdk.SafepointLatency` disabled. — [default.jfc @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.jfr/share/conf/jfr/default.jfc), [profile.jfc @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.jfr/share/conf/jfr/profile.jfc)
- Event types: 159 in JDK 21, 170 in JDK 25, 172 in JDK 27. New 21→25 include `CPUTimeSample`, `CPUTimeSamplesLost`, `MethodTiming`, `MethodTrace`, `SafepointLatency`, `CompilerQueueUtilization`, `JavaMonitorDeflate`, `JavaMonitorNotify`, `JavaMonitorStatistics`, `NativeLibraryLoad/Unload`, `DeprecatedInvocation`, `SwapSpace`; `VirtualThreadPinned` also appears as "new" in metadata.xml, but in JDK 21 it already existed as a Java-defined event (`jdk.internal.event.VirtualThreadPinnedEvent` in [jdk-21-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-21-ga/src/java.base/share/classes/jdk/internal/event/VirtualThreadPinnedEvent.java)), so this is a move to the native definition, not a new capability; removed: `GCLocker`, `SafepointCleanup`, `SafepointCleanupTask`, `ZUnmap`. New 25→27: `ShenandoahPromotionInformation`, `StringDeduplication`. — [metadata.xml @ jdk-21-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-21-ga/src/hotspot/share/jfr/metadata/metadata.xml), [@ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/jfr/metadata/metadata.xml), [@ jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/hotspot/share/jfr/metadata/metadata.xml) (note: `VirtualThreadPinned` appearing as "new" may reflect a rename/move in metadata.xml rather than a new capability — not verified)

**JDK 25 profiling JEPs (number/title verified via implementation commits; presence verified in jdk-25-ga source)**
- **JEP 509: JFR CPU-Time Profiling** — commit "8342818: Implement JEP 509: JFR CPU-Time Profiling" (2025-06-04), backed out and redone the next day ("8358666: [REDO] Implement JEP 509", 2025-06-05). Event `jdk.CPUTimeSample` is marked `experimental="true"` in jdk-25-ga metadata: "Snapshot of a threads state from the CPU time sampler, both threads executing native and Java code are included. The throttle setting can be either an upper bound for the event emission rate, e.g. 100/s, or the cpu-time period, e.g. 10ms"; fields `stackTrace`, `eventThread`, `failed`, `samplingPeriod`, `biased` ("The sample is safepoint-biased"). Mechanism in source: per-thread POSIX timer — `pthread_getcpuclockid` + `timer_create(clock, &sev, …)` with `SIGEV_THREAD_ID` and `SIGPROF` (Linux-specific). Views `cpu-time-hot-methods`, `cpu-time-statistics`. — [commit search "JEP 509"](https://api.github.com/search/commits?q=repo:openjdk/jdk+%22JEP+509%22); [metadata.xml @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/jfr/metadata/metadata.xml); [jfrCPUTimeThreadSampler.cpp @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/jfr/periodic/sampling/jfrCPUTimeThreadSampler.cpp)
- **JEP 518: JFR Cooperative Sampling** — commit "8352251: Implement JEP 518: JFR Cooperative Sampling" (2025-05-26). Mechanism in jdk-25-ga source: the sampler records a sample request (pc/sp/bcp) and calls `SafepointMechanism::arm_local_poll_release(jt)` so the *target thread itself* completes the stack walk at its next safepoint poll; "A biased sample request is denoted by an empty bcp and an empty pc"; the request time is reused as the start time of the new `jdk.SafepointLatency` event. — [commit search "JEP 518"](https://api.github.com/search/commits?q=repo:openjdk/jdk+%22JEP+518%3A%22); [jfrSampleRequest.cpp @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/jfr/periodic/sampling/jfrSampleRequest.cpp)
- **JEP 520: JFR Method Timing and Tracing** — commit "8352738: Implement JEP 520: JFR Method Timing and Tracing" (2025-05-29). Events `jdk.MethodTiming` (period `endChunk`) and `jdk.MethodTrace` (threshold 0 ms, with stack trace); .jfc options `method-timing` / `method-trace` whose filter "can be an annotation (@jakarta.ws.rs.GET), a full qualified class name (com.example.Foo), a fully qualified method reference (java.lang.HashMap::resize) or a class initializer (::<clinit>). Use <init> for constructors. Separate multiple filters with semicolon." Views: `method-timing` (Invocations, Minimum/Average/Maximum Time) and `method-calls` (Traced Method, Caller, Invocations). — [commit search "JEP 520"](https://api.github.com/search/commits?q=repo:openjdk/jdk+%22JEP+520%3A%22); [default.jfc @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.jfr/share/conf/jfr/default.jfc); [view.ini @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.jfr/share/classes/jdk/jfr/internal/query/view.ini)
- Inferred command lines (built from the documented `option=value` / `event#setting=value` syntax and option names; **not executed**, JDK 25 not installed): `java -XX:StartFlightRecording:method-timing='com.acme.pay.FeeService::calculate',report-on-exit=method-timing ...`; `java -XX:StartFlightRecording:jdk.CPUTimeSample#enabled=true,jdk.CPUTimeSample#throttle=10ms,filename=cpu.jfr ...` then `jfr view cpu-time-hot-methods cpu.jfr`; for Quarkus REST endpoints the annotation filter form `@jakarta.ws.rs.GET` applies.

**JDK 27: JEP 536 JFR In-Process Data Redaction**
- Commit "8367584: Implement JEP 536: JFR In-Process Data Redaction" (2026-06-03). jdk-27-ga `java.md` documents `-XX:FlightRecorderOptions` `redact-argument=<glob;glob>` (e.g. `*secret*;password*`, case-insensitive, `@file` to load patterns, `+` prefix to add to defaults, `none` to disable, replaced with `[REDACTED]`, best-effort: applies to `jdk.JVMInformation` arguments, `java.command` in `jdk.InitialSystemProperty`, and matching text in `jdk.InitialEnvironmentVariable`; "`jdk.ProcessStart` (child processes) are not redacted") and `redact-key=` for env vars/system properties by key. — [java.md @ jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/java.base/share/man/java.md); [commit search "JEP 536"](https://api.github.com/search/commits?q=repo:openjdk/jdk+%22JEP+536%22)

**Streaming and programmatic parsing**
- `jdk.jfr.consumer.RecordingStream` — "A recording stream produces events from the current JVM", `@since 14` (this is JFR Event Streaming, JEP 349 — the JEP number is from memory; GitHub commit search found no "JEP 349" commit and the JEP page was unreachable), with `onEvent(String, Consumer<RecordedEvent>)`, `onFlush`, `setMaxAge`, `start()`, `startAsync()`. — [RecordingStream.java @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.jfr/share/classes/jdk/jfr/consumer/RecordingStream.java)
- `jdk.jfr.consumer.RecordingFile` — `@since 9`; `hasMoreEvents()`, `readEvent()`, `readEventTypes()`, `static readAllEvents(Path)`, `write(Path, Predicate<RecordedEvent>)` `@since 19`. — [RecordingFile.java @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.jfr/share/classes/jdk/jfr/consumer/RecordingFile.java)

**Leyden / AOT (profiling-adjacent), JEP numbers verified via commits; flags verified in GA source**
- JEP 483 "Ahead-of-Time Class Loading & Linking" (commit 2024-11-15 → JDK 24); JEP 514 "Ahead-of-Time Command Line Ergonomics" (2025-05-28 → JDK 25); **JEP 515 "Ahead-of-Time Method Profiling"** (2025-05-28 → JDK 25); JEP 516 "Ahead-of-Time Object Caching with Any GC" (2025-11-07 → JDK 26); **JEP 544 "Ahead-of-Time Code Compilation"** (commit 2026-10-08, i.e. after JDK 27 GA → in mainline for JDK 28, unreleased). — [commit search "JEP 515"](https://api.github.com/search/commits?q=repo:openjdk/jdk+%22JEP+515%3A%22), [commit search "JEP 544"](https://api.github.com/search/commits?q=repo:openjdk/jdk+%22JEP+544%22)
- jdk-25-ga `cds_globals.hpp` contains `AOTMode`, `AOTConfiguration`, `AOTCache`, `AOTCacheOutput`, `AOTRecordTraining`, `AOTReplayTraining`, `AOTCompileEagerly`, `AOTAdapterCaching`, `AOTStubCaching` (all product flags; training flags default false). — [cds_globals.hpp @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/cds/cds_globals.hpp)

**JDK Mission Control**
- JMC is developed at `openjdk/jmc`; master `pom.xml` has `<revision>10.0.0</revision>` (in development); building it requires JDK 21 in the Maven toolchain; builds are distributed by several vendors (README lists "Released version" downloads per vendor; Red Hat ships it in RHEL). — [openjdk/jmc README](https://raw.githubusercontent.com/openjdk/jmc/master/README.md), [openjdk/jmc pom.xml](https://raw.githubusercontent.com/openjdk/jmc/master/pom.xml)

**Local JFR observations (JDK 21)**
- 15 s `settings=profile` recording of the 4-thread payment simulation: `jdk.ExecutionSample` 418 events, `jdk.ObjectAllocationSample` 4,085, `jdk.GCPhaseParallel` 29,309 (largest by size, 777,542 B), file 1.33 MB. — local experiment.
- JDK 21's view title reads "Java Methods that Executes the Most" (typo); JDK 25 view.ini reads "Java Methods that Execute the Most". — local run vs [view.ini @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.jfr/share/classes/jdk/jfr/internal/query/view.ini)

### Inferences
- The classic JFR `ExecutionSample` gives few samples (418 over 15 s × 4 busy threads at a nominal 10 ms period here), consistent with JFR sampling only a subset of threads per period; for CPU-hot-path work on Linux JDK 25+, enable `jdk.CPUTimeSample` (experimental) or use async-profiler. (The "subset of threads" mechanism is an inference; I did not verify the per-period thread cap in source.)
- `report-on-exit=allocation-by-site` (JDK 25) is a zero-tooling way to show learners an allocation profile in CI logs.
- Payments relevance: JFR records command lines/env vars by default; JDK 27 redaction (`redact-argument`, `redact-key`) matters for PCI-DSS secrets hygiene when shipping recordings to vendors.

### Gaps
- Could not read inside.java (Erik Gahlin's posts) or Oracle's JFR/JMC docs (blocked).
- JMC's latest GA version number could not be confirmed (GitHub tags API returned nothing; README does not state it).
- JEP 518/509/520 user-facing claims (overhead numbers, exact recommended command lines) not verified because JEP pages were unreachable.

---

## 6. async-profiler (4.6): modes, safepoint bias, AsyncGetCallTrace vs VM structs, flame graphs

### Takeaway
async-profiler samples stacks asynchronously (via perf_events/timers + signals) so it is not limited to safepoint polls, sees native/JVM/kernel frames and GC/JIT threads, and offers cpu, wall, alloc, lock, nativemem and method-tracing modes. Since 4.2 it walks Java stacks with its own HotSpot "VM structs" walker by default instead of `AsyncGetCallTrace`. A flame graph's x-axis is *population sorted alphabetically*, not time.

### Cited Findings
- "This project is a low overhead sampling profiler for Java that does not suffer from the Safepoint bias problem. It features HotSpot-specific API to collect stack traces and to track memory allocations… Unlike traditional Java profilers, async-profiler monitors non-Java threads (e.g., GC and JIT compiler threads) and shows native and kernel frames in stack traces." Stable release **4.6**. — [async-profiler README](https://raw.githubusercontent.com/async-profiler/async-profiler/master/README.md); release artifact [async-profiler-4.6-linux-x64.tar.gz](https://github.com/async-profiler/async-profiler/releases/download/v4.6/async-profiler-4.6-linux-x64.tar.gz) (`asprof --version`: "Async-profiler 4.6 built on Oct 12 2026"); Maven Central `tools.profiler:async-profiler` latest 4.6 ([metadata](https://maven-central.storage-download.googleapis.com/maven2/tools/profiler/async-profiler/maven-metadata.xml)).
- CPU mode: "receiving call stacks generated by `perf_events` and matching them up with call stacks generated by `AsyncGetCallTrace`"; advantages vs raw perf: no `-XX:+PreserveFramePointer` ("overhead that can be sometimes as high as 10%"), no address-translation agent, shows interpreter frames, no perf.data files. — [ProfilingModes.md](https://raw.githubusercontent.com/async-profiler/async-profiler/master/docs/ProfilingModes.md)
- Stack walking: "AsyncGetCallTrace (AGCT) is a non-standard extension of HotSpot JVM to obtain Java stack traces outside safepoints… it even got its name after this function… was broken several times even in minor JDK updates, e.g. JDK-8307549… can crash JVM… `vm` stack walking mode based on HotSpot VM Structs was introduced… Since async-profiler 4.2, this is the default mode when running on the HotSpot JVM." `vmx` = mixed Java/native interleaved stacks. Before 4.2 the default C-stack walker was frame pointers. — [StackWalkingModes.md](https://raw.githubusercontent.com/async-profiler/async-profiler/master/docs/StackWalkingModes.md)
- Allocation mode: TLAB-driven sampling using HotSpot callbacks "when an object is allocated in a newly created TLAB; when an object is allocated on a slow path outside TLAB"; `--alloc 500k` ≈ one sample per 500 KB; "the top frame of every call trace is the class of the allocated object, and the counter is the heap pressure"; does not disturb escape analysis. — [ProfilingModes.md](https://raw.githubusercontent.com/async-profiler/async-profiler/master/docs/ProfilingModes.md)
- Wall mode: "`-e wall` … sample all threads equally every given period of time regardless of thread status: Running, Sleeping or Blocked… most useful in per-thread mode: `-t`", e.g. `asprof -e wall -t -i 50ms -f result.html 8983`. Lock mode: "the top frame is the class of lock/monitor, and the counter is number of nanoseconds it took to enter this lock/monitor", e.g. `asprof -e lock -t -i 5ms -f result.html 8983`. Java method mode: `-e ClassName.methodName`. Multiple events: `-agentpath:/path/to/libasyncProfiler.so=start,event=cpu,alloc=2m,lock=10ms,file=profile.jfr`. — [ProfilingModes.md](https://raw.githubusercontent.com/async-profiler/async-profiler/master/docs/ProfilingModes.md)
- Options: `-i` interval "For CPU profiling, it's CPU time in nanoseconds… may be followed by `s`, `ms`, `us`, `ns`"; `--cstack fp|dwarf|vm|vmx|no`; `-a/--ann` annotates "JIT compiled methods with `_[j]`, inlined methods with `_[i]`, interpreted methods with `_[0]` and C1 compiled methods with `_[1]`"; `--all` enables cpu, wall, alloc, live, lock, nativelock, nativemem, proc ("not recommended for production"). — [ProfilerOptions.md](https://raw.githubusercontent.com/async-profiler/async-profiler/master/docs/ProfilerOptions.md); 4.6 `asprof --help` also lists `--ttsp` ("only time-to-safepoint profiling"), `--trace method`, `-o flat|traces|collapsed|flamegraph|tree|jfr|otlp`, `--reverse`, `--inverted` — local run.
- perf_events can be unavailable when `/proc/sys/kernel/perf_event_paranoid` ≥ 2, under seccomp in containers, or under hypervisors; fallback "`-e ctimer` … similar to `cpu` mode, but does not require perf_events support… no kernel stack traces". — [Troubleshooting.md](https://raw.githubusercontent.com/async-profiler/async-profiler/master/docs/Troubleshooting.md)
- Flame-graph colours (async-profiler HTML): image legend shows Kernel (orange), Native (red/salmon), C++ (yellow-olive), C1 compiled (light yellow-green), Interpreted (pale green), Java inlined (aqua), Java compiled (green), and "Match found" (magenta, search hits). — [flamegraph_colors.png](https://raw.githubusercontent.com/async-profiler/async-profiler/master/.assets/images/flamegraph_colors.png), referenced by [FlamegraphInterpretation.md](https://raw.githubusercontent.com/async-profiler/async-profiler/master/docs/FlamegraphInterpretation.md)
- Reading flame graphs (async-profiler doc): samples are "alphabetically sorted at the base level… X-axis is no longer a timeline. Flame graph does not preserve information on _when_ a particular stack trace was taken, it only indicates _how often_"; frames for the same function at the same depth are merged; the functions with wide *tops* (self time) are the optimisation candidates. — [FlamegraphInterpretation.md](https://raw.githubusercontent.com/async-profiler/async-profiler/master/docs/FlamegraphInterpretation.md)
- Brendan Gregg (flamegraph.pl header): "The output flame graph shows relative presence of functions in stack samples. The ordering on the x-axis has no meaning; since the data is samples, time order of events is not known. The order used sorts function names alphabetically… By default, the colors are selected at random (except for differentials)." Options `--reverse` ("stack-reversed flame graph"), `--inverted` ("icicle graph"), `--flamechart` ("sort by time, do not merge stacks"), `--countname` ("samples" → e.g. "bytes"); differential flame graphs colour "red for more, and blue for less". With `--color=java`: "green == Java, yellow == C++, red == user-mode native, orange == kernel". — [flamegraph.pl](https://raw.githubusercontent.com/brendangregg/FlameGraph/master/flamegraph.pl), [FlameGraph README](https://raw.githubusercontent.com/brendangregg/FlameGraph/master/README.md)

**Local async-profiler 4.6 run (JDK 21, 10 s, `-agentpath:…=start,event=cpu,interval=1ms,file=cpu-slow.collapsed,collapsed`)** on the "before" payment code: 8,005 CPU samples; inclusive share `PaymentSim.feeSlow` 71.8 %, `java.util.Formatter.format` 21.8 %, `java.util.regex.Pattern.compile` 17.7 %, `BigDecimal.<init>` 8.0 %, G1 GC frames ≈8 %, C2 compiler threads ≈9 %; top self frames: `Pattern.compile` 825, `__vdso_clock_gettime` 608 (the benchmark's own `System.nanoTime` calls), `BigDecimal.<init>` 473, `String.getBytes` 325, `SpinPause` 319. Alloc mode (sample counts): inclusive `Pattern.compile` 39.3 %, `Formatter.format` 21.4 %, `Matcher.<init>` 5.9 %, `BigDecimal.<init>` 4.2 %. `perf_event_paranoid` was 2 on this VM; profiling still worked without warnings in this setup. — local experiment.

### Inferences
- Safepoint bias explained (standard explanation; the README links Nitsan Wakart's post which I could not fetch): JVMTI `GetAllStackTraces`-style profilers can only observe threads at safepoint polls (method returns / loop back-edges in compiled code), so samples pile up at those points and tight inlined loops look "free". async-profiler avoids this by signalling the thread and walking its stack at the exact interrupted PC. JFR's own sampler is now partly safepoint-based by design (JEP 518), but keeps the *recorded PC* from the sampling instant and flags biased samples (`biased` field) — so "uses safepoints" ≠ "safepoint-biased".
- Measurement code shows up in profiles (`__vdso_clock_gettime` at 7.6 % of samples) — a nice reminder that instrumentation has a cost.

### Gaps
- Nitsan Wakart's safepoint-bias post, Andrei Pangin's talks/wiki pages beyond the repo docs, and brendangregg.com pages were not fetched (blocked).
- I did not check which mode (`perf_events` vs `ctimer`) async-profiler actually selected on this VM.

---

## 7. Worked end-to-end investigation: latency → JFR → flame graph → allocation hot spot → fix → JMH proof

### Takeaway
A reproducible payments-flavoured scenario: a fee calculator that (1) compiles a regex per request, (2) `String.format`s a DEBUG log line that is then discarded, and (3) re-creates constant `BigDecimal`s. JFR's `allocation-by-site` and a `RecordingFile` parser point at the exact source lines; async-profiler confirms; the fix cuts allocation from 2,032 to 72 B/op in JMH and GC pauses from 129 to 36 over 15 s.

### Cited Findings (all local experiments, JDK 21.0.12, 4 vCPU VM, `-Xmx256m`, 4 worker threads hammering the method, 15 s, latency via fixed-bucket histogram)
- **Before** (`feeSlow`): 604,529 req/s; p50 < 0.7 µs, p99 < 3.9 µs, p99.9 < 35.3 µs, **p99.99 < 13.6 ms**; 130 GCs, 996 ms GC time. `jfr view gc-pauses`: 129 pauses, total 984 ms, median 2.98 ms.
- `jfr view hot-methods` (top): `AbstractStringBuilder.ensureCapacityInternal` 22.49 %, `BigDecimal.<init>(char[],int,int,MathContext)` 11.48 %, `Pattern.compile()` 9.57 %, `Formatter$Conversion.isText` 9.09 %, `Long.getChars` 7.18 %, `PaymentSim.feeSlow` 5.74 %.
- `jfr view allocation-by-site` (top): `Formatter.parse` 12.48 %, `Pattern.compile()` 10.34 %, `PaymentSim.feeSlow` 10.12 %, `Arrays.copyOf` 7.92 %, `Pattern$BitClass.<init>` 7.80 %, `Matcher.<init>` 7.44 %.
- `RecordingFile` parser (lab model solution, first application frame, weighted by `weight`): line 17 (`Pattern.compile(...)`) 34.7 %, line 22 (`String.format(...)`) 31.9 %, line 23 (`toPlainString()` args) 15.9 %, line 20 (`new BigDecimal("0.029")`, `new BigDecimal("0.30")`) 8.9 %, line 19 (`new BigDecimal(amount)`) 5.4 %.
- `jfr print --events jdk.ObjectAllocationSample --stack-depth 8` output shape: `objectClass = …`, `weight = 20.6 MB`, `eventThread = "main"`, `stackTrace = [ … line: N … ]`.
- **After round 1** (precompiled `Pattern`, constant `BigDecimal`s, `if (LOG.debugEnabled)` guard): 3,355,692 req/s; p99 < 0.3 µs, p99.9 < 1.8 µs, **p99.99 < 35.6 µs**; 79 GCs (803 ms; 78 pauses, median 2.38 ms). Re-profiling: 94.8 % of remaining allocation at line 31 = `CCY.matcher(...)` (`Matcher.<init>` lines 251/253) — the *next* hot spot.
- **After round 2** (replace regex with a 3-char check): 4,292,668 req/s; p99.9 < 0.8 µs, p99.99 < 28.4 µs; 37 GCs, 426 ms (36 pauses, total 413 ms). Remaining allocation: 99.7 % at `new BigDecimal(p.amount())` (via `StringLatin1.toChars`).
- Max latency stayed 0.37–0.53 s in all three variants (environmental: shared VM, 4 busy threads on 4 vCPUs plus GC/JIT threads) — do not present max as an effect of the fix.
- **JMH proof** (`FeeBench`, 2 forks × 5 × 1 s, `-prof gc`): `before` 845.880 ± 338.287 ns/op, **2,032.006 ± 0.002 B/op**; `after1_hoistAndGuard` 149.884 ± 50.173 ns/op, **200.001 ± 0.001 B/op**; `after2_noRegex` 62.337 ± 16.858 ns/op, **72.000 ± 0.001 B/op**.

### Inferences
- The story arc for the lesson: symptom = tail latency (p99.99) and GC frequency, not average; tool 1 = JFR (always-on, `jfr view gc-pauses` → `allocation-by-site`); tool 2 = async-profiler flame graph to see *who calls* the allocating code; fix; then JMH with `-prof gc` as the regression-proof artifact (B/op is stable enough to gate in CI, time is not).
- "Fix one, re-profile" matters: round 1 exposed `Matcher` allocation that was invisible before.
- Quarkus/payments mapping: DEBUG-log formatting without guards (JBoss Logging supports parameterized `debugf`), per-request `Pattern.compile` in validators, and `BigDecimal` constants created inline are common in real fee/FX code (inference, not measured in Quarkus itself).

### Gaps
- Not run inside Quarkus or on JDK 25; the recipe uses only JDK tools available in both.
- No HTML flame graph screenshot included (the HTML was generated locally at a scratch path; lesson writers should regenerate).

---

## 8. Misconceptions to address (with evidence)

### Takeaway
Five beliefs the course should actively dismantle, each with a demo from the experiments above.

### Cited Findings
- "Microbenchmarks with nanoTime are fine": the naive sqrt loop reported 0.0000 ns/op after warm-up (code eliminated), while the naive log loop reported 7–9 ns/op and *drifted upward* across rounds — neither is trustworthy without JMH's controls. JMH's own disclaimer: "The numbers below are just data… Do not assume the numbers tell you what you want them to tell." — local experiment; JMH 1.37 output.
- "`final` makes methods faster": C2 devirtualizes and inlines based on *receiver type profiles* (`TypeProfile (977323/977323 counts) = Hot$Square` → inlined) regardless of `final`; a megamorphic site becomes `virtual call`. Inlining limits are bytecode-size based (MaxInlineSize/FreqInlineSize). — local PrintInlining; [bytecodeInfo.cpp @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/opto/bytecodeInfo.cpp). (Note: `final` *fields* do matter for constant folding — see JMH sample 10 — which is why `final` is a benchmarking hazard, not a speed-up.)
- "JIT output is stable across runs": three identical runs compiled `longLoop` first at 40, 47, 60 ms with different interleavings; the compile *policy* depends on queue lengths and timing (`s = queue_size_X / (TierXLoadFeedback * compiler_count_X) + 1`). — local experiment; [compilationPolicy.hpp @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/compiler/compilationPolicy.hpp)
- "A profiler that uses safepoints is accurate": async-profiler's README positions itself against the "Safepoint bias problem"; JDK 25's JFR marks samples with a `biased` field ("The sample is safepoint-biased") precisely because the bias exists. — [async-profiler README](https://raw.githubusercontent.com/async-profiler/async-profiler/master/README.md); [metadata.xml @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/jfr/metadata/metadata.xml)
- "More threads = more throughput": Striped64's own comment — contended atomics in adjacent memory "will most often share cache lines (with a huge negative performance impact)"; (my own false-sharing benchmark was inconclusive on a shared VM, so cite the JDK comment and JMH sample 22 rather than local timings); and the investigation shows GC/JIT threads competing for the same 4 vCPUs (≈8 % G1, ≈9 % C2 samples). — [Striped64.java @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/atomic/Striped64.java); local experiments.
- Bonus: "flame graph x-axis is time" — explicitly false per Gregg and async-profiler docs (section 6).

### Inferences
- Pair each misconception with a 2-minute demo; learners believe their own terminal more than slides.

### Gaps
- No Amdahl/USL citation fetched for the threads misconception; rely on the experiments.

---

## 9. Lab exercises gradable deterministically with JUnit (no timing assertions)

### Takeaway
Grade structure and invariants (field-offset distances, allocation counts, JFR-derived facts, source shape), never nanoseconds.

### Cited Findings (APIs/tools verified above)
- JOL `ClassLayout.parseClass(X.class)` exposes field offsets (used locally on JDK 21; output reflects the real VM layout, including `@Contended` gaps). — local experiment with jol-core 0.17.
- `jdk.jfr.consumer.RecordingFile.readAllEvents(Path)` / `readEvent()`; `RecordedEvent.getStackTrace().getFrames()`; `RecordedFrame.getMethod().getType().getName()`, `getLineNumber()`; `e.getLong("weight")` on `jdk.ObjectAllocationSample`. — [RecordingFile.java @ jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.jfr/share/classes/jdk/jfr/consumer/RecordingFile.java); local `TopAllocSite` program compiled and ran on JDK 21.
- JMH's annotation processor generates `META-INF/BenchmarkList` at compile time (observed locally), so "does it compile as a JMH benchmark" is checkable. — local experiment.
- `jdk.jfr.Recording` can be started programmatically in a test (API exists since JDK 9 alongside RecordingFile; not separately fetched — see Gaps).

### Inferences — proposed labs with expected outcomes
1. **Padded counter** — learner writes `PaddedCounters { volatile long a; …; volatile long b; }` (manual padding or `@Contended` + documented JVM flags in the build's test `jvmArgs`). JUnit: JOL `ClassLayout.parseClass(...).fields()` → assert `abs(offset(b) − offset(a)) >= 64` (or ≥128 for `@Contended`). Expected: unpadded fails (8 bytes apart), padded passes. Robust across JDK 21/25/27 header layouts because it checks distance.
2. **Fix the dead-code benchmark** — provide a JMH class with `void measureWrong() { compute(x); }` and `private final int x = 42`. Grading via reflection/ASM or source parsing: every `@Benchmark` method returns non-void or takes a `Blackhole` parameter; no `final` fields in `@State` classes used as inputs; class has `@State`, `@Fork(≥1)`, `@Warmup`, `@Measurement`; build produces `META-INF/BenchmarkList` containing the method. Expected: original fails 2 checks, fixed passes.
3. **Top allocation site from a JFR file** — commit a small `.jfr` produced by the course's `PaymentSim slow` (or generate it in `@BeforeAll` with `jdk.jfr.Recording` + `settings=profile`); learner implements `TopAllocSite.firstAppFrame(Path, String pkg)`. JUnit asserts the top site is `PaymentSim.feeSlow` at the `Pattern.compile` line (line 17 in the reference program, 34.7 % share in my run). Deterministic if graded on a *committed* recording; if generated live, assert only the method name (sampling).
4. **Allocation budget** — learner refactors `feeSlow`; JUnit measures `com.sun.management.ThreadMXBean.getThreadAllocatedBytes` around 100k warm calls and asserts < 300 B/call (reference: 2,032 B/op before, 72–200 B/op after per JMH). Deterministic enough because allocation, unlike time, is stable (B/op error ±0.002). (ThreadMXBean API not fetched in this session — mark as to-verify.)
5. **Read PrintCompilation** — give a captured log (section 2 verbatim lines); learner writes a parser returning `{compileId, tier, osr, osrBci, method, bytes, madeNotEntrant}`; JUnit checks parsed records for the provided fixture (including JDK 25's `made not entrant: <reason>` variant).
6. **Megamorphic detection** — fixture PrintInlining text; learner classifies call sites as `inline (hot)` vs `virtual call` vs `too big`.

### Gaps
- `jdk.jfr.Recording`, `ThreadMXBean.getThreadAllocatedBytes` and JOL's `fields()` API surface were used from memory/locally, not fetched as docs this session.

---

## Verified URLs

Pages/files actually fetched in this session (via curl/raw GitHub or tool output):
- OpenJDK HotSpot source (GA tags): https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/compiler/compiler_globals.hpp · https://raw.githubusercontent.com/openjdk/jdk/jdk-21-ga/src/hotspot/share/compiler/compiler_globals.hpp · https://raw.githubusercontent.com/openjdk/jdk/jdk-26-ga/src/hotspot/share/compiler/compiler_globals.hpp · https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/hotspot/share/compiler/compiler_globals.hpp · https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/opto/c2_globals.hpp · https://raw.githubusercontent.com/openjdk/jdk/jdk-21-ga/src/hotspot/share/opto/c2_globals.hpp · https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/hotspot/share/opto/c2_globals.hpp · https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/cpu/x86/c2_globals_x86.hpp · https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/hotspot/cpu/x86/c2_globals_x86.hpp · https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/runtime/globals.hpp · https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/hotspot/share/runtime/globals.hpp · https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/compiler/compilerDefinitions.cpp · https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/compiler/compilerDefinitions.hpp · https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/compiler/compilationPolicy.hpp · https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/opto/bytecodeInfo.cpp · https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/compiler/compileTask.cpp · https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/code/nmethod.cpp · https://raw.githubusercontent.com/openjdk/jdk/jdk-21-ga/src/hotspot/share/code/nmethod.cpp · https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/runtime/deoptimization.cpp · https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/compiler/compilationPolicy.cpp · https://raw.githubusercontent.com/openjdk/jdk/jdk-17-ga/src/hotspot/share/compiler/compilerOracle.hpp · https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/cds/cds_globals.hpp · https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/hotspot/share/cds/cds_globals.hpp
- JFR source/config/man pages: https://raw.githubusercontent.com/openjdk/jdk/jdk-21-ga/src/hotspot/share/jfr/metadata/metadata.xml · https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/jfr/metadata/metadata.xml · https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/hotspot/share/jfr/metadata/metadata.xml · https://raw.githubusercontent.com/openjdk/jdk/jdk-21-ga/src/jdk.jfr/share/classes/jdk/jfr/internal/query/view.ini · https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.jfr/share/classes/jdk/jfr/internal/query/view.ini · https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/jdk.jfr/share/classes/jdk/jfr/internal/query/view.ini · https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.jfr/share/conf/jfr/default.jfc · https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.jfr/share/conf/jfr/profile.jfc · https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.jfr/share/man/jfr.md · https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/jdk.jfr/share/man/jfr.md · https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/man/java.md · https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/java.base/share/man/java.md · https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.jcmd/share/man/jcmd.md · https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.jfr/share/classes/jdk/jfr/consumer/RecordingStream.java · https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.jfr/share/classes/jdk/jfr/consumer/RecordingFile.java · https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/jfr/periodic/sampling/jfrSampleRequest.cpp · https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/jfr/periodic/sampling/jfrCPUTimeThreadSampler.cpp
- JDK library source: https://raw.githubusercontent.com/openjdk/jdk/jdk-21-ga/src/java.base/share/classes/jdk/internal/event/VirtualThreadPinnedEvent.java · https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/atomic/Striped64.java · https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/jdk/internal/vm/annotation/Contended.java · https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.unsupported/share/classes/sun/misc/Unsafe.java
- JEP verification via GitHub commit search (openjdk/jdk): https://api.github.com/search/commits?q=repo:openjdk/jdk+%22JEP+509%22 (and the same query form for JEPs 450, 483, 498, 514, 515, 516, 518, 519, 520, 523, 534, 536, 544, plus "HotCodeHeap" and "lukewarm")
- JMH: https://raw.githubusercontent.com/openjdk/jmh/master/jmh-samples/src/main/java/org/openjdk/jmh/samples/JMHSample_08_DeadCode.java · …/JMHSample_09_Blackholes.java · …/JMHSample_10_ConstantFold.java · …/JMHSample_11_Loops.java · …/JMHSample_22_FalseSharing.java · …/JMHSample_35_Profilers.java (also fetched 01, 02, 03, 05, 12, 13, 16, 21, 25, 27, 34, 36, 37, 38) · https://raw.githubusercontent.com/openjdk/jmh/master/pom.xml · https://maven-central.storage-download.googleapis.com/maven2/org/openjdk/jmh/jmh-core/maven-metadata.xml · https://maven-central.storage-download.googleapis.com/maven2/org/openjdk/jmh/jmh-core/1.37/jmh-core-1.37.jar · https://maven-central.storage-download.googleapis.com/maven2/org/openjdk/jmh/jmh-generator-annprocess/1.37/jmh-generator-annprocess-1.37.jar · https://maven-central.storage-download.googleapis.com/maven2/org/openjdk/jol/jol-core/maven-metadata.xml
- async-profiler: https://raw.githubusercontent.com/async-profiler/async-profiler/master/README.md · https://raw.githubusercontent.com/async-profiler/async-profiler/master/docs/ProfilingModes.md · https://raw.githubusercontent.com/async-profiler/async-profiler/master/docs/StackWalkingModes.md · https://raw.githubusercontent.com/async-profiler/async-profiler/master/docs/ProfilerOptions.md · https://raw.githubusercontent.com/async-profiler/async-profiler/master/docs/FlamegraphInterpretation.md · https://raw.githubusercontent.com/async-profiler/async-profiler/master/docs/Troubleshooting.md · https://raw.githubusercontent.com/async-profiler/async-profiler/master/.assets/images/flamegraph_colors.png · https://github.com/async-profiler/async-profiler/releases/download/v4.6/async-profiler-4.6-linux-x64.tar.gz · https://maven-central.storage-download.googleapis.com/maven2/tools/profiler/async-profiler/maven-metadata.xml
- Brendan Gregg: https://raw.githubusercontent.com/brendangregg/FlameGraph/master/README.md · https://raw.githubusercontent.com/brendangregg/FlameGraph/master/flamegraph.pl
- JMC / JITWatch: https://raw.githubusercontent.com/openjdk/jmc/master/README.md · https://raw.githubusercontent.com/openjdk/jmc/master/pom.xml · https://raw.githubusercontent.com/AdoptOpenJDK/jitwatch/master/README.md · https://raw.githubusercontent.com/AdoptOpenJDK/jitwatch/master/scripts/makeDemoLogFile.sh · https://raw.githubusercontent.com/wiki/AdoptOpenJDK/jitwatch/Instructions.md

Not reachable (blocked by the session's network policy; nothing cited from them): openjdk.org (JEP pages incl. 509/518/520/515, bugs.openjdk.org), docs.oracle.com (JFR/JMC guides), inside.java, brendangregg.com, shipilev.net, psy-lob-saw.blogspot.com.

---

## Teaching notes

### Takeaway
Teach with live terminal evidence: every claim in the track has a 1–3 minute demo from the experiments above, and every lab is graded on allocation, layout or parsed output, never wall-clock time.

### Suggested 7-lesson mapping
1. **Execution pipeline** — tiers 0–4, thresholds (200 / 5000; OSR back-edge 60000 / 40000), code cache 240 MB segmented. Demo: `Hot.java` with `-XX:+PrintCompilation`; read one OSR line column by column. Lab 5 (parser).
2. **What the JIT bets on** — inlining (35/325 bytecodes, 2500 B compiled), type profiles, megamorphic call sites, EA, loop opts, intrinsics, uncommon traps/deopt. Demo: PrintInlining `inline (hot)` → `virtual call`; `-Xlog:deoptimization=debug` showing `class_check maybe_recompile`. Lab 6.
3. **Benchmarking honestly with JMH** — DCE, constant folding, loops, warm-up/forks, Blackhole, @State scopes, @Param, modes, `-prof gc`/`stack`. Demo: naive sqrt loop printing 0.0000 ns/op next to JMH baseline/Wrong/Right; the `Math.log` twist. Lab 2.
4. **Hardware sympathy** — cache lines, false sharing, `@Contended` (+ `-XX:-RestrictContended`, `--add-exports java.base/jdk.internal.vm.annotation=ALL-UNNAMED`), LongAdder's Cell. Demo: JOL layouts (32 → 160 → 288 bytes). Lab 1.
5. **JFR** — `-XX:StartFlightRecording`, `jcmd JFR.start/dump/view`, default vs profile, `jfr summary/print/view`, built-in views, streaming, JMC; JDK 25 CPU-time sampling/method timing; JDK 27 redaction. Demo: `report-on-exit=allocation-by-site` (JDK 25). Lab 3.
6. **async-profiler & flame graphs** — cpu/wall/alloc/lock, safepoint bias, AGCT → VM structs (4.2+), reading width/tops/colours, icicle/reversed views, differential graphs. Demo: cpu + alloc profile of `PaymentSim slow`.
7. **Capstone investigation** — section 7 end-to-end, finishing with JMH B/op as the proof artifact and an allocation-budget test (Lab 4).

### Analogies
- Tiered compilation = a payments risk engine: interpreter is manual review, C1 tier 3 is "approve but log everything" (profiling), C2 is the tuned fast path that trusts the history; an uncommon trap is a chargeback that sends the merchant back to review (deopt) and a fresh model (recompile).
- Megamorphic call site = a routing switch that has seen too many card networks to keep a fast lane for any of them.
- Flame graph = a sorted bar chart of stack populations; "wide top = where the CPU actually sits", not a timeline.
- False sharing = two cashiers sharing one cash drawer: each has their own money, but only one can have the drawer open.

### Misconceptions checklist (see section 8)
nanoTime microbenchmarks are fine · `final` makes methods faster · JIT output is stable · safepoint-based profilers are accurate · more threads = more throughput · flame-graph x-axis is time · "average latency improved, so we're done" (show p99.99 instead).

### Demo/lab caveats for writers
- Version-tag every number: thresholds/inlining limits "JDK 21–27"; `jfr view` "JDK 21+"; CPU-time sampling and method timing/tracing "JDK 25+" (CPU-time sampling experimental, Linux only); `report-on-exit` and `jcmd JFR.view` are documented in the JDK 25 man pages but I could not pin down the release that introduced them (the JDK 21–23 man-page files I probed did not contain them, possibly because the file path/format differs) — tag them "JDK 25 (introduced earlier?)" until checked; `made not entrant: <reason>` "JDK 25" vs bare "made not entrant" "JDK 21"; redaction "JDK 27"; compact headers default "JDK 27"; JEP 544 AOT code compilation "mainline for JDK 28, unreleased".
- All local numbers: JDK 21.0.12 on a shared 4-vCPU VM — present as illustrative; prefer B/op and layout facts over ns/op.
- Don't use `Math.log` for a DCE demo on modern x86_64 JDKs; use JMH sample 08's arithmetic `compute` or `Math.sqrt`.
- `sun.misc.Unsafe.objectFieldOffset` is deprecated for removal (since 18) and warns on JDK 24+; use JOL in labs.
