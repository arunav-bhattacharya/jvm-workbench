import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/kotlin/src"
P = "kotlin/workbench/kotlin/l06"
DK = "kotlin/workbench/kotlin/l06/demo"
DJ = "java/workbench/kotlin/l06/demo"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :kotlin:demo -Pmain=workbench.kotlin.l06.demo."


def demo(name):
    """Kotlin demo with its runnable Java twin."""
    return {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{DK}/{name}.kt"),
            "run": RUN + name + "Kt", "file": f"{lab}/demo/{DK}/{name}.kt",
            "alt": {"lang": "java", "title": f"{name}Java.java", "src": read(f"{lab}/demo/{DJ}/{name}Java.java"),
                    "run": RUN + name + "Java", "file": f"{lab}/demo/{DJ}/{name}Java.java"}}


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


FIG = (
    '<svg viewBox="0 0 680 270" role="img" aria-label="Three compiler plugins and what each changes in the class file: all-open removes final, no-arg adds a hidden zero-argument constructor, serialization adds a generated serializer class">'
    '<text class="t-s t-m" x="165" y="28" text-anchor="middle">your source</text>'
    '<text class="t-s t-m" x="515" y="28" text-anchor="middle">what the plugin writes into the class file</text>'
    '<rect class="box-a" x="20" y="44" width="290" height="44" rx="8"/>'
    '<text class="t-s t-code" x="165" y="71" text-anchor="middle">@OpenForProxies class PrintQueue</text>'
    '<line class="ln" x1="314" y1="66" x2="362" y2="66" marker-end="url(#arr)"/>'
    '<rect class="box-ok" x="370" y="44" width="290" height="44" rx="8"/>'
    '<text class="t-s t-code" x="515" y="71" text-anchor="middle">public class PrintQueue (no final)</text>'
    '<rect class="box-a" x="20" y="108" width="290" height="44" rx="8"/>'
    '<text class="t-s t-code" x="165" y="135" text-anchor="middle">@NoArgEntity class JobRow(val id: String)</text>'
    '<line class="ln" x1="314" y1="130" x2="362" y2="130" marker-end="url(#arr)"/>'
    '<rect class="box-ok" x="370" y="108" width="290" height="44" rx="8"/>'
    '<text class="t-s t-code" x="515" y="135" text-anchor="middle">+ public JobRow(), hidden from Kotlin</text>'
    '<rect class="box-a" x="20" y="172" width="290" height="44" rx="8"/>'
    '<text class="t-s t-code" x="165" y="199" text-anchor="middle">@Serializable class Queued(...)</text>'
    '<line class="ln" x1="314" y1="194" x2="362" y2="194" marker-end="url(#arr)"/>'
    '<rect class="box-ok" x="370" y="172" width="290" height="44" rx="8"/>'
    '<text class="t-s t-code" x="515" y="199" text-anchor="middle">+ Queued$$serializer, serializer()</text>'
    '<text class="t-s t-m" x="340" y="252" text-anchor="middle">all three run inside kotlinc; KSP and kapt generate new source files instead</text>'
    '</svg>'
)

# ---------------------------------------------------------------- opening
OPENING = """Picture the print shop's print line, where a job goes in as a file and comes out as paper. On the way, machines change every job that passes. One takes off the shrink-wrap so that a cover sheet can go in front, one adds a blank form at the back, one clips on a slip that describes the job. Each acts on a note on the job's ticket.

The Kotlin compiler has a line like that, and compiler plugins are its machines. You mark a class with an annotation, a label that tools can read. A plugin then changes what the compiler writes for it: it takes away a `final`, adds a constructor, or writes a whole new class. The trap is that your source shows none of it: the class you read is not the class the JVM loads.

In the last lesson, contracts told the compiler facts; now plugins change what it writes. We'll open classes for frameworks that subclass them, add an empty constructor for frameworks that fill objects in later, write JSON with a serializer nobody typed, and meet tools that write source files instead. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_FINAL = """class LoggedPrintQueue extends PrintQueue {      // error: cannot inherit from final PrintQueue
    @Override public String print(String job) { return super.print(job); }
}"""
K_FINAL = """class TimedPrintQueue : PrintQueue() {             // error: this type is final, so it cannot be extended.
    override fun print(job: String): String =      // error: 'print' in 'PrintQueue' is final
        super.print(job)                           //        and cannot be overridden.
}"""
K_GRADLE = """// labs/kotlin/build.gradle.kts (the version, 2.4.21, is set once in the root build file)
plugins {
    kotlin("plugin.allopen")
    kotlin("plugin.noarg")
    kotlin("plugin.serialization")
}

allOpen { annotation("workbench.kotlin.OpenForProxies") }
noArg { annotation("workbench.kotlin.NoArgEntity") }"""

S0 = """Many libraries add behavior to your classes without touching your source. A **framework** is a library that calls your code, rather than the other way round. Many frameworks do it with a **proxy**: a class they generate that extends yours and overrides each method. The override does some work before and after calling your original through `super`. A timing proxy starts a clock, calls your method, and writes down how long it took. Write such a subclass by hand for the shop's `PrintQueue`, and the problem shows at once:

""" + pair(J_FINAL, K_FINAL) + """

Kotlin classes and their members are final unless you write `open`: nobody may extend them or override their methods. That default is a good one, because a class then behaves exactly as its author wrote it. But a framework that generates subclasses hits the same wall as your hand-written one, only later, while the program starts. You could write `open` on every class and every method a framework touches, and nobody keeps that up for long.

On the print line, a final class is a job that arrives shrink-wrapped and ready to ship. Nobody can slip a cover sheet in front of it.

A **compiler plugin** is a jar (the zip file a Java library ships in) that the Kotlin compiler loads to change what it writes into class files. The **all-open** plugin "makes classes and their members open at compile time without requiring the open keyword". It does that for every class that carries an annotation you name in the build, or whose superclass does. It's the machine that takes the shrink-wrap off every job with the right note on its ticket. This lab module names `workbench.kotlin.OpenForProxies` for all-open, and a second marker for the plugin of the next section:

```kotlin solo
""" + K_GRADLE + """
```

`javap` on the demo's `PrintQueue` then shows `public class` and `public java.lang.String print(java.lang.String)`, with no `final` in sight. What the plugin leaves alone matters just as much. Private members stay private, the field behind `traySize` stays `private final`, and the unmarked `PlainHelper` stays `public final class`. The plugin matches the annotation by its full name, package included, so an annotation with the same simple name in another package does nothing at all.

**An annotation is only a note on the ticket. A plugin named in the build is what acts on it.**

The figure puts the three plugins of this lesson side by side. Each one reads an annotation while the code compiles, and each one changes the class file in its own way: it removes a modifier, adds a constructor, or adds a whole class. The second machine is for frameworks with a different need."""

ASIDE0 = {
    "title": "Which annotations does my framework need?",
    "body": "Real frameworks come with presets, ready-made lists of annotations. `kotlin-spring` is all-open with the annotations of Spring, a widely used Java framework for web services, already listed: `@Component`, `@Transactional` and a few more. Presets can lag behind their framework, though. In the Kotlin 2.4.21 plugin, the `quarkus` preset still lists only the old `javax.enterprise.context` annotations. Quarkus 3, another framework for services, uses `jakarta.enterprise.context`, so a class marked with the new name stays final. Whatever your framework, name the annotations it needs yourself in `allOpen { annotation(...) }`, and check one class with `javap` after every change to the build.",
}

# ---------------------------------------------------------------- section 1
J_NOARG = """public class JobRow {
    private String id;
    private int pages;
    private String status = "NEW";

    protected JobRow() { }                          // for the database library
    public JobRow(String id, int pages) { this.id = id; this.pages = pages; }
}"""
K_NOARG = """class JobRow(val id: String, var pages: Int) {
    var status: String = "NEW"

    constructor() : this("", 0)                    // the hand-written version: invented values
}"""

S1 = """Some libraries build your objects in two steps. A library that loads records from a database, for example, first calls a constructor with no parameters to get an empty object. Then it sets each field from the stored record. So it needs every such class to have a constructor with no parameters that isn't private. The shop's `JobRow(val id: String, var pages: Int)` has none. By hand, you'd add one:

""" + pair(J_NOARG, K_NOARG) + """

The hand-written Kotlin constructor works, but it invents an empty id and zero pages, and now any Kotlin caller can create that half-made row by mistake. The **no-arg** plugin generates the constructor instead, for classes with an annotation you configure, here `workbench.kotlin.NoArgEntity`. The docs say it's "annotated with @Deprecated at the HIDDEN level, so you can call it from Java but not from Kotlin". `javap -v` shows both annotations on it, `kotlin.Deprecated` with `level=HIDDEN` and `java.lang.Deprecated`. The demo shows the two sides: Kotlin's `JobRow()` fails with `no value passed for parameter 'id'.`, and Java's `new JobRow()` compiles, with only a deprecation note from javac.

On the print line, no-arg is the machine that adds a blank form at the back of every job marked for it, so that a clerk further down can fill it in.

Now the trap, and the picture shows it. The blank form is really blank. The generated constructor runs no property initializers: its bytecode is three instructions, `aload_0`, `invokespecial Object.<init>` and `return`, and nothing else. The option that would run them, `invokeInitializers`, is "disabled by default". So after `new JobRow()`, `status` holds `null`, even though Kotlin declared it a non-null `String` with the value `"NEW"`. The first `status.length` in Kotlin code throws a `NullPointerException`. A paper form would at least have "status: NEW" printed on it.

For a database library that's usually fine, because it sets every stored field right afterwards. For anything else, turn `invokeInitializers` on, or don't rely on initializers in those classes.

**A no-arg constructor skips your initializers. Don't trust a field of an object you didn't build yourself.**

Hibernate is the best-known such library for Java, and it follows JPA, the Java standard for mapping classes to database tables. For Hibernate and other JPA libraries, use `kotlin-jpa` rather than configuring no-arg yourself. It is no-arg with a preset for `@Entity`, `@Embeddable` and `@MappedSuperclass`, in both the `javax.persistence` and `jakarta.persistence` packages. Since Kotlin 2.3.20, the Gradle `org.jetbrains.kotlin.plugin.jpa` plugin also applies all-open with a JPA preset, so that, in the release notes' words, "lazy associations work as expected instead of causing eager loading". On older Kotlin versions you had to add all-open for those classes yourself.

The first two machines change the shape of a class. The third writes code the class never had."""

# ---------------------------------------------------------------- section 2
J_SER = """// Java's usual approach, with Jackson, a JSON library that reads these annotations by reflection
@JsonTypeInfo(use = JsonTypeInfo.Id.NAME, property = "type")
@JsonSubTypes({
    @JsonSubTypes.Type(value = Queued.class, name = "queued"),
    @JsonSubTypes.Type(value = Cancelled.class, name = "cancelled")
})
public sealed interface JobEvent permits Queued, Cancelled { String jobId(); }

String json = new ObjectMapper().writeValueAsString(events);"""
K_SER = """@Serializable
sealed interface JobEvent { val jobId: String }

@Serializable @SerialName("queued")
data class Queued(override val jobId: String, val pages: Int, val paper: String = "A4") : JobEvent

@Serializable @SerialName("cancelled")
data class Cancelled(override val jobId: String, val reason: String? = null) : JobEvent

private val lenient = Json { ignoreUnknownKeys = true; explicitNulls = false }
val text = lenient.encodeToString(events)      // events: List<JobEvent>"""

S2 = """The shop's app records what happens to each job as events: a job was queued, printed, jammed or cancelled. To save those events in a file, or send them to another program, the app turns each one into text and back. The usual format for that text is JSON, `{"jobId":"job-1","pages":12}`: names and values in braces, readable by people and by almost every programming language.

Most JSON libraries on the JVM work by **reflection**, which means inspecting a class while the program runs: they find its constructor and its properties, and guess how to fill them. Kotlin classes make the guessing harder, with default arguments and non-null types that the JVM knows nothing about. kotlinx.serialization doesn't guess. "When you annotate a class with @Serializable, the Kotlin serialization plugin generates a KSerializer for that class."

The demo's `Queued` gets a nested class, `Queued$$serializer`, that implements `GeneratedSerializer<Queued>` with real `serialize` and `deserialize` methods, plus `Queued.serializer()` on the companion object. On the print line, it's the machine that clips a slip to each job, listing its fields one by one. With the slip, anyone further down can write the job out as text and read it back. Without the plugin, `Queued.serializer()` is `unresolved reference 'serializer'.`

""" + pair(J_SER, K_SER) + """

A sealed hierarchy, a base type whose subclasses are all known when the code compiles, is what the docs call "closed polymorphism". The plugin knows every subclass, so it can write and read a `"type"` field with no registration. That field is the **class discriminator**: it tells the reader which subclass an object is. Three details decide what the JSON looks like.

The discriminator is written only when the static type, the type the compiler sees, is the base. `List<JobEvent>` gets `"type":"queued"`, while `Json.encodeToString(q)` with `q` typed `Queued` gets none. Its value is the fully qualified class name unless you set `@SerialName`, so without it, moving a class to another package changes your saved files. And the default `Json` leaves out properties that equal their default (`encodeDefaults` is off), writes nulls, and rejects keys it doesn't know: `Encountered an unknown key 'tray'`.

For saved events, that last default matters most. A newer version of the app adds a `tray` field, and every older reader with the default `Json` puts the whole file down at the first key it doesn't know. So set `ignoreUnknownKeys = true`. Build one `Json` instance and reuse it: the docs say instances "are immutable and thread-safe", and reusing one is faster. The JSON format is Stable; HOCON, ProtoBuf, CBOR and Properties are still Experimental.

**Pin every subtype with @SerialName, and tolerate unknown keys in data that outlives one version of the app.**

The generated serializer is plain bytecode, with no reflection while the program runs. Java can call it too, as the demo's twin does with `Queued.Companion.serializer()`.

All three machines so far change the compiler's own output. A second family of tools leaves the class files alone and writes new source files instead."""

# ---------------------------------------------------------------- section 3
S3 = """The three plugins above change the compiler's output from the inside. A second family of tools generates new source files from your annotations, the way Java's annotation processors do. An **annotation processor** is a program that runs during compilation, reads the annotations in your code and writes extra source files, which are then compiled with the rest. Libraries use them for code that would be dull to write by hand: mappers that copy fields from one class to another, or the glue that builds your objects and hands each one the helpers it needs.

**kapt** runs Java annotation processors on Kotlin code. The docs say it "generates stub files from Kotlin source code and then runs the Java annotation processors on those stubs". Those stubs are Java declarations of your Kotlin classes, written only so that a Java processor can read them. The migration guide calls them "expensive": they "significantly increase build time" and lose Kotlin-specific features.

**KSP**, Kotlin Symbol Processing, is the Kotlin-native alternative, "a source code generation framework for Kotlin". Its processors read Kotlin declarations directly, and its README says they "can run up to 2x faster" than kapt. The limits are part of the design: KSP processors "can't examine expressions or statements, and they can't modify the source code". They only add new files.

On the print line, kapt and KSP aren't machines at all. They are a second shop that prints extra pages from the notes on your tickets, and the extra pages then join the job. kapt first copies every page into another language so that its workers can read it. KSP reads the original.

Two version facts matter today. KSP2 "is no longer a compiler plugin" and is built on the same compiler APIs as IntelliJ IDEA. And since KSP 2.3.0, KSP1 is deprecated and "KSP version is no longer tied to the Kotlin compiler version", so a KSP release number no longer has to match your Kotlin version.

My rule: use KSP whenever the library ships a KSP processor, and kapt only for processors that exist just for Java. Watch the build time when you add kapt: every module that uses it pays for the stub step on each build. Part 5 of this course is all about KSP: there you'll write processors of your own, from the first one to a small dependency injection tool.

That's also the limit of this whole family of tools, plugins included. They change what the compiler writes, and your source doesn't show it. A class that reads as final is open, a constructor nobody wrote exists, and a serializer nobody typed runs. When something surprises you, `javap` shows what is really there, and the build file says who put it there.

A check to end on, and the answer follows from how the serialization plugin works: a module depends on the `kotlinx-serialization-json` library but doesn't apply `kotlin("plugin.serialization")`. You mark a class `@Serializable` and call `Queued.serializer()`. What happens, and at which stage? (It fails at compile time with `unresolved reference 'serializer'.`: the annotation compiles because it lives in the library, but nobody generates the companion function.)"""

# ---------------------------------------------------------------- closing
CLOSING = """We started on the shop's print line, where machines change every job as it passes. Compiler plugins are those machines: all-open takes the `final` off for frameworks that subclass, no-arg adds a blank constructor for frameworks that fill objects in later, and kotlinx.serialization clips a serializer to each class. That ends the track: every feature in it was code the compiler writes.

In your own build, run `javap` on one class a plugin should have changed, and check that it did.

Next, in this part's capstone, we'll build one small library with these tools, starting with a sealed event model. How do you make the compiler list every place that must change when a new kind of event appears?"""

L = {
 "id": "kt-06",
 "title": "Compiler plugins: all-open, no-arg and kotlinx.serialization",
 "minutes": 35,
 "goal": "By the end you can say what each of the three plugins changes in the class file, configure all-open for the annotations your framework uses, avoid the no-arg initializer trap, and serialize a sealed event hierarchy with stable type names.",
 "opening": OPENING,
 "warmup": {
  "q": "A Kotlin class is marked `@OpenForProxies`, but the build applies no compiler plugins. What does `javap` show for the class?",
  "options": ["`public class`: the annotation opens it", "`public final class`: an annotation is only a label until a plugin reads it", "It depends on the JDK version", "The class doesn't compile until you add `open`"],
  "answer": 1,
  "why": "Kotlin makes classes and their members final by default, and an annotation is just data: it changes nothing unless a compiler plugin reads it. That's what the all-open plugin does, as the first section shows. Many people pick the first option, because the name sounds like an instruction and because Java classes are open by default."
 },
 "sections": [
  {
   "h": "Kotlin classes are final, and frameworks that subclass them need them open",
   "body": S0,
   "aside": ASIDE0,
   "figure": {"svg": FIG, "caption": "Each plugin reads an annotation at compile time and changes the class file: a modifier, a new constructor, or a whole new class."},
   "try": {
    "title": "Open a class without writing open",
    "minutes": 4,
    "steps": [
     "Run `AllOpenDemo`, then `AllOpenDemoJava`, which extends the same Kotlin class from Java.",
     "Run `javap -p -cp kotlin/build/classes/kotlin/demo workbench.kotlin.l06.demo.PrintQueue` from `labs/`. Which members are still final?",
     "Delete `@OpenForProxies` above `PrintQueue`. Predict the errors, run, and put it back."
    ],
    "code": demo("AllOpenDemo"),
    "expect": "The demo prints `PrintQueue: open class; getTraySize:open, print:open, secret:private`, `PlainHelper: final class; help:final`, a timing line and `printed flyer.pdf from a tray of 500 sheets`. Ignore the timing: one cold call measures class loading, not the proxy. `javap` shows `public class PrintQueue`, `private final int traySize` and `private int secret()`: only the field keeps its `final`. Without the marker, the build fails with `this type is final, so it cannot be extended.` and `'print' in 'PrintQueue' is final and cannot be overridden.`, and the Java twin would get `cannot inherit from final PrintQueue`."
   },
   "refs": [{"title": "All-open compiler plugin (Kotlin docs)", "url": "https://kotlinlang.org/docs/all-open-plugin.html", "kind": "docs"},
            {"title": "Kotlin-spring plugin (Kotlin docs)", "url": "https://kotlinlang.org/docs/kotlin-spring-plugin.html", "kind": "docs"}]
  },
  {
   "h": "no-arg: an empty constructor for frameworks that build objects first, minus your initializers",
   "body": S1,
   "try": {
    "title": "Build an object the way a database library does",
    "minutes": 3,
    "steps": [
     "Run `NoArgDemo`, then `NoArgDemoJava`. Predict `blank.status` before you look.",
     "Uncomment the wrong move in `NoArgDemo.kt`, predict, run, and comment it out again.",
     "In `NoArgDemo.kt`, add `println(blank.status.length)` at the end of `main`. Predict what happens, then run."
    ],
    "code": demo("NoArgDemo"),
    "expect": "Both show `pages = 0` and a `null` status, and the Java twin also prints `getId() = null`: the generated constructor sets nothing and runs no initializer. The Kotlin call `JobRow()` fails with `no value passed for parameter 'id'.` and the same for `pages`. The added line compiles, because `status` is declared `String`, and throws `NullPointerException: Cannot invoke \"String.length()\" because the return value of \"...JobRow.getStatus()\" is null`."
   },
   "refs": [{"title": "No-arg compiler plugin (Kotlin docs)", "url": "https://kotlinlang.org/docs/no-arg-plugin.html", "kind": "docs"},
            {"title": "Kotlin-jpa plugin (Kotlin docs)", "url": "https://kotlinlang.org/docs/kotlin-jpa-plugin.html", "kind": "docs"}]
  },
  {
   "h": "kotlinx.serialization writes the serializer while your code compiles",
   "body": S2,
   "try": {
    "title": "Read the JSON a sealed hierarchy produces",
    "minutes": 4,
    "steps": [
     "Run `SerializationDemo`. Before you do, predict which lines will contain `\"type\"`.",
     "Remove `@SerialName(\"queued\")` from `Queued` and run again. What is the type value now?",
     "Run `SerializationDemoJava`, which uses the generated serializer from Java through `Queued.Companion.serializer()`."
    ],
    "code": demo("SerializationDemo"),
    "expect": "The list prints `[{\"type\":\"queued\",\"jobId\":\"job-1\",\"pages\":12},{\"type\":\"cancelled\",\"jobId\":\"job-1\"}]`: no `paper` (it equals its default) and no `reason` (null, with `explicitNulls = false`). The static-type `Queued` line has no `type`; the `JobEvent` line has one. The lenient instance ignores `tray`, and the default one fails with `Encountered an unknown key 'tray'`. Without `@SerialName` the type becomes `workbench.kotlin.l06.demo.Queued`. The Java twin prints the JSON of one `Queued` and the class name `Queued$$serializer`."
   },
   "refs": [{"title": "Serialize polymorphic classes (Kotlin docs)", "url": "https://kotlinlang.org/docs/serialization-polymorphism.html", "kind": "docs"},
            {"title": "Customize the Json instance (Kotlin docs)", "url": "https://kotlinlang.org/docs/serialization-json-configuration.html", "kind": "docs"}]
  },
  {
   "h": "KSP and kapt write new source files instead",
   "body": S3
  }
 ],
 "compare": {
  "title": "A proxy-ready service and a database row: Java as written vs Kotlin with plugins",
  "java": {"title": "Beans.java", "src": "public class SheetPlanner {                         // open by default in Java\n    public int sheetsFor(int pages) { return (pages + 1) / 2; }\n}\n\npublic class JobRecord {                            // open by default\n    private String id;\n    private int pages;\n    private String status = \"NEW\";                  // runs in every constructor\n\n    protected JobRecord() { }                       // the no-arg constructor, written by hand\n    public JobRecord(String id, int pages) { this.id = id; this.pages = pages; }\n}"},
  "kotlin": {"title": "Beans.kt", "src": "@OpenForProxies                                     // all-open is configured for this annotation\nclass SheetPlanner {\n    fun sheetsFor(pages: Int): Int = (pages + 1) / 2\n}\n\n@NoArgEntity @OpenForProxies                        // no-arg adds the constructor, all-open the open\nclass JobRecord(val id: String, var pages: Int) {\n    var status: String = \"NEW\"                      // skipped by the generated no-arg constructor\n}"},
  "note": "Java gets proxy-ready classes for free: classes and methods are open unless marked `final`, and you write the no-arg constructor yourself, where field initializers run as usual. Kotlin's defaults point the other way, so the plugins put back what frameworks need, at compile time, driven by annotations. The class files end up close to the Java ones, with one difference that bites: Kotlin's generated no-arg constructor skips property initializers unless you enable `invokeInitializers`, so `status` is `null` on a fresh instance, while Java's hand-written constructor runs `status = \"NEW\"`."
 },
 "worked": {
  "title": "Add a field to saved job events without breaking older readers",
  "steps": [
   {"say": "Version 1 of the shop's app saves job events to a file, and a second program, the label printer, reads them with the default `Json`. Here are both sides, with a Java reader that uses Jackson.",
    "code": "// Java reader with Jackson: by default it also fails on unknown properties\nObjectMapper mapper = new ObjectMapper();\nPrinted p = mapper.readValue(line, Printed.class);", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "@Serializable @SerialName(\"printed\")\ndata class Printed(override val jobId: String, val pages: Int) : JobEvent\n\nval event = Json.decodeFromString<JobEvent>(line)   // the default Json: strict"},
   {"say": "Version 2 adds a `tray` field, and the app is updated first. The label printer, still on version 1, now fails on every new line, because unknown keys \"result in an error\" by default.",
    "code": "// version 2 writes {\"type\":\"printed\",\"jobId\":\"job-7\",\"pages\":12,\"tray\":\"2\"}\nJson.decodeFromString<JobEvent>(v2)\n// SerializationException: ... Encountered an unknown key 'tray' at path: $", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "mapper.readValue(v2, Printed.class);\n// Jackson: UnrecognizedPropertyException, unless FAIL_ON_UNKNOWN_PROPERTIES is turned off"},
   {"say": "Configure the reader once, in one shared instance: tolerate new keys, keep every `@SerialName` stable, and give new fields defaults so that old lines still decode.",
    "code": "// 1. one instance, reused: immutable and thread-safe\nval events = Json { ignoreUnknownKeys = true; explicitNulls = false }\n\n// 2. a new field gets a default, so version 1 lines without it still decode\n@Serializable @SerialName(\"printed\")\ndata class Printed(override val jobId: String, val pages: Int, val tray: String? = null) : JobEvent", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "ObjectMapper mapper = new ObjectMapper()\n        .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);"},
   {"say": "Check the other direction. A version-1 reader that doesn't know a new subtype, say `\"type\":\"recycled\"`, still fails, and it should: `ignoreUnknownKeys` covers fields, not types. When you add a subtype, update the readers before the writers.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "A serializable event hierarchy and proxy-ready classes",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/JobEvents.kt", f"{lab}/main/{P}/Beans.kt", f"{lab}/main/kotlin/workbench/kotlin/Annotations.kt"],
  "run": "./gradlew :kotlin:test --tests 'workbench.kotlin.l06.*'",
  "steps": [
   "Read `Annotations.kt` and the two plugin lines in `labs/kotlin/build.gradle.kts`. The annotations do nothing by themselves; the plugins look for their names.",
   "Run the tests. All seven fail.",
   "In `JobEvents.kt`, add `@Serializable` and `@SerialName` (TODO 1), create the shared `Json` (TODO 2), and write `encodeEvents` and `decodeEvents` (TODOs 3 and 4).",
   "In `Beans.kt`, mark `SheetPlanner` with `@OpenForProxies` (TODO 5), and `JobRecord` with `@NoArgEntity` and `@OpenForProxies` (TODO 6).",
   "Run until all seven pass, including `EventsFromJavaTest`. Then run `javap -p -cp kotlin/build/classes/kotlin/main workbench.kotlin.l06.JobRecord` and find the constructor nobody wrote."
  ],
  "hints": [
   "`encodeToString` and `decodeFromString` are extension functions with reified types: `json.encodeToString(events)` and `json.decodeFromString<List<JobEvent>>(text)`, or let the return type infer it.",
   "The `\"type\"` field appears because the static type is `List<JobEvent>`, the sealed base. You don't configure it.",
   "`Json { ignoreUnknownKeys = true; explicitNulls = false }` covers both rules. Leave `encodeDefaults` alone: off is the default, and the test expects `paper` to be left out.",
   "The marker annotations live in package `workbench.kotlin`: import `workbench.kotlin.OpenForProxies` and `workbench.kotlin.NoArgEntity`."
  ],
  "done_when": "All seven tests in `PluginsTest` and `EventsFromJavaTest` pass."
 },
 "drill": {
  "title": "Write a serializable parcel hierarchy from memory",
  "minutes": 4,
  "prompt": "Close this page. Write a sealed `ParcelEvent` with two subtypes, `ParcelWeighed(parcelId, grams)` and `ParcelSent(parcelId, sentAtEpochMs)`, serialized with the stable type names `parcel_weighed` and `parcel_sent`, and a shared `Json` that tolerates new fields. Then write the Java version with Jackson annotations. Where does each version find the subtypes?",
  "answer": {"lang": "kotlin", "src": "@Serializable\nsealed interface ParcelEvent { val parcelId: String }\n\n@Serializable @SerialName(\"parcel_weighed\")\ndata class ParcelWeighed(override val parcelId: String, val grams: Long) : ParcelEvent\n\n@Serializable @SerialName(\"parcel_sent\")\ndata class ParcelSent(override val parcelId: String, val sentAtEpochMs: Long) : ParcelEvent\n\n// the plugin finds the subtypes at compile time, from the sealed hierarchy\nval parcelJson = Json { ignoreUnknownKeys = true }",
             "alt": {"lang": "java", "title": "ParcelEvent.java", "src": "// Jackson finds the subtypes at run time, from these annotations\n@JsonTypeInfo(use = JsonTypeInfo.Id.NAME, property = \"type\")\n@JsonSubTypes({\n    @JsonSubTypes.Type(value = ParcelWeighed.class, name = \"parcel_weighed\"),\n    @JsonSubTypes.Type(value = ParcelSent.class, name = \"parcel_sent\")\n})\npublic sealed interface ParcelEvent permits ParcelWeighed, ParcelSent { String parcelId(); }\n\nrecord ParcelWeighed(String parcelId, long grams) implements ParcelEvent {}\nrecord ParcelSent(String parcelId, long sentAtEpochMs) implements ParcelEvent {}\n\nObjectMapper mapper = new ObjectMapper()\n        .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);"}}
 },
 "recap": [
  "A compiler plugin changes what kotlinc writes into class files, driven by annotations you name in the build. The annotations do nothing on their own.",
  "all-open removes `final` from marked classes and their members (not private members, not fields), so a framework can subclass them. kotlin-spring and kotlin-jpa are presets; when a preset lags, name the annotations yourself.",
  "no-arg adds a zero-argument constructor, hidden from Kotlin, callable from Java and reflection. It skips property initializers unless `invokeInitializers` is on.",
  "kotlinx.serialization generates a `$$serializer` class at compile time. A sealed base gets a `\"type\"` discriminator: pin it with `@SerialName`, reuse one `Json`, and set `ignoreUnknownKeys` for data that outlives one version.",
  "KSP and kapt generate new source files. Prefer KSP; kapt runs Java processors on generated stubs and costs build time.",
  "The limit: none of this shows in your source. `javap` shows what the plugins really wrote, and the build file says which plugin wrote it."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "The build configures all-open with `annotation(\"com.shop.Proxied\")`. A class is marked with `com.shop.legacy.Proxied`, an annotation with the same simple name in another package. What does `javap` show for the class?",
   "options": ["`public class`, with open methods", "`public final class`: the plugin matches the full name, package included", "A compile error: the plugin rejects the unknown annotation", "`public class`, but every method is still `final`"],
   "answer": 1, "why": "all-open looks for the fully qualified names listed in the build. `com.shop.legacy.Proxied` matches none of them, so the plugin leaves the class alone, and it stays final like every Kotlin class. A framework preset that still lists an old package name leaves classes closed in exactly this way."},
  {"q": "A class built with the default no-arg settings has `var status: String = \"NEW\"`. What does `status` hold right after a database library calls the generated constructor, before it sets any field?",
   "options": ["`\"NEW\"`", "`\"\"`", "`null`, even though the type is `String`", "Nothing: the constructor throws because `status` isn't set"],
   "answer": 2, "why": "The generated constructor doesn't run property initializers unless `invokeInitializers` is enabled, and it is off by default. Its bytecode only calls `Object.<init>`. The library normally overwrites the field from the stored row; any other code that reads it first sees `null` in a non-null property."},
  {"q": "`Queued` is a `@Serializable @SerialName(\"queued\")` subclass of a sealed `JobEvent`, and `q` is typed `Queued`. What does `Json.encodeToString(q)` produce?",
   "options": ["`{\"jobId\":\"job-2\",\"pages\":1}`: no discriminator, because the static type isn't the base", "`{\"type\":\"queued\",\"jobId\":\"job-2\",\"pages\":1}`", "The fully qualified class name in a `\"type\"` field", "A `SerializationException`: sealed subtypes must be encoded as the base"],
   "answer": 0, "why": "The docs say the class discriminator is included only when the base class is the static type. Encode `q` as a `JobEvent` (or inside a `List<JobEvent>`) to get `\"type\":\"queued\"`. The fully qualified name appears only when there is no `@SerialName`."},
  {"q": "Your project needs generated mappers from an annotation processor that exists only for Java. Which tool runs it on Kotlin classes?",
   "options": ["KSP", "all-open", "kotlinx.serialization", "kapt"],
   "answer": 3, "why": "kapt generates Java stubs from your Kotlin sources and runs Java annotation processors on them. KSP runs KSP processors, which a Java-only processor isn't. all-open and kotlinx.serialization change the compiler's output and don't run processors at all."},
  {"q": "From the patterns track: a framework proxy wraps `SheetPlanner`, and inside `SheetPlanner`, `plan()` calls `this.sheetsFor()`, which has a timing interceptor. With a proxy that forwards to a separate target object, does the interceptor run for that inner call?",
   "options": ["Yes, because all-open made `sheetsFor` open", "No: `this` is the target, so the call never goes through the proxy", "Only if `sheetsFor` is private", "Only when the class is written in Java"],
   "answer": 1, "why": "all-open makes the proxy possible; it doesn't route calls through it. A forwarding proxy calls the target, and inside the target `this.sheetsFor()` is a plain call on the target. That's the self-invocation trap from the Decorator and Proxy lesson, and it's the same in Java and Kotlin.",
   "from": "pat-05"}
 ],
 "flashcards": [
  {"front": "Why does a Kotlin class need all-open (or `open`) before a framework can proxy it?", "back": "Kotlin classes and members are final by default, and those proxies are generated subclasses that override your methods."},
  {"front": "What does all-open leave unchanged?", "back": "Private members, backing fields (still `final`), and every class without a configured annotation."},
  {"front": "How does all-open decide which classes to open?", "back": "By the fully qualified names of the annotations listed in the build (or in a preset), on the class or one of its superclasses. A same-named annotation in another package doesn't count."},
  {"front": "What does no-arg generate, and who can call it?", "back": "A zero-argument constructor marked `@Deprecated(level = HIDDEN)`: Java and reflection can call it, Kotlin code can't."},
  {"front": "Does no-arg's constructor run property initializers?", "back": "Not by default (`invokeInitializers` is off), so a non-null property can hold `null` on a fresh instance."},
  {"front": "When does kotlinx.serialization write the `\"type\"` discriminator?", "back": "Only when the static type is the polymorphic base, such as `List<JobEvent>`. Its value is the `@SerialName`, or else the fully qualified class name."},
  {"front": "KSP vs kapt in one line each?", "back": "kapt runs Java annotation processors on generated Java stubs (slow builds). KSP processors read Kotlin declarations directly, up to 2x faster, and can only add files."}
 ],
 "terms": [
  {"term": "Compiler plugin", "plain": "A jar the Kotlin compiler loads to change what it writes into class files, usually driven by annotations."},
  {"term": "Proxy", "plain": "A class a framework generates that extends yours and overrides methods to add work before and after each call."},
  {"term": "all-open", "plain": "Compiler plugin that makes marked classes and their members open, without writing `open`."},
  {"term": "no-arg", "plain": "Compiler plugin that adds a zero-argument constructor, hidden from Kotlin, for frameworks that need one."},
  {"term": "kotlin-jpa", "plain": "no-arg with a preset for JPA annotations; since Kotlin 2.3.20 its Gradle plugin also applies all-open for them."},
  {"term": "Class discriminator", "plain": "The `\"type\"` field that tells a JSON reader which subclass an object is."},
  {"term": "KSP", "plain": "Kotlin Symbol Processing: a framework for processors that read Kotlin declarations and generate new source files."},
  {"term": "kapt", "plain": "Runs Java annotation processors on Kotlin code by first generating Java stubs of the Kotlin classes."}
 ],
 "explain_back": {
  "prompt": "A teammate's Kotlin class carries the annotation their framework uses, yet the framework's timing proxy never runs, and `javap` shows `public final class`. Explain what's going on in the class file and what you'd change.",
  "answer": "Kotlin compiles classes and their methods as final unless something opens them. The framework adds its timing through a generated subclass that overrides the class's methods, and a final class or method can't be overridden. The all-open plugin is supposed to remove `final` from classes with certain annotations, but it only does that for the annotations it's told about, matched by their full names, package included. Here the build either doesn't apply all-open at all, or names a different annotation, for example a preset that still lists an older package name for the framework's annotation. The annotation on the class is only data, so nothing acts on it and the class stays final. I'd list the exact annotation the class uses in `allOpen { annotation(\"...\") }`, rebuild, and check with `javap` that `final` is gone from the class and its public methods."
 },
 "deeper": {
  "minutes": 8,
  "body": "The presets inside the 2.4.21 all-open plugin, read from the plugin's own classes, say more than the docs page. `spring` lists `@Component`, `@Transactional`, `@Async`, `@Cacheable`, `@SpringBootTest` and also `org.springframework.validation.annotation.Validated`, which the docs page leaves out. `micronaut` lists four of that framework's annotations for adding behavior to methods, `jpa` lists `Entity`, `Embeddable` and `MappedSuperclass` in both packages, and `quarkus` lists only the two old `javax` scopes. When a framework moves its annotations to a new package, presets lag behind, and listing annotations by name is the only setting you control.\n\nOn the command line the same plugins take `-P` options, which helps when you test an idea with plain `kotlinc`: `-Xplugin=<allopen jar> -P plugin:org.jetbrains.kotlin.allopen:annotation=workbench.kotlin.OpenForProxies`, and for no-arg `-P plugin:org.jetbrains.kotlin.noarg:invokeInitializers=true`. Maven users add `<plugin>all-open</plugin>` to the Kotlin Maven plugin with the `kotlin-maven-allopen` dependency. Since Kotlin 2.3.20, `kotlin-maven-noarg` also includes `kotlin-maven-allopen`.\n\nkotlinx.serialization has more for data that changes over time. Open polymorphism, where subclasses live in other modules and the compiler can't see them all, needs a `SerializersModule` that registers each one. `classDiscriminator` renames the `\"type\"` field if your data already uses that name. `coerceInputValues` turns invalid values, such as an unknown enum constant, into the property's default instead of failing. And `@JsonIgnoreUnknownKeys` (Experimental) relaxes unknown keys for one class instead of a whole `Json` instance.\n\nFinally, the generated code is plain JVM bytecode, fast and free of reflection while the program runs. That also makes it a good fit for native images, programs compiled ahead of time into a single executable, where reflection needs extra setup. The startup track covers why."
 },
 "sources": [
  {"title": "All-open compiler plugin (Kotlin docs)", "url": "https://kotlinlang.org/docs/all-open-plugin.html"},
  {"title": "No-arg compiler plugin (Kotlin docs)", "url": "https://kotlinlang.org/docs/no-arg-plugin.html"},
  {"title": "Serialize polymorphic classes (Kotlin docs)", "url": "https://kotlinlang.org/docs/serialization-polymorphism.html"},
  {"title": "KSP overview (Kotlin docs)", "url": "https://kotlinlang.org/docs/ksp-overview.html"},
  {"title": "What's new in Kotlin 2.3.20 (kotlin-jpa applies all-open)", "url": "https://kotlinlang.org/docs/whatsnew2320.html"}
 ]
}
out = ROOT / "content/lessons/kt-06.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
