import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/startup/src"
DJ = "java/workbench/startup/l01/demo"
DK = "kotlin/workbench/startup/l01/demo"
read = lambda p: (ROOT / p).read_text()


def demo(name):
    """A Try-it code object for a Java demo with its Kotlin twin, read from disk."""
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{DJ}/{name}.java"),
            "run": f"./gradlew :startup:demo -Pmain=workbench.startup.l01.demo.{name}",
            "file": f"{lab}/demo/{DJ}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{DK}/{name}.kt"),
                    "run": f"./gradlew :startup:demo -Pmain=workbench.startup.l01.demo.{name}Kt",
                    "file": f"{lab}/demo/{DK}/{name}.kt"}}


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


FIG = (
    '<svg viewBox="0 0 700 230" role="img" aria-label="Timeline of a JVM start-up: launch, create VM, class loading, '
    'program start, first request and JIT warm-up, with three clocks marked under it">'
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
    '<text class="t-s" x="445" y="69" text-anchor="middle">program start</text>'
    '<text class="t-s t-m" x="445" y="86" text-anchor="middle">config, wiring</text>'
    '<rect class="box" x="510" y="50" width="90" height="44" rx="8"/>'
    '<text class="t-s" x="555" y="69" text-anchor="middle">first request</text>'
    '<text class="t-s t-m" x="555" y="86" text-anchor="middle">more classes</text>'
    '<rect class="box-dim" x="605" y="50" width="85" height="44" rx="8"/>'
    '<text class="t-s" x="647" y="69" text-anchor="middle">warm-up</text>'
    '<text class="t-s t-m" x="647" y="86" text-anchor="middle">C1, then C2</text>'
    '<line class="ln-a" x1="185" y1="98" x2="185" y2="140"/>'
    '<text class="t-s t-a" x="185" y="156" text-anchor="middle">Create VM</text>'
    '<text class="t-s t-m" x="185" y="172" text-anchor="middle">lights on</text>'
    '<line class="ln-a" x1="505" y1="98" x2="505" y2="140"/>'
    '<text class="t-s t-a" x="505" y="156" text-anchor="middle">started in</text>'
    '<text class="t-s t-m" x="505" y="172" text-anchor="middle">the OPEN sign</text>'
    '<line class="ln-a" x1="600" y1="98" x2="600" y2="185"/>'
    '<text class="t-s t-a" x="600" y="201" text-anchor="middle">first 200</text>'
    '<text class="t-s t-m" x="600" y="217" text-anchor="middle">first customer served</text>'
    '</svg>'
)

OPENING = """Picture a corner shop with an odd habit. Every evening the shopkeeper packs the whole shop into boxes. Every morning she unlocks the door, switches on the lights, unpacks each box, checks every item against its delivery note and fills the shelves. Only then can she serve the first customer, and even then she's slow, because she still looks up where the tea is.

The JVM, the program that runs your compiled Java and Kotlin, starts the same way on every launch. Our running example is a small parcel-tracking service: ask it where parcel PX-1042 is, and it tells you. One run on JDK 25 printed `started in 0.151s`, yet the first answer reached the outside 429 ms after launch. Both numbers are true. They time different things.

The gap is easy to miss: the line a program prints looks like the whole story. The performance track made a running program fast; this track is about the wait before it runs at all. In this lesson, we'll watch the JVM unpack its classes, see when it runs your static code, read three start-up clocks and weigh the service's memory. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
S0 = """Let's count the boxes first. `ClassSourcesDemo`, in the Try it below, has exactly one class of its own. It starts a second JVM, has it read three lines of settings, format a date and join a few strings, then counts the classes that JVM loaded. On JDK 25.0.5 it printed this:

```text
JDK 25.0.5.0.3+1-1-24.04.1-Ubuntu, flags []: 818 classes loaded
      1  file: (your classes and JARs)
     19  jrt:/ (the JDK's modules file, parsed now)
      5  other (hidden classes: lambdas, method handles)
    793  shared objects file (the CDS archive)
```

One class was ours. The other 817 belong to the JDK and to the machinery that runs Java. A bigger program tells the same story: a generated app with 300 classes of its own loaded 1,537 classes on JDK 21 with the JDK's archive turned off. Its own classes were a fifth of the total.

Here's the morning routine, step by step. When you type `java`, a small native program called the launcher starts first. (Native means compiled for your machine, as C programs are, rather than for the JVM.) The launcher loads the JVM and asks it to create a VM, which is the shopkeeper unlocking the door and switching on the lights. The JVM reserves memory for the heap, the area where your objects will live. It generates its interpreter, starts its own helper threads, and sets up the core `java.lang` classes and the module system. Only then does it look for your main class.

From there, each class goes through the same steps the first time something needs it. The JVM finds the class file and parses it into its own internal form, in metaspace, memory the JVM keeps for class data outside the heap. That's unpacking a box. Then it **verifies** the bytecode, the instructions `javac` and `kotlinc` write into class files: it checks that every instruction is type-safe before any of them runs. That's the delivery note, checked item by item. Later it runs the class's static initializer, which the next section is about.

Your code then runs in the interpreter, which executes bytecode one instruction at a time, like a shopkeeper looking up every price in the catalogue. The JIT compilers turn hot methods, the ones that run often, into machine code while the program runs. First, though, they wait for profiles: counts of which methods, branches and types the code really uses. That's the shopkeeper learning the popular items by heart, and it takes a while. A framework, a library that starts and wires your program for you, adds work of its own. It scans classes for annotations, creates objects by reflection (code that finds classes and calls them by name) and reads configuration.

Nothing of this survives the process. Stop the JVM, and the next launch unpacks, checks and learns it all again, with exactly the same care. There's one exception, and it's in the output above. A JDK build ships an archive of about 1,300 of its own classes, already parsed, and the JVM maps them from disk instead of unpacking them. Those are the 793 `shared objects file` lines. Lesson 2 of this track is about that archive and the bigger ones you can build.

You can watch the unpacking yourself. `-Xlog:class+load` prints one line per class, and the end of each line says where the class came from. Four real lines from a run of the same work, with the folder shortened:

```text
[0.063s][info][class,load] java.lang.Object source: shared objects file
[0.078s][info][class,load] sun.util.PreHashedMap source: jrt:/java.base
[0.124s][info][class,load] workbench.startup.l01.demo.ClassSourcesDemo source: file:.../classes/java/demo/
[0.171s][info][class,load] workbench.startup.l01.demo.ClassSourcesDemo$$Lambda/0x000000006f040210 source: workbench.startup.l01.demo.ClassSourcesDemo
```

`shared objects file` means the class came ready-made from the archive. `jrt:/` means the JVM read it from the JDK's modules file, where the JDK keeps its classes, and parsed it on the spot. `file:` is your own class path, the list of folders and JAR files (zip files of classes) where the JVM looks for your code. A class name as the source marks a **hidden class**, a class the JVM generates in memory while the program runs, with no class file behind it. Each lambda gets one.

Here the shop picture breaks, and the break matters. Our shopkeeper unpacks everything before she opens. The JVM doesn't: it unpacks a box only when someone first asks for something inside it.

Check yourself before the Try it: a hidden class has no class file. Why can its source never start with `file:`? (Because `file:` names the place its bytes were read from, and a hidden class's bytes were made in memory.)

So the JVM unpacks lazily. The next question is when it runs the static code inside a class, and that decides how much of your own work lands on the start-up path."""

# ---------------------------------------------------------------- section 1
J_EAGER = """// Naive: the health check pays for the whole table (trimmed)
public final class PostcodeTable {
    private static final Map<String, String> TABLE = build();   // runs in <clinit>

    public static String version() { return "postcodes-2026.11"; }
    public static String depotOf(String postcode) { return TABLE.get(postcode); }
}"""
K_EAGER = """// Naive: the health check pays for the whole table
class PostcodeTable {
    companion object {
        private val table = build()                 // also runs in PostcodeTable's <clinit>

        fun version() = "postcodes-2026.11"
        fun depotOf(postcode: String) = table[postcode]
    }
}"""
J_HOLDER = """// Fixed: the table waits in a class of its own
public final class PostcodeTable {
    private static final class Holder {
        static final Map<String, String> TABLE = build();   // runs on first use of Holder
    }

    public static String version() { return "postcodes-2026.11"; }
    public static String depotOf(String postcode) { return Holder.TABLE.get(postcode); }
}"""
K_HOLDER = """// Fixed: the table waits in a class of its own
object PostcodeTable {
    fun version() = "postcodes-2026.11"
    fun depotOf(postcode: String) = Holder.table[postcode]

    private object Holder {
        val table = build()                         // a nested object is its own class
    }
}"""

S1 = """The tracking service has to know which depot delivers to each postcode. The lab class `PostcodeTable` keeps that as a map of 200,000 rows, which a real service would build from a big file. It also has a `version()` method, and the service's health check calls it. A health check is a tiny request that another program sends every few seconds to ask "are you up?", and this one also reports which postcode data is loaded.

Here's the first version, as the lab hands it to you:

""" + pair(J_EAGER, K_EAGER) + """

To see what's wrong, separate two events that sound alike. The JVM loads a class when something needs its definition. It initializes the class, which means it runs the class's static initializer, only on the class's first **active use**. The static initializer is a hidden method that the bytecode calls `<clinit>`. It holds every static field initializer and `static {}` block, in source order.

Active uses are `new`, a call to a static method, a read or write of a static field that isn't a compile-time constant, and reflection that asks for initialization. Initializing a class initializes its superclass first. Declaring a variable of the type doesn't count, and neither does `PostcodeTable.class`, which loads the class but runs nothing.

Now the problem is plain. The health check calls `version()`, a static method, so it initializes `PostcodeTable`, and the initializer builds the table. The health check asked for one line of text and paid for 200,000 rows.

The Kotlin version has the same problem, and that one surprises people. A companion object's properties compile to static fields of the outer class, and the outer class's `<clinit>` fills them. The worked example below shows it in `javap` output, the JDK's tool for reading class files.

In the shop, the fix is a sealed box in the back room, opened only when a customer asks for what's inside. In code, it's the **holder idiom**: give the expensive field a small class of its own.

""" + pair(J_HOLDER, K_HOLDER) + """

Now `version()` touches only `PostcodeTable`. The JVM loads and initializes `Holder` the first time `depotOf` reads `Holder.TABLE`. Two things changed in Kotlin: the `class` with a companion became an `object`, and the table moved into a private nested `object`, which is a class of its own with its own `<clinit>`.

You may wonder what happens if eight requests arrive at once and all call `depotOf` first. The table is still built once. The JVM initializes each class under its own lock (JLS 12.4.2, the language rules for initialization): one thread runs the initializer, and the others wait, then see the finished table. In Kotlin, `val table by lazy { build() }` gives the same laziness with a lock you can see. The memory model track's lesson "Lazy init done right: double-checked locking and holders" shows why the holder is safe.

Lazy isn't always better, though. Moving the cost to the first lookup makes the first customer wait instead. Be lazy about work that many starts never need, such as a rarely used report. Do the work early, on purpose, when every request needs it.

**Work that every start pays for should be work that every start needs. Move the rest behind a holder.**

Check the rule on a case we didn't show. `PostcodeTable` gets `public static final String VERSION = "postcodes-2026.11";`, and the health check reads `PostcodeTable.VERSION` instead. Is the table built? (No. `javac` copies a compile-time constant into the caller's class file, so reading it doesn't touch `PostcodeTable` at all.)

We can now take work off the start-up path. To know whether that helped, we need a clock, and there are three to choose from."""

# ---------------------------------------------------------------- section 2
S2 = """The tracking service from the opening printed two numbers that disagreed. There's a third one, and the three are easy to mix up.

The first is the JVM's own. `-Xlog:startuptime` prints the phases of creating the VM, and its last line reads like `Create VM, 0.0550112 secs`. That's the lights going on: the JVM is ready to run `main`. It says nothing about your code.

The second is the program's own log line, such as `started in 0.151s`. It's the shop turning its sign to OPEN. The program measures it from the inside, and every framework starts its clock at a slightly different place. Our demo service prints the JVM's uptime at the moment its server is ready to accept connections.

The third is **time to first request**: the time from launching the process to the first successful answer, measured from outside. A request is a message another program sends to ask for something, and a successful answer on the web carries status 200, the code for "OK". This is the first customer walking out with what they came for, and it's the only clock the street sees. A load balancer, a program that spreads incoming requests over several copies of a service, waits for it. So do your users.

`FirstRequestTimer`, in the Try it below, reads all three. It starts the tracking service in a second JVM, asks `/track` every 2 ms from outside, and stops its clock at the first 200. On JDK 25.0.5, on a busy machine with 4 cores (a core is one of the processor's independent workers), one run printed:

```text
log      : [0.056s][info][startuptime] Create VM, 0.0550112 secs
log      : started in 0.151s. Listening on: http://127.0.0.1:40931
first 200: 429 ms after launch, measured outside (19 attempts)
```

That's 55 ms, 151 ms and 429 ms. The service's own clock is honest; it simply starts late and stops early. The gap after it holds the launcher, the creation of the process and the first request itself. That request loads more classes again: the code that reads it, builds the answer and writes it out. On a machine this busy, some of the gap is plain waiting for a free core. Over nine runs in a row, the medians were 62, 255 and 529 ms.

Even the first 200 isn't the end of the story. HotSpot, the JVM in most JDK builds, has two JIT compilers: C1 compiles quickly with simple optimizations, and C2 compiles slowly into much faster code. Early requests run in the interpreter or in C1's code, and C2 takes over a method only after it has run often. So a new copy of a service answers at once, but slowly for a while. Lesson 4 of this track comes back to that, and the performance track's first lesson, "From bytecode to machine code", covers the tiers.

**Time start-up from outside the process. That's the clock your users read.**

Before the Try it, predict this. `-Xshare:off` turns the JDK's archive off. Does it slow down `Create VM` too, or only the two later clocks? Think about which classes the JVM needs while it creates itself.

Time is half of what a start costs. The other half is memory, and there the numbers disagree even more."""

# ---------------------------------------------------------------- section 3
S3 = """The same demo can also ask how much memory the service takes, and two honest answers differ by a factor of five. Run it with `-XX:NativeMemoryTracking=summary`, and on JDK 25.0.5 it printed:

```text
RSS      : VmRSS: 60376 kB, RssAnon: 33056 kB, RssFile: 27320 kB
NMT      : Total: reserved=4904MB, committed=296MB
NMT      : Java Heap (reserved=3420MB, committed=216MB)
```

Footprint is how much memory a running program really takes. Native Memory Tracking (NMT) is the JVM's own accounting of its memory, and it says the JVM has **committed** 296 MB, 216 MB of it for the heap. Committed memory is memory the JVM has asked the operating system for. The operating system says the process has about 60 MB **resident**. RSS, the resident set size, is the memory of a process that is really in RAM.

Both are right, and the shop explains why. Committed is the floor space you've booked; resident is the floor you've actually put shelves on. Memory comes in pages, small blocks of usually 4 KB, and a page becomes resident only when the program first touches it. A fresh heap is mostly untouched pages. Reserved is larger still: 4,904 MB of addresses set aside, most of them never even booked.

RSS is the number a memory limit cares about, and it holds much more than the heap. It counts the touched heap pages and metaspace, the code cache where the JIT keeps its machine code, and the tables of the garbage collector, the part of the JVM that frees memory no object uses anymore. It also counts every thread's stack, the mapped archive from the first section, the JDK's modules file and the JVM itself. `RssAnon` is memory the process made for itself. `RssFile` is pages read from files, such as the modules file, which processes that map the same file can share.

You can read all of it with three commands:

```bash
ps -o pid,rss,args -p <pid>                 # RSS in kB, on Linux and macOS
grep -E 'VmRSS|RssAnon|RssFile' /proc/<pid>/status
jcmd <pid> VM.native_memory summary         # only if started with -XX:NativeMemoryTracking=summary
```

`<pid>` is the process id, the number the operating system gives each running program, and `jcmd` is a tool that comes with the JDK.

Many services run in a container, a box the operating system builds around a program to cap its memory and CPU. When the program goes over the memory limit, the operating system stops it, and it judges by resident memory. So "heap used" on a monitoring dashboard isn't your footprint either. It leaves out everything in the list above, and it counts live objects, not the heap pages the collector has already touched.

**A memory limit counts resident pages. Measure RSS, then ask NMT where it went.**

Check yourself: the service starts with `-Xms2g`, which makes the JVM commit a 2 GB heap at once. Right after start-up, is its RSS about 2 GB? (No. The JVM books 2 GB of floor, but RSS grows only as the program and the collector touch those pages.)

Every number in this lesson comes back on the next launch, because the JVM keeps nothing between runs. Almost nothing, that is: those 793 classes from the archive were unpacked before the shop ever opened."""

ASIDE3 = {
    "title": "What about the memory figure my container tool shows?",
    "body": "Docker, a popular tool for running containers, has a `docker stats` command that prints a memory figure for each one. The Quarkus project, which makes a framework for Java services, warns against using it for footprint in its guide on measuring performance: it \"only measures a subset of the in-use resident pages\", while a container is stopped \"based on its full RSS memory usage\". The guide suggests `ps -e -o pid,rss,args`, or `docker top <id> -o pid,rss,args`, instead. Both print the RSS this section measures. Lesson 3 of this track meets Quarkus properly."
}

L = {
 "id": "boot-01",
 "title": "Why the JVM starts slowly, and how to measure it",
 "minutes": 35,
 "goal": "By the end you can say where a JVM's start-up time and memory go, measure them with the clock users see and the memory the operating system counts, and move expensive static work off the start-up path with a holder class.",
 "opening": OPENING,
 "warmup": {
  "q": "`ClassSourcesDemo` has exactly one class of its own. It reads three lines of settings, formats a date and joins a few strings. How many classes does the JVM load to run it on JDK 25?",
  "options": ["About 10: the demo plus the few JDK classes it uses", "About 100", "About 800", "About 30,000: the whole JDK"],
  "answer": 2,
  "why": "On JDK 25.0.5 it loaded 818 classes: 1 from the demo, 793 ready-made from the JDK's archive, 19 parsed from the JDK's modules file and 5 generated on the spot. Before `main` runs, the JVM needs hundreds of its own classes for strings, threads, class loaders and the module system. A generated app with 300 classes of its own loaded about 1,500. The JDK is most of the work, not your code, and the first section counts it."
 },
 "sections": [
  {
   "h": "Start-up is work the JVM repeats on every launch",
   "body": S0,
   "try": {
    "title": "Count where your classes come from",
    "minutes": 4,
    "steps": [
     "Read `ClassSourcesDemo`. It starts a second JVM with `-Xlog:class+load`, runs a little start-up work there (settings, a regular expression, a date, a stream), and groups the log lines by `source:`.",
     "Predict: out of roughly 800 classes, how many come from the JDK's archive? Then run it from `labs/` with the command below.",
     "Run it again with `-Pargs=-Xshare:off` added. That turns the archive off in the second JVM. Predict the `jrt:/` line first.",
     "Run the Kotlin twin (`ClassSourcesDemoKt`) once, and look at the `file:` line."
    ],
    "code": demo("ClassSourcesDemo"),
    "expect": "Gradle runs the demo on the JDK that runs Gradle. On JDK 25.0.5: 818 classes, 793 from the shared objects file, 19 from `jrt:/`, 5 hidden and 1 from `file:`, the demo itself. With `-Xshare:off`: 831 classes, 816 parsed from `jrt:/`, 14 hidden, none shared. On JDK 21 the same runs gave 734 (718 shared) and 767 (747 from `jrt:/`). The Kotlin twin loads 929 on JDK 25 and 876 on JDK 21, with 63 from `file:` both times, because the Kotlin standard library is a JAR on your class path like any other."
   },
   "refs": [
    {"title": "The java command (JDK 25 man page source): -Xlog and class data sharing", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/man/java.md", "kind": "docs"}
   ]
  },
  {
   "h": "Loading is lazy, and initialization is lazier",
   "body": S1,
   "try": {
    "title": "Predict the order of static initializers",
    "minutes": 4,
    "steps": [
     "Open `InitOrderDemo`. `main` calls `Eager.version()`, then `Lazy.version()`, then `Lazy.table()` twice. Each static initializer adds a line to a log.",
     "Write down the order of the log lines before you run it. Which call adds no line at all?",
     "Run it. Then run the Kotlin twin, `InitOrderDemoKt`, which compares a companion object (`Postcodes`), a nested object (`Depots`) and `by lazy` (`Routes`)."
    ],
    "code": demo("InitOrderDemo"),
    "expect": "Java prints `main starts`, `Eager.<clinit> builds the table`, `Lazy.<clinit> (no table here)`, `-- both versions read --`, `Lazy.Holder.<clinit> builds the table`, `-- Lazy.table() called --`. Calling `Eager.version()` built a table nobody asked for. The second `Lazy.table()` adds nothing, because a class is initialized once. Kotlin prints `Postcodes companion: table built with the outer class` before `-- all three versions read --`, and `Depots.Holder: table built` and `Routes lazy: table built` only after it."
   },
   "refs": [
    {"title": "JLS 12.4: Initialization of classes and interfaces", "url": "https://docs.oracle.com/javase/specs/jls/se25/html/jls-12.html#jls-12.4", "kind": "docs"}
   ]
  },
  {
   "h": "Three clocks, and only one is what users see",
   "body": S2,
   "figure": {"svg": FIG, "caption": "The JVM's clock stops when the lights go on, the program's at its OPEN sign, and only the outside clock waits for the first customer."},
   "try": {
    "title": "Read all three clocks",
    "minutes": 5,
    "steps": [
     "Read `FirstRequestTimer`. It picks a free port, starts the same class as a tracking service in a second JVM, asks `/track` every 2 ms from outside, and stops the clock at the first 200.",
     "Run it with `-Pargs=-Xlog:startuptime` added to the command below. Write down the three numbers, then run it twice more: they move around.",
     "Predict what turning the archive off does to each clock. Then run it with `-Pargs='-Xlog:startuptime -Xshare:off'`, three times."
    ],
    "code": demo("FirstRequestTimer"),
    "expect": "Medians of nine runs on JDK 25.0.5, on a 4-core machine with a load average of about 25: `Create VM` 62 ms, `started in` 255 ms, first 200 at 529 ms. With `-Xshare:off` all three moved: 173 ms, 348 ms and 731 ms. Creating the VM already loads the core `java.lang` classes, so it slows down too, and every later class is now read, parsed and verified from the modules file. JDK 21 moved the same way. Single runs jump around by a factor of two on a busy machine, so compare runs on the same machine, several of each."
   }
  },
  {
   "h": "Footprint is RSS, and the heap is only part of it",
   "body": S3,
   "aside": ASIDE3,
   "try": {
    "title": "Committed is not resident",
    "minutes": 3,
    "steps": [
     "Run `FirstRequestTimer` again with `-Pargs=-XX:NativeMemoryTracking=summary`. Before it stops the service, the demo asks it for its NMT summary with `jcmd`.",
     "Compare the `Total: committed` line with `VmRSS`. Which one would a 512 MiB memory limit compare against?",
     "On Linux, run `grep Rss /proc/self/status` in a shell to see the same fields for `grep` itself."
    ],
    "code": demo("FirstRequestTimer"),
    "expect": "On JDK 25.0.5, NMT reported `committed=296MB` with `Java Heap (reserved=3420MB, committed=216MB)`, while `VmRSS` was about 60,000 kB. The JVM has committed far more than it has touched. A memory limit counts resident pages, so RSS is the number to watch. On macOS the demo prints the `ps` value instead of the `/proc` breakdown."
   },
   "refs": [
    {"title": "Quarkus guide: Measuring performance (RSS, not docker stats)", "url": "https://github.com/quarkusio/quarkus/blob/main/docs/src/main/asciidoc/performance-measure.adoc", "kind": "read"}
   ]
  }
 ],
 "compare": {
  "title": "A lazy table in Java and in Kotlin",
  "java": {"title": "DepotDirectory.java", "src": "public final class DepotDirectory {\n    // eager: built in DepotDirectory.<clinit>, on the first use of the class\n    private static final Map<String, String> ALIASES = loadAliases();\n\n    // lazy: built in Holder.<clinit>, on the first read of Holder.POSTCODES\n    private static final class Holder {\n        static final Map<String, String> POSTCODES = loadPostcodes();\n    }\n\n    public static String version() { return \"dir-v7\"; }\n    public static String depotOf(String postcode) { return Holder.POSTCODES.get(postcode); }\n}"},
  "kotlin": {"title": "DepotDirectory.kt", "src": "object DepotDirectory {\n    // eager: built in DepotDirectory.<clinit>, on the first use of the object\n    private val aliases = loadAliases()\n\n    // lazy: Holder is its own class with its own <clinit>\n    private object Holder {\n        val postcodes = loadPostcodes()\n    }\n\n    // also lazy, with a visible lock (LazyThreadSafetyMode.SYNCHRONIZED by default)\n    val routes by lazy { loadRoutes() }\n\n    fun version() = \"dir-v7\"\n    fun depotOf(postcode: String) = Holder.postcodes[postcode]\n}"},
  "note": "Both versions compile to the same JVM mechanism: a static field filled in a class initializer, which runs once, on first active use, under the JVM's initialization lock. What differs is where Kotlin puts the fields. Properties of an `object` live in the object's own class. Properties of a `companion object` live as static fields of the outer class, so touching the outer class at all builds them. A private nested `object` is the exact twin of Java's holder class. `by lazy` is a library feature, not a JVM one: it creates a small `Lazy` object and takes a lock on first access. That costs a little, but it also works for instance properties, where a holder class can't help."
 },
 "worked": {
  "title": "Find and fix a companion object that builds on start-up",
  "steps": [
   {"say": "The tracking service's health check calls `DeliveryCalendar.source()` to report where the public holidays came from. Start-up got 400 ms slower the week this class arrived. Here it is, with its Java equivalent. Before you read on, decide whether `source()` loads the holiday file.",
    "code": "class DeliveryCalendar {\n    companion object {\n        private val holidays: Set<LocalDate> = loadHolidayFile()   // 400 ms\n\n        fun source() = \"national-holidays-2026\"\n        fun isHoliday(day: LocalDate) = day in holidays\n    }\n}",
    "lang": "kotlin", "alt_lang": "java",
    "alt_code": "public final class DeliveryCalendar {\n    private static final Set<LocalDate> HOLIDAYS = loadHolidayFile();   // 400 ms\n\n    public static String source() { return \"national-holidays-2026\"; }\n    public static boolean isHoliday(LocalDate day) { return HOLIDAYS.contains(day); }\n}"},
   {"say": "It does. Let the class file settle it: `javap -p` lists a class's members, private ones included. Here is its output for this lesson's Kotlin demo class `Postcodes`, which has the same shape. The `table` property is a `private static final` field of the outer class itself, and the outer class's `static {}` fills it. So the first call to anything on the companion initializes the outer class, and the table is built.",
    "code": "$ javap -p workbench/startup/l01/demo/Postcodes.class\nCompiled from \"InitOrderDemo.kt\"\npublic final class workbench.startup.l01.demo.Postcodes {\n  public static final workbench.startup.l01.demo.Postcodes$Companion Companion;\n  private static final java.util.Map<java.lang.String, java.lang.String> table;\n  public workbench.startup.l01.demo.Postcodes();\n  public static final java.util.Map access$getTable$cp();\n  static {};\n}",
    "lang": "text"},
   {"say": "Give the holidays a class of their own. The health check now touches only `DeliveryCalendar`. The first delivery that asks `isHoliday` initializes `Holder` and pays the 400 ms once.",
    "code": "object DeliveryCalendar {\n    fun source() = \"national-holidays-2026\"\n    fun isHoliday(day: LocalDate) = day in Holder.holidays\n\n    // 1. its own class, so its own initializer\n    private object Holder {\n        val holidays: Set<LocalDate> = loadHolidayFile()\n    }\n}",
    "lang": "kotlin", "alt_lang": "java",
    "alt_code": "public final class DeliveryCalendar {\n    public static String source() { return \"national-holidays-2026\"; }\n    public static boolean isHoliday(LocalDate day) { return Holder.HOLIDAYS.contains(day); }\n\n    // 1. its own class, so its own initializer\n    private static final class Holder {\n        static final Set<LocalDate> HOLIDAYS = loadHolidayFile();\n    }\n}"},
   {"say": "Prove it instead of trusting it. Run with `-Xlog:class+load` and check that the holder class loads only after the cheap calls. Here's this lesson's Kotlin demo on JDK 25.0.5: `Depots$Holder` loads last, after all three `version()` calls, and its line comes after `Routes`, whose lambda shows up as a hidden class.",
    "code": "[0.128s][info][class,load] workbench.startup.l01.demo.Postcodes source: file:.../demo/\n[0.128s][info][class,load] workbench.startup.l01.demo.Postcodes$Companion source: file:.../demo/\n[0.241s][info][class,load] workbench.startup.l01.demo.Depots source: file:.../demo/\n[0.241s][info][class,load] workbench.startup.l01.demo.Routes source: file:.../demo/\n[0.243s][info][class,load] workbench.startup.l01.demo.Routes$$Lambda/0x0000000040042830 source: workbench.startup.l01.demo.Routes\n[0.248s][info][class,load] workbench.startup.l01.demo.Depots$Holder source: file:.../demo/",
    "lang": "text"}
  ]
 },
 "lab": {
  "title": "Take a table off the start-up path, and build an outside clock",
  "minutes": 15,
  "files": [
   "labs/startup/src/main/java/workbench/startup/l01/PostcodeTable.java",
   "labs/startup/src/main/java/workbench/startup/l01/FirstRequestProbe.java"
  ],
  "run": "./gradlew :startup:test --tests 'workbench.startup.l01.*'",
  "steps": [
   "Run the tests once. Five of the nine fail: `version() does not build the table`, and all four probe tests.",
   "Open `PostcodeTable`, the tracking service's map from postcode to depot. Fix it with the holder idiom: move `TABLE` into a `private static final class Holder`, and read `Holder.TABLE` in `depotOf`. Keep calling `build()`, which records `table-built` so the tests can see when it runs.",
   "Now write `FirstRequestProbe.await`, the outside clock from this lesson. Build one `HttpRequest` with a short timeout. Loop up to `maxAttempts`: send it, record the status as a string, and stop at 200. Catch `java.net.ConnectException` and record `\"refused\"`, because nothing listening yet only means \"not up yet\". Sleep `pause` between attempts.",
   "Run the tests until all nine pass. Then read `PostcodeTableTest`. Each test gets a `FreshLoader`, a class loader of its own, so each one sees a `PostcodeTable` that nobody has initialized yet."
  ],
  "hints": [
   "Why does each test need a fresh class loader? A class is initialized once per loader. If every test used the normal one, the first test to call `depotOf` would build the table, and every later test would find it already built.",
   "`client.send(request, HttpResponse.BodyHandlers.discarding())` returns a response whose `statusCode()` you need. Nothing else of the answer matters.",
   "`ConnectException` extends `IOException`, so catch it first. Treat any other `IOException` (a connection reset while the server starts) as a failed attempt too."
  ],
  "done_when": "All nine tests in `PostcodeTableTest` and `FirstRequestProbeTest` pass."
 },
 "drill": {
  "title": "Write the holder idiom from memory",
  "minutes": 4,
  "prompt": "Close this page. Write a class `CountryRules` with `static String version()`, which returns `\"rules-3\"`, and `static String regionOf(String country)`, which reads from a map built by an expensive `load()` method. `version()` must never call `load()`, and `load()` must run once even when many threads make their first call together, with no `synchronized` in your code. Then write the Kotlin version with an `object`.",
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
  "Every launch repeats the morning routine: create the VM, then load, parse and verify each class the first time it's needed (818 for a one-class demo on JDK 25), interpret until the JIT has profiles, and run any framework's own start-up.",
  "`-Xlog:class+load` shows where each class came from: `shared objects file` (the JDK's archive), `jrt:/` (parsed from the JDK's modules file now), `file:` (your class path), or a class name (a hidden class, such as a lambda).",
  "A class's `<clinit>` runs on first active use. A Kotlin companion's properties are static fields of the outer class; a Java holder class or a Kotlin nested `object` keeps expensive work off the start-up path, and the JVM's init lock builds it once.",
  "There are three clocks: `Create VM` (the lights on), the program's own `started in` (the OPEN sign), and time to first request, measured from outside (the first customer served). Only the last is what users and load balancers see.",
  "Footprint is the whole process's RSS. NMT's committed memory includes pages nobody has touched, and \"heap used\" leaves out metaspace, the code cache, thread stacks and more.",
  "The limit: a holder only moves work, and measuring only shows it. The JVM still unpacks and checks every class again on every launch, which is the work lesson 2's archives attack."
 ],
 "closing": "We started with a shop that unpacks everything each morning, and a service that said 0.151 s while its first customer waited 429 ms. The JVM runs that routine on every launch: it loads and checks hundreds of classes, runs static initializers on first use and interprets until the JIT catches up. Only the outside clock and RSS show what the street sees.\n\nNow look in your own code for `static final` fields, or companion properties, whose initializer calls something slow: `load(`, `read`, `parse`. Each one runs on the start-up path.\n\nNext, we'll keep yesterday's unpacked shelves in the back room. How much of the morning does class data sharing save, and what does Project Leyden's AOT cache add?",
 "quiz": [
  {"q": "A load balancer decides when a new copy of your service starts getting traffic. Which number tells you how long that takes?",
   "options": ["The `Create VM` line from `-Xlog:startuptime`", "The service's own `started in` log line", "Time from launching the process until the health check answers 200, measured from outside", "The time until C2 has compiled the hot methods"],
   "answer": 2,
   "why": "The load balancer sees only the outside clock: launch to first successful answer. `Create VM` stops before your code runs, and the service's own line is measured inside the process, from wherever its framework starts counting, and before the first request loads its own classes. C2 is about full speed, which comes later still."},
  {"q": "A health check calls `DepotDirectory.version()`. In Kotlin the class is `class DepotDirectory { companion object { val postcodes = loadPostcodes(); fun version() = \"v3\" } }`. Does the health check run `loadPostcodes()`?",
   "options": ["No, companion objects are initialized lazily, on first property access", "Yes: `postcodes` is a static field of `DepotDirectory`, filled by its static initializer, which this first use runs", "Only if the health check runs on a different thread", "No, because `version()` doesn't read `postcodes`"],
   "answer": 1,
   "why": "Kotlin compiles a companion's properties to static fields of the outer class and fills them in the outer class's `<clinit>`. Calling `version()` initializes `DepotDirectory`, and that runs `loadPostcodes()`, whether or not `version()` reads the field. A private nested `object` or `by lazy` would keep it off this path."},
  {"q": "For one service you see four numbers: a container tool's memory figure of 180 MiB, NMT total committed 420 MiB, live heap after a garbage collection 90 MiB, and `ps -o rss` 260 MiB. Which one counts against the container's memory limit?",
   "options": ["180 MiB from the container tool", "420 MiB committed", "90 MiB of live heap", "260 MiB of RSS"],
   "answer": 3,
   "why": "RSS counts every resident page of the process, heap or not, and that's what the limit judges. Committed memory includes pages nobody has touched yet, live heap ignores metaspace, the code cache, thread stacks and the rest, and a tool like `docker stats` measures only part of the resident pages."},
  {"q": "Which of these runs the static initializer of class `Depots`, assuming nothing else has?",
   "options": ["`Class.forName(\"com.example.Depots\", false, loader)`", "Declaring a local variable `Depots d = null;`", "Calling the static method `Depots.version()`", "Writing `Depots.class` to get its `Class` object"],
   "answer": 2,
   "from": "cls-01",
   "why": "A class is initialized on its first active use, and a static method call is one. `Class.forName` with `initialize` set to `false` loads the class without initializing it, a variable declaration needs neither, and a class literal gives you the `Class` object without running `<clinit>`."},
  {"q": "You start the same service with `-Xshare:off`. The number of classes it loads hardly changes, but its first answer comes about 200 ms later. Why?",
   "options": ["The JDK's classes are now read, parsed and verified from the modules file, instead of mapped ready-made from the archive", "The JIT is turned off along with sharing", "The heap is smaller, so the garbage collector runs more often", "The JVM now loads each of your classes twice"],
   "answer": 0,
   "why": "`-Xshare:off` turns off the JDK's default archive. The same classes still load, but each one now goes through finding, parsing and verifying. In the demo the `jrt:/` count jumped from 19 to 816 on JDK 25. The flag doesn't touch the JIT or the heap."}
 ],
 "flashcards": [
  {"front": "What does each line of `-Xlog:class+load` tell you?", "back": "The class name and its `source:`: `shared objects file` (the archive), `jrt:/...` (parsed from the JDK's modules file), `file:...` (your class path), or a defining class name for a hidden class such as a lambda."},
  {"front": "When does the JVM run a class's `<clinit>`?", "back": "On first active use: `new`, a static method call, a read or write of a non-constant static field, reflection that initializes, or initializing a subclass. Loading alone doesn't run it."},
  {"front": "Why is the holder idiom thread-safe with no lock in your code?", "back": "The JVM initializes each class under its own lock (JLS 12.4.2). One thread runs `Holder.<clinit>`; the others wait, then see the finished field."},
  {"front": "Is a Kotlin `companion object` property initialized lazily?", "back": "No. It compiles to a static field of the outer class, filled by the outer class's `<clinit>`, so any first use of the outer class builds it. Use a private nested `object` or `by lazy`."},
  {"front": "What does the `Create VM` line of `-Xlog:startuptime` measure?", "back": "Only the JVM creating itself, before `main` runs: not your classes, not the framework, not the first request."},
  {"front": "NMT says 296 MB committed and RSS is 60 MB. Which one is resident memory?", "back": "RSS. Committed memory has been requested from the operating system, but untouched pages (most of a fresh heap) aren't resident."},
  {"front": "Which start-up number does a load balancer see?", "back": "Time to first request: from launching the process to the first successful answer, measured from outside the process."}
 ],
 "terms": [
  {"term": "Class loading", "plain": "Finding a class's bytes and turning them into the JVM's internal form in metaspace."},
  {"term": "Verification", "plain": "The check, before a class runs, that its bytecode is type-safe."},
  {"term": "Static initializer (`<clinit>`)", "plain": "The method that sets a class's static fields and runs its static blocks, once, on first active use."},
  {"term": "Holder idiom", "plain": "Putting an expensive static field in a small nested class, so it is built on first use of that field only."},
  {"term": "Hidden class", "plain": "A class the JVM generates in memory while the program runs, with no class file, for example for a lambda."},
  {"term": "Time to first request", "plain": "From launching the process to the first successful answer, measured from outside."},
  {"term": "RSS", "plain": "Resident set size: the memory of a process that is really in RAM."},
  {"term": "NMT", "plain": "Native Memory Tracking: the JVM's own breakdown of the memory it has reserved and committed."}
 ],
 "explain_back": {
  "prompt": "A teammate says: \"Our service starts in 0.9 seconds and uses 180 MiB. I read it in the service's log and in the container dashboard.\" Explain what each number leaves out, and what you would measure instead.",
  "answer": "The 0.9 seconds is the service's own clock, taken inside the process. It starts after the launcher and the JVM have done their part, and it stops before the first request, which loads more classes and runs in the interpreter. The load balancer and the users see the time from launch to the first 200, so I'd ask the health check from outside, again and again, and time that. The 180 MiB from the dashboard may cover only part of the resident pages. The container is stopped on its full RSS, which includes metaspace, the code cache, thread stacks, the mapped archive and the touched heap. I'd read RSS with `ps -o rss` or `/proc/<pid>/status`, and use NMT only to see which part of the JVM the memory went to."
 },
 "deeper": {
  "minutes": 10,
  "body": "Loading is lazy, but not quite as lazy as the rule in this lesson suggests. Two things load classes you never called.\n\nThe first is the verifier. To check that a method is type-safe, it sometimes needs to know whether one class is a subtype of another, for example when two branches produce different classes that meet in the same variable. To answer that, it loads both. A prototype of lesson 2's lab hit this: a test class whose static initializer read a field of its outer class pulled in the outer class, and verifying that class pulled in more. That's why the lab compares the exact set of classes your own loader defined, taken from a run of the reference answer, and never a count of all loaded classes, which changes from one JDK build to the next.\n\nThe second is the framework. Scanning for annotations reads class files, and wiring objects by reflection loads every class it wires, all at start-up. Some frameworks, Quarkus among them, move that work into the build: they index the classes, decide the wiring and generate plain code that does it, so a start has nothing to scan. Lesson 3 of this track, and the capstone after it, come back to that idea.\n\nIf you want to see where a large program spends its start-up, pipe `-Xlog:class+load` through `sed -E 's/.*source: //' | sort | uniq -c | sort -rn | head` for the same histogram as the demo. The JDK Flight Recorder's `jdk.ClassLoad` event, off by default, records a stack trace for each class load once you enable it, so you can see who asked for each box. Measure first, then pick a fix from lessons 2 to 4."
 },
 "sources": [
  {"title": "The java command, JDK 25 (man page source: -Xlog, class data sharing, AOT cache)", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/man/java.md"},
  {"title": "Java Virtual Machine Specification, chapter 5: Loading, Linking, and Initializing", "url": "https://docs.oracle.com/javase/specs/jvms/se25/html/jvms-5.html"},
  {"title": "Java Language Specification 12.4.2: Detailed initialization procedure", "url": "https://docs.oracle.com/javase/specs/jls/se25/html/jls-12.html#jls-12.4.2"},
  {"title": "Quarkus guide: Measuring performance", "url": "https://github.com/quarkusio/quarkus/blob/main/docs/src/main/asciidoc/performance-measure.adoc"}
 ]
}
out = ROOT / "content/lessons/boot-01.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
