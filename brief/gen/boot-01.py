import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/startup/src"
DJ = "java/workbench/startup/l01/demo"
DK = "kotlin/workbench/startup/l01/demo"
read = lambda p: (ROOT / p).read_text()


def demo(name, title=None):
    """A Try-it code object for a Java demo with its Kotlin twin, read from disk."""
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{DJ}/{name}.java"),
            "run": f"./gradlew :startup:demo -Pmain=workbench.startup.l01.demo.{name}",
            "file": f"{lab}/demo/{DJ}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{DK}/{name}.kt"),
                    "run": f"./gradlew :startup:demo -Pmain=workbench.startup.l01.demo.{name}Kt",
                    "file": f"{lab}/demo/{DK}/{name}.kt"}}


FIG = (
    '<svg viewBox="0 0 700 230" role="img" aria-label="Timeline of a JVM start-up: launch, create VM, class loading, '
    'framework start, first request and JIT warm-up, with three clocks marked under it">'
    '<text class="t-s t-m" x="20" y="20">time since launch</text>'
    '<line class="ln-d" x1="20" y1="30" x2="690" y2="30" marker-end="url(#arr)"/>'
    '<rect class="box-dim" x="20" y="50" width="70" height="44" rx="8"/>'
    '<text class="t-s" x="55" y="77" text-anchor="middle">launch</text>'
    '<rect class="box" x="95" y="50" width="90" height="44" rx="8"/>'
    '<text class="t-s" x="140" y="77" text-anchor="middle">create VM</text>'
    '<rect class="box-a" x="190" y="50" width="190" height="44" rx="8"/>'
    '<text class="t-s" x="285" y="69" text-anchor="middle">load, verify, init classes</text>'
    '<text class="t-s t-m" x="285" y="86" text-anchor="middle">interpreter runs your code</text>'
    '<rect class="box-b" x="385" y="50" width="120" height="44" rx="8"/>'
    '<text class="t-s" x="445" y="69" text-anchor="middle">framework start</text>'
    '<text class="t-s t-m" x="445" y="86" text-anchor="middle">scan, wire, config</text>'
    '<rect class="box" x="510" y="50" width="90" height="44" rx="8"/>'
    '<text class="t-s" x="555" y="69" text-anchor="middle">first request</text>'
    '<text class="t-s t-m" x="555" y="86" text-anchor="middle">more classes</text>'
    '<rect class="box-dim" x="605" y="50" width="85" height="44" rx="8"/>'
    '<text class="t-s" x="647" y="69" text-anchor="middle">warm-up</text>'
    '<text class="t-s t-m" x="647" y="86" text-anchor="middle">C1, then C2</text>'
    '<line class="ln-a" x1="185" y1="98" x2="185" y2="140"/>'
    '<text class="t-s t-a" x="185" y="156" text-anchor="middle">Create VM</text>'
    '<text class="t-s t-m" x="185" y="172" text-anchor="middle">-Xlog:startuptime</text>'
    '<line class="ln-a" x1="505" y1="98" x2="505" y2="140"/>'
    '<text class="t-s t-a" x="505" y="156" text-anchor="middle">started in</text>'
    '<text class="t-s t-m" x="505" y="172" text-anchor="middle">framework log line</text>'
    '<line class="ln-a" x1="600" y1="98" x2="600" y2="185"/>'
    '<text class="t-s t-a" x="600" y="201" text-anchor="middle">first 200</text>'
    '<text class="t-s t-m" x="600" y="217" text-anchor="middle">probe, from outside</text>'
    '</svg>'
)

S1 = """A generated test app with 300 classes loads **1,537 classes** on JDK 21 before it finishes, with class sharing turned off. 301 come from the app's JAR. 911 come from the JDK's own modules. The other 325 are hidden classes that the JVM spins up at run time for lambdas and method handles. Your 300 classes are a fifth of the work.

For every one of those classes the JVM does the same steps on every launch. It finds the bytes, parses them into its internal form in metaspace, verifies the bytecode, and later runs the static initializer. Then it runs your code in the interpreter, because the JIT compilers only start once they have profiles of what is hot. A framework adds its own start-up work on top: scanning the classpath for annotations, wiring beans by reflection, generating proxies, parsing config. Quarkus moves as much of that as it can to build time; its extension guide says to favor "doing work at build time ... as opposed to let the framework do work at startup time".

Nothing of this survives the process. Stop the JVM and the next start does it all again. Only one thing is cached by default: the JDK ships a class data sharing archive with about 1,300 of its own classes, which the JVM maps from disk instead of parsing. Lesson 2 of this track is about that archive and the bigger ones you can build.

You can watch the loading happen. `-Xlog:class+load` prints one line per class, and the end of each line says where the class came from:

```text
[info][class,load] java.lang.Object source: shared objects file
[info][class,load] java.util.regex.Pattern$Node source: jrt:/java.base
[info][class,load] com.acme.pay.Main source: file:/srv/app.jar
[info][class,load] com.acme.pay.Main$$Lambda/0x... source: com.acme.pay.Main
```

`shared objects file` means the class was mapped from a CDS archive. `jrt:/` means it was read and parsed from the JDK's modules file. `file:` is your classpath. A class name as the source marks a hidden class that this class defined at run time, usually a lambda. `-verbose:class` prints the same lines.

That `source:` column turns "start-up is slow" into a histogram you can read. When you try lesson 2's archives later, the same histogram shows them working."""

S2 = """Loading a class and initializing it are two different events. The JVM loads a class when something needs its definition. It runs the class's static initializer, the method the bytecode calls `<clinit>`, only on the first **active use**: `new`, a call to a static method, a read or write of a static field that is not a compile-time constant, or a reflective call that asks for initialization. Initializing a subclass initializes its superclass first. Declaring a variable of the type, or writing `Fees.class`, does neither.

That rule decides what ends up on your start-up path. Here is a common shape: a table built in a static field.

```java
public final class BinTable {
    private static final Map<String, String> TABLE = build();   // runs in <clinit>

    public static String version() { return "bins-2026.11"; }
    public static String issuerOf(String pan) { return TABLE.get(pan.substring(0, 6)); }
}
```

```kotlin
class BinTable {
    companion object {
        private val table = build()             // also runs in BinTable's <clinit>

        fun version() = "bins-2026.11"
        fun issuerOf(pan: String) = table[pan.take(6)]
    }
}
```

The readiness check only logs `version()`. It still pays for the whole table, because calling any static method initializes the class, and the class's initializer builds the table. The Kotlin version has the same problem, and it surprises people. A companion object's properties compile to static fields of the outer class, and the outer class's `<clinit>` fills them. `javap` shows `private static final java.util.Map table` on `BinTable` itself.

The fix is the **holder idiom**: give the expensive field its own class.

```java
public final class BinTable {
    private static final class Holder {
        static final Map<String, String> TABLE = build();   // runs on first use of Holder
    }
    public static String version() { return "bins-2026.11"; }
    public static String issuerOf(String pan) { return Holder.TABLE.get(pan.substring(0, 6)); }
}
```

```kotlin
object BinTable {
    fun version() = "bins-2026.11"
    fun issuerOf(pan: String) = Holder.table[pan.take(6)]

    private object Holder {
        val table = build()                     // a nested object is its own class
    }
}
```

Now `version()` touches only `BinTable`. The JVM loads and initializes `Holder` the first time `issuerOf` reads `Holder.TABLE`. It is also thread-safe without any lock in your code: the JVM initializes a class under its own lock (JLS 12.4.2), so if eight threads arrive at once, one runs the initializer and the others wait for it. In Kotlin, `val table by lazy { build() }` gives you the same laziness with a lock you can see. The memory model track covers why this is safe in lesson 5, "Lazy init done right".

Lazy is not always better. Moving the cost to the first request makes that request slow instead. Be lazy about work that many starts never need, such as admin tables or rarely used reports. Do the work early, on purpose, when every request needs it."""

S3 = """There are three start-up numbers, and people mix them up.

The first is the JVM's own. `-Xlog:startuptime` prints the phases of creating the VM and ends with a line like `Create VM, 0.0381310 secs`. That is the JVM getting ready to run `main`. It says nothing about your code or your framework.

The second is the framework's log line. Quarkus prints `started in 0.968s. Listening on: http://localhost:8080`. That number comes from inside the process, and every framework starts its clock at a slightly different place.

The third is **time to first request**: from launching the process to the first successful response, measured from outside. This is the one that matters. A Kubernetes readiness probe, a load balancer and a user all see this clock and no other. It includes everything: the launcher, VM creation, class loading, framework start, and the first request itself, which loads more classes again (the HTTP handler path, JSON, your service code).

On a shared 4-vCPU Linux VM, the demo below printed this for a tiny JDK `HttpServer` app on JDK 21:

```text
log      : [0.031s][info][startuptime] Create VM, 0.0301657 secs
log      : started in 0.103s. Listening on: http://127.0.0.1:45969
first 200: 179 ms after launch, measured outside (15 attempts)
```

30 ms, 103 ms and 179 ms. The gap between the last two is the launcher, process creation, and the first request's own class loading.

Even the first 200 is not the end. Early requests run in the interpreter or in C1-compiled code, and the C2 compiler only takes over hot methods after it has seen enough of them. So time to first request and time to peak throughput are different numbers too. You can feel this when a new pod joins under load: it answers, but slowly, for a while. The performance track's first lesson, "From bytecode to machine code", goes into the tiers."""

S4 = """The same demo also reads the service's memory, and the numbers disagree by a factor of five.

```text
RSS      : VmRSS: 53456 kB, RssAnon: 28824 kB, RssFile: 24632 kB
NMT      : Total: reserved=4901MB, committed=290MB
NMT      : Java Heap (reserved=3420MB, committed=216MB)
```

Native Memory Tracking (NMT) is the JVM's own accounting. It says the JVM has **committed** 290 MB, 216 MB of it for the heap. The operating system says the process has 53 MB **resident** (RSS). Both are right. Committed memory is memory the JVM has asked the OS for. A page only becomes resident when someone touches it, and a fresh heap is mostly untouched pages.

RSS is the number the container limit cares about. It is much more than the heap. It counts touched heap pages, metaspace and the class space, the JIT's code cache, GC data structures, thread stacks, the mapped CDS archive, the JDK's modules file, `libjvm.so`, direct buffers and malloc arenas. `RssAnon` is memory the process created. `RssFile` is file-backed: the archive, the modules file and native libraries, which other processes on the same host may share. For shared pages, `Pss` in `/proc/<pid>/smaps_rollup` splits each one between the processes that map it.

Measure it like this:

```bash
ps -o pid,rss,args -p <pid>                 # RSS in kB, Linux and macOS
grep -E 'VmRSS|RssAnon|RssFile' /proc/<pid>/status
jcmd <pid> VM.native_memory summary         # only if started with -XX:NativeMemoryTracking=summary
```

Don't use `docker stats`. The Quarkus guide on measuring performance says so in capitals: it "only measures a subset of the in-use resident pages", while a container is killed "based on its full RSS memory usage". It recommends `ps -e -o pid,rss,args` or `docker top <id> -o pid,rss,args` instead.

One more trap: heap usage from your metrics is not footprint either. A service with 80 MB of live heap can sit at 300 MB RSS, and the other 220 MB is the JVM itself plus everything the GC has touched."""

L = {
 "id": "boot-01",
 "title": "Why the JVM starts slowly, and how to measure it",
 "minutes": 35,
 "goal": "By the end you can say where a JVM's start-up time and memory go, measure them with the right clock and the OS's view of RSS, and move expensive static work off the start-up path with a holder class.",
 "warmup": {
  "q": "A test app has 300 classes of its own. How many classes does the JVM load to run it to the end?",
  "options": ["About 300", "About 600: your classes plus the JDK classes they import", "About 1,500", "About 30,000"],
  "answer": 2,
  "why": "A generated 300-class app loaded 1,537 classes on JDK 21 with class sharing off: 301 from the app's JAR, 911 from the JDK's modules, and 325 hidden classes for lambdas and method handles. The JDK and the run-time machinery are most of the work, not your code. 30,000 is the order of a large Spring app (JEP 483 cites about 21,000 for PetClinic)."
 },
 "sections": [
  {
   "h": "Start-up is work the JVM repeats on every launch",
   "body": S1,
   "try": {
    "title": "Count where your classes come from",
    "minutes": 4,
    "steps": [
     "Read `ClassSourcesDemo`. It starts a second JVM with `-Xlog:class+load`, runs a little start-up work there (regex, `java.time`, a stream, `String.format`), and groups the log lines by `source:`.",
     "Predict: out of roughly 700 classes, how many come from the CDS archive? Then run it with the command below.",
     "Run it again with `-Pargs=-Xshare:off` added. This turns the archive off for the child JVM.",
     "Run the Kotlin twin (`ClassSourcesDemoKt`) once. Look at the `file:` line."
    ],
    "code": demo("ClassSourcesDemo"),
    "expect": "On JDK 21 on a shared Linux VM: 734 classes, 718 from the shared objects file, 8 from `jrt:/`, 7 hidden, and 1 from `file:` (the demo itself). With `-Xshare:off`: 767 classes, 747 parsed from `jrt:/`, 19 hidden, none shared. JDK 25.0.4 loaded 818 with 793 shared, and 831 with sharing off. The Kotlin twin loads 876, with 63 from `file:`, because the Kotlin standard library is a JAR on your classpath like any other."
   },
   "refs": [
    {"title": "The java command (JDK 25 man page source): -Xlog and CDS", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/man/java.md", "kind": "docs"}
   ]
  },
  {
   "h": "Loading is lazy, and initialization is lazier",
   "body": S2,
   "try": {
    "title": "Predict the order of static initializers",
    "minutes": 4,
    "steps": [
     "Open `InitOrderDemo`. `main` calls `Eager.version()`, then `Lazy.version()`, then `Lazy.table()` twice.",
     "Write down the order of the log lines before you run it. Which line appears twice?",
     "Run it. Then run the Kotlin twin, `InitOrderDemoKt`, which compares a companion object, a nested object and `by lazy`."
    ],
    "code": demo("InitOrderDemo"),
    "expect": "Java prints `main starts`, `Eager.<clinit> builds the table`, `Lazy.<clinit> (no table here)`, `-- both versions read --`, `Lazy.Holder.<clinit> builds the table`, `-- Lazy.table() called --`. Calling `Eager.version()` built a table nobody asked for. The second `Lazy.table()` prints nothing: a class is initialized once. In Kotlin, `Fees.version()` builds the companion's table, while `Bins` and `Rates` build theirs only after `-- all three versions read --`."
   },
   "refs": [
    {"title": "JLS 12.4: Initialization of classes and interfaces", "url": "https://docs.oracle.com/javase/specs/jls/se25/html/jls-12.html#jls-12.4", "kind": "docs"}
   ]
  },
  {
   "h": "Three clocks, and only one is what users see",
   "body": S3,
   "figure": {"svg": FIG, "caption": "The JVM's clock stops after VM creation, the framework's after its own start-up, and only the outside probe includes the first request."},
   "try": {
    "title": "Read all three clocks",
    "minutes": 5,
    "steps": [
     "Read `FirstRequestTimer`. It picks a free port, starts the same class as a service in a second JVM, polls `/hello` every 2 ms from outside, and stops the clock at the first 200.",
     "Run it with `-Pargs=-Xlog:startuptime` added to the command below. Note the three numbers.",
     "Predict what `-Pargs=-Xshare:off` does to each clock, then run it."
    ],
    "code": demo("FirstRequestTimer"),
    "expect": "On JDK 21 on a shared 4-vCPU VM: `Create VM` about 0.03 s, `started in` about 0.10 s, first 200 about 160 to 210 ms after launch. With `-Xshare:off`, `started in` rose to 0.167 s and the first 200 to 257 ms, because every JDK class was parsed and verified again. Your machine gives different absolute numbers; compare runs on the same machine only."
   }
  },
  {
   "h": "Footprint is RSS, and the heap is only part of it",
   "body": S4,
   "try": {
    "title": "Committed is not resident",
    "minutes": 3,
    "steps": [
     "Run `FirstRequestTimer` again with `-Pargs=-XX:NativeMemoryTracking=summary`. The demo asks the running service for its NMT summary with `jcmd` before it stops it.",
     "Compare the `Total: committed` line with `VmRSS`. Which one would a 512 MiB container limit compare against?",
     "On Linux, run `cat /proc/self/status | grep Rss` in a shell to see the same fields for `cat` itself."
    ],
    "code": demo("FirstRequestTimer"),
    "expect": "Here NMT reported `committed=290MB` with `Java Heap ... committed=216MB`, while `VmRSS` was about 53,000 kB. The JVM has reserved and committed far more than it has touched. The container limit counts resident memory, so RSS is the number to watch. On macOS the demo prints the `ps` value instead of the `/proc` breakdown."
   },
   "refs": [
    {"title": "Quarkus: Measuring performance (RSS, not docker stats)", "url": "https://github.com/quarkusio/quarkus/blob/main/docs/src/main/asciidoc/performance-measure.adoc", "kind": "read"}
   ]
  }
 ],
 "analogy": "Think of a shop that throws its stock away every night. Each morning someone unpacks every box, checks each item against the invoice, and puts it on a shelf before the first customer comes in. The lights going on is `Create VM`. The \"open\" sign is the framework's `started in` line. The first customer leaving with a receipt is the first 200, and that is the only moment the street cares about. A holder class is a box you leave sealed in the back until somebody asks for what is in it. The analogy breaks in one place: a real shop would keep its shelves stocked overnight. The JVM keeps nothing between runs unless you give it an archive, which is lesson 2.",
 "in_your_world": "Your Quarkus payment service runs as pods behind a readiness probe. Every scale-out under load, every rolling deploy and every `@QuarkusIntegrationTest` JVM pays the whole start-up again, and a new pod is slowest at the moment traffic is highest. Look for static work that every start pays for: a BIN or FX rate table built in a companion object, a Kafka schema registry client created in a static field, a big JSON mapping config parsed in `<clinit>`. Measure from outside: launch the pod and poll `/q/health/ready` until it answers 200, like the lab's probe does. For memory, read `ps -o rss` or `/proc/<pid>/status` inside the container, never `docker stats` and never just the heap from your metrics dashboard.",
 "mistake": "The common mistake is reading the wrong number and tuning against it. A team sees `started in 0.9s` in the Quarkus log and `180 MiB` in `docker stats` and calls it done, while the readiness probe needs 2.5 s to see a 200 and the container's RSS is close to its limit. The framework's clock starts late and stops early, and `docker stats` counts only part of the resident pages. Measure time to first request from outside the process, read RSS from `ps` or `/proc`, and keep NMT for the question of where inside the JVM the memory went.",
 "compare": {
  "title": "A lazy table in Java and in Kotlin",
  "java": {"title": "IssuerDirectory.java", "src": "public final class IssuerDirectory {\n    // eager: built in IssuerDirectory.<clinit>, on the first use of the class\n    private static final Map<String, String> ALIASES = loadAliases();\n\n    // lazy: built in Holder.<clinit>, on the first read of Holder.BINS\n    private static final class Holder {\n        static final Map<String, String> BINS = loadBins();\n    }\n\n    public static String version() { return \"dir-v7\"; }\n    public static String issuerOf(String pan) { return Holder.BINS.get(pan.substring(0, 6)); }\n}"},
  "kotlin": {"title": "IssuerDirectory.kt", "src": "object IssuerDirectory {\n    // eager: built in IssuerDirectory.<clinit>, on the first use of the object\n    private val aliases = loadAliases()\n\n    // lazy: Holder is its own class with its own <clinit>\n    private object Holder {\n        val bins = loadBins()\n    }\n\n    // also lazy, with a visible lock (LazyThreadSafetyMode.SYNCHRONIZED by default)\n    val rates by lazy { loadRates() }\n\n    fun version() = \"dir-v7\"\n    fun issuerOf(pan: String) = Holder.bins[pan.take(6)]\n}"},
  "note": "Both compile to the same JVM mechanism: a static field filled in a class initializer, which runs once, on first active use, under the JVM's class-initialization lock. What differs is where Kotlin puts the fields. Properties of an `object` live in the object's class. Properties of a `companion object` live as static fields of the outer class, so touching the outer class at all builds them. A private nested `object` is the exact twin of Java's holder. `by lazy` is a library feature, not a JVM one: it allocates a `Lazy` object and takes a lock on first access, which costs a little but works for instance properties too, where the holder idiom cannot help."
 },
 "worked": {
  "title": "Find and fix a companion object that builds on start-up",
  "steps": [
   {"say": "A readiness check calls `FxRates.source()` to report where the rates came from. Start-up got 400 ms slower after this class was added. Here it is, with the Java equivalent next to it.",
    "code": "class FxRates {\n    companion object {\n        private val rates: Map<String, Double> = loadRatesFile()   // 400 ms\n\n        fun source() = \"ecb-daily\"\n        fun rate(currency: String) = rates.getValue(currency)\n    }\n}",
    "lang": "kotlin", "alt_lang": "java",
    "alt_code": "public final class FxRates {\n    private static final Map<String, Double> RATES = loadRatesFile();   // 400 ms\n\n    public static String source() { return \"ecb-daily\"; }\n    public static double rate(String currency) { return RATES.get(currency); }\n}"},
   {"say": "Check where the field lives with `javap -p` on the compiled class. The `rates` field sits on `FxRates`, not on the companion, and `FxRates`'s static initializer fills it. So `source()` initializes `FxRates`, and that loads the file.",
    "code": "$ javap -p build/classes/kotlin/main/com/acme/fx/FxRates.class\npublic final class com.acme.fx.FxRates {\n  public static final com.acme.fx.FxRates$Companion Companion;\n  private static final java.util.Map<java.lang.String, java.lang.Double> rates;\n  ...\n  static {};\n}",
    "lang": "text"},
   {"say": "Give the rates their own class. The readiness check now touches only `FxRates`. The first call to `rate` initializes `Holder` and pays the 400 ms once.",
    "code": "object FxRates {\n    fun source() = \"ecb-daily\"\n    fun rate(currency: String) = Holder.rates.getValue(currency)\n\n    // 1. its own class, so its own initializer\n    private object Holder {\n        val rates: Map<String, Double> = loadRatesFile()\n    }\n}",
    "lang": "kotlin", "alt_lang": "java",
    "alt_code": "public final class FxRates {\n    public static String source() { return \"ecb-daily\"; }\n    public static double rate(String currency) { return Holder.RATES.get(currency); }\n\n    // 1. its own class, so its own initializer\n    private static final class Holder {\n        static final Map<String, Double> RATES = loadRatesFile();\n    }\n}"},
   {"say": "Prove it instead of trusting it. Start the service with `-Xlog:class+load` and grep for the holder. Before the fix nothing called `Holder` because it didn't exist. After the fix it must not appear until the first payment that needs a rate.",
    "code": "$ java -Xlog:class+load -jar app.jar | grep FxRates\n[info][class,load] com.acme.fx.FxRates source: file:/srv/app.jar\n... (readiness check passes, first payment arrives) ...\n[info][class,load] com.acme.fx.FxRates$Holder source: file:/srv/app.jar",
    "lang": "text"}
  ]
 },
 "lab": {
  "title": "Take a table off the start-up path, and build a readiness probe",
  "minutes": 15,
  "files": [
   "labs/startup/src/main/java/workbench/startup/l01/BinTable.java",
   "labs/startup/src/main/java/workbench/startup/l01/FirstRequestProbe.java"
  ],
  "run": "./gradlew :startup:test --tests 'workbench.startup.l01.*'",
  "steps": [
   "Run the tests once. Five of the nine fail: `version() does not build the table`, and all four probe tests.",
   "Fix `BinTable` with the holder idiom. Move `TABLE` into a `private static final class Holder` and read `Holder.TABLE` in `issuerOf`. Keep calling `build()`.",
   "Write `FirstRequestProbe.await`. Build one `HttpRequest` with a short timeout. Loop up to `maxAttempts`: send it, record the status as a string, and stop at 200. Catch `java.net.ConnectException` and record `\"refused\"`. Sleep `pause` between attempts.",
   "Run the tests until all nine pass. Then read `BinTableTest`: each test gets a `FreshLoader`, so each one sees a class nobody has initialized yet."
  ],
  "hints": [
   "Why does the test need a fresh class loader? A class is initialized once per loader. If every test used the normal loader, the first test to call `issuerOf` would build the table and every later test would see it already built.",
   "`client.send(request, HttpResponse.BodyHandlers.discarding())` returns a response whose `statusCode()` you need. Nothing else of the body matters.",
   "`ConnectException` extends `IOException`, so catch it first. Treat other `IOException`s (a reset while the server starts) as a failed attempt too."
  ],
  "done_when": "All nine tests in `BinTableTest` and `FirstRequestProbeTest` pass."
 },
 "drill": {
  "title": "Write the holder idiom from memory",
  "minutes": 4,
  "prompt": "Close this page. Write a class `CountryRules` with `static String version()` that returns `\"rules-3\"` and `static String regionOf(String country)` that reads from a map built by an expensive `load()` method. `version()` must never call `load()`, and `load()` must run once even under concurrent first calls, with no `synchronized` in your code. Then write the Kotlin version with an `object`.",
  "answer": {
   "lang": "java",
   "src": "public final class CountryRules {\n    private static final class Holder {\n        // runs once, on the first read of Holder.RULES, under the JVM's init lock\n        static final Map<String, String> RULES = load();\n    }\n\n    public static String version() { return \"rules-3\"; }\n\n    public static String regionOf(String country) {\n        return Holder.RULES.getOrDefault(country, \"unknown\");\n    }\n\n    private static Map<String, String> load() {\n        return Map.of(\"DE\", \"EU\", \"FR\", \"EU\", \"US\", \"NA\");   // imagine a big file\n    }\n}",
   "alt": {
    "lang": "kotlin",
    "src": "object CountryRules {\n    fun version() = \"rules-3\"\n    fun regionOf(country: String) = Holder.rules[country] ?: \"unknown\"\n\n    // a nested object is its own class: initialized on first use, once\n    private object Holder {\n        val rules: Map<String, String> = load()\n    }\n\n    private fun load() = mapOf(\"DE\" to \"EU\", \"FR\" to \"EU\", \"US\" to \"NA\")   // imagine a big file\n}"
   }
  }
 },
 "recap": [
  "A start-up repeats the same work every launch: load, parse and verify about 1,500 classes for a 300-class app, run static initializers, interpret until the JIT has profiles, and run the framework's own start-up.",
  "`-Xlog:class+load` shows each class and its source: `shared objects file` (CDS archive), `jrt:/` (parsed from the JDK), `file:` (your classpath), or a defining class for hidden classes.",
  "A class's `<clinit>` runs on first active use. A Kotlin companion's properties are static fields of the outer class; a nested `object` or a Java holder class is lazy.",
  "Three clocks: `Create VM` from `-Xlog:startuptime`, the framework's `started in`, and time to first request from outside. Only the last is what a probe or user sees.",
  "Footprint is the whole process's RSS. NMT committed memory includes untouched pages, and `docker stats` sees only part of the resident set."
 ],
 "quiz": [
  {"q": "A Kubernetes readiness probe decides when your new pod gets traffic. Which number tells you how long that takes?",
   "options": ["The `Create VM` line from `-Xlog:startuptime`", "The framework's `started in` log line", "Time from launching the process until the readiness endpoint returns 200, measured from outside", "The time until C2 has compiled the hot methods"],
   "answer": 2,
   "why": "The probe sees only the outside clock: launch to first successful response. `Create VM` stops before your code runs, and the framework's line is measured inside the process from wherever that framework starts counting. C2 compilation is about peak speed, which comes later still."},
  {"q": "A health check calls `IssuerDirectory.version()`. In Kotlin the class is `class IssuerDirectory { companion object { val bins = loadBins(); fun version() = \"v3\" } }`. Does the health check run `loadBins()`?",
   "options": ["No, companion objects are initialized lazily on first property access", "Yes: `bins` is a static field of `IssuerDirectory`, filled by its static initializer, which runs on this first use", "Only if the health check runs on a different thread", "No, because `version()` does not read `bins`"],
   "answer": 1,
   "why": "Kotlin compiles a companion's properties to static fields on the outer class and initializes them in the outer class's `<clinit>`. Calling `version()` goes through `IssuerDirectory.Companion`, which initializes `IssuerDirectory`, which runs `loadBins()`. A private nested `object` or `by lazy` would keep it off this path."},
  {"q": "For one service you see: `docker stats` 180 MiB, NMT total committed 420 MiB, live heap after GC 90 MiB, `ps -o rss` 260 MiB. Which number is the footprint that counts against the container's memory limit?",
   "options": ["180 MiB from docker stats", "420 MiB committed", "90 MiB of live heap", "260 MiB of RSS"],
   "answer": 3,
   "why": "RSS counts every resident page of the process, heap or not. Committed memory includes pages nobody has touched yet, live heap ignores metaspace, code cache, thread stacks and the rest, and the Quarkus guide warns that `docker stats` measures only a subset of the resident pages."},
  {"q": "Which of these runs the static initializer of class `Fees` (assuming nothing else has)?",
   "options": ["`Class.forName(\"com.acme.Fees\", false, loader)`", "Declaring a local variable `Fees f = null;`", "Calling the static method `Fees.version()`", "Writing `Fees.class` to get its Class object"],
   "answer": 2,
   "from": "cls-01",
   "why": "Initialization happens on first active use, and a static method call is one. `Class.forName` with `initialize=false` loads the class without initializing it, a variable declaration needs neither, and a class literal gives you the `Class` object without running `<clinit>`."},
  {"q": "You run the same service with `-Xshare:off`. The number of loaded classes barely changes, but time to first request goes up by about 80 ms. Why?",
   "options": ["The JDK classes are now read and parsed from the modules file and verified, instead of mapped ready-made from the CDS archive", "The JIT is disabled with sharing off", "The heap is smaller, so the GC runs more", "The JVM now loads your classes twice"],
   "answer": 0,
   "why": "`-Xshare:off` turns off the default CDS archive. The same classes still load, but each one now goes through finding, parsing and verifying in the JVM. In the demo the `jrt:/` count jumped from 8 to 747. The JIT and the heap are not affected by this flag."}
 ],
 "flashcards": [
  {"front": "What does each line of `-Xlog:class+load` tell you?", "back": "The class name and its `source:`: `shared objects file` (CDS archive), `jrt:/...` (parsed from the JDK modules file), `file:...` (your classpath), or a defining class name for a hidden class such as a lambda."},
  {"front": "When does the JVM run a class's `<clinit>`?", "back": "On first active use: `new`, a static method call, a read or write of a non-constant static field, initializing reflection, or initializing a subclass. Loading the class alone does not run it."},
  {"front": "Why is the holder idiom thread-safe with no lock in your code?", "back": "The JVM initializes each class under its own initialization lock (JLS 12.4.2). One thread runs `Holder.<clinit>`; the others wait and then see the finished field."},
  {"front": "Is a Kotlin `companion object` property initialized lazily?", "back": "No. It compiles to a static field of the outer class, filled by the outer class's `<clinit>`, so any first use of the outer class builds it. Use a private nested `object` or `by lazy`."},
  {"front": "What does the `Create VM` line of `-Xlog:startuptime` measure?", "back": "Only the JVM's own creation, before `main` runs. Not class loading for your app, not framework start, not the first request."},
  {"front": "NMT says 290 MB committed and RSS is 53 MB. Which is resident memory?", "back": "RSS. Committed memory has been requested from the OS, but untouched pages (most of a fresh heap) are not resident."},
  {"front": "Why not use `docker stats` for a JVM's footprint?", "back": "It measures only a subset of the resident pages (Quarkus's measuring guide). Use `ps -o rss`, `docker top <id> -o pid,rss,args` or `/proc/<pid>/status`."}
 ],
 "terms": [
  {"term": "Class loading", "plain": "Finding a class's bytes and turning them into the JVM's internal form in metaspace."},
  {"term": "Verification", "plain": "The check, done while linking, that a class's bytecode is type-safe before it runs."},
  {"term": "Static initializer (`<clinit>`)", "plain": "The method that sets a class's static fields and runs its static blocks, once, on first active use."},
  {"term": "Holder idiom", "plain": "Putting an expensive static field in a small nested class, so it is built on first use of that field only."},
  {"term": "Hidden class", "plain": "A class the JVM defines at run time with no class file, for example for a lambda."},
  {"term": "Time to first request", "plain": "From launching the process to the first successful response, measured from outside."},
  {"term": "RSS", "plain": "Resident set size: the memory pages of a process that are actually in RAM."},
  {"term": "NMT", "plain": "Native Memory Tracking: the JVM's own breakdown of the memory it has reserved and committed."}
 ],
 "explain_back": {
  "prompt": "A teammate says: \"Our service starts in 0.9 seconds and uses 180 MiB. I read it in the Quarkus log and in docker stats.\" Explain what each number leaves out and what you would measure instead.",
  "answer": "The 0.9 seconds is the framework's own clock, taken inside the process. It starts after the launcher and JVM creation, and it stops before the first request, which loads more classes and runs in the interpreter. The readiness probe and the users see the time from launch to the first 200, so I'd poll the readiness endpoint from outside and time that. The 180 MiB from docker stats covers only part of the resident pages. The container is killed on its full RSS, which includes metaspace, the code cache, thread stacks, the mapped archive and the touched heap. I'd read RSS with `ps -o rss` or `/proc/<pid>/status`, and use NMT only to see which part of the JVM the memory went to."
 },
 "deeper": {
  "minutes": 10,
  "body": "Loading is lazy, but not as lazy as the rule above suggests. Two things load classes you never called.\n\nThe first is the verifier. To check that a method is type-safe, it sometimes needs to know whether one class is a subtype of another, for example when two branches produce different classes that meet at the same variable. To answer that, it loads both classes. Lesson 2's lab hits this: a test fixture whose static initializer referenced an outer class pulled in the outer class and more. That is why the lab compares the exact set of classes your loader defined, taken from a run of the reference answer, and never a count of all loaded classes, which changes from one JDK build to the next.\n\nThe second is the framework. Annotation scanning reads class files to find `@Path` or `@ApplicationScoped`, and reflection-driven dependency injection loads every bean class at start-up. This is the work Quarkus moves to build time. At build time it indexes the classes (Jandex), decides the wiring and generates plain bytecode that does it, so at run time there is no scanning and much less reflection. Its extension guide puts it as registering classes \"at build time and generating code that registers them at static-init time instead of relying on reflection\". Spring's AOT mode makes a similar move with a different design.\n\nIf you want to see where a large app spends its start-up, `-Xlog:class+load` piped through `sed -E 's/.*source: //' | sort | uniq -c | sort -rn | head` gives the same histogram as the demo, and the JFR `jdk.ClassLoad` event (off by default) gives you stack traces for who triggered each load. Measure first, then pick a fix from lessons 2 to 4."
 },
 "sources": [
  {"title": "The java command, JDK 25 (man page source: -Xlog, CDS, AOT cache)", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/man/java.md"},
  {"title": "Java Virtual Machine Specification, chapter 5: Loading, Linking, and Initializing", "url": "https://docs.oracle.com/javase/specs/jvms/se25/html/jvms-5.html"},
  {"title": "Java Language Specification 12.4.2: Detailed initialization procedure", "url": "https://docs.oracle.com/javase/specs/jls/se25/html/jls-12.html#jls-12.4.2"},
  {"title": "Quarkus guide: Measuring performance", "url": "https://github.com/quarkusio/quarkus/blob/main/docs/src/main/asciidoc/performance-measure.adoc"}
 ]
}
out = ROOT / "content/lessons/boot-01.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
