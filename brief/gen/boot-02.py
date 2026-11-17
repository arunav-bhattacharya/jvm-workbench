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
    '<text class="t-s t-m" x="85" y="40" text-anchor="middle">a day with a notebook</text>'
    '<text class="t-s t-m" x="375" y="40" text-anchor="middle">the evening: app does not run</text>'
    '<text class="t-s t-m" x="635" y="40" text-anchor="middle">every morning after</text>'
    '<path class="ln-d" d="M 20 124 L 20 134 L 440 134 L 440 124"/>'
    '<text class="t-s t-a" x="230" y="154" text-anchor="middle">JDK 25+: -XX:AOTCacheOutput=app.aot does both in one command</text>'
    '<rect class="box-bad" x="20" y="174" width="670" height="36" rx="8"/>'
    '<text class="t-s" x="355" y="197" text-anchor="middle">valid only for the same JAR files, JDK build, OS and CPU, GC and module options</text>'
    '</svg>'
)

OPENING = """Back to the corner shop. Unpacking every box each morning is silly when the stock hardly changes. A sensible shopkeeper leaves yesterday's filled shelves in the back room and wheels them out at opening time. A clever one also keeps a note of which shelves she used and which shortcuts she learned, so tomorrow starts further along.

The JVM can do both. In the last lesson, 793 of a demo's 818 classes said `shared objects file`: they came ready-made from an archive the JDK ships. You can build a bigger archive that holds your own classes too. On JDK 25 you can build Project Leyden's AOT cache, which keeps the notes as well.

The catch is that each one is easy to switch off by accident, and the JVM says so only in a warning nobody reads. One mistake even makes start-up slower than having no archive at all. In this lesson, we'll look inside the JDK's own archive, add the tracking service's classes to one, train an AOT cache, and then break it on purpose. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
S0 = """Start with the cost of an empty back room. Turn the JDK's archive off with `-Xshare:off`, and `java -version` alone makes the JVM find, parse and verify 411 classes before it prints a line. With the archive on, it loads 396, and 393 of them come ready-made. Lesson 1's tracking service felt the difference. Over nine runs on JDK 25.0.5, `Create VM` took 173 ms instead of 62, and the first answer came at 731 ms instead of 529.

That archive is **class data sharing**, CDS for short: a file of classes the JVM has already parsed and verified, stored in the JVM's own internal form. Every JDK build since JDK 12 ships one, in `lib/server/classes.jsa`, with about 1,300 core JDK classes. (It came with JEP 341; a JEP, or JDK Enhancement Proposal, is the document that describes a new JDK feature.) In the shop, these are the shelves that came with the shop: the JDK's makers unpacked them before you ever opened.

The file doesn't hold class files. It holds the structures the JVM would otherwise build in metaspace, laid out the way they sit in memory. At start-up the JVM **memory-maps** the file: it asks the operating system to make the file part of the program's memory. Each page is then read from disk only when it's first touched. The JVM fixes up a few pointers and uses the classes as they are. All of that happens by default; `-Xshare:off` turns it off, which is mostly useful for lessons like this one.

There's more than one file in that folder, and the JVM picks the one that matches its settings. JDK 25 ships four. `classes_nocoops.jsa` is for a JVM running without compressed object pointers, the 32-bit object references it uses by default for heaps below 32 GB. The two `_coh` files are for compact object headers, a smaller layout for the hidden header every object carries. JEP 519 made them a product feature in JDK 25, still off by default.

That tells you what CDS can save and what it can't. It saves finding, parsing and verifying the archived classes: the unpacking and the checking. It doesn't run static initializers. Those still run on first use, in the same order, so lesson 1's 200,000-row table takes just as long with any archive. The research behind this course logged a program's initializer order with and without a JDK 21 archive and a JDK 25 AOT cache, and the output was identical. And an archive does nothing for the JIT, which still starts cold.

**An archive saves the unpacking and the checking. Your static initializers and the JIT still run on every start.**

Check yourself: with the archive on, `java -version` loaded 396 classes, and with it off, 411. Why would turning the archive off make the JVM load *more* classes? (Without the archive, the JVM must generate some classes on the spot that the archive would have supplied ready-made. On JDK 21 the gap is 35: 405 against 440.)

The JDK's shelves arrive ready-made. The tracking service's own classes still come out of boxes, one by one, from `file:`."""

# ---------------------------------------------------------------- section 1
S1 = """The default archive covers the JDK. **AppCDS**, application class data sharing, adds your own classes to an archive. It has been part of OpenJDK since JDK 10 (JEP 310), and it's the start-up gain you can have on JDK 21 without touching your code. There are three ways to build one.

The dynamic archive (JDK 13 and later, JEP 350) needs one **training run**: an ordinary run of the program whose extra job is to write down what it loaded. The JVM writes the archive when that run exits:

```bash
java -XX:ArchiveClassesAtExit=app.jsa -cp tracker.jar tracker.Main    # training run
java -XX:SharedArchiveFile=app.jsa -cp tracker.jar tracker.Main       # every start after
```

A dynamic archive stores only what the default archive lacks, so it's small: 221,184 bytes for the demo below.

The static archive takes three steps: record the list of classes, dump them into an archive, then use it.

```bash
java -Xshare:off -XX:DumpLoadedClassList=app.classlist -cp tracker.jar tracker.Main
java -Xshare:dump -XX:SharedClassListFile=app.classlist -XX:SharedArchiveFile=app.jsa -cp tracker.jar
java -XX:SharedArchiveFile=app.jsa -cp tracker.jar tracker.Main
```

`-XX:+AutoCreateSharedArchive` (JDK 19 and later), used with `-XX:SharedArchiveFile=app.jsa`, folds all this into your normal start command. If the file exists and came from the same JDK, the JVM uses it; if not, it writes one at exit. That's handy on a laptop and wrong for a server that starts from a read-only disk, or one that's thrown away after every run. There, build the archive when you build the program.

`ArchiveLadder`, in the Try it below, packs a small workload into a JAR and starts it under each setup. On JDK 25.0.5, one run printed:

```text
setup                  loaded  from archive    wall ms
no sharing                909             0        388
default CDS               897           868        187
AppCDS (dynamic)          826           794        153
AOT cache                 959           959         86
```

Read the counts first, because they don't change from run to run. With AppCDS, the demo's own classes join the JDK's on the ready-made shelves, and the JVM generates fewer classes on the spot. The times come from one run on a busy machine, so treat them as a direction. The research behind this course measured more carefully, with 30 interleaved runs of a 300-class app on JDK 21. AppCDS cut its start-up CPU time about in half, from 349 ms to 171 ms. Leave the last row for the next section.

The archive comes with rules, and the JVM checks them like a strict stock clerk. The class path must hold JAR files, not folders of class files. It must be the same as when the archive was made, or start with it. And if a JAR changed after the archive was made, the JVM refuses the archive. Here's JDK 21 starting a rebuilt JAR with its old archive, trimmed:

```text
[0.020s][warning][cds] hello.jar timestamp has changed.
[0.020s][warning][cds] hello.jar size has changed.
[0.020s][warning][cds,dynamic] Unable to use shared archive. The top archive failed to load: hello.jsa
  version TWO, rebuilt
```

It warned, ran the new code from the JAR, and kept the default archive for the JDK's own classes. Remember that last detail, because the AOT cache behaves differently.

**Build the archive with the program, from the same JARs, and ship the two together.**

Check yourself: you add `-XX:ArchiveClassesAtExit=app.jsa` while the class path is a folder of compiled classes. What happens at exit? (JDK 25 refuses with `Cannot have non-empty directory in paths`. Pack the classes into a JAR first, as `ArchiveLadder` does.)

AppCDS saves the unpacking. But a class taken from the shelf still has to be linked, every lambda is still built on the spot, and the JIT still learns everything from scratch. That's the work Project Leyden goes after."""

# ---------------------------------------------------------------- section 2
S2 = """Project Leyden is the OpenJDK project that moves start-up work out of production runs, the real runs that serve your users. Its first result is the **AOT cache**, where AOT means ahead of time. It arrived one JEP at a time, and every piece of it is a final, standard feature: no preview flag and no special switch.

| JDK | What arrived |
|---|---|
| 24 | JEP 483: the AOT cache, with classes already loaded and linked; flags `-XX:AOTMode`, `-XX:AOTConfiguration` and `-XX:AOTCache` |
| 25 (LTS) | JEP 514: one command, `-XX:AOTCacheOutput`, to create it. JEP 515: method profiles from training, for faster warm-up |
| 26 | JEP 516: the full cache works with every garbage collector, ZGC included |
| 27 | no Leyden JEP; `-XX:AOTMode=required` becomes the name for `on` |
| 28, in development | JEP 544: compiled machine code in the cache |

LTS means a long-term-support release, the kind most teams run in production, and JDK 25 is the current one.

The `java` manual names three phases, and the shop has all three. In training, you run the program on a realistic workload, and the JVM writes what it loaded and linked into an AOT configuration file. That's an ordinary day, with a notebook on the counter. In assembly, the JVM turns that file into the cache, and your program doesn't run: the evening, spent writing up the notes. In production, every start uses the cache. On JDK 25, one command does the first two:

```bash
java -XX:AOTCacheOutput=app.aot -cp tracker.jar tracker.Main     # training and assembly, JDK 25+
java -XX:AOTCache=app.aot -cp tracker.jar tracker.Main           # production
```

When training and assembly run at different times, use the two-step form from JDK 24:

```bash
java -XX:AOTMode=record -XX:AOTConfiguration=app.aotconf -cp tracker.jar tracker.Main
java -XX:AOTMode=create -XX:AOTConfiguration=app.aotconf -XX:AOTCache=app.aot -cp tracker.jar
```

The one-step command does the same underneath: when the training run ends, it starts a second JVM with `-XX:AOTMode=create`, as the Try it below shows.

The cache holds more than an AppCDS archive. Normally the JVM **links** a class lazily. The first time an instruction runs, the JVM turns a symbolic name in the class file, such as `java/util/Map.get`, into a pointer to the real method. The first run of a lambda costs more. Its `invokedynamic` instruction, the bytecode that asks a helper method how to make a call, builds the lambda's hidden class on the spot. The AOT cache stores the results of that work from the training run. It holds classes already linked, names and lambda call sites already resolved, and Java objects the JVM would otherwise build at every start, such as its map of modules. On JDK 25 it also stores the method profiles that tell the JIT what's hot.

Look back at the ladder. The AOT cache row loaded 959 classes, more than any other row, and all 959 came from the archive: the JVM loads and links every cached class before `main` runs. Code the training never ran gets none of this. It loads the usual way, as the lab shows.

The research behind this course measured the gain carefully on JDK 25. For a 300-class app, start-up CPU time fell from 504 ms to 81 ms, wall time from 431 ms to 98 ms, and peak memory from 64 MiB to 42 MiB. A small web service's median time to first request fell from 218 ms to 136 ms. None of that needed a code change.

**Train on work that looks like production. The cache only knows the shelves you used.**

A cache built from one day's notes fits that day's shop exactly. Change the stock, the supplier or the layout, and it no longer fits."""

ASIDE2 = {
    "title": "Will my framework build the cache for me?",
    "body": "Quarkus, a framework for Java services, does from version 3.40. With `quarkus.package.jar.aot.enabled=true`, it trains the cache while your integration tests run (tests that start the whole program and talk to it from outside) and writes `target/quarkus-app/app.aot`, which you use with `java -XX:AOTCache=app.aot -jar quarkus-run.jar`. Its `aot-jar` packaging leaves all class loading to the JDK's own class loaders, the objects that find and define classes, because Leyden doesn't support custom ones yet. The guide repeats the rule from this section: \"The more representative your integration tests are of production traffic, the more effective the AOT cache will be.\" On JDK 21, `quarkus.package.jar.aot.type=app-cds` builds an AppCDS archive instead."
}

# ---------------------------------------------------------------- section 3
S3 = """The `java` manual is blunt about it. An AOT cache belongs to one application class path, one JDK release, and one operating system and CPU, and "if any of the above changes, you must recreate the AOT cache". The JVM checks, and in the default `auto` mode it starts without the cache when a check fails.

A changed JAR is the worst case, because on early JDK 25 builds that check was missing. On 25.0.0 to 25.0.3, and on 26.0.0 to 26.0.1, the JVM never compared the application's JARs with the cache (bug JDK-8377932). Rebuild the JAR, keep the old cache, and the JVM serves the **old classes**. The research behind this course reproduced it on JDK 25 GA. The log said the class came from `shared objects file`, and the rebuilt program printed `version ONE`, the text of the build before. A real shopkeeper would notice last week's stock on her shelves. Those builds didn't.

The fix shipped in JDK 27 and was backported to 25.0.4 and 26.0.2. `StaleCacheDemo`, in the Try it below, runs the same experiment. On 25.0.5 the JVM rejects the cache and runs the new code (output trimmed):

```text
[0.038s][warning][aot] This file is not the one used while building the AOT cache: 'hello.jar', timestamp has changed, size has changed
[0.038s][error  ][aot] shared class paths mismatch (hint: enable -Xlog:class+path=info to diagnose the failure)
[0.039s][error  ][aot] Unable to map shared spaces
  version TWO, rebuilt
```

So require **JDK 25.0.4 or later** (26.0.2 or later on 26), and rebuild the cache with every JAR, in the same build step. On a fixed JDK an old cache can't run old code, but it still costs you the whole gain.

Here's the surprise the opening promised. A cache the JVM can't use leaves you with no archive at all: unlike AppCDS, it doesn't fall back to the default CDS archive. The one-class program in that demo loaded 542 classes from the default archive with no flag, and 0 with the stale cache. Even the version line shows it: `java -XX:AOTCache=nope.aot -version` ends with `mixed mode`, where a normal start says `mixed mode, sharing`. A typo in the file name makes start-up slower than no flag at all.

The garbage collector matters on JDK 25 too. A garbage collector, or GC, is the part of the JVM that frees memory no object uses anymore, and you choose one with a flag. On 25.0.5, a cache trained under the default collector, G1, gave 0 archived classes under `-XX:+UseZGC`, and all 959 under the Parallel and Serial collectors. JDK 26's JEP 516 removes this limit. Until then, train with the collector you run.

Module and agent options must match as well: `--module-path`, `--add-modules` and `--enable-native-access` should be the same in training and production. The manual also lists "certain JVMTI options" as incompatible. JVMTI is the JVM's tool interface. Agents, add-ons loaded into the JVM to watch or change a program, use it to rewrite classes as they load, so this matters the day someone adds a monitoring agent.

Two flags catch all of this. `-Xlog:aot` prints `Opened AOT cache app.aot.` when the cache works, and the reason when it doesn't. `-XX:AOTMode=on` (JDK 24 to 26; `required` from JDK 27) makes the JVM stop with `Unable to use AOT cache.` instead of running without it. Use that in your build's checks, and keep it out of production. The JDK 27 manual warns that your application "may fail to launch" if, for example, a cloud provider's monitoring agent adds an incompatible option.

**A cache the JVM can't use is worse than none. Check that it opened, in every build.**

Check yourself: you train on JDK 25.0.4 with G1, then deploy the same JAR on 25.0.5 with G1. Does the cache load? (No. The cache records the exact JDK build, and the JVM refuses one made by any other build.)

Even a cache that opens leaves work in every new JVM: the interpreter still runs first, and the JIT still compiles. The next lesson removes the JVM's start-up altogether, at a price."""

L = {
 "id": "boot-02",
 "title": "Class data sharing and Project Leyden's AOT cache",
 "minutes": 40,
 "goal": "By the end you can build and use an AppCDS archive on JDK 21 and an AOT cache on JDK 25, prove from the logs that they're used, and avoid the traps that switch them off or, on JDK 25 builds before 25.0.4, run stale code.",
 "opening": OPENING,
 "warmup": {
  "q": "You rebuild your service's JAR with a bug fix, but keep the AOT cache from the previous build. You start it on JDK 25.0.5 with `-XX:AOTCache=app.aot`. What happens?",
  "options": ["It runs the fixed code with the full speed-up from the cache", "It runs the old code, served from the cache", "It warns that the JAR changed, ignores the cache, and runs the fixed code with no archive at all", "It refuses to start"],
  "answer": 2,
  "why": "On 25.0.4 and later the JVM compares the JAR with the cache, warns, and in the default `auto` mode carries on without the cache, and without the JDK's default archive too, so it starts slower than with no flag. On 25.0.0 to 25.0.3 the check was missing and the old classes really ran (bug JDK-8377932). It refuses to start only if you asked for that with `-XX:AOTMode=on`. The last section takes it apart."
 },
 "sections": [
  {
   "h": "The archive every JDK already ships",
   "body": S0,
   "try": {
    "title": "Look at the default archive",
    "minutes": 3,
    "steps": [
     "List the archives your JDK ships, with the first command.",
     "Predict: with `-Xshare:off`, will `java -version` load more classes than with the archive, fewer, or the same number? Then count both with the next two commands.",
     "Run the last command to see which archive file the JVM opened."
    ],
    "code": {"lang": "bash", "title": "terminal",
             "src": "ls -l \"$JAVA_HOME\"/lib/server/*.jsa\njava -Xlog:class+load -version 2>&1 | grep -c 'shared objects file'\njava -Xshare:off -Xlog:class+load -version 2>&1 | grep -c 'source:'\njava -Xlog:cds -version 2>&1 | grep -i opened",
             "run": ""},
    "expect": "On Ubuntu's JDK 25.0.5 build: four files (`classes.jsa` is 15,626,240 bytes, plus `classes_coh.jsa`, `classes_nocoops.jsa` and `classes_nocoops_coh.jsa`); 393 shared classes out of 396; 411 classes with sharing off; and `Opened shared archive file .../lib/server/classes.jsa.` On JDK 21: two files, 405 of 405 shared, 440 with sharing off. The archive saves work, and it also saves the JVM from generating classes on the spot."
   },
   "refs": [
    {"title": "The java command, JDK 25: class data sharing and the AOT cache (man page source)", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/man/java.md", "kind": "docs"}
   ]
  },
  {
   "h": "AppCDS puts your own classes in the archive",
   "body": S1,
   "try": {
    "title": "Climb the archive ladder",
    "minutes": 5,
    "steps": [
     "Read `ArchiveLadder`. It packs its own package into `startup/build/boot02/app.jar` (CDS wants JARs), then runs the same small workload under each setup and counts the `source:` lines.",
     "Predict the \"from archive\" column for the AppCDS row, then run it from `labs/`.",
     "Run it twice more and compare the `wall ms` column between runs. Which columns stay the same?",
     "Run the Kotlin twin. Its class path is the app JAR plus `kotlin-stdlib`, and both go into the archive.",
     "Gradle runs demos on the JDK that runs Gradle, and the AOT cache row needs JDK 25. On JDK 21, run the class with a JDK 25 `java` instead: `java -cp startup/build/classes/java/demo workbench.startup.l02.demo.ArchiveLadder`."
    ],
    "code": demo("ArchiveLadder"),
    "expect": "On JDK 25.0.5: no sharing 909 loaded, 0 from the archive; default CDS 897 and 868; AppCDS 826 and 794, with a 221,184-byte archive; AOT cache 959 and 959, with an 11,018,240-byte cache. On JDK 21: 855/0, 821/789 and 754/719. The Kotlin twin on JDK 25 gave 875/0, 855/789, 722/656 and 966/966. The counts repeat exactly; the times jumped by a factor of two between runs on a busy machine."
   }
  },
  {
   "h": "Leyden's AOT cache: train, assemble, then run",
   "body": S2,
   "figure": {"svg": FIG, "caption": "Training writes down what the program loaded and linked, assembly turns those notes into the cache without running the program, and every production start maps it."},
   "aside": ASIDE2,
   "try": {
    "title": "Make an AOT cache by hand (JDK 25+)",
    "minutes": 4,
    "steps": [
     "Run `ArchiveLadder` once (previous Try it), so `startup/build/boot02/app.jar` exists. Then `cd labs/startup/build/boot02` and use a JDK 25 `java`.",
     "Run the first command: training and assembly in one go. Find the `Launching child process` line and the second `Picked up JAVA_TOOL_OPTIONS` line, which hands the child its settings.",
     "Run the second command and look for `Opened AOT cache`.",
     "Predict the count the third command prints. It names a cache file that doesn't exist. Then run it."
    ],
    "code": {"lang": "bash", "title": "terminal (JDK 25+)",
             "src": "java -XX:AOTCacheOutput=track.aot -cp app.jar workbench.startup.l02.demo.ArchiveLadder --work\njava -XX:AOTCache=track.aot -Xlog:aot -cp app.jar workbench.startup.l02.demo.ArchiveLadder --work | grep Opened\njava -XX:AOTCache=nope.aot -Xlog:class+load -cp app.jar workbench.startup.l02.demo.ArchiveLadder --work | grep -c 'shared objects file'",
             "run": ""},
    "expect": "On 25.0.5 the first command printed `Temporary AOTConfiguration recorded: track.aot.config`, then `Launching child process ... to assemble AOT cache track.aot using configuration track.aot.config`, a `Picked up JAVA_TOOL_OPTIONS: ... -XX:AOTMode=create` line, and `AOTCache creation is complete: track.aot 11010048 bytes`. The second printed `[0.020s][info][aot] Opened AOT cache track.aot.` The third printed errors ending in `Unable to map shared spaces`, still ran the program, and counted 0 shared classes: a bad cache path loses the default archive too."
   },
   "refs": [
    {"title": "JEP 483: Ahead-of-Time Class Loading & Linking", "url": "https://openjdk.org/jeps/483", "kind": "read"},
    {"title": "JEP 514: Ahead-of-Time Command-Line Ergonomics", "url": "https://openjdk.org/jeps/514", "kind": "read"},
    {"title": "Quarkus 3.40: AOT and AppCDS guide (aot.adoc)", "url": "https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/docs/src/main/asciidoc/aot.adoc", "kind": "docs"}
   ]
  },
  {
   "h": "A cache fits one JAR, one JDK and one set of flags",
   "body": S3,
   "try": {
    "title": "Run new code with an old cache",
    "minutes": 4,
    "steps": [
     "Read `StaleCacheDemo`. It compiles a one-class program that prints \"version ONE\", trains a cache on it, rebuilds the JAR to print \"version TWO, rebuilt\", and starts the new JAR with the old cache.",
     "Run it through Gradle. On JDK 21 it uses a dynamic CDS archive, because there's no AOT cache before JDK 24.",
     "If Gradle runs on JDK 21 and you have a JDK 25, run the class with that JDK's `java`: `java -cp startup/build/classes/java/demo workbench.startup.l02.demo.StaleCacheDemo`. Check `java -version` first, and predict which output you'll get."
    ],
    "code": demo("StaleCacheDemo"),
    "expect": "JDK 21 refuses the archive (`hello.jar timestamp has changed`, `hello.jar size has changed`, `Unable to use shared archive`) and prints `version TWO, rebuilt`. JDK 25.0.5 prints the `timestamp has changed, size has changed` warning, `Unable to map shared spaces` and `version TWO, rebuilt`, loaded from `file:hello.jar`. On JDK 25.0.0 to 25.0.3, the research behind this course saw the class come from `shared objects file` and the program print `version ONE` instead: the old class, served from the cache."
   },
   "refs": [
    {"title": "The fix: 8377932, AOT cache is not rejected when JAR file has changed", "url": "https://github.com/openjdk/jdk/commit/b41ba3a496b59c8058067a49617f798606f0a51c", "kind": "read"}
   ]
  }
 ],
 "compare": {
  "title": "A training entry point in Java and Kotlin",
  "java": {"title": "TrainingMain.java", "src": "/** Starts the service, sends it every kind of request real users send, then exits so the JVM writes the cache. */\npublic final class TrainingMain {\n    public static void main(String[] args) throws Exception {\n        TrackingService service = TrackingService.start();          // the same wiring as production\n        for (String request : List.of(\"track PX-1042\", \"track PX-2001\", \"redirect PX-1042\", \"history PX-2001\")) {\n            service.handle(request);                               // real code paths, test depots\n        }\n        service.stop();\n        System.exit(0);   // JDK 24 and 25 write the training data when the JVM exits\n    }\n}"},
  "kotlin": {"title": "TrainingMain.kt", "src": "/** Starts the service, sends it every kind of request real users send, then exits so the JVM writes the cache. */\nfun main() {\n    val service = TrackingService.start()                          // the same wiring as production\n    listOf(\"track PX-1042\", \"track PX-2001\", \"redirect PX-1042\", \"history PX-2001\")\n        .forEach { service.handle(it) }                            // real code paths, test depots\n    service.stop()\n    exitProcess(0)    // JDK 24 and 25 write the training data when the JVM exits\n}"},
  "note": "Both versions do the same three things: start the service exactly as production does, drive every kind of request through it, and exit. The cache doesn't care which language produced the bytecode. What differs is the class path and the entry point. A Kotlin service has `kotlin-stdlib` as a JAR on its class path, and it must be there, in the same order, in training and in production, or the cache is refused. The Kotlin entry point is the class `TrainingMainKt`, not `TrainingMain`. Kotlin 2.x compiles lambdas to `invokedynamic`, like Java, so the cache can resolve those call sites ahead of time in both languages. Before JDK 26 a training run has to exit to write its data, which is why both versions end the process; JDK 26 adds `jcmd <pid> AOT.end_recording` for servers that should keep running."
 },
 "worked": {
  "title": "Add the AOT cache to your build",
  "steps": [
   {"say": "Pin the JDK, and use the same build of it where you train and where you run. The cache records the exact JDK build and is refused by any other. Pick 25.0.4 or later, so a changed JAR can never run stale classes.",
    "code": "# the build machine and the server must print the same line\njava -version 2>&1 | head -1\n# openjdk version \"25.0.5\" ...   must be 25.0.4 or later",
    "lang": "bash"},
   {"say": "In the build, put the JAR at the path it will have on the server, then train and assemble in one step. Use the training entry point from the compare block, so the run goes through every kind of request and then exits.",
    "code": "cp build/libs/tracker.jar /srv/tracker.jar\njava -XX:AOTCacheOutput=/srv/app.aot -cp /srv/tracker.jar tracker.TrainingMain\n# ... AOTCache creation is complete: /srv/app.aot <size> bytes",
    "lang": "bash"},
   {"say": "Add a check to the build: start the real entry point with `-XX:AOTMode=on` and `-Xlog:aot`, and fail if the cache doesn't open. A wrong path, a different JDK or a changed JAR all make this check fail, loudly, before any user is affected.",
    "code": "java -XX:AOTMode=on -XX:AOTCache=/srv/app.aot -Xlog:aot -cp /srv/tracker.jar tracker.SmokeMain \\\n  | grep -q 'Opened AOT cache' || { echo 'AOT cache not used'; exit 1; }   # JDK 27+: AOTMode=required",
    "lang": "bash"},
   {"say": "Ship `tracker.jar` and `app.aot` together, as one unit, and start production without `AOTMode`. If someone later adds an agent the cache can't work with, the service starts slower instead of not at all.",
    "code": "java -XX:AOTCache=/srv/app.aot -cp /srv/tracker.jar tracker.Main",
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
   "Implement `RecordingClassLoader.loadClass`. A class loader is the object that finds a class's bytes and defines the class; this one writes down every class it defines. Outside the prefix, call `super.loadClass(name, resolve)`. Inside it, take `getClassLoadingLock(name)`, return `findLoadedClass(name)` if the class is already there, otherwise read the class file from `parent.getResourceAsStream`, call `defineClass`, and record the name.",
   "Implement `defined()` and run `RecordingClassLoaderTest`. Look at the first two tests: `Class.forName(name, false, loader)` defines one class, and `true` defines two, because only initialization runs `ZoneTable`'s static initializer, which touches `ZoneRules`.",
   "Implement `TrainingRun.classList` (a fresh loader, `Class.forName(entryClass, true, loader)`, `getMethod(\"handle\", String::class.java)`, one `invoke` per request) and `missing` (one line of set arithmetic).",
   "Run all the tests until the ten pass. Then read the fixtures in `src/test/java/workbench/startup/l02/fixtures/`: `ParcelDesk` is a tiny tracking service, and a training run with tracking requests only never loads `Redirect`."
  ],
  "hints": [
   "Kotlin's `synchronized(lock) { ... }` is inline, so `return c` inside it returns from `loadClass` itself.",
   "`parent.getResourceAsStream(path)?.use { it.readBytes() } ?: throw ClassNotFoundException(name)` reads the bytes and handles a missing file in one expression.",
   "The tests compare sets of class names, never counts. A count of all loaded classes changes between JDK builds; the classes your own loader defined don't."
  ],
  "done_when": "All ten tests in `RecordingClassLoaderTest` and `TrainingRunTest` pass."
 },
 "drill": {
  "title": "The commands from memory",
  "minutes": 4,
  "prompt": "Close this page. For `tracker.jar` with main class `tracker.Main`, write: (1) the two JDK 21 commands for a dynamic AppCDS archive, (2) the two JDK 25 commands for an AOT cache, (3) the build check that fails if the cache can't be used. Then add a comment saying which JDK 25 update you require, and why.",
  "answer": {
   "lang": "bash",
   "src": "# 1. JDK 21: dynamic AppCDS\njava -XX:ArchiveClassesAtExit=app.jsa -cp tracker.jar tracker.Main\njava -XX:SharedArchiveFile=app.jsa -cp tracker.jar tracker.Main\n\n# 2. JDK 25: AOT cache (training and assembly, then production)\njava -XX:AOTCacheOutput=app.aot -cp tracker.jar tracker.Main\njava -XX:AOTCache=app.aot -cp tracker.jar tracker.Main\n\n# 3. build check only: stop with an error if the cache can't be used (AOTMode=required on JDK 27+)\njava -XX:AOTMode=on -XX:AOTCache=app.aot -Xlog:aot -cp tracker.jar tracker.Main\n\n# Require 25.0.4+ (or 26.0.2+): earlier builds don't check the JAR (JDK-8377932)\n# and can run stale classes. Rebuild app.aot with every tracker.jar."
  }
 },
 "recap": [
  "CDS maps ready-made classes from a `.jsa` file. The default archive (JDK 12+) holds about 1,300 JDK classes and is on unless you pass `-Xshare:off`. It saves loading and verifying, not static initializers or JIT warm-up.",
  "AppCDS adds your classes: a dynamic archive with `-XX:ArchiveClassesAtExit` and `-XX:SharedArchiveFile` (JDK 13+), a static one with a class list and `-Xshare:dump`, or `-XX:+AutoCreateSharedArchive` (JDK 19+). On JDK 21 it halved a 300-class app's start-up CPU.",
  "The AOT cache is final in JDK 24 (JEP 483), with one-step `-XX:AOTCacheOutput` and method profiles in JDK 25 (JEPs 514 and 515). It works in three phases, training, assembly and production, and holds linked classes, resolved lambdas, heap objects and profiles, but only for the code the training ran.",
  "Require JDK 25.0.4+ or 26.0.2+ for the AOT cache, and rebuild it with every JAR: earlier builds could run stale classes (JDK-8377932).",
  "A cache the JVM can't use leaves no archive at all, not even the default one. Check it with `-Xlog:aot` and `-XX:AOTMode=on` in your build, never in production, and on JDK 25 train with the GC you run.",
  "The limit: even a perfect cache leaves a JVM that interprets first and compiles each hot method again in every new process, so a new copy is still slow for a while."
 ],
 "closing": "We started with a shopkeeper who keeps yesterday's shelves in the back room, and a note of what she used. The JDK's default archive is those shelves, AppCDS adds your own goods, and the AOT cache adds the notes: linked classes, resolved lambdas and, on JDK 25, the profiles. Each one fits only the exact stock it was made from.\n\nNow search the start command and build of one of your services for `SharedArchiveFile`, `AOTCache` or `Xshare`. Then start it once with `-Xlog:cds` or `-Xlog:aot`. Did the archive open?\n\nNext, we'll stop starting a JVM at all. What does GraalVM's native image gain by building the whole program ahead of time, and what can it no longer do?",
 "quiz": [
  {"q": "You add `-XX:SharedArchiveFile=app.jsa`, a dynamic archive, and run with `-Xlog:class+load` on JDK 21. Most JDK classes log `source: shared objects file`, but your own classes log `source: file:/srv/tracker.jar`. What does that tell you?",
   "options": ["The JVM rejected your dynamic archive and kept only the default one, so look for the warning that says why", "Everything works: your classes are always logged with their JAR", "Your classes are archived, but `-Xlog:class+load` can't see that", "The default archive failed, and your archive replaced it"],
   "answer": 0,
   "from": "boot-01",
   "why": "Archived classes log `source: shared objects file`, yours included. When JDK 21 rejects a dynamic archive (a changed JAR, a different class path), it warns and keeps the default archive underneath, so the JDK's classes stay shared and only yours come from the JAR. The warnings at the start of the output say which check failed."},
  {"q": "The runs that train your AOT cache only ever track parcels. In production, someone redirects a parcel. What happens on the redirect path?",
   "options": ["The redirect fails with `ClassNotFoundException`", "The JVM throws the whole cache away", "Its classes load the usual way, from the JAR, parsed and verified at that moment, so the first redirect is a little slower", "The JVM retrains the cache in the background"],
   "answer": 2,
   "why": "The cache holds what the training run loaded. Anything else loads the usual way, so the program stays correct, but those classes get no head start. That's why training should look like production traffic, which is what the lab's `missing` function measures."},
  {"q": "A service runs ZGC on JDK 25. Its AOT cache was trained with the default G1. What do you get?",
   "options": ["The full speed-up, because the cache doesn't depend on the GC", "Only the method profiles", "A crash at start-up", "Nothing: the JVM can't use the G1-trained cache under ZGC and runs with zero archived classes"],
   "answer": 3,
   "why": "On JDK 25.0.5 a G1-trained cache gave 0 archived classes under `-XX:+UseZGC`, and the JVM ran on without any archive. Training under ZGC helps only partly on JDK 25. JDK 26's JEP 516 stores the cache's heap objects in a form every GC can load."},
  {"q": "Your company adds a monitoring agent to every server through `JAVA_TOOL_OPTIONS`. Your service starts with `-XX:AOTMode=on -XX:AOTCache=app.aot`. What's the risk?",
   "options": ["None: `on` only means the cache is enabled", "If the agent's options don't work with the cache, the JVM stops at start-up instead of running without the cache", "The agent's classes get added to the cache", "The cache is rebuilt on every start"],
   "answer": 1,
   "why": "`on` (`required` from JDK 27) is a fail-fast setting: if the cache can't be used, the JVM stops with `Unable to use AOT cache.` The manual lists certain JVMTI options, which agents use, among the incompatible ones, and the JDK 27 manual warns about exactly this case. In production leave the mode at the default, `auto`, which runs without the cache instead."},
  {"q": "A JDK 21 service starts from a read-only disk, and each copy of it is thrown away when it stops. You want AppCDS with no code change. Which setup fits?",
   "options": ["`-XX:+AutoCreateSharedArchive -XX:SharedArchiveFile=/app/app.jsa` in the start command", "`-XX:AOTCacheOutput=app.aot` in the start command", "A dynamic archive made during the build with `-XX:ArchiveClassesAtExit`, shipped with the program and used with `-XX:SharedArchiveFile`", "`-Xshare:off`, for a predictable start-up"],
   "answer": 2,
   "why": "`AutoCreateSharedArchive` writes the file at the exit of a run that had none, which fails on a read-only disk and is lost with the copy anyway. Building the archive during the build gives every copy the same archive from its first start. `-XX:AOTCacheOutput` needs JDK 25."}
 ],
 "flashcards": [
  {"front": "What work does a CDS archive save at start-up?", "back": "Finding, parsing and verifying the archived classes: the JVM maps them ready-made from the `.jsa` file. Static initializers still run on first use."},
  {"front": "The two commands for a dynamic AppCDS archive (JDK 13+)?", "back": "`java -XX:ArchiveClassesAtExit=app.jsa -cp app.jar Main`, then `java -XX:SharedArchiveFile=app.jsa -cp app.jar Main`."},
  {"front": "The two commands for an AOT cache on JDK 25?", "back": "`java -XX:AOTCacheOutput=app.aot -cp app.jar Main` (training and assembly), then `java -XX:AOTCache=app.aot -cp app.jar Main`."},
  {"front": "Which JDK builds can run stale classes from an AOT cache after the JAR changed?", "back": "25.0.0 to 25.0.3 and 26.0.0 to 26.0.1 (JDK-8377932). Fixed in 25.0.4, 26.0.2 and 27."},
  {"front": "`-XX:AOTCache=` names a missing or stale file, in the default mode. What do you get?", "back": "The program runs with no archive at all, not even the default CDS archive, so it starts slower than with no flag."},
  {"front": "Where does `-XX:AOTMode=on` (JDK 27: `required`) belong?", "back": "In your build's checks, to fail fast when the cache doesn't open. Not in production, where an incompatible agent would stop the JVM from starting."},
  {"front": "From which JDK does the full AOT cache work with ZGC?", "back": "JDK 26 (JEP 516). On JDK 25 a G1-trained cache gives nothing under ZGC."}
 ],
 "terms": [
  {"term": "CDS", "plain": "Class data sharing: classes stored ready-made in a `.jsa` file that the JVM maps into memory at start-up."},
  {"term": "Default CDS archive", "plain": "The archive of about 1,300 JDK classes in `lib/server/classes.jsa`, used unless you pass `-Xshare:off`."},
  {"term": "AppCDS", "plain": "A CDS archive that also holds your application's classes."},
  {"term": "AOT cache", "plain": "Leyden's archive (JDK 24+): classes loaded and linked ahead of time, heap objects and, from JDK 25, method profiles."},
  {"term": "Training run", "plain": "A run of the program on a realistic workload that records what to put in the archive or cache."},
  {"term": "Assembly", "plain": "The step that turns the training notes into the AOT cache; the program itself doesn't run."},
  {"term": "AOTMode", "plain": "The flag that says how the JVM treats the cache: `auto` (the default), `record`, `create`, `on` (`required` on 27+) or `off`."}
 ],
 "explain_back": {
  "prompt": "A teammate wants to keep `app.aot` from the last build and reuse it, because training adds two minutes to every build. Explain why that's a bad idea, and what happens on JDK 25.0.3 compared with 25.0.5 when the JAR has changed.",
  "answer": "The cache belongs to one exact set of JARs, one JDK build and one set of flags. When the JAR changes, the old cache describes classes that no longer exist in that form. On 25.0.3 the JVM didn't check the application's JARs at all, so it would serve the old classes from the cache and run last build's code with no error. On 25.0.5 it notices the changed timestamp and size, warns, and runs without the cache, so the code is right but every start loses the gain, and the JDK's default archive with it. Either way the cache has to be built in the same step as the JAR and shipped with it. Two minutes are cheaper than either failure."
 },
 "deeper": {
  "minutes": 10,
  "body": "A few details that matter once you run this for real.\n\nThe static archive is dumped in interpreter-only mode, as if `-Xint` were set, so the output is the same bit for bit every time. For long class lists you can add `-Xmixed` to speed up the dump when you don't need that.\n\nYou can also take an archive from a running process: `jcmd <pid> VM.cds dynamic_dump app.jsa`, if the process was started with `-XX:+RecordDynamicDumpInfo`, or `jcmd <pid> VM.cds static_dump app.jsa`. That suits a service whose real warm-up needs real traffic. To try flags without editing start scripts, `JAVA_TOOL_OPTIONS=-XX:SharedArchiveFile=app.jsa` works, because the JVM reads that variable at start-up. In AOT cache file names, `%p` and `%t` are replaced by the process id and the start time, as in `-XX:AOTCacheOutput=tracker%p.aot`, so parallel training runs don't overwrite each other.\n\nOld articles sell CDS as a way for many JVMs on one machine to share memory. Count on start-up time instead. Modern JDKs map each archive at a different, random address by default and then patch its pointers, which writes to most of its pages and makes them private to the process. In one JDK 25 process, 11.5 MiB of the 14.4 MiB resident in the AOT cache's mapping were private.\n\nThe manual lags behind the code in one place: the JDK 25 page still says the cache holds \"Java classes and heap objects\" and that profiles will come in a future release, although JEP 515 shipped them in JDK 25.\n\nWhat's next, as of the JDK 28 development line: JEP 544 moves JIT compilation into the training run and ships the machine code in the cache, while the JIT can still recompile in production, and JEP 545 targets start-up and warm-up with ZGC. Neither is in a released JDK yet, so treat them as previews of where this is going, not as flags to use."
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
