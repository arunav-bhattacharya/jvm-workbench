# JVM memory layout and garbage collection (state as of November 2026: JDK 21, 24, 25 LTS, 26, 27)

Research conditions, so lesson writers know how much weight each fact carries:
- `openjdk.org` (JEP pages, wiki, bugs, mail), `docs.oracle.com` (GC Tuning Guide), `shipilev.net`, `inside.java`, `dev.java`, `help.eclipse.org` were all **unreachable** from this machine (DNS blocked). No JEP page was fetched.
- To compensate, every per-version default below was read from the **OpenJDK source at the GA tags** (`jdk-21-ga`, `jdk-23-ga`, `jdk-24-ga`, `jdk-25-ga`, `jdk-26-ga`, `jdk-27-ga`) via raw.githubusercontent.com, including the official `java` and `jcmd` man pages (`java.md`, `jcmd.md`) that ship in the source tree. `master` is already JDK 28 (`DEFAULT_VERSION_FEATURE=28`, GA date 2027-03-23) — [version-numbers.conf@master](https://raw.githubusercontent.com/openjdk/jdk/master/make/conf/version-numbers.conf).
- JEP numbers and JEP-page wording for JDK 26/27 changes (JEP 522, 523, 534) and JEP 519/521 benchmark numbers come **only from web-search result snippets** (page not fetched); they are marked "[search snippet]".
- All runtime experiments ran on the only usable JDK, **OpenJDK 21.0.12.1 (Ubuntu build), 4 CPUs, cgroup v1, container memory limit 13.35 GB**. I downloaded Ubuntu's OpenJDK 24/25/26/27 packages to verify behaviour on newer JDKs, but executing them was refused by the sandbox's permission system, so nothing below was run on JDK 22+.

Local runs cited as [Lx] (code and logs were in `/tmp/claude-0/-home-user/b1ec521c-18dd-5b5d-967f-de5283ba1787/scratchpad/memgc_research_q7/`; that scratchpad is shared and may be cleaned, so key code and outputs are reproduced here):
- **[L1]** JOL 0.17 (`jol-core-0.17.jar`, `jol-cli-0.17-full.jar` from Maven Central) on JDK 21 in five VM modes: default; `-XX:-UseCompressedOops`; `-XX:-UseCompressedOops -XX:-UseCompressedClassPointers`; `-XX:ObjectAlignmentInBytes=16`; `-Xmx40g`. Plus `jol-cli estimates` (layout simulation, including "Lilliput (current experiment)" = 8-byte header model) and `jol-cli heapdump-estimates`.
- **[L2]** `GcWorkload.java`: per-"request" garbage (5,000 × 64–320-byte arrays per round), a cache of 8 KiB arrays that grows to a fraction of max heap, then every other entry is evicted, plus a 3 MiB array every 50 rounds (humongous with 1–2 MiB regions); `System.gc()` at the end. Run with `-Xlog:gc`, `-Xlog:gc*`, `-Xlog:safepoint` under G1 (256 MB and 1 GB heaps), generational and non-generational ZGC, Shenandoah, Parallel, Serial.
- **[L3]** Ergonomics: `java [flags] -XX:+PrintFlagsFinal -version`, `-XshowSettings:system`, `-Xlog:os+container=debug`.
- **[L4]** `NativeDemo.java`: 64 MiB `ByteBuffer.allocateDirect` + 32 MiB `Arena.ofConfined().allocate` (FFM, preview in 21) + 50 parked threads, `-Xmx256m -XX:NativeMemoryTracking=summary`, then `jcmd <pid> VM.native_memory summary scale=MB`.
- **[L5]** `LeakyService.java` (unbounded idempotency cache), `-XX:+HeapDumpOnOutOfMemoryError`, `jcmd GC.class_histogram`, `jcmd GC.heap_dump`, `-XX:MaxDirectMemorySize` OOMs.
- **[L6]** `MemoryLabTest.java`: 11 JUnit Jupiter test methods (63 test executions incl. repetitions) run 3× with `junit-platform-console-standalone-6.1.3` (the labs use JUnit 6.1.3), then once each under ZGC (gen + non-gen), Serial, Parallel, Shenandoah, `-XX:+DisableExplicitGC`, `-XX:+ExplicitGCInvokesConcurrent`.
- **[L7]** `Demos.java`: SoftReference under pressure (`-Xmx64m`), escape analysis on/off, finalization enabled/disabled, Epsilon OOM, TLAB trace logging.
- **[L8]** Negative checks on JDK 21: `-XX:+UseCompactObjectHeaders`, `-XX:ShenandoahGCMode=generational`, FFM without `--enable-preview`.

---

## Q1. What exactly are the current defaults and flags per JDK version (21, 24, 25, 26, 27)?

### Takeaway
The big 2026 changes are in **JDK 27**: G1 is now chosen in *all* environments (Serial is never auto-selected), and **compact object headers are on by default**. JDK 24 removed non-generational ZGC; JDK 25 made compact headers and generational Shenandoah product features (both still opt-in); JDK 26 changed initial-heap ergonomics (`InitialRAMPercentage` 0) and deprecated `MaxRAM` and the server-class switches. Container support has been on by default throughout, and `MaxRAMPercentage` is still 25.

### Cited Findings

**Summary table (all values read from source at the GA tag unless marked)**

| Item | JDK 21 | JDK 24 | JDK 25 (LTS) | JDK 26 | JDK 27 |
|---|---|---|---|---|---|
| Default GC (no GC flag given) | G1 on "server-class" machines, else Serial | same | same | same (server-class override flags deprecated) | **G1 always** (if built in) |
| `UseCompactObjectHeaders` | flag does not exist | `false`, **EXPERIMENTAL** (needs `-XX:+UnlockExperimentalVMOptions`) | `false`, product | `false`, product | **`true`**, product |
| `UseCompressedClassPointers` | `true` | `true` | `true`, **deprecated** | `true`, deprecated | **obsolete** |
| `UseCompressedOops` | ergonomic (on when max heap fits, ~32 GB) | same | same | same | same |
| ZGC modes | non-generational default; generational via `-XX:+ZGenerational` | generational only; `ZGenerational` obsolete | generational only | generational only | generational only |
| Shenandoah `ShenandoahGCMode` | `satb` default; no `generational` mode | `satb` default; `generational` experimental | `satb` default; `generational` product | same as 25 | same as 25 |
| `MaxRAMPercentage` / `MinRAMPercentage` | 25 / 50 | 25 / 50 | 25 / 50 | 25 / 50 | 25 / 50 |
| `InitialRAMPercentage` | 1.5625 | 1.5625 | 1.5625 | **0.0** | 0.0 |
| `MaxRAM` | platform default (128 GB on x64, [L3]) | same | same | default 0 (= physical memory), **deprecated** | **obsolete** |
| `UseContainerSupport` (Linux) | `true` | `true` | `true` | `true` | `true` |
| `LockingMode` (affects mark word) | `LM_LEGACY`, experimental flag | `LM_LIGHTWEIGHT`, deprecated | deprecated | obsolete | expired (entry gone from the 27 table) |

Supporting citations:
- Default GC selection JDK 21–26: `select_gc_ergonomically()` sets `UseG1GC` only `if (os::is_server_class_machine())`, else `UseSerialGC` — [gcConfig.cpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/shared/gcConfig.cpp) (identical in [jdk-21-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-21-ga/src/hotspot/share/gc/shared/gcConfig.cpp), [jdk-24-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-24-ga/src/hotspot/share/gc/shared/gcConfig.cpp), [jdk-26-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-26-ga/src/hotspot/share/gc/shared/gcConfig.cpp)).
- "Server class" = `active_processor_count() >= 2` **and** `physical_memory() >= 2 GB - 256 MB` (i.e. ≥ 1792 MB) — [os.cpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/runtime/os.cpp). Both inputs are container-aware (inference supported by [L3]: with `-XX:ActiveProcessorCount=1`, JDK 21 selected `UseSerialGC=true`, `UseG1GC=false`).
- JDK 27: `select_gc_ergonomically()` is now `#if INCLUDE_G1GC FLAG_SET_ERGO_IF_DEFAULT(UseG1GC, true); #else` (server-class check only for builds without G1) — [gcConfig.cpp@jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/hotspot/share/gc/shared/gcConfig.cpp). This is **JEP 523 "Make G1 the Default Garbage Collector in All Environments"**, targeted to JDK 27 [search snippet: openjdk.org/jeps/523 and inside.java/2026/05/26/jep523-target-jdk27; pages not fetched]. The JDK 27 man page now says of `-XX:+UseG1GC`: "By default, this option is enabled and G1 is used as the default garbage collector" — [java.md@jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/java.base/share/man/java.md).
- `NeverActAsServerClassMachine`, `AlwaysActAsServerClassMachine`, `MaxRAM`, `ParallelRefProcEnabled`: deprecated in 26, obsolete in 27, expire in 28 (special-flags table) — [arguments.cpp@jdk-26-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-26-ga/src/hotspot/share/runtime/arguments.cpp), [arguments.cpp@jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/hotspot/share/runtime/arguments.cpp).
- Compact headers: JDK 24 `product(bool, UseCompactObjectHeaders, false, EXPERIMENTAL, "Use compact 64-bit object headers in 64-bit VM")` — [globals.hpp@jdk-24-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-24-ga/src/hotspot/share/runtime/globals.hpp) (JEP 450, experimental). JDK 25: same flag without `EXPERIMENTAL`, default `false` — [globals.hpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/runtime/globals.hpp) (JEP 519, product). JDK 26: still `false` — [globals.hpp@jdk-26-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-26-ga/src/hotspot/share/runtime/globals.hpp). JDK 27: default **`true`** — [globals.hpp@jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/hotspot/share/runtime/globals.hpp). Web search attributes the JDK 27 default flip to **JEP 534** ("Compact Object Headers by Default", draft id 8361187) [search snippet; not fetched].
- JDK 25 man page: "`-XX:+UseCompactObjectHeaders` Enables compact object headers. By default, this option is disabled. Enabling this option reduces memory footprint in the Java heap by 4 bytes per object (on average) and often improves performance. The feature remains disabled by default while it continues to be evaluated. In a future release it is expected to be enabled by default, and eventually will be the only mode of operation." — [java.md@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/man/java.md).
- JDK 27 man page: "`-XX:-UseCompactObjectHeaders` Disables compact object headers. By default, this option is enabled ... This option can be used if performance regressions are suspected. In a future release compact object headers is expected to become the only mode of operation." — [java.md@jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/java.base/share/man/java.md).
- JDK 21 rejects the flag: `Unrecognized VM option 'UseCompactObjectHeaders'` — [L8].
- `UseCompressedClassPointers`: help text "(Deprecated)" in 25 — [globals.hpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/runtime/globals.hpp); special-flags entry `{ "UseCompressedClassPointers", jdk(25), jdk(27), undefined }` (deprecated 25, obsolete 27) — [arguments.cpp@jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/hotspot/share/runtime/arguments.cpp). The JDK 25 table still said obsolete in 26 — [arguments.cpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/runtime/arguments.cpp) — so the removal slipped one release.
- ZGC: JDK 21 `product(bool, ZGenerational, false, "Use the generational version of ZGC")` — [gc_globals.hpp@jdk-21-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-21-ga/src/hotspot/share/gc/shared/gc_globals.hpp) (JEP 439, generational ZGC opt-in in 21; [L3] confirms `ZGenerational=false` by default and `true {command line}` with `-XX:+ZGenerational`). JDK 23: default `true` — [gc_globals.hpp@jdk-23-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-23-ga/src/hotspot/share/gc/shared/gc_globals.hpp) (JEP 474, generational by default). JDK 24: `{ "ZGenerational", jdk(23), jdk(24), undefined }` = deprecated 23, obsolete 24 — [arguments.cpp@jdk-24-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-24-ga/src/hotspot/share/runtime/arguments.cpp) (JEP 490 removed the non-generational mode).
- Shenandoah generational mode: `is_experimental() { return true; }` in JDK 24 — [shenandoahGenerationalMode.hpp@jdk-24-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-24-ga/src/hotspot/share/gc/shenandoah/mode/shenandoahGenerationalMode.hpp) (JEP 404, experimental); `return false;` in JDK 25 — [shenandoahGenerationalMode.hpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/shenandoah/mode/shenandoahGenerationalMode.hpp). The product JEP is **JEP 521 "Generational Shenandoah"** (JDK 25): the man page's `ShenandoahGCMode` entry links "JEP 404 and JEP 521" — [java.md@jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/java.base/share/man/java.md). Per search snippet of the JEP 521 page: single-generation mode stays the default and `-XX:+UnlockExperimentalVMOptions` is no longer needed but tolerated [search snippet; not fetched].
- `ShenandoahGCMode` default is `"satb"` in every version incl. 27 — [shenandoah_globals.hpp@jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/hotspot/share/gc/shenandoah/shenandoah_globals.hpp). JDK 21 rejects `-XX:ShenandoahGCMode=generational` with `Unknown -XX:ShenandoahGCMode option` — [L8].
- Heap-percentage defaults: `MaxRAMPercentage 25.0`, `MinRAMPercentage 50.0`, `InitialRAMPercentage 1.5625` in 21/24/25 — [gc_globals.hpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/shared/gc_globals.hpp); `InitialRAMPercentage 0.0` and `MaxRAM` "(Deprecated)", default 0 in 26 — [gc_globals.hpp@jdk-26-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-26-ga/src/hotspot/share/gc/shared/gc_globals.hpp); same percentages in 27 — [gc_globals.hpp@jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/hotspot/share/gc/shared/gc_globals.hpp).
- `UseContainerSupport` default `true` — [globals_linux.hpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/os/linux/globals_linux.hpp) (same at all five tags).
- `LockingMode`: JDK 21 default `LM_LEGACY` (EXPERIMENTAL flag) — [globals.hpp@jdk-21-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-21-ga/src/hotspot/share/runtime/globals.hpp); JDK 24 default `LM_LIGHTWEIGHT`, "(Deprecated)" — [globals.hpp@jdk-24-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-24-ga/src/hotspot/share/runtime/globals.hpp); `{ "LockingMode", jdk(24), jdk(26), jdk(27) }` — [arguments.cpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/runtime/arguments.cpp).
- G1 pause goal: `MaxGCPauseMillis` is `max_uintx - 1` in the flag table, set ergonomically to **200** when G1 is selected — [L3] (`MaxGCPauseMillis=200` with G1; `18446744073709551614` when Serial was selected) and [gc_globals.hpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/shared/gc_globals.hpp).
- Other relevant defaults (unchanged 21→27): `HeapDumpOnOutOfMemoryError false` (manageable), `ExitOnOutOfMemoryError false`, `CrashOnOutOfMemoryError false`, `NativeMemoryTracking "off"` in product builds, `MaxMetaspaceSize max_uintx` (unlimited), `CompressedClassSpaceSize 1G`, `SoftRefLRUPolicyMSPerMB 1000`, `MaxDirectMemorySize 0` ("Ignored if not explicitly set" in 27) — [globals.hpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/runtime/globals.hpp), [globals.hpp@jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/hotspot/share/runtime/globals.hpp).
- ZGC uncommit: `ZUncommit true`, `ZUncommitDelay 300` s — [z_globals.hpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/z/z_globals.hpp); G1 periodic GC `G1PeriodicGCInterval 0` (disabled) — [g1_globals.hpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/g1/g1_globals.hpp).
- JDK 26 G1 change: **JEP 522 "G1 GC: Improve Throughput by Reducing Synchronization"** delivered in 26; it introduces a second card table that is swapped with the one application threads write to, simplifying the write barrier; each card table costs ~2 MB native per 1 GB heap [search snippet: openjdk.org/jeps/522; not fetched]. Consistent with source: `G1UpdateBufferSize` became obsolete in 26 — [arguments.cpp@jdk-26-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-26-ga/src/hotspot/share/runtime/arguments.cpp).

**Measured JDK 21 defaults on this machine [L3]** (cgroup v1, memory limit 13.35G, 4 CPUs): `UseG1GC=true`, `MaxHeapSize=3586129920` (3420 MB = 25% of limit), `InitialHeapSize=224395264` (214 MB = 1.5625%), `G1HeapRegionSize=2097152` (2 MB), `MaxRAM=137438953472` (128 GB), `UseCompressedOops=true`, `UseCompressedClassPointers=true`, `ZGenerational=false`.

### Inferences
- A payments service on Quarkus running in a container with **1 CPU or < 1792 MB memory limit** silently ran **Serial GC** on JDK 21/25/26 unless a GC was named; on JDK 27 the same container gets G1. This is the most practically important default change of 2026 for small pods.
- Teams upgrading 25 → 27 get compact headers for free; the escape hatch is `-XX:-UseCompactObjectHeaders`. Tools that hard-code 12-byte headers (old agents, off-heap layout hacks via `Unsafe`) are what can break.
- For 21 → 25 LTS upgrades: remove `-XX:+ZGenerational` (obsolete in 24, the VM warns and ignores — standard obsolete-flag behaviour, not run here) and stop passing `-XX:-UseCompressedClassPointers` (deprecated 25, obsolete 27).

### Gaps
- JEP pages (450, 519, 534, 523, 522, 439, 474, 490, 404, 521, 421, 454) could not be fetched; JEP titles above come from prior knowledge plus search snippets; behaviour is verified from source only.
- Nothing was executed on JDK 22–27; JDK 26/27 behaviour is source-reading only.
- Exact warning text printed for obsolete flags (e.g. `-XX:+ZGenerational` on 24+) not verified.

---

## Q2. Where do objects live and what do JOL layouts look like (with and without compressed oops and compact headers)?

### Takeaway
On a default 64-bit HotSpot (JDK 21–26) every object starts with a 12-byte header (8-byte mark word + 4-byte compressed class pointer) and is padded to 8 bytes; references are 4 bytes while max heap is under ~32 GB. Turning compressed oops off (explicitly or by a > 32 GB heap) makes references 8 bytes and grows typical objects 20–25%. Compact headers (JDK 24 experimental, 25 opt-in, 27 default) fold the class pointer into the mark word: the header becomes 8 bytes and many small objects shrink by one 8-byte step.

### Cited Findings

**Memory areas**
- Native Memory Tracking output from a 256 MB-heap JDK 21 process shows the separate areas a lesson should name: `Java Heap (reserved=256MB, committed=216MB)`, `Class (reserved=1024MB, committed=0MB)` with `(classes #1002)` (metaspace + compressed class space), `Thread (reserved=71MB, committed=6MB) (threads #71) (stack: reserved=71MB, committed=6MB)`, `Code (reserved=242MB, committed=7MB)` (code cache), `GC (reserved=46MB, committed=45MB)`, `Other (reserved=96MB, committed=96MB) (malloc=96MB #2)` (the direct buffer + FFM segment), `Shared class space (reserved=16MB, committed=13MB)` (CDS), `Metaspace (reserved=64MB, committed=1MB)`; total `reserved=1820MB, committed=390MB` — [L4].
- `CompressedClassSpaceSize` default `1*G`; `MaxMetaspaceSize` default `max_uintx` (no cap) — [globals.hpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/runtime/globals.hpp). The 1 GB class-space reservation is visible in G1's startup log: `Compressed class space mapped at: 0x00007f9340000000-0x00007f9380000000, reserved size: 1073741824` — [L2].
- Compressed oops: "object references are represented as 32-bit offsets instead of 64-bit pointers ... By default this range is 32 GB ... It's possible to use compressed pointers with Java heap sizes greater than 32 GB. See the `-XX:ObjectAlignmentInBytes` option." — [java.md@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/man/java.md). JOL reports `Compressed references (oops): 3-bit shift` by default and `4-bit shift` with `-XX:ObjectAlignmentInBytes=16` (8 × 4 GB = 32 GB vs 16 × 4 GB = 64 GB addressable) — [L1].
- `-Xmx40g` turns compressed oops off automatically: `UseCompressedOops=false` while class pointers stay compressed — [L3], [L1] (`Compressed references (oops): disabled`, `Compressed class pointers: 3-bit shift`). G1's log reports `Compressed Oops: Enabled (32-bit)` for a 1 GB heap — [L2].
- Mark word (JDK 21, 64-bit): `unused:25 hash:31 -->| unused_gap:1 age:4 unused_gap:1 lock:2 (normal object)` — [markWord.hpp@jdk-21-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-21-ga/src/hotspot/share/oops/markWord.hpp). JDK 25: `unused:22 hash:31 -->| unused_gap:4 age:4 self-fwd:1 lock:2`, and **with compact headers** `klass:22 hash:31 -->| unused_gap:4 age:4 self-fwd:1 lock:2`; `klass_bits = 22`; `unused_gap_bits = 4 // Reserved for Valhalla` — [markWord.hpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/oops/markWord.hpp).
- Compact-header class pointers: `narrow_klass_pointer_bits_coh = 22` (vs 32 otherwise), `max_shift_coh = 10` (vs 3) — [compressedKlass.hpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/oops/compressedKlass.hpp). (Inference: 2^22 ≈ 4 M distinct encodable classes, 2^(22+10) = 4 GB encoding range.)
- Arrays with compact headers: "The _length field ... is allocated after the mark-word when using compact headers (+UseCompactObjectHeaders), otherwise after the compressed Klass*"; element base = header (length offset + 4) aligned up to 8 only for 8-byte element types — [arrayOop.hpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/oops/arrayOop.hpp), [oop.hpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/oops/oop.hpp). (Inference: `byte[3]` = 8 mark + 4 length + 3 data = 15 → **16 bytes** vs 24 today; not run.)
- JEP 519 page (per search snippet): in one SPECjbb2015 configuration 22% less heap and 8% less CPU time; 15% fewer GCs with G1 and Parallel; a JSON-parser benchmark 10% faster [search snippet: openjdk.org/jeps/519; not fetched].

**JOL 0.17 output on JDK 21 [L1]** — instance sizes in bytes (verbatim JOL numbers; "COH sim" = `jol-cli estimates` mode "JDK 99, 64-bit model, Lilliput (current experiment), compressed references, compressed classes, 8-byte aligned", which models today's 8-byte compact header; it is a JOL **simulation**, not a JDK 25 run):

| Object | default (coops + ccp) | `-XX:-UseCompressedOops` | `-UseCompressedOops -UseCompressedClassPointers` | `ObjectAlignmentInBytes=16` | `-Xmx40g` | COH sim |
|---|---|---|---|---|---|---|
| `new Object()` | 16 (8+4+4 gap) | 16 | 16 (8+8) | 16 | 16 | **8** |
| `Integer` | 16 | 16 | 24 | 16 | 16 | 16 |
| `Long` | 24 (8+4+4 gap+8) | – | – | – | – | **16** |
| `String` (shell only) | 24 | 32 | 32 | 32 | 32 | 24 |
| `Payment` (below) | 40 | 48 | 48 | 48 | 48 | **32** |
| `record Money(long, String)` | 24 | – | – | – | – | 24 |
| `HashMap` (empty) / `HashMap$Node` | 48 / 32 | – | – | – | – | **40 / 24** |
| `byte[3]` | 24 | 24 | 32 | 32 | 24 | (16, inferred) |
| `Object[2]` | 24 | 32 | 40 | 32 | 32 | – |
| Graph: `"EUR"` (String + byte[]) | 48 | 56 | 64 | 64 | 56 | – |
| Graph: `new Money(1999, new String("EUR"))` | 72 | 88 | 96 | 96 | 88 | – |
| Graph: `new BigDecimal("19.99")` | 40 | 48 | 48 | 48 | 48 | – |
| Graph: `ArrayList<Integer>` of 0..999 | 20,976 | 25,920 | 33,928 | 20,992 | 25,920 | – |
| Graph: `int[1000]` | 4,016 | 4,016 | 4,024 | 4,016 | 4,016 | – |

The `Payment` class used: `boolean captured; long amountMinor; byte status; String currency; int attempts; Object metadata;`. Verbatim default layout (field order is the VM's, not source order):
```
JolLayouts$Payment object internals:
OFF  SZ               TYPE DESCRIPTION               VALUE
  0   8                    (object header: mark)     N/A
  8   4                    (object header: class)    N/A
 12   4                int Payment.attempts          N/A
 16   8               long Payment.amountMinor       N/A
 24   1            boolean Payment.captured          N/A
 25   1               byte Payment.status            N/A
 26   2                    (alignment/padding gap)
 28   4   java.lang.String Payment.currency          N/A
 32   4   java.lang.Object Payment.metadata          N/A
 36   4                    (object alignment gap)
Instance size: 40 bytes
Space losses: 2 bytes internal + 4 bytes external = 6 bytes total
```
With `-XX:-UseCompressedOops -XX:-UseCompressedClassPointers` the class word is 8 bytes and references are 8 bytes:
```
  0   8                    (object header: mark)     N/A
  8   8                    (object header: class)    N/A
 16   8               long Payment.amountMinor       N/A
 24   4                int Payment.attempts          N/A
 28   1            boolean Payment.captured          N/A
 29   1               byte Payment.status            N/A
 30   2                    (alignment/padding gap)
 32   8   java.lang.String Payment.currency          N/A
 40   8   java.lang.Object Payment.metadata          N/A
Instance size: 48 bytes
```
JOL simulation of compact headers (8-byte header, no class word):
```
***** Hotspot Layout Simulation (JDK 99, 64-bit model, Lilliput (current experiment), compressed references, compressed classes, 8-byte aligned)
  0   8                    (object header: mark)     N/A
  8   8               long Payment.amountMinor       N/A
 16   4                int Payment.attempts          N/A
 20   1            boolean Payment.captured          N/A
 21   1               byte Payment.status            N/A
 22   2                    (alignment/padding gap)
 24   4   java.lang.String Payment.currency          N/A
 28   4   java.lang.Object Payment.metadata          N/A
Instance size: 32 bytes
```
- Field packing into the header gap (JDK 15+ field layout): `Long.value` cannot use the 4-byte gap at offset 12 (`12 4 (alignment/padding gap)`, `16 8 long Long.value`), but `int` fields and references can (`12 4 int Payment.attempts`; `12 4 java.lang.String Money.currency`) — [L1]. Subclass fields fill superclass gaps: `Derived extends Base { byte d; long l; }` with `Base { byte b; }` lays out `12 1 byte Base.b`, `13 1 byte Derived.d`, `16 8 long Derived.l` → 24 bytes — [L1].
- Arrays: `byte[3]` = mark 8 + class 4 + `(array length) 3` 4 + 3 data + 5 gap = 24; with both compressions off the length is at 16, data at 24 and `Array base offsets: 24` — [L1].
- Mark-word contents seen by JOL on JDK 21 (default `LM_LEGACY`): fresh object `0x0000000000000001 (non-biasable; age: 0)`; after `System.identityHashCode`: `0x00000077846d2c01 (hash: 0x77846d2c; age: 0)`; inside `synchronized`: `0x00007f310cdfe928 (thin lock: 0x00007f310cdfe928)` (mark word displaced to the stack) — [L1].
- One-entry `HashMap<String, Long>` footprint (default mode): `[B` 24, `HashMap$Node[]` 80, `Long` 24, `String` 24, `HashMap` 48, `HashMap$Node` 32 → `232 (total)` for 6 objects — [L1].
- JOL README: commands `internals`, `externals`, `footprint`, `estimates` (README on master calls it `internals-estimates`); "JOL module would try to self-attach as Java Agent" — [jol README](https://raw.githubusercontent.com/openjdk/jol/master/README.md). The 0.17 jar lists modes `estimates, externals, footprint, heapdump-estimates, heapdumpstats, internals, shapes, string-compress` — [L1]. Latest release on Maven Central is 0.17 (`lastUpdated 20230227`) — [jol-cli maven-metadata.xml](https://maven-central.storage-download.googleapis.com/maven2/org/openjdk/jol/jol-cli/maven-metadata.xml).
- JOL gotchas on JDK 21 [L1]: records fail with `RuntimeException: Cannot get the field offset, try with -Djol.magicFieldOffset=true` (cause: `UnsupportedOperationException: can't get field offset on a record class`); without ptrace rights JOL prints `WARNING: Unable to attach Serviceability Agent` and that addresses are guesses (layouts are still correct); dynamic self-attach needs `-Djdk.attach.allowAttachSelf=true` / `-XX:+EnableDynamicAgentLoading`.
- Whole-heap view: `jol-cli heapdump-estimates` on the 49.8 MB leak dump of [L5] (dominated by 2 KB `byte[]`) gives total object size 45,807,656 B for "JDK 15, compressed references, compressed classes, 8-byte aligned" vs 45,224,768 B for "Lilliput (current experiment), compressed references" (−1.3%) and 47,257,216 B with no compression (+3.2%) — [L1].

### Inferences
- Header savings are proportional to object *count*, not heap size: heaps full of small objects (DTOs, `HashMap$Node`, boxed `Long`, `BigDecimal`) benefit most; heaps dominated by large `byte[]` (buffers, JSON payloads) barely change (the −1.3% above).
- `ArrayList<Integer>` costs ~5× an `int[]` (20,976 vs 4,016 bytes): the per-element cost is a 4-byte reference plus a 16-byte `Integer`.
- The ~32 GB compressed-oops cliff is real: going from `-Xmx31g` to `-Xmx40g` makes the same object graph ~24% bigger (ArrayList case 20,976 → 25,920 bytes), so a 40 GB heap can hold *less* data than expected.
- Thread stacks, metaspace, code cache, CDS, GC data structures, and direct/FFM memory are all outside `-Xmx` (see Q8).

### Gaps
- The 8-byte `new Object()` under compact headers is JOL's simulation; HotSpot's actual minimum object size with `+UseCompactObjectHeaders` was not verified.
- No JOL run on a JDK with real compact headers (only JOL 0.17's simulation, which predates JEP 450; the 8-byte "current experiment" model matches the source layout but was not checked against a live JDK 25/27).
- JOL has had no release since 0.17 (Feb 2023); whether master builds decode JDK 24+ compact headers correctly was not verified.

---

## Q3. How does allocation work (TLABs, bump-pointer), and what do escape analysis and scalar replacement do?

### Takeaway
Most allocations are a pointer bump inside a thread-local allocation buffer (TLAB) carved from eden; only TLAB refills and large objects take a slower path. C2's escape analysis can remove allocations of objects that never escape a compiled method (scalar replacement), so "allocated bytes" drops to zero once the code is hot.

### Cited Findings
- TLAB: "a descriptor for thread-local storage used by the threads for allocation. It is thread-private at any time, but maybe multiplexed over time across multiple threads" — [threadLocalAllocBuffer.hpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/shared/threadLocalAllocBuffer.hpp).
- Bump-pointer fast path: `HeapWord* obj = top(); if (pointer_delta(end(), obj) >= size) { set_top(obj + size); return obj; } return nullptr;` — [threadLocalAllocBuffer.inline.hpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/shared/threadLocalAllocBuffer.inline.hpp).
- `-XX:+UseTLAB`: "Enables the use of thread-local allocation blocks (TLABs) in the young generation space. This option is enabled by default." — [java.md@jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/java.base/share/man/java.md).
- TLAB trace on JDK 21 (`-Xlog:gc+tlab=trace`): `TLAB: fill thread: 0x00007f79d401a8a0 [id: 22952] desired_size: 266KB slow allocs: 0  refill waste: 4256B alloc: 0.99998     1024KB refills: 1 waste  0.0% gc: 0B slow: 0B` — [L7].
- G1 never allocates humongous objects in a TLAB: "ensure that we don't try to allocate a TLAB as humongous and that we don't allocate a humongous object in a TLAB"; threshold `region_size / 2` — [g1CollectedHeap.hpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/g1/g1CollectedHeap.hpp).
- C2 flags: `DoEscapeAnalysis true` ("Perform escape analysis"), `EliminateAllocations true` ("Use escape analysis to eliminate allocations"), `EliminateLocks true`, `EliminateAllocationArraySizeLimit 64` ("Array size (number of elements) limit for scalar replacement") — [c2_globals.hpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/opto/c2_globals.hpp).
- Measured scalar replacement [L7]: loop creating 1,000,000 `record Point(long x, long y)` per round, summing fields, bytes measured by `getCurrentThreadAllocatedBytes`:
  - default: round 0 `allocated=8000848`, round 1 `1572832`, rounds 2–3 `262112`, rounds 4–9 `allocated=0 bytes`;
  - `-XX:-DoEscapeAnalysis`: round 0 `32005488`, rounds 1–9 `32000000` (= 1,000,000 × 32-byte `Point`).
- Allocation counter API: `getCurrentThreadAllocatedBytes()` (`@since 14`) returns "an approximation of the total amount of memory, in bytes, allocated in heap memory"; for a virtual thread, a dead thread, or when measurement is disabled it returns `-1` — [ThreadMXBean.java@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.management/share/classes/com/sun/management/ThreadMXBean.java).
- Measured accuracy on JDK 21 [L6]: `new byte[1 << 20]` → delta **exactly 1,048,592** bytes in 20/20 repetitions (1 MiB + 16-byte array header); 1,000 × `Long.valueOf(i % 128)` → **0** bytes (Long cache), 1,000 × `Long.valueOf(1000 + i)` → **24,000** bytes (24-byte `Long`), 5/5 repetitions.

### Inferences
- Interpreted or C1-compiled code allocates every object; scalar replacement appears only after C2 compiles the method (round 4 above). Asserting "zero allocation" in a unit test is therefore timing-dependent; assert in a demo, not a CI test.
- `getCurrentThreadAllocatedBytes` is a great *deterministic* teaching tool for code run once (interpreter), because it counts exact object sizes, which ties back to JOL numbers.
- Do not measure allocation inside a virtual thread (returns −1 per Javadoc) — relevant for Quarkus `@RunOnVirtualThread` code.

### Gaps
- TLAB sizing heuristics (`TLABSize`, `ResizeTLAB`, `TLABWasteTargetPercent`) were not read from source.
- Scalar replacement limits beyond the array-size flag (e.g. merges, control-flow) not researched; no Shipilëv "JVM Anatomy Quarks" pages could be fetched.

---

## Q4. Reachability: strong, soft, weak, phantom references, ReferenceQueue, Cleaner, finalization

### Takeaway
The `java.lang.ref` package defines a strict ladder (strong > soft > weak > phantom > unreachable); the GC clears references and enqueues them when reachability drops. `Cleaner` (phantom-reference based) is the supported replacement for `finalize()`, which has been deprecated for removal since JDK 18 (JEP 421) and can be switched off with `--finalization=disabled`.

### Cited Findings
- Reachability levels, verbatim: "An object is *strongly reachable* if it is reachable and if it can be accessed without traversing the referent of a Reference object. An object is *softly reachable* if it is not strongly reachable but can be reached by traversing a soft reference. An object is *weakly reachable* if it is neither strongly nor softly reachable but can be reached by traversing a weak reference. When the weak references to a weakly-reachable object are cleared, the object becomes eligible for finalization. An object is *phantom reachable* if it is neither strongly, softly, nor weakly reachable, it has been finalized, and some phantom reference refers to it. Finally, an object is *unreachable*, and therefore eligible for reclamation..." — [java/lang/ref/package-info.java@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/ref/package-info.java).
- Notification: "Some time after the garbage collector determines that the reachability of the referent has changed to correspond with the type of the reference, it will clear the reference and add it to the associated queue." — same source.
- SoftReference: "Soft references are most often used to implement memory-sensitive caches." "All soft references to softly-reachable objects are guaranteed to have been cleared before the virtual machine throws an OutOfMemoryError. Otherwise no constraints are placed upon the time at which a soft reference will be cleared ... implementations are, however, encouraged to bias against clearing recently-created or recently-used soft references." — [SoftReference.java@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/ref/SoftReference.java). HotSpot knob: `SoftRefLRUPolicyMSPerMB 1000` ("Number of milliseconds per MB of free space in the heap") — [globals.hpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/runtime/globals.hpp).
- Measured [L7], `-Xmx64m`: `SoftReference<byte[40 MB]>` → `soft before: true`; allocating another 40 MB succeeds and `soft after allocating 40MB more: false big=41943040`. The G1 log shows the VM escalating: `Pause Full (G1 Compaction Pause) 42M->42M(64M)` then `Pause Full (G1 Compaction Pause) 42M->1M(8M)` (second full GC clears soft refs).
- PhantomReference: "Phantom references are most often used to schedule post-mortem cleanup actions"; `get()` "always returns null" — [PhantomReference.java@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/ref/PhantomReference.java).
- WeakHashMap holds *weak keys*; "care should be taken to ensure that value objects do not strongly refer to their own keys, either directly or indirectly, since that will prevent the keys from being discarded"; stale entries are removed by `expungeStaleEntries()` called from `size()`, `get`, `put` etc. — [WeakHashMap.java@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/WeakHashMap.java).
- Cleaner (verbatim highlights): "Cleaning actions are registered to run after the cleaner is notified that the object has become phantom reachable. The cleaner uses PhantomReference and ReferenceQueue ... The most efficient use is to explicitly invoke the clean method when the object is closed ... The cleaning action is a Runnable to be invoked at most once ... Note that the cleaning action must not refer to the object being registered. If so, the object will not become phantom reachable ... An 'inner' class, anonymous or not, must not be used because it implicitly contains a reference to the outer instance ... The behavior of cleaners during System.exit is implementation specific. No guarantees are made relating to whether cleaning actions are invoked or not." — [Cleaner.java@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/ref/Cleaner.java).
- Finalization: `@Deprecated(since="9", forRemoval=true) protected void finalize()`; "Finalization is deprecated and subject to removal in a future release. The use of finalization can lead to problems with security, performance, and reliability. See JEP 421 for discussion and alternatives ... Use Cleaner and PhantomReference as safer ways to release resources ... Alternatively, add a close method ... and implement AutoCloseable" — [Object.java@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Object.java).
- Measured [L7]: 1,000 objects overriding `finalize()`, then 20 × `System.gc()`: `finalized=1000` by default, `finalized=0` with `java --finalization=disabled` (JDK 21).

### Inferences
- Lesson framing: weak = "forget as soon as nobody else cares" (cleared by the next GC that processes references; the bounded `System.gc()` loop in [L6] always succeeded), soft = "keep until memory is tight, with LRU-ish bias" (cleared before OOME), phantom = "tell me after it is gone" (cleanup hooks).
- For services: `Cleaner` is a safety net for leaked native handles, not a replacement for `try-with-resources`; the explicit `close()` → `cleanable.clean()` path is deterministic and idempotent ([L6] asserts exactly one run).
- `--finalization=disabled` is a cheap way to test whether a dependency still relies on finalizers before finalization is removed.

### Gaps
- JEP 421 text (timeline for actual removal) not fetched; no source states the removal release as of JDK 27.
- `Reference.reachabilityFence` semantics were used in the lab but its Javadoc was not extracted.

---

## Q5. How do collectors work (generations, marking, copying, compaction, card tables, write barriers, safepoints) and how does G1 work in detail?

### Takeaway
HotSpot's default G1 splits the heap into equal regions (1–32 MB ergonomically, up to 512 MB manually), collects eden + survivor regions in stop-the-world evacuation (copying) pauses, runs concurrent SATB marking when old-gen occupancy crosses the (adaptive) IHOP threshold, and then reclaims the emptiest old regions in "mixed" pauses. Card tables plus write barriers track old→young and cross-region pointers so a young pause does not scan the whole heap. Full compaction is a last-resort fallback.

### Cited Findings
- Region size: `G1HeapRegionSize 0` means ergonomic; region = `clamp(max_heap / 2048, 1 MB, 32 MB)` rounded up to a power of 2, absolute bounds `MIN_REGION_SIZE = 1 MB`, `MAX_REGION_SIZE = 512 MB`, `MAX_ERGONOMICS_SIZE = 32 MB`, `TARGET_REGION_NUMBER = 2048` — [g1HeapRegionBounds.hpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/g1/g1HeapRegionBounds.hpp), [g1HeapRegion.cpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/g1/g1HeapRegion.cpp). Measured on JDK 21: 1 GB heap → 1 MB, default 3.4 GB heap → 2 MB, `-Xmx40g` → 32 MB regions — [L3].
- Humongous objects: anything larger than half a region (`humongous_threshold_for(region_size) { return (region_size / 2); }`) is allocated directly in contiguous humongous regions — [g1CollectedHeap.hpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/g1/g1CollectedHeap.hpp). In [L2] 3 MiB buffers showed up as `Humongous regions: 8->0` and as GC cause `(G1 Humongous Allocation)`.
- G1 tuning defaults (JDK 25): `InitiatingHeapOccupancyPercent 45`, `G1UseAdaptiveIHOP true`, `G1MixedGCCountTarget 8` ("target number of mixed GCs after a marking cycle"), `G1HeapWastePercent 5`, `G1MixedGCLiveThresholdPercent 85` (experimental), `G1OldCSetRegionThresholdPercent 10` (experimental), `G1ReservePercent 10`, `G1NewSizePercent 5` / `G1MaxNewSizePercent 60` (experimental), `G1RSetUpdatingPauseTimePercent 10`, `MaxTenuringThreshold 15`, `SoftMaxHeapSize` manageable — [g1_globals.hpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/g1/g1_globals.hpp), [gc_globals.hpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/shared/gc_globals.hpp).
- Write barriers: "This barrier is specialized to use a logging barrier to support snapshot-at-the-beginning marking"; `G1BarrierSet` extends `CardTableBarrierSet` and owns a `G1SATBMarkQueueSet` and a `G1DirtyCardQueueSet` — [g1BarrierSet.hpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/g1/g1BarrierSet.hpp) (JDK 25; JEP 522 reworked this in 26, see Q1).
- Card size: G1 startup log on JDK 21 prints `CardTable entry size: 512` — [L2].
- G1 pause phases as logged on JDK 21: `Pre Evacuate Collection Set`, `Merge Heap Roots` (remembered sets merged into the scan), `Evacuate Collection Set`, `Post Evacuate Collection Set`, `Other` — [L2]. Concurrent cycle phases: `Concurrent Scan Root Regions`, `Concurrent Mark From Roots`, `Concurrent Preclean`, `Pause Remark`, `Concurrent Rebuild Remembered Sets and Scrub Regions`, `Pause Cleanup`, `Concurrent Clear Claimed Marks`, `Concurrent Cleanup for Next Mark` — [L2].
- Full GC is mark-compact in 5 phases (JDK 21 G1): `Phase 1: Mark live objects`, `Phase 2: Prepare compaction`, `Phase 3: Adjust pointers`, `Phase 4: Compact heap`, `Phase 5: Reset Metadata` — [L2].
- GC cause strings in HotSpot include `System.gc()`, `Allocation Failure`, `Metadata GC Threshold`, `G1 Evacuation Pause`, `G1 Compaction Pause`, `G1 Humongous Allocation`, `G1 Periodic Collection`, `Diagnostic Command`, `Heap Dump Initiated GC`, `Heap Inspection Initiated GC`, `Warmup`, `Allocation Rate`, `Allocation Stall`, `Proactive`, `High Usage`, `Timer` — [gcCause.cpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/shared/gcCause.cpp).
- Safepoints: `-Xlog:safepoint` line on JDK 21: `Safepoint "G1CollectForAllocation", Time since last: 32350666 ns, Reaching safepoint: 3409 ns, Cleanup: 4274 ns, At safepoint: 1671830 ns, Leaving safepoint: 1364 ns, Total: 1680877 ns` — [L2].
- Generational evidence from a real run: generational ZGC's age table for one minor GC on the workload: `Eden 27M (3%) live / 470M (46%) garbage`, `Survivor 1 43M live / 2M garbage` — [L2]: most young objects die young, survivors mostly stay alive.

### Inferences
- "Reaching safepoint" (time-to-safepoint) is separate from the GC work ("At safepoint"); long TTSP points at code without safepoint polls (e.g. long counted loops), not at the collector.
- G1's 200 ms default pause goal is a *goal*: pauses in [L2] were 1–50 ms on 1 GB heaps; the risky events are `(Evacuation Failure)` and `Pause Full (G1 Compaction Pause)`, both of which signal a heap too small for the live set + allocation rate.
- Background concepts (copying vs mark-compact, generational hypothesis, SATB, card marking) are standard GC theory; the source comments above confirm HotSpot's G1 uses SATB marking and card tables, but a primary reference text (GC Tuning Guide) could not be fetched.

### Gaps
- HotSpot GC Tuning Guide (docs.oracle.com/en/java/javase/25/gctuning) unreachable; G1 descriptions of adaptive IHOP and mixed-GC candidate selection come only from flag help text.
- JEP 522's dual-card-table design known only from a search snippet.

---

## Q6. Low-pause collectors (ZGC, Shenandoah) and how to choose a GC (Serial, Parallel, G1, ZGC, Shenandoah, Epsilon)

### Takeaway
ZGC (generational only since JDK 24) and Shenandoah do marking *and* relocation/evacuation concurrently, so pauses are sub-millisecond and independent of heap size, paid for with CPU and barrier overhead. G1 stays the right default for most payment services; pick ZGC when tail latency matters and spare cores exist; Serial for tiny single-CPU containers; Parallel for batch throughput; Epsilon only for tests and allocation budgets.

### Cited Findings
- ZGC: "a low latency garbage collector, providing max pause times of a few milliseconds, at some throughput cost. Pause times are independent of what heap size is used. Supports heap sizes from 8MB to 16TB." — [java.md@jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/java.base/share/man/java.md). Tuning flags documented there: `ZAllocationSpikeTolerance` (default 2.0), `ZCollectionInterval` (0 = disabled), `ZFragmentationLimit` (25), `ZProactive` (enabled), `ZUncommit` (enabled), `ZUncommitDelay` (300 s) — same source.
- ZGC colored pointers: "Layout of metadata bits in colored pointer / zpointer ... Used by load barrier", with "Remapped bits" `RRRR` and bit patterns like `aaa...aaa0001MMmmFFrr0000 = Remapped00 zpointer` — [zAddress.hpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/z/zAddress.hpp).
- Measured ZGC pauses (generational, JDK 21, 1 GB heap): `y: Pause Mark Start 0.021ms`, `y: Pause Mark End 0.017ms`, `y: Pause Relocate Start 0.017ms`, while the whole minor collection took `0.052s` concurrently — [L2]. Startup: `GC Workers for Old Generation: 1 (dynamic)`, `GC Workers for Young Generation: 1 (dynamic)`, `Uncommit Delay: 300s`, `Heap Backing File: /memfd:java_heap` — [L2].
- Shenandoah: "a low pause time, concurrent garbage collector. Its pause times are not proportional to the size of the heap"; modes `satb` ("Snapshot-at-the-beginning concurrent GC (three pass mark-evac-update). It is a single generation GC") and `generational`; heuristics `adaptive` (default; the only one supported in generational mode), `static`, `compact` — [java.md@jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/java.base/share/man/java.md).
- Shenandoah turns `System.gc()` into concurrent cycles: `Heuristics ergonomically sets -XX:+ExplicitGCInvokesConcurrent` and `-XX:+ShenandoahImplicitGCInvokesConcurrent` (JDK 21 log) — [L2]. Pauses measured: `Pause Init Mark (unload classes) 0.159ms`, `Pause Final Mark (unload classes) 0.174ms`, `Pause Init Update Refs 0.005ms`, `Pause Final Update Refs 0.022ms` — [L2].
- Serial: "generally the best choice for small and simple applications that don't require any special functionality from garbage collection" — [java.md@jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/java.base/share/man/java.md). Parallel: "the throughput collector ... leveraging multiple processors"; `UseGCOverheadLimit`: "the parallel GC will throw an OutOfMemoryError if more than 98% of the total time is spent on garbage collection and less than 2% of the heap is recovered" — same source. G1: "recommended for applications requiring large heaps (sizes of around 6 GB or larger) with limited GC latency requirements (a stable and predictable pause time below 0.5 seconds)" — same source.
- Epsilon: `UseEpsilonGC` is `EXPERIMENTAL` (needs `-XX:+UnlockExperimentalVMOptions`) in 21 through 27 — [gc_globals.hpp@jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/hotspot/share/gc/shared/gc_globals.hpp). Measured [L7]: `Using Epsilon`, `Heap: 128M reserved, 128M (100.00%) committed, 125M (98.10%) used`, then `Terminating due to java.lang.OutOfMemoryError: Java heap space`.
- Same workload (cache = 30% of heap), 1 GB max heap on JDK 21 [L2] (event counts, not a benchmark): G1 (8 s run, `-Xms1g`) — 20 young-only pauses (2 with evacuation failure), 1 concurrent cycle, 1 prepare-mixed, 1 mixed, then the final `System.gc()` full GC; generational ZGC (5 s) — 57 cycles = 46 minor + 3 warmup major + 7 allocation-rate major + 1 `System.gc()` major, 0 allocation stalls in the sampled cycle; non-generational ZGC (5 s) — ~48 cycles (one `Garbage Collection (...)` line each); Parallel `Pause Young (Allocation Failure) 55M->5M(205M) 13.814ms`; Serial needed `Pause Full (Allocation Failure)` repeatedly (e.g. `253M->253M(586M) 33.416ms`).
- Lab tests (references, Cleaner, histogram, ThreadLocal) passed unchanged under G1, Serial, Parallel, ZGC (both modes) and Shenandoah on JDK 21 — [L6].

### Inferences
Decision table for the course (inference from the cited behaviour, not a benchmark):

| Collector | Pick when | Watch out for |
|---|---|---|
| Serial | ≤ 1 CPU and small heap (≤ a few hundred MB); was the silent default in small containers on JDK ≤ 26 | full GCs scale with live set |
| Parallel | batch/ETL, throughput over latency | long full-GC pauses on big heaps |
| G1 (default) | general services incl. Quarkus payments APIs; heaps from ~256 MB to tens of GB | `(Evacuation Failure)`, `Pause Full (G1 Compaction Pause)`, humongous churn |
| ZGC (generational) | p99/p999 latency SLOs, large heaps, spare CPU | concurrent GC threads compete with app threads in CPU-limited pods; `Allocation Stall` = heap too small |
| Shenandoah | similar to ZGC; available in OpenJDK builds such as Ubuntu's (ran here) | generational mode is product only from 25; vendor availability varies |
| Epsilon | tests: allocation budgets, "does this code path allocate", GC-free benchmarks | process dies at heap exhaustion by design |

### Gaps
- No throughput/latency benchmarking was done (container noise; out of scope); the event counts above are illustrative only.
- Whether Oracle JDK builds ship Shenandoah was not verified (no access to Oracle docs).
- GraalVM native-image GCs (relevant to Quarkus native mode) were not researched.

---

## Q7. How do you read real GC log lines (G1 young pause, mixed, ZGC cycle)?

### Takeaway
Unified logging (`-Xlog:gc` for one line per event, `-Xlog:gc*` for phases/heap/metaspace detail) prints `[uptime][level][tags] GC(id) <event> (<cause>) <before>-><after>(<capacity>) <duration>`. For G1 the duration is a stop-the-world pause; for ZGC the one-line duration is the *concurrent cycle*, and the real pauses are the sub-millisecond `Pause ...` phase lines.

### Cited Findings
All lines below are **verbatim from JDK 21.0.12 runs** [L2] (`-Xlog:gc` default decorators `uptime,level,tags`).

**G1 young pause**
```
[0.128s][info][gc] GC(0) Pause Young (Normal) (G1 Evacuation Pause) 14M->1M(256M) 12.723ms
```
- `[0.128s]` JVM uptime; `[info]` level; `[gc]` tag set; `GC(0)` GC id (concurrent cycles get their own id, and pause lines inside a cycle reuse it);
- `Pause Young` = STW evacuation of eden + survivors; `(Normal)` = young-only (other values: `(Concurrent Start)`, `(Prepare Mixed)`, `(Mixed)`);
- `(G1 Evacuation Pause)` = cause (eden exhausted); other causes seen: `(G1 Humongous Allocation)`, `(System.gc())`;
- `14M->1M` = heap used before → after; `(256M)` = committed heap; `12.723ms` = pause time.

Same event with `-Xlog:gc*` (1 GB heap run):
```
[0.701s][info][gc,start    ] GC(3) Pause Young (Normal) (G1 Evacuation Pause)
[0.701s][info][gc,task     ] GC(3) Using 4 workers of 4 for evacuation
[0.717s][info][gc,phases   ] GC(3)   Pre Evacuate Collection Set: 0.32ms
[0.717s][info][gc,phases   ] GC(3)   Merge Heap Roots: 0.04ms
[0.717s][info][gc,phases   ] GC(3)   Evacuate Collection Set: 15.51ms
[0.717s][info][gc,phases   ] GC(3)   Post Evacuate Collection Set: 0.25ms
[0.717s][info][gc,phases   ] GC(3)   Other: 0.08ms
[0.717s][info][gc,heap     ] GC(3) Eden regions: 120->0(199)
[0.717s][info][gc,heap     ] GC(3) Survivor regions: 13->14(17)
[0.717s][info][gc,heap     ] GC(3) Old regions: 2->9
[0.717s][info][gc,heap     ] GC(3) Humongous regions: 8->0
[0.717s][info][gc,metaspace] GC(3) Metaspace: 164K(384K)->164K(384K) NonClass: 156K(256K)->156K(256K) Class: 8K(128K)->8K(128K)
[0.717s][info][gc          ] GC(3) Pause Young (Normal) (G1 Evacuation Pause) 141M->20M(1024M) 16.335ms
[0.717s][info][gc,cpu      ] GC(3) User=0.00s Sys=0.01s Real=0.02s
```
- `Eden regions: 120->0(199)` = before → after (target eden size for the next cycle, adaptive); survivors `13->14(17)` (max); old `2->9` = 7 regions promoted; `Humongous regions: 8->0` = dead humongous buffers reclaimed eagerly in a young pause.
- `Evacuate Collection Set` = the copying work; `Merge Heap Roots` = folding remembered sets/cards into roots.

**G1 concurrent cycle → mixed collections** (1 GB heap, cache = 30% of heap)
```
[7.552s][info][gc] GC(20) Pause Young (Concurrent Start) (G1 Humongous Allocation) 556M->527M(1024M) 13.734ms
[7.560s][info][gc] GC(21) Concurrent Mark Cycle
[7.580s][info][gc] GC(21) Pause Remark 583M->583M(1024M) 0.835ms
[7.604s][info][gc] GC(21) Pause Cleanup 637M->637M(1024M) 0.379ms
[7.613s][info][gc] GC(21) Concurrent Mark Cycle 53.866ms
[7.885s][info][gc] GC(22) Pause Young (Prepare Mixed) (G1 Evacuation Pause) (Evacuation Failure) 996M->760M(1024M) 43.391ms
[8.054s][info][gc] GC(23) Pause Young (Mixed) (G1 Evacuation Pause) 981M->660M(1024M) 10.429ms
[8.365s][info][gc] GC(24) Pause Full (System.gc()) 974M->1M(1024M) 46.892ms
```
- `Concurrent Start` = a young pause that also starts marking (here triggered by a humongous allocation crossing the IHOP); `Concurrent Mark Cycle` runs alongside the app (53.9 ms total, 1 worker); `Pause Remark` finalizes marking (0.8 ms); `Pause Cleanup` (0.4 ms); `Prepare Mixed` = last young-only pause before mixed; `Mixed` = young regions + some old regions with the most garbage (`981M->660M`, note bigger drop than a young pause).
- `(Evacuation Failure)` = G1 could not copy some objects (no free regions); the regions are kept in place — the log equivalent of "heap too small". In the stressed 256 MB run it preceded `Pause Full (G1 Compaction Pause) 224M->94M(256M) 16.652ms`.
- Whole stressed run (256 MB heap, cache 60%, 8 s): 33 Normal (28 evacuation-pause + 5 humongous-allocation), 35 Concurrent Start, 32 Prepare Mixed, 91 Mixed, 35 concurrent mark cycles, 4 `Pause Full (G1 Compaction Pause)` — a lab-ready "bad config" sample.

`-Xlog:gc*` for a mixed pause (256 MB heap):
```
[0.908s][info][gc,start    ] GC(18) Pause Young (Mixed) (G1 Evacuation Pause)
[0.912s][info][gc,heap     ] GC(18) Eden regions: 62->0(44)
[0.912s][info][gc,heap     ] GC(18) Survivor regions: 8->6(9)
[0.912s][info][gc,heap     ] GC(18) Old regions: 172->192
[0.912s][info][gc,heap     ] GC(18) Humongous regions: 4->0
[0.912s][info][gc          ] GC(18) Pause Young (Mixed) (G1 Evacuation Pause) (Evacuation Failure) 242M->195M(256M) 4.411ms
```
(old regions *grew* 172→192 because of the evacuation failure: failed regions stay old.)

Other G1 lines worth showing:
- `[6.089s][info][gc] GC(151) Pause Young (Concurrent Start) (System.gc()) 177M->87M(256M) 4.693ms` — `System.gc()` with `-XX:+ExplicitGCInvokesConcurrent`.
- `GC(1) Concurrent Undo Cycle` (0.084 ms, [L7] soft-ref run) — my interpretation: the concurrent start was triggered by a humongous allocation, and by the time marking would begin occupancy was below the threshold again, so G1 undid the cycle instead of marking (semantics not verified against documentation).
- Startup block (`-Xlog:gc*`): `Using G1`, `CPUs: 4 total, 4 available`, `Memory: 13673M`, `Compressed Oops: Enabled (32-bit)`, `Heap Region Size: 1M`, `Heap Min Capacity: 1G`, `Heap Initial Capacity: 1G`, `Heap Max Capacity: 1G`, `Parallel Workers: 4`, `Concurrent Workers: 1`, `Concurrent Refinement Workers: 4`, `Periodic GC: Disabled`.

**Generational ZGC (JDK 21 `-XX:+UseZGC -XX:+ZGenerational`; the only ZGC mode on 24+)**
```
[0.368s][info][gc] GC(0) Major Collection (Warmup)
[0.434s][info][gc] GC(0) Major Collection (Warmup) 106M(10%)->182M(18%) 0.066s
[1.278s][info][gc] GC(4) Minor Collection (Allocation Rate)
[1.331s][info][gc] GC(4) Minor Collection (Allocation Rate) 582M(57%)->226M(22%) 0.052s
[5.313s][info][gc] GC(56) Major Collection (System.gc())
[5.354s][info][gc] GC(56) Major Collection (System.gc()) 472M(46%)->2M(0%) 0.041s
```
- Two lines per cycle (start, end). `Minor Collection` = young generation only; `Major Collection` = young + old. Causes seen: `Warmup` (first cycles while ZGC learns allocation rate), `Allocation Rate` (predicted to run out), `System.gc()`.
- `582M(57%)->226M(22%)` = used at mark start → used at relocate end (percent of max heap); `0.052s` = **concurrent cycle duration, not a pause**.
- After can exceed before: `GC(7) Major Collection (Allocation Rate) 342M(33%)->466M(46%) 0.119s` because the application kept allocating during the 119 ms cycle.

`-Xlog:gc*` for the minor collection (selected lines):
```
[1.279s][info][gc,phases   ] GC(4) y: Young Generation
[1.279s][info][gc,phases   ] GC(4) y: Pause Mark Start 0.021ms
[1.297s][info][gc,phases   ] GC(4) y: Concurrent Mark 16.749ms
[1.297s][info][gc,phases   ] GC(4) y: Pause Mark End 0.017ms
[1.304s][info][gc,reloc    ] GC(4) y: Using tenuring threshold: 4 (Computed)
[1.305s][info][gc,phases   ] GC(4) y: Concurrent Select Relocation Set 2.104ms
[1.305s][info][gc,phases   ] GC(4) y: Pause Relocate Start 0.017ms
[1.331s][info][gc,phases   ] GC(4) y: Concurrent Relocate 24.731ms
[1.331s][info][gc,alloc    ] GC(4) y: Allocation Stalls:          0                0                0                0
[1.331s][info][gc,mmu      ] GC(4) y: MMU: 2ms/97.4%, 5ms/99.0%, 10ms/99.3%, 20ms/99.5%, 50ms/99.8%, 100ms/99.8%
[1.331s][info][gc,reloc    ] GC(4) y: Eden              27M (3%)          470M (46%)        233 / 217            1 / 0              0 / 0
[1.331s][info][gc,heap     ] GC(4) y:      Live:         -                99M (10%)          95M (9%)           94M (9%)
[1.331s][info][gc,heap     ] GC(4) y:  Promoted:         -                  -                 3M (0%)            4M (0%)
[1.331s][info][gc,phases   ] GC(4) y: Young Generation 582M(57%)->226M(22%) 0.052s
```
- Prefixes: `y:` = young collection of a minor GC; in a major GC `Y:` = its young part and `O:` = old generation (e.g. `O: Concurrent Mark 47.970ms`, `O: Concurrent Remap Roots 37.542ms`, `O: Pause Relocate Start 0.046ms`).
- The three `Pause ...` lines (≈0.02 ms each) are the only STW parts. `Allocation Stalls` must stay 0 (non-zero = threads blocked waiting for memory: heap too small or GC too slow). `MMU 2ms/97.4%` = in any 2 ms window the app got ≥ 97.4% of time. The Eden row (live 27M vs garbage 470M) shows the generational hypothesis.

**Non-generational ZGC (JDK 21 default `-XX:+UseZGC`; removed in 24)**: `[0.622s][info][gc] GC(3) Garbage Collection (Allocation Rate) 364M(36%)->120M(12%)` with phases `Pause Mark Start 0.009ms`, `Concurrent Mark 12.268ms`, `Pause Mark End 0.014ms`, `Concurrent Process Non-Strong References 0.444ms`, `Pause Relocate Start 0.009ms`, `Concurrent Relocate 6.687ms`.

**Shenandoah (satb)**: `GC(0) Pause Init Mark (unload classes) 0.159ms` → `Concurrent marking (unload classes) 2.978ms` → `Pause Final Mark (unload classes) 0.174ms` → `Concurrent evacuation 8.790ms` → `Pause Init Update Refs 0.005ms` → `Concurrent update references 2.547ms` → `Pause Final Update Refs 0.022ms` → `Concurrent cleanup 157M->43M(277M) 0.061ms`; trigger lines like `Trigger: Learning 1 of 5. Free (716M) is below initial threshold (716M)`.

**Parallel / Serial**: `GC(0) Pause Young (Allocation Failure) 55M->5M(205M) 13.814ms` (Parallel), `GC(48) Pause Full (Allocation Failure) 151M->151M(351M) 8.752ms` (Serial: a full GC that freed nothing).

### Inferences
- Teach students to grep three things first: `Pause Full`, `(Evacuation Failure)` (G1) / `Allocation Stall` (ZGC), and the `after` value trend of young pauses (a rising floor = growing live set = possible leak).
- `Pause Full (System.gc())` collapsing to `->1M` is a sign that a library or `jcmd` asked for it; Quarkus apps should not call `System.gc()`.
- In production logging use `-Xlog:gc*:file=gc.log:time,uptime,level,tags:filecount=5,filesize=20m` (standard unified-logging syntax; rotation options not verified in this session).

### Gaps
- Logs are from JDK 21; JDK 25/27 G1 phase names may differ after JEP 522 (not verified).
- The GC Tuning Guide's official field-by-field explanation of G1 log lines could not be fetched; the explanations above are from reading the logs against the source cause strings.

---

## Q8. Heap sizing in containers and memory outside the heap (NMT, direct buffers, FFM)

### Takeaway
The JVM sizes its heap from the container's memory limit (25% by default), and everything else — thread stacks, metaspace, code cache, GC structures, direct buffers, FFM segments, malloc by native libraries — sits on top. Setting `-Xmx` equal to the container limit leaves no room for that native memory; size the heap with `-XX:MaxRAMPercentage` (typically well under 100%) and verify with Native Memory Tracking.

### Cited Findings
- Container detection: "The VM now provides automatic container detection support, which allows the VM to determine the amount of memory and number of processors that are available to a Java process running in docker containers ... The default for this flag is true ... Use `-Xlog:os+container=trace` for maximum logging" — [java.md@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/man/java.md).
- Measured on this cgroup-v1 container [L3]: `-XshowSettings:system` → `Provider: cgroupv1`, `Effective CPU Count: 4`, `Memory Limit: 13.35G`; `-Xlog:os+container=debug` → `Detected cgroups hybrid or legacy hierarchy, using cgroups v1 controllers`, `OSContainer::init: is_containerized() = true because either a cpu or a memory limit is present`; default `MaxHeapSize` = 25% of 13.35G.
- `MaxRAMPercentage`: "Sets the maximum amount of memory that the JVM may use for the Java heap before applying ergonomics heuristics as a percentage of the maximum amount determined as described in the `-XX:MaxRAM` option. The default value is 25 percent. Specifying this option disables automatic use of compressed oops if the combined result of this and other options influencing the maximum amount of memory is larger than the range of memory addressable by compressed oops." — [java.md@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/man/java.md).
- Heap ergonomics source (JDK 25): if any of `MaxRAMPercentage/MinRAMPercentage/InitialRAMPercentage/MaxRAM` is set, the physical (container) memory is used directly and compressed oops can be disabled with the log message "UseCompressedOops and UseCompressedClassPointers have been disabled due to max heap ... Please check the setting of MaxRAMPercentage"; otherwise memory is `MIN2(os::physical_memory(), MaxRAM)`; `MinRAMPercentage` applies "on systems with small physical memory size" — [arguments.cpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/runtime/arguments.cpp). JDK 26 rewrote this: `MaxRAM` is set to `os::physical_memory()` (or 1 GB in client-emulation mode) and the initial heap is `MaxRAM * InitialRAMPercentage / 100` (now 0) raised to at least `OldSize + NewSize` / `MinHeapSize` — [arguments.cpp@jdk-26-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-26-ga/src/hotspot/share/runtime/arguments.cpp). JDK 27 doc: `InitialRAMPercentage` is "a percentage of the available memory to the JVM process" — [java.md@jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/java.base/share/man/java.md).
- Measured heap maths on JDK 21 using `-XX:MaxRAM` as a stand-in for a container limit [L3]: `MaxRAM=1g` → `MaxHeapSize=268435456` (256 MB, 25%), `InitialHeapSize=16777216`; `MaxRAM=1g -XX:MaxRAMPercentage=75` → `MaxHeapSize=805306368` (768 MB); `MaxRAM=256m` → `MaxHeapSize=132120576` (126 MB, the 50% `MinRAMPercentage` rule for small memory).
- Native memory for a 256 MB heap [L4]: total committed **390 MB**, of which Java heap 216 MB committed; non-heap committed ≈ 174 MB (GC 45, Other/direct+FFM 96, Shared class space 13, Code 7, Thread 6 for 71 threads, Arena 2, Metaspace 1, Symbol 1, Internal 1). Reserved (virtual) total 1820 MB.
- NMT usage: `-XX:NativeMemoryTracking=`*mode* — [java.md@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/man/java.md); `jcmd VM.native_memory` options `summary`, `detail`, `baseline`, `summary.diff`, `detail.diff`, `statistics`, `scale` (KB/MB/GB) — [jcmd.md@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.jcmd/share/man/jcmd.md). Default `NativeMemoryTracking` is `"off"` in product builds — [globals.hpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/runtime/globals.hpp).
- Direct buffer limit: "-XX:MaxDirectMemorySize not given, take default → `directMemory = Runtime.getRuntime().maxMemory()`" — [VM.java@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/jdk/internal/misc/VM.java). So by default off-heap NIO buffers may grow to another full `-Xmx`.
- Measured [L5]: `-XX:MaxDirectMemorySize=32m` + `allocateDirect(64 MB)` → `java.lang.OutOfMemoryError: Cannot reserve 67108864 bytes of direct buffer memory (allocated: 0, limit: 33554432)` at `java.nio.Bits.reserveMemory`.
- FFM: Arena kinds — Global (unbounded lifetime, not closeable, multi-thread), Automatic (bounded, GC-managed, not closeable, multi-thread), Confined (bounded, closeable, single thread), Shared (bounded, closeable, multi-thread) — [Arena.java@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/foreign/Arena.java). FFM is final since JDK 22 (JEP 454; the man page's `--enable-native-access` entry links `openjdk.org/jeps/454#Safety` — [java.md@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/man/java.md)); on JDK 21 it is preview: `error: Arena is a preview API and is disabled by default.` — [L8].
- FFM segments count against the direct-memory limit: JDK 25 `SegmentFactories` calls `NIO_ACCESS.reserveMemory(allocationSize, byteSize)` when allocating native segments (and `unreserveMemory` on free) — [SegmentFactories.java@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/jdk/internal/foreign/SegmentFactories.java). Measured on JDK 21: `Arena.ofConfined().allocate(32 MB)` under `-XX:MaxDirectMemorySize=16m` → `OutOfMemoryError: Cannot reserve 33554432 bytes of direct buffer memory (allocated: 0, limit: 16777216)`; and `BufferPoolMXBean` "direct" reported `count=2 used=100663296` for 64 MB direct + 32 MB segment — [L4], [L5].

### Inferences
- Rule of thumb for a payments pod (inference, to be validated per service with NMT): heap ≈ 50–75% of the limit via `-XX:MaxRAMPercentage`, cap direct memory explicitly (`-XX:MaxDirectMemorySize`) when Netty/Vert.x (Quarkus' I/O layer) is in play, and keep thread count bounded (each platform thread reserves stack).
- If the process exceeds the cgroup limit the kernel's OOM killer ends it (typically exit code 137): no `OutOfMemoryError`, no heap dump, no `ExitOnOutOfMemoryError`. This is standard Linux/cgroup behaviour, not verified in this session.
- `-XX:MaxRAM` is fine for a JDK 21/25 lab but is deprecated in 26 and obsolete in 27; a lab targeting 27 needs real container limits (`docker run --memory`) instead.

### Gaps
- No real container (Docker/Podman) was available; cgroup v2 behaviour and `-XX:ActiveProcessorCount` interaction with CPU quotas not measured.
- Quarkus-specific memory defaults (e.g. its container-image JVM options) not researched.

---

## Q9. Memory leaks: heap dumps, Eclipse MAT, common leak patterns

### Takeaway
A leak is memory that stays reachable from a GC root after it is no longer needed. Capture evidence with `jcmd <pid> GC.class_histogram` (fast, forces a full GC) and `jcmd <pid> GC.heap_dump` or `-XX:+HeapDumpOnOutOfMemoryError`, then use MAT's dominator tree and retained sizes to find the object that keeps the leak alive. In services the usual culprits are unbounded maps/caches, ThreadLocals on pooled threads, listeners never unregistered, and classloader leaks.

### Cited Findings
- `GC.heap_dump`: "Generate a HPROF format dump of the Java heap. Impact: High ... Request a full GC unless the '-all' option is specified"; options on JDK 21: `-all`, `-gz` (compression level 1–9), `-overwrite` — [L5]; JDK 24/25/27 docs add `-parallel` ("Number of parallel threads to use for heap dump") and `%p` expansion to the PID in the filename — [jcmd.md@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.jcmd/share/man/jcmd.md), [jcmd.md@jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/jdk.jcmd/share/man/jcmd.md).
- `HeapDumpOnOutOfMemoryError` default `false`, `MANAGEABLE` (can be switched on at runtime) — [globals.hpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/runtime/globals.hpp).
- Measured [L5] (`-Xmx64m -XX:+HeapDumpOnOutOfMemoryError`, unbounded `ConcurrentHashMap` idempotency cache):
  ```
  java.lang.OutOfMemoryError: Java heap space
  Dumping heap to .../oom.hprof ...
  Heap dump file created [70967188 bytes in 0.048 secs]
  ```
- Measured class histogram of the leaking service after 20,000 requests [L5]:
  ```
   num     #instances         #bytes  class name (module)
  -------------------------------------------------------
     1:         49704       42820600  [B (java.base@21.0.12.1)
     2:         29621         710904  java.lang.String (java.base@21.0.12.1)
     3:         22201         710432  java.util.concurrent.ConcurrentHashMap$Node (java.base@21.0.12.1)
     4:         20000         640000  LeakyService$PaymentResponse
  ```
  and `jcmd <pid> GC.heap_dump .../live.hprof` → `Heap dump file created [49817293 bytes in 0.096 secs]`.
- MAT dominator tree: "An object x dominates an object y if every path in the object graph from the start (or the root) node to y must go through x ... The objects belonging to the sub-tree of x (i.e. the objects dominated by x) represent the retained set of x ... The edges in the dominator tree do not directly correspond to object references from the object graph." — [MAT help: dominatortree.html](https://raw.githubusercontent.com/eclipse-mat/mat/master/plugins/org.eclipse.mat.ui.help/concepts/dominatortree.html).
- MAT shallow vs retained: "Shallow heap is the memory consumed by one object ... Retained set of X is the set of objects which would be removed by GC when X is garbage collected. Retained heap of X is the sum of shallow sizes of all objects in the retained set of X, i.e. memory kept alive by X." — [MAT help: shallowretainedheap.html](https://raw.githubusercontent.com/eclipse-mat/mat/master/plugins/org.eclipse.mat.ui.help/concepts/shallowretainedheap.html).
- MAT GC roots: "A garbage collection root is an object that is accessible from outside the heap", kinds include System Class, JNI Local, JNI Global, Thread Block, Thread ("A started, but not stopped, thread"), Busy Monitor, Java Local, Native Stack — [MAT help: gcroots.html](https://raw.githubusercontent.com/eclipse-mat/mat/master/plugins/org.eclipse.mat.ui.help/concepts/gcroots.html).
- ThreadLocal-in-pool retention measured [L6]: a 1 MiB value set in a `ThreadLocal` inside a task on a 1-thread pool stays strongly reachable after the task finishes (WeakReference to it non-null after 5 × `System.gc()`), and becomes collectable only after a task calls `remove()` on the same pooled thread.
- Listener/static-collection leak measured [L6]: 10,000 `LeakedPaymentEvent` objects held by a static `List` → `gcClassHistogram` reports exactly 10,000 instances; after `clear()` exactly 0.

### Inferences
- In the dominator tree for [L5] one expects `LeakyService` class → static `IDEMPOTENCY_CACHE` (`ConcurrentHashMap`) to retain ~42 MB (the `byte[]` receipts); the histogram alone shows *what* (byte[]), the dominator tree shows *who holds it*.
- Classloader leaks (redeploys, dynamic proxies, metaspace growth) show up as `Class` / `Metaspace` growth in NMT and repeated `Metadata GC Threshold` GC causes; Quarkus in production rarely redeploys, but dev mode and test suites do.

### Gaps
- MAT itself was not run (download and execution of a desktop tool was out of reach); the dominator-tree result for the sample dump is an expectation, not an observation.
- MAT "Leak Suspects" report wording not extracted.

---

## Q10. What are the most common misconceptions?

### Takeaway
Most misconceptions come from treating the JVM process as "the heap": `-Xmx` is not process memory, `System.gc()` is a hint that can be disabled, a bigger heap can hold less data and pause longer, ZGC trades CPU for latency, and weak references make terrible caches.

### Cited Findings
1. **"`System.gc()` frees memory now."** The Javadoc: "There is no guarantee that this effort will recycle any particular number of unused objects, reclaim any particular amount of space, or complete at any particular time, if at all" — [Runtime.java@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Runtime.java). With `-XX:+DisableExplicitGC`, 25 of 63 lab test executions that wait for GC failed — [L6]; with `-XX:+ExplicitGCInvokesConcurrent` G1 logs `Pause Young (Concurrent Start) (System.gc())` instead of a full GC, and Shenandoah turns that flag on by itself — [L2]. Freeing heap is not the same as returning memory to the OS: with `-Xms1g`, `Pause Full (System.gc()) 974M->1M(1024M)` keeps capacity at 1024M — [L2]; without `-Xms`, a G1 full GC did shrink it (`Pause Full (G1 Compaction Pause) 42M->1M(8M)`) — [L7]; returning memory is otherwise a separate policy (`ZUncommitDelay 300`s, `G1PeriodicGCInterval 0` = off) — [z_globals.hpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/z/z_globals.hpp), [g1_globals.hpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/g1/g1_globals.hpp).
2. **"A bigger heap is always better."** Above ~32 GB compressed oops switch off (`-Xmx40g` → `UseCompressedOops=false`) and the same `ArrayList<Integer>` grows from 20,976 to 25,920 bytes — [L1], [L3]; bigger heaps also mean bigger regions (32 MB at 40 GB) — [L3]; and in a container, heap + native must fit the limit (Q8).
3. **"ZGC is always best."** The man page itself says "at some throughput cost" — [java.md@jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/java.base/share/man/java.md); ZGC's "before→after" in the log is a concurrent cycle, and allocation can outrun it (`342M(33%)->466M(46%)`) — [L2].
4. **"`-Xmx` caps total process memory."** A `-Xmx256m` process committed 390 MB (NMT) — [L4]; default direct memory limit = max heap — [VM.java@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/jdk/internal/misc/VM.java); metaspace is unbounded by default (`MaxMetaspaceSize max_uintx`) — [globals.hpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/runtime/globals.hpp).
5. **"Use weak references for caches."** A weakly-reachable value is gone as soon as a GC processes references: in [L6] the bounded `System.gc()` loop cleared and enqueued it every time (10/10, every collector). `WeakHashMap` is weak on *keys* and warns that values must not reference their keys — [WeakHashMap.java@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/WeakHashMap.java). Soft references are the "memory-sensitive cache" reference type but are only "guaranteed" to be cleared before OOME, otherwise timing is unspecified — [SoftReference.java@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/ref/SoftReference.java).
6. **"An `Integer` costs 4 bytes / objects cost their fields."** `Integer` = 16 bytes, `Long` = 24, a 3-char `String` = 48 bytes total — [L1].
7. **"Every `new` hits the heap."** After C2 compilation a non-escaping `Point` allocation costs 0 bytes; with `-XX:-DoEscapeAnalysis` 32 MB per million — [L7].
8. **"`finalize()` is a destructor."** Deprecated for removal; can be disabled wholesale (`finalized=0` with `--finalization=disabled`) — [Object.java@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Object.java), [L7].
9. **"Compact headers save 4 bytes on every object."** "4 bytes per object (on average)" — [java.md@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/man/java.md); alignment means some objects save 8 bytes (`Object` 16→8, `Long` 24→16, `Payment` 40→32) and some save nothing (`Integer` stays 16, `String` stays 24) — [L1] simulation.
10. **"The JVM picks G1 everywhere."** Only from JDK 27; on 21–26 a 1-CPU container gets Serial — [gcConfig.cpp@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/shared/gcConfig.cpp), [L3].

### Inferences
- "A heap dump will explain my container OOM-kill" is also wrong: a heap dump covers the Java heap only; native growth needs NMT (inference from Q8 data).

### Gaps
- No primary source (Oracle tuning guide, GC-team talks) was reachable to quote on "ZGC vs G1" guidance beyond the man page.

---

## Q11. Which hands-on exercises work in a Gradle lab with JUnit (deterministic assertions only)?

### Takeaway
All of the requested exercises can be made deterministic on JDK 21 by (a) measuring with `getCurrentThreadAllocatedBytes` in code that runs once, (b) waiting for reference processing with a bounded `System.gc()` + `ReferenceQueue.remove(timeout)` loop, and (c) counting live instances with the class-histogram diagnostic command (which forces a full GC). They passed 3 out of 3 full runs and under every collector, but **fail if the test JVM gets `-XX:+DisableExplicitGC`**.

### Cited Findings
- Results [L6] on JDK 21.0.12 with JUnit Platform Console 6.1.3: `63 tests successful, 0 tests failed` in 3/3 runs (default G1); also 63/63 under `-XX:+UseZGC -XX:+ZGenerational`, `-XX:+UseZGC`, `-XX:+UseSerialGC`, `-XX:+UseParallelGC`, `-XX:+UseShenandoahGC`, `-XX:+ExplicitGCInvokesConcurrent`; **38 passed / 25 failed with `-XX:+DisableExplicitGC`** (the WeakHashMap, implicit-Cleaner and ThreadLocal tests; failures like `expected: <1> but was: <0>`).
- Exercise 1, allocation accounting: `byte[1 << 20]` → exactly 1,048,592 bytes (20/20); cached `Long.valueOf(0..127)` → 0 bytes; uncached → 24,000 bytes per 1,000 (5/5) — [L6]. API caveat: returns −1 on virtual threads — [ThreadMXBean.java@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.management/share/classes/com/sun/management/ThreadMXBean.java).
- Exercise 2, WeakHashMap + ReferenceQueue: entry gone (`map.size() == 0`), probe enqueued (`assertSame(probe, q.remove(...))`) 10/10 — [L6].
- Exercise 3, Cleaner: explicit `close()` twice → action ran exactly once (10/10); never-closed owner → action ran after GC (10/10) — [L6]. Cleaner contract (state class must not reference owner) — [Cleaner.java@jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/ref/Cleaner.java).
- Exercise 4, leak + histogram: exactly 10,000 then 0 live `LeakedPaymentEvent` via `DiagnosticCommand.gcClassHistogram`; passes even with `-XX:+DisableExplicitGC` — [L6].
- Exercise 5, ThreadLocal in a pool: value retained until `remove()` (5/5) — [L6].
- Exercise 6, PhantomReference `get()` always null; strongly reachable referent survives 5 GCs — [L6].
- The existing course labs project (`/home/user/jvm-workbench/labs`) already declares `org.openjdk.jol:jol-core:0.17` for the `memory` module and runs tests with JUnit 6.1.3, `-XX:+EnableDynamicAgentLoading -Xshare:off`, a 20 s default timeout — local file `/home/user/jvm-workbench/labs/build.gradle.kts` and `/home/user/jvm-workbench/labs/memory/build.gradle.kts` (read, not modified).

Verified test code (condensed; full file ran as `MemoryLabTest.java`):
```java
static final com.sun.management.ThreadMXBean TMX =
    (com.sun.management.ThreadMXBean) ManagementFactory.getThreadMXBean();

@RepeatedTest(20) void oneMebibyteArrayCostsPayloadPlusHeader() {
    long before = TMX.getCurrentThreadAllocatedBytes();
    byte[] b = new byte[1 << 20];
    long delta = TMX.getCurrentThreadAllocatedBytes() - before;
    assertTrue(delta >= (1 << 20) && delta <= (1 << 20) + 64);   // observed: always 1_048_592
}

@RepeatedTest(10) void weakHashMapEntryVanishesAfterKeyBecomesUnreachable() throws Exception {
    ReferenceQueue<Object> q = new ReferenceQueue<>();
    WeakHashMap<Object, String> map = new WeakHashMap<>();
    Object key = new Object();
    WeakReference<Object> probe = new WeakReference<>(key, q);
    map.put(key, "session-data");
    key = null;
    Reference<?> enqueued = null;
    for (int i = 0; i < 50 && enqueued == null; i++) { System.gc(); enqueued = q.remove(20); }
    assertSame(probe, enqueued);
    assertEquals(0, map.size());            // size() expunges stale entries
}

static final Cleaner CLEANER = Cleaner.create();
static final class NativeHandle implements AutoCloseable {
    private static final class State implements Runnable {      // must not reference NativeHandle
        final AtomicInteger frees; State(AtomicInteger f) { frees = f; }
        public void run() { frees.incrementAndGet(); }
    }
    private final Cleaner.Cleanable cleanable;
    NativeHandle(AtomicInteger frees) { cleanable = CLEANER.register(this, new State(frees)); }
    public void close() { cleanable.clean(); }                   // at most once
}

static long liveInstances(String className) throws Exception {   // forces a full GC
    String histo = (String) ManagementFactory.getPlatformMBeanServer().invoke(
        new ObjectName("com.sun.management:type=DiagnosticCommand"), "gcClassHistogram",
        new Object[] { null }, new String[] { String[].class.getName() });
    for (String line : histo.split("\n")) {
        String[] f = line.trim().split("\\s+");
        if (f.length >= 4 && f[3].equals(className)) return Long.parseLong(f[1]);
    }
    return 0;
}

@RepeatedTest(5) void threadLocalValueOutlivesTheTaskInAPool() throws Exception {
    ExecutorService pool = Executors.newFixedThreadPool(1);
    ThreadLocal<byte[]> buffer = new ThreadLocal<>();
    WeakReference<byte[]> probe = pool.submit(() -> {
        byte[] b = new byte[1 << 20]; buffer.set(b); return new WeakReference<>(b); }).get();
    for (int i = 0; i < 5; i++) System.gc();
    assertNotNull(probe.get());                 // still reachable via the pooled thread
    pool.submit(buffer::remove).get();
    for (int i = 0; i < 50 && probe.get() != null; i++) { System.gc(); Thread.sleep(10); }
    assertNull(probe.get());
    pool.shutdownNow();
}
```

### Inferences
- Put `systemProperty("jol.magicFieldOffset", "true")` on the memory module's test task if JOL is used on records (otherwise JOL throws on JDK 21, [L1]).
- Keep non-deterministic items (escape analysis "0 bytes", GC log contents, pause times) as demos run with `./gradlew :memory:demo`, not as assertions.
- Heap-dump exercise: in-test use `HotSpotDiagnosticMXBean.dumpHeap(path, true)` and assert only that the file exists and is non-empty; the "find the leak" part is a guided MAT walkthrough (not automatable deterministically without a heap-dump parser).
- A forked-JVM test (ProcessBuilder) can deterministically assert the direct-memory OOM message and SoftReference clearing under `-Xmx64m`, both observed in [L5]/[L7].

### Gaps
- Not run through the course's own Gradle build (to avoid touching the repo); run via the JUnit console launcher with the same JUnit version.
- `HotSpotDiagnosticMXBean.dumpHeap` was not exercised from a test (the `jcmd` equivalent was).

---

## Verified URLs

Pages/files actually fetched in this session (all returned HTTP 200):

OpenJDK source at GA tags (raw.githubusercontent.com):
- https://raw.githubusercontent.com/openjdk/jdk/master/make/conf/version-numbers.conf (and the same path at `jdk-21-ga` … `jdk-27-ga`, `jdk-28+20` as tag probes)
- `src/hotspot/share/runtime/globals.hpp` at jdk-21-ga, jdk-24-ga, jdk-25-ga, jdk-26-ga, jdk-27-ga — e.g. https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/hotspot/share/runtime/globals.hpp
- `src/hotspot/share/gc/shared/gc_globals.hpp` at jdk-21-ga, jdk-23-ga, jdk-24-ga, jdk-25-ga, jdk-26-ga, jdk-27-ga — e.g. https://raw.githubusercontent.com/openjdk/jdk/jdk-26-ga/src/hotspot/share/gc/shared/gc_globals.hpp
- `src/hotspot/share/gc/shared/gcConfig.cpp` at 21/24/25/26/27 GA — e.g. https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/hotspot/share/gc/shared/gcConfig.cpp
- `src/hotspot/share/runtime/os.cpp` at 21/24/25/26/27 GA — e.g. https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/runtime/os.cpp
- `src/hotspot/share/runtime/arguments.cpp` at 21/24/25/26/27 GA — e.g. https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/hotspot/share/runtime/arguments.cpp
- `src/hotspot/share/gc/z/z_globals.hpp` at 21/23/24/25/26/27 GA
- `src/hotspot/share/gc/shenandoah/shenandoah_globals.hpp` at 21/24/25/26/27 GA
- `src/hotspot/os/linux/globals_linux.hpp` at 21/24/25/26/27 GA
- `src/hotspot/share/gc/g1/g1_globals.hpp`, `g1Arguments.cpp`, `src/hotspot/share/gc/shared/gcArguments.cpp`, `src/hotspot/share/oops/markWord.hpp` at 21/24/25/26/27 GA
- `src/java.base/share/man/java.md` at 24/25/26/27 GA — e.g. https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/java.base/share/man/java.md
- `src/jdk.jcmd/share/man/jcmd.md` at 24/25/26/27 GA — e.g. https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.jcmd/share/man/jcmd.md
- https://raw.githubusercontent.com/openjdk/jdk/jdk-24-ga/src/hotspot/share/gc/shenandoah/mode/shenandoahGenerationalMode.hpp
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/shenandoah/mode/shenandoahGenerationalMode.hpp
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/oops/compressedKlass.hpp
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/oops/arrayOop.hpp
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/oops/oop.hpp
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/g1/g1HeapRegionBounds.hpp
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/g1/g1HeapRegion.cpp
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/g1/g1CollectedHeap.hpp
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/g1/g1BarrierSet.hpp
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/g1/g1Policy.cpp (fetched, not used)
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/shared/cardTable.hpp
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/shared/threadLocalAllocBuffer.hpp
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/shared/threadLocalAllocBuffer.inline.hpp
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/shared/gcCause.cpp
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/gc/z/zAddress.hpp
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/opto/c2_globals.hpp
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/ref/package-info.java
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/ref/SoftReference.java
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/ref/PhantomReference.java
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/ref/Cleaner.java
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Object.java
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/Runtime.java
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/System.java
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/util/WeakHashMap.java
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/foreign/Arena.java
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/jdk/internal/foreign/SegmentFactories.java
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/jdk/internal/misc/VM.java
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.management/share/classes/com/sun/management/ThreadMXBean.java

JOL and Maven Central:
- https://raw.githubusercontent.com/openjdk/jol/master/README.md
- https://maven-central.storage-download.googleapis.com/maven2/org/openjdk/jol/jol-cli/maven-metadata.xml
- https://maven-central.storage-download.googleapis.com/maven2/org/openjdk/jol/jol-cli/0.17/jol-cli-0.17-full.jar
- https://maven-central.storage-download.googleapis.com/maven2/org/openjdk/jol/jol-core/0.17/jol-core-0.17.jar
- https://maven-central.storage-download.googleapis.com/maven2/org/junit/platform/junit-platform-console-standalone/maven-metadata.xml
- https://maven-central.storage-download.googleapis.com/maven2/org/junit/platform/junit-platform-console-standalone/6.1.3/junit-platform-console-standalone-6.1.3.jar

Eclipse MAT help sources (official MAT repository):
- https://raw.githubusercontent.com/eclipse-mat/mat/master/plugins/org.eclipse.mat.ui.help/concepts/dominatortree.html
- https://raw.githubusercontent.com/eclipse-mat/mat/master/plugins/org.eclipse.mat.ui.help/concepts/shallowretainedheap.html
- https://raw.githubusercontent.com/eclipse-mat/mat/master/plugins/org.eclipse.mat.ui.help/concepts/gcroots.html
- https://raw.githubusercontent.com/eclipse-mat/mat/master/plugins/org.eclipse.mat.ui.help/gettingstarted/basictutorial.html
- (also fetched, not used: `concepts/reachability.html`, `tasks/analyzingjavacollectionusage.html`)

Known only from web-search result lists (NOT fetched; treat as unverified pointers): https://openjdk.org/jeps/523, https://openjdk.org/jeps/519, https://openjdk.org/jeps/521, https://openjdk.org/jeps/522, https://openjdk.org/jeps/8361187 (JEP draft "Compact Object Headers by Default", reported as JEP 534), https://inside.java/2026/05/26/jep523-target-jdk27/, https://openjdk.org/projects/jdk/27.

Unreachable from this machine (tried): openjdk.org (JEPs), docs.oracle.com (GC tuning guide), shipilev.net, inside.java, dev.java, wiki/bugs/mail/cr.openjdk.org, help.eclipse.org, github.com HTML and api.github.com.

---

## Teaching notes

### Suggested 7-lesson arc (each with its anchor demo)
1. **Where objects live and what they cost** — NMT summary of a tiny app (heap 216 MB committed out of 390 MB total) + JOL tables (`Payment` 40 → 48 → 32 bytes across modes).
2. **Allocation is cheap; escaping is not free** — TLAB bump-pointer code (5 lines of HotSpot), `getCurrentThreadAllocatedBytes` = 1,048,592 for 1 MiB, escape analysis 32,000,000 → 0 bytes.
3. **Reachability** — Weak/Soft/Phantom ladder, WeakHashMap vanishing entry, Cleaner vs `finalize()` (`finalized=1000` vs `0` with `--finalization=disabled`).
4. **How G1 works** — regions/humongous, young → concurrent start → remark → cleanup → mixed, read the verbatim log sequence from Q7, spot `(Evacuation Failure)` and `Pause Full`.
5. **Low-pause collectors and choosing one** — ZGC log: 0.02 ms pauses vs 52 ms cycle; when *not* to use ZGC (CPU-limited pods); JDK 27 default change.
6. **Containers and native memory** — `MaxRAMPercentage` maths, why `-Xmx = limit` OOM-kills, `MaxDirectMemorySize` default = heap, FFM arenas count against it.
7. **Leak hunting** — histogram → heap dump → MAT dominator tree; patterns: unbounded idempotency cache, ThreadLocal on pooled (Vert.x/worker) threads, listeners, classloaders.

### Analogies
- **TLAB** = each cashier has their own cash drawer (no lock); refilling the drawer from the vault is the slow path. Humongous objects are pallets that go straight to the warehouse floor.
- **Mark word** = a sticky note on every object (hash, GC age, lock state); compact headers write the class name on the same sticky note instead of a second one.
- **Compressed oops** = 4-byte "seat numbers" in a stadium of 8-byte-aligned seats: 2^32 seats × 8 bytes = 32 GB; bigger stadium, back to full addresses.
- **Card table / remembered set** = the old generation keeps a ledger of "pages that point at young objects", so a young collection reads the ledger instead of the whole archive (512-byte cards in G1's log).
- **G1 mixed GC** = cleaning the dirtiest rooms first under a time budget (pause goal 200 ms).
- **ZGC** = moving house while people keep living in it; load barriers are the forwarding address checks at every door.
- **Weak vs soft** = weak: "forget me when nobody else remembers"; soft: "keep me unless you're running out of room".
- **Dominator tree / retained size** = "if I cut this one rope, how much falls?"

### Misconceptions to address explicitly (evidence in Q10)
`System.gc()` frees memory now · bigger heap is always better · ZGC is always best · `-Xmx` caps process memory · weak references for caches · `Integer` is 4 bytes · every `new` allocates · `finalize()` is a destructor · compact headers save exactly 4 bytes per object · "the JVM always uses G1" (only from 27) · a heap dump explains an OOM-kill.

### Demo ideas (all run on JDK 21 unless noted)
- `java -XX:+PrintFlagsFinal -version | grep -E 'Use(Serial|G1|Parallel|Z|Shenandoah)GC |MaxHeapSize|MaxRAMPercentage'` with and without `-XX:ActiveProcessorCount=1` → Serial appears (JDK ≤ 26 behaviour; on 27 G1 stays).
- `java -XshowSettings:system -version` inside the student's container to show the detected limit.
- JOL `internals` on a payments DTO in default / `-XX:-UseCompressedOops` / `-Xmx40g`; `jol-cli estimates` to preview compact headers.
- Same `GcWorkload` under `-Xlog:gc` with G1, ZGC, Serial: compare line shapes; then shrink the heap until `(Evacuation Failure)` and `Pause Full (G1 Compaction Pause)` appear.
- `-Xlog:safepoint` to separate time-to-safepoint from pause work.
- Epsilon `-XX:+UnlockExperimentalVMOptions -XX:+UseEpsilonGC -Xmx128m` as an "allocation budget" test that dies with `Terminating due to java.lang.OutOfMemoryError: Java heap space`.
- NMT: `-XX:NativeMemoryTracking=summary` then `jcmd <pid> VM.native_memory summary scale=MB`; add a 64 MB direct buffer and watch `Other` grow by 64 MB.
- `-XX:MaxDirectMemorySize=32m` + 64 MB `allocateDirect` → `Cannot reserve 67108864 bytes of direct buffer memory (allocated: 0, limit: 33554432)`.
- `-Xmx64m -XX:+HeapDumpOnOutOfMemoryError` on the leaky idempotency cache → `Heap dump file created [70967188 bytes in 0.048 secs]`, open in MAT, dominator tree.

### Lab exercises with expected outcomes (all observed in [L6]/[L7] unless marked)
| # | Exercise | Deterministic assertion | Observed |
|---|---|---|---|
| 1 | Measure `new byte[1 << 20]` with `getCurrentThreadAllocatedBytes` | `1 MiB ≤ delta ≤ 1 MiB + 64` | exactly 1,048,592, 20/20 |
| 2 | Long cache: `Long.valueOf(i % 128)` vs `Long.valueOf(1000 + i)` ×1000 | `cached == 0`, `uncached ≥ 16,000` | 0 and 24,000, 5/5 |
| 3 | WeakHashMap entry vanishes; probe enqueued on `ReferenceQueue` | `assertSame(probe, q.remove)`; `map.size() == 0` | 10/10, all collectors |
| 4 | PhantomReference.get() | `assertNull` | pass |
| 5 | Cleaner explicit close twice | action count `== 1` | 10/10 |
| 6 | Cleaner implicit (owner dropped) | count `== 1` after bounded GC loop | 10/10 |
| 7 | Static-list leak found by class histogram | `== 10_000`, after `clear()` `== 0` | pass, also with DisableExplicitGC |
| 8 | ThreadLocal on pooled thread | value retained until `remove()` | 5/5 |
| 9 | SoftReference under `-Xmx64m` (forked JVM) | `soft.get() == null` after allocating 40 MB more | `soft after ...: false` |
| 10 | Direct-memory limit (forked JVM) | stderr contains `Cannot reserve 67108864 bytes of direct buffer memory` | observed |
| 11 | Escape analysis (demo, not CI) | — | 0 bytes/round after warm-up vs 32,000,000 with `-XX:-DoEscapeAnalysis` |
| 12 | Finalization switch (demo) | — | `finalized=1000` vs `0` |

Lab-harness rules learned the hard way:
- Never add `-XX:+DisableExplicitGC` to the test JVM (25 of 63 executions failed with it).
- Bound every GC wait loop (e.g. 50 × `System.gc()` + 10–20 ms) so a misbehaving test fails within the 20 s JUnit timeout instead of hanging.
- Cleaner state classes must be `static` and must not capture the owner (otherwise the action never runs).
- Run allocation-measurement tests on platform threads (virtual threads return −1).
- JOL on records needs `-Djol.magicFieldOffset=true` on JDK 21.
