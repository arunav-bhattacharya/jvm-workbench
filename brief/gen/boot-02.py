import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/startup/src"
DJ = "java/workbench/startup/l02/demo"
DK = "kotlin/workbench/startup/l02/demo"
read = lambda p: (ROOT / p).read_text()


def demo(name):
    """A Try-it code object for a Java demo with its Kotlin twin, read from disk."""
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{DJ}/{name}.java"),
            "run": f"./gradlew :startup:demo -Pmain=workbench.startup.l02.demo.{name}",
            "file": f"{lab}/demo/{DJ}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{DK}/{name}.kt"),
                    "run": f"./gradlew :startup:demo -Pmain=workbench.startup.l02.demo.{name}Kt",
                    "file": f"{lab}/demo/{DK}/{name}.kt"}}


FIG = (
    '<svg viewBox="0 0 700 225" role="img" aria-label="The AOT cache workflow: a training run writes an AOT '
    'configuration, assembly turns it into app.aot, and production runs with the cache. All three need the same JAR, JDK and flags.">'
    '<rect class="box-a" x="20" y="56" width="130" height="56" rx="8"/>'
    '<text class="t" x="85" y="80" text-anchor="middle">training run</text>'
    '<text class="t-s t-code" x="85" y="99" text-anchor="middle">AOTMode=record</text>'
    '<line class="ln" x1="150" y1="84" x2="172" y2="84" marker-end="url(#arr)"/>'
    '<rect class="box-dim" x="175" y="56" width="110" height="56" rx="8"/>'
    '<text class="t" x="230" y="80" text-anchor="middle">config file</text>'
    '<text class="t-s t-code" x="230" y="99" text-anchor="middle">app.aotconf</text>'
    '<line class="ln" x1="285" y1="84" x2="307" y2="84" marker-end="url(#arr)"/>'
    '<rect class="box-a" x="310" y="56" width="130" height="56" rx="8"/>'
    '<text class="t" x="375" y="80" text-anchor="middle">assembly</text>'
    '<text class="t-s t-code" x="375" y="99" text-anchor="middle">AOTMode=create</text>'
    '<line class="ln" x1="440" y1="84" x2="462" y2="84" marker-end="url(#arr)"/>'
    '<rect class="box-ok" x="465" y="56" width="90" height="56" rx="8"/>'
    '<text class="t t-code" x="510" y="80" text-anchor="middle">app.aot</text>'
    '<text class="t-s" x="510" y="99" text-anchor="middle">the cache</text>'
    '<line class="ln" x1="555" y1="84" x2="577" y2="84" marker-end="url(#arr)"/>'
    '<rect class="box-b" x="580" y="56" width="110" height="56" rx="8"/>'
    '<text class="t" x="635" y="80" text-anchor="middle">production</text>'
    '<text class="t-s t-code" x="635" y="99" text-anchor="middle">-XX:AOTCache</text>'
    '<text class="t-s t-m" x="85" y="40" text-anchor="middle">app runs a real workload</text>'
    '<text class="t-s t-m" x="375" y="40" text-anchor="middle">app does not run</text>'
    '<text class="t-s t-m" x="635" y="40" text-anchor="middle">every start after</text>'
    '<path class="ln-d" d="M 20 124 L 20 134 L 440 134 L 440 124"/>'
    '<text class="t-s t-a" x="230" y="154" text-anchor="middle">JDK 25+: -XX:AOTCacheOutput=app.aot does both in one command</text>'
    '<rect class="box-bad" x="20" y="174" width="670" height="36" rx="8"/>'
    '<text class="t-s" x="355" y="197" text-anchor="middle">valid only for the same JAR files, JDK build, OS and CPU, GC and module options</text>'
    '</svg>'
)

S1 = """Start with the cost. Turn sharing off and `java -version` alone makes the JVM find, parse and verify 440 classes before it prints one line. On a shared 4-vCPU VM that doubled the `Create VM` time from lesson 1, from about 27 ms to about 54 ms, and lesson 1's tiny service needed about 250 ms instead of about 180 ms to its first 200.

Most JDK builds since JDK 12 avoid most of that work. They ship a **class data sharing** (CDS) archive, `lib/server/classes.jsa`, holding about 1,300 core JDK classes. The file does not contain class files. It contains the JVM's own internal structures for those classes, the ones it would otherwise build in metaspace, already parsed and verified, laid out as they sit in memory. At start-up the JVM memory-maps the file: it asks the OS to make the file part of its address space, so pages are read from disk only when they are touched. Then it fixes up the pointers and uses the classes as they are. This happens by default; `-Xshare:off` turns it off.

`java -version` shows it. On JDK 21 that command loads 405 classes, and all 405 say `source: shared objects file`. With `-Xshare:off` it loads 440 classes and none are shared. The extra 35 are classes the JVM has to generate at run time when there is no archive to take them from.

A JDK 21 package has two archives: `classes.jsa` (14.6 MB here) and `classes_nocoops.jsa`, for when compressed object pointers (32-bit object references, the default for heaps under 32 GB) are off. JDK 25 adds two `_coh` variants for compact object headers, a smaller object header layout that JEP 519 made a product feature in JDK 25 (still off by default). The JVM picks the archive that matches its flags.

That tells you what CDS can and can't save. It saves the find, parse and verify steps from lesson 1. It does not run static initializers: those still run on first use, in the same order, so a class whose `<clinit>` takes 400 ms takes 400 ms with any archive. A test program that logs its initializer order printed identical output with and without a JDK 21 archive and a JDK 25 AOT cache. It also does nothing for the JIT, which still starts cold.

Old articles also sell CDS as a way for JVMs on one host to share memory. Count on start-up time instead. Since JDK 21 the JVM maps archives at an alternative address by default (the log says `ArchiveRelocationMode == 1`), and patching the pointers writes to most pages, which makes them private. In one JDK 25 process, 11.5 MiB of the 14.4 MiB resident in the AOT cache's mapping were private dirty pages."""

S2 = """The default archive covers the JDK. **AppCDS** adds your own classes. It has been part of OpenJDK since JDK 10, and on JDK 21 it is the start-up gain you can have today without touching code. There are three ways to build one.

The dynamic archive (JDK 13 and later) needs one training run. The JVM writes the archive when that run exits:

```bash
java -XX:ArchiveClassesAtExit=app.jsa -cp app.jar com.acme.pay.Main   # training run
java -XX:SharedArchiveFile=app.jsa -cp app.jar com.acme.pay.Main      # every start after
```

It stores only what the default archive lacks, so it is small: 1.47 MB for a 300-class app, where the static archive below was 12.9 MB because it holds the JDK classes too.

The static archive takes three steps: record the class list, dump it, use it.

```bash
java -Xshare:off -XX:DumpLoadedClassList=app.classlist -cp app.jar com.acme.pay.Main
java -Xshare:dump -XX:SharedClassListFile=app.classlist -XX:SharedArchiveFile=app.jsa -cp app.jar
java -XX:SharedArchiveFile=app.jsa -cp app.jar com.acme.pay.Main
```

`-XX:+AutoCreateSharedArchive` (JDK 19 and later), used with `-XX:SharedArchiveFile=app.jsa`, folds this into your normal start command. If the file exists and came from the same JDK, the JVM uses it; if not, it writes one at exit. That is handy on a laptop and wrong for an immutable container: the file disappears with the pod, or the filesystem is read-only. Build the archive when you build the image.

On JDK 21, on a shared 4-vCPU VM, the 300-class app's median CPU time fell from 349 ms with the default archive to 171 ms with a dynamic archive and 178 ms with a static one. Wall time fell from 333 ms to 196 ms and 191 ms. Your absolute numbers will differ. The halving is what carries over.

The archive has rules. The class path must be JAR files, not directories of classes. The class path at run time must be the same as when the archive was made, or start with it. If a JAR changed after the archive was made, the JVM refuses the archive with warnings such as `h21.jar timestamp has changed` and `size has changed`, and runs normally from the JARs. It keeps using the default archive for the JDK classes. On JDK 21 this check works; keep that in mind for the last section.

Check: in development you run the app with `-cp build/classes/java/main:libs/*.jar` and add `-XX:ArchiveClassesAtExit=app.jsa`. What happens at exit? (JDK 21 refuses: `Cannot have non-empty directory in paths`. Package the classes into a JAR first, as the Try it does.)"""

S3 = """Project Leyden is the OpenJDK project that moves start-up work out of production runs. Its first result is the **AOT cache**, built one JEP at a time:

| JDK | What arrived |
|---|---|
| 24 | JEP 483: the AOT cache, with classes already loaded and linked; flags `-XX:AOTMode`, `-XX:AOTConfiguration`, `-XX:AOTCache` |
| 25 (LTS) | JEP 514: one-step `-XX:AOTCacheOutput`. JEP 515: method profiles from training, for faster warm-up |
| 26 | JEP 516: the full cache works with every GC, ZGC included |
| 27 | no Leyden JEP; `-XX:AOTMode=required` becomes the name for `on` |
| 28, in development | JEP 544: compiled code in the cache |

The `java` man page names three phases. In **training** you run the app with a representative workload, and the JVM records what it loaded and linked into an AOT configuration file. In **assembly** the JVM turns that file into the cache; your application does not run. In **production** you start with the cache. On JDK 25 one command does the first two:

```bash
java -XX:AOTCacheOutput=app.aot -cp app.jar com.acme.pay.Main   # training + assembly, JDK 25+
java -XX:AOTCache=app.aot -cp app.jar com.acme.pay.Main         # production
```

When training and assembly run in different pipeline stages, use the two-step form from JDK 24:

```bash
java -XX:AOTMode=record -XX:AOTConfiguration=app.aotconf -cp app.jar com.acme.pay.Main
java -XX:AOTMode=create -XX:AOTConfiguration=app.aotconf -XX:AOTCache=app.aot -cp app.jar
```

The one-step command does the same underneath: after training it starts a second JVM with `-XX:AOTMode=create`, passing the settings through `JAVA_TOOL_OPTIONS`.

The cache holds more than an AppCDS archive. Normally the JVM resolves references lazily: the first time an instruction runs, it turns a symbolic name in the constant pool, such as `java/util/Map.get`, into a pointer to the real method. The first run of a lambda does more: its `invokedynamic` instruction calls a bootstrap method that generates the lambda's hidden class. The AOT cache stores the results of that work from the training run: classes already linked, those references and `invokedynamic` call sites already resolved (these modes switch on `-XX:+AOTClassLinking`), Java objects the JVM would build at start-up, such as its module graph, and on JDK 25 the method profiles, the counts that tell the JIT what is hot. The JVM loads and links every cached class before `main` runs, so it reports more classes loaded than without the cache, all from the archive. Code that training never ran gets none of this; it is resolved lazily, as before.

On JDK 25 on the same VM, the 300-class app went from 504 ms of CPU to 81 ms, from 431 ms to 98 ms of wall time, and from 64 MiB to 42 MiB of max RSS. A JDK `HttpServer` app's median time to first request fell from 218 ms to 136 ms. Quarkus's perf lab measured time to first request of 4,417 ms in JVM mode and 1,859 ms with the cache, with peak throughput about 7% lower.

Quarkus 3.40 wires it up for you. Set `quarkus.package.jar.aot.enabled=true` and it trains the cache while your `@QuarkusIntegrationTest`s run and writes `target/quarkus-app/app.aot`; start with `java -XX:AOTCache=app.aot -jar quarkus-run.jar`. Its `aot-jar` packaging leaves all class loading to the JDK's own loaders, because Leyden does not support custom class loaders yet. The docs add the rule the lab makes concrete: "The more representative your integration tests are of production traffic, the more effective the AOT cache will be.\""""

S4 = """The man page is blunt: a cache belongs to one application class path, one JDK release, and one OS and CPU, and "if any of the above changes, you must recreate the AOT cache". The JVM checks, and in the default `auto` mode it starts without the cache when a check fails.

A changed JAR is the worst case, because on early JDK 25 builds the check was missing. On 25.0.0 to 25.0.3 and on 26.0.0 to 26.0.1, the JVM never compared the application's JARs with the cache (bug JDK-8377932). Rebuild the JAR, keep the old `app.aot`, and the JVM serves the **old classes**. This is JDK 25 GA running a JAR rebuilt to print "version TWO":

```text
[info][class,load] stale.Hello source: shared objects file
version ONE
```

The fix shipped in JDK 27 and was backported to 25.0.4 and 26.0.2. The same run on 25.0.4.1 rejects the cache and runs the new code:

```text
[warning][aot] This file is not the one used while building the AOT cache: 'hello.jar', timestamp has changed, size has changed
[error  ][aot] shared class paths mismatch (hint: enable -Xlog:class+path=info to diagnose the failure)
version TWO, rebuilt
```

So require **JDK 25.0.4 or later** (26.0.2 or later on 26), and rebuild the cache with every JAR, in the same build step, shipped in the same image layer. On a fixed JDK an old cache can't run old code, but it still costs you the whole speed-up.

An AOT cache the JVM can't use leaves you with no archive at all. It does not fall back to the default CDS archive. A one-class program loaded 542 classes from the default archive with no flag, and 0 with a stale or missing cache file. A typo in the path makes start-up slower than no flag.

A different GC breaks it on JDK 25. A cache trained under G1 gave 0 archived classes under `-XX:+UseZGC`. Training under ZGC worked only partly: CPU fell from 610 ms to 439 ms, against 504 ms to 81 ms with G1. JDK 26's JEP 516 removes this limit. Until then, train with the GC you run.

Module and agent options must match too. `--module-path`, `--add-modules` and `--enable-native-access` should be the same in training and production. Quarkus documents one trap: `-XX:StartFlightRecording` quietly adds the `jdk.jfr` module, and the cache no longer matches. The man page also lists "certain JVMTI options" as incompatible. JVMTI is the JVM's tool interface, the one monitoring (APM) agents use to rewrite classes as they load, so this matters as soon as someone attaches an agent.

Two flags catch all of this. `-Xlog:aot` prints `Opened AOT cache app.aot.` when the cache works and the reason when it doesn't. `-XX:AOTMode=on` (JDK 24 to 26; `required` from JDK 27) makes the JVM exit instead of running without the cache. Use that in CI. Keep it out of production: the JDK 27 man page warns that your application "may fail to launch" if something like a cloud provider's monitoring agent adds an incompatible option.

Check with the mechanism: you train on JDK 25.0.4 with G1, then deploy the same JAR on 25.0.5 with G1. Does the cache load? (No. The cache records the exact JDK build, and the JVM refuses one made by a different build.)"""

L = {
 "id": "boot-02",
 "title": "Class data sharing and Project Leyden's AOT cache",
 "minutes": 40,
 "goal": "By the end you can build and use an AppCDS archive on JDK 21 and an AOT cache on JDK 25, prove from the logs that they are used, and avoid the traps that switch them off or, on JDK 25 builds before 25.0.4, run stale code.",
 "warmup": {
  "q": "You rebuild your service's JAR with a bug fix but keep the AOT cache from the previous build. You start it on JDK 25.0.4 with `-XX:AOTCache=app.aot`. What happens?",
  "options": ["It runs the fixed code with the full speed-up from the cache", "It runs the old code, served from the cache", "It warns that the JAR changed, ignores the cache, and runs the fixed code with no archive at all", "It refuses to start"],
  "answer": 2,
  "why": "On 25.0.4 and later the JVM compares the JAR with the cache, prints a warning, and in the default `auto` mode carries on without the cache, and without the default CDS archive too. On 25.0.0 to 25.0.3 the check was missing and the old classes really did run (bug JDK-8377932). It only refuses to start if you asked for that with `-XX:AOTMode=on`."
 },
 "sections": [
  {
   "h": "The JDK already ships a class archive",
   "body": S1,
   "try": {
    "title": "Look at the default archive",
    "minutes": 3,
    "steps": [
     "List the archives your JDK ships with the first command.",
     "Predict: with `-Xshare:off`, will `java -version` load more classes than with the archive, fewer, or the same number? Then count both with the next two commands.",
     "Run the last command to see which archive file the JVM opened."
    ],
    "code": {"lang": "bash", "title": "terminal",
             "src": "ls -l \"$JAVA_HOME\"/lib/server/*.jsa\njava -Xlog:class+load -version 2>&1 | grep -c 'shared objects file'\njava -Xshare:off -Xlog:class+load -version 2>&1 | grep -c 'source:'\njava -Xlog:cds -version 2>&1 | grep -i opened",
             "run": ""},
    "expect": "On Ubuntu's JDK 21 build: two files, `classes.jsa` (14,581,760 bytes) and `classes_nocoops.jsa`; 405 shared classes; 440 classes with sharing off; and `Opened archive .../lib/server/classes.jsa`. On JDK 25.0.4: four files, including `classes_coh.jsa` and `classes_nocoops_coh.jsa`; 393 of 396 classes shared; 411 with sharing off."
   },
   "refs": [
    {"title": "The java command, JDK 25: Class Data Sharing and the AOT cache (man page source)", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/man/java.md", "kind": "docs"}
   ]
  },
  {
   "h": "AppCDS puts your own classes in the archive",
   "body": S2,
   "try": {
    "title": "Climb the archive ladder",
    "minutes": 5,
    "steps": [
     "Read `ArchiveLadder`. It packs its own package into `startup/build/boot02/app.jar` (CDS wants JARs), then runs the same small workload under each setup and counts the `source:` lines.",
     "Predict the \"from archive\" column for the dynamic AppCDS row, then run it.",
     "Run the Kotlin twin. Its class path is the app JAR plus `kotlin-stdlib`, and both go into the archive.",
     "Gradle runs demos on the JDK that runs Gradle. If that is JDK 21, run the class with a JDK 25 `java` to get the AOT cache row: `java -cp startup/build/classes/java/demo workbench.startup.l02.demo.ArchiveLadder`."
    ],
    "code": demo("ArchiveLadder"),
    "expect": "One run on JDK 21 on a shared VM printed: no sharing 855 loaded, 0 from archive, 143 ms; default CDS 821 and 789, 120 ms; dynamic AppCDS 754 and 719, 82 ms, with a 221 KB archive. On JDK 25.0.4: 909/0, 897/868, 826/794, and the AOT cache row 959 loaded, all 959 from the archive (11.5 MB file). Times jump around between runs; the counts don't."
   }
  },
  {
   "h": "Leyden's AOT cache: train, assemble, run",
   "body": S3,
   "figure": {"svg": FIG, "caption": "Training records what the app loads and links, assembly writes the cache without running the app, and production maps it."},
   "try": {
    "title": "Make an AOT cache by hand (JDK 25+)",
    "minutes": 4,
    "steps": [
     "Run `ArchiveLadder` once (previous Try it) so `startup/build/boot02/app.jar` exists. Then `cd labs/startup/build/boot02` and use a JDK 25 `java`.",
     "Run the first command: training and assembly in one go. Find the `Launching child process` and `Picked up JAVA_TOOL_OPTIONS` lines.",
     "Run the second command and look for `Opened AOT cache`.",
     "Predict the count from the third command, which names a file that doesn't exist. Then run it."
    ],
    "code": {"lang": "bash", "title": "terminal (JDK 25+)",
             "src": "java -XX:AOTCacheOutput=pay.aot -cp app.jar workbench.startup.l02.demo.ArchiveLadder --work\njava -XX:AOTCache=pay.aot -Xlog:aot -cp app.jar workbench.startup.l02.demo.ArchiveLadder --work | grep Opened\njava -XX:AOTCache=nope.aot -Xlog:class+load -cp app.jar workbench.startup.l02.demo.ArchiveLadder --work | grep -c 'shared objects file'",
             "run": ""},
    "expect": "On 25.0.4.1 the first command printed `Temporary AOTConfiguration recorded: pay.aot.config`, `Launching child process ... to assemble AOT cache pay.aot`, a `Picked up JAVA_TOOL_OPTIONS: ... -XX:AOTMode=create` line, and `AOTCache creation is complete: pay.aot ... bytes` (about 11.5 MB). The second printed `Opened AOT cache pay.aot.` The third printed errors ending in `Unable to map shared spaces`, still ran the app, and counted 0 shared classes: a bad cache path also loses the default archive."
   },
   "refs": [
    {"title": "JEP 483: Ahead-of-Time Class Loading & Linking", "url": "https://openjdk.org/jeps/483", "kind": "read"},
    {"title": "JEP 514: Ahead-of-Time Command-Line Ergonomics", "url": "https://openjdk.org/jeps/514", "kind": "read"},
    {"title": "Quarkus 3.40: AOT and AppCDS guide (aot.adoc)", "url": "https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/docs/src/main/asciidoc/aot.adoc", "kind": "docs"}
   ]
  },
  {
   "h": "A cache is valid for one JAR, one JDK and one set of flags",
   "body": S4,
   "try": {
    "title": "Run new code with an old cache",
    "minutes": 4,
    "steps": [
     "Read `StaleCacheDemo`. It compiles a one-class program that prints \"version ONE\", trains a cache on it, rebuilds the JAR to print \"version TWO\", and starts the new JAR with the old cache.",
     "Run it through Gradle. On JDK 21 it uses a dynamic CDS archive, because there is no AOT cache.",
     "If you have a JDK 25, run it with that JDK's `java` directly: `java -cp startup/build/classes/java/demo workbench.startup.l02.demo.StaleCacheDemo`. Check `java -version` first and predict which output you'll get."
    ],
    "code": demo("StaleCacheDemo"),
    "expect": "JDK 21 refuses the archive (`hello.jar size has changed`, `Unable to use shared archive`) and prints `version TWO, rebuilt`. JDK 25 GA (25+36) prints `stale.Hello source: shared objects file` and `version ONE`: the old class, from the cache. JDK 25.0.4 and later print the `timestamp has changed, size has changed` warning, `Unable to map shared spaces`, and `version TWO, rebuilt`, loaded from the JAR."
   },
   "refs": [
    {"title": "The fix: 8377932, AOT cache is not rejected when JAR file has changed", "url": "https://github.com/openjdk/jdk/commit/b41ba3a496b59c8058067a49617f798606f0a51c", "kind": "read"}
   ]
  }
 ],
 "analogy": "Without CDS, the JVM is a librarian who unpacks every book each morning, reads it, checks it for errors and only then shelves it. CDS is a bookcase that arrives already filled: you wheel it in and open the doors. The AOT cache is the same bookcase with the cross-references between books already filled in and sticky notes on the pages people read most. A training run is the day you watch which books people actually take. The analogy breaks at the worst place: a librarian would notice that the books in the wheeled-in bookcase are last year's edition. JDK 25 before 25.0.4 didn't.",
 "in_your_world": "For a Quarkus 3.40 payment service on JDK 25, the cheapest start-up win is one property: `quarkus.package.jar.aot.enabled=true`, with the cache trained by your `@QuarkusIntegrationTest`s. Make those tests look like production: if they only authorize cards, the refund and chargeback code paths load the slow way in every new pod. Pin the JDK patch level in your base image to 25.0.4 or later, train in the same image you run, and copy `app.aot` in the same layer as the JAR. Run a CI step with `-XX:AOTMode=on -Xlog:aot` that fails the build if the cache does not open, and leave `AOTMode` unset in production so an APM agent can't keep pods from starting. Services still on JDK 21 can use Quarkus's AppCDS fallback, `quarkus.package.jar.aot.type=app-cds`.",
 "mistake": "The costly mistake is treating the cache as a build artifact you make once and reuse. A pipeline caches `app.aot` to save a minute, the JAR changes, and on JDK 25.0.0 to 25.0.3 the service runs last week's classes with no error at all. On 25.0.4 and later it runs the right code, but with no archive, so every pod starts slower than before you added the cache, and only a warning line says why. The fix is to generate the cache in the same build step as the JAR, ship both together, require 25.0.4 or later, and let CI fail when `-XX:AOTMode=on` can't open it.",
 "compare": {
  "title": "A training entry point in Java and Kotlin",
  "java": {"title": "TrainingMain.java", "src": "/** Starts the service, drives every kind of request production sees, then exits so the JVM writes the cache. */\npublic final class TrainingMain {\n    public static void main(String[] args) throws Exception {\n        PaymentService service = PaymentService.start();          // the same wiring as production\n        for (String fixture : List.of(\"authorize-eur.json\", \"authorize-usd.json\", \"refund.json\", \"capture.json\")) {\n            service.handle(Fixtures.load(fixture));               // real code paths, fake card issuer\n        }\n        service.stop();\n        System.exit(0);   // JDK 24/25 write the training data when the JVM exits\n    }\n}"},
  "kotlin": {"title": "TrainingMain.kt", "src": "/** Starts the service, drives every kind of request production sees, then exits so the JVM writes the cache. */\nfun main() {\n    val service = PaymentService.start()                         // the same wiring as production\n    listOf(\"authorize-eur.json\", \"authorize-usd.json\", \"refund.json\", \"capture.json\")\n        .forEach { service.handle(Fixtures.load(it)) }           // real code paths, fake card issuer\n    service.stop()\n    exitProcess(0)    // JDK 24/25 write the training data when the JVM exits\n}"},
  "note": "The cache does not care which language produced the bytecode. What differs is the class path and the entry point. A Kotlin service has `kotlin-stdlib` (and often `kotlinx-coroutines`) as JARs on the class path, and they must be there in the same order in training and in production, or the cache is refused. The training entry point is `TrainingMainKt`, not `TrainingMain`. Kotlin 2.x compiles lambdas to `invokedynamic`, like Java, so the cache can pre-resolve those call sites in both. Before JDK 26 the training run has to exit to write its data, which is why both versions end the process; JDK 26 adds `jcmd <pid> AOT.end_recording` for long-running servers."
 },
 "worked": {
  "title": "Add the AOT cache to a container build",
  "steps": [
   {"say": "Pin the JDK and use the same image to build and to run. The cache records the exact JDK build: a cache made on 25 GA was refused on 25.0.4.1 with `The AOT cache was created by a different version or build of HotSpot`. Pick 25.0.4 or later, so a changed JAR can never run stale classes.",
    "code": "# check the build stage and the runtime stage print the same line\njava -version 2>&1 | head -1\n# openjdk version \"25.0.4.1\" ...   must be 25.0.4 or later",
    "lang": "bash"},
   {"say": "In the build stage, put the JAR at the path it will have at run time, then train and assemble in one step. Use the training entry point from the compare block, so the run exercises every request type and then exits.",
    "code": "cp build/libs/pay.jar /srv/pay.jar\njava -XX:AOTCacheOutput=/srv/app.aot -cp /srv/pay.jar com.acme.pay.TrainingMain\n# ... AOTCache creation is complete: /srv/app.aot ... bytes",
    "lang": "bash"},
   {"say": "In CI, start the real entry point with `-XX:AOTMode=on` and `-Xlog:aot` and fail the build if the cache doesn't open. A wrong path, a different JDK or a changed JAR all make this exit with an error.",
    "code": "java -XX:AOTMode=on -XX:AOTCache=/srv/app.aot -Xlog:aot -cp /srv/pay.jar com.acme.pay.SmokeMain \\\n  | grep -q 'Opened AOT cache' || { echo 'AOT cache not used'; exit 1; }   # JDK 27+: AOTMode=required",
    "lang": "bash"},
   {"say": "Ship `pay.jar` and `app.aot` in the same image layer and start production without `AOTMode`. If someone later attaches an agent that the cache can't handle, the pod starts slower instead of not at all.",
    "code": "java -XX:AOTCache=/srv/app.aot -cp /srv/pay.jar com.acme.pay.Main",
    "lang": "bash"}
  ]
 },
 "lab": {
  "title": "Write a recording class loader and a training run",
  "minutes": 15,
  "files": [
   "labs/startup/src/main/kotlin/workbench/startup/l02/RecordingClassLoader.kt",
   "labs/startup/src/main/kotlin/workbench/startup/l02/TrainingRun.kt"
  ],
  "run": "./gradlew :startup:test --tests 'workbench.startup.l02.*'",
  "steps": [
   "Run the tests once. All ten fail with `NotImplementedError`.",
   "Implement `RecordingClassLoader.loadClass`. Outside the prefix, call `super.loadClass(name, resolve)`. Inside it, take `getClassLoadingLock(name)`, return `findLoadedClass(name)` if it is already there, otherwise read the class file from `parent.getResourceAsStream`, call `defineClass`, and record the name.",
   "Implement `defined()` and run `RecordingClassLoaderTest`. Look at the first two tests: `Class.forName(name, false, loader)` defines one class, `true` defines two, because only initialization runs `FeeTable`'s static initializer.",
   "Implement `TrainingRun.classList` (a fresh loader, `Class.forName(entryClass, true, loader)`, `getMethod(\"handle\", String::class.java)`, one `invoke` per request) and `missing` (one line of set arithmetic).",
   "Run all tests until the ten pass. Read the fixtures in `src/test/java/workbench/startup/l02/fixtures/`: training with authorizations only never loads `Refund`."
  ],
  "hints": [
   "Kotlin's `synchronized(lock) { ... }` is inline, so `return c` inside it returns from `loadClass`.",
   "`parent.getResourceAsStream(path)?.use { it.readBytes() } ?: throw ClassNotFoundException(name)` reads the bytes and handles a missing file in one expression.",
   "The tests compare sets of class names, never counts. A count of all loaded classes changes between JDK builds; the classes your own loader defined do not."
  ],
  "done_when": "All ten tests in `RecordingClassLoaderTest` and `TrainingRunTest` pass."
 },
 "drill": {
  "title": "The commands from memory",
  "minutes": 4,
  "prompt": "Close this page. For `pay.jar` with main class `com.acme.pay.Main`, write: (1) the two JDK 21 commands for a dynamic AppCDS archive, (2) the two JDK 25 commands for an AOT cache, (3) the CI command that fails if the cache can't be used. Then add one comment saying which JDK patch level you require and why.",
  "answer": {
   "lang": "bash",
   "src": "# 1. JDK 21: dynamic AppCDS\njava -XX:ArchiveClassesAtExit=app.jsa -cp pay.jar com.acme.pay.Main\njava -XX:SharedArchiveFile=app.jsa -cp pay.jar com.acme.pay.Main\n\n# 2. JDK 25: AOT cache (training + assembly, then production)\njava -XX:AOTCacheOutput=app.aot -cp pay.jar com.acme.pay.Main\njava -XX:AOTCache=app.aot -cp pay.jar com.acme.pay.Main\n\n# 3. CI only: exit with an error if the cache can't be used (AOTMode=required on JDK 27+)\njava -XX:AOTMode=on -XX:AOTCache=app.aot -Xlog:aot -cp pay.jar com.acme.pay.Main\n\n# Require 25.0.4+ (or 26.0.2+): earlier builds don't check the JAR (JDK-8377932)\n# and can run stale classes. Rebuild app.aot with every pay.jar."
  }
 },
 "recap": [
  "CDS maps pre-parsed classes from a `.jsa` file. The default archive (JDK 12+) covers about 1,300 JDK classes; `-Xshare:off` turns it off.",
  "AppCDS adds your classes: dynamic with `-XX:ArchiveClassesAtExit` and `-XX:SharedArchiveFile`, static with a class list and `-Xshare:dump`, or `-XX:+AutoCreateSharedArchive`. On JDK 21 it halved a test app's start-up CPU.",
  "The AOT cache (JEP 483 in JDK 24, one-step `-XX:AOTCacheOutput` in JDK 25) adds linked classes and profiles. Training, assembly, production; a training run only captures the code paths it ran.",
  "Require JDK 25.0.4+ or 26.0.2+ for the AOT cache, and rebuild it with every JAR: earlier builds could run stale classes (JDK-8377932).",
  "An AOT cache the JVM can't use leaves no archive at all, not even the default one. Check with `-Xlog:aot` and `-XX:AOTMode=on` in CI, never in production.",
  "Match the GC (ZGC needs JDK 26 for the full cache), the module flags and the class path between training and production."
 ],
 "quiz": [
  {"q": "You add `-XX:SharedArchiveFile=app.jsa`, a dynamic archive, and run with `-Xlog:class+load` on JDK 21. Most JDK classes log `source: shared objects file`, but your own classes log `source: file:/srv/app.jar`. What does that tell you?",
   "options": ["The JVM rejected your dynamic archive and kept only the default one, so look for the warning that says why", "Everything works: app classes are always logged with their JAR", "Your classes are archived but `-Xlog:class+load` can't see that", "The default archive failed and your archive replaced it"],
   "answer": 0,
   "from": "boot-01",
   "why": "Archived classes log `source: shared objects file`, yours included. When JDK 21 rejects a dynamic archive (a changed JAR, a different class path) it warns and keeps the default archive underneath, so the JDK classes stay shared and only yours load from the JAR. The warning lines at the start of the output say which check failed."},
  {"q": "Your integration tests, which train the AOT cache, only send card authorizations. In production a refund arrives. What happens on the refund path?",
   "options": ["The refund fails with ClassNotFoundException", "The JVM throws away the whole cache", "Its classes load the usual way from the JAR, parsed and verified at that moment, so the first refund is slower", "The JVM retrains the cache in the background"],
   "answer": 2,
   "why": "The cache contains what the training run loaded. Anything else loads the usual way, so the program is still correct, but those classes get no head start. That is why the training workload should look like production traffic, which is what the lab's `missing` function measures."},
  {"q": "A service runs ZGC on JDK 25. Its AOT cache was trained with the default G1. What do you get?",
   "options": ["The full speed-up, because the cache does not depend on the GC", "Only the method profiles", "A crash at start-up", "Nothing: the JVM can't use the G1-trained cache under ZGC and runs with zero archived classes"],
   "answer": 3,
   "why": "On JDK 25 a G1-trained cache gave 0 archived classes under `-XX:+UseZGC`. Training under ZGC helps only partly. JDK 26's JEP 516 stores heap objects in a form every GC can load, so the full cache works with ZGC from 26 on."},
  {"q": "A platform team adds an APM agent to every pod through `JAVA_TOOL_OPTIONS`. Your service starts with `-XX:AOTMode=on -XX:AOTCache=app.aot`. What is the risk?",
   "options": ["None: `on` only means the cache is enabled", "If the agent's options are incompatible with the cache, the JVM exits at start-up instead of running without the cache", "The agent's classes get added to the cache", "The cache is rebuilt on every start"],
   "answer": 1,
   "why": "`on` (`required` from JDK 27) is a fail-fast setting: if the cache can't be used, the JVM stops. The man page lists certain JVMTI options among the incompatible ones, and the JDK 27 page warns about exactly this case. In production leave the mode at the default `auto`, which falls back to running without the cache."},
  {"q": "A JDK 21 service runs in an immutable container with a read-only root filesystem. You want AppCDS with no code change. Which setup fits?",
   "options": ["`-XX:+AutoCreateSharedArchive -XX:SharedArchiveFile=/app/app.jsa` in the start command", "`-XX:AOTCacheOutput=app.aot` in the start command", "A dynamic archive made at image build time with `-XX:ArchiveClassesAtExit`, shipped in the image and used with `-XX:SharedArchiveFile`", "`-Xshare:off`, for predictable start-up"],
   "answer": 2,
   "why": "`AutoCreateSharedArchive` writes the file at the exit of a run that had none, which fails on a read-only filesystem and is lost with a short-lived pod anyway. Building the archive during the image build gives every pod the same archive from its first start. `-XX:AOTCacheOutput` needs JDK 25."}
 ],
 "flashcards": [
  {"front": "What work does a CDS archive save at start-up?", "back": "Finding, parsing and verifying the archived classes: the JVM maps them ready-made from the `.jsa` file. Static initializers still run at first use."},
  {"front": "The two commands for a dynamic AppCDS archive (JDK 13+)?", "back": "`java -XX:ArchiveClassesAtExit=app.jsa -cp app.jar Main`, then `java -XX:SharedArchiveFile=app.jsa -cp app.jar Main`."},
  {"front": "The two commands for an AOT cache on JDK 25?", "back": "`java -XX:AOTCacheOutput=app.aot -cp app.jar Main` (training and assembly), then `java -XX:AOTCache=app.aot -cp app.jar Main`."},
  {"front": "Which JDK builds can run stale classes from an AOT cache after the JAR changed?", "back": "25.0.0 to 25.0.3 and 26.0.0 to 26.0.1 (JDK-8377932). Fixed in 25.0.4, 26.0.2 and 27."},
  {"front": "`-XX:AOTCache=` names a missing or stale file, default mode. What do you get?", "back": "The app runs with no archive at all, not even the default CDS archive, so it starts slower than with no flag."},
  {"front": "Where does `-XX:AOTMode=on` (JDK 27: `required`) belong?", "back": "In CI, as a fail-fast check that the cache opens. Not in production, where an incompatible agent would stop the JVM from starting."},
  {"front": "From which JDK does the full AOT cache work with ZGC?", "back": "JDK 26 (JEP 516). On JDK 25 a G1-trained cache gives nothing under ZGC, and a ZGC-trained one only part of the gain."}
 ],
 "terms": [
  {"term": "CDS", "plain": "Class data sharing: classes stored pre-parsed in a `.jsa` file that the JVM maps at start-up."},
  {"term": "Default CDS archive", "plain": "The archive of about 1,300 JDK classes that ships in `lib/server/classes.jsa` and is used unless `-Xshare:off`."},
  {"term": "AppCDS", "plain": "A CDS archive that also holds your application's classes."},
  {"term": "AOT cache", "plain": "Leyden's archive (JDK 24+): classes loaded and linked ahead of time, heap objects, and from JDK 25 method profiles."},
  {"term": "Training run", "plain": "A run of the app with a representative workload that records what to put in the archive or cache."},
  {"term": "Assembly", "plain": "The step that turns the training data into the AOT cache; the application itself does not run."},
  {"term": "AOTMode", "plain": "The flag that sets how the JVM treats the cache: `auto` (default), `record`, `create`, `on` or `required` (27+), `off`."}
 ],
 "explain_back": {
  "prompt": "A teammate wants to keep `app.aot` in the CI cache between builds, because training adds two minutes. Explain why that is a bad idea, and what happens on JDK 25.0.3 versus 25.0.4 when the JAR has changed.",
  "answer": "The cache belongs to one exact set of JARs, one JDK build and one set of flags. When the JAR changes, the old cache describes classes that no longer exist in that form. On 25.0.3 the JVM didn't check the application JARs at all, so it would serve the old classes from the cache and run last build's code with no error. On 25.0.4 and later it notices the changed timestamp and size, warns, and runs without the cache, so the code is right but every pod loses the speed-up, and the default CDS archive too. Either way the cache has to be built in the same step as the JAR and shipped with it. The two minutes are cheaper than either failure."
 },
 "deeper": {
  "minutes": 10,
  "body": "A few details that matter once you run this for real.\n\nThe static archive is dumped in interpreter-only mode, as if `-Xint` were set, so the output is deterministic, bit for bit. For big class lists you can add `-Xmixed` to speed up the dump when you don't need that.\n\nYou can also take an archive from a running process: `jcmd <pid> VM.cds dynamic_dump app.jsa`, if the process was started with `-XX:+RecordDynamicDumpInfo`, or `jcmd <pid> VM.cds static_dump app.jsa`. That suits a service whose real warm-up needs real traffic. To try flags without editing start scripts, `JAVA_TOOL_OPTIONS=-XX:SharedArchiveFile=app.jsa` works, because the JVM reads that variable at start.\n\nIn the AOT cache file names, `%p` and `%t` are replaced by the PID and the start time, as in `-XX:AOTCacheOutput=pay%p.aot`, so parallel training runs don't overwrite each other.\n\nThe man page lags behind the code in one place: the JDK 25 page still says the cache holds \"Java classes and heap objects\" and that profiles will come in a future release, although JEP 515 shipped profiles in JDK 25. The JDK 28 development page lists classes, heap objects, execution profiles and compiled methods.\n\nWhat's next in Leyden, as of the JDK 28 development line: JEP 544 moves JIT compilation into the training run and ships the native code in the cache, while the JIT can still recompile in production. JEP 545 targets start-up and warm-up with ZGC. Neither is in a released JDK yet, so treat them as previews of where this is going, not as flags to use."
 },
 "sources": [
  {"title": "The java command, JDK 25 (man page source): CDS and the AOT cache", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/man/java.md"},
  {"title": "JEP 483: Ahead-of-Time Class Loading & Linking", "url": "https://openjdk.org/jeps/483"},
  {"title": "JEP 515: Ahead-of-Time Method Profiling", "url": "https://openjdk.org/jeps/515"},
  {"title": "Quarkus 3.40 AOT guide (aot.adoc)", "url": "https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/docs/src/main/asciidoc/aot.adoc"},
  {"title": "OpenJDK commit b41ba3a: 8377932, AOT cache is not rejected when JAR file has changed", "url": "https://github.com/openjdk/jdk/commit/b41ba3a496b59c8058067a49617f798606f0a51c"}
 ]
}
out = ROOT / "content/lessons/boot-02.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
