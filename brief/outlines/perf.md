# Track: perf, "JIT, profiling and benchmarking" (lab: labs/performance, package workbench.performance.lNN)

Research notes: "research_notes/Advanced JVM runtime topics/jit_profiling_benchmarking.md". The lab module has JMH 1.37 with its annotation
processor on main, solution and demo, so JMH benchmarks must be Java classes. Benchmarks are run as
demos (a main that calls org.openjdk.jmh.runner.Runner with short warmup/measurement), never in JUnit.
JUnit tests check correctness or structure only (no timing assertions). Kotlin twins can show the
same code being measured, or the JIT-relevant Kotlin details (inline functions, boxing).

Lessons:
- perf-01 From bytecode to machine code: interpreter, C1, C2, tiered levels, code cache, OSR,
  -XX:+PrintCompilation read line by line (real output from the notes).
- perf-02 Inlining, deoptimization and intrinsics: inlining limits, megamorphic call sites,
  uncommon traps, why a type check in a hot loop changes speed. Demo with PrintCompilation "made not entrant".
- perf-03 Benchmarking with JMH: why nanoTime loops lie (dead code, constant folding, warm-up), the
  annotations, Blackhole, modes, -prof gc. Lab: fix three broken benchmarks (tests inspect behaviour,
  for example that the benchmark method returns or consumes its result).
- perf-04 CPU caches, false sharing and @Contended: cache lines, the LongAdder cell trick, padding.
  Lab: a padded counter whose field offsets (checked with JOL from labs/memory or reflection
  with Unsafe-free means) are at least 64 bytes apart.
- perf-05 JDK Flight Recorder and Mission Control: starting and dumping recordings, jfr print/summary/view,
  JFR streaming, custom events. Lab: emit a custom jdk.jfr.Event and read it back with RecordingFile.
- perf-06 async-profiler and flame graphs: modes (cpu, alloc, lock, wall), safepoint bias, reading a
  flame graph correctly. Use a flame graph SVG/figure built from real collapsed stacks in the notes.
- perf-07 A performance investigation, start to finish: a slow payment endpoint, JFR to find the
  allocation hot spot, a flame graph, the fix, and a JMH benchmark that proves it.
