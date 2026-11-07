import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/container/src"
J = "java/workbench/container/l03"
K = "kotlin/workbench/container/l03"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :container:demo -Pmain=workbench.container.l03.demo."


def demo(name):
    """A Java demo and its Kotlin twin, read from disk."""
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{J}/demo/{name}.java"),
            "run": RUN + name, "file": f"{lab}/demo/{J}/demo/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/demo/{name}.kt"),
                    "run": RUN + name + "Kt", "file": f"{lab}/demo/{K}/demo/{name}.kt"}}


FIGURE = """<svg viewBox="0 0 700 250" role="img" aria-label="Two rows. Run-time wiring scans, reflects, orders the graph and generates proxies with Byte Buddy on every start. Build-time wiring scans, orders the graph, writes Java source and compiles it once per build, so a start only runs holder initializers.">
<text class="t t-a" x="20" y="28">run time: on every start (lessons 1 and 2)</text>
<rect class="box" x="20" y="44" width="90" height="38" rx="8"/><text class="t" x="65" y="68" text-anchor="middle">scan</text>
<rect class="box" x="125" y="44" width="120" height="38" rx="8"/><text class="t" x="185" y="68" text-anchor="middle">reflection</text>
<rect class="box" x="260" y="44" width="100" height="38" rx="8"/><text class="t" x="310" y="68" text-anchor="middle">graph</text>
<rect class="box-bad" x="375" y="44" width="120" height="38" rx="8"/><text class="t" x="435" y="68" text-anchor="middle">Byte Buddy</text>
<rect class="box-ok" x="600" y="44" width="80" height="38" rx="8"/><text class="t" x="640" y="68" text-anchor="middle">ready</text>
<line class="ln" x1="110" y1="63" x2="123" y2="63" marker-end="url(#arr)"/>
<line class="ln" x1="245" y1="63" x2="258" y2="63" marker-end="url(#arr)"/>
<line class="ln" x1="360" y1="63" x2="373" y2="63" marker-end="url(#arr)"/>
<line class="ln" x1="495" y1="63" x2="598" y2="63" marker-end="url(#arr)"/>
<text class="t-s t-m" x="546" y="56" text-anchor="middle">2,207 classes</text>
<text class="t t-a" x="20" y="134">build time: once per build (this lesson)</text>
<rect class="box-dim" x="12" y="142" width="490" height="54" rx="8"/>
<rect class="box" x="20" y="150" width="90" height="38" rx="8"/><text class="t" x="65" y="174" text-anchor="middle">scan</text>
<rect class="box" x="125" y="150" width="100" height="38" rx="8"/><text class="t" x="175" y="174" text-anchor="middle">graph</text>
<rect class="box" x="240" y="150" width="130" height="38" rx="8"/><text class="t" x="305" y="174" text-anchor="middle">write source</text>
<rect class="box" x="385" y="150" width="110" height="38" rx="8"/><text class="t" x="440" y="174" text-anchor="middle">javac, jar</text>
<rect class="box-a" x="510" y="150" width="80" height="38" rx="8"/><text class="t" x="550" y="174" text-anchor="middle">holders</text>
<rect class="box-ok" x="600" y="150" width="80" height="38" rx="8"/><text class="t" x="640" y="174" text-anchor="middle">ready</text>
<line class="ln" x1="110" y1="169" x2="123" y2="169" marker-end="url(#arr)"/>
<line class="ln" x1="225" y1="169" x2="238" y2="169" marker-end="url(#arr)"/>
<line class="ln" x1="370" y1="169" x2="383" y2="169" marker-end="url(#arr)"/>
<line class="ln-d" x1="495" y1="169" x2="508" y2="169" marker-end="url(#arr)"/>
<line class="ln" x1="590" y1="169" x2="598" y2="169" marker-end="url(#arr)"/>
<text class="t-s t-m" x="257" y="216" text-anchor="middle">on the build machine; a cycle fails the build</text>
<text class="t-s t-m" x="595" y="216" text-anchor="middle">start: 991 classes</text>
<text class="t-s t-m" x="595" y="234" text-anchor="middle">no reflection</text>
</svg>"""

HISTOGRAM = """$ jcmd 2158 GC.class_histogram | grep -E 'workbench|Proxy|ByteBuddy|ByteArray'
 100:            42            672  jdk.proxy2.$Proxy8 (jdk.proxy2)
 144:            13            312  workbench.container.l03.Container$$Lambda/0x00007f0630008aa8
 145:            13            312  workbench.container.l03.SingletonCell
 254:             1            112  net.bytebuddy.dynamic.loading.ByteArrayClassLoader
 285:             4             96  workbench.container.l03.TimedInterceptor
 396:             2             48  workbench.container.l03.RetryInterceptor
 523:             1             32  workbench.container.l03.Container
 760:             1             24  workbench.container.l03.InterceptingHandler
 866:             1             16  jdk.proxy2.$Proxy6 (jdk.proxy2)
 910:             1             16  workbench.container.l03.SettlementService$ByteBuddy$iUqWQUJF
 911:             1             16  workbench.container.l03.SubclassBridge
 ...                                (81 lines in all: more $Proxy classes, net.bytebuddy types, beans)

$ jcmd 2158 GC.heap_dump /home/.../labs/container/build/heapdumps/container.hprof
2158:
Dumping heap to /home/.../labs/container/build/heapdumps/container.hprof ...
Heap dump file created [8078672 bytes in 0.028 secs]"""

BASH_ARCHIVE = """# from labs/, after StartupLadder has run once: it wrote app.jar and classpath.txt
cd container/build/cap4
CP=$(cat classpath.txt)
MAIN=workbench.container.l03.demo.StartupLadder

# JDK 21 or later: a dynamic AppCDS archive for the reflective start
java -XX:ArchiveClassesAtExit=reflective.jsa -cp "$CP" $MAIN --reflective 2>&1 | grep -c 'Unsupported location'
java -XX:SharedArchiveFile=reflective.jsa -Xlog:class+load -cp "$CP" $MAIN --reflective \\
    | grep -o 'source: __[A-Za-z_]*' | sort | uniq -c

# JDK 25.0.4 or later: the one-step AOT cache for the generated registry
java -XX:AOTCacheOutput=generated.aot -cp "$CP" workbench.container.l03.demo.gen.GeneratedStart
java -XX:AOTCache=generated.aot -Xlog:aot -cp "$CP" workbench.container.l03.demo.gen.GeneratedStart | grep Opened"""

L = {
 "id": "cap4-03",
 "title": "Measure it, then make it start fast",
 "minutes": 40,
 "goal": "By the end you can measure what the container's proxies cost per call and at start-up, read a class histogram and a heap dump of the running container, generate its wiring at build time as plain Java, and defend when run-time or build-time wiring is the right design.",
 "warmup": {
  "q": "The reflective container wires a 14-component payment app with one JDK proxy and one Byte Buddy subclass. Roughly how many classes does that JVM load before the first payment is done?",
  "options": ["About 30: the 14 components and a few container classes", "About 1,000, the same as any small Java program", "More than 2,000", "About 15,000"],
  "answer": 2,
  "why": "On JDK 21 the reflective start loaded 2,207 classes: 814 of them from the Byte Buddy JAR, 30 JDK proxy classes, 3 classes Byte Buddy generated, and over a hundred hidden classes for lambdas and method handles. The same app wired by generated code loaded 991. Most of a container's start-up cost is the machinery, not your components."
 },
 "sections": [
  {
   "h": "A proxied call costs nanoseconds and a couple of hundred bytes",
   "body": """Start with the cost per call, measured the way *Benchmarking with JMH, and the traps it saves you from* taught: the result returned, the input in a non-final `@State` field, and `-prof gc` for bytes. `ProxyCallBench` calls one fee calculation four ways. Each interceptor chain holds a single interceptor that only calls `proceed()`, so the numbers are the proxies' own cost, and the direct call is the baseline. One run on this course's 4-vCPU VM, which was shared with other builds at the time:

| Call | ns/op | B/op |
|---|---|---|
| direct | 3.2 | 0 |
| generated forwarding class (this lesson) | 4.0 | 0 |
| Byte Buddy subclass (lesson 2) | 90 | 160 |
| JDK proxy (lesson 2) | 112 | 208 |

The time error bars were larger than most of the scores, so read only the order. The bytes are exact and the same on every run, which is why they are the number to trust.

Where do 208 bytes come from? The JDK proxy's generated method boxes the `long` argument and puts it in an `Object[]`. The handler builds an `Invocation` for each step of the chain and a lambda for the target call. `Method.invoke` boxes the result. The generated forwarding class does the same things in its source: `new Object[] {p0}`, `new Invocation(...)`, a lambda. But its whole call is plain code that C2 can inline, and once inlined none of those objects leaves the compiled method. Escape analysis, from *Allocation, TLABs and escape analysis*, removes them all. On the two reflective paths C2 couldn't see the whole call, so the objects stay. Don't build on that zero: as the Try it shows, one more interceptor is enough to lose it. The Kotlin twin counts the same calls in a plain loop and gets 0, 208, 192 and 48 bytes: the same order, with less of the generated class's allocation removed.

Does it matter? At 2,000 issuer calls a second, 208 bytes is 400 KB/s of garbage, next to a 120 ms network call: nothing. In a loop that prices 10,000 line items through a proxied `FeeCalculator`, it is 2 MB per batch. Proxy the issuer client, not the arithmetic.""",
   "try": {
    "title": "Count the bytes per call",
    "minutes": 4,
    "steps": [
     "Read `ProxyCallBench`. Predict the B/op of each of the four benchmarks before you run it.",
     "Run it (it forks four JVMs, about 10 seconds). Then run the Kotlin twin, which counts bytes with the per-thread allocation counter instead of JMH.",
     "In `ProxyCallBench`, add a second `PASS` to `CHAIN` (`List.of(PASS, PASS)`) and run it again. Which rows change?"
    ],
    "code": demo("ProxyCallBench"),
    "expect": "`direct` and `generated` show 0.0 B/op, `byteBuddy` 160 and `jdkProxy` 208 (or very close), every run. Times jump around, with errors larger than the scores on a busy machine, but `direct` and `generated` stay within a few nanoseconds and the two reflective paths are far slower. With two interceptors every row but `direct` allocates more. In one run the reflective rows grew by 32 bytes each (one more `Invocation`, to 192 and 240), and `generated` jumped from 0 to 128 B/op: with the longer chain, escape analysis no longer removed its objects. That is why *Allocation, TLABs and escape analysis* said to show escape analysis in demos and never assert it in tests. Change the chain back afterwards. The Kotlin twin prints 0, 208, 192 and 48 bytes per call."
   },
   "refs": [
    {"title": "JMHSample_35_Profilers (the GC profiler)", "url": "https://github.com/openjdk/jmh/blob/master/jmh-samples/src/main/java/org/openjdk/jmh/samples/JMHSample_35_Profilers.java", "kind": "read"}
   ]
  },
  {
   "h": "At start-up the reflective container loads Byte Buddy and generates classes",
   "body": """The per-call cost is small. The start-up cost is not. `StartupLadder` packs the demo app into a JAR and starts it in fresh JVMs, counting `-Xlog:class+load` lines by their `source:` as *Why the JVM starts slowly, and how to measure it* did. On JDK 21:

```text
setup                       loaded  archived  run-time  ready ms  wall ms
reflective + Byte Buddy       2207       953       156      1029     1307
    parsed from byte-buddy.jar 814, JDK proxies 30, defined from bytes 3, hidden 123
generated registry             991       834        51       266      418
```

The 1,216 extra classes are all machinery. 814 come from `byte-buddy-1.18.17.jar`: the library has to load its own type model, its matchers and its class writer before it can write one subclass. The 3 classes `defined from bytes` (`source: __JVM_DefineClass__`) are what it wrote: `SettlementService$ByteBuddy$...` and two `$auxiliary$` classes, the `@SuperCall` callables for `settle` and `audit`. Then 30 JDK proxy classes (`__dynamic_proxy__`). Only one of them is the issuer proxy. Every annotation you read through reflection is an instance of a proxy class the JDK generates for that annotation type, so `getAnnotation(Component.class)` and `isAnnotationPresent(Timed.class)` generate classes too, and Byte Buddy uses a few proxies inside. The 123 hidden classes are lambdas and method handles; since JDK 18 core reflection itself runs on method handles, so every reflective call path adds some.

Each of those classes is found, parsed and verified, and then run in the interpreter, because nothing is hot yet (*From bytecode to machine code: interpreter, C1, C2*). That is why `ready` (from the first line of `main` to the first payment done) was 1,029 ms against 266 ms. The machine was busy and the times moved by a factor of two between runs. The reflective start was always several times slower, and the class counts barely moved.

None of this is Byte Buddy being slow. It is doing at every start what a compiler could have done once.""",
   "try": {
    "title": "Count what each start loads",
    "minutes": 5,
    "steps": [
     "Read `StartupLadder` (the Kotlin twin runs the first two rows). It generates the registry, compiles it with javac, packs `container/build/cap4/app.jar`, and starts the app in child JVMs.",
     "Predict the `loaded` column for the first two rows, and the `parsed from byte-buddy.jar` count for the generated registry.",
     "Run it. It takes about 10 seconds. Ignore the last two rows until section 5."
    ],
    "code": demo("StartupLadder"),
    "expect": "On JDK 21 the reflective start loads about 2,200 classes, 814 of them parsed from the Byte Buddy JAR, plus 30 JDK proxies and 3 classes defined from bytes. The generated registry loads about 990 and none of those. Its 51 hidden classes are mostly the lambdas in the generated interceptor classes and the JDK's own. `ready` and `wall` differ by machine and run, but the reflective start is several times slower each time. Another JDK version gives other counts; the gap between the two rows is what to look at."
   }
  },
  {
   "h": "Move the wiring to build time: generate the registry",
   "body": """Everything the reflective container works out at start-up depends only on the classes, and the classes are fixed when you build. So do the work then. `RegistryGenerator` runs the same `BeanGraph` from lesson 1 at build time: it picks the constructors, orders the graph and checks for cycles, and a cycle now fails the build instead of the deploy. Then it writes a Java class that does the wiring with plain `new` calls. The lab's test compiles that class with javac, the way a build would.

Each singleton gets a holder class. Lesson 1 promised it:

```java
private static final class FeeCalculator_Holder {
    static final FeeCalculator INSTANCE = new FeeCalculator(FxRates_Holder.INSTANCE);
}
```

```kotlin
private object FeeCalculatorHolder {
    val INSTANCE = FeeCalculator(FxRatesHolder.INSTANCE)    // a Kotlin object is a holder class too
}
```

The JVM initializes `FeeCalculator_Holder` the first time `get` touches it, once, under the class initialization lock from *Class loading: loaders, delegation, linking and initialization*. Its dependency is another holder, initialized first. There is no `volatile`, no lock after the first call, and no map: `get` is a list of `if (type == FeeCalculator.class)` checks. Prototypes get a factory method instead.

Interceptors become source too. For `CardIssuerClient` the generator writes `HttpIssuerClient_Proxy implements CardIssuerClient`, and for `SettlementService` it writes `SettlementService_Intercepted extends SettlementService`, the same two models as lesson 2. It reads `@Timed` and `@Retry` now and writes their values into the code, `INTERCEPTION.chain(true, 3, IssuerUnavailableException.class)`, so nothing reads an annotation at run time. Quarkus ArC does this with its generated `_Subclass` classes. Micronaut does the graph work in an annotation processor while javac runs, and Spring's AOT processing generates bean definitions as code ahead of time.

You give up two things. The set of components is fixed when you build: nothing can scan a plugin directory at start-up or choose a bean from an environment variable without code the generator wrote for it. And a holder fails forever. If `PaymentService`'s constructor throws on first use, the JVM marks `PaymentService_Holder` as failed, and every later `get` throws `NoClassDefFoundError` until you restart, where lesson 1's cell would simply try again.""",
   "figure": {"svg": FIGURE, "caption": "The same steps in both rows. Build-time wiring runs all of them but the last on the build machine, once."},
   "try": {
    "title": "Read the class the generator writes",
    "minutes": 4,
    "steps": [
     "Run `GenerateDemo` (or the Kotlin twin). It prints the registry the generator writes for the demo app, then tries a graph with a cycle.",
     "Find `PaymentService_Holder`. Which holders must the JVM initialize before it, and in what order?",
     "Find `SettlementService_Intercepted.audit`. Which line makes `settle`'s self-call go through the chain?"
    ],
    "code": demo("GenerateDemo"),
    "expect": "About 156 lines: 13 holder classes, one factory method (`new_PaymentAttempt`, the prototype), a `get` with one identity check per bound type, and two generated interceptor classes. `PaymentService_Holder` reads `HttpIssuerClient_Holder` (which reads `IssuerConfig_Holder`), `FeeCalculator_Holder`, `RiskRules_Holder` and `Ledger_Holder`, so the JVM initializes those first, in the order the constructor's arguments are evaluated. `settle` reaches `audit` through `this`, which is the `_Intercepted` object, so its overriding `audit` runs the chain before `super.audit(p0)`. The last line is `the build fails: Dependency cycle: Payouts -> Statements -> Payouts`."
   },
   "refs": [
    {"title": "Quarkus: Writing your own extension (do the work at build time)", "url": "https://github.com/quarkusio/quarkus/blob/main/docs/src/main/asciidoc/writing-extensions.adoc", "kind": "read"}
   ]
  },
  {
   "h": "Look inside the running container: a histogram and a heap dump",
   "body": """Measure the running container from outside, as *Hunting memory leaks: heap dumps, native memory and off-heap* did. `jcmd <pid> GC.class_histogram` runs a full GC and counts the live objects of every class. Here is the reflective container after one payment, one refund and one payout, trimmed:

```text
 num     #instances         #bytes  class name (module)
 100:            42            672  jdk.proxy2.$Proxy8 (jdk.proxy2)
 145:            13            312  workbench.container.l03.SingletonCell
 176:            14            224  jdk.proxy2.$Proxy2 (jdk.proxy2)
 254:             1            112  net.bytebuddy.dynamic.loading.ByteArrayClassLoader
 523:             1             32  workbench.container.l03.Container
 866:             1             16  jdk.proxy2.$Proxy6 (jdk.proxy2)
 910:             1             16  workbench.container.l03.SettlementService$ByteBuddy$iUqWQUJF
```

Read it like a ledger. 13 `SingletonCell`s are the 14 components minus the one prototype. One `$Proxy6` is the issuer proxy. One `ByteArrayClassLoader` holds the Byte Buddy subclass and its two helper classes, and one `SettlementService$ByteBuddy$...` is the bean. The other proxy objects are not beans. In this run `$Proxy2`, with 14 instances, is the `@Component` annotation, one instance per component class, and `$Proxy8`, with 42, is a proxy Byte Buddy uses to call JDK methods that don't exist on every Java version it supports (its `JavaDispatcher`). There were 119 proxy objects in all, and one of them was a bean.

The histogram says what is alive, not who holds it. `jcmd <pid> GC.heap_dump <file>` writes every object and reference to an HPROF file, 8 MB here. The JVM pauses while it writes, so on a production pod take it when you can afford a pause. In Eclipse MAT, "Path to GC Roots" on the `SettlementService$ByteBuddy$...` object should lead through `SingletonCell.instance` and the container's `singletons` map to the `Container`, held by a local variable of the `main` thread.

The demo also proves it by letting go. It drops its only reference to the container and asks for a GC. Byte Buddy's class loader is collected, and with it the generated class: a class keeps its loader alive and an object keeps its class alive, so once the container was unreachable, the whole chain was. The JDK proxy class stays loaded, because it was defined in the application class loader and is cached by `Proxy` for that loader. The annotation instances stay too, cached with the classes and methods they annotate.

The generated registry has a different root. Its singletons are static fields of holder classes, so they live as long as the class loader that loaded the registry. That is why the lab's tests load a fresh copy of the class for every test.""",
   "try": {
    "title": "Take a histogram and a heap dump of the container",
    "minutes": 6,
    "steps": [
     "Run `RunningContainer` with `-Pargs=wait` added to the command below. It wires the app, makes three calls, prints its pid and two `jcmd` commands, and waits.",
     "In a second terminal, from `labs/`, run the two commands it printed. Count the `SingletonCell`s, the `ByteArrayClassLoader`s and the `$ByteBuddy$` instances before you look at the answer.",
     "Optional: open `container/build/heapdumps/container.hprof` in Eclipse MAT and use \"Path to GC Roots\" on the `SettlementService$ByteBuddy$...` object.",
     "Press Enter in the first terminal. It drops the container. Run the histogram command again, then press Enter to end. Without `-Pargs=wait`, the demo (and its Kotlin twin) runs both `jcmd` commands itself and prints a shorter, grouped histogram."
    ],
    "code": demo("RunningContainer"),
    "expect": "Real output from one run, trimmed:\n\n```text\n" + HISTOGRAM + "\n```\n\nThe numbers after `$Proxy` and the random `$ByteBuddy$` suffix differ per run. After you press Enter the demo prints `Byte Buddy's class loader collected: true` and `jdk.proxy2.$Proxy6 still loaded: true`, and the second histogram has no `SingletonCell`, no `Container`, no `ByteArrayClassLoader` and no beans. What is left of `workbench.container.l03` is static: enum constants, cached lambdas and `Interception$Companion`."
   },
   "refs": [
    {"title": "The jcmd command, JDK 25 man page source: GC.class_histogram and GC.heap_dump", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.jcmd/share/man/jcmd.md", "kind": "docs"}
   ]
  },
  {
   "h": "Archive what is left: AppCDS on JDK 21, the AOT cache on JDK 25",
   "body": """*Class data sharing and Project Leyden's AOT cache* showed how to skip parsing and verifying classes at start-up. Apply it to both containers and the last two rows of `StartupLadder` appear:

```text
reflective, AppCDS            2145      2037       108       544      858
    parsed from byte-buddy.jar 0, JDK proxies 30, defined from bytes 3, hidden 75
generated, AppCDS              882       847        35       143      362
    parsed from byte-buddy.jar 0, JDK proxies 0, defined from bytes 0, hidden 35
```

AppCDS took Byte Buddy's 814 classes from the archive and nearly halved the reflective start. It could not take the classes made at run time. When the archive was written, JDK 21 printed `Skipping jdk/proxy2/$Proxy3: Unsupported location` for each of the 30 proxy classes, and the archived run still logs Byte Buddy's three classes as `__JVM_DefineClass__`: defined from bytes by its own class loader, at every start. So every start still generates and verifies them, and still runs the code that generates them. The generated registry has nothing of the kind: its only run-time classes are 35 hidden ones for lambdas.

The AOT cache on JDK 25 goes further for the classes it can store: they arrive loaded and linked, with profiles from the training run. Use JDK 25.0.4 or later, as that lesson explained. The custom-loader limit stays: as Quarkus's AOT guide puts it, Leyden doesn't support custom class loaders yet, so Byte Buddy's classes are made at every start either way.

The registry is also the shape native image wants (*GraalVM native image and Quarkus native*). It has no reflection to declare and no classes defined at run time, which a closed world can't contain. That is the whole argument for build-time wiring in one sentence: the less a start has to discover, generate and verify, the more of it a cache, an archive or a native build can do for you.""",
   "try": {
    "title": "Archive both starts",
    "minutes": 4,
    "steps": [
     "Run `StartupLadder` once (section 2), so `app.jar` and `classpath.txt` exist in `container/build/cap4`.",
     "Run the two JDK 21 commands. Predict both numbers before you run them: how many classes does the archive refuse, and which run-time classes remain?",
     "If you have JDK 25.0.4 or later, run the last two commands with its `java`."
    ],
    "code": {"lang": "bash", "title": "terminal (from labs/)", "src": BASH_ARCHIVE, "run": ""},
    "expect": "On JDK 21 the first command prints 30: one `Unsupported location` warning per proxy class. The second prints `3 source: __JVM_DefineClass__`, `75 source: __JVM_LookupDefineClass__` and `30 source: __dynamic_proxy__`: the Byte Buddy classes, hidden classes and proxies that every start still makes, even with the archive. On JDK 25.0.4 or later the AOT cache commands should end with `Opened AOT cache generated.aot.` (this course's machine had only JDK 21, so that line comes from the start-up track's runs, not from this app)."
   },
   "refs": [
    {"title": "JEP 483: Ahead-of-Time Class Loading & Linking", "url": "https://openjdk.org/jeps/483", "kind": "read"}
   ]
  }
 ],
 "analogy": "Run-time wiring is a wedding caterer who arrives with raw ingredients and a recipe book, and starts cooking when the guests sit down. It works for any menu, even one changed that morning, and the guests wait. Build-time wiring is the caterer who cooks the day before and only reheats. Dinner is fast, and the menu is fixed the night before: a guest who arrives with a new allergy gets whatever was planned. AppCDS is a faster stove, and it helps both caterers, but only the second one has nothing left to cook. The analogy breaks at freshness: reheated code is exactly as good as fresh, and the JIT still warms it up after the start.",
 "in_your_world": "This lesson is the reason Quarkus moved its container to build time: ArC does the equivalent of this generator during the Maven build, so your pods start without scanning the class path for beans, and its interceptors are ordinary generated subclasses. The habits that keep that true are concrete. Put configuration a component needs at start-up into build-time properties only when it really is fixed per build. Treat a reflection call or a run-time proxy on the start-up path as a cost you can count with `-Xlog:class+load`. Read `jcmd GC.class_histogram` on a running pod before guessing what a container keeps. And when a pod's readiness probe is slow, compare the class count of a cold start before and after the last dependency upgrade.",
 "mistake": "The common mistake is measuring the wrong cost. Teams benchmark one proxied call, find a few nanoseconds, and conclude that proxies are free, while the start-up cost (thousands of classes loaded, generated, verified and interpreted before the first request) never appears in a microbenchmark. Others go the other way and remove a proxy from a component that makes one network call a second. People make it because JMH is the tool they know for performance. The fix is to measure both clocks, the way this lesson did: B/op from JMH for the hot path, and `-Xlog:class+load` counts plus time to the first request for the start, each on its own, before changing anything.",
 "compare": {
  "title": "A generated registry in Java and the same idea written by hand in Kotlin",
  "java": {
   "title": "AppRegistry.java (generated, trimmed)",
   "src": "public final class AppRegistry implements Registry {\n    private static final class FxRates_Holder {\n        static final FxRates INSTANCE = new FxRates();\n    }\n\n    private static final class FeeCalculator_Holder {\n        static final FeeCalculator INSTANCE = new FeeCalculator(FxRates_Holder.INSTANCE);\n    }\n\n    private static PaymentAttempt new_PaymentAttempt() {        // a prototype\n        return new PaymentAttempt(FeeCalculator_Holder.INSTANCE);\n    }\n\n    @Override\n    public <T> T get(Class<T> type) {\n        if (type == FxRates.class) return type.cast(FxRates_Holder.INSTANCE);\n        if (type == FeeCalculator.class) return type.cast(FeeCalculator_Holder.INSTANCE);\n        if (type == PaymentAttempt.class) return type.cast(new_PaymentAttempt());\n        throw new ContainerException(\"No component provides \" + type.getSimpleName());\n    }\n}"
  },
  "kotlin": {
   "title": "AppRegistry.kt (by hand)",
   "src": "object AppRegistry {\n    private object FxRatesHolder { val INSTANCE = FxRates() }\n    private object FeeCalculatorHolder { val INSTANCE = FeeCalculator(FxRatesHolder.INSTANCE) }\n\n    private fun newPaymentAttempt() = PaymentAttempt(FeeCalculatorHolder.INSTANCE)   // a prototype\n\n    @Suppress(\"UNCHECKED_CAST\")\n    fun <T> get(type: Class<T>): T = when (type) {\n        FxRates::class.java -> FxRatesHolder.INSTANCE\n        FeeCalculator::class.java -> FeeCalculatorHolder.INSTANCE\n        PaymentAttempt::class.java -> newPaymentAttempt()\n        else -> throw ContainerException(\"No component provides ${type.simpleName}\")\n    } as T\n}"
  },
  "note": "Both compile to the same mechanism: one class per singleton whose static initializer builds it on first use, under the JVM's class initialization lock. A Kotlin `object` is that holder class, with its instance in a static `INSTANCE` field. The difference is who writes it. The Java one comes from a generator and is never edited; the Kotlin one is the kind of code Dagger generates, written by hand, which is fine for ten components and painful for eighty. You don't need `by lazy` here: it would work, but it adds a `Lazy` object per bean and a volatile read per access to do what the class initialization lock already does."
 },
 "worked": {
  "title": "Design review: where does a feature flag go?",
  "steps": [
   {
    "say": "A new requirement: in staging, the app must use `MockIssuerClient` instead of `HttpIssuerClient`, chosen by the property `issuer=mock`. In the run-time container it is one filter before the graph is built, because the container learns its components at start-up anyway.",
    "code": "List<Class<?>> components = new ArrayList<>(DemoApp.COMPONENTS);\nif (\"mock\".equals(System.getProperty(\"issuer\"))) {\n    components.remove(HttpIssuerClient.class);          // decided at start-up\n    components.add(MockIssuerClient.class);\n}\nRegistry registry = new Container(components);",
    "lang": "java",
    "alt_lang": "kotlin",
    "alt_code": "val components = DemoApp.COMPONENTS.toMutableList()\nif (System.getProperty(\"issuer\") == \"mock\") {\n    components -= HttpIssuerClient::class.java          // decided at start-up\n    components += MockIssuerClient::class.java\n}\nval registry: Registry = Container(components)"
   },
   {
    "say": "The generated registry has no start-up graph to change. One option is to generate one registry per profile and choose at the edge of the program. Each registry stays plain code, and the flag picks a class, not a graph.",
    "code": "String source = RegistryGenerator.generate(\"com.acme.gen\", \"StagingRegistry\", stagingComponents);\n// ...and ProductionRegistry from the production list, both at build time\n\nRegistry registry = \"mock\".equals(System.getProperty(\"issuer\"))\n        ? new StagingRegistry()\n        : new ProductionRegistry();",
    "lang": "java",
    "alt_lang": "kotlin",
    "alt_code": "val source = RegistryGenerator.generate(\"com.acme.gen\", \"StagingRegistry\", stagingComponents)\n// ...and ProductionRegistry from the production list, both at build time\n\nval registry: Registry =\n    if (System.getProperty(\"issuer\") == \"mock\") StagingRegistry() else ProductionRegistry()"
   },
   {
    "say": "Check the costs. Two registries double the generated code and ship the mock in the production artifact. If the flag really is fixed per environment, a build-time property is cleaner: build the staging image with the staging list. Quarkus draws exactly this line between build-time configuration, fixed in the artifact, and run-time configuration, read at start-up."
   },
   {
    "say": "Write the decision down in one sentence a reviewer can check: \"The issuer implementation is chosen per build, so each image wires one graph; a run-time property may change the issuer's URL and timeouts, never which class is wired.\" That sentence is the design review's answer, and the test that proves it is the lab's: the generated registry wires the same graph as the reflective one, for each list."
   }
  ]
 },
 "lab": {
  "title": "Generate the registry",
  "minutes": 15,
  "files": [
   f"{lab}/main/{J}/RegistryGenerator.java"
  ],
  "run": "./gradlew :container:test --tests 'workbench.container.l03.*'",
  "steps": [
   "Run the tests once. All seven fail with `UnsupportedOperationException`. Everything else in `l03` is the finished container from lessons 1 and 2, plus `Registry` (what both containers offer) and `ProxySource`, which writes the interceptor classes as source. Skim `ProxySource.emit` once.",
   "Read `GeneratedCode` in the test folder: it is the \"build\". It compiles your source with javac and loads it in a fresh class loader for every test, so each test gets fresh singletons.",
   "In `RegistryGenerator.generate`, build a `BeanGraph`, take its creation order, and start with `header(...)`. For each component, write a holder class for a singleton or a factory method for a prototype, using the helpers `holder`, `factory`, `beanType` and `newExpression`.",
   "Write `get`: for each component, one `if (type == X.class) return type.cast(...)` line per type in `boundTypes(graph, c)`, using `reference(c)`. End with the `throw` line and `footer(order)`.",
   "Run the tests until all seven pass. If one says `the generated source does not compile`, read the numbered listing it prints. Then run `GenerateDemo` and read what your code writes for the demo app."
  ],
  "hints": [
   "Write class names with `getCanonicalName()`. `getName()` gives `WiringTest$Payouts` for a nested class, which javac reads as a class named with a dollar sign, not as a nested class.",
   "`Container.scopeOf(c)` is package-private in `Container`, and `RegistryGenerator` is in the same package, so you can call it.",
   "The concurrency test passes as soon as your holders are right, with no lock in your code. If you can say why (one thread runs a class's static initializer while the others wait), you have the main idea of this lesson.",
   "A test that sees `NoClassDefFoundError: Could not initialize class ...Holder` means a constructor threw inside a holder. The first failure in the output names the real exception."
  ],
  "done_when": "All seven tests in `BuildTimeTest` pass, and `GenerateDemo` prints a registry whose `PaymentService_Holder` uses four other holders."
 },
 "drill": {
  "title": "A holder-based registry by hand",
  "minutes": 5,
  "prompt": "Close the lab. Without a generator, write a registry for three components: `FxRates()` (singleton), `FeeCalculator(FxRates)` (singleton) and `Quote(FeeCalculator)` (prototype), with a `get(Class<T>)` that throws for anything else. Then compare. Which line makes `FeeCalculator` safe when eight threads ask first?",
  "answer": {
   "lang": "java",
   "src": "public final class FeeRegistry {\n    private static final class FxRatesHolder {\n        static final FxRates INSTANCE = new FxRates();\n    }\n\n    private static final class FeeCalculatorHolder {             // initialized once, under the JVM's lock\n        static final FeeCalculator INSTANCE = new FeeCalculator(FxRatesHolder.INSTANCE);\n    }\n\n    private static Quote newQuote() {                            // a prototype: new every time\n        return new Quote(FeeCalculatorHolder.INSTANCE);\n    }\n\n    public <T> T get(Class<T> type) {\n        if (type == FxRates.class) return type.cast(FxRatesHolder.INSTANCE);\n        if (type == FeeCalculator.class) return type.cast(FeeCalculatorHolder.INSTANCE);\n        if (type == Quote.class) return type.cast(newQuote());\n        throw new IllegalArgumentException(\"No component provides \" + type.getSimpleName());\n    }\n}",
   "alt": {
    "lang": "kotlin",
    "src": "object FeeRegistry {\n    private object FxRatesHolder { val INSTANCE = FxRates() }\n    private object FeeCalculatorHolder { val INSTANCE = FeeCalculator(FxRatesHolder.INSTANCE) }   // once, under the JVM's lock\n\n    private fun newQuote() = Quote(FeeCalculatorHolder.INSTANCE)   // a prototype: new every time\n\n    @Suppress(\"UNCHECKED_CAST\")\n    fun <T> get(type: Class<T>): T = when (type) {\n        FxRates::class.java -> FxRatesHolder.INSTANCE\n        FeeCalculator::class.java -> FeeCalculatorHolder.INSTANCE\n        Quote::class.java -> newQuote()\n        else -> throw IllegalArgumentException(\"No component provides ${type.simpleName}\")\n    } as T\n}"
   }
  }
 },
 "recap": [
  "Measure both clocks. JMH's `-prof gc` gave 0 B/op for a direct call and for generated interceptor code (escape analysis removed its objects), 160 for a Byte Buddy subclass and 208 for a JDK proxy. Per call, that only matters in hot loops.",
  "At start-up the reflective container loaded 2,207 classes against 991 for generated wiring: 814 from Byte Buddy's JAR, 30 JDK proxy classes (mostly annotation instances), 3 generated subclasses and helpers, and over a hundred hidden classes.",
  "A generated registry does the graph work at build time and wires with `new`: a holder class per singleton (lazy and thread-safe through the class initialization lock), a factory per prototype, identity checks in `get`, and interceptors as source. A cycle fails the build; a failing holder fails until restart.",
  "`jcmd GC.class_histogram` shows what the container keeps alive; a heap dump and MAT's path to GC roots show who holds it. Dropping the container freed Byte Buddy's loader and classes; the JDK proxy class and annotation instances stayed.",
  "AppCDS and the AOT cache archive classes from JARs, not classes made at run time: the 30 proxies are skipped and Byte Buddy's classes come from a custom loader. Generated wiring leaves almost nothing to make at start-up, which also suits native image."
 ],
 "quiz": [
  {
   "q": "You want CI to fail when someone makes the issuer proxy more expensive. Which number from `ProxyCallBench` should the check use?",
   "options": [
    "ns/op, with a 10% margin",
    "`gc.alloc.rate.norm` (B/op), with a small margin",
    "The score error, which must stay below 1 ns",
    "The number of forks"
   ],
   "answer": 1,
   "why": "Allocation per operation is the same on every run for the same code, while time on a shared CI machine can move by more than the score itself, as this lesson's runs did. Keep a small margin, because B/op can shift between JDK versions and JIT decisions.",
   "from": "perf-03"
  },
  {
   "q": "The generated `Fees_Proxy` allocates `new Object[] {p0}`, a boxed `Long` and an `Invocation` on every call, in its source. JMH reports 0 B/op for it. Why?",
   "options": [
    "JMH doesn't count objects smaller than 64 bytes",
    "The TLAB hides allocations from the GC profiler",
    "C2 inlined the whole call, and escape analysis removed the objects because none of them leaves the compiled method",
    "The objects are allocated off-heap"
   ],
   "answer": 2,
   "why": "Allocation in a TLAB is still allocation and still counted. What removed it is escape analysis after inlining: when every use of an object is inside one compiled method, C2 can replace it with its fields in registers. It only works once C2 has compiled the code and can see the whole call, which is why the reflective paths, where it can't, keep their 160 to 208 bytes.",
   "from": "mem-02"
  },
  {
   "q": "On JDK 21 you add a dynamic AppCDS archive to the reflective container's start. Which classes does every start still create at run time?",
   "options": [
    "None: the archive stores every class the training run loaded",
    "Only the application's own classes",
    "Byte Buddy's own classes from its JAR",
    "The JDK proxy classes, the classes Byte Buddy generates, and some hidden classes"
   ],
   "answer": 3,
   "why": "An archive holds classes the JVM can find again at a known location, such as a JAR on the class path. At dump time JDK 21 skips each proxy class with `Unsupported location`, and Byte Buddy's subclass is defined from bytes by its own class loader. Byte Buddy's JAR classes do come from the archive, which is why AppCDS still halved this start.",
   "from": "boot-02"
  },
  {
   "q": "A generated holder's constructor throws on first use because the issuer key is missing. Ops fix the configuration, and the next request calls `get(PaymentService.class)` again on the same JVM. What happens?",
   "options": [
    "`NoClassDefFoundError: Could not initialize class ...PaymentService_Holder`, until the JVM restarts",
    "The holder retries and the request succeeds",
    "`get` returns `null`",
    "The JVM retries the static initializer after a back-off"
   ],
   "answer": 0,
   "why": "A static initializer runs once. When it throws, the JVM marks the class as failed, and every later use gets `NoClassDefFoundError`, for the life of its class loader. Lesson 1's `SingletonCell` stores nothing when its factory throws, so it retries. That is one real cost of build-time holders: keep their constructors free of I/O and configuration lookups.",
   "from": "cls-01"
  },
  {
   "q": "In a heap dump of the generated registry, what holds the `PaymentService` singleton?",
   "options": [
    "A `SingletonCell` in the registry's map",
    "The static field `INSTANCE` of the class `PaymentService_Holder`, which lives as long as its class loader",
    "Nothing: the JVM keeps holder instances off the heap",
    "The thread that first called `get`"
   ],
   "answer": 1,
   "why": "A holder's instance is a static field, and static fields belong to their class, which stays loaded while its class loader is reachable. The registry has no map and no cells. That is why the lab loads the registry in a new class loader for each test: the only way to get fresh singletons is a fresh copy of the classes.",
   "from": "mem-07"
  }
 ],
 "flashcards": [
  {"front": "Which JMH number should a CI gate on proxy cost use?", "back": "`gc.alloc.rate.norm`, bytes per operation, with a small margin. Time is too noisy on shared machines."},
  {"front": "Why can generated interceptor code show 0 B/op although its source allocates?", "back": "C2 inlines the whole call, and escape analysis removes objects that never leave the compiled method."},
  {"front": "Name the `-Xlog:class+load` sources for classes made at run time.", "back": "`__dynamic_proxy__` (JDK proxies), `__JVM_DefineClass__` (defined from bytes, as Byte Buddy does), and hidden classes such as lambdas."},
  {"front": "Why does reading annotations by reflection create classes?", "back": "Each annotation instance is an object of a JDK proxy class generated for that annotation type."},
  {"front": "What makes a generated holder thread-safe without a lock in your code?", "back": "The JVM runs a class's static initializer once, under the class initialization lock; other threads wait for it."},
  {"front": "What happens when a holder's constructor throws?", "back": "`ExceptionInInitializerError` once, then `NoClassDefFoundError` on every later use until the JVM restarts. A `SingletonCell` would retry."},
  {"front": "Why can't AppCDS on JDK 21 archive a JDK proxy class?", "back": "The class has no location an archive can check (`Unsupported location`); it is generated at run time."}
 ],
 "terms": [
  {"term": "Build-time wiring", "plain": "Working out the dependency graph while the application is built and writing plain code that creates the components."},
  {"term": "Holder class", "plain": "A nested class whose static field holds one singleton; the JVM builds it on first use, once, under its class-init lock."},
  {"term": "Class histogram", "plain": "A count of live objects and bytes per class, after a full GC: `jcmd <pid> GC.class_histogram`."},
  {"term": "Heap dump", "plain": "A file with every object on the heap and every reference between them, read with a tool such as Eclipse MAT."},
  {"term": "Path to GC roots", "plain": "The chain of references that keeps an object alive, from a root such as a thread's local variable or a static field."},
  {"term": "B/op", "plain": "Bytes allocated per benchmark operation, from JMH's GC profiler: steady enough to compare and to gate in CI."}
 ],
 "explain_back": {
  "prompt": "Design review. A sceptical reviewer says: \"Our Spring Boot services wire everything by reflection and proxies at start-up, and it works. Generating code is extra build machinery. Why should we ever wire at build time?\" Defend the design you built across these three lessons, with the numbers you measured, and say when you would not do it.",
  "answer": "Both containers compute the same thing: the same constructors, the same order, the same interceptor chains. The only question is when. At run time it costs every start: here 2,207 classes against 991, because the container loads Byte Buddy, reads annotations through proxies, generates and verifies subclasses, and runs all of it cold in the interpreter. AppCDS halved that, but it can't archive the proxies or Byte Buddy's classes, so every start still generates them. Generated wiring moves the work to the build: a cycle fails the build, the start runs only holder initializers, the per-call path allocates nothing after inlining, and the result has no reflection for native image to declare. What it costs: a generator in the build, a component set fixed per artifact, and holders that fail permanently if a constructor throws, so constructors must be trivial. I wouldn't do it for a long-running service that starts once a week and needs plugins or beans chosen at run time; there, reflection's flexibility is worth a slower start. I would for services that scale out often, run as many small instances, or must start inside a tight readiness budget, which is most of what we deploy to Kubernetes."
 },
 "deeper": {
  "minutes": 12,
  "body": """What a production container adds to the one you built, roughly in the order you would need it:

- Lifecycle callbacks: `@PostConstruct` after injection and `@PreDestroy` on shutdown, run in reverse creation order so a `Ledger` closes after the `PaymentService` that writes to it.
- Qualifiers (`@Named`, `@Qualifier`) for two implementations of one interface, and resolution by generic type, so `Repository<Payment>` and `Repository<Refund>` are different dependencies.
- More scopes: per request, per session, per Kafka message, with a client proxy that forwards to the right instance for the current scope.
- Configuration injection, with type conversion and validation, split into build-time and run-time properties.
- Interceptor ordering by priority, decorators, and events between components.
- Lookup injection (`Provider<T>`, `Instance<T>`) for edges that must be followed at call time.
- Test support: replacing one component with a mock without rewriting the graph.
- Error messages that print the whole dependency path, not only the cycle.

The way the generator runs matters too. This lab runs it as a separate step on compiled classes, which is close to what Quarkus does during its build. Dagger and Micronaut run theirs as annotation processors inside javac, so the generated classes are compiled with your code and IDEs can show them, but the processor sees source-level elements instead of loaded classes. Spring's AOT processing starts the application context during the build and writes what it found as code.

For the start itself, the next levers after this lesson are the ones the start-up track covered: an AOT cache trained on representative traffic, then native image if memory per instance or start time is still the limit. Generated wiring makes both of them easier, because there is less left for the JVM to discover."""
 },
 "sources": [
  {"title": "JMH (OpenJDK Code Tools)", "url": "https://github.com/openjdk/jmh"},
  {"title": "The jcmd command, JDK 25 man page source", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.jcmd/share/man/jcmd.md"},
  {"title": "JEP 483: Ahead-of-Time Class Loading & Linking", "url": "https://openjdk.org/jeps/483"},
  {"title": "Quarkus: Contexts and Dependency Injection reference", "url": "https://quarkus.io/guides/cdi-reference"},
  {"title": "Quarkus: Writing your own extension", "url": "https://github.com/quarkusio/quarkus/blob/main/docs/src/main/asciidoc/writing-extensions.adoc"}
 ]
}

out = ROOT / "content/lessons/cap4-03.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print("wrote", out)
