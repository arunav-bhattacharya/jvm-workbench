import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
read = lambda p: (ROOT / p).read_text()
MAIN = "labs/injector/src/main/kotlin/workbench/injector/l03"
APP_K = "labs/injector/app/src/l03/kotlin/workbench/injector/app/l03"
APP_J = "labs/injector/app/src/l03/java/workbench/injector/app/l03"


def code(kotlin_file, kotlin_run, java_file, java_run):
    """A Kotlin demo with its runnable Java twin."""
    return {"lang": "kotlin", "title": kotlin_file.rsplit("/", 1)[1], "src": read(kotlin_file), "run": kotlin_run, "file": kotlin_file,
            "alt": {"lang": "java", "title": java_file.rsplit("/", 1)[1], "src": read(java_file), "run": java_run, "file": java_file}}


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


# ---------------------------------------------------------------- figure (section 2)
def row(x, y, w, label, cls):
    return (f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="24" rx="6"/>'
            f'<text class="t-s t-code" x="{x + w / 2:g}" y="{y + 16}" text-anchor="middle">{label}</text>')


SOURCES = [("Truck.kt", "box-b"), ("Crew.kt", "box-a"), ("MovingDay.kt", "box-a"), ("MovingDayComponent.kt", "box-a"),
           ("RouteModule.kt", "box-a"), ("Driver.kt", "box-dim"), ("GpsUnit.kt", "box-dim"), ("Packer.kt", "box-dim"),
           ("TapeRoll.kt", "box-dim")]
OUTPUTS = [("TruckFactory.kt", "box-ok", 50), ("CrewFactory.kt", "box-ok", 82), ("MovingDayFactory.kt", "box-ok", 114),
           ("GeneratedMovingDayComponent.kt", "box-ok", 162), ("DriverFactory.kt", "box-dim", 210),
           ("GpsUnitFactory.kt", "box-dim", 242), ("PackerFactory.kt", "box-dim", 274), ("TapeRollFactory.kt", "box-dim", 306)]
LINKS = [(0, 50), (1, 82), (2, 114), (3, 162), (4, 162), (5, 210), (6, 242), (7, 274), (8, 306)]
FIG = (
    '<svg viewBox="0 0 680 372" role="img" aria-label="After a comment is added to Truck.kt, five source files are dirty and KSP redoes '
    'TruckFactory, CrewFactory, MovingDayFactory and the generated component; the factories of Driver, GpsUnit, Packer and TapeRoll come back from backup.">'
    '<text class="t-s t-m" x="120" y="34" text-anchor="middle">sources (Truck.kt edited)</text>'
    '<text class="t-s t-m" x="540" y="34" text-anchor="middle">outputs</text>'
    + "".join(row(20, 50 + 32 * i, 200, name, cls) for i, (name, cls) in enumerate(SOURCES))
    + "".join(row(420, y, 240, name, cls) for name, cls, y in OUTPUTS)
    + "".join(f'<line class="{"ln" if i < 5 else "ln-d"}" x1="222" y1="{50 + 32 * i + 12}" x2="416" y2="{y + 12}" marker-end="url(#arr)"/>'
              for i, y in LINKS)
    + '<text class="t-s t-m" x="340" y="352" text-anchor="middle">edited, dirty, clean (faded); redone (green), restored from backup (faded)</text>'
    '</svg>'
)

# ---------------------------------------------------------------- opening
OPENING = """Picture two crews arriving at two houses at seven in the morning. The first crew follows a sheet written the night before and starts carrying boxes. The second crew first reads every name tag on the pavement, works out who needs whom, and only then lifts anything. Both houses get moved. One crew starts later, and you'd like to know by how much.

The last two lessons wrote the plan during the build and taught it to refuse a broken plan. The easy trap now is to believe that this is faster without measuring it, or to measure only the part that's tiny.

In this sitting we'll race the generated component against a reflection container from a cold start and count the classes each one loads. Then we'll let the truck's slow GPS wait until it's needed, watch one edit go through KSP's incremental log, and meet the real tools. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_PROBE = """long t0 = System.nanoTime();
MovingDayComponent plan = new GeneratedMovingDayComponent();   // builds every singleton, in order
long t1 = System.nanoTime();
MovingDay day = plan.movingDay();                              // returns a field
long t2 = System.nanoTime();
// the other way: ReflectionContainer c = new ReflectionContainer(RouteModule.INSTANCE);
//                MovingDay day = c.get(MovingDay.class);      // reads the notes, builds everything"""
K_PROBE = """val t0 = System.nanoTime()
val plan = GeneratedMovingDayComponent()                       // builds every singleton, in order
val t1 = System.nanoTime()
val day = plan.movingDay()                                     // returns a field
val t2 = System.nanoTime()
// the other way: val c = ReflectionContainer(RouteModule)
//                val day = c.get(MovingDay::class.java)       // reads the notes, builds everything"""
OUT_RACE = """7 cold starts each, medians (a busy machine: compare the two rows, not the numbers with yours)
               create   first get   second get   JVM run  classes  proxy classes  annotations
generated    25.53 ms     0.00 ms     0.000 ms    181 ms      817              0            0
reflection   50.92 ms    21.02 ms     0.002 ms    256 ms     1059              6            4"""

S0 = """First, the words in one breath. **KSP**, Kotlin Symbol Processing, runs processors, plug-ins for the build that read your declarations and write new code. Java has had the same kind of plug-in since Java 6, the annotation processors that javac runs, and KSP is Kotlin's own, faster way to do that job for Kotlin code. Our **component** is the class our processor generates to build the **graph**: every object of the moving day, and who needs whom. It hands each object its **dependencies**, the objects it needs, through its constructor, which is **dependency injection** by **constructor injection**. Each line of the plan is a **binding**. A **singleton** is built once per component, anything else on each request, and each class has a generated **factory** that calls its constructor.

Now the race. `StartupRace` in the lesson 3 app starts a fresh JVM for every run, seven runs for each way of wiring the same crew. In each JVM, `WiringProbe` wires the crew one way and asks for the moving day twice, timing each step with `System.nanoTime()`:

""" + pair(J_PROBE, K_PROBE) + """

The parent times the whole JVM run, and `-Xlog:class+load`, a JVM switch that logs every class as it's loaded, counts the classes. Both ways build the same crew: each probe's line ends with the plan's first line, `Sam drives truck MOVE-1 on the highway`. Make your guess for the wiring ratio before you read on. On this machine, four cores with a load average around 5 from other builds, the race printed:

```text
""" + OUT_RACE + """
```

The generated component does all its work in `create`: its constructor builds every singleton in order, so the first `movingDay()` only returns a field. Add `create` and `first get` together, and it's 25.5 ms against 71.9 ms, about 2.8 times faster. The whole JVM run was 75 ms shorter. An earlier run, at a higher load, gave 17.6 against 46.3 ms and 139 against 192 ms, and the Java twin's run gave 32.1 against 66.6 ms. So the times moved by a third from run to run, and the ratio stayed between 2 and 3. The class counts didn't move at all.

What are the 242 extra classes? About forty come from `java.lang.reflect`, much of it the JDK's proxy machinery. Six are proxy classes it generated while the program ran, `jdk.proxy1.$Proxy0` to `jdk.proxy2.$Proxy5`, to stand for annotations being read. Others parse the generic signature `Lazy<GpsUnit>` out of the class file. And four are the annotation classes themselves. The generated component never loads `Inject`, `Singleton`, `Named` or `Provides` at all. The sticky notes did their job in the build and stayed there.

Once wired, the two are equally quick: the second request costs a few microseconds or less either way. Fifty milliseconds won't matter to a program that starts once a week. They matter to one that starts often, like a command-line tool, or a test suite that builds a fresh component for every test. And this crew has eight classes, where a real program has hundreds.

**Reflection pays for the wiring at every start. Generated wiring pays once, in the build.**

Look at the generated `create` time again. It builds everything at once, including parts nobody needs at seven in the morning. The truck's GPS is one of them."""

# ---------------------------------------------------------------- section 1
J_LAZY = """// Closest Java equivalent: a Supplier, which the component makes build the GPS only once
public class Truck {
    private final Supplier<GpsUnit> gps;
    @Inject public Truck(Driver driver, Supplier<GpsUnit> gps) { this.gps = gps; /* ... */ }
    public String directions() { return gps.get().directionsTo("the new house"); }
}

public class Packer {
    private final Supplier<TapeRoll> newTape;                     // one more roll on every get()
    @Inject public Packer(Supplier<TapeRoll> newTape) { this.newTape = newTape; }
    public String pack(String room) { return room + " packed with tape roll #" + newTape.get().getNumber(); }
}"""
K_LAZY = """@Singleton
class Truck @Inject constructor(val driver: Driver, private val gps: Lazy<GpsUnit>) {
    fun directions(): String = gps.value.directionsTo("the new house")   // switched on here, once
}

class Packer @Inject constructor(private val newTape: () -> TapeRoll) { // one more roll on every call
    fun pack(room: String): String = "$room packed with tape roll #${newTape().number}"
}"""
J_HELD = """// The same lines in Java, written by a javac processor; memoize() is a small generated helper
private final Supplier<GpsUnit> gpsUnit = memoize(GpsUnitFactory::create);  // built on the first get()
private final Truck truck = TruckFactory.create(driver, gpsUnit);
private Packer newPacker() { return PackerFactory.create(this::newTapeRoll); }"""
K_HELD = """private val gpsUnit: Lazy<GpsUnit> = lazy { GpsUnitFactory.create() }      // built on the first .value
private val truck: Truck = TruckFactory.create(driver, gpsUnit)
private fun newPacker(): Packer = PackerFactory.create({ newTapeRoll() })"""
OUT_GPS = """crew ready after 109 ms, GPS switched on: 0
Sam drives truck MOVE-1 on the highway
the family takes the back roads
kitchen packed with tape roll #1
pantry packed with tape roll #2
bedroom packed with tape roll #3
GPS: turn left at the bakery for the new house
first directions after 488 ms, GPS switched on: 1
GPS: turn left at the bakery for the new house
second directions after 489 ms, GPS switched on: 1"""

S1 = """The truck's GPS takes a while to switch on, because it has to find the satellites first. In the demo app, `GpsUnit`'s constructor sleeps for 300 ms to stand in for that wait, a delay chosen for teaching. With the plan as it was, the component's constructor would build the GPS along with the truck. Every start would pay those 300 ms, even on a day the truck never asks for directions.

**Lazy injection** fixes that. The truck asks for `Lazy<GpsUnit>` instead of `GpsUnit`. That's a box that builds its contents the first time someone opens it with `.value`, and hands back the same contents after that. **Provider injection** is its sibling. The packer asks for `() -> TapeRoll`, a function that hands out one more roll on every call. In the moving-day picture, the GPS is on call and comes when it's first needed, and every room gets a fresh roll of tape:

""" + pair(J_LAZY, K_LAZY) + """

The processor changes in two of the KSP track's five moves. In the Read move, `requestOf` unwraps the type a parameter asks for: `Lazy<GpsUnit>` becomes (LAZY, `GpsUnit`), and `() -> TapeRoll`, whose class is `kotlin.Function0`, becomes (PROVIDER, `TapeRoll`). The key is the type inside, so every check from lesson 2 still works. Forget the GPS's `@Inject`, and the build says `MovingDay needs Crew needs Truck needs GpsUnit: nobody provides GpsUnit.`, on the truck's `gps` parameter.

In the Write move, a singleton that someone asks for lazily is held in a `Lazy` of its own, and each request gets the expression for its kind:

""" + pair(J_HELD, K_HELD) + """

| asked for as | `gpsUnit` (singleton, held in a Lazy) | `truck` (singleton, built at once) | `newTapeRoll` (no `@Singleton`) |
|---|---|---|---|
| the type itself | `gpsUnit.value` | `truck` | `newTapeRoll()` |
| `Lazy<T>` | `gpsUnit` | `lazyOf(truck)` | `lazy { newTapeRoll() }` |
| `() -> T` | `{ gpsUnit.value }` | `{ truck }` | `{ newTapeRoll() }` |

Kotlin's `lazy { }` is safe with threads by default: its mode is `SYNCHRONIZED`, so the body runs once even if two threads open the box at the same moment. The app shows the result:

```text
""" + OUT_GPS + """
```

The crew was ready with the GPS still off. The first request for directions paid for the GPS, and the second paid nothing: the same GPS, still on. Three rooms, three rolls of tape. Ask for `GpsUnit` directly instead, and the generated line becomes `private val gpsUnit: GpsUnit = GpsUnitFactory.create()`; the crew is then ready after 327 ms, with the GPS already on.

Laziness moves a cost; it doesn't remove one. The first caller who needs directions waits the 300 ms, perhaps at a worse moment than seven in the morning. And a **cycle**, a chain of "needs" that comes back to where it started, is still a cycle to our processor when one link is a `Lazy`. Nothing would actually be built twice there, but we chose to keep the check simple and strict.

**Make a part lazy when it's expensive and not always needed. Build the rest with the plan.**

The plan is fast now, and patient. But two claims about it still rest on our word: that the generated code uses no reflection, and that one edit doesn't redo everything. Let's check both."""

# ---------------------------------------------------------------- section 2
J_SCAN = """// The same check in Java, with AssertJ, calling the Kotlin test helper
for (Map.Entry<String, String> file : run.getGenerated().entrySet()) {
    assertThat(file.getValue()).as(file.getKey() + " uses reflection")
            .doesNotContain("java.lang.reflect", "kotlin.reflect", "::class", "Class.forName", "javaClass", "getDeclared");
}"""
K_SCAN = """for ((path, text) in run.generated) {                          // every file KSP wrote
    assertThat(text).withFailMessage("$path uses reflection:\\n$text")
        .doesNotContain("java.lang.reflect", "kotlin.reflect", "::class", "Class.forName", "javaClass", "getDeclared")
}"""
OUT_DIRTY = """Modified
  src/l03/kotlin/workbench/injector/app/l03/Truck.kt
...
Affected By new syms
  build/generated/ksp/l03/kotlin/workbench/injector/app/l03/GeneratedMovingDayComponent.kt
  src/l03/kotlin/workbench/injector/app/l03/Crew.kt
  src/l03/kotlin/workbench/injector/app/l03/MovingDayComponent.kt
...
Dirty:
  src/l03/kotlin/workbench/injector/app/l03/RouteModule.kt
  src/l03/kotlin/workbench/injector/app/l03/Crew.kt
  src/l03/kotlin/workbench/injector/app/l03/Truck.kt
  src/l03/kotlin/workbench/injector/app/l03/MovingDayComponent.kt
  src/l03/kotlin/workbench/injector/app/l03/MovingDay.kt

Dirty / All: 29.41%"""
OUT_REDONE = """All reprocessed outputs
  build/generated/ksp/l03/kotlin/workbench/injector/app/l03/CrewFactory.kt
  build/generated/ksp/l03/kotlin/workbench/injector/app/l03/TruckFactory.kt
  build/generated/ksp/l03/kotlin/workbench/injector/app/l03/MovingDayFactory.kt
  build/generated/ksp/l03/kotlin/workbench/injector/app/l03/GeneratedMovingDayComponent.kt"""

S2 = """The first claim is that the generated code uses no **reflection**, a program inspecting its own classes while it runs. The lab doesn't take that on trust. One test reads every file KSP generated and fails if any of them reaches for reflection:

""" + pair(J_SCAN, K_SCAN) + """

The race's class log agrees from the other side: no proxy classes, and not one annotation class loaded. That test is a cheap habit to keep. It fails on the day someone "just quickly" reads an annotation at run time.

The second claim is about the build. **Incremental processing** means KSP reprocesses only the files a change can affect. In the KSP track's picture, you repack one box, redo its card, and redo the master list. Let's watch it in lesson 3's source set. Build once with KSP's log switched on, add one comment line to `Truck.kt`, and build again:

```bash
./gradlew :injector:app:compileL03Kotlin -Pksp.incremental.log=true
echo "// a comment, so the file's text changes" >> injector/app/src/l03/kotlin/workbench/injector/app/l03/Truck.kt
./gradlew :injector:app:compileL03Kotlin -Pksp.incremental.log=true
```

KSP rewrites its logs on every run, in `injector/app/build/kspCaches/l03/logs/`. The second run's `kspDirtySet.log` said, shortened:

```text
""" + OUT_DIRTY + """
```

And the end of `kspSourceToOutputs.log`:

```text
""" + OUT_REDONE + """
```

Five of the source set's seventeen files were dirty. `Truck.kt` is the one we touched. `Crew.kt` and `MovingDayComponent.kt` are listed as affected because the processors looked up `Truck` while reading them. Dirtiness then spreads: `MovingDay.kt` looked up `Crew`, so it joins, until no new dirty files appear. `RouteModule.kt` is dirty for another reason. It's one of the declared sources of the component, an **aggregating** output, and KSP files the component under `<AnyChanges is a virtual file; DO NOT USE.>`, its key for outputs that any change redoes. The figure draws the result. Three cards and the master list were redone; four cards came back from KSP's backups untouched: the driver's, the GPS's, the packer's and the tape roll's.

Two traps wait for anyone repeating this. `touch Truck.kt` changes nothing, because Gradle compares the text, not the date. And the build cache can restore old outputs after you undo an edit without running KSP at all, so make a fresh edit, or add `--no-build-cache`. One odd result, too: in three edit-and-build tries on this machine, one run reported `Dirty / All: 100.00%` with an empty `Modified` list, a full pass. KSP processes everything on a first build or after a failed one, and we didn't find what triggered this one; the next edit was incremental again.

**Don't take a claim about generated code on trust. Test the text, and read the log.**

That's the limit of the aggregating design, said plainly: the component is redone on every edit, however small. Here it's one short file. In a program with hundreds of classes it's one long file each time, which is a fair price for a plan that's always complete."""

# ---------------------------------------------------------------- section 3
K_GRADLE = """// build.gradle.kts of an app module: one of these, not both
dependencies {
    ksp("com.google.dagger:dagger-compiler:2.60.1")            // Dagger
    ksp("me.tatarka.inject:kotlin-inject-compiler-ksp:0.9.0")  // kotlin-inject
}"""

S3 = """Everything in this capstone has full-sized relatives. Now that the idea is clear, here they are, each in a few plain sentences, as of November 2026.

**Dagger** generates component implementations and factories, the same two kinds of output as ours. Its KSP processor is `dagger-compiler`, and its docs say "Dagger's KSP support is stable as of Dagger 2.60+ and KSP 2.3.9+". **Hilt**, built on Dagger for Android phone apps, ships its own KSP processor, `hilt-compiler`, at the same version. Two warnings from Dagger's docs matter when you move a project over. Plugins written against Dagger's SPI, the interface its plug-ins use, must move to its new SPI. And "KSP processors are not able to resolve types generated by other Javac/KAPT processors". kotlinlang's list of supported libraries, on a page dated November 2026, still says "Dagger: Alpha" and "Hilt: In progress". Dagger's own docs are the ones to trust.

**kotlin-inject** is closer to what you wrote. It runs only on KSP, and its 0.9.0 release removed KSP1 support. In its README's words, "An implementation of this component will be generated for you". You reach it through a generated `.create()` extension, instead of a class name like our `GeneratedMovingDayComponent`.

**Koin** moved the other way. Its annotations used to go through a KSP processor that generated visible source files and extensions such as `AppModule().module`. Its docs now say "`koin-ksp-compiler` is deprecated and will be removed in a future Koin version". The annotations stay, and the Koin Compiler Plugin, `koin-compiler-plugin`, now processes them (1.2.3 on Maven Central, November 2026). They keep KSP only for projects that "can't move to Kotlin 2.3.20 or later yet". The plugin "replaces `single<UserRepository>()` (or the `@Singleton` class) with the equivalent of `single { UserRepository(get(), get()) }`" during compilation. That's a change to your own code. In the KSP track's picture, it's a job for the mover who repacks the box, not for the helper who can only add new cards. Each `get()` in that line asks Koin's container for an argument, so that part of the lookup still happens while the program runs.

Adding either of the first two to a real build is one line, as our app's processors are:

```kotlin solo
""" + K_GRADLE + """
```

What you built has the same bones. There's a factory per class and a component per interface, checks fail the build on the exact line, and parts can be asked for lazily or through a provider. The real tools add years of cases you can now recognise when you meet them."""

# ---------------------------------------------------------------- closing
CLOSING = """We started with two crews at two houses. The crew with the sheet written the night before was wired two to three times sooner, loaded 242 fewer classes, and never read an annotation on the day.

That closes Part 5. It began with a helper who reads the labels on sealed boxes and writes new cards. The capstone turned those cards into a plan that the build checks before anyone lifts a box.

In your own code, find one thing that reads annotations at start-up. Could its answer be written down during the build?

That ends the course. From here, take one program you know well and try one tool from each Part on it."""

L = {
 "id": "cap5-03",
 "title": "Measure the payoff, then meet the real tools",
 "minutes": 40,
 "goal": "By the end you can measure what compile-time wiring saves at start-up, inject Lazy<T> and () -> T so that an expensive part waits until it's needed, read KSP's incremental log for one changed class, and say how Dagger, Hilt, kotlin-inject and Koin differ from the processor you built.",
 "opening": OPENING,
 "warmup": {
  "q": "Seven cold starts each wire the same moving-day crew, once with the generated component and once with a reflection container, on a busy machine. Which difference do you expect to stay the same from run to run?",
  "options": ["The wiring time in milliseconds", "The time of the whole JVM run", "The number of classes loaded", "None of them: everything jumps around on a busy machine"],
  "answer": 2,
  "why": "Timings depend on what else the machine is doing; between our runs they moved by about a third, though the generated side won every time. The classes a program loads depend only on the code it runs, so the count was the same in every run: 817 for the generated component and 1,059 for reflection. When a machine is noisy, count something before you time it."
 },
 "sections": [
  {
   "h": "Race them from cold: wiring time, start-up and classes loaded",
   "body": S0,
   "try": {
    "title": "Run the cold-start race",
    "minutes": 5,
    "steps": [
     "Write down your guess: how much faster will the generated component wire the crew, and how many extra classes will reflection load?",
     "Run `StartupRace` from `labs/`. It starts fourteen small JVMs, one after another, and prints one row per way of wiring.",
     "Run `StartupRaceJava`, the same race with Java calling the same generated component and the same container.",
     "Run `StartupRace` again with `-Pargs=3` added (three starts each). Which columns moved, and which didn't?"
    ],
    "code": code(f"{APP_K}/StartupRace.kt", "./gradlew :injector:app:demo -Pmain=workbench.injector.app.l03.StartupRaceKt",
                 f"{APP_J}/StartupRaceJava.java", "./gradlew :injector:app:demo -Pmain=workbench.injector.app.l03.StartupRaceJava"),
    "expect": "Two rows. Your times will differ from the ones above, but the generated row should win on `create` plus `first get` and on `JVM run`, with `first get` near 0.00 ms because its constructor already built everything. The class counts should hardly move between runs: about 817 against 1,059 (the Java twin loads a couple fewer), 0 against 6 proxy classes and 0 against 4 annotation classes. `second get` is tiny for both."
   },
   "refs": [{"title": "Unified JVM logging, -Xlog (java command, JDK 25)", "url": "https://docs.oracle.com/en/java/javase/25/docs/specs/man/java.html", "kind": "docs"}]
  },
  {
   "h": "The GPS can wait: Lazy<T> and () -> T",
   "body": S1,
   "try": {
    "title": "Keep the GPS off until the truck asks",
    "minutes": 4,
    "steps": [
     "Predict the first line `MovingDayApp` prints: how long until the crew is ready, and is the GPS on?",
     "Run `MovingDayApp`, then its Java twin.",
     "In `app/src/l03/.../Truck.kt`, change `private val gps: Lazy<GpsUnit>` to `private val gps: GpsUnit` and `gps.value.directionsTo` to `gps.directionsTo`. Predict, run `MovingDayApp` again, then change both back."
    ],
    "code": code(f"{APP_K}/MovingDayApp.kt", "./gradlew :injector:app:demo -Pmain=workbench.injector.app.l03.MovingDayAppKt",
                 f"{APP_J}/MovingDayAppJava.java", "./gradlew :injector:app:demo -Pmain=workbench.injector.app.l03.MovingDayAppJava"),
    "expect": "With `Lazy`, the crew is ready with `GPS switched on: 0`, the first directions arrive a little over 300 ms later with the GPS on, and the second directions take no time and switch nothing on again. Three rooms use tape rolls #1, #2 and #3. Asked for directly, the GPS is built with the crew: the first line reads about `crew ready after 327 ms, GPS switched on: 1`, and the directions cost nothing extra."
   },
   "refs": [{"title": "Lazy properties (Kotlin docs)", "url": "https://kotlinlang.org/docs/delegated-properties.html#lazy-properties", "kind": "docs"}]
  },
  {
   "h": "Proof, not promises: no reflection in the generated code, and what one edit rebuilds",
   "body": S2,
   "figure": {"svg": FIG, "caption": "One comment in Truck.kt: five source files are dirty, KSP redoes three factories and the aggregating component, and the other four factories come back from its backups."},
   "try": {
    "title": "Read KSP's incremental log after one edit",
    "minutes": 5,
    "steps": [
     "From `labs/`, run `./gradlew :injector:app:compileL03Kotlin -Pksp.incremental.log=true`. Open `injector/app/build/kspCaches/l03/logs/kspDirtySet.log`: what does `Dirty / All` say for this first build?",
     "Add a comment line at the end of `injector/app/src/l03/kotlin/workbench/injector/app/l03/Truck.kt` and run the same command again. Read the `Dirty:` list and `Dirty / All`, then `All reprocessed outputs` in `kspSourceToOutputs.log`.",
     "Now add a comment to `Packer.kt` instead and run once more. Before you look, predict which outputs are redone this time. Remove both comments when you're done."
    ],
    "expect": "The first build with the log switched on reports `Dirty / All: 100.00%`: everything was processed. After the comment in `Truck.kt`, five files are dirty (`Dirty / All: 29.41%`), and the reprocessed outputs are `CrewFactory.kt`, `TruckFactory.kt`, `MovingDayFactory.kt` and `GeneratedMovingDayComponent.kt`. For `Packer.kt` it's 29.41% again, with `PackerFactory.kt`, `CrewFactory.kt`, `MovingDayFactory.kt` and the component redone: the crew looked up `Packer`, and the moving day looked up `Crew`. If the log shows `100.00%` with an empty `Modified` list, KSP did a full pass; make another edit and run again. If nothing ran at all, the build cache restored the outputs: make a fresh edit or add `--no-build-cache`."
   },
   "refs": [{"title": "Incremental processing (Kotlin docs)", "url": "https://kotlinlang.org/docs/ksp-incremental.html", "kind": "docs"}]
  },
  {
   "h": "The real tools: Dagger and Hilt, kotlin-inject, and Koin",
   "body": S3,
   "refs": [{"title": "Dagger: KSP (dagger.dev)", "url": "https://dagger.dev/dev-guide/ksp", "kind": "docs"},
            {"title": "kotlin-inject (GitHub)", "url": "https://github.com/evant/kotlin-inject", "kind": "read"},
            {"title": "Koin Annotations with KSP (Koin docs)", "url": "https://insert-koin.io/docs/setup/annotations-ksp", "kind": "docs"}]
  }
 ],
 "compare": {
  "title": "A part that waits: Supplier in Java, Lazy in Kotlin",
  "java": {"title": "Truck.java", "src": "public class Truck {\n    private final Supplier<GpsUnit> gps;\n\n    @Inject\n    public Truck(Driver driver, Supplier<GpsUnit> gps) { this.gps = gps; }\n\n    public String directions() {\n        return gps.get().directionsTo(\"the new house\");   // builds once only if the Supplier remembers\n    }\n}\n\n// a Supplier that remembers, written by hand\nstatic <T> Supplier<T> memoize(Supplier<T> make) {\n    return new Supplier<>() {\n        private volatile T value;\n        public synchronized T get() { if (value == null) value = make.get(); return value; }\n    };\n}"},
  "kotlin": {"title": "Truck.kt", "src": "@Singleton\nclass Truck @Inject constructor(val driver: Driver, private val gps: Lazy<GpsUnit>) {\n    fun directions(): String = gps.value.directionsTo(\"the new house\")   // builds once, then remembers\n}\n\n// the component's side: the standard library's lazy {}, SYNCHRONIZED by default\nprivate val gpsUnit: Lazy<GpsUnit> = lazy { GpsUnitFactory.create() }"},
  "note": "Java's `Supplier<T>` only promises a `get()`: whether it builds once or every time is up to whoever wrote it, so a component that wants \"once, on first use\" has to wrap it, as `memoize` does. Kotlin's `Lazy<T>` makes the promise part of the type: `.value` builds on first use and returns the same object afterwards, and `lazy { }` is thread-safe by default. For a fresh object on every call, the two languages meet in the middle: Java's `Supplier<TapeRoll>` and Kotlin's `() -> TapeRoll` are both just functions with no parameters."
 },
 "worked": {
  "title": "Choose how each part asks for what it needs",
  "steps": [
   {"say": "The driver is cheap to build and needed every day: ask for him directly. The component builds him with the plan and passes the object.",
    "code": "class Truck @Inject constructor(val driver: Driver /* ... */)\n// generated: TruckFactory.create(driver, ...)", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "@Inject public Truck(Driver driver /* ... */) { /* ... */ }\n// generated: TruckFactory.create(driver, ...)"},
   {"say": "The GPS is slow to start and not needed on every day: ask for `Lazy<GpsUnit>`. Because it's a singleton asked for lazily, the component holds it in a `Lazy` and passes that.",
    "code": "class Truck @Inject constructor(val driver: Driver, private val gps: Lazy<GpsUnit>)\n// generated: private val gpsUnit: Lazy<GpsUnit> = lazy { GpsUnitFactory.create() }", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "@Inject public Truck(Driver driver, Supplier<GpsUnit> gps) { /* ... */ }\n// generated: private final Supplier<GpsUnit> gpsUnit = memoize(GpsUnitFactory::create);"},
   {"say": "Tape runs out room by room: the packer asks for `() -> TapeRoll` and calls it once per room. `TapeRoll` has no `@Singleton`, so each call builds a new roll.",
    "code": "class Packer @Inject constructor(private val newTape: () -> TapeRoll)\n// generated: PackerFactory.create({ newTapeRoll() })", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "@Inject public Packer(Supplier<TapeRoll> newTape) { /* ... */ }\n// generated: PackerFactory.create(this::newTapeRoll)"},
   {"say": "Check the choice with the app, not with your intuition: `MovingDayApp` prints when the crew is ready and when the GPS switched on. If a part is needed on every start anyway, `Lazy` only adds a lock and a box; ask for it directly.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Lazy and provider requests",
  "minutes": 12,
  "files": [f"{MAIN}/Bindings.kt", f"{MAIN}/ComponentProcessor.kt"],
  "run": "./gradlew :injector:test --tests 'workbench.injector.l03.*'",
  "steps": [
   "Run the tests once. All four fail with `l03 not done yet: unwrap Lazy<T> into (LAZY, T) ...`. Everything except two functions is the solution of lessons 1 and 2, as given code. The crew is in `src/test/kotlin/workbench/injector/l03/MoveMateSources.kt`, and its `GpsUnit` counts how often it was switched on.",
   "Read: in `Bindings.kt`, write `requestOf`. Compare the type's qualified name with `kotlin.Lazy` and `kotlin.Function0`, and take the one type argument with `type.arguments.singleOrNull()?.type?.resolve()`. Anything else is a direct request for the type itself.",
   "Write: in `ComponentProcessor.kt`, write `reference(binding, kind, held)` from the table in its KDoc. Then read `heldLazily` and `componentFile`, which are given, to see where your expressions end up.",
   "Prove: run the tests until all four pass, including the one that scans every generated file for reflection. Then run `./gradlew :injector:app:demo -Pmain=workbench.injector.app.l03.MovingDayAppKt -Pmine=l03` and check that the GPS stays off until the first directions.",
   "Prove it again, from cold: run `StartupRace` with `-Pmine=l03` and compare its class counts with this lesson's.",
   "From memory: close the files and write the table of nine references (three kinds of request, three kinds of binding) on paper. Check it against your `reference`."
  ],
  "hints": [
   "For `Lazy<GpsUnit>`, `type.arguments` has one entry, and its `type` is a `KSTypeReference`: call `resolve()` on it.",
   "A function type with no parameters is `kotlin.Function0`. Comparing that exact name also keeps `(Int) -> Box`, a `Function1`, out of the provider case.",
   "`CodeBlock.of(\"lazy { %N() }\", name)` writes `lazy { newTapeRoll() }`; `%N` takes the member name as a String.",
   "If the GPS test sees `GPS on before: 1`, a lazily asked singleton is being built in the constructor. In `reference`, check `binding.key in held` before the plain singleton case."
  ],
  "done_when": "All four tests in `LazyAndProvidersTest` pass, and `MovingDayApp` with `-Pmine=l03` prints `GPS switched on: 0` until the first directions."
 },
 "drill": {
  "title": "Write a once-only box from memory",
  "minutes": 5,
  "prompt": "Close this page. Write a class `Once<T>(make: () -> T)` whose `value` calls `make` the first time and returns the same object after that, and is safe when two threads ask at the same moment. Then write the Java version as a `Supplier<T>`. (Kotlin's `lazy { }` is this, done for you; the memory model track explains why the field needs `volatile`.)",
  "answer": {"lang": "kotlin", "src": "class Once<T : Any>(private val make: () -> T) {\n    @Volatile private var made: T? = null\n\n    val value: T\n        get() {\n            made?.let { return it }                 // fast path: already built\n            synchronized(this) {\n                made?.let { return it }             // look again with the lock held\n                return make().also { made = it }    // build once\n            }\n        }\n}\n\nval gps = Once { GpsUnit() }                        // nothing built yet\nprintln(gps.value === gps.value)                   // true: built on the first .value",
             "alt": {"lang": "java", "title": "Once.java", "src": "final class Once<T> implements Supplier<T> {\n    private final Supplier<T> make;\n    private volatile T made;\n\n    Once(Supplier<T> make) { this.make = make; }\n\n    @Override\n    public T get() {\n        T result = made;\n        if (result != null) return result;          // fast path: already built\n        synchronized (this) {\n            if (made == null) made = make.get();    // look again with the lock held, build once\n            return made;\n        }\n    }\n}"}}
 },
 "recap": [
  "From cold, on a busy machine, the generated component wired the crew two to three times faster than the reflection container and the JVM run was shorter. The stable number was the class count: 817 against 1,059.",
  "The generated path loaded no proxy classes and none of the annotation classes. A test that scans the generated text for reflection keeps it that way.",
  "`Lazy<T>` builds once, on the first `.value`; `() -> T` gives one more on every call. The processor unwraps both to the type inside, so the graph checks don't change.",
  "One comment in `Truck.kt` dirtied 5 of 17 files: the edited file, files that looked up its types, and the sources of the aggregating component, which is redone on every change.",
  "Dagger and Hilt (stable on KSP since Dagger 2.60) and kotlin-inject generate component code as we did. Koin has moved its annotations from a KSP processor to a compiler plugin that rewrites your calls, which KSP can't do.",
  "The limit: laziness moves a cost rather than removing it, and a generated plan can't change while the program runs."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "In the race, the generated component's `first get` was 0.00 ms, while its `create` took about 25 ms. Why?",
   "options": ["The JIT compiled `movingDay()` away", "Its constructor builds every singleton in order, so `movingDay()` only returns a field", "The timer can't measure below a millisecond", "It cached a reflection result from the build"],
   "answer": 1,
   "why": "The generated plan is eager: every singleton is a `private val` set in the constructor, so all the work lands in `create`. The fair comparison is `create` plus `first get` on both sides, which is why the lesson adds them. There is no reflection in the generated code to cache."},
  {"q": "`Truck` asks for `Lazy<GpsUnit>`, and `GpsUnit` is a `@Singleton`. What does the generated component hold for the GPS?",
   "options": ["`private val gpsUnit: Lazy<GpsUnit> = lazy { GpsUnitFactory.create() }`", "`private val gpsUnit: GpsUnit = GpsUnitFactory.create()`", "`private fun newGpsUnit(): GpsUnit`", "Nothing: the truck builds its own GPS"],
   "answer": 0,
   "why": "A singleton that someone asks for lazily is held in a `Lazy`, and the truck gets that `Lazy` itself, so the GPS is built on the first `.value` and shared afterwards. A plain `val` would build it with the plan; a `new...()` function would make a new GPS per request, which is what you get without `@Singleton`."},
  {"q": "A packer asks for `newTape: () -> TapeRoll`, and `TapeRoll` has no `@Singleton`. The packer packs three rooms, calling `newTape()` once per room. How many rolls does it use?",
   "options": ["One, built on the first call", "None until the component is closed", "Three, one per call", "It depends on how many threads pack"],
   "answer": 2,
   "why": "The generated argument is `{ newTapeRoll() }`, and `newTapeRoll()` builds a new roll every time because `TapeRoll` isn't a singleton. One roll for every call is the point of provider injection; `Lazy<TapeRoll>` would have given one roll, built on first use."},
  {"q": "From Compiler plugins: Koin's compiler plugin replaces `single<UserRepository>()` with the equivalent of `single { UserRepository(get(), get()) }` while your code compiles. Why couldn't a KSP processor do the same job?",
   "options": ["KSP is too slow for Koin's users", "KSP can't read annotations on classes", "KSP runs after the Kotlin compiler, too late to change anything", "KSP can only add new files: it can't change an expression in your code"],
   "answer": 3,
   "why": "KSP processors read declarations and write new files; they can't see expressions or change existing code, as the compiler plugins lesson put it. Rewriting a call inside your function is a compiler plugin's job. KSP actually runs before the Kotlin compile, and it reads annotations well, which is how Koin's older KSP processor worked.",
   "from": "kt-06"},
  {"q": "You add one comment to `Truck.kt` and rebuild lesson 3's app with `-Pksp.incremental.log=true`. Which output does KSP restore from its backup instead of regenerating?",
   "options": ["`GpsUnitFactory.kt`", "`TruckFactory.kt`", "`GeneratedMovingDayComponent.kt`", "`CrewFactory.kt`"],
   "answer": 0,
   "why": "`GpsUnit.kt` neither changed nor looked up anything in `Truck.kt`, so its isolating card is restored. `TruckFactory.kt` comes from the edited file, `CrewFactory.kt` from a file that looked up `Truck`, and the component is aggregating, so it's redone on every change."}
 ],
 "flashcards": [
  {"front": "What does `Lazy<T>` injection give a class?", "back": "A box that builds its T on the first `.value` and returns the same one after that."},
  {"front": "What does provider injection, `() -> T`, give a class?", "back": "A function that returns one more T on every call, or the shared one if T is a singleton."},
  {"front": "Which number in the cold-start race stayed the same from run to run?", "back": "The classes loaded: 817 for the generated component, 1,059 for reflection. The times moved with the machine's load."},
  {"front": "Why does the generated path load no annotation classes?", "back": "KSP read the annotations during the build. The generated code only calls constructors and factories."},
  {"front": "Why is the component redone after any edit?", "back": "It's an aggregating output: KSP files it under `<AnyChanges is a virtual file; DO NOT USE.>`, so any change redoes it."},
  {"front": "Why did Koin move its annotations from a KSP processor to a compiler plugin?", "back": "The plugin rewrites `single<T>()` calls in your code into constructor calls. KSP can only add new files."}
 ],
 "terms": [
  {"term": "Reflection", "plain": "A program inspecting its own classes, constructors and annotations while it runs."},
  {"term": "Cold start", "plain": "A start in a fresh JVM, before anything is loaded or compiled, the way a program really starts."},
  {"term": "Lazy injection", "plain": "Asking for Lazy<T>: the object is built on the first .value and shared after that."},
  {"term": "Provider injection", "plain": "Asking for () -> T: a function that hands out one more object on every call."},
  {"term": "Incremental processing", "plain": "KSP reprocessing only the files a change can affect, and restoring the other outputs from its backups."},
  {"term": "Aggregating output", "plain": "A generated file built from many sources, which KSP redoes whenever any file changes."},
  {"term": "Compiler plugin", "plain": "A jar the Kotlin compiler loads to change the code it compiles, which KSP can't do."}
 ],
 "explain_back": {
  "prompt": "A teammate says reflection containers cost nothing worth measuring, because a call through one takes microseconds. Using the race and the GPS, explain what they're right about, what they're missing, and when Lazy helps.",
  "answer": "They're right about the steady state: once wired, the second request took a few microseconds or less either way. What they're missing is the start. A reflection container reads every class's annotations and constructors on every start, so in our race it took two to three times as long to wire the same crew, the JVM run was tens of milliseconds longer, and it loaded about 240 more classes, including proxy classes the JDK generated to represent annotations. The generated component did that work once, in the build, and never even loaded the annotation classes. Fifty milliseconds hardly matters for a program that starts once a week, but it does for a tool or a test suite that starts often, and real programs have far more than eight classes. Lazy helps with a different cost: a part that's slow to build and not always needed, like the GPS. Asked for as Lazy, it's built on the first use instead of with the plan, so the crew is ready sooner. It doesn't remove the cost, it moves it to the first caller."
 },
 "deeper": {
  "minutes": 8,
  "body": "Why count classes at all? Loading a class means finding its bytes, checking them and linking them, and every class costs the start a little. A count is also the honest number on a busy machine: it doesn't depend on what else is running. `-Xlog:class+load` prints one line per class with its source, so you can tell your own classes from the JDK's and from classes made while the program ran, such as `jdk.proxy2.$Proxy1`.\n\nWiring generated at build time also suits the start-up tools of Part 4. A class data sharing archive or an AOT cache stores classes loaded from jars; classes defined while the program runs, such as dynamic proxies, can't be archived the same way, as the Part 4 capstone found. A generated plan leaves almost nothing to be made at run time, so more of the start can come from the archive.\n\nOur component is eager except where you ask for `Lazy`. An eager plan is simple to read and fails fast: if a constructor throws, it throws when the component is created. A fully lazy plan, with every singleton in a `lazy { }`, would start faster still and build only what's used, but a broken constructor would then surface later, on first use. Both are reasonable; pick the failure time you'd rather have.\n\nIn KSP's incremental logs, `kspLookupGraph.log` lists what each reprocessed file looked up, so you can see exactly why `Crew.kt` became dirty when `Truck.kt` changed. With `-Pksp.incremental.log.graph.origin=` and a fully qualified name, KSP also writes a `.dot` file of the lookups around that symbol."
 },
 "sources": [
  {"title": "Dagger: KSP (dagger.dev)", "url": "https://dagger.dev/dev-guide/ksp"},
  {"title": "kotlin-inject (GitHub)", "url": "https://github.com/evant/kotlin-inject"},
  {"title": "Koin Annotations with KSP (Koin docs)", "url": "https://insert-koin.io/docs/setup/annotations-ksp"},
  {"title": "Incremental processing (Kotlin docs)", "url": "https://kotlinlang.org/docs/ksp-incremental.html"},
  {"title": "Lazy properties (Kotlin docs)", "url": "https://kotlinlang.org/docs/delegated-properties.html#lazy-properties"}
 ]
}
out = ROOT / "content/lessons/cap5-03.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
