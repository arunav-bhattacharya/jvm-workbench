# JVM Startup Time and Memory Footprint: CDS, Project Leyden AOT Cache, GraalVM Native Image, Quarkus, CRaC (state as of 7 November 2026)

**Read this first: how these notes were verified.**
- **Network:** openjdk.org (DNS block), docs.oracle.com, graalvm.org, quarkus.io, inside.java, mail/bugs.openjdk.org, docs.azul.com, bell-sw.com, docs.aws.amazon.com, foojay.io, github.com HTML pages and api.github.com were all **blocked**. Reachable: raw.githubusercontent.com, `git clone` of public GitHub repos, www.oracle.com (release notes), repo1.maven.org.
- **So the primary sources here are the source trees themselves:**
  - the `java` man-page source (`src/java.base/share/man/java.md`);
  - the HotSpot flag definitions (`src/hotspot/share/cds/cds_globals.hpp`) at the tags `jdk-21-ga`, `jdk-24-ga`, `jdk-25-ga`, `jdk-26-ga`, `jdk-27-ga` and `master`;
  - the full openjdk/jdk, jdk25u and jdk26u **git histories**, used for JEP integration commits and the tag each first appears in;
  - Oracle's JDK 24–27 release-note pages;
  - the GraalVM docs and JSON schemas (oracle/graal master, commit d1b9545, 2026-11-07);
  - the Quarkus docs (main, commit ff19f58b, 2026-11-06, plus tag **3.40.1.1** = latest 3.x);
  - the CRaC docs and the org.crac source.
- **JEP pages were not opened.** Wording from JEPs comes from web-search summaries and is tagged **[S]**.
- **Tags:**
  - **[V]** read in the primary source file or git history this session;
  - **[L]** measured or observed locally this session;
  - **[S]** search-summary only (page not opened);
  - **[TK]** training knowledge, not re-checked: verify before publishing.
- **JDKs used locally:**
  - Ubuntu OpenJDK **21.0.12.1+1** (installed);
  - Eclipse **Temurin 25+36** (25 GA). A tarball found in the session scratchpad; its SHA-256 `ee04de95…90e8` matched Adoptium's published checksum file, so the Leyden flags were run for real, not only documented.
  - No JDK 24, 26 or 27 binary was available.
- **Machine caveat for every number:**
  - 4 vCPU Firecracker VM, Linux 6.18, 16 GB RAM, shared with other agents (load average 3–20 during runs);
  - wall times are inflated and noisy, so configurations were interleaved round-robin and CPU time (user+sys) is reported too;
  - compare rows *within* a table, never against numbers from other machines.
- JDK timeline: 21 LTS (Sep 2023), 24 (Mar 2025), **25 LTS (Sep 2025)**, 26 (Mar 2026), **27 GA (Sep 2026)**, 28 in development (master). Quarkus: latest 3.x is **3.40.1.1** (2026-10-19). Quarkus main is already **4.0.0.Beta3** (2026-11-04), so watch for docs that describe 4.0 only.

---

## Q1. Why does a JVM start slowly and use memory, and how do you measure it?

### Takeaway
Startup cost is mostly work the JVM repeats on every launch:
- reading, parsing and verifying classes (about 1,500 classes even for a 300-class app);
- running static initializers;
- spinning lambdas and method handles;
- interpreting until the JIT has profiles;
- in frameworks, scanning and reflection.

Footprint (RSS) is much more than the heap: metaspace and class space, code cache, GC structures, thread stacks, and mapped archives. Measure with:
- `-Xlog:class+load` (and its `source:` field);
- `-Xlog:startuptime` (JVM creation phases only);
- time-to-first-request from outside the process;
- RSS/PSS from `/proc` or `ps`;
- Native Memory Tracking for the JVM's own accounting (committed is not resident).

### Cited Findings
- **[L] Class counts for a 300-class app.** A generated app (300 classes, each with a lambda, plus streams, regex, `java.time` and `String.format`) loads **1,537 classes with `-Xshare:off` on JDK 21**:
  - 301 from app.jar;
  - 911 from the `jrt:/` modules image;
  - 325 "other" (hidden classes: lambda proxies and LambdaForms).

  With the default CDS archive: 1,507 loaded, **875 from "shared objects file"**. JDK 25: 1,632 loaded with `-Xshare:off`; 1,620 with default CDS, 990 of them shared. — local run (see Q4)
- **[V] Reading `-Xlog:class+load` output.** The man page shows that an archived class logs as `[info][class,load] test.Hello source: shared objects file`. — [JDK 25 java.md](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/man/java.md)
- **[L] Other `source:` values seen.** `file:/…/app.jar` (classpath JAR), `jrt:/java.base` (modules image), and, for hidden classes, the defining class name (e.g. `source: demo.Main`, `__JVM_LookupDefineClass__`). `-verbose:class` is an alias of `-Xlog:class+load` (1,518 lines in one JDK 21 run).
- **[L] `-Xlog:startuptime` exists on JDK 21 and 25.** It prints JVM-creation phases only, e.g. on JDK 21: `Genesis, 0.0120722 secs` … `Initialize java.lang classes, 0.0068201 secs` … `Initialize module system, 0.0019588 secs` … `Create VM, 0.0536765 secs`. JDK 25: `Create VM, 0.0283517 secs`.
  - It says nothing about application or framework init, so measure time-to-first-request externally.
  - `-Xlog:init` printed nothing at info level for this app on either JDK.
- **[L] NMT: committed is not resident.** NMT summary at exit (`-XX:NativeMemoryTracking=summary -XX:+UnlockDiagnosticVMOptions -XX:+PrintNMTStatistics`, JDK 21, same app) reported:
  - Total committed ≈ 288 MiB, of which Java Heap ≈ 216 MiB, GC ≈ 45 MiB, Shared class space ≈ 12.6 MiB, Code ≈ 7.5 MiB, Metaspace ≈ 1.5 MiB, Thread ≈ 0.7 MiB;
  - while the process's **max RSS was ≈ 50 MiB**. Committed-but-untouched heap pages are not resident.
  - For a live process: `jcmd <pid> VM.native_memory summary`, which prints "Native memory tracking is not enabled" unless the JVM was started with `-XX:NativeMemoryTracking`. [L]
- **[L] RSS breakdown for a JDK `HttpServer` app after the first request** (`/proc/<pid>/status`, `smaps_rollup`):

  | | VmRSS | RssAnon | RssFile | Pss |
  |---|---|---|---|---|
  | JDK 21 default CDS | 50.6 MiB | 26.6 MiB | 24.0 MiB | 33.1 MiB |
  | JDK 25 default CDS | 56.6 MiB | 31.5 MiB | 25.2 MiB | 39.8 MiB |
- **[V] Quarkus measures footprint as RSS of the whole process.** It warns: "**DO NOT use docker stat or anything derived from it** (e.g. ctop). This approach only measures a subset of the in-use resident pages". It recommends `ps -e -o pid,rss,args` or `docker top <id> -o pid,rss,args`, and notes containers are killed "based on its full RSS memory usage". — [Quarkus performance-measure.adoc](https://github.com/quarkusio/quarkus/blob/main/docs/src/main/asciidoc/performance-measure.adoc)
- **[V] Quarkus startup log line** has the form `started in 0.968s. Listening on: http://localhost:8080`. — [Quarkus getting-started.adoc](https://github.com/quarkusio/quarkus/blob/main/docs/src/main/asciidoc/getting-started.adoc)
- **[V] Build-time principle.** Quarkus's extension guide: "As much as possible favor doing work at build time (deployment part of the extension) as opposed to let the framework do work at startup time (runtime)". Also: "classes at build time and generating code that registers them at static-init time instead of relying on reflection". — [Quarkus writing-extensions.adoc](https://github.com/quarkusio/quarkus/blob/main/docs/src/main/asciidoc/writing-extensions.adoc)
- **[V] Class initialization cost** (GraalVM docs): "the simple 'Hello, World!' application requires more than 300 classes to be initialized". Without build-time initialization, per-access init checks "can reduce performance by more than twofold" in AOT-compiled code. — [GraalVM ClassInitialization.md](https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/ClassInitialization.md)
- **[V] Why JIT warm-up exists** (GraalVM PGO doc): HotSpot "keeps track of how many times each branch of an `if` statement is executed… This information, called a 'profile', is passed to a tier-2 JIT compiler". Creating a profile "adds execution time and memory usage overheads… This causes warmup issues". — [GraalVM PGO.md](https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/PGO.md)

### Background facts (training knowledge) [TK]
- **Class lifecycle (JVMS ch. 5).**
  - Loading: find bytes, parse, create the `InstanceKlass` in metaspace.
  - Linking: *verification* (type-checking bytecode with StackMapTable; may itself load other classes, as seen in [L] Q10), *preparation* (default static values), *resolution* (lazy, of constant-pool entries).
  - *Initialization*: run `<clinit>` on first active use (new, static field get/put, static method, reflection, subclass init).
  - CDS/AOT removes parse and verify cost, and with AOT linking some resolution cost. It does **not** run `<clinit>` for app classes (see Q8, verified [L]).
- **Execution tiers.** HotSpot tiered compilation: interpreter (tier 0), then C1 with profiling (tiers 2–3), then C2 (tier 4). Early requests run in the interpreter or C1 code, so time-to-first-request and time-to-peak differ.
- **RSS components:** Java heap (touched pages only); metaspace and compressed class space; code cache; GC data structures (card tables, remembered sets); thread stacks (touched pages); symbol and string tables; CDS/AOT mapped regions; direct/NIO buffers; malloc arenas (glibc); JIT compiler arenas.
- **Container heap defaults.** In containers the default max heap is `MaxRAMPercentage=25` of the container limit and the initial heap is `InitialRAMPercentage=1.5625`. Consistent with [L]: NMT reported 3,420 MiB reserved heap and ≈ 216 MiB committed at start on this VM.
- **Framework startup:** classpath/annotation scanning, reflection-driven DI, proxies generated at runtime, config parsing. Quarkus moves these to build time (Jandex index, generated bytecode). Spring AOT does a similar move with a different design.

### Inferences
- A lesson can show the whole problem in one command: `java -Xlog:class+load -cp app.jar Main | awk -F'source: ' '{print $2}' | sort | uniq -c`. The `source:` column turns "startup = class loading" into a visible histogram that changes as CDS or AOT is applied.
- Teach three different clocks: JVM creation (`-Xlog:startuptime`), the framework's "started in" line, and external time-to-first-request. Only the last is what an orchestrator or load balancer sees.

### Gaps
- Exact JDK 25 numbers for `-Xlog:startuptime` and NMT categories on a real Quarkus service were not measured (no Quarkus app was built here; Maven/Quarkus artifacts were not downloaded).

---

## Q2. Class Data Sharing: default CDS, AppCDS, static vs dynamic archives, AutoCreateSharedArchive (flags, defaults, versions)

### Takeaway
CDS memory-maps pre-parsed class metadata from a `.jsa` file.
- Every JDK since 12 ships a default archive of about 1,300 JDK classes (on by default, `-Xshare:auto`).
- AppCDS adds your classpath classes: static via `-XX:DumpLoadedClassList` + `-Xshare:dump`, or dynamic via `-XX:ArchiveClassesAtExit` (JDK 13).
- `-XX:+AutoCreateSharedArchive` (JDK 19) makes the dynamic archive self-maintaining.

On JDK 21 locally, AppCDS cut CPU time for the 300-class app by about half. From JDK 24 on, the JDK documentation steers you to the AOT cache for "the full set of CDS/AOT optimizations".

### Cited Findings
- **[V] What AppCDS gives.** It "stores classes used by your applications in an archive file… loaded very quickly… can improve the start-up time… [and] can reduce the runtime memory footprint by sharing parts of these classes across multiple processes". Archived classes are "about 2 to 5 times larger than classes stored in JAR files", so archive only what's used. — [JDK 25 java.md](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/man/java.md)
- **[V] Default archive.** "By default, in most JDK distributions, unless `-Xshare:off` is specified, the JVM starts up with a default CDS archive… `JAVA_HOME/lib/server/classes.jsa`… about 1300 core library classes". — same source
- **[L] Default archives shipped.**
  - Ubuntu JDK 21: `classes.jsa` (14.6 MB) and `classes_nocoops.jsa`.
  - Temurin 25: `classes.jsa` (15.6 MB), `classes_coh.jsa`, `classes_nocoops.jsa`, `classes_nocoops_coh.jsa`.
- **[V] The `_coh` archives.** These are compact-object-header variants. The JDK 25 release notes say two additional CDS archives "called classes_coh.jsa and…" exist to support compact object headers. JDK 27 release notes: compact object headers are enabled by default, and "Alternate CDS archives are provided if the feature is turned off". — [JDK 25 release notes](https://www.oracle.com/java/technologies/javase/25-relnote-issues.html), [JDK 27 release notes](https://www.oracle.com/java/technologies/javase/27-relnote-issues.html)
- **[V] `-XX:SharedArchiveFile` syntax.** General form `-XX:SharedArchiveFile=<static_archive>:<dynamic_archive>` (`;` on Windows). The dynamic archive "records the location of the `<static_archive>`", so `-XX:SharedArchiveFile=<dynamic_archive>` alone works. The JVM "can use up to two archives". — [JDK 25 java.md](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/man/java.md)
- **[V] Static archive, exact sequence** (man page, JDK 21–27):
  1. `java -Xshare:off -XX:DumpLoadedClassList=hello.classlist -cp hello.jar test.Hello`
  2. `java -Xshare:dump -XX:SharedArchiveFile=hello.jsa -XX:SharedClassListFile=hello.classlist -cp hello.jar`
  3. `java -XX:SharedArchiveFile=hello.jsa -cp hello.jar test.Hello`

  "The classpath specified by the `-cp` parameter must contain only JAR files." `-Xshare:dump` runs "in interpreter-only mode (as if the `-Xint` option were specified)… to generate deterministic output… bit-for-bit"; add `-Xmixed` to speed up large dumps when determinism doesn't matter. — same source
- **[V] Dynamic archive.** `java -XX:ArchiveClassesAtExit=hello.jsa -cp hello.jar Hello`, then `java -XX:SharedArchiveFile=hello.jsa -cp hello.jar Hello`. It "usually use[s] less disk space" and needs "one fewer step". The man page also says the dynamic archive "supports fewer optimizations than available for the static CDS archive. If the full set of CDS/AOT optimizations are desired, consider using the AOT cache". — same source
- **[V] jcmd route.** `jcmd <pid> VM.cds static_dump my_static_archive.jsa` / `jcmd <pid> VM.cds dynamic_dump my_dynamic_archive.jsa`. The dynamic dump requires the target to have been started with `-XX:+RecordDynamicDumpInfo`. Inject options without editing scripts: `env JAVA_TOOL_OPTIONS=-XX:SharedArchiveFile=… bash app_start.sh`. — same source
- **[V] `-XX:+AutoCreateSharedArchive` (JDK 19+).** `java -XX:+AutoCreateSharedArchive -XX:SharedArchiveFile=hello.jsa -cp hello.jar Hello`.
  - If the file "exists and was created by the same version of the JDK, then it will be loaded as a dynamic archive".
  - "At VM exit, if the specified archive file does not exist, it will be created. If it exists but was created with a different (but post JDK 19) version… it will be replaced."
  - Archives from before JDK 19 are ignored and not replaced.

  — same source. The integration commit is `8261455: Automatically generate the CDS archive if necessary` (2022-01-13), first tag jdk-19+6. — [openjdk/jdk commit 1228b2f](https://github.com/openjdk/jdk/commit/1228b2f1f8737a363ab6a7065b24e9f972441b27) (read via git clone)
- **[V] Classpath and module-path restrictions** (man page): no non-empty directories on the class path; only modular JARs on `--module-path`. "The class path used at archive creation time must be the same as (or a prefix of) the class path used at run time". "The CDS archive cannot be loaded if any JAR files in the class path or module path are modified after the archive is generated." `--upgrade-module-path`, `--patch-module` and `--limit-modules` disable CDS entirely. — same source
- **[V] Module options must match.** "`--module-path`, `--module`, `--add-modules`, and `--enable-native-access`… should be identical when creating and using the CDS archive". If `AOTClassLinking` was on at creation, a mismatch means the archive "cannot be used" ("CDS archive has aot-linked classes…"). Diagnose with `-Xlog:aot`. — same source
- **[V] Version history from git** (openjdk/jdk history, read via clone):
  - Default CDS archives commit `8202951: Implementation of JEP 341` dated 2018-10-05 → JDK 12.
  - `8207812: Implement Dynamic CDS Archive` (JEP 350) dated 2019-05-17 → JDK 13.
  - The tags for these pre-2020 commits were not resolvable in my clone, so the release mapping is from dates and is consistent with JEPs 341 (JDK 12) and 350 (JDK 13). [V for commits; JDK numbers TK-consistent]
  - AppCDS itself became open-source and product in JDK 10 via JEP 310 [TK; no commit found by grep].
- **[V] Flag defaults in `cds_globals.hpp`** (identical in 21, 24, 25, 26, 27 unless noted), all `product`:
  - `AutoCreateSharedArchive=false`, `RecordDynamicDumpInfo=false`, `ArchiveClassesAtExit=nullptr`, `SharedArchiveFile=nullptr`, `DumpLoadedClassList=nullptr`, `SharedClassListFile=nullptr`, `PrintSharedArchiveAndExit=false`, `VerifySharedSpaces=false`;
  - diagnostic `ArchiveRelocationMode=1` "(1) always map at alternative address (default)";
  - diagnostic `AllowArchivingWithJavaAgent` exists in 21–25 and is **gone in 26**.

  — [cds_globals.hpp @ jdk-21-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-21-ga/src/hotspot/share/cds/cds_globals.hpp), [@ jdk-26-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-26-ga/src/hotspot/share/cds/cds_globals.hpp)
- **[V] Relocation is randomized.** `8323556: CDS archive space addresses should be randomized with ArchiveRelocationMode=1` landed in January 2024 (jdk-23+7 on master, and a same-subject commit on the JDK 22 line). — [commit 437342b](https://github.com/openjdk/jdk/commit/437342b93e9e66340ac57bd1c6fdc948b3302db0)
- **[L] Consequence for cross-process sharing.** In a running JDK 25 process, the AOT cache mapping was `rw-p` (private, writable): Rss 14,376 kB, of which **Private_Dirty 11,480 kB** and Shared_Clean 0 kB. The log said "ArchiveRelocationMode == 1: always map archive(s) at an alternative address".
- **[L] JDK 21 measurements**, 300-class app, 30 interleaved rounds, medians:

  | config | CPU | wall | archive size |
  |---|---|---|---|
  | default CDS | 349 ms | 333 ms | — |
  | dynamic AppCDS | 171 ms | 196 ms | 1.47 MB |
  | static AppCDS | 178 ms | 191 ms | 12.9 MB |
  | AutoCreateSharedArchive | 171 ms | 210 ms | — |

  Details in Q4.
- **[L] AppCDS also archives lambda proxies.** The JDK 21 classlist contained `@lambda-proxy demo/C0 applyAsInt …` lines. With AppCDS the "other/hidden" class count fell from 316 to 3.
- **[L] JDK 21 correctly rejects a changed JAR:** "[warning][cds] h21.jar timestamp has changed." / "h21.jar size has changed." / "Unable to use shared archive. The top archive failed to load". The program then ran the **new** code ("version TWO").

### Inferences
- Because of `ArchiveRelocationMode=1` (default in 21+), most of a mapped archive becomes private dirty memory after relocation. The "sharing across processes" footprint benefit in the man page is much smaller than older blog posts suggest; on modern JDKs, sell CDS/AOT for **startup**, not cross-container RAM savings. Only one JDK 25 AOT mapping was inspected; the default `classes.jsa` mapping in JDK 21 was not.
- For JDK 21 services, the lowest-friction option is `-XX:+AutoCreateSharedArchive -XX:SharedArchiveFile=/some/writable/path.jsa`. But in immutable containers the archive should be created at image build time (dynamic or static), because a read-only filesystem or an ephemeral pod loses the auto-created file.

### Gaps
- Whether `classes.jsa` regions stay `r--p`/shared in JDK 21 default mode was not inspected.
- JEP 310 and 341 pages were not opened; JDK-number attribution for JEPs 310, 341 and 350 rests on commit dates and training knowledge.

---

## Q3. Project Leyden as delivered: JEPs, JDK versions, flags, defaults, and the exact JDK 25 AOT-cache sequence

### Takeaway
Leyden has shipped, in order:
- **JEP 483** (JDK 24): AOT class loading and linking, plus the AOT cache and the flags `-XX:AOTMode/-XX:AOTConfiguration/-XX:AOTCache`.
- **JEP 514** (JDK 25): one-step `-XX:AOTCacheOutput`, with `JDK_AOT_VM_OPTIONS`.
- **JEP 515** (JDK 25): method profiles in the cache.
- **JEP 516** (JDK 26): GC-agnostic "streamable" heap objects, so the full cache works with ZGC.

**JDK 27 shipped no Leyden JEP.** It added `-XX:AOTMode=required` as the preferred spelling of `on` (JDK-8374348), and made compact object headers (JEP 534) and G1 everywhere (JEP 523) defaults. **JEP 544 (AOT code compilation) and JEP 545 (faster startup and warmup with ZGC) are integrated in master for JDK 28, not in any GA release.**

The JDK 25 sequence is either:
- **one step:** `java -XX:AOTCacheOutput=app.aot -cp app.jar Main` (training plus assembly), then `java -XX:AOTCache=app.aot -cp app.jar Main`; or
- **two steps:** `-XX:AOTMode=record -XX:AOTConfiguration=app.aotconf`, then `-XX:AOTMode=create -XX:AOTConfiguration=app.aotconf -XX:AOTCache=app.aot`, then `-XX:AOTCache=app.aot`.

### Cited Findings
**JEP status by JDK version (from git integration commits and the first tag containing them):**

| JDK | Startup/footprint-relevant JEPs and changes | Evidence |
|---|---|---|
| 21 (LTS) | No Leyden. CDS: default archive, AppCDS, dynamic archive, AutoCreateSharedArchive (19). | [V] `cds_globals.hpp@jdk-21-ga` |
| 22 | (G1 region pinning JEP 423; not startup) | [V] git |
| 23 | ZGC generational by default (JEP 474) | [V] git |
| **24** | **JEP 483 AOT Class Loading & Linking** (`8331497`, 2024-11-15, first tag jdk-24+25); JEP 450 Compact Object Headers (experimental); JEP 490 removes non-generational ZGC | [V] [commit 41a2d49](https://github.com/openjdk/jdk/commit/41a2d49f0a1ed298b8ab023ce634335464454fe7); [JDK 24 release notes](https://www.oracle.com/java/technologies/javase/24-relnote-issues.html) |
| **25 (LTS)** | **JEP 514 AOT Command-Line Ergonomics** (`8355798`, 2025-05-28); **JEP 515 AOT Method Profiling** (`8355003`, 2025-05-28); JEP 519 Compact Object Headers → product (off by default) | [V] [commit dede353](https://github.com/openjdk/jdk/commit/dede3532f7238d527fb89be41f1b8050bde02ee3), [commit e3f85c9](https://github.com/openjdk/jdk/commit/e3f85c961b4c1e5e01aedf3a0f4e1b0e6ff457fd); both in `git log jdk-24-ga..jdk-25-ga`; [JDK 25 release notes](https://www.oracle.com/java/technologies/javase/25-relnote-issues.html) |
| **26** | **JEP 516 AOT Object Caching with Any GC** (`8365932`, 2025-11-07, jdk-26+24); `jcmd <pid> AOT.end_recording` diagnostic command (`8370203`, jdk-26+26); JEP 522 G1 throughput | [V] [commit c865644](https://github.com/openjdk/jdk/commit/c8656449c28581ae9c3d815105e338e42253bb43), [commit 65f1ad6](https://github.com/openjdk/jdk/commit/65f1ad616977428fcb498479132086777dc929cb); [JDK 26 release notes](https://www.oracle.com/java/technologies/javase/26-relnote-issues.html) (JEPs: 500, 504, 516, 517, 522, 524, 525, 526, 529, 530) |
| **27** | **No Leyden JEP.** `-XX:AOTMode=required` alias for `on` (`8374348`, jdk-27+23); JEP 534 Compact Object Headers by Default; JEP 523 G1 default in all environments; JDK-8377932 stale-JAR fix (see Q4) | [V] [commit 42d6307](https://github.com/openjdk/jdk/commit/42d6307030543948317d767d6085840f1b0a2ea8), [commit 630b831](https://github.com/openjdk/jdk/commit/630b8319b9f664ccc2d987ac3377842afdafd03c), [commit 8663770](https://github.com/openjdk/jdk/commit/86637704fd01493ddb57e455dbd1e35e4798237d); [JDK 27 release notes](https://www.oracle.com/java/technologies/javase/27-relnote-issues.html) (JEPs: 523, 527, 531–534, 536–538) |
| 28 (in development) | **JEP 544 Ahead-of-Time Code Compilation** (`8380476`, 2026-10-08, jdk-28+20); **JEP 545 Faster Startup and Warmup with ZGC** and JEP 546 Adaptive Heap Sizing for ZGC (`8380289`, 2026-10-21, jdk-28+21) | [V] [commit f6fa653](https://github.com/openjdk/jdk/commit/f6fa65381d0c32e22120159415f8c472e990cdc7), [commit d544fca](https://github.com/openjdk/jdk/commit/d544fca92aab371187df86fbbf3b473abdab25b2); not in `jdk-27-ga` |

**Exact man-page text for the AOT cache (JDK 25; JDK 26 identical):** [V] — [JDK 25 java.md](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/man/java.md)
- "The Ahead-of-Time Cache (AOT cache) is a container introduced in JDK 24 for storing artifacts produced by AOT optimizations."
- "An AOT cache is specific to a combination of… A particular application (as expressed by `-classpath`, `-jar`, or `--module-path`.) A particular JDK release. A particular OS and CPU architecture. If any of the above changes, you must recreate the AOT cache."
- Three phases: "**Training:** We execute the application with a representative work-load… saved in an *AOT Configuration* file. **Assembly:** We use the AOT Configuration file to produce an AOT cache. **Production:** We execute the application with the AOT cache".
- `-XX:AOTCache=`*cachefile*: "standard extension… `.aot`. This option cannot be used together with `-XX:AOTCacheOutput`." It is read in modes `on`/`auto`, ignored by `off`, and written by `create` (where it equals `-XX:AOTCacheOutput`).
- `-XX:AOTCacheOutput=`*cachefile*: compatible with `record`, `create`, `auto`.
- `-XX:AOTConfiguration=`*configfile*: "standard extension… `.aotconfig`". Read by `create`, written by the other modes. "If the AOT mode is `auto`, then `AOTCacheOutput` must also be present."
- `-XX:AOTMode` values in JDK 25/26: `auto` (default), `off`, `record`, `create`, `on`.
  - **auto:** "If `-XX:AOTCacheOutput=`… is specified, the AOT mode is changed to `record` (a training run, with a subsequent `create` operation). Otherwise, if an AOT cache can be loaded, the AOT mode is changed to `on`… Otherwise… `off`".
  - **record:** if no `AOTConfiguration` is given, a temp name such as `AOTCacheOutput+".config"` is used. "If `-XX:AOTCacheOutput=`… is specified, a second JVM process is launched to perform the Assembly phase". "Extra JVM options can be passed to the second JVM process using the environment variable `JDK_AOT_VM_OPTIONS`" (same format as `JAVA_TOOL_OPTIONS`).
  - **create:** "the application itself is not executed in this phase."
  - **on:** a failed load means "print an error message and exit immediately… only as a 'fail-fast' debugging aid". In `auto`, "the JVM will continue execution without using the AOT cache. This is the recommended mode for production environments".
  - Failure reasons listed: incompatible app, JDK or OS/CPU; missing file; "Incompatible JVM options… (for example, certain JVMTI options)". It points to JEP 483 "Consistency of training and subsequent runs".
- `-XX:+AOTClassLinking`: "ahead-of-time resolution of invokedynamic instructions"… "When `-XX:AOTMode` *is used*… `AOTClassLinking` is automatically enabled… When `-XX:AOTMode` *is not used*… disabled by default to provide full compatibility with traditional CDS options such as `-Xshare:dump`."
- `%p` and `%t` in file names are replaced by PID and start timestamp, e.g. `java -XX:AOTConfiguration=foo%p.aotconfig -XX:AOTCacheOutput=foo%p.aot -cp foo.jar Foo`.
- **Doc lag:** the JDK 25 man page still says "The AOT cache currently contains Java classes and heap objects. In future JDK releases… execution profiles and compiled methods", even though JEP 515 (profiles) shipped in 25. The master (JDK 28) page says it "contains Java classes, heap objects, execution profiles, and compiled methods". [V] (diff of `jdk-27-ga` vs `master` java.md)

**JDK 27 changes to the same section:** [V] — [JDK 27 java.md](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/java.base/share/man/java.md)
- Modes are "`auto`, `off`, `record`, `create`, `on`, or `required`. Note that `on` is an alias for `required`… The use of `on` is discouraged. The support of `on` may be deprecated and removed in future releases."
- `required`: "`-XX:AOTCache=`*cachefile* must be specified" (in 25/26, `on` without `AOTCache` would try the default CDS archive).
- New warning: "In production environments, `-XX:AOTMode=required` should be used with care. Your application may fail to launch if an incompatible VM option is added without your knowledge. For example, a cloud provider might run your JVM with a JVMTI class-file load hook for monitoring purposes."
- The release note confirms: "-XX:AOTMode=required has been added as an alias to -XX:AOTMode=on in order to clarify the purpose and effects of this option (JDK-8374348)". — [JDK 27 release notes](https://www.oracle.com/java/technologies/javase/27-relnote-issues.html)
- **[V] master (JDK 28) adds:**
  - `-XX:AOTCache=<oldcache>` is allowed during `record`, so a new training run merges "Statistical data previously recorded in `<oldcache>`" (incremental training);
  - `on` is listed as deprecated;
  - new diagnostic flag `AOTCodeCaching` ("saving and restoring JIT compiled code in AOT cache");
  - `AOTCodeMaxSize` raised from 10M to 512M;
  - `AOTIgnoreIncompatibleCacheInTraining`.

  — [cds_globals.hpp @ master](https://raw.githubusercontent.com/openjdk/jdk/master/src/hotspot/share/cds/cds_globals.hpp)

**Flags and defaults by version** ([V] parsed from `cds_globals.hpp` at each GA tag):
- **JDK 24:** product `AOTMode=nullptr` ("off, record, create, auto, on; the default is auto"), `AOTConfiguration`, `AOTCache`, `AOTClassLinking=false`; diagnostic `AOTInvokeDynamicLinking=false`, `AOTCacheParallelRelocation=true`.
- **JDK 25 adds:** product **`AOTCacheOutput`** ("Specifies the file name for writing the AOT cache"); diagnostic `AOTRecordTraining`, `AOTReplayTraining`, `AOTPrintTrainingInfo`, `AOTVerifyTrainingData`, `AOTAdapterCaching=false`, `AOTStubCaching=false`, `AOTCodeMaxSize=10M`, `AbortVMOnAOTCodeFailure`; experimental `AOTCompileEagerly`.
- **JDK 26 adds:** diagnostic `AOTStreamableObjects=false` ("Archive the Java heap in a generic streamable object format") and `AOTEagerlyLoadObjects=false`. JDK 26 drops `AllowArchivingWithJavaAgent`.
- **JDK 27:** the flag set is identical to 26. The `required` alias is implemented in argument parsing, and the flag's help string was not yet updated at the jdk-27-ga tag.
- `AOTClassLinking` help string (24–27): "Load/link all archived classes for the boot/platform/app loaders before application main".

**[S] JEP content (pages not opened):**
- JEP 483 benchmark: Spring PetClinic 3.2.0 "loads and links about 21,000 classes at startup".
  - The *draft* (JDK-8315737) reported 4.486 s → 2.604 s (42%).
  - InfoQ reported the shipped feature as starting PetClinic "up to 40% faster".
  - JEP 483 limitations quoted by InfoQ: cannot cache classes from user-defined class loaders; does not work with JVMTI agents using ClassFileLoadHook or `AddToBootstrapClassLoaderSearch`/`AddToSystemClassLoaderSearch`.

  — [JEP 483](https://openjdk.org/jeps/483), [JEP draft 8315737](https://openjdk.org/jeps/8315737), [InfoQ, Mar 2025](https://www.infoq.com/news/2025/03/java-24-leyden-ships)
- JEP 515: "Improve warmup time by making method-execution profiles from a previous run of an application instantly available, when the HotSpot Java Virtual Machine starts". No isolated warm-up numbers were found in the summaries. — [JEP 515](https://openjdk.org/jeps/515)
- JEP 516: ZGC was excluded because it "stores metadata bits inside object references" and earlier caches stored references as raw addresses. 516 stores references as logical indices so objects are "streamed" and materialized at startup. The streamable format is chosen automatically "if training used ZGC, if -XX:-UseCompressedOops was used, or if the heap was larger than 32GB", or forced with `-XX:+AOTStreamableObjects`. — [JEP 516](https://openjdk.org/jeps/516). The Oracle JDK 26 release note [V] says JEP 516 "introduces a new way of loading objects in the background, instead of directly memory mapping a file, which is compatible across all GC implementations… the full range of optimizations of the AOT cache is now available across all GC implementations, including ZGC." — [JDK 26 release notes](https://www.oracle.com/java/technologies/javase/26-relnote-issues.html)
- JEP 544 (draft JDK-8335368): "shifts dynamic (JIT) method compilation from production runs to training runs, conveying the necessary native code via the AOT cache"; the JIT can still recompile. InfoQ: Candidate, then Proposed to Target for JDK 28. — [JEP draft 8335368](https://openjdk.org/jeps/8335368), [InfoQ Sep 2026 roundup](https://www.infoq.com/news/2026/09/java-news-roundup-sep21-2026/)

**[L] JDK 25 (Temurin 25+36) commands run and what they printed:**
- Two-step:
  - `java -XX:AOTMode=record -XX:AOTConfiguration=app.aotconf -cp app.jar demo.Main` prints `AOTConfiguration recorded: app.aotconf` (13.1 MB).
  - `java -XX:AOTMode=create -XX:AOTConfiguration=app.aotconf -XX:AOTCache=app.aot -cp app.jar` prints `Reading AOTConfiguration app.aotconf and writing AOTCache app.aot` and `AOTCache creation is complete: app.aot 15110144 bytes`.
- One-step: `java -XX:AOTCacheOutput=app1.aot -cp app.jar demo.Main` runs the app, then a child JVM prints `Picked up JAVA_TOOL_OPTIONS: -Djava.class.path=app.jar -XX:AOTCacheOutput=app1.aot -XX:AOTConfiguration=app1.aot.config -XX:AOTMode=create`, then `AOTCache creation is complete: app1.aot 15114240 bytes` and `Removed temporary AOT configuration file app1.aot.config`. This shows how JEP 514 is implemented: a forked assembly JVM configured through `JAVA_TOOL_OPTIONS`.
- Production with logging: `java -XX:AOTCache=app.aot -Xlog:aot -cp app.jar demo.Main` prints `Opened AOT cache app.aot.` and `The AOT cache was created with UseCompressedOops = 1, UseCompressedClassPointers = 1, UseCompactObjectHeaders = 0`.
- A missing cache file in auto mode prints `[error][aot] Specified AOT cache not found (nope.aot)`, and the JVM continues with **0 archived classes**: the default CDS archive is not used either.

### Inferences
- Lesson writers should present the **JDK 25 one-step workflow as the default** (`-XX:AOTCacheOutput` for training, `-XX:AOTCache` for production). Show the two-step form when training and assembly happen on different machines or in different pipeline stages. Recommend `auto` (no `-XX:AOTMode`) in production and `required` (JDK 27+) or `on` (24–26) only in CI as a fail-fast check.
- JDK 26's `jcmd <pid> AOT.end_recording` matters for servers: before 26 a training run had to exit (e.g. a shutdown endpoint) to write the configuration. This session's server lab used a `/quit` endpoint for that reason.
- Because JDK 27 turns on compact object headers by default and the cache records `UseCompactObjectHeaders`, a cache built on 27 defaults probably will not load if production runs with `-XX:-UseCompactObjectHeaders`, or vice versa. This is an inference from the log line; not tested on 27.

### Gaps
- No JDK 24, 26 or 27 binaries, so the JDK 26 ZGC improvement, `AOT.end_recording`, and the JDK 27 `required` behaviour were not run.
- JEP 514, 515 and 516 texts (motivation sections, exact benchmark numbers) were not read directly.
- Whether JDK 25 training *profiles* (JEP 515) are recorded by default in `record` mode: the JEP summaries say profiles come from the training run. Diagnostic flags `AOTRecordTraining`/`AOTReplayTraining` exist with default `false` in source, and their interaction with ergonomics was not traced in code. Mark as unverified.

---

## Q4. Local measurements: startup with and without AppCDS (JDK 21.0.12) and with the Leyden AOT cache (JDK 25), plus a correctness finding

### Takeaway
On this noisy 4-vCPU VM:
- **JDK 21 AppCDS halved the CPU cost of starting a 300-class app** (349 → about 171 ms CPU; wall median 333 → about 196 ms).
- **The JDK 25 AOT cache cut it about sixfold** (504 → 81 ms CPU; wall median 431 → 98 ms) and lowered max RSS from 64 to 42 MiB.
- For a JDK `HttpServer` app, the JDK 25 AOT cache cut median time-to-first-request from 218 to 136 ms.
- With ZGC on JDK 25 the benefit mostly disappears; JEP 516 in JDK 26 is the fix.

**Critical finding:** on 25+36 the AOT cache was **not rejected when the application JAR changed**, so the JVM ran **stale class bytes**. The bug is JDK-8377932, fixed in JDK 27 and backported to **25.0.4** and **26.0.2**.

### Cited Findings
- **[L] Benchmark design.**
  - App: 300 generated classes, each with a `static final IntUnaryOperator` lambda, plus a `Main` using streams, regex, `java.time`, `String.format` and a `TreeMap` collector. Packaged as a JAR (CDS needs JARs).
  - Harness: Python `os.wait4` gives wall time, CPU (`ru_utime+ru_stime`) and `ru_maxrss` per run. Two warm-up runs per config, then **30 rounds in shuffled order** (interleaving spreads load spikes evenly).
  - Class counts come from one extra run with `-Xlog:class+load`.
- **[L] Results** (medians; wall IQR and min shown to convey noise):

| config | wall median ms | CPU median ms | wall IQR | wall min | max RSS MiB | classes loaded | from archive |
|---|---|---|---|---|---|---|---|
| JDK 21 `-Xshare:off` | 379 | 377 | 288–507 | 183 | 47.7 | 1537 | 0 |
| JDK 21 default CDS | 333 | 349 | 233–442 | 155 | 50.2 | 1507 | 875 |
| JDK 21 dynamic AppCDS (`ArchiveClassesAtExit`) | 196 | 171 | 126–242 | 115 | 45.0 | 1413 | 1409 |
| JDK 21 static AppCDS (`-Xshare:dump`) | 191 | 178 | 146–237 | 92 | 41.9 | 1415 | 1411 |
| JDK 21 `AutoCreateSharedArchive` | 210 | 171 | 118–257 | 108 | 45.0 | 1413 | 1409 |
| JDK 25 `-Xshare:off` | 463 | 584 | 330–661 | 231 | 60.6 | 1632 | 0 |
| JDK 25 default CDS | 431 | 504 | 305–538 | 195 | 64.4 | 1620 | 990 |
| JDK 25 dynamic AppCDS | 225 | 205 | 130–286 | 104 | 52.6 | 1519 | 1518 |
| **JDK 25 AOT cache (2-step record/create)** | **98** | **81** | 67–131 | 52 | **41.9** | 1690 | 1689 |
| **JDK 25 AOT cache (1-step `AOTCacheOutput`)** | **99** | **84** | 61–145 | 44 | **41.6** | 1690 | 1689 |
| JDK 25 ZGC, default CDS | 498 | 610 | 357–611 | 243 | 67.4 | 1633 | 1003 |
| JDK 25 ZGC + AOT cache built under ZGC | 370 | 439 | 305–450 | 186 | 61.2 | 1549 | 1225 |

- **[L] Artifact sizes:**
  - JDK 21: dynamic archive 1.47 MB; static archive 12.9 MB (it includes the JDK classes too); classlist 1,589 lines (301 `demo/` classes plus `@lambda-proxy` entries).
  - JDK 25: dynamic 1.50 MB; `app.aot` 15.1 MB; `app.aotconf` 13.1 MB; ZGC-built cache 11.6 MB.
- **[L] Why the cache loads more classes.** With the AOT cache the JVM loaded 1,690 classes (more than the 1,620 without), consistent with the `AOTClassLinking` help text "Load/link all archived classes for the boot/platform/app loaders before application main" [V].
- **[L] ZGC on JDK 25.**
  - A cache built under G1 is **unusable** with `-XX:+UseZGC`: "The saved state of UseCompressedOops and UseCompressedClassPointers is different from runtime, CDS will be disabled", then "Unable to map shared spaces" and **0** archived classes.
  - A cache built under ZGC loads, but logs `UseCompressedOops = 0` and "full module graph: disabled", serves only 1,225 of 1,549 classes, and cuts CPU only from 610 to 439 ms.
  - `-XX:+UseParallelGC` with a G1-built cache works (1,689 archived classes).
- **[L] Time-to-first-request** (JDK `com.sun.net.httpserver` app with a JSON-ish `/hello` handler). Harness: spawn, poll `GET /hello` every 2 ms, read `/proc` after the first 200, then `/quit`. 25 interleaved rounds. Training runs served 200 requests before `/quit`.

| config | TTFR median ms | TTFR min ms | VmRSS MiB | RssAnon MiB | RssFile MiB | Pss MiB |
|---|---|---|---|---|---|---|
| JDK 21 default CDS | 229 | 135 | 50.6 | 26.6 | 24.0 | 33.1 |
| JDK 21 dynamic AppCDS | 192 | 106 | 49.7 | 26.2 | 23.5 | 32.4 |
| JDK 25 default CDS | 218 | 127 | 56.6 | 31.5 | 25.2 | 39.8 |
| **JDK 25 AOT cache** | **136** | **90** | **48.5** | **23.5** | 25.0 | 34.0 |

  Cache sizes: `srv21.jsa` 1.79 MB, `srv25.aot` 16.6 MB.
- **[L] Stale-JAR bug, reproduced on Temurin 25+36.**
  1. Build `hello.jar` whose `p.Hello` prints "version ONE".
  2. `java -XX:AOTCacheOutput=h.aot -cp hello.jar p.Hello`.
  3. Rebuild `hello.jar` so it prints "version TWO" (mtime +3 s; also tested with a different size: 798 → 910 bytes).
  4. `java -XX:AOTCache=h.aot -cp hello.jar p.Hello` logs `p.Hello source: shared objects file` and **prints "version ONE"**.
  5. Same with `-XX:AOTMode=on` (exit 0), and with absolute classpaths.

  `-Xlog:class+path` showed only "Checking [0] (modules image) ok… Archived boot classpath validation: passed"; the app entry `[1] = hello.jar` was never checked. Controls run in the same session:
  - JDK 25 `-XX:ArchiveClassesAtExit` archive: "[error][cds] shared class paths mismatch… Unable to use shared archive", then prints "version TWO".
  - JDK 21 dynamic and static archives: "timestamp has changed", "size has changed", then "version TWO".
  - JDK 25 AOT cache with an extra JAR prepended to `-cp` (not a prefix match) was also accepted (1,689 archived classes). Likely the same root cause (inference).
- **[V] The fix.** `8377932: AOT cache is not rejected when JAR file has changed` (Ioi Lam, 2026-02-16, reviewed by kvn and asmehra), first tag jdk-27+10, contained in `jdk-27-ga`. — [commit b41ba3a](https://github.com/openjdk/jdk/commit/b41ba3a496b59c8058067a49617f798606f0a51c)
  - Root cause, from the diff of `aotClassLocation.cpp`: when dumping the final static archive (the `-XX:AOTMode=create` step), "the classes are loaded from their images in the AOT config file, so we don't go through `ClassLoader::record_result()`", so `_max_used_index` was never updated and runtime validation skipped the app classpath entries. The fix calls `dumptime_update_max_used_index(runtime()->_max_used_index)`. A new test `aotCache/ChangedJarFile.java` has `@summary AOT cache should be rejected if JAR file(s) in the classpath have changed`.
- **[V] Backports** (jdk25u and jdk26u git histories):
  - jdk25u commit `2fb3e9c69` (2026-03-16), first contained in **jdk-25.0.4** (GA tag commit dated 2026-07-07);
  - jdk26u commit `3d23e5061` (2026-03-05), contained in **jdk-26.0.2** (GA tag commit dated 2026-06-17).
  - jdk25u GA tags exist through `jdk-25.0.5-ga` (2026-10-19). — [openjdk/jdk25u](https://github.com/openjdk/jdk25u), [openjdk/jdk26u](https://github.com/openjdk/jdk26u) (read via git clone)

### Inferences
- **Affected range:** JDK 25.0.0–25.0.3 and 26.0.0–26.0.1 (and probably 24, since the bug is in the `create` path introduced with JEP 483, but 24 was not tested). A pipeline that rebuilt the JAR but reused an old `app.aot` would silently run old code.
- **Teach two rules:** (1) generate the cache in the same build step as the JAR and ship them together, ideally in the same container layer; (2) require JDK ≥ 25.0.4 / 26.0.2 / 27 for Leyden in production. This finding is a good "trust but verify" lesson.
- **Relative gains are robust; absolutes are not.** The machine was contended (load average 3–20), so absolute numbers are 2–4× what a quiet laptop shows. The CPU-time column is the most trustworthy comparison.
- **Do not read this as JDK 25 being slower.** JDK 25's default and `-Xshare:off` rows are slower than JDK 21's on this box. The builds differ (Ubuntu vs Temurin) and JDK 25 loaded about 100 more JDK classes; this is not a clean JDK-vs-JDK comparison.

### Gaps
- Not measured: JDK 24, 26, 27; a real Quarkus app; containers with CPU limits; `-XX:TieredStopAtLevel=1`; warm-up curves (JEP 515's main benefit is warm-up, which a 100 ms run cannot show).
- The stale-JAR behaviour was not re-tested on 25.0.4+ (no binary).

---

## Q5. GraalVM Native Image: closed world, build-time init, reachability metadata (exact JSON), agent, PGO, GC, trade-offs

### Takeaway
Native Image compiles the reachable part of the app plus the JDK into one executable (SubstrateVM) under a **closed-world assumption**, so reflection, resources, proxies, serialization and JNI must be declared in `META-INF/native-image/<groupId>/<artifactId>/reachability-metadata.json`. The current schema is **v1.2.0**, with top-level keys `reflection`, `resources`, `foreign` and `comment` only.
- **Proxies** are reflection entries with `"type": {"proxy": [...]}`.
- **Serialization** is `"serializable": true` on a reflection entry.
- **JNI** is `"jniAccessible": true`.

The tracing agent generates metadata; PGO (Oracle GraalVM only) and G1 (Oracle GraalVM, Linux only) close part of the throughput gap. The default GC is Serial.

### Cited Findings
- **[V] Why metadata is needed.** "the `native-image` builder performs static analysis at build time to determine only the necessary program elements… determining dynamically-accessed application elements via static analysis is infeasible… the `native-image` builder requires **reachability metadata**". Ways to provide it: compute in code at build time, `reachability-metadata.json` under `META-INF/native-image/<groupId>/<artifactId>/`, `-H:Preserve=<classpath-selector>`, or the Feature API. — [GraalVM ReachabilityMetadata.md](https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/ReachabilityMetadata.md)
- **[V] Strict-mode migration:** "pass the option `--exact-reachability-metadata` at build time"; `-XX:MissingRegistrationReportingMode=Warn` (report all) or `=Exit` at run time; "The user-friendly implementation for reflection will become the default in future releases". — same source
- **[V] Conditional entries:** `"condition": {"typeReached": "<fully-qualified-class-name>"}`. The entry becomes active once that type is *reached*, i.e. "right before the class-initialization routine starts for that type… or any of the type's subtypes are reached". `ConditionType.class` alone does **not** reach it. — same source
- **[V] Reflection entry fields:** `type` (string, or object with `proxy` or `lambda`), `methods[{name, parameterTypes}]`, `fields[{name}]`, `allDeclaredConstructors`, `allPublicConstructors`, `allDeclaredMethods`, `allPublicMethods`, `allDeclaredFields`, `allPublicFields`, `unsafeAllocated`, `serializable`. Schema v1.2.0 also lists `reason`, `condition` and `jniAccessible`. — same source; [reachability-metadata-schema-v1.2.0.json](https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/assets/reachability-metadata-schema-v1.2.0.json)
- **[V] Exact JSON: reflection** (from the docs' sample):
```json
{
  "reflection": [
    {
      "condition": { "typeReached": "com.example.App" },
      "type": "com.example.Person",
      "fields": [ { "name": "first" } ],
      "methods": [ { "name": "getFirst", "parameterTypes": [] },
                   { "name": "<init>", "parameterTypes": ["java.lang.String", "java.lang.String"] } ],
      "allDeclaredConstructors": true
    }
  ]
}
```
  (The fields and keys are as documented; `<init>` for constructors is [TK]. The docs' sample uses `"name": "method1", "parameterTypes": ["<param-type1>", …]`.)
- **[V] Exact JSON: JDK dynamic proxy.** "Metadata, for proxy classes, is in the form an ordered collection of interfaces that defines a proxy":
```json
{
  "reflection": [
    { "type": { "proxy": ["com.example.Greeter", "java.io.Closeable"] } }
  ]
}
```
  Proxy plus serialization: the same entry with `"serializable": true`. "Proxy classes can only be registered for serialization via the JSON files." Lambda-proxy classes cannot be given reflection metadata. — same source
- **[V] Exact JSON: resources and bundles:**
```json
{ "resources": [ { "glob": "META-INF/**/*.properties" },
                 { "module": "optional.module.of.a.resource", "glob": "path1/level*/**" },
                 { "bundle": "fully.qualified.bundle.name" } ] }
```
  — same source
- **[V] Schema check (parsed locally).**
  - v1.2.0 top-level properties are `['comment', 'reflection', 'resources', 'foreign']` with `additionalProperties: False`; `type` is `oneOf` a type name or an object with `proxy` (array of class names) or `lambda` (`declaringClass`, `declaringMethod`, `interfaces` with `minItems 1`).
  - The older v1.1.0 had top-level `['comment','reflection','jni','serialization','resources','bundles','foreign']`.
  - **Conflict:** the same ReachabilityMetadata.md prose says the file "contains three main sections: `reflection`, `jni`, and `resources`" and its sample has a top-level `"jni"` array, which v1.2.0 would reject. Validate against the schema that matches your GraalVM.

  — [schema v1.2.0](https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/assets/reachability-metadata-schema-v1.2.0.json), [schema v1.1.0](https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/assets/reachability-metadata-schema-v1.1.0.json)
- **[V] Tracing agent:** `$JAVA_HOME/bin/java -agentlib:native-image-agent=config-output-dir=/path/to/config-dir/ ...`. Options include `config-merge-dir=` to add to existing files, periodic writes (`config-write-period-secs=300,config-write-initial-delay-secs=5`), caller filters and access filters. The output directory is searched for `reachability-metadata.json`. Conditional metadata collection is "mainly aimed towards library maintainers". — [GraalVM AutomaticMetadataCollection.md](https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/AutomaticMetadataCollection.md)
- **[V] Class initialization:**
  - "Native Image initializes most JDK classes at build time".
  - For application classes it "tries to find classes that can be safely initialized at build time". A class is unsafe if its initializer transitively calls native code (e.g. `System.out.println`), makes non-single-target virtual calls, or hits substituted methods.
  - Track decisions with `-H:+PrintClassInitialization`. Override with `--initialize-at-build-time=<pkgs/classes>` (implies superclasses) and `--initialize-at-run-time=<…>` (implies subclasses).
  - "No instances of classes that are initialized at runtime must be present in the executable."

  — [ClassInitialization.md](https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/ClassInitialization.md), [BuildOptions.md](https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/BuildOptions.md)
- **[V] PGO:** "PGO is not available in GraalVM Community Edition". Workflow: `native-image --pgo-instrument -cp . GameOfLife -o gameoflife-instrumented`; run it (writes `default.iprof` on exit, or `-XX:ProfilesDumpFile`); then `native-image -cp . GameOfLife -o gameoflife-pgo --pgo=gameoflife.iprof`. — [PGO.md](https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/PGO.md), [PGO-Basic-Usage.md](https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/PGO-Basic-Usage.md)
- **[V] GC options:**
  - "The **Serial GC** is the default GC in GraalVM Native Image" (`--gc=serial`), "optimized for low footprint and small Java heap sizes". Without an explicit max heap it sets "maximum Java heap size to 80% of the physical memory size" (tune with `-XX:MaximumHeapSizePercent`, or `-R:MaximumHeapSizePercent=25` at build).
  - **G1** via `--gc=G1`: "Linux AMD64 and AArch64… (Not available in GraalVM Community Edition.)"
  - **Epsilon** via `--gc=epsilon` never frees memory.

  — [MemoryManagement.md](https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/MemoryManagement.md)
- **[V] Debugging:** `native-image -g Hello` (with `javac -g`) for GDB debug info, `-H:+SourceLevelDebug`; JFR and other diagnostics have their own pages. — [DebugInfo.md](https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/DebugInfo.md), [DebuggingAndDiagnostics.md](https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/DebuggingAndDiagnostics.md)
- **[V] Release line.** GraalVM release tags on oracle/graal include `vm-25.0.3`, `vm-25.0.4`, `vm-25.0.5`, … up to `vm-25.0.5.0.3`, i.e. the "GraalVM for JDK 25" line tracks JDK 25 update numbers. (Tags such as `vm-25.5.5.0.3` also exist; their meaning was not determined.) — `git ls-remote --tags https://github.com/oracle/graal.git`
- **[V] Measured trade-offs** (Quarkus docs table, 2026-04-21 perf-lab tuned benchmark, "Quarkus 3.34.3, JDK 25.0.2, …"; the rest of the configuration was truncated in my extract):

| Mode | Cold start | TTFR | Peak throughput | RSS | Image size | Build cost |
|---|---|---|---|---|---|---|
| JVM fast-jar | ~0.4 s (small REST) to ~3 s (large CRUD) | 4,417 ms | 13,265 tps | 304 MiB | 517 MB | ~30 s build |
| JVM + Leyden AOT cache | ~80 ms to ~900 ms | 1,859 ms | 12,389 tps (~7% below JVM) | 240 MiB | 715 MB (cache adds ~198 MB) | build + training run |
| Native (Mandrel) | ~17 ms to ~240 ms | 581 ms | 5,411 tps (~59% below JVM) | 95 MiB | 244 MB | 3–10 min; 4–8 GB build-host RAM |

  The same section appears in 3.40.1.1 docs. — [Quarkus building-native-image.adoc](https://github.com/quarkusio/quarkus/blob/main/docs/src/main/asciidoc/building-native-image.adoc)

### Background facts (training knowledge) [TK]
- Native images start in milliseconds because there is no class loading, verification or bytecode interpretation, and the **image heap** (objects created by build-time initializers) is mapped from the executable.
- Costs:
  - no JIT, so peak throughput depends on AOT code quality (PGO helps);
  - long, memory-hungry builds;
  - per-platform binaries;
  - reflection, proxies and resources need metadata;
  - `Class.forName` of unregistered classes fails;
  - no runtime bytecode generation or Java agents (limited JVMTI);
  - debugging and profiling use native tools (gdb, perf), with JFR, NMT and JMX partially supported.
- The `oracle/graalvm-reachability-metadata` repository hosts community metadata for common libraries; the GraalVM Gradle/Maven plugins can pull it automatically.

### Inferences
- For a Kotlin/Java engineer the key mental model is: **the build is the program's first run**. Anything a static initializer computes ends up frozen into the image heap (Quarkus's `Random`/`SplittableRandom` error is the classic symptom; see Q6).

### Gaps
- graalvm.org pages and release notes were blocked, so the GraalVM 25 release date and feature list were not verified. Native Image JFR/NMT support levels were not checked.
- `<init>` as the constructor name in `methods` is from training knowledge.

---

## Q6. Quarkus: build-time work, native mode, registration annotations, AOT/AppCDS packaging, SnapStart

### Takeaway
Quarkus does at build time what other frameworks do at startup (indexing, DI wiring, proxy and bytecode generation); "By default, Quarkus initializes all classes at build time" in native mode.
- **Registration:** `@RegisterForReflection` (attributes: `methods`, `fields`, `ignoreNested`, `targets`, `classNames`, `serialization`, `unsafeAllocated`, `registerFullHierarchy`, `lambdaDescriptors`) and `@RegisterForProxy(targets=…)`. Quarkus generates `reachability-metadata.json` itself.
- **JVM mode:** Quarkus 3.40 ships first-class Leyden support. Set `quarkus.package.jar.aot.enabled=true`; the `aot-jar` packaging trains during `@QuarkusIntegrationTest`, produces `target/quarkus-app/app.aot`, and runs with `java -XX:AOTCache=app.aot -jar quarkus-run.jar`. The AppCDS fallback is `quarkus.package.jar.aot.type=app-cds` for JDK < 24.
- **Version split:** Quarkus 3.x docs still show the legacy `reflect-config.json`/`proxy-config.json`; Quarkus 4.0 (main) says those legacy files are not supported.

### Cited Findings
- **[V] Closed world, in Quarkus's words:** "GraalVM operates with a closed world assumption. It analyzes the call tree and removes all the classes/methods/fields that are not used directly. The elements used via reflection are not part of the call tree… JSON libraries typically use reflection". — [Quarkus 3.40.1.1 writing-native-applications-tips.adoc](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/docs/src/main/asciidoc/writing-native-applications-tips.adoc)
- **[V] `@RegisterForReflection`:** `@RegisterForReflection public class MyClass {}`; for third-party classes `@RegisterForReflection(targets={ MyClassRequiringReflection.class, … }) public class MyReflectionConfiguration {}` (the host class itself is *not* registered). "By default the `@RegisterForReflection` annotation will also register any potential nested classes… set the `ignoreNested` attribute to `true`" to avoid that. — same source
- **[V] Annotation source (Quarkus main):**
```java
public @interface RegisterForReflection {
    boolean methods() default true;
    boolean fields() default true;
    boolean ignoreNested() default false;
    Class<?>[] targets() default {};
    String[] classNames() default {};
    boolean serialization() default false;
    boolean unsafeAllocated() default false;
    @Deprecated(forRemoval = true, since = "4.0")
    String[] lambdaCapturingTypes() default {};
    LambdaDescriptor[] lambdaDescriptors() default {};
    boolean registerFullHierarchy() default false;
}
@Repeatable(RegisterForProxy.List.class)
public @interface RegisterForProxy { Class<?>[] targets() default {}; … }
```
  — [RegisterForReflection.java](https://raw.githubusercontent.com/quarkusio/quarkus/main/core/runtime/src/main/java/io/quarkus/runtime/annotations/RegisterForReflection.java), [RegisterForProxy.java](https://raw.githubusercontent.com/quarkusio/quarkus/main/core/runtime/src/main/java/io/quarkus/runtime/annotations/RegisterForProxy.java). (This is the main/4.0 source; `lambdaDescriptors` and the 4.0 deprecation may not exist in 3.x. Not checked at the 3.40 tag.)
- **[V] `@RegisterForProxy`:** "`@RegisterForProxy public interface MyInterface extends MySecondInterface {}`… `MyInterface` and all its super interfaces will be registered". Or `@RegisterForProxy(targets={MyInterface.class, MySecondInterface.class})` on a host class. "the order of the specified proxy interfaces is significant". — 3.40.1.1 tips doc
- **[V] Version split on JSON files.**
  - 3.40.1.1 docs: "we create `reflect-config.json` (the most common location is within `src/main/resources`)"; for proxies, "create a `proxy-config.json` file under `src/main/resources/META-INF/native-image/<group-id>/<artifact-id>`".
  - Main/4.0 docs: "Legacy individual configuration files (`resource-config.json`, `reflect-config.json`, `proxy-config.json`, `jni-config.json`, `serialization-config.json`) are not supported by Quarkus. Use the unified `reachability-metadata.json` format"; "Quarkus automatically generates `reachability-metadata.json` files"; a `reachability-metadata.json` "placed directly under `src/main/resources/META-INF/native-image/`" is overwritten by Quarkus, so use the `<group-id>/<artifact-id>` subfolder.
  - **Doc error:** main says "Use `reachability-metadata.json` with a `proxy` section", but GraalVM schema v1.2.0 has no top-level `proxy` key (see Q5). The correct form is a `reflection` entry whose `type` is `{"proxy": [...]}`.

  — [3.40.1.1 tips](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/docs/src/main/asciidoc/writing-native-applications-tips.adoc), [main tips](https://github.com/quarkusio/quarkus/blob/main/docs/src/main/asciidoc/writing-native-applications-tips.adoc)
- **[V] Resources:** `quarkus.native.resources.includes=foo/**,bar/**/*.txt`. — same sources
- **[V] Build-time initialization and its failure modes:** "By default, Quarkus initializes all classes at build time." Typical errors:
  - "No instances are allowed in the image heap for a class that is initialized or reinitialized at image runtime: sun.security.provider.NativePRNG";
  - "Detected an instance of Random/SplittableRandom class in the image heap. Instances created during image generation have cached seed values".

  Fix: `quarkus.native.additional-build-args=--initialize-at-run-time=com.example.SomeClass\\,org.acme.SomeOtherClass` (the comma must be escaped). — 3.40.1.1 tips doc
- **[V] Native build commands:** `./mvnw package -Dnative`; `./mvnw verify -Dnative` runs `@QuarkusIntegrationTest`s against the executable. Mandrel is "a downstream distribution tailored for Quarkus. It excludes components not needed by Quarkus (such as polyglot support)". Docs advice: "Start with JVM mode. Move to native when you have a concrete need." — [building-native-image.adoc](https://github.com/quarkusio/quarkus/blob/main/docs/src/main/asciidoc/building-native-image.adoc)
- **[V] Quarkus Leyden support** (aot.adoc; 3.40.1.1 and main agree except a main-only section on `--add-modules`):
  - "Leyden AOT requires **JDK 24 or newer**. For older JDK versions, Quarkus can fall back to AppCDS".
  - Quick start: `./mvnw verify -Dquarkus.package.jar.aot.enabled=true -DskipITs=false`, then `cd target/quarkus-app; java -XX:AOTCache=app.aot -jar quarkus-run.jar`.
  - The `aot-jar` packaging "Delegates all class loading to the JDK's class loaders (required for AOT to work effectively as Leyden currently does not support custom class loaders)" and "Caches frequently-accessed resources". It is "not recommended… outside of the AOT use case, as the `fast-jar` packaging offers more optimizations".
  - `quarkus.package.jar.aot.phase`: `auto` (default; integration tests), `build` ("very limited training, faster builds"), `integration-tests`. "The more representative your integration tests are of production traffic, the more effective the AOT cache will be."
  - Manual: `mvn package -Dquarkus.package.jar.type=aot-jar`, then `java -XX:AOTCacheOutput=app.aot -jar quarkus-run.jar`, drive load, stop.
  - Container images: with `quarkus-container-image-jib|docker|podman`, `-Dquarkus.container-image.build=true` builds an extra image tagged with an `-aot` suffix that is "pre-configured to use it".
  - Limitations: "The AOT cache is **JDK version specific**"; "untested on Windows".
  - Legacy AppCDS: `-Dquarkus.package.jar.aot.type=app-cds` produces `app-cds.jsa`, run with `java -XX:SharedArchiveFile=app-cds.jsa -jar quarkus-run.jar`. "The paths to the JAR and archive must match exactly"; "Training during integration tests is not supported for AppCDS".
  - IBM Semeru: Quarkus generates a Semeru shared-classes cache instead (`-Xshareclasses:name=quarkus-app,cacheDir=app-scc,readonly`).
  - Main only: the cache is rejected if `--add-modules` differs ("Mismatched values for property jdk.module.addmods: jdk.jfr specified during runtime but not during dump time"). `-XX:StartFlightRecording` implicitly adds `jdk.jfr`; fix with `quarkus.package.jar.aot.additional-recording-args=--add-modules=jdk.jfr`, or start JFR later with `jcmd <pid> JFR.start`.

  — [Quarkus 3.40.1.1 aot.adoc](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/docs/src/main/asciidoc/aot.adoc), [main aot.adoc](https://github.com/quarkusio/quarkus/blob/main/docs/src/main/asciidoc/aot.adoc)
- **[V] Quarkus doc claim to treat with care:** the AppCDS limitations list says "AppCDS only caches class metadata, not method profiles or verification results". The method-profiles part is right (profiles are JEP 515, AOT cache only). The "verification results" part conflicts with training knowledge that CDS archives store classes already verified at dump time [TK]. Flag it, don't repeat it.
- **[V] Quarkus SnapStart extension (3.40.1.1):**
  - Optimizations are on automatically with the AWS Lambda extension; `quarkus.snapstart.enable=true|false` ("does not enable/disable SnapStart for your function, only the Quarkus optimizations").
  - **Class preloading during the snapshot:** from `PreloadClassBuildItem` (extensions) and `src/main/resources/META-INF/quarkus-preload-classes.txt` (one class per line). To compute the list, set `JAVA_TOOL_OPTIONS=-verbose:class`. Toggles: `quarkus.snapstart.generate-application-class-list`, `quarkus.snapstart.preload-classes=false`, and `quarkus.snapstart.initialize-classes=false` (preloaded classes are also initialized by default).

  — [Quarkus 3.40.1.1 aws-lambda-snapstart.adoc](https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/docs/src/main/asciidoc/aws-lambda-snapstart.adoc)
- **[V] Versions** (Maven Central): latest 3.x is `3.40.1.1` (2026-10-19), `3.40.0` (2026-09-23); `4.0.0.Beta3` is the latest overall (metadata lastUpdated 2026-11-04). — [quarkus-core maven-metadata.xml](https://repo1.maven.org/maven2/io/quarkus/quarkus-core/maven-metadata.xml)

### Background facts (training knowledge) [TK]
- Quarkus "fast-jar" layout (`target/quarkus-app/quarkus-run.jar` plus `lib/`, `app/`, `quarkus/`) uses a custom `RunnerClassLoader` with a pre-computed index. That is why it beats `aot-jar` without Leyden, and why Leyden (no custom loaders) needs `aot-jar`.
- Earlier Quarkus 3.x versions used `quarkus.package.jar.appcds.enabled=true` for AppCDS (renamed later to the `aot` properties). Verify against the specific 3.x minor in the course.
- Quarkus native builds can run in a container: `-Dquarkus.native.container-build=true`, with the builder image set by `quarkus.native.builder-image` (Mandrel UBI images).

### Inferences
- For a 3.x course, lessons should show `@RegisterForReflection`/`@RegisterForProxy` first (framework-agnostic to GraalVM changes) and present raw JSON as the escape hatch. Teach the unified `reachability-metadata.json` form, noting that 3.x docs still show legacy files.

### Gaps
- The 3.40 annotation source was not compared with main.
- The quarkus.io blog benchmarks referenced by the docs (Leyden integration, Mar 2026) were blocked.

---

## Q7. CRaC (Coordinated Restore at Checkpoint) and AWS Lambda SnapStart

### Takeaway
CRaC snapshots a warmed-up JVM process to disk (via CRIU on Linux) and restores it in tens of milliseconds, with the JIT code intact.
- Coordination goes through `org.crac.Resource` (`beforeCheckpoint(Context)` / `afterRestore(Context)`), registered on `Context.getGlobalContext()`.
- Open files and sockets **must** be closed before the checkpoint unless a file-descriptor policy says otherwise. The default policy is `error`, and socket `reopen` is not implemented.
- CRaC is **not in mainline OpenJDK** (no JEP, zero mainline commits). It ships in OpenJDK-based vendor builds: Azul Zulu 17/21/25 Linux builds with "-crac-" in the name, and BellSoft Liberica 17/21 CRaC builds.
- AWS Lambda SnapStart is the managed version of the same idea, using the same `org.crac` hook API.

### Cited Findings
- **[V] What CRaC is:** "A Java application and JVM are started from an image in a warmed-up form. The image is created from a running Java instance at arbitrary point of time ('checkpoint')… After the restore, Java runtime performance is also on-par with the one at the checkpoint." "CRaC implementation creates the checkpoint only if the whole Java instance state can be stored in the image. Resources like open files or sockets are cannot, so it is required to release them". — [CRaC/docs README](https://github.com/CRaC/docs/blob/master/README.md)
- **[V] Flow:**
  - checkpoint-enable with `java -XX:CRaCCheckpointTo=cr -jar app.jar`;
  - trigger with `jcmd app.jar JDK.checkpoint` ("success is always reported in jcmd output, problems are reported in the console of the application") or `jdk.crac.Core.checkpointRestore()`;
  - restore with `java -XX:CRaCRestoreFrom=cr`.

  "By the current implementation, the image is a directory with image files." It is based on CRIU; CRIU permissions may need `sudo chown root:root $JAVA_HOME/lib/criu; sudo chmod u+s $JAVA_HOME/lib/criu`. Restoring on a different CPU can fail: "You have to specify -XX:CPUFeatures=[...] together with -XX:CRaCCheckpointTo". — same source
- **[V] Published results** ("Time to first operation", ms, from a 2020 JDK 14 CRaC build on an i7-5500U laptop, Linux 5.7):

  | app | normal | restored |
  |---|---|---|
  | Spring Boot | 3,898 | 38 |
  | Micronaut | 1,001 | 46 |
  | Quarkus | 980 | 33 |
  | xml-transform | 4,352 | 53 |

  — [CRaC/docs startup.data](https://github.com/CRaC/docs/blob/master/startup.data) and startup.plot
- **[V] APIs:** `jdk.crac` lives in the CRaC JDK. `org.crac` is a compatibility library: "In compile-time, `org.crac` package totally mirrors `jdk.crac` and `javax.crac`. In runtime, org.crac uses reflection to detect CRaC implementation." Without an implementation, resources can still be registered but a "checkpoint request fails with an exception". — CRaC/docs README
- **[V] org.crac source (master, 2026-03-18):**
```java
public interface Resource {
    void beforeCheckpoint(Context<? extends Resource> context) throws Exception;
    void afterRestore(Context<? extends Resource> context) throws Exception;
}
public abstract class Context<R extends Resource> implements Resource {
    public static Context<Resource> getGlobalContext() { … }
    public static boolean isImplemented() { … }
    public abstract void beforeCheckpoint(Context<? extends Resource> context) throws CheckpointException;
    public abstract void afterRestore(Context<? extends Resource> context) throws RestoreException;
    public abstract void register(R resource);
}
```
  On master, `Core` (`getGlobalContext()`, `checkpointRestore()`) is `@Deprecated`: "Use `Context#getGlobalContext()` or `CRaCMXBean#checkpointRestore()`". The latest **released** artifact is `org.crac:crac:1.5.0` (metadata lastUpdated 2024-06-19; tags 1.4.0, 1.5.0), so the deprecation is unreleased as far as Maven Central shows. — [org.crac Resource.java](https://github.com/CRaC/org.crac/blob/master/src/main/java/org/crac/Resource.java), [Context.java](https://github.com/CRaC/org.crac/blob/master/src/main/java/org/crac/Context.java), [Core.java](https://github.com/CRaC/org.crac/blob/master/src/main/java/org/crac/Core.java), [Maven metadata](https://repo1.maven.org/maven2/org/crac/crac/maven-metadata.xml)
- **[V] File-descriptor policies:** "CRaC requires that the application closes all open files, network connections etc.".
  - **Configuration:** the system property `jdk.crac.resource-policies` points to a file of rules separated by `---`; types are `file`, `pipe`, `socket`, `filedescriptor`; the first matching rule wins.
  - **Actions:** "`error`: The default action, just print error and fail the checkpoint"; `ignore` (leave it to CRIU); `close` ("An attempt to use it after restore will fail"); `reopen` (files: reopen at the same position).
  - **Sockets:** match by `family`, `localAddress`/`remoteAddress`, `localPort`/`remotePort`, `localPath`/`remotePath`. For sockets "It is possible to use action `reopen`, too - this will close the socket before checkpoint, but the reopening part is not implemented, therefore will result in a runtime exception after restore."

  — [CRaC/docs fd-policies.md](https://github.com/CRaC/docs/blob/master/fd-policies.md)
- **[V] Best-practices doc sections:** "Implementing Resource as inner class"; "Component lifecycle": "unknown number of threads arriving randomly", "One or known number of periodically arriving threads", "Eventloop model". — [best-practices.md](https://github.com/CRaC/docs/blob/master/best-practices.md)
- **[V] Not in mainline:** `git log master` of openjdk/jdk has **0** commits whose subject mentions CRaC or coordinated restore. The project repo `openjdk/crac` has branches `crac` (default) and `crac-17`. — openjdk/jdk history; `git ls-remote https://github.com/openjdk/crac.git`
- **[S] Azul:** "full CRaC functionality is only available on Linux/x64 and Linux/ARM64, in version 17, 21, and 25 of Azul Zulu Builds of OpenJDK", available since April 2023; "Only the builds with '-crac-' in the filename include the CRaC functionality". Other platforms get "a simulated checkpoint/restore mechanism to be used for development and testing". Zing has CRaC for 17 and 21. From Zulu 25 GA and the Oct 2025 updates of 17/21, a "shorter post-restore warm-up when using G1". — [Azul: running CRaC](https://docs.azul.com/crac/usage/running-crac), [Azul: Zulu vs Zing CRaC](https://docs.azul.com/crac/azul-zulu-zing-crac-compared), [Azul release notes](https://docs.azul.com/core/release-notes)
- **[S] BellSoft:** CRaC-enabled Liberica JDK 17 and 21 for Linux x86_64 and AArch64, announced 6 Nov 2023 (initially "bare metal and in virtual machines", containers "still in development", "not yet verified by the TCK"). 2026 release notes (e.g. 17.0.19, April 2026) still include a CRaC section. — [BellSoft announcement](https://bell-sw.com/blog/bellsoft-releases-liberica-jdk-lts-17-and-21-with-coordinated-restore-at-checkpoint-crac-for-fast-startup/), [Liberica 17.0.19 release notes PDF](https://download.bell-sw.com/documentation/liberica-jdk/17.0.19+11-psu/release-notes-17.0.19+11-psu-liberica-jdk.pdf)
- **[S] AWS Lambda SnapStart hooks:**
  - "Lambda's runtime includes a customized CRaC context"; `beforeCheckpoint()` runs in **reverse registration order** and `afterRestore()` in **registration order**;
  - the docs show the `org.crac` dependency (1.4.0 in the example);
  - JVM restore plus `afterRestore()` must finish within **10 seconds** or you get `SnapStartTimeoutException`; `beforeCheckpoint()` work counts toward the init limit.

  — [AWS: SnapStart runtime hooks for Java](https://docs.aws.amazon.com/lambda/latest/dg/snapstart-runtime-hooks-java.html)
- **[L] Prototype matches the AWS ordering.** A three-resource simulated context (register pool, socket, cache) produced `[before:cache, before:socket, before:pool, --snapshot--, after:pool, after:socket, after:cache]`.

### Background facts (training knowledge) [TK]
- The jdk.crac global context documents the same ordering as AWS (reverse for checkpoint, forward for restore). This was not verified here: the openjdk/crac raw paths could not be resolved.
- On checkpoint failure the JVM throws `CheckpointException` carrying the individual failures as suppressed exceptions, and the process keeps running.
- Restored state hazards:
  - anything time- or entropy-dependent captured before the checkpoint: `SecureRandom` seeds, UUID generators, cached clocks, tokens and credentials, DNS caches, connection pools;
  - restoring one snapshot into many instances makes them share that state, hence AWS's guidance on uniqueness.
- Spring Framework 6.1+ / Boot 3.2+ support CRaC (`-Dspring.context.checkpoint=onRefresh`), as do Micronaut and Quarkus (`quarkus-crac` / the Lambda SnapStart integration).

### Inferences
- **Lab analogy:** CRaC is "hibernate the laptop, not reboot faster". Leyden is "reboot faster with a pre-sorted bookshelf". Native image is "replace the laptop with a calculator built for one job".

### Gaps
- Official SnapStart supported runtimes (whether Java 25 is supported) and architecture support could not be verified: AWS docs were blocked, and third-party summaries conflict on ARM64.
- The Azul and BellSoft current build matrices were not opened (blocked).

---

## Q8. Misconceptions (with evidence)

### Takeaway
Five common beliefs are false or only conditionally true:
- native is not always faster (peak throughput drops about 59% in Quarkus's own benchmark);
- CDS/AOT does not change semantics by design, and class-init order is unchanged (verified locally), but a real stale-JAR bug existed in 25.0.0–25.0.3;
- Leyden is not native image (open world, same JVM, cache can be ignored);
- CRaC fails on open sockets by default;
- startup matters well beyond serverless.

### Cited Findings
- **"Native image is always faster."**
  - In the Quarkus perf-lab table, native peak throughput is **5,411 tps vs 13,265 tps for JVM** ("~59% below JVM"), while TTFR is 581 ms vs 4,417 ms and RSS 95 vs 304 MiB [V]. — [building-native-image.adoc](https://github.com/quarkusio/quarkus/blob/main/docs/src/main/asciidoc/building-native-image.adoc)
  - GraalVM's own PGO doc explains AOT's disadvantage: "without profiling information, it is difficult to generate machine code of the same quality as a JIT compiler", and PGO is "not available in GraalVM Community Edition" [V]. — [PGO.md](https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/PGO.md)
- **"CDS/AOT changes program behaviour."**
  - [L] A test program logs static-initializer order (an eager class, a lazy holder) and a simulated CRaC sequence. Its output was **identical** with and without a JDK 21 AppCDS archive and with and without a JDK 25 AOT cache, while 8 of its classes were served from the archive. Archived classes are loaded and linked, not initialized early.
  - The man page frames incompatibilities as the cache being *disabled* (auto mode continues "without using the AOT cache"), not as behaviour change [V].
  - **The counter-example to teach:** JDK-8377932 (Q4), where 25.0.0–25.0.3 and 26.0.0–26.0.1 could run stale classes from an old cache [V][L].
- **"Leyden is the same as native image."**
  - The AOT cache is "an optimization feature" that the JVM may refuse to load; in auto mode it then runs normally [V].
  - JEP 544 keeps the JIT ("the JVM dynamically recompiles…") [S].
  - Quarkus calls Leyden a JVM mode that "keeps full JVM tooling (debuggers, profilers, JFR)" [V].
  - Native Image needs reachability metadata because of the closed world [V].
- **"CRaC works with any open socket."** The default fd policy is `error`, which fails the checkpoint. For sockets, "the reopening part is not implemented, therefore will result in a runtime exception after restore" [V]. — [fd-policies.md](https://github.com/CRaC/docs/blob/master/fd-policies.md)
- **"Startup only matters for serverless."**
  - Quarkus recommends Leyden for "Cold-start-sensitive but not millisecond-critical" services and native for "high-density container hosts where memory is the binding constraint" [V].
  - JEP 515's goal is **warm-up**, i.e. the slow period after every scale-out or rolling deploy [S].

### Inferences
- Other places startup matters: Kubernetes HPA scale-out under load (new pods are slow while traffic is highest), rolling deploys, readiness probes, CLI tools, batch jobs, and the CI test cycle (every `@QuarkusIntegrationTest` JVM). These are reasoning, not sourced claims.

### Gaps
- No published measurement was found of how much JEP 515 shortens warm-up for a typical service.

---

## Q9. Decision guide: AppCDS/Leyden, native image, CRaC, or nothing

### Takeaway
Default to the **JVM**. On JDK 25+ (≥ 25.0.4), add a **Leyden AOT cache** trained by integration tests: it is low-risk, needs no code changes, and in Quarkus 3.40 it is one property. On JDK 21, use **AppCDS** (dynamic or AutoCreate).
- Choose **native** when cold start in milliseconds or RSS density is the binding constraint and the team accepts slower builds, metadata upkeep and lower peak throughput.
- Choose **CRaC/SnapStart** when you need instant *warmed* performance and control the runtime (Lambda, or Azul/Liberica CRaC builds on Linux with CRIU privileges) and can make resources checkpoint-safe.
- Choose **nothing** for long-running services where nobody waits on startup.

### Decision table (assembled from the cited findings above; cells are judgments unless marked)

| Constraint | Nothing | AppCDS (JDK 21) | Leyden AOT cache (JDK 25+, ideally 26+ for ZGC) | Native image | CRaC / SnapStart |
|---|---|---|---|---|---|
| Code changes needed | none | none | none (Quarkus: `quarkus.package.jar.aot.enabled=true`) [V] | reflection/proxy/resource metadata; build-time init fixes [V] | `Resource` hooks for sockets, files, pools [V] |
| Startup gain (this session, 300-class app) | — | ~2× CPU [L] | ~6× CPU, TTFR −38% [L] | ms-level start (Quarkus table: TTFR 581 ms vs 4,417 ms) [V] | ~100× in CRaC's 2020 numbers [V] |
| Peak throughput | baseline | same | ~7% below JVM in Quarkus perf lab [V] | ~59% below JVM in Quarkus perf lab [V] | same as JVM (warmed) |
| RSS | baseline | small gain [L] | 240 vs 304 MiB (Quarkus) [V]; 42 vs 64 MiB (this app) [L] | 95 MiB (Quarkus) [V] | similar to warmed JVM |
| Build/ops cost | none | archive step | training run; image +~198 MB (Quarkus) [V]; same JDK build, same flags, same classpath [V] | 3–10 min, 4–8 GB RAM builds [V] | CRIU privileges, vendor JDK, snapshot storage, uniqueness hygiene |
| GC caveats | — | — | JDK 25: ZGC needs a ZGC-built cache, small gain [L]; JDK 26+: JEP 516 any GC [V] | Serial default; G1 only Oracle GraalVM on Linux [V] | Azul notes G1 restore warm-up improvements [S] |
| Tooling | full | full | full JVM tooling [V] | native tools; limited agents | full JVM after restore |

### Inferences
- For the target learner (Quarkus in containers), the realistic sequence is:
  1. measure TTFR and RSS honestly (`ps`, not `docker stats`);
  2. turn on the Leyden cache with integration-test training and a pinned JDK patch level;
  3. only then evaluate native for scale-to-zero or density.
- **Pitfalls to pre-empt:**
  - mismatched `--add-modules` (e.g. JFR) [V];
  - JVMTI agents (APM tools) disabling the cache [V];
  - `AOTMode=required` in production [V];
  - the stale-cache bug before 25.0.4 [V].

### Gaps
- No vendor guidance was found that compares Leyden and CRaC head-to-head.

---

## Q10. Lab exercises gradable with JUnit (deterministic), with verified expected outcomes

### Takeaway
Five deterministic labs are feasible:
1. holder-idiom lazy initialization (assert init order through a log);
2. counting classes defined by an isolated class loader;
3. building and validating a `reachability-metadata.json` (reflection plus proxy) against the v1.2.0 shape;
4. a simulated CRaC `Resource` lifecycle (reverse/forward order, closed-before-checkpoint invariant);
5. a process-level CDS lab that asserts *counts of `source: shared objects file` lines*, never timings.

Prototypes of 1, 2 and 4 were run locally.

### Cited Findings
- **[L] Lab 1, holder idiom.** Prototype: `Eager` holds a static table built in `<clinit>`; `Lazy` exposes `name()`, and its table lives in a nested `Holder`. Calling `Eager.name(); Lazy.name();` then `Lazy.table()` logged `[Eager.<clinit>, Lazy.<clinit>, -- names done --, Lazy.Holder.<clinit>]`. So the holder's initializer runs only on first `table()`. The output was identical under JDK 21 AppCDS and the JDK 25 AOT cache [L].
- **[L] Lab 4, CRaC simulation.** Registering pool, socket and cache, then `checkpointRestore()`, gave `[before:cache, before:socket, before:pool, --snapshot--, after:pool, after:socket, after:cache]`. This matches AWS's documented ordering [S].
- **[L] Lab 2 pitfall.** A child-first counting `ClassLoader` that defines classes from the build directory recorded `[lab.Proto$Lazy, lab.Proto, lab.Proto$Resource, lab.Proto$1Counting]` after initializing only `Proto$Lazy`.
  - `Lazy.<clinit>` referenced the outer class's static `LOG`, which loaded `Proto`, and linking/verifying `Proto` pulled in more classes. Expected sets must come from the reference solution.
  - Fixture classes should be self-contained (no outer-class references); compare **sets of names defined by your loader**, never global counts (JDK internals vary by version).
  - Also: reflective calls on package-private nested classes need `setAccessible(true)`; and resolving class files relative to a JAR code-source URL needs `jar:` URLs (my prototype's directory-relative URL failed when run from a JAR).
- **[V] Lab 3 schema facts to assert:**
  - top-level keys ⊆ {`reflection`, `resources`, `foreign`, `comment`}, with no `proxy`, `jni` or `serialization` at top level in v1.2.0;
  - a proxy is `{"type": {"proxy": [<ordered FQCNs>]}}`;
  - serialization is `"serializable": true`;
  - methods are `{"name": …, "parameterTypes": [FQCNs]}`;
  - conditions are `{"typeReached": FQCN}`.

  — [schema v1.2.0](https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/assets/reachability-metadata-schema-v1.2.0.json)
- **[L] Lab 5 assertions that held here.**
  - With `-Xshare:off`, there are 0 `shared objects file` lines.
  - With default CDS, many: 875 on JDK 21 and 990 on JDK 25 for the sample app. Assert `> 500`, not an exact number.
  - After `-XX:ArchiveClassesAtExit=app.jsa`, a run with `-XX:SharedArchiveFile=app.jsa` serves **all 301 app classes** from the archive.
  - On JDK 25+ (`assumeTrue(Runtime.version().feature() >= 25)`), `-XX:AOTCacheOutput` then `-XX:AOTCache` with `-Xlog:aot` prints `Opened AOT cache`, and app classes come from "shared objects file".

### Inferences (lab specs for writers)
- **Lab A, "Make it lazy" (JUnit 5, any JDK 21+).**
  - Given a `CurrencyTable` whose static initializer builds a 10k-entry map and appends `"table-built"` to a test-visible `InitLog`, refactor (holder idiom) so `CurrencyTable.version()` does not trigger the build but `CurrencyTable.lookup("EUR")` does.
  - Tests: (1) after `version()`, `InitLog` contains no `"table-built"`; (2) after `lookup`, it contains `"table-built"` exactly once; (3) concurrent first `lookup` from 8 threads still yields exactly one `"table-built"` (JLS class-init locking).
  - Each test runs in a **fresh class loader**, because class init happens once per loader: use the Lab B loader, or one Gradle `forkEvery` test JVM per test.
- **Lab B, "Who loaded what?"**
  - Implement `CountingClassLoader extends ClassLoader` (parent = platform loader; defines only `lab.fixtures.*` from bytes) with `List<String> defined()`.
  - Tests: `Class.forName("lab.fixtures.A", false, cl)` defines `[A]` only (no init); with `initialize=true`, A's static references define `[A, B]`; calling a method that uses `C` adds `C`. Expected sets come from the solution, run on the same JDK.
  - Variant: `ManagementFactory.getClassLoadingMXBean().getTotalLoadedClassCount()` deltas are *not* deterministic across JDKs. Use them in a demo, not a test.
- **Lab C, "Write the metadata".**
  - Student implements `MetadataWriter.reflection(Class<?> c, String... methods)` and `MetadataWriter.proxy(Class<?>... interfaces)`, returning a `Map`/JSON string.
  - Tests parse it (Jackson/Gson if the lab has one, or a tiny hand-rolled check) and assert: top-level key set; `type.proxy` order equals the argument order; `parameterTypes` are fully qualified (`java.lang.String`, not `String`); interfaces-only check for proxies (reject classes, as `java.lang.reflect.Proxy` does).
  - Optional: run the real `Proxy.newProxyInstance` to show the same interface list works on HotSpot.
- **Lab D, "Checkpoint-safe pool".**
  - Provide `interface Resource { void beforeCheckpoint() throws Exception; void afterRestore() throws Exception; }` and a `FakeContext` that refuses to "snapshot" if any registered `FakeSocket` is open (mirrors the `error` fd policy).
  - Student makes `ConnectionPool` register itself, close its sockets in `beforeCheckpoint`, and reconnect in `afterRestore`.
  - Tests: ordering (reverse/forward); `snapshot` fails with `IllegalStateException` (or a custom `CheckpointException` with suppressed causes) if the pool doesn't close; after restore, `pool.borrow()` returns a *new* socket generation; a `beforeCheckpoint` that throws aborts the checkpoint and leaves other resources restored.
- **Lab E (process lab, optional), "Prove the archive is used".** A JUnit test uses `ProcessBuilder` to run the lab's own JAR with `-Xlog:class+load` under `-Xshare:off`, default, and `-XX:ArchiveClassesAtExit` then `-XX:SharedArchiveFile`, and asserts the `source:` counts above. Count-based, so deterministic; never assert milliseconds.

### Gaps
- Labs were prototyped as plain `main` programs, not as JUnit/Gradle modules in `labs/`.
- JUnit timing and fork configuration for one-loader-per-test is a writer task.

---

## Teaching notes

### Misconceptions to address explicitly (with the one-line fix)
- **"Native is always faster."** Faster to *start* and smaller; slower at *peak* (−59% tps in Quarkus's perf lab) unless PGO (Oracle GraalVM only) narrows it.
- **"CDS/AOT changes what my code does."** It changes *where class bytes come from*, not init order (demo Lab 1 under a cache). Caveat: pin JDK ≥ 25.0.4/26.0.2 (JDK-8377932 stale-JAR bug) and rebuild the cache with every JAR.
- **"Leyden = native image."** Leyden is the same JVM with a cache it may ignore; native image is a different runtime with a closed world.
- **"An AOT cache flag typo is harmless."** A missing `-XX:AOTCache` file also disables the *default* CDS archive (0 archived classes [L]), so startup gets *worse* than no flag.
- **"Use `-XX:AOTMode=on/required` to be safe in prod."** It is a fail-fast debugging aid; an APM agent's ClassFileLoadHook can then stop your pod from starting (JDK 27 man page).
- **"CRaC can snapshot anything."** Open sockets fail the checkpoint by default; socket `reopen` isn't implemented.
- **"docker stats shows my memory."** Quarkus explicitly says not to use it; use `ps -o rss` / `/proc/<pid>/status` / `smaps_rollup`.
- **"NMT committed = memory used."** 288 MiB committed vs ~50 MiB RSS in this session's run.
- **"CDS saves RAM across containers."** With randomized relocation (default since JDK 21's `ArchiveRelocationMode=1`), most mapped archive pages become private dirty (11.5 of 14.4 MiB [L]). Sell it for startup.
- **"Startup only matters for Lambda."** Scale-out, rolling deploys, CI integration tests, CLIs.

### Analogies
- **Class loading without CDS:** every morning you unpack, read and fact-check every book before shelving it. **CDS** is a pre-shelved bookcase you wheel in (memory-mapped). **Leyden AOT** is the same bookcase with the cross-references already resolved and your reading habits (profiles) noted on sticky notes; JDK 28 adds pre-written summaries (compiled code).
- **Native image:** printing only the pages you proved you'll read into one booklet (closed world). Any page you look up dynamically must be on the list (metadata).
- **CRaC:** hibernate the laptop with all apps warmed, then wake it. Close network connections before hibernating.
- **Holder idiom:** a locked cupboard (nested class) that is opened only the first time someone asks for what's inside.

### Demo ideas (with expected outcomes from this session)
1. **Histogram of class sources:** `java -Xlog:class+load -cp app.jar demo.Main | sed -E 's/.*source: //' | sort | uniq -c | sort -rn | head`. Expect "shared objects file" ≈ 875 (JDK 21) / 990 (JDK 25), app.jar 301, `jrt:` small. With `-Xshare:off`, jrt ≈ 911 and 0 shared.
2. **AppCDS on JDK 21:** `-XX:ArchiveClassesAtExit=app.jsa`, then `-XX:SharedArchiveFile=app.jsa`. Expect shared ≈ 1,409, app.jar 0, hidden classes 316 → 3, CPU roughly halved.
3. **Leyden on JDK 25:** `java -XX:AOTCacheOutput=app.aot -cp app.jar demo.Main`. Show the forked child's `Picked up JAVA_TOOL_OPTIONS … -XX:AOTMode=create` line and `AOTCache creation is complete`. Then `-XX:AOTCache=app.aot -Xlog:aot` shows `Opened AOT cache`. Expect ~6× lower CPU on this app.
4. **Fail-fast vs auto:** `-XX:AOTCache=nope.aot` prints `[error][aot] Specified AOT cache not found` but the app runs; with `-XX:AOTMode=on` (25/26) or `required` (27) it exits. (Mode `on` was not tested with a missing file here; the man page says it exits.)
5. **ZGC on 25 vs 26:** a G1-built cache with `-XX:+UseZGC` shows "CDS will be disabled" and 0 shared classes. A ZGC-built cache works partially. On JDK 26 rerun to show JEP 516 (not run here).
6. **Stale cache (JDK 25.0.0–25.0.3 only):** cache "version ONE", rebuild the jar to "version TWO", run with the old cache. It prints ONE. On ≥ 25.0.4 it should warn and print TWO (not verified locally).
7. **Memory truth:** run the HttpServer app; compare `ps -o rss`, `/proc/<pid>/smaps_rollup` Pss, and `jcmd <pid> VM.native_memory summary` (start with `-XX:NativeMemoryTracking=summary`). Point at heap committed ≫ heap resident.
8. **Time-to-first-request:** poll `/hello` from a script. Expect JDK 25 default ≈ 218 ms vs AOT ≈ 136 ms median on this VM; absolute values vary by machine.

### Exercise ideas (with expected outcomes)
- Labs A–E in Q10.
- **Quiz items:**
  - "Which JDK added `-XX:AOTCacheOutput`?" (25, JEP 514)
  - "Which release made the AOT cache usable with ZGC?" (26, JEP 516)
  - "What is the JDK 27 name for `-XX:AOTMode=on`?" (`required`)
  - "Where must `reachability-metadata.json` live?" (`META-INF/native-image/<groupId>/<artifactId>/`)
  - "What does CRaC do by default with an open file?" (`error`: fail the checkpoint)
  - "Order of `beforeCheckpoint` calls?" (reverse registration)

### Version-pinning advice for lesson writers
- State JDK versions explicitly in every Leyden command block: one-step `AOTCacheOutput` needs 25+; `AOT.end_recording` needs 26+; `required` needs 27+; AOT code compilation is JDK 28 (in development as of Nov 2026).
- For Quarkus, write against **3.40.x**: properties `quarkus.package.jar.aot.enabled`, `.phase`, `.type=app-cds`, `.additional-recording-args` (the last appears only in main docs; check it exists in 3.40 before using). Note that 4.0 drops the legacy JSON files.
- Recommend JDK **25.0.4+** (or 26.0.2+ / 27) whenever an AOT cache is used.

---

## Verified URLs
Pages and files actually fetched this session (via curl, `git clone` or `git ls-remote`; GitHub HTML views were blocked, so GitHub links point at files read from clones):
- https://raw.githubusercontent.com/openjdk/jdk/jdk-21-ga/src/java.base/share/man/java.1
- https://raw.githubusercontent.com/openjdk/jdk/jdk-24-ga/src/java.base/share/man/java.md
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/man/java.md
- https://raw.githubusercontent.com/openjdk/jdk/jdk-26-ga/src/java.base/share/man/java.md
- https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/java.base/share/man/java.md
- https://raw.githubusercontent.com/openjdk/jdk/master/src/java.base/share/man/java.md
- https://raw.githubusercontent.com/openjdk/jdk/jdk-21-ga/src/hotspot/share/cds/cds_globals.hpp (and the same path at jdk-24-ga, jdk-25-ga, jdk-26-ga, jdk-27-ga, master)
- https://raw.githubusercontent.com/openjdk/jdk/jdk-26-ga/src/jdk.jcmd/share/man/jcmd.md
- https://github.com/openjdk/jdk (full commit history via `git clone --filter=tree:0`), including commits 41a2d49, dede353, e3f85c9, c865644, 65f1ad6, 42d6307, 630b831, 8663770, f6fa653, d544fca, b41ba3a (with diff), 1228b2f, 437342b, 57b516d, 72dc572
- https://github.com/openjdk/jdk25u and https://github.com/openjdk/jdk26u (commit histories and tags)
- https://www.oracle.com/java/technologies/javase/24-relnote-issues.html
- https://www.oracle.com/java/technologies/javase/25-relnote-issues.html
- https://www.oracle.com/java/technologies/javase/26-relnote-issues.html
- https://www.oracle.com/java/technologies/javase/27-relnote-issues.html
- https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/ReachabilityMetadata.md (clone at d1b9545)
- https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/assets/reachability-metadata-schema-v1.2.0.json
- https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/assets/reachability-metadata-schema-v1.1.0.json
- https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/ClassInitialization.md
- https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/AutomaticMetadataCollection.md
- https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/PGO.md
- https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/PGO-Basic-Usage.md
- https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/MemoryManagement.md
- https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/BuildOptions.md
- https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/DebugInfo.md
- https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/DebuggingAndDiagnostics.md
- `git ls-remote --tags https://github.com/oracle/graal.git`
- https://github.com/quarkusio/quarkus/blob/main/docs/src/main/asciidoc/aot.adoc (clone at ff19f58b)
- https://github.com/quarkusio/quarkus/blob/main/docs/src/main/asciidoc/writing-native-applications-tips.adoc
- https://github.com/quarkusio/quarkus/blob/main/docs/src/main/asciidoc/building-native-image.adoc
- https://github.com/quarkusio/quarkus/blob/main/docs/src/main/asciidoc/performance-measure.adoc
- https://github.com/quarkusio/quarkus/blob/main/docs/src/main/asciidoc/writing-extensions.adoc
- https://github.com/quarkusio/quarkus/blob/main/docs/src/main/asciidoc/getting-started.adoc
- https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/docs/src/main/asciidoc/aot.adoc
- https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/docs/src/main/asciidoc/writing-native-applications-tips.adoc
- https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/docs/src/main/asciidoc/building-native-image.adoc
- https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/docs/src/main/asciidoc/aws-lambda-snapstart.adoc
- https://raw.githubusercontent.com/quarkusio/quarkus/main/core/runtime/src/main/java/io/quarkus/runtime/annotations/RegisterForReflection.java
- https://raw.githubusercontent.com/quarkusio/quarkus/main/core/runtime/src/main/java/io/quarkus/runtime/annotations/RegisterForProxy.java
- https://repo1.maven.org/maven2/io/quarkus/quarkus-core/maven-metadata.xml and https://repo1.maven.org/maven2/io/quarkus/quarkus-core/ (directory listing with dates)
- https://repo1.maven.org/maven2/org/crac/crac/maven-metadata.xml
- https://github.com/CRaC/docs (clone at f528f3d): README.md, fd-policies.md, best-practices.md, startup.data, startup.plot
- https://github.com/CRaC/org.crac (clone at a8701a7): src/main/java/org/crac/Resource.java, Context.java, Core.java; `git ls-remote --tags`
- `git ls-remote https://github.com/openjdk/crac.git`
- https://github.com/adoptium/temurin25-binaries/releases/download/jdk-25%2B36/OpenJDK25U-jdk_x64_linux_hotspot_25_36.tar.gz.sha256.txt (checksum used to verify the local JDK 25)

Cited but **not fetched** (search-summary only, tagged [S]): openjdk.org/jeps/483, /515, /516, /8315737, /8335368; infoq.com Java 24 Leyden article and Sep 2026 roundup; docs.azul.com CRaC pages; bell-sw.com announcement and Liberica release-notes PDF; docs.aws.amazon.com SnapStart runtime hooks.

**Blocked in this session:** openjdk.org, docs.oracle.com, graalvm.org, quarkus.io, inside.java, mail.openjdk.org, bugs.openjdk.org, cr.openjdk.org, docs.azul.com, bell-sw.com, docs.aws.amazon.com, foojay.io, jdk.java.net, github.com HTML pages, api.github.com.
