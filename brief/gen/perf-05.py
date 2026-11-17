import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/performance/src"
P = "java/workbench/performance/l05"
K = "kotlin/workbench/performance/l05"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :performance:demo -Pmain=workbench.performance.l05."


def demo(name):
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{P}/{name}.java"),
            "run": DEMO + name, "file": f"{lab}/demo/{P}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
                    "run": DEMO + name + "Kt", "file": f"{lab}/demo/{K}/{name}.kt"}}


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


def box(cls, x, y, w, h, title, sub):
    return (f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/>'
            f'<text class="t" x="{x + w // 2}" y="{y + 21}" text-anchor="middle">{title}</text>'
            f'<text class="t-s t-m" x="{x + w // 2}" y="{y + 38}" text-anchor="middle">{sub}</text>\n')


FIG = ('<svg viewBox="0 0 680 240" role="img" aria-label="The JVM\'s events and your own events go into a recording, which keeps them in memory buffers and on disk within maxage and maxsize. A dump writes a .jfr file that the jfr tool, JDK Mission Control and RecordingFile read. RecordingStream reads the same events live inside the JVM.">\n'
       + box("box", 20, 40, 170, 50, "JVM events", "GC, JIT, locks, samples")
       + box("box-a", 20, 140, 170, 50, "your events", "workbench.StoreCall")
       + '<rect class="box-b" x="250" y="76" width="170" height="78" rx="8"/>'
         '<text class="t" x="335" y="100" text-anchor="middle">recording</text>'
         '<text class="t-s t-m" x="335" y="120" text-anchor="middle">buffers, then disk</text>'
         '<text class="t-s t-m" x="335" y="138" text-anchor="middle">maxage, maxsize</text>\n'
       + box("box", 490, 16, 170, 50, ".jfr file", "dump, filename, exit")
       + box("box-ok", 490, 92, 170, 50, "jfr, JMC", "RecordingFile API")
       + box("box-a", 490, 176, 170, 50, "RecordingStream", "live, same JVM")
       + '<line class="ln-a" x1="190" y1="65" x2="248" y2="100" marker-end="url(#arr)"/>\n'
         '<line class="ln-a" x1="190" y1="165" x2="248" y2="130" marker-end="url(#arr)"/>\n'
         '<line class="ln-a" x1="420" y1="96" x2="488" y2="46" marker-end="url(#arr)"/>\n'
         '<line class="ln-a" x1="575" y1="66" x2="575" y2="90" marker-end="url(#arr)"/>\n'
         '<line class="ln-a" x1="420" y1="138" x2="488" y2="198" marker-end="url(#arr)"/>\n'
         '</svg>')

EVENT_J = """@Name("workbench.StoreCall")
@Label("Store Call")
@Category({"Workbench", "Reports"})
public class StoreCallEvent extends Event {
    @Label("Shelf") String shelf;
    @Label("Words") long words;
    @Label("Found") boolean found;
}

StoreCallEvent event = new StoreCallEvent();
event.begin();                                  // 1. start the clock
String text = store.fetch(shelf, title);
event.end();                                    // 2. stop it
if (event.shouldCommit()) {                     // 3. false if no recording wants it
    event.shelf = shelf;
    event.words = text == null ? 0 : countWords(text);
    event.found = text != null;
    event.commit();                             // 4. write it, with a stack trace
}"""
EVENT_K = """@Name("workbench.StoreCall")
@Label("Store Call")
@Category("Workbench", "Reports")
class KStoreCallEvent : Event() {
    @Label("Shelf") var shelf: String? = null
    @Label("Words") var words = 0L
    @Label("Found") var found = false
}

val event = KStoreCallEvent()
event.begin()                                   // 1. start the clock
val text = store.fetch(shelf, title)
event.end()                                     // 2. stop it
if (event.shouldCommit()) {                     // 3. false if no recording wants it
    event.shelf = shelf
    event.words = if (text == null) 0 else countWords(text)
    event.found = text != null
    event.commit()                              // 4. write it, with a stack trace
}"""

STREAM_J = """try (RecordingStream rs = new RecordingStream()) {
    rs.enable("workbench.StoreCall").withThreshold(Duration.ofMillis(35));   // only the slow ones
    rs.enable("jdk.GarbageCollection");
    rs.onEvent("workbench.StoreCall", e -> System.out.printf("slow store call: %s, %d ms%n",
            e.getString("shelf"), e.getDuration().toMillis()));
    rs.onEvent("jdk.GarbageCollection", e -> System.out.printf("GC: %s, %.1f ms pause total%n",
            e.getString("name"), e.getDuration("sumOfPauses").toNanos() / 1e6));
    rs.startAsync();                     // events arrive on a background thread
    ReportWorkload.run(3);
}"""
STREAM_K = """RecordingStream().use { rs ->
    rs.enable("workbench.StoreCall").withThreshold(Duration.ofMillis(35))   // only the slow ones
    rs.enable("jdk.GarbageCollection")
    rs.onEvent("workbench.StoreCall") { e ->
        println("slow store call: ${e.getString("shelf")}, ${e.duration.toMillis()} ms")
    }
    rs.onEvent("jdk.GarbageCollection") { e ->
        println("GC: %s, %.1f ms pause total".format(e.getString("name"), e.getDuration("sumOfPauses").toNanos() / 1e6))
    }
    rs.startAsync()                      // events arrive on a background thread
    kRunWorkload(3)
}"""

OPENING = """Back in the restaurant, a long night is over. A customer says the soup took forty minutes, and the cook remembers making it in six. Both can be true: the bowl may have waited for the only waiter, or for the kitchen to finish washing up. To settle it, you'd want one log of everything the kitchen did, every order, wait and wash-up, on one clock. It must be cheap enough to keep every night, because nobody knows which night will go wrong.

The JVM, the program that runs your Java and Kotlin, keeps a log like that. It's already in your JDK, and it's called JDK Flight Recorder.

The easy trap is the tool we all reach for first: a timer and a log line around the slow call. It answers one question about one call, on a clock of its own. Lesson 4 made one hot spot cheaper once we knew where it was. Now we need to find where a running program spends its time. In this lesson, we'll record the report service, question the recording, add our own notes to it and watch events live. Before we start, make a guess, and keep it in mind."""

S1 = """Start with the hand-made answer. The report service from the earlier lessons fetches each document from a document store, another program that keeps the documents and answers over the network. Some fetches are slow, so we wrap one in a timer and log `fetch took 46 ms`. That's one number for one call. It can't say whether every thread was paused for a garbage collection at that moment. (The garbage collector, or GC, is the part of the JVM that frees memory nobody uses.) Nor can it say whether the thread waited for a lock, a guard that lets one thread at a time into a piece of code, or whether something allocated a lot of memory that second.

**JDK Flight Recorder (JFR)** is a recorder built into HotSpot, the JVM in every OpenJDK build. It writes **events**: small records with a start time, often a duration, the thread, and usually a stack trace, the chain of method calls that led there. HotSpot has events for GC pauses, JIT compilations (the JVM turning busy methods into machine code, as lessons 1 and 2 showed), waits for locks, file and network reads, and samples of running threads and of allocation. Your code can add events of its own. All of them go into one timeline, on one clock. That's the kitchen's log for the whole night.

A **recording** is one session of that log, with its settings and limits. It keeps events in memory buffers and moves them to disk in chunks. Picture a log book that tears out its oldest pages when it's full: `maxage` says how far back to keep, `maxsize` how many bytes. Set neither, and the JVM keeps 250 MB. You can start a recording when the JVM starts, or on a JVM that's already running:

```bash
java -XX:StartFlightRecording:filename=rec.jfr,settings=profile -jar app.jar

jcmd <pid> JFR.start name=reports settings=profile     # on a JVM that's already running
jcmd <pid> JFR.dump name=reports filename=reports.jfr  # copy what it has so far to a file
jcmd <pid> JFR.stop name=reports
```

`jcmd` is a tool in the JDK that sends commands to a running JVM, and `<pid>` is the process id, the number the operating system gives each running program. On JDK 25, the report service answered the first command like this:

```text
Started recording 1. No limit specified, using maxsize=250MB as default.

Use jcmd 30725 JFR.dump name=reports filename=FILEPATH to copy recording data to file.
```

A dump copies the pages written so far and stops nothing. That's why a recording that's always on pays off: when something goes wrong, the last hour is already in the book.

`settings` picks a configuration file. `default.jfc` describes itself as "safe for continuous use in production environments, typically less than 1 % overhead". `profile.jfc` says "typically around 2 % overhead" and records more. In JDK 25, `default` samples running threads every 20 ms, takes up to 150 allocation samples a second and records lock waits of 20 ms or more. `profile` samples every 10 ms, takes 300 allocation samples a second and records lock waits from 10 ms.

The first question to ask any recording is what's in it. `jfr summary`, from the JDK's `jfr` tool, lists every event type with a count. For the Try it below, four threads, lines of work that run side by side inside the program, wrote reports for 4 seconds under `profile`. Part of the summary:

```text
 Event Type                              Count  Size (bytes)
=============================================================
 jdk.GCPhaseParallel                      1951         50576
 workbench.StoreCall                      1361         35305
 jdk.ObjectAllocationSample               1207         16978
 jdk.ThreadSleep                           560         10078
 ...
 jdk.ExecutionSample                        40           400
 jdk.JavaMonitorEnter                       29           667
```

`workbench.StoreCall` is ours, one event per call to the document store, and section 3 builds it. Everything else is the JVM's, and only the garbage collector's paperwork outnumbers us. Notice how few execution samples there are. The threads spent most of the time asleep, waiting for the store, and the sampler only counts threads that are running Java code. Keep that 40 in mind for the end of the lesson.

**A cheap recording that's always on is evidence you already have. Dump it instead of restarting.**

The summary says what the log holds. Next, we'll ask it a question."""

S2 = """Three subcommands of the `jfr` tool cover most days. You've met `jfr summary`. `jfr view <view> <file>` prints a ready-made report: views arrived in JDK 21, and `jfr help view` lists the dozens there are now. `jfr print` prints events one by one.

Three views answer the questions from the opening. Did threads wait for each other? `contention-by-site` groups the waits to enter a `synchronized` block, the lock Java takes with the `synchronized` keyword, by where they happened:

```text
                                 Contention by Site

StackTrace                                                     Count    Avg.    Max.
-------------------------------------------------------------- ----- ------- -------
workbench.performance.l05.ReportWorkload.reportLoop(int, long)    28 15.5 ms 34.0 ms
jdk.jfr.internal.PlatformRecorder.periodicTask()                   1 11.0 ms 11.0 ms
```

Twenty-eight waits at the shared archive lock, 15.5 ms on average: about the 15 ms each writer holds it. The second line is JFR's own housekeeping thread, which once got stuck behind a lock of its own.

Who allocates? `allocation-by-site` adds up the allocation samples by the method that did the allocating:

```text
Method                                                               Allocation Pressure
-------------------------------------------------------------------- -------------------
java.util.Arrays.copyOfRange(byte[], int, int)                                    36.56%
java.lang.StringLatin1.newString(byte[], int, int)                                33.31%
jdk.internal.misc.Unsafe.allocateUninitializedArray(Class, int)                    9.76%
java.util.ArrayList.grow(int)                                                      9.51%
java.lang.String.split(char, int, boolean)                                         6.27%
```

Every line is JDK code, and every one is the inside of `String.split`, which our `countWords` calls 2,000 times per document. A view names the method that allocated, not the line of yours that asked for it. Lesson 7 walks down the stack traces to find that line.

Did the JVM stop every thread? `gc-pauses` gives the count, the total and the longest pause. And lesson 2 promised a view for the JIT's lost bets, `deoptimizations-by-reason`:

```text
Reason                                                                     Count
------------------------------------------------------ -------------------------
unstable_if                                                                    7
bimorphic_or_optimized_type_check                                              4
class_check                                                                    4
intrinsic_or_type_checked_inlining                                             1
```

Sixteen in a program that ran 4 seconds is the burst at start-up that lesson 2 described. A steady stream hours after start is the thing to worry about.

Each view is a query over events, and `jfr view --verbose` shows the query. Pass the name of an event type as the view, such as `jfr view workbench.StoreCall rec.jfr`, and you get a table of those events. On a running JVM, `jcmd <pid> JFR.view hot-methods` prints a view without writing a file. `jfr print --events workbench.StoreCall --stack-depth 2 rec.jfr` prints events one at a time with every field; add `--json` for a script.

**JDK Mission Control (JMC)** is the desktop app for the same files: timelines, flame graphs of the samples (lesson 6 explains those) and an automatic analysis. It's developed in the `openjdk/jmc` project and downloaded separately, from builds that several vendors publish. The `jfr` tool is enough for everything in this lesson, and it's already in your JDK.

**Read `jfr summary` first, then ask one question per view.**

Before you send a recording to anyone, look at what else it holds. The demo's file has 169 `jdk.InitialEnvironmentVariable` events and the full command line. A recording remembers more than you told it, and environment variables are where programs often keep passwords. JDK 27 adds redaction inside the JVM (JEP 536, `-XX:FlightRecorderOptions:redact-argument=...`). On older JDKs, check the file first, or share the views instead of the file.

The figure shows where all these events go. So far they've been the JVM's, apart from one type we haven't explained yet."""

S3 = """An event of your own is a class that extends `jdk.jfr.Event`. Its fields are the data, and annotations give it a stable name and labels for the tools. Here's the demo's event for one call to the document store. The demo's store is fake and only sleeps, so the code around the call is shown the way a real service would write it:

""" + pair(EVENT_J, EVENT_K) + """

Read it from the top. `@Name` is the name that recordings and tools use to find the event. `@Label` and `@Category` are what JMC and `jfr view` display. `begin()` starts the event's clock and `end()` stops it, so its duration covers the store call. `shouldCommit()` returns `true` only if some recording has this event switched on and the duration passes that recording's **threshold**, the shortest duration it keeps. Only then do we fill in the fields and `commit()`, which writes the event with the thread and a stack trace taken at that moment.

The `shouldCommit()` check matters because Java works out each field's value before the assignment, and `countWords` isn't free. When no recording wants the event, the check skips that work, and the event costs almost nothing. In the kitchen, it's a note the cook writes only when somebody is keeping the log.

Kotlin needs nothing special. JFR records the field behind each Kotlin property, and a Java annotation such as `@Label` on a property lands on that field.

Compare it with the log line from section 1. The event has fields you can filter, instead of text you have to parse. A recording can also keep only the slow ones: `+workbench.StoreCall#threshold=30ms` on the command line keeps calls of 30 ms or more. The `+` is needed because your event isn't listed in the `.jfc` file. Leave it out, and JDK 25 warns `The .jfc option/setting 'workbench.StoreCall#threshold' doesn't exist.` and ignores it. Above all, the event sits on the same timeline as the GC pauses and lock waits, with the same thread names. `jfr view workbench.StoreCall` showed the demo's events like this (trimmed to two rows):

```text
Start Time Duration Event Thread Stack Trace                                                     Shelf   Words Found
---------- -------- ------------ --------------------------------------------------------------- ------- ----- -----
07:47:36    18.3 ms report-2     workbench.performance.l05.ReportWorkload.callStore(String, int) shelf-1   201  true
07:47:36    46.6 ms report-3     workbench.performance.l05.ReportWorkload.callStore(String, int) shelf-7   207  true
```

Reading events back in code is short. `RecordingFile.readAllEvents(path)` returns every event in a file. Each `RecordedEvent` has `getEventType().getName()`, `getDuration()`, `getString("shelf")`, `getBoolean("found")` and friends. That's the lab.

**Fill an event's fields inside `shouldCommit()`. When nobody records, the event costs almost nothing.**

Check yourself: your event sits in a method that runs 50,000 times a second, and no recording has it switched on. What does `shouldCommit()` return, and what does it save you? (It returns `false`, and it saves you the work of computing the fields. `commit()` would have written nothing anyway.)

A recording answers questions after the fact. Sometimes you want the answers while the program is still running."""

S4 = """`jdk.jfr.consumer.RecordingStream`, in the JDK since version 14, hands the same events to your own code while the JVM runs:

""" + pair(STREAM_J, STREAM_K) + """

Events reach the callbacks in batches, about once a second, on a background thread. That suits turning JVM events into numbers for a dashboard, such as GC pause time per minute. It's not a hook into the busy path of your code. One run of `StreamingDemo` printed lines like these:

```text
slow store call: shelf-1, 46 ms
GC: G1New, 16.3 ms pause total
slow store call: shelf-7, 155 ms
slow store call: shelf-9, 130 ms
```

Shelf 7 is slow on purpose. The others were slow because the machine was: more than 30 other busy programs shared its four cores that day, so a 12 ms sleep often lasted much longer. A stream can't tell which slowness you meant. That's one more reason to have the CPU and GC events on the same clock as your own.

JDK 25 added three profiling features to JFR, and all of these ran here on JDK 25.

- Method timing and tracing (JEP 520) counts and times chosen methods with no change to the code. `-XX:StartFlightRecording:method-timing=workbench.performance.l05.ReportWorkload::countWords,report-on-exit=method-timing` printed a table as the JVM exited: 2,024,000 calls of `countWords`, 0.001160 ms on average, 88.6 ms at most. That maximum is a call that waited out a GC pause or a busy CPU; the average is the cost of the call. The filter can also name a whole class or an annotation.
- CPU-time sampling (JEP 509), experimental and only on Linux, samples each thread by the CPU time it uses. Switch on `jdk.CPUTimeSample` (for example `jdk.CPUTimeSample#enabled=true,jdk.CPUTimeSample#throttle=10ms`) and read it with `jfr view cpu-time-hot-methods`. On the report workload it took 64 samples in 4 seconds, a quarter of them in `String.split`.
- Cooperative sampling (JEP 518) changes how the JVM takes execution samples inside. There's nothing to configure.

`report-on-exit=<view>` prints any view when the JVM exits, so a test run can leave a report in its log. JDK 21 doesn't know the option and says so.

Here's where today's tool stops. JFR's classic sampler took 40 execution samples in 4 seconds of a busy program. That's enough to spot a method that takes most of the time, and far too few to see what that method does inside. Lesson 6 brings in a profiler that takes thousands."""

L = {
 "id": "perf-05",
 "title": "JDK Flight Recorder and Mission Control",
 "minutes": 38,
 "goal": "By the end you can start and dump a JFR recording on a running JVM, answer questions with `jfr summary`, `jfr view` and `jfr print`, and add your own events that land on the same timeline as the JVM's garbage collections and lock waits.",
 "opening": OPENING,
 "warmup": {
  "q": "The report service's log says \"fetch took 46 ms\" for a few slow requests. What can a JFR recording of the same minutes tell you that the log line can't?",
  "options": [
   "Nothing more: the log line already has the duration",
   "Whether a garbage-collection pause, a wait for a lock or a burst of allocation happened at the same moment, on the same clock",
   "What the document store did inside its own program",
   "Which line of the document store's code was slow"
  ],
  "answer": 1,
  "why": "JFR records the JVM's own events, such as garbage-collection pauses, waits for locks, sampled allocations and sampled stacks, each with a timestamp and a thread, next to any events you add. So you can see what else happened while the slow call ran. It can't look inside another program: the document store would need a recording of its own."
 },
 "sections": [
  {
   "h": "JFR records what the JVM did, on one clock, cheap enough to leave on",
   "body": S1,
   "try": {
    "title": "Record the busy report service",
    "minutes": 4,
    "steps": [
     "Read `JfrDemo` and skim `ReportWorkload` next to it. Four threads each count the words in 2,000 short lines, ask a fake document store for a document (it sleeps a few milliseconds, longer for `shelf-7`), and on every tenth document hold a shared archive lock for 15 ms.",
     "Predict which event type will have the highest count, and roughly how many execution samples 4 seconds will give.",
     "Run it from `labs/`. The demo starts a second JVM with `-XX:StartFlightRecording` and prints the path of the `.jfr` file.",
     "Run `jfr summary` on that file (the demo prints the command)."
    ],
    "code": demo("JfrDemo"),
    "expect": "The JVM prints its \"Started recording\" lines, then the demo prints the file path; the file was about 440 KB here. In the run above, `jfr summary` counted 1,951 `jdk.GCPhaseParallel`, 1,361 `workbench.StoreCall`, 1,207 `jdk.ObjectAllocationSample` and 560 `jdk.ThreadSleep` events, but only 40 `jdk.ExecutionSample`, because the threads spend most of their time asleep. Your counts will differ from run to run."
   },
   "refs": [
    {"title": "The java command, JDK 25 (-XX:StartFlightRecording)", "url": "https://docs.oracle.com/en/java/javase/25/docs/specs/man/java.html", "kind": "docs"}
   ]
  },
  {
   "h": "Asking the recording questions with jfr view and jfr print",
   "body": S2,
   "figure": {"svg": FIG, "caption": "Events go into a recording. A dump makes a .jfr file for the jfr tool, JMC or RecordingFile; RecordingStream reads the same events live."},
   "try": {
    "title": "Answer three questions from one file",
    "minutes": 5,
    "steps": [
     "Using the file from the last Try it: where do threads wait for locks, and for how long at most? Run `jfr view contention-by-site <file>`.",
     "Which methods allocate the most? Run `jfr view allocation-by-site <file>`. Which line of `ReportWorkload` calls all of them?",
     "Which shelf has slow store calls? Run `jfr view workbench.StoreCall <file>` and look at the Duration column, then `jfr print --events workbench.StoreCall --stack-depth 2 <file> | head -20`."
    ],
    "code": {"lang": "bash", "title": "terminal (from labs/)", "src": "jfr view contention-by-site performance/build/perf05.jfr\njfr view allocation-by-site performance/build/perf05.jfr\njfr view workbench.StoreCall performance/build/perf05.jfr\njfr print --events workbench.StoreCall --stack-depth 2 performance/build/perf05.jfr | head -20", "run": ""},
    "expect": "Contention shows `reportLoop` with a few dozen waits of about 15 ms (28 in the run above, the longest 34 ms). Allocation is all `String.split` and its helpers, which `countWords` calls. In the table, `shelf-7` calls take up to about 40 ms; on a busy machine some other shelves stretch past their 12 ms too. `jfr print` shows each event's fields and the two frames that called it, with line numbers."
   },
   "refs": [
    {"title": "The jfr command, JDK 25", "url": "https://docs.oracle.com/en/java/javase/25/docs/specs/man/jfr.html", "kind": "docs"}
   ]
  },
  {
   "h": "Your own events add the service's notes to the same log",
   "body": S3,
   "try": {
    "title": "Keep only the slow calls",
    "minutes": 4,
    "steps": [
     "In `JfrDemo.java`, change the recording option to `\"-XX:StartFlightRecording:filename=\" + file + \",settings=profile,+workbench.StoreCall#threshold=30ms\"` (note the `+`).",
     "Predict: out of about 1,300 store calls, roughly how many will be recorded now, and from which shelves?",
     "Run the demo again, then `jfr summary` and `jfr view workbench.StoreCall` on the new file."
    ],
    "expect": "Only a few dozen `workbench.StoreCall` events remain, all 30 ms or longer: 50 in one run here, 33 of them from `shelf-7`, whose fake store sleeps up to 40 ms. The other 17 came from shelves that sleep at most 12 ms; the busy machine stretched those sleeps past 30 ms, which is a finding of its own. The JVM's own events are unchanged, because the threshold is a setting of the recording, not of your code."
   }
  },
  {
   "h": "Watching events live, and what JDK 25 added",
   "body": S4,
   "try": {
    "title": "Watch slow calls and GCs as they happen",
    "minutes": 4,
    "steps": [
     "Run `StreamingDemo` and watch the output for 3 seconds.",
     "Predict before running the Kotlin twin: which shelves will show up, and how slow?",
     "On JDK 25 only: run the workload with method timing, using the command in the note below, and compare the table with your guess for one `countWords` call."
    ],
    "code": demo("StreamingDemo"),
    "expect": "Lines such as `slow store call: shelf-7, 39 ms` arrive in batches, mixed with lines such as `GC: G1New, 16.3 ms pause total`. `shelf-7` shows up most, between 35 and 50 ms; other shelves appear when the machine is busy. For the JDK 25 step, run `java '-XX:StartFlightRecording:method-timing=workbench.performance.l05.ReportWorkload::countWords,report-on-exit=method-timing' -cp performance/build/classes/java/demo workbench.performance.l05.JfrDemo child` from `labs/` after the Gradle run has compiled the demos. It ends with a Method Timing table for `countWords`: about two million calls, around a microsecond each."
   }
  }
 ],
 "compare": {
  "title": "A custom JFR event in Java and Kotlin",
  "java": {"title": "StoreCallEvent.java", "src": EVENT_J},
  "kotlin": {"title": "JfrDemo.kt", "src": EVENT_K},
  "note": "The same event, recorded the same way. A Kotlin `var` compiles to a private field plus a getter and a setter, and JFR records the field. A Java annotation such as `@Label` placed on a Kotlin property goes to that field, because `FIELD` is the only one of its targets a property can use. `@Category` takes an array, written `{\"Workbench\", \"Reports\"}` in Java and as plain arguments in Kotlin. Both versions produce the same event type, `workbench.StoreCall`, so the same `jfr view` works on either recording. The Kotlin field for the shelf is a nullable `String?`, because an event is created empty and filled in later."
 },
 "worked": {
  "title": "Explain a slow evening with one dump",
  "steps": [
   {"say": "The report service's slowest requests got slower at 14:02, and it runs a continuous recording. Check which recordings exist, then dump the last 10 minutes without restarting anything.", "code": "jcmd 4711 JFR.check\njcmd 4711 JFR.dump name=1 maxage=10m filename=/tmp/reports-1402.jfr", "lang": "bash"},
   {"say": "First question: did the JVM stop every thread? `gc-pauses` answers in one screen. If the longest pause is a few milliseconds, the GC isn't your 200 ms.", "code": "jfr view gc-pauses /tmp/reports-1402.jfr", "lang": "bash"},
   {"say": "Second question: did threads wait for each other? `contention-by-site` lists the `synchronized` blocks that threads waited to enter, with counts and the longest wait. A 180 ms maximum on the archive lock would explain a lot.", "code": "jfr view contention-by-site /tmp/reports-1402.jfr", "lang": "bash"},
   {"say": "Third question: which calls were slow, and on which shelf? Your own event answers, on the same clock. Self-check: if a slow store call and a long lock wait share a thread name and a timestamp, which one do you look at first? (The lock wait: it happens inside your own process, and the store call may only look slow because its thread was waiting.)", "code": "jfr print --events workbench.StoreCall /tmp/reports-1402.jfr | grep -B3 -A6 'duration = [0-9][0-9][0-9] ms'", "lang": "bash"},
   {"say": "Write the finding down with the evidence, and attach the views, not the file: the file holds environment variables and the command line.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Record your own event and read it back",
  "minutes": 14,
  "files": [f"{lab}/main/{P}/LookupEvent.java", f"{lab}/main/{P}/Librarian.java", f"{lab}/main/{P}/LookupReport.java"],
  "run": "./gradlew :performance:test --tests 'workbench.performance.l05.*'",
  "steps": [
   "Open `DocumentStore`, the given interface for the program that keeps the documents, and `Librarian`, the report service's class that asks it for a document by shelf and title. Run the tests. Five of the six fail. Each one starts a real JFR recording, makes six lookups, writes a real `.jfr` file and reads it back. The one that passes checks that `lookup` still returns the store's answer.",
   "Make `LookupEvent` an event named `workbench.Lookup`, with a label, a category that includes `Reports`, and three labelled fields: `shelf`, `title` and `found`.",
   "In `Librarian.lookup`, record one event per call. Its duration must cover the store call: the test's `basement` shelf takes 100 ms to answer, and a test checks for it.",
   "Write `LookupReport.missingByShelf` and `LookupReport.slowestShelf` with `RecordingFile`. The file also holds `jdk.ThreadSleep` events, so filter by event name.",
   "Run the tests until all six pass."
  ],
  "hints": [
   "The annotations are `@Name`, `@Label`, `@Category` and `@Description` from `jdk.jfr`. The fields can stay package-private.",
   "Call `begin()` right before `store.fetch(...)` and `end()` right after it. Fill the fields and `commit()` inside `if (event.shouldCommit())`. `found` is `text != null`.",
   "`RecordingFile.readAllEvents(path)` returns a `List<RecordedEvent>`. Filter on `e.getEventType().getName()`, then use `e.getBoolean(\"found\")`, `e.getString(\"shelf\")` and `e.getDuration()`.",
   "`Map.merge(shelf, 1L, Long::sum)` counts per key in one line. A `TreeMap` keeps the result sorted, which makes failures easier to read."
  ],
  "done_when": "All six tests in `FlightRecorderTest` pass."
 },
 "drill": {
  "title": "From memory: event, recording, query",
  "minutes": 5,
  "prompt": "Close this page. Write (1) an event class `ReportWriteEvent` named `workbench.ReportWrite` with a `title` field, (2) the code that times writing one report with it, and (3) the two shell commands that start a recording on JVM 4711 and later write it to `reports.jfr`. Then check against the answer.",
  "answer": {"lang": "java", "src": "@Name(\"workbench.ReportWrite\")\n@Label(\"Report Write\")\n@Category({\"Workbench\", \"Reports\"})\nclass ReportWriteEvent extends Event {\n    @Label(\"Title\") String title;\n}\n\nReportWriteEvent event = new ReportWriteEvent();\nevent.begin();\nwriter.write(report);\nevent.end();\nif (event.shouldCommit()) {\n    event.title = report.title();\n    event.commit();\n}\n\n// jcmd 4711 JFR.start name=reports settings=profile\n// jcmd 4711 JFR.dump name=reports filename=reports.jfr",
             "alt": {"lang": "kotlin", "src": "@Name(\"workbench.ReportWrite\")\n@Label(\"Report Write\")\n@Category(\"Workbench\", \"Reports\")\nclass ReportWriteEvent : Event() {\n    @Label(\"Title\") var title: String? = null\n}\n\nval event = ReportWriteEvent()\nevent.begin()\nwriter.write(report)\nevent.end()\nif (event.shouldCommit()) {\n    event.title = report.title\n    event.commit()\n}\n\n// jcmd 4711 JFR.start name=reports settings=profile\n// jcmd 4711 JFR.dump name=reports filename=reports.jfr"}}
 },
 "recap": [
  "JFR is built into HotSpot and records timestamped events (GC, JIT, locks, CPU and allocation samples, I/O) on one timeline. Start it with `-XX:StartFlightRecording` or `jcmd <pid> JFR.start`, and copy data out with `JFR.dump`, which stops nothing.",
  "`default.jfc` is meant to stay on (under 1% overhead, by its own description); `profile.jfc` samples twice as often and keeps shorter lock waits, so use it for short investigations. Set `maxage` or `maxsize`, or the JVM keeps 250 MB.",
  "`jfr summary` shows what a file holds, `jfr view` (JDK 21+) prints reports such as `contention-by-site`, `allocation-by-site`, `gc-pauses` and `deoptimizations-by-reason`, and `jfr print` shows single events.",
  "Your own events extend `jdk.jfr.Event`: `begin`, `end`, `shouldCommit`, `commit`. They share the timeline with the JVM's events. `RecordingFile` reads them back; `RecordingStream` delivers them live.",
  "JDK 25 adds method timing (JEP 520), experimental CPU-time sampling on Linux (JEP 509) and `report-on-exit`. Recordings hold environment variables and the command line; JDK 27 can redact them.",
  "The limit: JFR's classic sampler took 40 stack samples in 4 seconds here, and its views name the JDK method rather than your line. Seeing where the time goes inside a method takes a profiler with many more samples (lesson 6)."
 ],
 "closing": """We started with a soup that took forty minutes in the customer's story and six in the cook's. JFR keeps the log that settles it: the JVM's events and ours, on one clock, cheap enough to leave on all night, and dumped without stopping anything.

Now look in your own code for a log line that prints a duration, such as `took {} ms`. Each one could be an event with fields and a threshold, sitting on the same timeline as the GC.

Next, we'll take thousands of samples instead of forty. How does a sampling profiler find where the time goes, and why does it draw its answer as a flame graph?""",
 "quiz": [
  {"q": "The report service is misbehaving right now and you can't restart it. How do you get JFR data from the last few minutes?",
   "options": ["Restart it with `-XX:StartFlightRecording`", "If a recording is running, `jcmd <pid> JFR.dump name=1 filename=now.jfr`; otherwise `jcmd <pid> JFR.start` and wait", "Read the GC log", "Attach a debugger and suspend every thread"],
   "answer": 1,
   "why": "`JFR.dump` copies a running recording to a file without stopping the JVM, which is why a recording that's always on pays off. Without one, `JFR.start` begins recording now, so you only see what happens next. A restart throws away the very minutes you wanted."},
  {"q": "Which `jfr view` tells you where threads waited to enter a `synchronized` block, and for how long?",
   "options": ["`hot-methods`", "`allocation-by-site`", "`contention-by-site`", "`gc-pauses`"],
   "answer": 2,
   "why": "`contention-by-site` groups `jdk.JavaMonitorEnter` events by stack, with the count, the average and the longest wait. `hot-methods` shows where threads ran, not where they waited."},
  {"q": "Your event has `@Name(\"workbench.Lookup\")`, but `jfr summary` of a recording shows none of them, although the code calls `commit()`. What's the most likely cause?",
   "options": ["Your own events are only recorded with `settings=profile`", "Events with a `String` field can't be recorded", "`commit()` needs a call to `flush()` afterwards", "The recording's settings switch the event off, or give it a threshold longer than the calls take"],
   "answer": 3,
   "why": "Your own event types are switched on by default with no threshold, so even a bare `new Recording()` keeps them, and any `.jfc` file works. When they're missing although `commit()` runs, the settings turned them off (`+workbench.Lookup#enabled=false`) or set a threshold the calls never reach. There's no flush call to make."},
  {"q": "On JDK 25 you need call counts and timings for one method of the report service. You may restart it with a new flag, but you can't change its code. What fits best?",
   "options": ["`-XX:StartFlightRecording:method-timing=com.example.Reports::render,report-on-exit=method-timing`", "`-XX:+PrintCompilation`", "A JMH benchmark of the method", "`jcmd <pid> Thread.print` every second"],
   "answer": 0,
   "why": "JEP 520 (JDK 25) counts and times the methods a filter matches, and `report-on-exit` prints the table when the JVM exits. PrintCompilation shows compiles, not timings. JMH measures the method on its own, outside the running service."},
  {"q": "From lesson 2: hours after start-up, a service still keeps throwing away C2 code because a type check fails. Which JFR view helps you confirm it?",
   "options": ["`jfr view gc-pauses`", "`jfr view allocation-by-site`", "`jfr view deoptimizations-by-reason`", "`jfr view hot-methods`"],
   "answer": 2,
   "why": "JFR records a `jdk.Deoptimization` event each time compiled code hits an uncommon trap, and this view groups them by reason, such as `class_check` or `unstable_if`. The demo showed 16 in its first 4 seconds, the normal start-up burst. A count that keeps growing hours later is the signal lesson 2 described.",
   "from": "perf-02"}
 ],
 "flashcards": [
  {"front": "How do you start a JFR recording on a JVM that's already running, and get the data out?", "back": "`jcmd <pid> JFR.start name=x settings=profile`, and later `jcmd <pid> JFR.dump name=x filename=x.jfr`. The dump stops nothing."},
  {"front": "`default.jfc` or `profile.jfc` for a recording that stays on all the time?", "back": "`default.jfc` (\"typically less than 1 % overhead\"). `profile.jfc` samples twice as often; use it for short investigations."},
  {"front": "What's the first command to run on a `.jfr` file you've never seen?", "back": "`jfr summary file.jfr`: every event type with its count and size. Then ask one question per `jfr view`."},
  {"front": "What does `event.shouldCommit()` tell you?", "back": "Whether some recording has this event switched on and the duration passes its threshold. If it's false, skip filling in the fields."},
  {"front": "How do you read events from a .jfr file in Java?", "back": "`RecordingFile.readAllEvents(path)`, then filter on `e.getEventType().getName()` and read fields with `getString`, `getLong`, `getBoolean`, `getDuration`."},
  {"front": "Your event's threshold on the command line is ignored with a warning that the setting doesn't exist. What's missing?", "back": "The `+`: `+workbench.StoreCall#threshold=30ms`. Your event isn't in the `.jfc` file, so the setting must be added."},
  {"front": "Why check a .jfr file before sharing it?", "back": "It holds environment variables and the command line, where secrets often live. JDK 27 adds redaction (JEP 536)."}
 ],
 "terms": [
  {"term": "JFR (JDK Flight Recorder)", "plain": "A recorder built into HotSpot that writes timestamped events about the JVM and your code."},
  {"term": "Event", "plain": "One timestamped record, such as a GC pause, a lock wait or one call to the document store."},
  {"term": "Recording", "plain": "A running JFR session with its settings and limits, which you dump to a .jfr file."},
  {"term": "Execution sample", "plain": "A snapshot of a running thread's stack, taken every 10 or 20 ms, used to find busy methods."},
  {"term": "Threshold", "plain": "The shortest duration a recording keeps for an event; shorter ones are dropped."},
  {"term": "JMC (JDK Mission Control)", "plain": "The desktop app for reading .jfr files, downloaded separately from the JDK."},
  {"term": "RecordingStream", "plain": "An API that hands JFR events to your code while the JVM runs, in batches."}
 ],
 "explain_back": {
  "prompt": "A teammate asks why you'd add a JFR event around the call to the document store when there's already a log line with the duration. Explain the difference in your own words.",
  "answer": "The log line is one number per call, written as text, and it's always on. A JFR event has fields, so I can filter and group by shelf or outcome without parsing anything. It costs almost nothing when no recording wants it, because I fill the fields only after `shouldCommit()`, and a recording can keep only the slow ones with a threshold. Most of all, it lands on the same timeline as the JVM's own events. So for a slow call I can see whether a GC pause, a lock wait or a burst of allocation happened on the same thread at the same moment. A log line can't tell me that."
 },
 "deeper": {
  "minutes": 10,
  "body": "JFR's views are queries, kept in the JDK source in a file called `view.ini`. For example, `hot-methods` counts `ExecutionSample` events grouped by their top frame, and `deoptimizations-by-reason` counts `Deoptimization` events grouped by `reason`. `jfr view --verbose` prints the query a view runs, which helps when you build your own analysis with `RecordingFile`.\n\nThe demo got only 40 execution samples in 4 seconds. Its threads sleep most of the time, and the classic sampler records threads that are running Java code, not sleeping ones. On a machine shared with many busy programs, a running thread may also be waiting for a CPU core when the sampler looks. That's one reason lesson 6 brings in async-profiler, which samples with signals and timers, and why JDK 25 added the CPU-time sampler.\n\n`jfr` has more subcommands: `jfr configure` builds a custom `.jfc` file from options, `jfr scrub` writes a copy of a recording without chosen events, `jfr assemble` and `jfr disassemble` join and split chunk files, and `jfr metadata` lists every event type and field.\n\nTo record a whole test run, add `-XX:StartFlightRecording:filename=build/test.jfr` to the test JVM's arguments. On JDK 25, adding `report-on-exit=allocation-by-site` prints the allocation report straight into the build log, so a reviewer can see it without opening any file."
 },
 "sources": [
  {"title": "The java command, JDK 25 (-XX:StartFlightRecording)", "url": "https://docs.oracle.com/en/java/javase/25/docs/specs/man/java.html"},
  {"title": "The jfr command, JDK 25", "url": "https://docs.oracle.com/en/java/javase/25/docs/specs/man/jfr.html"},
  {"title": "jdk.jfr.Event (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/jdk.jfr/jdk/jfr/Event.html"},
  {"title": "JEP 520: JFR Method Timing and Tracing", "url": "https://openjdk.org/jeps/520"},
  {"title": "JDK Mission Control (openjdk/jmc)", "url": "https://github.com/openjdk/jmc"}
 ]
}
out = ROOT / "content/lessons/perf-05.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
