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
<text class="t-s t-m" x="257" y="216" text-anchor="middle">on the build machine; a loop fails the build</text>
<text class="t-s t-m" x="595" y="216" text-anchor="middle">start: 991 classes</text>
<text class="t-s t-m" x="595" y="234" text-anchor="middle">no reflection</text>
</svg>"""

HISTOGRAM = """$ jcmd 20094 GC.class_histogram | grep -E 'workbench|Proxy|ByteBuddy|ByteArray'
  99:            42            672  jdk.proxy2.$Proxy8 (jdk.proxy2)
 137:            13            312  workbench.container.l03.Container$$Lambda/0x00007f2a80008aa8
 138:            13            312  workbench.container.l03.SingletonCell
 167:            14            224  jdk.proxy2.$Proxy2 (jdk.proxy2)
 247:             1            112  net.bytebuddy.dynamic.loading.ByteArrayClassLoader
 279:             4             96  workbench.container.l03.TimedInterceptor
 395:             2             48  workbench.container.l03.RetryInterceptor
 523:             1             32  workbench.container.l03.Container
 524:             1             32  workbench.container.l03.demo.app.BoxOffice
 760:             1             24  workbench.container.l03.InterceptingHandler
 866:             1             16  jdk.proxy2.$Proxy6 (jdk.proxy2)
 910:             1             16  workbench.container.l03.ShowCloser$ByteBuddy$3cYlOLuY
 911:             1             16  workbench.container.l03.SubclassBridge
 ...                                (81 lines in all: more $Proxy classes, net.bytebuddy types, the other parts)

$ jcmd 20094 GC.heap_dump /home/.../labs/container/build/heapdumps/container.hprof
20094:
Dumping heap to /home/.../labs/container/build/heapdumps/container.hprof ...
Heap dump file created [7850112 bytes in 0.049 secs]"""

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

OPENING = """Picture the box office computer restarting ten minutes before the doors open, with the queue already out on the street. The program has to be back before the first customer reaches the counter, and every start repeats the whole of lessons 1 and 2. It scans the classes, reads every annotation, checks the graph, and has Byte Buddy sew its costume copy.

Two numbers wait for us, and they point in opposite directions. A call through a stand-in costs a few hundred nanoseconds at most. A start with all that machinery loads more than twice as many classes as the same wiring written out as plain code. The easy trap is to measure only the first number, find it tiny, and call the proxies free.

The last lesson gave the container its stand-ins. In this one, we'll measure them per call and at start-up, and look inside the running container. Then we'll move the wiring to the build, and archive what's left. Before we start, make a guess, and keep it in mind."""

S1 = """Start with the cost of one call. Measuring a single call needs care. From bytecode to machine code: interpreter, C1, C2 pictured the JVM as a new cook. A fresh JVM reads every method from its recipe card, line by line, and cooks the busy ones from memory only later, with shortcuts. Time the first calls, and you've measured the cook's first day. So `ProxyCallBench` uses JMH, the OpenJDK project's benchmark harness. JMH runs a small piece of code in a fresh JVM and measures it only after the JIT compiler has done its work. (The JIT compiler is the part of the JVM that turns busy methods into machine code.) Benchmarking with JMH, and the traps it saves you from called it the fair taste test: a warmed-up kitchen, a fresh JVM for each round, ingredients the cook can't predict, and a judge who eats every result. Here we return each result and read the input from a non-final field, so the JIT can neither throw the work away nor fold it into a constant. JMH's `-prof gc` option adds a second number: the bytes each call allocates, B/op.

The benchmark makes one booking-fee calculation four ways. Each chain holds a single interceptor that only calls `proceed()`, so the numbers are the stand-ins' own cost, and the direct call is the baseline. One run on this course's 4-core machine, which was busy with other builds at the time:

| Call | ns/op | B/op |
|---|---|---|
| direct | 1.4 | 0 |
| generated forwarding class (this lesson) | 2.3 | 0 |
| Byte Buddy subclass (lesson 2) | 69 | 160 |
| JDK proxy (lesson 2) | 239 | 208 |

Every error bar was larger than its score, so read the time column for its order only. The bytes held up better. Over four runs, the direct and generated rows stayed at 0, and the JDK proxy at 208 to 213 B/op, while its time went from about 110 ns to over 3,000. Byte Buddy's row moved between 64 and 160 B/op: these runs are short, and the JIT didn't remove the same objects on that path every time.

Where do 208 bytes come from? The JDK proxy's generated method boxes the `long` argument, wrapping it in a `Long` object, and puts it in an `Object[]`. The handler builds an `Invocation` for each step of the chain and a lambda for the target call, and `Method.invoke` boxes the result. The generated forwarding class does the same things in its source: `new Object[] {p0}`, `new Invocation(...)`, a lambda. But its whole call is plain code that C2, the JIT's optimizing compiler, can inline: it copies each method the call reaches into the caller. Inlining, deoptimization and intrinsics pictured that as the cook who copies the sauce from page 12 into the main recipe. Once inlined, none of those objects leaves the compiled method, and escape analysis, C2's check for objects that never leave the code it compiled, removes them all. Allocation, TLABs and escape analysis put it in the warehouse's words: a box that never leaves the desk is never made. On the two reflective paths, C2 couldn't see the whole call, so the objects stay.

Don't build on that zero. As the Try it shows, one more interceptor is enough to lose it. The Kotlin twin counts the same calls in a plain loop and gets 0, 208, 192 and 48 bytes: the same order, with less of the generated class's allocation removed.

Does any of it matter? At 2,000 booking calls a second, 208 bytes each is 400 KB of short-lived garbage a second, next to a network call that takes milliseconds: nothing. In a loop that prices 10,000 seats through a proxied `PriceList`, it's 2 MB for every pass. Put the stand-in in front of the booking service, not in front of the arithmetic. Per call, then, the stand-ins are cheap. The start is another matter."""

S2 = """`StartupLadder` packs the demo box office into a JAR and starts it in fresh JVMs. It counts the lines that `-Xlog:class+load` prints, one per class the JVM loads, grouped by the `source:` each line names, as Why the JVM starts slowly, and how to measure it did. On JDK 21:

```text
setup                       loaded  archived  run-time  ready ms  wall ms
reflective + Byte Buddy       2207       953       156      1029     1307
    parsed from byte-buddy.jar 814, JDK proxies 30, defined from bytes 3, hidden 123
generated registry             991       834        51       266      418
```

The 1,216 extra classes are all machinery. 814 come from `byte-buddy-1.18.17.jar`: the library loads its own model of types, its matchers and its class writer before it can write one subclass. The costume department unpacks its whole sewing room to sew one costume. The 3 classes `defined from bytes` (`source: __JVM_DefineClass__`) are what it sewed: `ShowCloser$ByteBuddy$...` and two `$auxiliary$` helper classes, the `@SuperCall` callables for `close` and `verify`.

Then come 30 JDK proxy classes (`__dynamic_proxy__`), and only one of them is the booking stand-in. Every annotation you read through reflection is an object of a proxy class that the JDK writes for that annotation's type. So `getAnnotation(Component.class)` and `isAnnotationPresent(Timed.class)` make stand-ins too, and Byte Buddy uses a few proxies of its own inside. The 123 hidden classes are lambdas and method handles. A hidden class is one the JVM makes for its own use, which no class loader can find by name, and a method handle is a small JDK object that points at a method. Each lambda becomes a hidden class the first time its "ask the director" cue runs, as invokedynamic: how lambdas and string concatenation compile showed. Since JDK 18, core reflection itself runs on method handles, so every reflective call path adds a few more.

Each of those classes is found, parsed and verified, the corner shop unpacking and checking every box again, then run in the interpreter, because nothing is hot yet. Every start is the cook's first day again. That's why `ready`, from the first line of `main` to the first ticket sold, was 1,029 ms against 266 ms. The machine was busy, and the times moved by a factor of two between runs. The reflective start was always several times slower, though, and the class counts barely moved: a later run gave 2,208 and 991.

None of this means Byte Buddy is slow. It does at every start what a compiler could have done once. So let's give that work to the compiler."""

S3 = """Everything the reflective container works out at start-up depends only on the classes, and the classes are fixed when the program is built. So do the work then. Picture the front-of-house manager from lesson 1 writing the evening's running order the afternoon before. On the night, nobody reads a single card; the crew follows the sheet.

`RegistryGenerator` is that afternoon. It runs the same `BeanGraph` from lesson 1 at build time: it picks the constructors, orders the graph and checks for loops, and a loop now fails the build instead of the start. Then it prints a Java class that does the wiring with plain `new` calls, and the lab's test compiles that class with javac, the way a build would. It prints source rather than class files on purpose. Generating and transforming classes with the ClassFile API showed the theatre's own printing press for class files, but source is easier to read, and javac checks it for us.

Each singleton gets a holder class, as lesson 1 promised:

```java
private static final class PriceList_Holder {
    static final PriceList INSTANCE = new PriceList(SeatingPlan_Holder.INSTANCE);
}
```

```kotlin
private object PriceListHolder {
    val INSTANCE = PriceList(SeatingPlanHolder.INSTANCE)    // a Kotlin object is a holder class too
}
```

The JVM initializes `PriceList_Holder` the first time `get` touches it: one dress rehearsal, under the class initialization lock from Class loading: loaders, delegation, linking and initialization. Its dependency is another holder, which the JVM initializes first. There is no `volatile`, no lock after the first call, and no map: `get` is a list of checks like `if (type == PriceList.class)`. A prototype gets a factory method instead.

Interceptors become source too. For `BookingClient`, the generator writes `RemoteBookingClient_Proxy implements BookingClient`, and for `ShowCloser` it writes `ShowCloser_Intercepted extends ShowCloser`: the same stand-in and costume copy as lesson 2, printed in advance. The generator reads `@Timed` and `@Retry` while it runs and writes their values into the code, as in `INTERCEPTION.chain(true, 3, BookingUnavailableException.class)`, so nothing reads an annotation when the program starts. Real frameworks do the same. Quarkus's container, ArC, generates subclasses like these while the application is built; Micronaut does the graph work while javac compiles; and Spring can generate its wiring as code ahead of time.

You give up two things. The set of components is fixed when you build: nothing can scan a plugin directory at start-up, or choose a part from a setting, unless the generator wrote code for it. And a holder fails for good. If `BoxOffice`'s constructor throws on first use, the JVM marks `BoxOffice_Holder` as failed, and every later `get` throws `NoClassDefFoundError` until the program restarts. Lesson 1's cell would simply have tried again.

**What depends only on your classes can be worked out once, when you build. Do it there, and leave the start only what's left.**

Before we archive what's left, let's look inside a running container and count what it keeps."""

S4 = """Measure the running container from outside. Picture the warehouse from the Memory and GC track: the heap is its shared floor, and each object is a box with a label that names its class. `jcmd <pid> GC.class_histogram` runs a full GC and then counts the boxes on the floor by label. (`jcmd` is the JDK's tool for sending commands to a running JVM, and `<pid>` is that JVM's process id.) Here is the reflective container after one sale, one return and one closing, trimmed:

```text
 num     #instances         #bytes  class name (module)
  99:            42            672  jdk.proxy2.$Proxy8 (jdk.proxy2)
 138:            13            312  workbench.container.l03.SingletonCell
 167:            14            224  jdk.proxy2.$Proxy2 (jdk.proxy2)
 247:             1            112  net.bytebuddy.dynamic.loading.ByteArrayClassLoader
 523:             1             32  workbench.container.l03.Container
 866:             1             16  jdk.proxy2.$Proxy6 (jdk.proxy2)
 910:             1             16  workbench.container.l03.ShowCloser$ByteBuddy$3cYlOLuY
```

Read it like a stock list. The 13 `SingletonCell`s are the 14 components minus the one prototype, `Basket`. One `$Proxy6` is the booking stand-in. One `ByteArrayClassLoader` holds the Byte Buddy subclass and its two helper classes, and one `ShowCloser$ByteBuddy$...` is the closer itself. The other proxy objects are not parts of the box office at all. In this run, `$Proxy2`, with 14 instances, is the `@Component` annotation, one instance per component class. `$Proxy8`, with 42, is a proxy Byte Buddy uses to call JDK methods that don't exist on every Java version it supports. There were 119 proxy objects in all, and one of them was a part of the box office.

The histogram says what is alive, not who holds it. `jcmd <pid> GC.heap_dump <file>` writes every object and every reference between them to a file, 8 MB here, in the HPROF format that heap tools read. The JVM pauses while it writes, so on a busy program, take one only when you can afford a pause. Eclipse MAT, a free tool for reading heap dumps, can then show any object's path to GC roots. That's the cleaning crew's route from the Memory track: the notes it follows from the workers' desks and the noticeboard to the box. For the `ShowCloser$ByteBuddy$...` object, the path should run through `SingletonCell.instance` and the container's `singletons` map to the `Container`, held by a local variable of the `main` thread.

The demo also proves it by letting go. It drops its only reference to the container and asks for a GC. Byte Buddy's class loader is collected, and with it the generated class. A class keeps its loader alive and an object keeps its class alive, so once the container was unreachable, the whole chain was. The plan for that box left the filing cabinet once no box made from it remained. The JDK proxy class stays loaded, because it was defined in the application class loader, which lives as long as the program, and `Proxy` caches it there. The annotation instances stay too, cached with the classes and methods they label.

The generated registry has a different root. Its singletons sit in static fields of holder classes, so they live as long as the class loader that loaded the registry. That's why the lab's tests load a fresh copy of the class for every test. And that registry leaves very little to make at start-up, which is exactly what an archive wants."""

S5 = """Class data sharing and Project Leyden's AOT cache showed how to skip part of a start. Its shopkeeper keeps yesterday's filled shelves in the back room and wheels them out at opening time. An archive is a file of classes the JVM has already parsed and checked; at the next start, the JVM maps the file into memory instead of reading each class again. AppCDS, application class data sharing, puts your own classes in such an archive, and on JDK 21 one flag on a training run writes it. Apply it to both containers, and the last two rows of `StartupLadder` appear:

```text
reflective, AppCDS            2145      2037       108       544      858
    parsed from byte-buddy.jar 0, JDK proxies 30, defined from bytes 3, hidden 75
generated, AppCDS              882       847        35       143      362
    parsed from byte-buddy.jar 0, JDK proxies 0, defined from bytes 0, hidden 35
```

AppCDS took Byte Buddy's 814 classes from the archive and nearly halved the reflective start. It couldn't take the classes made while the program runs. When the archive was written, JDK 21 printed `Skipping jdk/proxy2/$Proxy3: Unsupported location` for each of the 30 proxy classes. And the archived run still logs Byte Buddy's three classes as `__JVM_DefineClass__`: defined from bytes by its own class loader, at every start. So every start still writes and verifies them, and still runs the code that writes them. The generated registry has nothing of the kind. Its only classes made at start-up are 35 hidden ones for lambdas.

The AOT cache, Project Leyden's newer archive, goes further for the classes it can store. They arrive already loaded and linked, with the shopkeeper's notes from the training run about which code was busy. JEP 483 brought it in JDK 24, and JDK 25 made it a single step with `-XX:AOTCacheOutput`. Use JDK 25.0.4 or later, as that lesson explained. The limit on custom class loaders stays: the cache doesn't store the classes they define, so Byte Buddy's classes are made at every start either way.

The registry is also the shape GraalVM native image wants. GraalVM native image and Quarkus native pictured it as a pop-up stall built at a factory, which sells only what the factory packed. The registry has no reflection to declare and no classes defined at run time, which a closed world can't contain. (CRaC, the photo of the warm shop, sidesteps the question: a restored JVM already holds the classes Byte Buddy made before the photo.) That is the whole argument for build-time wiring in one sentence: the less a start has to discover, write and verify, the more of it a cache, an archive or a native build can do for you."""

CLOSING = """We started with the box office computer restarting ten minutes before the doors open. A stand-in cost a few hundred bytes a call, the machinery behind it more than a thousand classes a start, and writing the wiring out at build time took most of that away.

Now run a program of your own with `-Xlog:class+load`, and count the classes it loads before its first request.

That ends Part 4, and the course. Part 1 kept a bank correct under many threads, Part 2 kept a post office counter answering while it waited, Part 3 gave a courier's events types the compiler checks, and Part 4 went backstage at the theatre, the warehouse and the kitchen. From here, take one program you know well and try one tool from each Part on it: a thread dump, a cancellation, a sealed type, a class count. The flashcards will keep the rest fresh."""

L = {
 "id": "cap4-03",
 "title": "Measure it, then make it start fast",
 "minutes": 40,
 "goal": "By the end you can measure what the container's proxies cost per call and at start-up, read a class histogram and a heap dump of the running container, generate its wiring at build time as plain Java, and defend when run-time or build-time wiring is the right design.",
 "opening": OPENING,
 "warmup": {
  "q": "The reflective container wires a 14-component box office with one JDK proxy and one Byte Buddy subclass. Roughly how many classes does that JVM load before the first ticket is sold?",
  "options": ["About 30: the 14 components and a few container classes", "About 1,000, the same as any small Java program", "More than 2,000", "About 15,000"],
  "answer": 2,
  "why": "On JDK 21 the reflective start loaded 2,207 classes: 814 of them from the Byte Buddy JAR, 30 JDK proxy classes, 3 classes Byte Buddy wrote, and over a hundred hidden classes for lambdas and method handles. The same app wired by generated code loaded 991, which is the second option's number. Most of a container's start-up cost is the machinery, not your components."
 },
 "sections": [
  {
   "h": "One call through a stand-in: nanoseconds and a couple of hundred bytes",
   "body": S1,
   "try": {
    "title": "Count the bytes per call",
    "minutes": 4,
    "steps": [
     "Read `ProxyCallBench`. Predict the B/op of each of the four benchmarks before you run it.",
     "Run it (it forks four JVMs, about 10 seconds on a quiet machine). Then run the Kotlin twin, which counts bytes with the per-thread allocation counter instead of JMH.",
     "In `ProxyCallBench`, add a second `PASS` to `CHAIN` (`List.of(PASS, PASS)`) and run it again. Which rows change? Change it back afterwards."
    ],
    "code": demo("ProxyCallBench"),
    "expect": "`direct` and `generated` show 0.0 B/op and `jdkProxy` about 208. `byteBuddy` shows 160 in most runs, and less in some on a busy machine. Times jump around, with errors larger than the scores, but `direct` and `generated` stay within a few nanoseconds and the two reflective paths are far slower. With two interceptors, every row but `direct` allocates more. In one run the reflective rows grew by 32 bytes each (one more `Invocation`, to 192 and 240), and `generated` jumped from 0 to 128 B/op: with the longer chain, escape analysis no longer removed its objects. That's why Allocation, TLABs and escape analysis said to show escape analysis in demos and never assert it in tests. The Kotlin twin prints 0, 208, 192 and 48 bytes per call."
   },
   "refs": [
    {"title": "JMHSample_35_Profilers (the GC profiler)", "url": "https://github.com/openjdk/jmh/blob/master/jmh-samples/src/main/java/org/openjdk/jmh/samples/JMHSample_35_Profilers.java", "kind": "read"}
   ]
  },
  {
   "h": "At start-up, the reflective container loads Byte Buddy and writes classes",
   "body": S2,
   "try": {
    "title": "Count what each start loads",
    "minutes": 5,
    "steps": [
     "Read `StartupLadder` (the Kotlin twin runs the first two rows). It generates the registry, compiles it with javac, packs `container/build/cap4/app.jar`, and starts the app in child JVMs.",
     "Predict the `loaded` column for the first two rows, and the `parsed from byte-buddy.jar` count for the generated registry.",
     "Run it. It takes about 10 to 20 seconds. Ignore the last two rows until section 5."
    ],
    "code": demo("StartupLadder"),
    "expect": "On JDK 21 the reflective start loads about 2,200 classes, 814 of them parsed from the Byte Buddy JAR, plus 30 JDK proxies and 3 classes defined from bytes. The generated registry loads about 990 and none of those. Its 51 hidden classes are mostly the lambdas in the generated interceptor classes and the JDK's own. `ready` and `wall` differ by machine and by run, but the reflective start is several times slower each time. Another JDK version gives other counts; the gap between the two rows is what to look at."
   }
  },
  {
   "h": "Write the wiring out at build time: generate the registry",
   "body": S3,
   "figure": {"svg": FIGURE, "caption": "The same steps in both rows. Build-time wiring runs all of them but the last on the build machine, once."},
   "try": {
    "title": "Read the class the generator writes",
    "minutes": 4,
    "steps": [
     "Run `GenerateDemo` (or the Kotlin twin). It prints the registry the generator writes for the demo box office, then tries a graph with a loop.",
     "Find `BoxOffice_Holder`. Which holders must the JVM initialize before it, and in what order?",
     "Find `ShowCloser_Intercepted.verify`. Which line makes `close`'s self-call go through the chain?"
    ],
    "code": demo("GenerateDemo"),
    "expect": "156 lines: 13 holder classes, one factory method (`new_Basket`, the prototype), a `get` with one identity check per bound type, and two generated interceptor classes. `BoxOffice_Holder` reads `RemoteBookingClient_Holder` (which reads `BookingConfig_Holder`), `PriceList_Holder`, `TicketRules_Holder` and `SalesBook_Holder`, so the JVM initializes those first, in the order the constructor's arguments are evaluated. `close` reaches `verify` through `this`, which is the `_Intercepted` object, so its overriding `verify` runs the chain before `super.verify(p0)`. The last line is `the build fails: Dependency cycle: Rota -> CastList -> Rota`."
   },
   "refs": [
    {"title": "Quarkus: Writing your own extension (do the work at build time)", "url": "https://github.com/quarkusio/quarkus/blob/main/docs/src/main/asciidoc/writing-extensions.adoc", "kind": "read"}
   ]
  },
  {
   "h": "Look inside the running container: a histogram and a heap dump",
   "body": S4,
   "try": {
    "title": "Take a histogram and a heap dump of the container",
    "minutes": 6,
    "steps": [
     "Run `RunningContainer` with `-Pargs=wait` added to the command below. It wires the box office, makes three calls, prints its pid and two `jcmd` commands, and waits.",
     "In a second terminal, from `labs/`, run the two commands it printed. Count the `SingletonCell`s, the `ByteArrayClassLoader`s and the `$ByteBuddy$` instances before you look at the answer.",
     "Optional: open `container/build/heapdumps/container.hprof` in Eclipse MAT and use \"Path to GC Roots\" on the `ShowCloser$ByteBuddy$...` object.",
     "Press Enter in the first terminal. It drops the container. Run the histogram command again, then press Enter to end. Without `-Pargs=wait`, the demo (and its Kotlin twin) runs both `jcmd` commands itself and prints a shorter, grouped histogram."
    ],
    "code": demo("RunningContainer"),
    "expect": "Real output from one run, trimmed:\n\n```text\n" + HISTOGRAM + "\n```\n\nThe numbers after `$Proxy` and the random `$ByteBuddy$` suffix differ per run. After you press Enter, the demo prints `Byte Buddy's class loader collected: true` and `jdk.proxy2.$Proxy6 still loaded: true`, and the second histogram has no `SingletonCell`, no `Container`, no `ByteArrayClassLoader` and no box office parts. What is left of `workbench.container.l03` is static: enum constants, cached lambdas and `Interception$Companion`."
   },
   "refs": [
    {"title": "The jcmd command, JDK 25 man page source: GC.class_histogram and GC.heap_dump", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/jdk.jcmd/share/man/jcmd.md", "kind": "docs"}
   ]
  },
  {
   "h": "Archive what's left: AppCDS on JDK 21, the AOT cache on JDK 25",
   "body": S5,
   "try": {
    "title": "Archive both starts",
    "minutes": 4,
    "steps": [
     "Run `StartupLadder` once (section 2), so `app.jar` and `classpath.txt` exist in `container/build/cap4`.",
     "Run the two JDK 21 commands. Predict both answers first: how many classes does the archive refuse, and which classes made at start-up remain?",
     "If you have JDK 25.0.4 or later, run the last two commands with its `java`."
    ],
    "code": {"lang": "bash", "title": "terminal (from labs/)", "src": BASH_ARCHIVE, "run": ""},
    "expect": "On JDK 21 the first command prints 30: one `Unsupported location` warning per proxy class. The second prints `3 source: __JVM_DefineClass__`, `75 source: __JVM_LookupDefineClass__` and `30 source: __dynamic_proxy__`: the Byte Buddy classes, hidden classes and proxies that every start still makes, even with the archive. On JDK 25.0.4 or later the AOT cache commands should end with `Opened AOT cache generated.aot.` (this course's machine had only JDK 21, so that line comes from the Startup track's runs, not from this app)."
   },
   "refs": [
    {"title": "JEP 483: Ahead-of-Time Class Loading & Linking", "url": "https://openjdk.org/jeps/483", "kind": "read"}
   ]
  }
 ],
 "compare": {
  "title": "A generated registry in Java, and the same idea written by hand in Kotlin",
  "java": {
   "title": "AppRegistry.java (generated, trimmed)",
   "src": "public final class AppRegistry implements Registry {\n    private static final class SeatingPlan_Holder {\n        static final SeatingPlan INSTANCE = new SeatingPlan();\n    }\n\n    private static final class PriceList_Holder {\n        static final PriceList INSTANCE = new PriceList(SeatingPlan_Holder.INSTANCE);\n    }\n\n    private static Basket new_Basket() {                        // a prototype\n        return new Basket(PriceList_Holder.INSTANCE);\n    }\n\n    @Override\n    public <T> T get(Class<T> type) {\n        if (type == SeatingPlan.class) return type.cast(SeatingPlan_Holder.INSTANCE);\n        if (type == PriceList.class) return type.cast(PriceList_Holder.INSTANCE);\n        if (type == Basket.class) return type.cast(new_Basket());\n        throw new ContainerException(\"No component provides \" + type.getSimpleName());\n    }\n}"
  },
  "kotlin": {
   "title": "AppRegistry.kt (by hand)",
   "src": "object AppRegistry {\n    private object SeatingPlanHolder { val INSTANCE = SeatingPlan() }\n    private object PriceListHolder { val INSTANCE = PriceList(SeatingPlanHolder.INSTANCE) }\n\n    private fun newBasket() = Basket(PriceListHolder.INSTANCE)   // a prototype\n\n    @Suppress(\"UNCHECKED_CAST\")\n    fun <T> get(type: Class<T>): T = when (type) {\n        SeatingPlan::class.java -> SeatingPlanHolder.INSTANCE\n        PriceList::class.java -> PriceListHolder.INSTANCE\n        Basket::class.java -> newBasket()\n        else -> throw ContainerException(\"No component provides ${type.simpleName}\")\n    } as T\n}"
  },
  "note": "Both compile to the same mechanism: one class per singleton whose static initializer builds it on first use, under the JVM's class initialization lock. A Kotlin `object` is that holder class, with its instance in a static `INSTANCE` field. The difference is who writes it. The Java one comes from a generator and is never edited; the Kotlin one is the kind of code Dagger, a build-time container, generates, written here by hand, which is fine for ten components and painful for eighty. You don't need `by lazy` here: it would work, but it adds a `Lazy` object per part and a volatile read per access to do what the class initialization lock already does."
 },
 "worked": {
  "title": "Design review: where does a setting go?",
  "steps": [
   {
    "say": "A new requirement: on the theatre's test machine, the box office must use `MockBookingClient` instead of `RemoteBookingClient`, chosen by the property `booking=mock` (a setting passed on the command line as `-Dbooking=mock`). In the run-time container it's one filter before the graph is built, because the container learns its components at start-up anyway.",
    "code": "List<Class<?>> components = new ArrayList<>(DemoApp.COMPONENTS);\nif (\"mock\".equals(System.getProperty(\"booking\"))) {\n    components.remove(RemoteBookingClient.class);       // decided at start-up\n    components.add(MockBookingClient.class);\n}\nRegistry registry = new Container(components);",
    "lang": "java",
    "alt_lang": "kotlin",
    "alt_code": "val components = DemoApp.COMPONENTS.toMutableList()\nif (System.getProperty(\"booking\") == \"mock\") {\n    components -= RemoteBookingClient::class.java       // decided at start-up\n    components += MockBookingClient::class.java\n}\nval registry: Registry = Container(components)"
   },
   {
    "say": "The generated registry has no start-up graph to change. One option is to generate one registry per setup and choose at the edge of the program, where it starts. Each registry stays plain code, and the setting picks a class, not a graph.",
    "code": "String source = RegistryGenerator.generate(\"theatre.gen\", \"TestRegistry\", testComponents);\n// ...and LiveRegistry from the live list, both at build time\n\nRegistry registry = \"mock\".equals(System.getProperty(\"booking\"))\n        ? new TestRegistry()\n        : new LiveRegistry();",
    "lang": "java",
    "alt_lang": "kotlin",
    "alt_code": "val source = RegistryGenerator.generate(\"theatre.gen\", \"TestRegistry\", testComponents)\n// ...and LiveRegistry from the live list, both at build time\n\nval registry: Registry =\n    if (System.getProperty(\"booking\") == \"mock\") TestRegistry() else LiveRegistry()"
   },
   {
    "say": "Check the costs. Two registries double the generated code and ship the mock inside the real program. If the choice really is fixed per machine, a build-time setting is cleaner: build the test copy from the test list. Quarkus draws exactly this line between build-time configuration, fixed in the built program, and run-time configuration, read at start-up."
   },
   {
    "say": "Write the decision down in one sentence a reviewer can check: \"The booking implementation is chosen per build, so each build wires one graph; a run-time property may change the booking service's address and timeouts, never which class is wired.\" That sentence is the design review's answer, and the test that proves it is the lab's: the generated registry wires the same graph as the reflective one, for each list."
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
   "Run the tests until all seven pass. If one says `the generated source does not compile`, read the numbered listing it prints. Then run `GenerateDemo` and read what your code writes for the demo box office."
  ],
  "hints": [
   "Write class names with `getCanonicalName()`. `getName()` gives `BuildTimeTest$Rota` for a nested class, which javac reads as a class whose name contains a dollar sign, not as a nested class.",
   "`Container.scopeOf(c)` is package-private in `Container`, and `RegistryGenerator` is in the same package, so you can call it.",
   "The concurrency test passes as soon as your holders are right, with no lock in your code. If you can say why (one thread runs a class's static initializer while the others wait), you have the main idea of this lesson.",
   "A test that sees `NoClassDefFoundError: Could not initialize class ...Holder` means a constructor threw inside a holder. The first failure in the output names the real exception."
  ],
  "done_when": "All seven tests in `BuildTimeTest` pass, and `GenerateDemo` prints a registry whose `BoxOffice_Holder` uses four other holders."
 },
 "drill": {
  "title": "A holder-based registry by hand",
  "minutes": 5,
  "prompt": "Close the lab. Without a generator, write a registry for three components: `SeatingPlan()` (singleton), `PriceList(SeatingPlan)` (singleton) and `Basket(PriceList)` (prototype), with a `get(Class<T>)` that throws for anything else. Then compare. Which line makes `PriceList` safe when eight threads ask first?",
  "answer": {
   "lang": "java",
   "src": "public final class BoxOfficeRegistry {\n    private static final class SeatingPlanHolder {\n        static final SeatingPlan INSTANCE = new SeatingPlan();\n    }\n\n    private static final class PriceListHolder {                 // initialized once, under the JVM's lock\n        static final PriceList INSTANCE = new PriceList(SeatingPlanHolder.INSTANCE);\n    }\n\n    private static Basket newBasket() {                           // a prototype: new every time\n        return new Basket(PriceListHolder.INSTANCE);\n    }\n\n    public <T> T get(Class<T> type) {\n        if (type == SeatingPlan.class) return type.cast(SeatingPlanHolder.INSTANCE);\n        if (type == PriceList.class) return type.cast(PriceListHolder.INSTANCE);\n        if (type == Basket.class) return type.cast(newBasket());\n        throw new IllegalArgumentException(\"No component provides \" + type.getSimpleName());\n    }\n}",
   "alt": {
    "lang": "kotlin",
    "src": "object BoxOfficeRegistry {\n    private object SeatingPlanHolder { val INSTANCE = SeatingPlan() }\n    private object PriceListHolder { val INSTANCE = PriceList(SeatingPlanHolder.INSTANCE) }   // once, under the JVM's lock\n\n    private fun newBasket() = Basket(PriceListHolder.INSTANCE)   // a prototype: new every time\n\n    @Suppress(\"UNCHECKED_CAST\")\n    fun <T> get(type: Class<T>): T = when (type) {\n        SeatingPlan::class.java -> SeatingPlanHolder.INSTANCE\n        PriceList::class.java -> PriceListHolder.INSTANCE\n        Basket::class.java -> newBasket()\n        else -> throw IllegalArgumentException(\"No component provides ${type.simpleName}\")\n    } as T\n}"
   }
  }
 },
 "recap": [
  "Measure both clocks. JMH's `-prof gc` gave 0 B/op for a direct call and for generated interceptor code (escape analysis removed its objects), about 160 for a Byte Buddy subclass and 208 for a JDK proxy. Bytes per call were far steadier than time, and per call they only matter in hot loops.",
  "At start-up the reflective container loaded 2,207 classes against 991 for generated wiring: 814 from Byte Buddy's JAR, 30 JDK proxy classes (mostly annotation instances), 3 generated subclasses and helpers, and over a hundred hidden classes.",
  "A generated registry does the graph work at build time and wires with `new`: a holder class per singleton (lazy and thread-safe through the class initialization lock), a factory per prototype, identity checks in `get`, and interceptors as source. A loop fails the build.",
  "`jcmd GC.class_histogram` shows what the container keeps alive; a heap dump and its path to GC roots show who holds it. Dropping the container freed Byte Buddy's loader and classes; the JDK proxy class and the annotation instances stayed.",
  "AppCDS and the AOT cache archive classes from JARs, not classes made at run time: the 30 proxies are skipped, and Byte Buddy's classes come from a custom loader. Generated wiring leaves almost nothing to make at start-up, which also suits native image.",
  "Where build-time wiring stops: the set of parts is fixed when you build, and a holder whose constructor throws stays broken until restart. Run-time wiring keeps that flexibility and pays for it at every start."
 ],
 "closing": CLOSING,
 "quiz": [
  {
   "q": "You want CI, the build server that checks every change, to fail when someone makes the booking stand-in more expensive. Which number from `ProxyCallBench` should the check use?",
   "options": [
    "ns/op, with a 10% margin",
    "`gc.alloc.rate.norm` (B/op), with a small margin",
    "The score error, which must stay below 1 ns",
    "The number of forks"
   ],
   "answer": 1,
   "why": "Over four runs on a busy machine, the JDK proxy's bytes per call stayed between 208 and 213 while its time went from about 110 ns to over 3,000, so a 10% margin on time fails at random. Keep a margin on the bytes too, because B/op can shift with the JDK version, the length of the chain and what the JIT manages to remove.",
   "from": "perf-03"
  },
  {
   "q": "The generated `Prices_Proxy` allocates `new Object[] {p0}`, a boxed `Long` and an `Invocation` on every call, in its source. JMH reports 0 B/op for it. Why?",
   "options": [
    "JMH doesn't count objects smaller than 64 bytes",
    "The TLAB hides allocations from the GC profiler",
    "C2 inlined the whole call, and escape analysis removed the objects because none of them leaves the compiled method",
    "The objects are allocated off-heap"
   ],
   "answer": 2,
   "why": "Allocation in a TLAB is still allocation and is still counted, so the second option fails. What removed it is escape analysis after inlining: when every use of an object stays inside one compiled method, C2 can replace the object with its fields in registers. It only works once C2 has compiled the code and can see the whole call, which is why the reflective paths keep their 160 to 208 bytes.",
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
   "why": "An archive holds classes the JVM can find again at a known location, such as a JAR on the class path. At dump time JDK 21 skips each proxy class with `Unsupported location`, and Byte Buddy's subclass is defined from bytes by its own class loader. Byte Buddy's JAR classes do come from the archive, so the third option is wrong, and that's why AppCDS still nearly halved this start.",
   "from": "boot-02"
  },
  {
   "q": "A generated holder's constructor throws on first use because the booking service key is missing. Someone fixes the configuration, and the next sale calls `get(BoxOffice.class)` again on the same JVM. What happens?",
   "options": [
    "`NoClassDefFoundError: Could not initialize class ...BoxOffice_Holder`, until the JVM restarts",
    "The holder retries, and the sale succeeds",
    "`get` returns `null`",
    "The JVM retries the static initializer after a pause"
   ],
   "answer": 0,
   "why": "A static initializer runs once: the dress rehearsal can't be held twice. When it throws, the JVM marks the class as failed, and every later use gets `NoClassDefFoundError` for the life of its class loader. Lesson 1's `SingletonCell` stores nothing when its factory throws, so it retries, which is what the second option describes. That's one real cost of build-time holders: keep their constructors free of input, output and configuration lookups.",
   "from": "cls-01"
  },
  {
   "q": "In a heap dump of the generated registry, what holds the `BoxOffice` singleton?",
   "options": [
    "A `SingletonCell` in the registry's map",
    "The static field `INSTANCE` of the class `BoxOffice_Holder`, which lives as long as its class loader",
    "Nothing: the JVM keeps holder instances off the heap",
    "The thread that first called `get`"
   ],
   "answer": 1,
   "why": "A holder's instance is a static field, and static fields belong to their class, which stays loaded while its class loader is reachable. The registry has no map and no cells, so the first option describes the reflective container instead. That's why the lab loads the registry in a new class loader for each test: the only way to get fresh singletons is a fresh copy of the classes.",
   "from": "mem-07"
  }
 ],
 "flashcards": [
  {"front": "Which JMH number should a CI check on proxy cost use?", "back": "`gc.alloc.rate.norm`, bytes per operation, with a small margin. Time is too noisy on shared machines."},
  {"front": "Why can generated interceptor code show 0 B/op although its source allocates?", "back": "C2 inlines the whole call, and escape analysis removes objects that never leave the compiled method."},
  {"front": "Name the `-Xlog:class+load` sources for classes made at run time.", "back": "`__dynamic_proxy__` (JDK proxies), `__JVM_DefineClass__` (defined from bytes, as Byte Buddy does), and hidden classes such as lambdas."},
  {"front": "Why does reading annotations by reflection create classes?", "back": "Each annotation instance is an object of a JDK proxy class generated for that annotation type."},
  {"front": "What makes a generated holder thread-safe without a lock in your code?", "back": "The JVM runs a class's static initializer once, under the class initialization lock; other threads wait for it."},
  {"front": "What happens when a holder's constructor throws?", "back": "`ExceptionInInitializerError` once, then `NoClassDefFoundError` on every later use until the JVM restarts. A `SingletonCell` would retry."},
  {"front": "Why can't AppCDS on JDK 21 archive a JDK proxy class?", "back": "The class has no location an archive can check (`Unsupported location`); it is generated at run time."}
 ],
 "terms": [
  {"term": "Build-time wiring", "plain": "Working out the dependency graph while the application is built, and writing plain code that creates the components."},
  {"term": "Holder class", "plain": "A nested class whose static field holds one singleton; the JVM builds it on first use, once, under its class initialization lock."},
  {"term": "Class histogram", "plain": "A count of live objects and bytes per class, taken after a full GC: `jcmd <pid> GC.class_histogram`."},
  {"term": "Heap dump", "plain": "A file with every object on the heap and every reference between them, read with a tool such as Eclipse MAT."},
  {"term": "Path to GC roots", "plain": "The chain of references that keeps an object alive, from a root such as a thread's local variable or a static field."},
  {"term": "B/op", "plain": "Bytes allocated per benchmark operation, from JMH's GC profiler: far steadier than time, so it is the number to compare and to check in CI."}
 ],
 "explain_back": {
  "prompt": "Design review. A sceptical reviewer says: \"Our services wire everything by reflection and proxies at start-up, and it works. Generating code is extra build machinery. Why should we ever wire at build time?\" Defend the design you built across these three lessons, with the numbers you measured, and say when you would not do it.",
  "answer": "Both containers compute the same thing: the same constructors, the same order, the same interceptor chains. The only question is when. At run time it costs every start: here 2,207 classes against 991, because the container loads Byte Buddy, reads annotations through proxies, writes and verifies subclasses, and runs all of it cold in the interpreter. AppCDS nearly halved that, but it can't archive the proxies or Byte Buddy's classes, so every start still makes them. Generated wiring moves the work to the build: a loop fails the build, the start runs only holder initializers, the per-call path allocates nothing after inlining, and the result has no reflection for native image to declare. What it costs: a generator in the build, a set of components fixed per build, and holders that fail for good if a constructor throws, so constructors must be trivial. I wouldn't do it for a program that starts once a week, runs for days, and needs plugins or parts chosen at start-up; there, reflection's flexibility is worth a slower start. I would for programs that start often, run as many small copies at once, or must be answering within a second or two of starting."
 },
 "deeper": {
  "minutes": 12,
  "body": """What a production container adds to the one you built, roughly in the order you would need it:

- Lifecycle callbacks: `@PostConstruct` after injection, and `@PreDestroy` at shutdown, run in reverse creation order so a `SalesBook` closes after the `BoxOffice` that writes to it.
- Qualifiers (`@Named`, `@Qualifier`) for two implementations of one interface, and matching by generic type, so `Repository<Show>` and `Repository<Seat>` are different dependencies.
- More scopes: one instance per request or per user session, with a client proxy that forwards each call to the right instance for the current scope.
- Configuration injection, with type conversion and checks, split into build-time and run-time settings.
- Interceptor ordering by priority, decorators, and events between components.
- Lookups (`Provider<T>`, `Instance<T>`) for edges that must be followed at call time.
- Test support: swapping one component for a fake without rewriting the graph.
- Error messages that print the whole dependency path, not only the loop.

The way the generator runs matters too. This lab runs it as a separate step on compiled classes, which is close to what Quarkus does during its build. Dagger and Micronaut run theirs as annotation processors inside javac, so the generated classes are compiled with your code and IDEs can show them, but the processor sees source-level elements instead of loaded classes. Spring's AOT processing starts the application's wiring during the build and writes what it found as code.

For the start itself, the next levers after this lesson are the ones the Startup track covered: an AOT cache trained on representative work, then native image if memory per copy or start time is still the limit. Generated wiring makes both easier, because there is less left for the JVM to discover."""
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
