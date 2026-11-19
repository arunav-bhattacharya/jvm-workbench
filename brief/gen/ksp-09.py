import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/ksp/src"
app = "labs/ksp/app/src/l09"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :ksp:demo -Pmain=workbench.ksp.l09.demo."


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


def timing_code():
    """The timing program in the playground, with its Java twin calling the same generated Kotlin cards."""
    k = f"{app}/kotlin/workbench/ksp/app/l09/CardTiming.kt"
    j = f"{app}/java/workbench/ksp/app/l09/CardTimingJava.java"
    return {"lang": "kotlin", "title": "CardTiming.kt", "src": read(k),
            "run": "./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l09.CardTimingKt", "file": k,
            "alt": {"lang": "java", "title": "CardTimingJava.java", "src": read(j),
                    "run": "./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l09.CardTimingJava", "file": j}}


def port_code():
    """The port demo (KSP, in memory) with the javac processor it ports as its Java twin."""
    k = f"{lab}/demo/kotlin/workbench/ksp/l09/demo/PortDemo.kt"
    j = f"{lab}/main/java/workbench/ksp/l09/JavacPackingSlipProcessor.java"
    return {"lang": "kotlin", "title": "PortDemo.kt", "src": read(k), "run": RUN + "PortDemoKt", "file": k,
            "alt": {"lang": "java", "title": "JavacPackingSlipProcessor.java", "src": read(j), "file": j}}


def kdemo(name):
    """A kctfork demo: Kotlin only (a processor run in memory has no Java twin)."""
    f = f"{lab}/demo/kotlin/workbench/ksp/l09/demo/{name}.kt"
    return {"lang": "kotlin", "title": f"{name}.kt", "src": read(f), "run": RUN + name + "Kt", "file": f, "solo": True}


FIG = (
    '<svg viewBox="0 0 700 300" role="img" aria-label="Choosing the tool in three questions. Must the job change a class '
    'you wrote? Then it needs a compiler plugin. Does it run a few times, on a few classes? Then reflection is fine. Does a '
    'KSP processor exist for it? Then use KSP. If only a Java processor exists, kapt runs it on Java copies of your classes.">'
    '<rect class="box" x="20" y="20" width="400" height="50" rx="8"/>'
    '<text class="t" x="220" y="50" text-anchor="middle">Must the job change a class you wrote?</text>'
    '<line class="ln" x1="424" y1="45" x2="476" y2="45" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="450" y="38" text-anchor="middle">yes</text>'
    '<rect class="box-b" x="480" y="20" width="200" height="50" rx="8"/>'
    '<text class="t-s" x="580" y="41" text-anchor="middle">a compiler plugin</text>'
    '<text class="t-s t-m" x="580" y="59" text-anchor="middle">the mover repacks the box</text>'
    '<line class="ln" x1="220" y1="72" x2="220" y2="96" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="236" y="88" text-anchor="start">no</text>'
    '<rect class="box" x="20" y="100" width="400" height="50" rx="8"/>'
    '<text class="t" x="220" y="130" text-anchor="middle">Does it run a few times, on a few classes?</text>'
    '<line class="ln" x1="424" y1="125" x2="476" y2="125" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="450" y="118" text-anchor="middle">yes</text>'
    '<rect class="box-ok" x="480" y="100" width="200" height="50" rx="8"/>'
    '<text class="t-s" x="580" y="121" text-anchor="middle">reflection is fine</text>'
    '<text class="t-s t-m" x="580" y="139" text-anchor="middle">unpack at the new house</text>'
    '<line class="ln" x1="220" y1="152" x2="220" y2="176" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="236" y="168" text-anchor="start">no</text>'
    '<rect class="box" x="20" y="180" width="400" height="50" rx="8"/>'
    '<text class="t" x="220" y="210" text-anchor="middle">Does a KSP processor exist for it?</text>'
    '<line class="ln" x1="424" y1="205" x2="476" y2="205" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="450" y="198" text-anchor="middle">yes</text>'
    '<rect class="box-a" x="480" y="180" width="200" height="50" rx="8"/>'
    '<text class="t-s" x="580" y="201" text-anchor="middle">KSP</text>'
    '<text class="t-s t-m" x="580" y="219" text-anchor="middle">the helper writes new cards</text>'
    '<line class="ln" x1="220" y1="232" x2="220" y2="250" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="236" y="246" text-anchor="start">no</text>'
    '<rect class="box-dim" x="20" y="254" width="400" height="40" rx="8"/>'
    '<text class="t-s" x="220" y="279" text-anchor="middle">kapt: a Java processor, run on Java copies of your classes</text>'
    '</svg>'
)

# ---------------------------------------------------------------- opening
OPENING = """Picture moving day itself, with a different person for each kind of job. A helper with a clipboard writes new cards from the labels. A mover opens a box and repacks it. Someone at the new house unpacks a box and checks what's inside. And one older helper reads only labels written in Java, so every label is copied out for that helper first.

Eight lessons have been about the helper with the clipboard, and the last one proved that the helper's cards are right. That leaves the question a newcomer to KSP asks first and an experienced team asks too late: is a processor the right tool for this job at all? The easy trap is to answer from habit, or from a benchmark someone quoted, instead of from the job.

In this lesson, we'll measure generated cards against reflection, find the jobs a processor can't do, port a Java processor to KSP, and meet KSP2 on several platforms at once. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_REFL = """static String reflectionCard(Object thing) throws IllegalAccessException {
    Class<?> type = thing.getClass();
    if (!type.isAnnotationPresent(Inventory.class))
        throw new IllegalArgumentException(type.getSimpleName() + " has no @Inventory");
    StringJoiner pairs = new StringJoiner(", ");
    for (Field field : type.getDeclaredFields()) {
        if (Modifier.isStatic(field.getModifiers()) || field.isSynthetic()) continue;
        field.setAccessible(true);                       // open the box
        pairs.add(field.getName() + "=" + field.get(thing));
    }
    return type.getSimpleName() + ": " + pairs;
}"""
K_REFL = """fun reflectionCard(thing: Any): String {
    val type = thing.javaClass
    require(type.isAnnotationPresent(Inventory::class.java)) { "${type.simpleName} has no @Inventory" }
    val fields = type.declaredFields.filter { !Modifier.isStatic(it.modifiers) && !it.isSynthetic }
    return type.simpleName + ": " + fields.joinToString(", ") { field ->
        field.isAccessible = true                        // open the box
        "${field.name}=${field.get(thing)}"
    }
}"""

S0 = """**Reflection** is a program inspecting its own classes while it runs: finding a class's fields, reading their values, calling methods by name. Lesson 1 wrote MoveMate's card that way, and lesson 7 generated the same card during the build. Lesson 9's playground puts the two side by side, plus a third version that gives reflection its best shot by looking up each class's fields once and keeping them. Here is the plain reflection card:

""" + pair(J_REFL, K_REFL) + """

The generated card is what lesson 7's processor wrote: `MovingDayList.cardFor(thing)`, a `when` with one branch per class and a string template per card. The program `CardTiming` checks correctness first, then measures. It times the first call of each way in a fresh JVM, with the classes the JVM loaded for it, then a million calls of each after a warm-up. On our machine, four cores busy with other builds, it printed:

```text
first call, generated:  34.55 ms, 116 classes loaded -> Lamp: name=desk lamp, bulbs=1, shade=null
first call, reflection:  25.45 ms, 114 classes loaded -> Lamp: name=desk lamp, bulbs=1, shade=null
all three ways agree on all 4 cards: true
generated    119 / 38 / 47 ns per card
reflection   313 / 273 / 267 ns per card
cached       197 / 192 / 178 ns per card
```

And with the first calls the other way round, `-Pargs=reflection-first`:

```text
first call, reflection:  33.17 ms, 136 classes loaded -> Lamp: name=desk lamp, bulbs=1, shade=null
first call, generated:  23.46 ms,  95 classes loaded -> Lamp: name=desk lamp, bulbs=1, shade=null
```

The first calls surprised me. I expected reflection to pay a lot at its first call. It pays a little: in the same position, about 20 more classes and a few more milliseconds. Both ways pay 20 to 35 ms and about a hundred classes for their first card, whichever goes first. The class log says what most of them are: `java.lang.invoke` classes, the machinery the JVM uses to link a string template the first time it runs. The way that goes second still loads about a hundred, so each new kind of template seems to pay for its own. With four small classes, the first call can't tell the two ways apart. The Part 4 capstone showed where start-up does tell. Its container wired a program's objects by reflection, and it loaded more than twice as many classes as the same wiring written out as plain code.

The warm numbers are steady across runs. A generated card costs about 45 ns; reflection's best shot about 190 ns, four times as much; plain reflection about 280 ns, six times. Lesson 1 saw the same gap between its hand-written card and reflection. Either way, it's a fifth of a microsecond. Nobody at the new house waits for that, unless the program prints a million cards.

So reflection is fine for work that runs a few times, on a few classes: a debug screen, a test helper, a small tool reading settings once at start. It also reaches what a processor can't: classes that arrive while the program runs. Generated code wins when the work repeats, and it brings two things the stopwatch doesn't show. A mistake stops the build with a file and line, as in lesson 5, instead of failing on moving day. And programs compiled ahead of time into a single executable need extra setup for every class they reach by reflection, and none for plain code.

**Reflection that runs a few times on a few classes is fine. Generate code when the work repeats, or when a mistake should stop the build.**

In the picture, reflection is unpacking a box at the new house to see what's inside. The picture breaks on the size of the cost: unpacking takes an afternoon, and reflection a fifth of a microsecond. Speed, though, was never the only question. Some jobs aren't cards at all."""

# ---------------------------------------------------------------- section 1
J_NEXT = """// The javac way, the same as KSP's: a new file next to the class, never a change to it
public final class LampCards {
    private LampCards() {}

    public static String inventoryCard(Lamp lamp) {
        return "Lamp: name=" + lamp.getName() + ", bulbs=" + lamp.getBulbs() + ", shade=" + lamp.getShade();
    }
}"""
K_NEXT = """// What a KSP processor can do: a new file next to the class, with an extension function
fun Lamp.inventoryCard(): String = "Lamp: name=$name, bulbs=$bulbs, shade=$shade"

// What it can't do: give Lamp itself a new member. Writing Lamp again is a second Lamp.
data class Lamp(val name: String, val bulbs: Int, val shade: String?) {
    fun inventoryCard(): String = "Lamp: name=$name, bulbs=$bulbs, shade=$shade"
}"""

S1 = """Lesson 1 named KSP's two limits in the docs' words: processors "can't examine expressions or statements, and they can't modify the source code". A newcomer reads that and thinks of a workaround: if a processor can't add a function to `Lamp`, it can write `Lamp` again, with the function inside. `RepackDemo` tries exactly that, and then the way that works:

""" + pair(J_NEXT, K_NEXT) + """

KSP lets the processor write the file, because KSP doesn't check what's in new files. The Kotlin compiler then meets two classes with one name:

```text
=== repack Lamp itself: COMPILATION_ERROR
e: LampExtra.kt:3:12 Redeclaration:
data class Lamp : Any
e: Lamp.kt:6:12 Redeclaration:
data class Lamp : Any
=== add a new card next to it: OK
desk.inventoryCard() returns: Lamp: name=desk lamp, bulbs=1, shade=null
```

That's one lamp too many. A processor's outputs are always new declarations next to yours: an extension function, a builder class, a list. Java's annotation processors have the same limit, which is why the Java twin is a separate `LampCards` class.

Some jobs need the class itself to change. A **compiler plugin** is a jar that the Kotlin compiler loads to change what it writes into class files, and lesson 6 of the Advanced Kotlin track met three. all-open removes `final` from classes a framework must subclass. no-arg adds a constructor that Kotlin code can't see. kotlinx.serialization writes a serializer inside each `@Serializable` class and a `serializer()` function on its companion. No processor can do any of those, because each one changes a class you wrote. In the picture, that's the mover who repacks the box. A plugin can do more, and it costs more to trust: kt-06's whole lesson was that the class you read is not the class the JVM loads.

The ecosystem shows the same line from the other side. Arrow Optics, which generates helpers for reading and copying nested data, still ships a KSP processor, but its docs say "Since version 2.3.0, we recommend using the compiler plug-in". With KSP, "you need to have a companion object declaration in each class, even if it's empty. This is due to limitations in KSP itself": the processor can add functions to a companion, but it can't create the companion. Koin is a library that builds a program's objects and hands them out. Its docs say `koin-ksp-compiler` "is deprecated and will be removed in a future Koin version", and its annotations are now processed by the Koin Compiler Plugin. Kotlin DataFrame deprecated its KSP plugin the same way. All three pages were checked in November 2026.

**If the job is to change a class, it's a compiler plugin's job. If it's to write a new file next to the class, it's KSP's.**

The figure puts the choice in three questions. The last box is for a helper we haven't met properly yet: the one who reads only Java."""

# ---------------------------------------------------------------- section 2
GRADLE_KAPT = """// build.gradle.kts, before: kapt runs a javac processor on Java stubs of your Kotlin classes
plugins {
    kotlin("jvm") version "2.4.21"
    kotlin("kapt") version "2.4.21"
}
dependencies {
    kapt("com.squareup.moshi:moshi-kotlin-codegen:1.15.2")
}
kapt { arguments { arg("movemate.household", "Okafor") } }

// after: KSP reads the Kotlin declarations directly
plugins {
    kotlin("jvm") version "2.4.21"
    id("com.google.devtools.ksp") version "2.3.14"
}
dependencies {
    ksp("com.squareup.moshi:moshi-kotlin-codegen:1.15.2")   // the same artifact serves kapt and KSP
}
ksp { arg("movemate.household", "Okafor") }"""

J_PORT = """// Closest Java equivalent: the given javac processor, Find and Write
for (Element element : roundEnv.getElementsAnnotatedWith(Inventory.class)) { ... }

var slip = processingEnv.getFiler().createResource(StandardLocation.CLASS_OUTPUT, "",
        "META-INF/movemate/packing-slip.txt", classes.toArray(new Element[0]));
try (Writer out = slip.openWriter()) { out.write(text); }"""
K_PORT = """// The KSP port, Find and Write (the Write is given in the lab)
val found = resolver.getSymbolsWithAnnotation(Inventory::class.qualifiedName!!).toList()

codeGenerator.createNewFile(slipDependencies(classes), "META-INF/movemate", "packing-slip", "txt")
    .use { it.write(text.toByteArray()) }"""

S2 = """Java has had annotation processors, programs that javac runs while it compiles, since Java 6, and the Java world has written many of them. KSP is Kotlin's own way to do that job for Kotlin code. Between the two sits **kapt**, Kotlin's bridge to Java's processors. The docs say it "generates stub files from Kotlin source code and then runs the Java annotation processors on those stubs". A **stub** is a Java copy of a Kotlin class's declarations with the bodies emptied out: methods `return null;` or `return 0;`, nullability turned into `@NotNull` annotations, default values gone.

In the picture, kapt is the older helper who reads only Java, so every label in the room is first copied out in Java for that helper. That copying is the slowness. The picture breaks in one place: a person copying labels would keep every word, and stubs lose some, such as default values. The migration guide calls it "expensive" and says it "significantly increases build time". Android's guide adds a detail that matters when you migrate one library at a time: "If a module has any kapt processors remaining, stubs are still generated in that module." The often-quoted "up to 2x faster" comes from the KSP alpha announcement in 2021, where "initial benchmarks with the Room library show that KSP is approximately 2x faster than KAPT". It's one benchmark, from KSP1 days, not a law.

kapt is still the answer for a processor that exists only for Java. Android's Data Binding is one: "KSP support for Data Binding is not planned". When a library ships both, moving to KSP is mostly a change to the build file. The migration guide says: "For most libraries, this replacement is enough":

```kotlin solo
""" + GRADLE_KAPT + """
```

KSP and kapt can run side by side, so a project can move one library at a time. Many libraries ship both processors in one jar: Moshi's codegen jar holds a javac services file, a KSP services file and the Gradle incremental descriptor.

When the library is your own, migrating means porting the processor, and this lesson's lab does exactly that. The Java team's `JavacPackingSlipProcessor` writes `META-INF/movemate/packing-slip.txt`, one line per `@Inventory` class with its room and its fields. You port it to KSP, move by move, until the two outputs match byte for byte. Each javac line has a KSP line:

""" + pair(J_PORT, K_PORT) + """

The rest of the mapping is the same kind of swap. `element.getKind() != ElementKind.CLASS` becomes `classKind != ClassKind.CLASS`, and `messager.printMessage(ERROR, text, element)` becomes `logger.error(text, symbol)`. Fields in source order become the primary constructor's properties. `type.getAnnotation(Room.class)` becomes a `KSAnnotation` and its `arguments`, and `getOptions()` becomes `environment.options`. Two javac ideas have no twin. Claiming an annotation by returning `true` doesn't exist in KSP, where every processor sees every symbol. And Gradle's `aggregating` category for the whole processor becomes `Dependencies(aggregating = true, ...)` on the one output, as in lesson 7.

**Use KSP for every processor that has a KSP version, and keep kapt only for the ones that don't. One kapt processor left in a module keeps the stubs in that module.**

One port detail catches people. Kotlin has a kind of class javac never sees, the `object`, so the port needs an answer for it that the Java processor never needed. KSP's own story, meanwhile, has moved on from the days of that 2021 benchmark."""

ASIDE2 = {
    "title": "Which libraries ship a KSP processor today?",
    "body": "These were checked in November 2026. Room 3.0, Android's database library, is KSP only: \"configuration of annotation processor via KAPT or JavaAP is no longer possible in Room 3.0\", while Room 2.x still supports javac, kapt and KSP. Dagger and Hilt, which wire a program's objects at compile time, say \"Dagger's KSP support is stable as of Dagger 2.60+ and KSP 2.3.9+\", although kotlinlang's own table of libraries still calls Dagger \"Alpha\". kotlin-inject does the same job and has been KSP only since 0.9.0. Moshi's codegen, which writes JSON adapters, serves kapt and KSP from one jar. Tables go stale, so check each library's own docs before you migrate."
}

# ---------------------------------------------------------------- section 3
GRADLE_KMP = """// build.gradle.kts of a multiplatform module: one KSP configuration per target
kotlin {
    jvm()
    js { browser() }
}
dependencies {
    add("kspCommonMainMetadata", project(":processor"))   // the shared code
    add("kspJvm", project(":processor"))                  // the JVM target: task kspKotlinJvm
    add("kspJs", project(":processor"))                   // the JavaScript target: task kspKotlinJs
    // ksp(project(":processor")) here fails the build:
    // The 'ksp' configuration is deprecated in Kotlin Multiplatform projects.
    // Please use target-specific configurations like 'kspJvm' instead.
}"""

S3 = """The KSP in this track is **KSP2**, and it differs from older articles in ways that matter. Since KSP 2.3.0, KSP2 is the only kind: setting `ksp.useKSP2=false` fails the build with "KSP1 is no longer available. Please use KSP2 instead". KSP2 "is no longer a compiler plugin". It runs inside the Gradle daemon, the long-lived Gradle process, so a big project may need more heap there, and KSP's docs suggest settings such as `org.gradle.jvmargs=-Xmx4096M`. Its version number is no longer tied to Kotlin's: this track builds with Kotlin 2.4.21 and KSP 2.3.14. A version written like `2.2.21-2.0.5`, Kotlin's number and then KSP's, is the old scheme. The API moved too. KSP 2.3.12 deprecated `KSVisitorVoid()` and `validate()` without arguments, the spelling of the official quickstart, and 2.3.14 added the `apiFeatures` property that every lab in this track overrides.

The last setting is several houses at once. **Kotlin Multiplatform** is one project compiled for several platforms, such as the JVM, JavaScript and native code, from shared code and code for each platform. Each platform is a **target**, and each target compiles separately. So KSP runs once per target, with a task and a configuration each:

```kotlin solo
""" + GRADLE_KMP + """
```

The plain `ksp(...)` configuration is right in the single-platform builds of this track. In a multiplatform module it's an error since KSP 2.3.12: you name the targets that need the processor. Each target's output goes to its own folder, such as `build/generated/ksp/jvm/jvmMain/kotlin`. A class in the shared code gets its card once per target: a run with a JVM and a JavaScript target wrote one in each of `metadata/commonMain`, `jvm/jvmMain` and `js/jsMain`. Koin names "a KSP configuration per Kotlin Multiplatform target" among its reasons for moving to a compiler plugin.

In the picture, it's a family moving into two houses on the same day. Each house gets its own helper, its own pass through the boxes, and its own set of cards, even for the boxes both houses share. The picture breaks only in the counting: in a build, the shared boxes are read once more for the shared code itself.

**In a multiplatform module, add the processor to each target that needs it. Plain `ksp(...)` is for single-platform modules.**

That's the last piece of the toolbox. What's left is to use it on a job big enough to need all of it."""

# ---------------------------------------------------------------- closing
CLOSING = """We started with moving day and a person for each kind of job. The measurements said reflection is fine for a few cards and generated code wins when the work repeats. A processor that tried to repack a box met a second Lamp, kapt turned out to be a photocopier, and the port matched javac byte for byte.

In your own build, list every `kapt(` line, and check each library's docs for a KSP artifact.

Next, in this part's capstone, the helper writes the moving-day plan the night before: code that builds a program's objects and hands each one what its constructor asks for, generated at compile time. Who works out that the route comes before the driver, and the driver before the truck?"""

L = {
 "id": "ksp-09",
 "title": "Choosing the tool: KSP, reflection, kapt or a compiler plugin",
 "minutes": 40,
 "goal": "By the end you can choose between reflection, a KSP processor, a compiler plugin and kapt for a job, with evidence; move a library from kapt to KSP in Gradle; port a javac processor to KSP move by move; and set up KSP in a multiplatform module.",
 "opening": OPENING,
 "warmup": {
  "q": "You want every `@Inventory` class to get a member function `inventoryCard()` inside the class, so Java callers can write `lamp.inventoryCard()`. Which tool can do it?",
  "options": ["A KSP processor that writes the class again with the function inside", "A KSP processor that writes an extension function", "A compiler plugin", "kapt, because Java processors can add methods"],
  "answer": 2,
  "why": "A member inside the class means changing a class you wrote, and only a compiler plugin changes what the compiler writes for your classes. A processor that writes the class again gets a `Redeclaration` error, as section 2 shows. An extension function works from Kotlin and compiles to a static method that Java calls as `LampInventoryCardKt.inventoryCard(lamp)`, not as a member. Java processors have the same limit as KSP."
 },
 "sections": [
  {
   "h": "Reflection or generated cards: what the numbers say",
   "body": S0,
   "try": {
    "title": "Time the cards, both ways round",
    "minutes": 4,
    "steps": [
     "From `labs/`, run `CardTiming` with the command below. Before you look, write down which first call you expect to be slower.",
     "Run it again with `-Pargs=reflection-first`. Which numbers moved with the order, and which stayed with the way?",
     "Run the Java twin, `CardTimingJava`, once. It calls the cards KSP generated in Kotlin, through `MovingDayList.INSTANCE`."
    ],
    "code": timing_code(),
    "expect": "Every run prints `all three ways agree on all 4 cards: true`. The first calls cost tens of milliseconds and about a hundred classes each; reflection loads about 20 more than the generated card in the same position (on our run, 136 against 116 when first, 114 against 95 when second). After warm-up, the generated card takes roughly 40 to 70 ns, the cached reflection card roughly 160 to 250 ns, and plain reflection roughly 220 to 400 ns. Your numbers will differ, and the ratios should not move much."
   },
   "refs": [{"title": "KSP overview (Kotlin docs)", "url": "https://kotlinlang.org/docs/ksp-overview.html", "kind": "docs"}]
  },
  {
   "h": "Jobs a helper can't do: when the class itself must change",
   "body": S1,
   "figure": {"svg": FIG, "caption": "Three questions pick the tool: change a class, a compiler plugin; a few times on a few classes, reflection; a KSP processor exists, KSP; otherwise kapt."},
   "try": {
    "title": "Repack a box, then write a card next to it",
    "minutes": 3,
    "steps": [
     "Run `RepackDemo`. Read both errors: which files do they name, and at which lines?",
     "Open `labs/ksp/build/kctfork/demo/l09-repack/ksp/sources/kotlin/movemate/LampExtra.kt`. The second compile cleared the folder, so it holds the extension function. Which line would a Java caller write to call it?"
    ],
    "code": kdemo("RepackDemo"),
    "expect": "Repacking fails with `COMPILATION_ERROR` and two `Redeclaration:` errors, one in the generated `LampExtra.kt` at 3:12 and one in your `Lamp.kt` at 6:12. The extension compiles and prints `desk.inventoryCard() returns: Lamp: name=desk lamp, bulbs=1, shade=null`. A Java caller writes `LampExtraKt.inventoryCard(desk)`: the extension is a static method of the file's class, and `Lamp` itself still has no member."
   },
   "refs": [{"title": "Arrow: setup, the compiler plug-in and the KSP plugin", "url": "https://arrow-kt.io/learn/quickstart/setup/", "kind": "docs"},
            {"title": "Koin Annotations with KSP (Koin docs)", "url": "https://insert-koin.io/docs/setup/annotations-ksp", "kind": "docs"}]
  },
  {
   "h": "When the only helper reads Java: kapt, and moving a library to KSP",
   "body": S2,
   "aside": ASIDE2,
   "try": {
    "title": "Compare the port's slip with javac's",
    "minutes": 4,
    "steps": [
     "Read `JavacPackingSlipProcessor.java`, the Java twin below. Find its four moves.",
     "Run `PortDemo`. It runs the reference KSP port on Kotlin twins of the four classes and prints its slip next to the one javac wrote for the Java twins.",
     "Open `labs/ksp/src/test/resources/workbench/ksp/l09/java-twins.txt` to see how javac's slip was made. Once your port passes the lab, run `PortDemo` with `-Pmine=l09`."
    ],
    "code": port_code(),
    "expect": "Both slips read `# Okafor packing slip. Generated, do not edit.`, then `Bookshelf [study]: shelves, books`, `Box [hall]: label, room, weightGrams, fragile`, `Lamp [living room]: name, bulbs, shade` and `Plant [no room]: kind, potLitres, waterEveryDays`, and the last line is `--- the same, byte for byte: true`. With an unfinished port, the demo prints `w: [ksp] l09 not done yet: ...`, `(nothing yet)` and `false`."
   },
   "refs": [{"title": "Migrate from kapt to KSP (Kotlin docs)", "url": "https://kotlinlang.org/docs/ksp-kapt-migration.html", "kind": "docs"},
            {"title": "Migrate from kapt to KSP (Android Developers)", "url": "https://developer.android.com/build/migrate-to-ksp", "kind": "docs"}]
  },
  {
   "h": "Several houses at once: KSP2, versions and multiplatform",
   "body": S3,
   "refs": [{"title": "KSP with Kotlin Multiplatform (Kotlin docs)", "url": "https://kotlinlang.org/docs/ksp-multiplatform.html", "kind": "docs"},
            {"title": "KSP2 introduction (google/ksp docs)", "url": "https://github.com/google/ksp/blob/main/docs/ksp2.md", "kind": "docs"}]
  }
 ],
 "compare": {
  "title": "The packing slip processor: the javac original and its KSP port, move by move",
  "java": {"title": "JavacPackingSlipProcessor.java (excerpt)", "src": "// The given javac processor (javax.annotation.processing)\n@SupportedAnnotationTypes(\"workbench.ksp.annotations.Inventory\")\n@SupportedOptions(\"movemate.household\")\npublic class JavacPackingSlipProcessor extends AbstractProcessor {\n    private boolean slipWritten = false;\n\n    @Override\n    public boolean process(Set<? extends TypeElement> annotations, RoundEnvironment roundEnv) {\n        if (slipWritten || roundEnv.processingOver()) return false;\n        String household = processingEnv.getOptions().getOrDefault(\"movemate.household\", \"MoveMate\");\n        List<TypeElement> classes = new ArrayList<>();\n        for (Element element : roundEnv.getElementsAnnotatedWith(Inventory.class)) {   // 1. Find\n            if (element.getKind() != ElementKind.CLASS) {                                  // 2. Check\n                messager.printMessage(Diagnostic.Kind.ERROR, \"@Inventory goes on a class, but ...\", element);\n                continue;\n            }\n            classes.add((TypeElement) element);\n        }\n        // 3. Read: slipLine(type) reads the fields and @Room\n        // 4. Write: filer.createResource(CLASS_OUTPUT, \"\", \"META-INF/movemate/packing-slip.txt\", elements)\n        slipWritten = true;\n        return false;                                   // claim nothing\n    }\n}"},
  "kotlin": {"title": "PackingSlipProcessor.kt (the given part)", "src": "class PackingSlipProcessor(\n    private val codeGenerator: CodeGenerator,\n    private val logger: KSPLogger,\n    private val options: Map<String, String>,\n) : SymbolProcessor {\n    override val apiFeatures = buildApiFeatures { enableBackingFields = true; enableContextParameters = true }\n    private var slipWritten = false\n\n    fun processSlip(resolver: Resolver): List<KSAnnotated> {\n        if (slipWritten) return emptyList()                       // javac: if (slipWritten || processingOver())\n        val household = options[HOUSEHOLD] ?: \"MoveMate\"          // javac: getOptions().getOrDefault(...)\n        val classes = findInventory(resolver)                     // 1. Find\n            .mapNotNull { checkKind(it, logger) }                  // 2. Check\n            .sortedBy { it.simpleName.asString() }\n        if (classes.isEmpty()) return emptyList()\n        val lines = classes.map(::slipLine)                       // 3. Read\n        val text = \"# $household packing slip. Generated, do not edit.\\n\" + lines.joinToString(\"\") { \"$it\\n\" }\n        codeGenerator.createNewFile(slipDependencies(classes), \"META-INF/movemate\", \"packing-slip\", \"txt\")\n            .use { it.write(text.toByteArray()) }                 // 4. Write\n        slipWritten = true\n        return emptyList()                                        // deferred symbols: none\n    }\n}"},
  "note": "The two processors make the same moves in the same order, which is what makes a port a matter of swapping lines rather than redesigning. The differences are in the contract around them. javac creates the processor with a no-argument constructor and calls `process` with the annotations it may claim; returning `true` claims them, and KSP has no claiming at all. KSP creates the processor through a provider and gets back a list of symbols to defer, which javac has no word for. javac runs one more, empty round with `processingOver()` true; KSP calls `finish()` instead. And the incremental category moves from the processor (Gradle's descriptor file) to the output (`Dependencies`)."
 },
 "worked": {
  "title": "Pick the tool for MoveMate's next four jobs",
  "steps": [
   {"say": "Job 1: a debug screen that prints every field of whatever object a tester taps, a few times a day. It runs rarely and must work for classes nobody annotated. Reflection is fine, and a processor would only add a module and a test suite.",
    "code": "static String debugPrint(Object thing) throws IllegalAccessException {\n    StringJoiner parts = new StringJoiner(\", \", thing.getClass().getSimpleName() + \"(\", \")\");\n    for (Field f : thing.getClass().getDeclaredFields()) {\n        if (Modifier.isStatic(f.getModifiers())) continue;\n        f.setAccessible(true);\n        parts.add(f.getName() + \"=\" + f.get(thing));\n    }\n    return parts.toString();\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "fun debugPrint(thing: Any): String =\n    thing.javaClass.declaredFields\n        .filter { !Modifier.isStatic(it.modifiers) }\n        .onEach { it.isAccessible = true }\n        .joinToString(\", \", \"${thing.javaClass.simpleName}(\", \")\") { \"${it.name}=${it.get(thing)}\" }"},
   {"say": "Job 2: save every box to a file as JSON and read it back, thousands of times a day. The serializer belongs inside each class, with a `serializer()` function on its companion: that changes classes you wrote, so it's the kotlinx.serialization compiler plugin from the Advanced Kotlin track. In Java you'd reach for a library that reads annotations by reflection.",
    "code": "@Serializable\ndata class Box(val label: String, val room: String, val weightGrams: Int, val fragile: Boolean = false)\n\nval json = Json.encodeToString(Box(\"books\", \"study\", 12_000))  // the plugin wrote Box's serializer", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "// Java's usual approach: a JSON library such as Jackson, which reads the class by reflection\nString json = new ObjectMapper().writeValueAsString(new Box(\"books\", \"study\", 12_000, false));"},
   {"say": "Job 3: wire the moving-day crew, where each class asks for what it needs in its constructor, and a missing part should stop the build. The wiring is new code next to your classes, written from their constructors: a KSP processor, and the next capstone builds it.",
    "code": "class Truck @Inject constructor(val driver: Driver)   // the processor writes a factory for Truck\n// and a component that builds Driver before Truck, checked during the build", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "public class Truck {\n    private final Driver driver;\n\n    @Inject\n    public Truck(Driver driver) { this.driver = driver; }   // a javac processor writes the factory\n}"},
   {"say": "Job 4: a module uses a processor that exists only as a javac processor, with no KSP artifact. Keep it on kapt for now, move every other library in the module to `ksp(...)`, and remember that the stubs stay until the last kapt processor leaves the module.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Port a javac annotation processor to KSP",
  "minutes": 15,
  "files": [f"{lab}/main/kotlin/workbench/ksp/l09/PackingSlipProcessor.kt", f"{lab}/main/java/workbench/ksp/l09/JavacPackingSlipProcessor.java", f"{lab}/test/resources/workbench/ksp/l09/javac-packing-slip.txt", f"{lab}/test/resources/workbench/ksp/l09/java-twins.txt"],
  "run": "./gradlew :ksp:test --tests 'workbench.ksp.l09.*'",
  "steps": [
   "Read `JavacPackingSlipProcessor.java`: the Java team's processor, given and read-only. Its `process` method makes four moves, and `java-twins.txt` shows the Java classes javac ran it on and the command. `javac-packing-slip.txt` is what it wrote: your target, byte for byte.",
   "Read `PackingSlipProcessor.kt`. The provider, `apiFeatures`, the `process` wrapper and `processSlip` are given, in the same order as the Java `process`, and each comment names the javac line it replaces. Four functions are yours, one per move.",
   "Run the tests: all five fail. Run `./gradlew :ksp:app:kspL09Kotlin -Pmine=l09`: your port already runs in the real build and warns `w: [ksp] l09 not done yet: 1. Find: ...`.",
   "1. Find: write `findInventory`, the KSP line for `roundEnv.getElementsAnnotatedWith(Inventory.class)`.",
   "2. Check: write `checkKind`. A class passes; anything else gets `logger.error` on the symbol with the javac processor's words, `@Inventory goes on a class, but Shape is an interface`, plus one kind javac never sees: `Van is an object`.",
   "3. Read: write `slipLine`. javac read the fields in source order and `getAnnotation(Room.class)`; you read the primary constructor's properties in order, and the `name` argument of the `@Room` annotation. Check `shortName` first, then resolve the annotation type to be sure.",
   "4. Write: write `slipDependencies`, aggregating, with the file of every class on the slip: the KSP form of the originating elements and of Gradle's `aggregating` category.",
   "5. Prove: run the tests until all five pass. Run `PortDemo` with `-Pmine=l09` and look for `byte for byte: true`. Then run `./gradlew :ksp:app:kspL09Kotlin -Pmine=l09`, open `labs/ksp/app/build/generated/ksp/l09/resources/META-INF/movemate/packing-slip.txt`, and print it from the class path with `./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l09.PackingSlipKt -Pmine=l09`.",
   "From memory: close both files and write, on paper, the KSP line for each of these javac calls: `getElementsAnnotatedWith`, `printMessage(ERROR, text, element)`, `getAnnotation(Room.class).name()`, `getOptions().get(key)` and `createResource(...)`. The drill below has the answer."
  ],
  "hints": [
   "`Inventory::class.qualifiedName!!` gives the full name that `getSymbolsWithAnnotation` needs; the short name finds nothing.",
   "`ClassKind.INTERFACE`, `ENUM_CLASS`, `ANNOTATION_CLASS` and `OBJECT` match the Java processor's `kindWords` when you use the same words: an interface, an enum, an annotation, and an object for the new one.",
   "`cls.primaryConstructor?.parameters.orEmpty().filter { it.isVal || it.isVar }` gives the properties in order. For `@Room`: `annotations.firstOrNull { ... }?.arguments?.firstOrNull { it.name?.asString() == \"name\" }?.value as String?`.",
   "The first test compares bytes: a missing trailing newline or an extra space fails it. `processSlip` already writes the header and one `\\n` per line; `slipLine` returns the line without its newline.",
   "If the test that expects `Shape.kt:6` fails, check that the error is logged on the symbol, not without one: a message without a symbol has no file and line."
  ],
  "done_when": "All five tests in `PackingSlipProcessorTest` pass, and `PortDemo -Pmine=l09` prints `the same, byte for byte: true`."
 },
 "drill": {
  "title": "Port five javac lines from memory",
  "minutes": 4,
  "prompt": "Close this page. Write the KSP line for each javac line: (1) `roundEnv.getElementsAnnotatedWith(Inventory.class)`, (2) `messager.printMessage(Diagnostic.Kind.ERROR, text, element)`, (3) `type.getAnnotation(Room.class).name()`, (4) `processingEnv.getOptions().get(\"movemate.household\")`, (5) `filer.createResource(StandardLocation.CLASS_OUTPUT, \"\", \"META-INF/movemate/packing-slip.txt\", elements)`. Which javac idea has no KSP line at all?",
  "answer": {"lang": "kotlin", "src": "// 1. Find\nresolver.getSymbolsWithAnnotation(\"workbench.ksp.annotations.Inventory\")\n// 2. Check\nlogger.error(text, symbol)\n// 3. Read an annotation argument\ncls.annotations.first { it.shortName.asString() == \"Room\" }\n    .arguments.first { it.name?.asString() == \"name\" }.value as String\n// 4. Options\nenvironment.options[\"movemate.household\"]\n// 5. Write a resource, aggregating, from every class's file\ncodeGenerator.createNewFile(Dependencies(true, *files), \"META-INF/movemate\", \"packing-slip\", \"txt\")\n// no KSP line: claiming an annotation by returning true from process()",
             "alt": {"lang": "java", "title": "JavacLines.java", "src": "// The javac lines being ported\nroundEnv.getElementsAnnotatedWith(Inventory.class);                                // 1. Find\nmessager.printMessage(Diagnostic.Kind.ERROR, text, element);                         // 2. Check\nString room = type.getAnnotation(Room.class).name();                                 // 3. Read\nString household = processingEnv.getOptions().get(\"movemate.household\");           // 4. Options\nfiler.createResource(StandardLocation.CLASS_OUTPUT, \"\",\n        \"META-INF/movemate/packing-slip.txt\", elements);                             // 5. Write\nreturn true;   // claims @Inventory: KSP has no such thing"}}
 },
 "recap": [
  "Reflection inspects classes while the program runs. For four cards, its first call costs about as much as a generated card's, and each warm card about four to six times as much (some 190 to 280 ns against 45 ns here). It's fine for work that runs a few times on a few classes.",
  "Generated code wins when the work repeats or a mistake should stop the build, and it needs no reflection setup in programs compiled ahead of time.",
  "A processor only adds new files; writing a class again is a `Redeclaration` error. Jobs that change your classes (all-open, no-arg, kotlinx.serialization) belong to compiler plugins, and Arrow Optics, Koin and DataFrame now steer users from their KSP processors to plugins.",
  "kapt runs Java-only processors on Java stubs of your classes, and the stubs are the cost. Swap `kapt(...)` for `ksp(...)` wherever a library ships a KSP processor, and keep kapt for the rest; one kapt processor keeps stubs in its module.",
  "KSP2 is the only KSP since 2.3.0: not a compiler plugin, run in the Gradle daemon, versioned apart from Kotlin. In a multiplatform module, add the processor per target (`kspJvm`, `kspJs`, `kspCommonMainMetadata`); plain `ksp(...)` is an error.",
  "The limit: no tool covers every job. KSP can't change a class, a compiler plugin changes it out of sight, reflection checks nothing until it runs, and kapt is slow."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "A settings screen reads a `@MenuEntry` annotation on 12 classes once when the program starts, to build a menu. Which tool fits best?",
   "options": ["A KSP processor that generates the menu", "Reflection while the program runs", "A compiler plugin that adds a `label()` member to each class", "kapt, because the annotation is read at start-up"],
   "answer": 1, "why": "Twelve classes, once at start: a few milliseconds and a few dozen classes loaded, which nobody notices. A processor would add a module, a test suite and build time for no visible gain. The annotation needs `RUNTIME` retention for this, as `@Inventory` has, so it's still there while the program runs."},
  {"q": "A library needs each annotated class to gain a `companion object` with generated functions on it. What does KSP let it do?",
   "options": ["Generate the companion object in a new file", "Add functions to a companion only if the user already wrote one, even an empty one", "Nothing: KSP can't see companions", "Generate a second class with the same name that contains the companion"],
   "answer": 1, "why": "A processor can write extension functions on an existing companion, in a new file, but it can't add the companion to your class: that changes the class. That's why Arrow Optics' KSP version needs \"a companion object declaration in each class, even if it's empty\", and why Arrow now recommends its compiler plugin. A second class with the same name is a `Redeclaration` error."},
  {"q": "A module uses Moshi's codegen and one Java-only processor through kapt. You move Moshi to `ksp(...)`. What happens to the stubs?",
   "options": ["They are no longer generated", "They are still generated, because one kapt processor remains in the module", "KSP generates them instead", "They are generated only for Moshi's classes"],
   "answer": 1, "why": "kapt makes Java stubs for the whole module whenever it runs any processor there. Android's guide: \"If a module has any kapt processors remaining, stubs are still generated in that module.\" The build gets fast only when the last kapt processor leaves."},
  {"q": "In a Kotlin Multiplatform module with a JVM and a JavaScript target, someone writes `ksp(project(\":processor\"))`. What happens with KSP 2.3.14?",
   "options": ["KSP runs on every target", "KSP runs on the JVM target only", "The build fails: use target configurations such as `kspJvm` and `kspJs`", "KSP runs only on the shared code"],
   "answer": 2, "why": "Since KSP 2.3.12 the plain configuration is an error in multiplatform modules: \"The 'ksp' configuration is deprecated in Kotlin Multiplatform projects. Please use target-specific configurations like 'kspJvm' instead.\" Each target has its own KSP task, such as `kspKotlinJvm`."},
  {"q": "From the Advanced Kotlin track: a framework must subclass your Kotlin classes to wrap their methods. Which tool removes `final` from them?",
   "options": ["A KSP processor", "The all-open compiler plugin", "kapt", "Reflection at start-up"],
   "answer": 1, "why": "all-open changes what the compiler writes for marked classes: no `final` on the class or its members. A processor can't change an existing class, kapt only runs Java processors, and reflection can't make a final class subclassable.",
   "from": "kt-06"}
 ],
 "flashcards": [
  {"front": "When is reflection the right tool instead of a processor?", "back": "When the work runs a few times on a few classes, or the classes arrive while the program runs: a debug screen, a test helper, settings read once at start."},
  {"front": "Generated card against reflection card, once warm: roughly how far apart?", "back": "On this course's loaded machine, about 45 ns against about 190 ns cached and 280 ns plain: four to six times. The first calls were close."},
  {"front": "What happens when a processor writes a class with the same name as one of yours?", "back": "The compiler reports `Redeclaration:` in both files. A processor can only add new declarations, never change yours."},
  {"front": "Which kind of job needs a compiler plugin rather than KSP?", "back": "One that must change a class you wrote: remove `final` (all-open), add a constructor (no-arg), or add a serializer inside it (kotlinx.serialization)."},
  {"front": "What does kapt do, and why is it slow?", "back": "It writes Java stubs of your Kotlin classes, then runs Java annotation processors on them. Writing the stubs is the cost."},
  {"front": "How do you move a library from kapt to KSP in Gradle?", "back": "Apply `com.google.devtools.ksp`, replace `kapt(...)` with `ksp(...)` and `kapt { arguments { ... } }` with `ksp { arg(...) }`, and remove the kapt plugin when no kapt processor is left."},
  {"front": "How do you add a KSP processor in a multiplatform module?", "back": "Per target: `add(\"kspJvm\", ...)`, `add(\"kspJs\", ...)`, `add(\"kspCommonMainMetadata\", ...)`. Plain `ksp(...)` is a build error since KSP 2.3.12."}
 ],
 "terms": [
  {"term": "Reflection", "plain": "A program inspecting its own classes while it runs: their fields, values and methods."},
  {"term": "Compiler plugin", "plain": "A jar the Kotlin compiler loads to change what it writes into class files, for example all-open."},
  {"term": "kapt", "plain": "Kotlin's bridge to Java annotation processors: it writes Java stubs of Kotlin classes and runs the processors on them."},
  {"term": "Stub", "plain": "A Java copy of a Kotlin class's declarations, with empty bodies, made only for Java processors to read."},
  {"term": "KSP2", "plain": "The current KSP, the only one since 2.3.0: not a compiler plugin, run in the Gradle daemon."},
  {"term": "Kotlin Multiplatform", "plain": "One project compiled for several platforms, such as the JVM and JavaScript, from shared and per-platform code."},
  {"term": "Target", "plain": "One platform a multiplatform project compiles for, with its own compilation and its own KSP task."}
 ],
 "explain_back": {
  "prompt": "A colleague says: \"KSP is up to twice as fast as everything, so let's generate code for all our reflection and move every annotation library to KSP.\" Explain what you'd agree with, what you'd push back on, and how you'd decide each case.",
  "answer": "The \"up to 2x\" is a 2021 Room benchmark of KSP against kapt, so it's about build time, and it compares two ways of running processors, not KSP with reflection. I'd agree with moving every library that ships a KSP processor from kapt to KSP: kapt writes Java stubs of every class in the module, and one kapt processor left keeps them there. I'd keep kapt only for processors that exist just for Java. On reflection I'd decide case by case. Our measurement showed a generated card is four to six times faster once warm, but that's a fifth of a microsecond, and the first calls were close. A debug screen or a settings read once at start doesn't need a processor and its module and tests. Code that runs constantly, or where a mistake should fail the build, is worth generating. And some jobs can't be done by KSP at all: anything that must change a class we wrote, like adding a member or removing `final`, needs a compiler plugin."
 },
 "deeper": {
  "minutes": 8,
  "body": "Why are the first calls so close? Each first card makes the JVM link the card's string template: Kotlin compiles a template to a call through `java.lang.invoke`, and the JVM builds the code for each new kind of template the first time it runs. In the class log of the generated run, most of the hundred-odd classes loaded around the first card were `java.lang.invoke` classes, and reflection's first card needs the same machinery for its own templates, plus about twenty classes for reading annotations and fields. On a real program, reflection's start-up cost grows with the number of classes it inspects and with the libraries it drags in, which is what the Part 4 capstone measured.\n\nMoshi offers both paths in one library and says when to pick which: \"Prefer codegen for better performance and to avoid the kotlin-reflect dependency; prefer reflection to convert both private and protected properties.\" Its reflection adapter depends on `kotlin-reflect`, \"a 2.5 MiB .jar file\". This course's reflection cards avoid that by using plain Java reflection, which works for Kotlin classes because they compile to ordinary JVM classes, but sees only JVM facts: fields and their order, not Kotlin's nullability or default values.\n\nThe ecosystem moves both ways at once, and the reasons are the same picture. Libraries whose job is new code next to yours (Room's database code, Dagger's factories, kotlin-inject's components) went KSP-first or KSP-only. Libraries whose job is to change or extend your classes from the inside (Koin's wiring rewrites calls such as `single<UserRepository>()`, Arrow Optics needs companions, DataFrame adds properties) moved to compiler plugins, which also skip the per-target KSP configurations of multiplatform modules. Before you pick a library, read which of the two it has become."
 },
 "sources": [
  {"title": "Migrate from kapt to KSP (Kotlin docs)", "url": "https://kotlinlang.org/docs/ksp-kapt-migration.html"},
  {"title": "Migrate from kapt to KSP (Android Developers)", "url": "https://developer.android.com/build/migrate-to-ksp"},
  {"title": "KSP with Kotlin Multiplatform (Kotlin docs)", "url": "https://kotlinlang.org/docs/ksp-multiplatform.html"},
  {"title": "Announcing Kotlin Symbol Processing (Android Developers Blog, 2021)", "url": "https://android-developers.googleblog.com/2021/02/announcing-kotlin-symbol-processing-ksp.html"},
  {"title": "Koin Annotations with KSP (Koin docs)", "url": "https://insert-koin.io/docs/setup/annotations-ksp"}
 ]
}
out = ROOT / "content/lessons/ksp-09.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
