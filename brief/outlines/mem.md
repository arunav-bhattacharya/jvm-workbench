# Track: mem, "Memory and garbage collection" (lab: labs/memory, package workbench.memory.lNN)

Research notes: "research_notes/Advanced JVM runtime topics/memory_and_gc.md" (versions, flags, real JOL output, GC log samples). The lab module
has JOL (org.openjdk.jol:jol-core) for printing object layouts. Labs in Java and Kotlin; tests must be
deterministic (no "GC happened within 100 ms" timing). Use System.gc() only in demos, never as a test
assumption, except through helpers that loop until a ReferenceQueue delivers, with a timeout.
Link back to jmm (visibility), vt-04 (ThreadLocal), conc-11 (immutability) where it helps.

Lessons:
- mem-01 Where objects live: heap, stacks, metaspace, code cache; object headers, compressed oops and
  class pointers, alignment, compact object headers (JDK 25). Lab: compute object sizes and check with JOL.
- mem-02 Allocation, TLABs and escape analysis: bump-pointer allocation, measuring allocation with
  ThreadMXBean.getThreadAllocatedBytes, when scalar replacement removes an allocation. Lab: reduce
  allocations in a hot path (tests compare allocated bytes with generous margins).
- mem-03 Reachability: strong, soft, weak, phantom; ReferenceQueue; WeakHashMap; Cleaner; why
  finalize is deprecated for removal. Lab: a Cleaner-backed resource and a weak listener registry.
- mem-04 How garbage collectors work: generations, marking, copying, compaction, write barriers and
  card tables, safepoints; G1 regions, remembered sets, mixed collections, humongous objects. Figure.
- mem-05 Low-pause collectors: ZGC (generational only since JDK 24) and Shenandoah; how to choose
  between Serial, Parallel, G1, ZGC, Shenandoah, and Epsilon for tests. A decision table.
- mem-06 Reading GC logs and sizing the heap in containers: -Xlog:gc*, reading real G1 and ZGC lines,
  MaxRAMPercentage, why -Xmx = container limit gets the pod OOM-killed. Lab: parse GC log lines
  into pause stats (a small parser with tests on real sample lines from the notes).
- mem-07 Hunting memory leaks: heap dumps (jcmd GC.heap_dump, HeapDumpOnOutOfMemoryError), Eclipse
  MAT dominator tree and retained size, leak patterns in services, Native Memory Tracking, direct
  buffers and the Foreign Function and Memory API (Arena, MemorySegment; final in JDK 22, so show it
  in a JDK 25 single-file demo outside Gradle). Lab: find and fix a leak in a provided cache.
