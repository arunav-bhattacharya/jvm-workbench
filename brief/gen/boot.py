import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")

INTRO = """By the end of this track you can say where a JVM's start-up time and memory go, and measure both the way a load balancer and a container limit see them: time to first request from outside the process, and RSS from the OS. You can build and check a class data sharing archive on JDK 21 and a Project Leyden AOT cache on JDK 25, and you know the traps that make them silently useless, or, on JDK 25 builds before 25.0.4, run stale code. You can explain what GraalVM native image's closed world costs, write its reachability metadata for reflection and proxies, and spot static initializers that break when the build runs them. You can write CRaC checkpoint hooks in the right order, and pick between doing nothing, AppCDS, the AOT cache, native image and CRaC for a given service.

You need no background on any of this; lesson 1 starts from what happens between typing `java` and the first line of `main`. Install JDK 25, at least 25.0.4: earlier JDK 25 builds can run old classes from an AOT cache after the JAR changes. The Leyden flags need JDK 24 or 25 and say so wherever they appear. Native image needs GraalVM or Mandrel, and CRaC needs a vendor build such as Azul Zulu's CRaC builds on Linux; those steps are marked optional, and everything else runs on a plain JDK.

The labs live in `labs/startup`, one package per lesson (`workbench.startup.l01` to `l04`). Lessons 1 and 3 are Java, lessons 2 and 4 Kotlin, and every sample and demo comes in both languages. Start-up numbers are noisy, so no test measures time or counts loaded classes. The tests load your classes in fresh class loaders and compare exact sets of class names, check JSON metadata against the GraalVM schema and against what the code really does, and drive a simulated checkpoint. Many demos start a second JVM with the flags you pass in `-Pargs`, because start-up has to be measured on a fresh process. A few Try-its run `java` directly on a JDK 25 against `startup/build/classes/java/demo`. Run `./gradlew :startup:test --tests 'workbench.startup.lNN.*'` from `labs/` until it passes, and `./gradlew :startup:solutionTest` to run the same tests on the reference answers."""

CHEAT = """## Measure first

| Question | Command or tool |
|---|---|
| Where did each class come from? | `java -Xlog:class+load ...`: `source: shared objects file` (archive), `jrt:/` (parsed from the JDK), `file:` (class path), a class name (hidden class) |
| How long did VM creation take? | `-Xlog:startuptime`, last line `Create VM, 0.03 secs`. Nothing about your code |
| What does the user wait for? | Time to first request: launch the process, poll the endpoint from outside until 200 |
| What is the footprint? | RSS: `ps -o pid,rss,args -p <pid>`, `/proc/<pid>/status` (`VmRSS`, `RssAnon`, `RssFile`). Not `docker stats`, not heap used |
| Where inside the JVM did memory go? | `-XX:NativeMemoryTracking=summary`, then `jcmd <pid> VM.native_memory summary`. Committed is not resident |

## Class loading and initialization

- Loading parses a class into metaspace; linking verifies and prepares it; `<clinit>` runs on first active use (`new`, a static call, a non-constant static field, initializing reflection, a subclass).
- Holder idiom: put the expensive static field in a private nested class. Kotlin: a private nested `object`, or `by lazy`. A companion object's properties are static fields of the outer class and are built with it.

## Class data sharing (CDS)

| Kind | Commands | Since |
|---|---|---|
| Default archive | on unless `-Xshare:off`; `lib/server/classes.jsa` | JDK 12 |
| Dynamic AppCDS | `-XX:ArchiveClassesAtExit=app.jsa`, then `-XX:SharedArchiveFile=app.jsa` | JDK 13 |
| Static AppCDS | `-Xshare:off -XX:DumpLoadedClassList=app.classlist`, `-Xshare:dump -XX:SharedClassListFile=app.classlist -XX:SharedArchiveFile=app.jsa`, then `-XX:SharedArchiveFile=app.jsa` | |
| Auto-created | `-XX:+AutoCreateSharedArchive -XX:SharedArchiveFile=app.jsa` (not for read-only containers) | JDK 19 |

Rules: JARs only (no class directories), same class path or a prefix of it, a changed JAR is rejected. CDS saves parsing and verifying; it does not run static initializers or warm the JIT.

## Leyden AOT cache

| JDK | What you get |
|---|---|
| 24 | JEP 483: `-XX:AOTMode=record -XX:AOTConfiguration=app.aotconf`, then `-XX:AOTMode=create ... -XX:AOTCache=app.aot`, then `-XX:AOTCache=app.aot` |
| 25 | JEP 514: one step, `-XX:AOTCacheOutput=app.aot`. JEP 515: method profiles |
| 26 | JEP 516: full cache with any GC, including ZGC |
| 27 | `-XX:AOTMode=required` is the name for `on` |
| 28 (in development) | JEP 544: compiled code in the cache |

- Require **JDK 25.0.4+ or 26.0.2+** (JDK-8377932: earlier builds ran stale classes after the JAR changed). Rebuild the cache with every JAR, in the same build step.
- A cache is tied to the class path, the exact JDK build, OS and CPU, the GC (on JDK 25) and module options. A cache the JVM can't use leaves no archive at all, not even the default one.
- Production: no `AOTMode` (the default `auto` falls back safely). CI: `-XX:AOTMode=on` (`required` on 27+) with `-Xlog:aot`, looking for `Opened AOT cache`.
- Quarkus 3.40: `quarkus.package.jar.aot.enabled=true` trains during `@QuarkusIntegrationTest`s; run `java -XX:AOTCache=app.aot -jar quarkus-run.jar`. JDK 21: `quarkus.package.jar.aot.type=app-cds`.

## GraalVM native image

```json
{
  "reflection": [
    { "condition": { "typeReached": "com.acme.EventDecoder" },
      "type": "com.acme.PaymentAuthorized",
      "methods": [ { "name": "<init>", "parameterTypes": ["java.lang.String", "long"] },
                   { "name": "paymentId", "parameterTypes": [] } ] },
    { "type": { "proxy": ["com.acme.CardIssuerClient", "java.lang.AutoCloseable"] } }
  ]
}
```

- File: `META-INF/native-image/<groupId>/<artifactId>/reachability-metadata.json`. Schema v1.2.0 top level: `reflection`, `resources`, `foreign`, `comment` only.
- Proxies are ordered interface lists; serialization is `"serializable": true`; constant arguments to `Class.forName` need no entry.
- Tracing agent: `java -agentlib:native-image-agent=config-output-dir=<dir> ...`. Strict mode: `--exact-reachability-metadata`, `-XX:MissingRegistrationReportingMode=Exit`.
- Quarkus initializes all classes at build time. Fix with `quarkus.native.additional-build-args=--initialize-at-run-time=a.B\\\\,c.D`.
- Quarkus: `@RegisterForReflection` (`targets` for library classes, `ignoreNested`, `serialization`), `@RegisterForProxy(targets = ...)` in order, `quarkus.native.resources.includes`.

## CRaC

```bash
java -XX:CRaCCheckpointTo=cr -jar app.jar   # start, warm it up
jcmd app.jar JDK.checkpoint                 # check the app's console: jcmd always says success
java -XX:CRaCRestoreFrom=cr                 # restore, warm
```

- Hooks: `org.crac.Resource` (`beforeCheckpoint`, `afterRestore`), `Core.getGlobalContext().register(r)` in org.crac 1.5.0. Keep `r` in a field: the context holds weak references.
- Order: checkpoint in reverse registration order, restore in registration order. Everyone is told even if one throws; failures arrive as suppressed exceptions on `CheckpointException`.
- Open files and sockets fail the checkpoint (policy `error`). Socket `reopen` is not implemented. Recreate per-instance ids and tokens after restore.
- Builds: Azul Zulu 17/21/25 Linux `-crac-` builds, BellSoft Liberica 17/21 CRaC. Not in mainline OpenJDK. Lambda SnapStart uses the same hooks.

## Choosing

| Constraint | Pick |
|---|---|
| Long-running, rarely restarted, nobody waits on start-up | nothing |
| JDK 21, no code changes | dynamic AppCDS built with the image |
| JDK 25.0.4+, no code changes, full peak throughput | AOT cache trained by integration tests |
| Milliseconds to start or memory per instance is the limit | native image (about 59% lower peak in Quarkus's benchmark) |
| Must start fast and warm, runtime under your control | CRaC or Lambda SnapStart, with hooks |"""

RECAP = [
 "Start-up repeats the same work on every launch: create the VM, load, parse and verify about 1,500 classes for a 300-class app, run static initializers, interpret until the JIT has profiles, and run the framework's start-up.",
 "Measure what users see: time to first request from outside, and RSS from `ps` or `/proc`. `Create VM`, the framework's `started in`, NMT committed memory and `docker stats` each miss part of it.",
 "`<clinit>` runs on first active use. The holder idiom (a nested class or Kotlin nested `object`) keeps expensive static work off the start-up path; a Kotlin companion object does not.",
 "CDS maps pre-parsed classes from an archive: the default one for JDK classes, AppCDS for yours. It saves parsing and verification, not initialization or JIT warm-up.",
 "The AOT cache (JDK 24+, one step on JDK 25) adds linked classes, resolved call sites and profiles. Require JDK 25.0.4+ and rebuild it with every JAR; check it in CI, run production in the default mode.",
 "A training run, an AOT cache and the native-image tracing agent all see only the code paths you exercise, so drive them with production-like traffic.",
 "Native image starts in milliseconds and uses less memory, but has no JIT (lower peak), needs metadata for reflection and proxies, and runs static initializers at build time in Quarkus.",
 "CRaC restores a warm process from an image. Close sockets and files before the checkpoint, reopen them after, mind the hook order and weak references, and recreate per-instance state.",
 "Default to the JVM with an AOT cache or AppCDS; choose native or CRaC only when start-up or memory per instance is the real limit and you accept their costs."
]

QUIZ = [
 {"q": "Your new Quarkus pod logs `started in 0.9s`, but the load balancer only sends it traffic 2.4 s after the container starts. Which number should you work on, and how do you measure it?",
  "options": ["The 0.9 s, read from the log, because it is the framework's start-up", "The `Create VM` time from `-Xlog:startuptime`", "Time from launch to the first 200 from the readiness endpoint, measured from outside", "The time until C2 has compiled the hot methods"],
  "answer": 2,
  "from": "boot-01",
  "why": "Only the outside clock includes everything the load balancer waits for: the launcher, VM creation, class loading, framework start and the first request. The framework's log line starts late and stops early, and `Create VM` stops before your code runs."},
 {"q": "In Kotlin, `class FxRates { companion object { val rates = loadRates(); fun source() = \"ecb\" } }`. A health check calls `FxRates.source()`. Is `loadRates()` called?",
  "options": ["No, companion objects are lazy", "Yes: `rates` is a static field of `FxRates`, filled when `FxRates` is initialized, which this first call triggers", "Only on the first access to `rates`", "Only if `rates` is declared `const`"],
  "answer": 1,
  "why": "Kotlin compiles companion properties to static fields of the outer class and initializes them in its `<clinit>`. Use a private nested `object` holding `rates`, or `by lazy`, to build them only when needed."},
 {"q": "NMT reports 290 MB committed, 216 MB of it heap, while `VmRSS` is 53 MB. What explains the gap?",
  "options": ["NMT double-counts the heap", "The JVM leaked native memory", "RSS doesn't include the Java heap", "Committed memory has been requested from the OS, but most of it, such as a fresh heap, has never been touched, so it is not resident"],
  "answer": 3,
  "why": "Pages become resident only when something writes or reads them. A container is limited by resident memory, so RSS is the footprint; NMT tells you which part of the JVM asked for what."},
 {"q": "With `-Xshare:off`, `java -version` loads 440 classes and 0 come from an archive; without it, 405 load and all 405 are shared. Why did start-up get slower with sharing off?",
  "options": ["Each class now has to be found, parsed and verified by the JVM instead of being mapped ready-made from `classes.jsa`", "The JIT is disabled with sharing off", "The heap is smaller", "The JVM runs every static initializer twice"],
  "answer": 0,
  "from": "boot-02",
  "why": "The default CDS archive holds the JVM's internal form of about 1,300 JDK classes. Without it every class goes through the full load path, and the JVM generates at run time some classes the archive would have supplied, hence 440 instead of 405."},
 {"q": "A pipeline rebuilt `pay.jar` with a fix and reused last week's `app.aot`. Production runs JDK 25.0.2. What do you expect?",
  "options": ["A warning, then the fixed code without the cache", "The JVM refuses to start", "Possibly last week's classes, served from the cache with no error (JDK-8377932)", "The fixed code, with the full speed-up"],
  "answer": 2,
  "why": "JDK 25.0.0 to 25.0.3 (and 26.0.0 to 26.0.1) did not check application JARs against the cache. 25.0.4 and later warn and run without the cache. Pin 25.0.4+ and rebuild the cache with every JAR."},
 {"q": "Someone adds `-XX:AOTCache=/srv/app.aot` to every pod's `JAVA_TOOL_OPTIONS`, but the file isn't in the image. What happens to start-up?",
  "options": ["Nothing changes: the JVM ignores the flag", "It gets slower than with no flag: the JVM runs with no archive at all, not even the default CDS archive", "The JVM refuses to start", "The JVM writes the cache at exit"],
  "answer": 1,
  "why": "In the default `auto` mode the JVM prints an error and carries on, but with zero archived classes; in this track's run, a one-class program went from 542 shared classes to 0. Only `-XX:AOTMode=on` or `required` makes it exit, and only `AOTCacheOutput` writes a cache."},
 {"q": "Which entry correctly registers a JDK dynamic proxy over `com.acme.LedgerClient` and `java.io.Closeable` in schema v1.2.0?",
  "options": ["`{\"proxy\": [[\"com.acme.LedgerClient\", \"java.io.Closeable\"]]}` at the top level", "`{\"reflection\": [{\"type\": \"com.acme.LedgerClient\", \"allPublicMethods\": true}]}`", "A `proxy-config.json` next to the file", "`{\"reflection\": [{\"type\": {\"proxy\": [\"com.acme.LedgerClient\", \"java.io.Closeable\"]}}]}`"],
  "answer": 3,
  "from": "boot-03",
  "why": "In v1.2.0 a proxy is a reflection entry whose type is an object with an ordered `proxy` list. The top level allows only `reflection`, `resources`, `foreign` and `comment`, and Quarkus 4.0 doesn't support the legacy separate files. Registering the interface itself doesn't define the proxy class."},
 {"q": "A Quarkus native service has `static final String NODE_ID = UUID.randomUUID().toString().substring(0, 8);` in an ordinary class, used to prefix ledger entry ids. Assuming the build succeeds, what do pods started from the same binary see?",
  "options": ["The same `NODE_ID` in every pod, computed once during the build", "A different `NODE_ID` per pod", "`null`", "A different value on every read"],
  "answer": 0,
  "why": "Quarkus initializes all classes at build time by default, so the initializer runs once in the build and its result is stored in the image heap. Per-instance values belong in code that runs at start-up, or in a class marked `--initialize-at-run-time`."},
 {"q": "A service registers its ledger pool first and its Kafka consumer second with the CRaC global context. The consumer forgets to close its broker connection. What happens on `jcmd app.jar JDK.checkpoint`?",
  "options": ["jcmd reports an error and the JVM exits", "The checkpoint fails with the default `error` policy; the restore hooks run in registration order, and the app's console, not jcmd, shows the error", "The image is written and the connection is reopened after restore", "Only the consumer's hooks run"],
  "answer": 1,
  "from": "boot-04",
  "why": "Open sockets fail the checkpoint by default. The context still notifies everyone (consumer, then pool, before; pool, then consumer, after), collects the problems in a `CheckpointException`, and the process keeps running. jcmd prints success either way."},
 {"q": "An internal platform runs 120 small, lightly loaded Quarkus services per node, and memory per instance is what limits how many fit. Slower CI builds are acceptable. Which option fits best?",
  "options": ["The JVM with no changes", "An AOT cache on JDK 25", "A native image for each service", "CRaC for each service"],
  "answer": 2,
  "why": "Density is native image's strongest case: in Quarkus's benchmark, 95 MiB RSS against 304 MiB in JVM mode and 240 MiB with the AOT cache. Its lower peak throughput matters little for lightly loaded services. CRaC restores a full warm JVM, so it doesn't cut memory."}
]

T = {"id": "boot", "intro": INTRO, "cheatsheet": CHEAT, "recap": RECAP, "quiz": QUIZ}
out = ROOT / "content/tracks/boot.json"
out.write_text(json.dumps(T, indent=1, ensure_ascii=False) + "\n")
print(out)
