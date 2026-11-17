import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/startup/src"
DJ = "java/workbench/startup/l03/demo"
DK = "kotlin/workbench/startup/l03/demo"
read = lambda p: (ROOT / p).read_text()


def demo(name):
    """A Try-it code object for a Java demo with its Kotlin twin, read from disk."""
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{DJ}/{name}.java"),
            "run": f"./gradlew :startup:demo -Pmain=workbench.startup.l03.demo.{name}",
            "file": f"{lab}/demo/{DJ}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{DK}/{name}.kt"),
                    "run": f"./gradlew :startup:demo -Pmain=workbench.startup.l03.demo.{name}Kt",
                    "file": f"{lab}/demo/{DK}/{name}.kt"}}


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


FIG = (
    '<svg viewBox="0 0 700 250" role="img" aria-label="Native image build: the analysis starts at main and keeps reachable code; '
    'a class reached only through a name in a message is kept only if the metadata file lists it.">'
    '<text class="t-s t-m" x="20" y="22">at the factory: build time, minutes</text>'
    '<rect class="box-a" x="20" y="36" width="110" height="40" rx="8"/>'
    '<text class="t t-code" x="75" y="61" text-anchor="middle">main()</text>'
    '<line class="ln" x1="130" y1="56" x2="172" y2="56" marker-end="url(#arr)"/>'
    '<rect class="box" x="175" y="36" width="140" height="40" rx="8"/>'
    '<text class="t-s" x="245" y="61" text-anchor="middle">TrackingService</text>'
    '<line class="ln" x1="315" y1="56" x2="357" y2="56" marker-end="url(#arr)"/>'
    '<rect class="box" x="360" y="36" width="130" height="40" rx="8"/>'
    '<text class="t-s" x="425" y="61" text-anchor="middle">EventDecoder</text>'
    '<line class="ln-d" x1="425" y1="76" x2="425" y2="112"/>'
    '<text class="t-s t-bad" x="560" y="100" text-anchor="middle">Class.forName(header)</text>'
    '<rect class="box-ok" x="300" y="116" width="190" height="40" rx="8"/>'
    '<text class="t-s" x="395" y="141" text-anchor="middle">ParcelScanned: listed</text>'
    '<rect class="box-dim" x="505" y="116" width="185" height="40" rx="8"/>'
    '<text class="t-s" x="597" y="141" text-anchor="middle">ParcelReturned: not listed</text>'
    '<rect class="box-b" x="20" y="116" width="250" height="40" rx="8"/>'
    '<text class="t-s t-code" x="145" y="141" text-anchor="middle">reachability-metadata.json</text>'
    '<line class="ln-a" x1="270" y1="136" x2="297" y2="136" marker-end="url(#arr)"/>'
    '<line class="ln-d" x1="20" y1="176" x2="690" y2="176"/>'
    '<text class="t-s t-m" x="20" y="198">at the stall: run time, milliseconds</text>'
    '<rect class="box-ok" x="300" y="206" width="190" height="34" rx="8"/>'
    '<text class="t-s" x="395" y="228" text-anchor="middle">decodes as on the JVM</text>'
    '<rect class="box-bad" x="505" y="206" width="185" height="34" rx="8"/>'
    '<text class="t-s" x="597" y="228" text-anchor="middle">registration error</text>'
    '<line class="ln" x1="395" y1="156" x2="395" y2="204" marker-end="url(#arr)"/>'
    '<line class="ln-bad" x1="597" y1="156" x2="597" y2="204" marker-end="url(#arr)"/>'
    '</svg>'
)

OPENING = """Even with a full back room, the shop has a morning routine: wheel out the shelves, switch on the tills, get up to speed. Now picture a pop-up stall, built at a factory, fully stocked and loaded onto a van. Park it, open the shutter, and you're trading at once. The catch is printed on the side: it sells only what the factory packed.

GraalVM's native image builds that stall. It turns your program, and the parts of the JDK it uses, into one ready-to-run file, with no JVM to start. Lesson 2's AOT cache still left a JVM that interprets first and compiles later; a native image does all of that in the build.

The trap is the customer who asks for something by name, from a note in their pocket. Code that picks a class by a name it reads at run time works on every JVM, and fails in a native image. In this lesson, we'll see what the build packs, list what it can't see, catch code that runs at the factory, and meet Quarkus, a framework that writes the list for you. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
S0 = """Lesson 2's best result still started a JVM. Even with a perfect AOT cache, the JVM maps its classes, links what training missed, interprets, and waits for the JIT. In a benchmark that the Quarkus project publishes for one of its sample services, the first request still took 1,859 ms with the cache. (Quarkus is a framework for Java services, and we'll meet it properly in the last section.) Native image removes that work from every start by doing it once, in the build.

The tool is called `native-image`. It comes with GraalVM, a JDK from Oracle with extra tools, or with Mandrel, a build of the same tool that the Quarkus project tailors for its framework. A plain OpenJDK doesn't have it. GraalVM comes in two editions, the open-source Community Edition and Oracle GraalVM, and the difference matters below. `native-image` takes your class path and builds one executable file for one operating system and one kind of CPU, in three steps.

First it analyzes the program. Starting at `main`, it follows every method call and field access it can see, and works out which classes can show up at each call. Second, it runs static initializers where it can. It saves the objects they create into the **image heap**, a part of the executable that is mapped straight into memory at start-up. Third, it compiles every method it reached to machine code.

Code the analysis never reached is left out, and so are the JDK classes nothing uses. That's the **closed-world assumption**: everything the program will ever run is known when you build it. In the shop picture, the factory packs the stall by following the shop's own catalogue. Every item a page points to goes in the van, and nothing else does.

The finished binary runs on a small runtime called Substrate VM, with no class loading, no bytecode verification, no interpreter and no JIT. That's why it starts in milliseconds and stays small. The Quarkus benchmark (Quarkus 3.34.3 on JDK 25.0.2, tuned by its authors) puts numbers on it:

| | JVM | JVM + AOT cache | Native image (Mandrel) |
|---|---|---|---|
| Time to first request | 4,417 ms | 1,859 ms | 581 ms |
| Peak throughput | 13,265 requests/s | 12,389 requests/s | 5,411 requests/s |
| RSS | 304 MiB | 240 MiB | 95 MiB |
| Build | about 30 s | build plus a training run | 3 to 10 min, 4 to 8 GB of RAM |

Peak throughput, the most requests per second a service handles once it's busy, is 59% lower as a native image. With no JIT, there are no profiles from the real run. GraalVM's own docs say that "without profiling information, it is difficult to generate machine code of the same quality as a JIT compiler". The stall's staff follow a printed script, and they never learn shortcuts. Profile-guided optimization (PGO), building again with profiles recorded from a test run, narrows the gap, but "PGO is not available in GraalVM Community Edition", only in Oracle GraalVM. The default garbage collector is Serial, a single-threaded collector "optimized for low footprint and small Java heap sizes". G1 is available only in Oracle GraalVM, on Linux.

The other price is everything the analysis can't see. Reflection is code that looks up classes and methods by name while it runs. The analysis can't follow reflection, and it can't follow dynamic proxies, resources (files packed in a JAR) loaded by name, JNI (calls into native C code) or serialization (turning objects into bytes and back) either. The analysis is clever, not psychic. It works out reflective calls at build time "given that all the call arguments are constant", so `Class.forName("tracker.ParcelScanned")`, with the name written in the code, just works.

The tracking service isn't that lucky. It reads messages from its depots, and each message names its event class in a header: `Class.forName(message.header("type"))`. The build can't know that name. You have to tell it, or the call fails at run time. Current GraalVM throws `MissingReflectionRegistrationError`, which "extends `java.lang.Error` and should not be handled".

Here the stall picture breaks, and the break costs real time. Changing one price tag on a real stall takes a minute. Changing one line of your code means building the whole stall again at the factory, which takes minutes and gigabytes of memory, every time.

**A native image runs only what the build could see. Anything your code finds by name must be on a list.**

GraalVM calls that list reachability metadata, and the next section writes one."""

ASIDE0 = {
    "title": "Isn't this what Leyden does?",
    "body": "No, although both work ahead of time. Leyden's AOT cache is an optimization for the normal JVM: the same JVM, with the same open world, and if the cache doesn't fit, the JVM simply runs without it. A native image is a different runtime with a closed world: no class loading, no JIT, and no way to run a class the build didn't see. JEP 544, in development for JDK 28, will put compiled code in the AOT cache while the JVM keeps its JIT. The two keep borrowing each other's strengths, but they make opposite promises."
}

# ---------------------------------------------------------------- section 1
S1 = """You tell the build in a file named `reachability-metadata.json`, in the folder `META-INF/native-image/<groupId>/<artifactId>/` on the class path. (A group id and an artifact id are the two names that identify a library, such as `com.example` and `tracker`.) The current schema, version 1.2.0, allows four keys at the top level: `reflection`, `resources`, `foreign` and `comment`. Proxies, serialization and JNI all live inside `reflection` entries. In the shop, this file is the packing list for the items customers ask for by name.

A reflection entry names a type, and the members your code uses on it:

```json
{
  "reflection": [
    {
      "condition": { "typeReached": "tracker.EventDecoder" },
      "type": "tracker.ParcelScanned",
      "methods": [
        { "name": "<init>", "parameterTypes": ["java.lang.String", "java.lang.String", "long"] },
        { "name": "parcelId", "parameterTypes": [] }
      ]
    }
  ]
}
```

A constructor is named `<init>`, the JVM's own name for it. Parameter types are fully qualified, primitives go by name (`long`, `int`), and every method needs `parameterTypes`, even an empty one. Instead of listing members, you can set `allDeclaredConstructors` or `allPublicMethods`, which keeps more code in the binary. The optional `condition` switches the entry on only once `EventDecoder` is reached at run time, which means just before its static initializer starts. Writing `EventDecoder.class` on its own doesn't count.

A **dynamic proxy** is an object the JDK builds while the program runs: it implements a list of interfaces and sends every call to one handler method. Web client libraries use them a lot. The tracking service's `DepotClient`, which asks a depot where a parcel is, is one. In the metadata, a proxy is a reflection entry whose type is the ordered list of its interfaces:

```json
{ "reflection": [ { "type": { "proxy": ["tracker.DepotClient", "java.lang.AutoCloseable"] } } ] }
```

The order is part of the proxy's identity: a proxy for (A, B) is a different class from one for (B, A), as the Try it below shows. If the proxy gets serialized, add `"serializable": true`; the docs say proxies "can only be registered for serialization via the JSON files".

Two warnings about what you'll find online. The older schema, v1.1.0, had separate top-level `jni` and `serialization` sections, and some GraalVM pages still show a top-level `jni` array, which v1.2.0 rejects. The current Quarkus development docs tell you to use "a `proxy` section", which v1.2.0 rejects too. Check your file against the schema of the GraalVM you build with.

You rarely write all of it by hand. The tracing agent watches a run on a normal JVM and writes down every reflective call it saw:

```bash
java -agentlib:native-image-agent=config-output-dir=build/ni-config -jar tracker.jar
```

Like an AOT training run, the agent sees only the code paths you exercise, so drive it with real tests, then read what it wrote. To make a missing entry fail loudly, build with `--exact-reachability-metadata`, and run your tests with `-XX:MissingRegistrationReportingMode=Exit`.

**Write the list from what the code really does, then let a test prove it's complete.**

The list covers what the analysis can't see. But the factory also runs some of your code while it builds, and that has a surprise of its own."""

# ---------------------------------------------------------------- section 2
J_FROZEN = """static final Instant STARTED_AT = Instant.now();   // the build's clock, on every start
static final Random JITTER = new Random();         // the builder refuses this one"""
K_FROZEN = """val startedAt: Instant = Instant.now()             // the build's clock, on every start
val jitter = Random()                              // the builder refuses this one"""

S2 = """Class initialization is the other half of the story. GraalVM's docs give the numbers: "the simple 'Hello, World!' application requires more than 300 classes to be initialized". In code compiled ahead of time, checking "is this class initialized yet?" on every access "can reduce performance by more than twofold". So the builder runs static initializers **at build time** wherever it can, and stores what they produced in the image heap. The stall's displays are built at the factory.

Plain GraalVM initializes most JDK classes at build time, and your own classes only when it can prove that's safe. An initializer that calls native code (`System.out.println` counts) or makes a call it can't pin to one target stays at run time. Quarkus goes further: "By default, Quarkus initializes all classes at build time."

So your static initializer runs on the build machine, once, and its results are frozen into the binary:

""" + pair(J_FROZEN, K_FROZEN) + """

These two lines come from `BuildTimeInitDemo`, in the Try it below. The second one is a retry jitter: a small random delay before trying again, so that many copies of a service don't all retry at the same moment. On a JVM, each run prints a new start time and a new delay. In a native image with build-time initialization, `STARTED_AT` would tell every user, for months, the moment the factory built the stall.

The builder catches some of these. Quarkus lists two errors you're likely to meet: "Detected an instance of Random/SplittableRandom class in the image heap. Instances created during image generation have cached seed values", and "No instances are allowed in the image heap for a class that is initialized or reinitialized at image runtime: sun.security.provider.NativePRNG". A seed is the starting value of a random number generator, and the same seed gives the same "random" numbers. Don't count on the builder for anything else. A timestamp, the computer's name, a token fetched at start: whatever an initializer computes, every copy started from that binary sees the build's value.

The fix is to initialize that class at run time instead:

```properties
quarkus.native.additional-build-args=--initialize-at-run-time=tracker.InstanceInfo\\\\,tracker.RetryJitter
```

Quarkus needs the comma escaped like that. With plain `native-image`, the options are `--initialize-at-run-time=` and `--initialize-at-build-time=`, and `-H:+PrintClassInitialization` reports which classes were initialized where. Better still, keep per-copy values out of static initializers altogether, and compute them in a method that runs when the program starts.

**Whatever a static initializer computes, the build computes once. Keep per-run values out of it.**

Writing these lists by hand is fine for one decoder. For a whole service, you'd want the framework to write them for you."""

# ---------------------------------------------------------------- section 3
J_QUARKUS = """@RegisterForReflection
public record ParcelScanned(String parcelId, String depot, long weightGrams) { }

@RegisterForReflection(targets = {DepotReply.class, DepotError.class})   // a library's classes
public class DepotReflectionConfig { }

@RegisterForProxy(targets = {DepotClient.class, AutoCloseable.class})    // order matters
public class DepotProxyConfig { }"""
K_QUARKUS = """@RegisterForReflection
data class ParcelScanned(val parcelId: String, val depot: String, val weightGrams: Long)

@RegisterForReflection(targets = [DepotReply::class, DepotError::class])  // a library's classes
class DepotReflectionConfig

@RegisterForProxy(targets = [DepotClient::class, AutoCloseable::class])   // order matters
class DepotProxyConfig"""

S3 = """Quarkus is an open-source framework for writing services in Java and Kotlin, and it's the second half of this lesson's title. Its main idea is the one this track keeps coming back to: do at build time what other frameworks do at every start. It scans and wires your program while it builds, and it treats native image as a first-class target, which it calls Quarkus native.

Quarkus is made of extensions, add-on modules that each bring one library, such as a JSON library or a database driver. Each extension knows what its library reflects on, and Quarkus generates `reachability-metadata.json` itself. Your part is the classes only your own code knows about, and you declare them with annotations:

""" + pair(J_QUARKUS, K_QUARKUS) + """

`@RegisterForReflection` registers methods and fields by default, plus any nested classes unless you set `ignoreNested = true`. With `targets`, it registers the listed classes and not the class it sits on, which is how you cover a library's classes that you can't annotate. `serialization = true` adds Java serialization. `@RegisterForProxy` takes the interfaces in order, and the Quarkus docs repeat that "the order of the specified proxy interfaces is significant". Resources go in `application.properties`, Quarkus's settings file: `quarkus.native.resources.includes=templates/**,postcodes/*.csv`.

When you do need JSON, put it in `src/main/resources/META-INF/native-image/<group-id>/<artifact-id>/`. The current docs warn that Quarkus overwrites a file placed directly in `META-INF/native-image/`. Versions matter here too. The latest 3.x release is 3.40.1.1, and its guides still show the older separate files, `reflect-config.json` and `proxy-config.json`, while the 4.0 guides say those legacy files "are not supported". Write the unified `reachability-metadata.json`, and the file survives the upgrade.

`./mvnw verify -Dnative` (`mvnw` runs Maven, a build tool) builds the binary and runs your integration tests against it. Integration tests start the whole program and talk to it from outside. Because a native build takes minutes and gigabytes, most teams build it in a shared build, not after every change, and develop in JVM mode. Quarkus's own advice is "Start with JVM mode. Move to native when you have a concrete need." Lesson 4 of this track turns that into a decision table.

Check before the lab: your scan events live in a shared JAR that another team owns, so you can't annotate them. Which annotation do you add, and on which class? (`@RegisterForReflection(targets = {...})` on any class in your own code, listing their classes. The class carrying the annotation isn't registered itself.)

A native image wins the start and the memory, and pays at peak speed and in the build. The next lesson keeps the full JVM, JIT and all, and skips the warm-up instead."""

L = {
 "id": "boot-03",
 "title": "GraalVM native image and Quarkus native",
 "minutes": 40,
 "goal": "By the end you can explain what the closed-world assumption costs, write reachability metadata for reflection and proxies by hand, use Quarkus's annotations instead, and spot static initializers that break when the build runs them.",
 "opening": OPENING,
 "warmup": {
  "q": "The makers of Quarkus, a framework for Java services, measured one service on a normal JVM and as a native image. The native image answered its first request in 581 ms instead of 4,417 ms. What happened to the most requests per second it could handle once busy?",
  "options": ["It went up, because all the code was compiled before the program ran", "It stayed about the same", "It fell by about 59%", "It can't be measured, because native images have no JIT"],
  "answer": 2,
  "why": "Native peak throughput was 5,411 requests per second against 13,265 on the JVM. Code compiled ahead of time is compiled without the profiles a JIT gathers from the real run, so it's less specialized. Native wins start-up and memory (95 MiB against 304 MiB of RSS), not peak speed. Profile-guided optimization helps, but only in Oracle GraalVM. The first section has the whole table."
 },
 "sections": [
  {
   "h": "Native image builds a closed world",
   "body": S0,
   "figure": {"svg": FIG, "caption": "The analysis follows calls from main. A class reached only through a name in a message is in the binary only if the metadata lists it."},
   "aside": ASIDE0,
   "try": {
    "title": "A class name that only exists at run time",
    "minutes": 3,
    "steps": [
     "Read `DynamicLookupDemo`. It calls a static method with no arguments, chosen by two strings.",
     "Run it as it is, then with `-Pargs='java.util.UUID randomUUID'`. On the JVM, any class on the class path works.",
     "Ask yourself which classes a build would have to keep to support every possible argument. That's why the build needs a list.",
     "Optional, with a GraalVM JDK: run the class with `java -agentlib:native-image-agent=config-output-dir=build/ni -cp startup/build/classes/java/demo workbench.startup.l03.demo.DynamicLookupDemo java.util.UUID randomUUID`, and read the JSON the agent wrote into `build/ni`."
    ],
    "code": demo("DynamicLookupDemo"),
    "expect": "The first run prints today's date, such as `java.time.LocalDate.now() = 2026-11-17`, and the entry `{ \"reflection\": [ { \"type\": \"java.time.LocalDate\", \"methods\": [ { \"name\": \"now\", \"parameterTypes\": [] } ] } ] }`. The second prints a random UUID and the same entry for `java.util.UUID` and `randomUUID`. On the JVM both just work. A native image would work only for the class and method its metadata listed."
   },
   "refs": [
    {"title": "GraalVM: Reachability Metadata", "url": "https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/ReachabilityMetadata.md", "kind": "docs"}
   ]
  },
  {
   "h": "Reflection and proxies need reachability metadata",
   "body": S1,
   "try": {
    "title": "The order of proxy interfaces",
    "minutes": 3,
    "steps": [
     "Read `ProxyOrderDemo`. It builds three proxies: (DepotApi, AutoCloseable), (AutoCloseable, DepotApi), and the first pair again.",
     "Predict the two `same class` lines before you run it.",
     "Run it, then the Kotlin twin."
    ],
    "code": demo("ProxyOrderDemo"),
    "expect": "The first two proxies are different classes, `jdk.proxy1.$Proxy0` and `jdk.proxy1.$Proxy1`, so `same class for (A, B) and (B, A)?` prints `false`. The repeat of the first pair reuses `$Proxy0` and prints `true`, and the last line is `OUT FOR DELIVERY PX-1042`. The JVM keeps one proxy class per ordered list of interfaces, which is why the metadata lists them in order."
   },
   "refs": [
    {"title": "Reachability metadata schema v1.2.0 (JSON schema)", "url": "https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/assets/reachability-metadata-schema-v1.2.0.json", "kind": "docs"}
   ]
  },
  {
   "h": "The build is your program's first run",
   "body": S2,
   "try": {
    "title": "Values that would be frozen at build time",
    "minutes": 3,
    "steps": [
     "Read `BuildTimeInitDemo`. Two static fields are set in a class initializer.",
     "Run it twice and compare the two outputs.",
     "Now imagine the class was initialized at build time, the Quarkus default. Which line would be the same on every start of every copy, and which one would stop the build?"
    ],
    "code": demo("BuildTimeInitDemo"),
    "expect": "On the JVM each run prints a new `started at` time and a new jitter value, because the initializer runs at every start: one run printed `started at: 2026-11-17T07:11:25.498913321Z` and `retry jitter ms: 148`. Initialized at build time, `started at` would print the build's moment forever, in every copy. The `Random` in the image heap is one of the cases the builder refuses, with the \"cached seed values\" error."
   },
   "refs": [
    {"title": "GraalVM: Class Initialization in Native Image", "url": "https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/ClassInitialization.md", "kind": "docs"}
   ]
  },
  {
   "h": "Quarkus writes most of the metadata for you",
   "body": S3,
   "refs": [
    {"title": "Quarkus 3.40: Tips for writing native applications", "url": "https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/docs/src/main/asciidoc/writing-native-applications-tips.adoc", "kind": "docs"}
   ]
  }
 ],
 "compare": {
  "title": "The same event class registered from Java and from Kotlin",
  "java": {"title": "ParcelScanned.java", "src": "@RegisterForReflection\npublic record ParcelScanned(String parcelId, String depot, long weightGrams) { }\n\n// the same thing by hand in reachability-metadata.json:\n// { \"type\": \"tracker.ParcelScanned\",\n//   \"methods\": [\n//     { \"name\": \"<init>\", \"parameterTypes\": [\"java.lang.String\", \"java.lang.String\", \"long\"] },\n//     { \"name\": \"parcelId\", \"parameterTypes\": [] } ] }"},
  "kotlin": {"title": "ParcelScanned.kt", "src": "@RegisterForReflection\ndata class ParcelScanned(val parcelId: String, val depot: String, val weightGrams: Long)\n\n// the same thing by hand: the accessor is a getter on the JVM\n// { \"type\": \"tracker.ParcelScanned\",\n//   \"methods\": [\n//     { \"name\": \"<init>\", \"parameterTypes\": [\"java.lang.String\", \"java.lang.String\", \"long\"] },\n//     { \"name\": \"getParcelId\", \"parameterTypes\": [] } ] }"},
  "note": "The annotation is the same, and Quarkus reads it the same way from both languages. What differs is the bytecode it describes. A Java record has an accessor named `parcelId()`. A Kotlin `val parcelId` compiles to a private field and a method named `getParcelId()`. Hand-written metadata names JVM members, so the two entries differ even though the sources look alike. A non-null Kotlin `Long` is the primitive `long` in the constructor's signature; `Long?` would be `java.lang.Long`. Annotation arrays are `{...}` with `.class` in Java and `[...]` with `::class` in Kotlin."
 },
 "worked": {
  "title": "Write the metadata for a scan decoder",
  "steps": [
   {"say": "Here is the tracking service's decoder: each message from a depot names its event class in a header. Find every reflective call and, for each one, the exact member it needs. Ignore code that names a class in the source, such as `new` or a direct method call: the analysis sees those.",
    "code": "Object decode(Message msg) throws ReflectiveOperationException {\n    Class<?> type = Class.forName(msg.header(\"type\"));                          // 1\n    Object event = type.getConstructor(String.class, String.class, long.class)   // 2\n            .newInstance(msg.parcelId(), msg.depot(), msg.weightGrams());\n    log.info(type.getMethod(\"parcelId\").invoke(event));                         // 3\n    return event;\n}",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "fun decode(msg: Message): Any {\n    val type = Class.forName(msg.header(\"type\"))                                // 1\n    val event = type.getConstructor(String::class.java, String::class.java, Long::class.javaPrimitiveType)  // 2\n        .newInstance(msg.parcelId(), msg.depot(), msg.weightGrams())\n    log.info(type.getMethod(\"parcelId\").invoke(event))                          // 3\n    return event\n}"},
   {"say": "There are three needs: (1) the class by name, for every event type a depot can send; (2) its `(String, String, long)` constructor; (3) its `parcelId()` method. Say the depots send `ParcelScanned` and `ParcelDelivered`. Each gets one entry, and the condition limits them to binaries where the decoder is used.",
    "code": "{\n  \"reflection\": [\n    {\n      \"condition\": { \"typeReached\": \"tracker.EventDecoder\" },\n      \"type\": \"tracker.ParcelScanned\",\n      \"methods\": [\n        { \"name\": \"<init>\", \"parameterTypes\": [\"java.lang.String\", \"java.lang.String\", \"long\"] },\n        { \"name\": \"parcelId\", \"parameterTypes\": [] }\n      ]\n    },\n    {\n      \"condition\": { \"typeReached\": \"tracker.EventDecoder\" },\n      \"type\": \"tracker.ParcelDelivered\",\n      \"methods\": [\n        { \"name\": \"<init>\", \"parameterTypes\": [\"java.lang.String\", \"java.lang.String\", \"long\"] },\n        { \"name\": \"parcelId\", \"parameterTypes\": [] }\n      ]\n    }\n  ]\n}",
    "lang": "json"},
   {"say": "Put the file at `src/main/resources/META-INF/native-image/com.example/tracker/reachability-metadata.json`, the `<groupId>/<artifactId>` folder. In a Quarkus service, the annotation does the same job, and it moves with the class when someone renames it. That's the version to prefer.",
    "code": "@RegisterForReflection\npublic record ParcelScanned(String parcelId, String depot, long weightGrams) { }\n\n@RegisterForReflection\npublic record ParcelDelivered(String parcelId, String depot, long weightGrams) { }",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "@RegisterForReflection\ndata class ParcelScanned(val parcelId: String, val depot: String, val weightGrams: Long)\n\n@RegisterForReflection\ndata class ParcelDelivered(val parcelId: String, val depot: String, val weightGrams: Long)"},
   {"say": "Prove it in the shared build. Build the native binary and run the integration tests against it, with missing registrations turned into a hard exit. A new event type that nobody registered now fails the build, not a parcel at three in the morning.",
    "code": "./mvnw verify -Dnative \\\n  -Dquarkus.native.additional-build-args=--exact-reachability-metadata\n# and start the binary under test with -XX:MissingRegistrationReportingMode=Exit",
    "lang": "bash"}
  ]
 },
 "lab": {
  "title": "Write reachability metadata for a class and a proxy",
  "minutes": 15,
  "files": [
   "labs/startup/src/main/resources/META-INF/native-image/workbench/startup/reachability-metadata.json",
   "labs/startup/src/main/java/workbench/startup/l03/MetadataWriter.java"
  ],
  "run": "./gradlew :startup:test --tests 'workbench.startup.l03.*'",
  "steps": [
   "Run the tests once. Eight of the ten fail. Two `MetadataFileTest` checks pass already, because the empty file you start with has a valid shape.",
   "Read `EventDecoder` and `DepotClients`. Write down every reflective call: which class, which constructor (with its parameter types), which methods, and which proxy interfaces in which order.",
   "Edit `reachability-metadata.json` by hand. Add one reflection entry for `workbench.startup.l03.ParcelScanned` with its `<init>` and the three accessors from `EventDecoder.ACCESSORS`, and one entry whose type is `{\"proxy\": [...]}`. Run `MetadataFileTest` until it passes.",
   "Implement `MetadataWriter.reflection` and `MetadataWriter.proxy`, so the same entries can be generated from `Class` objects. Run all ten tests."
  ],
  "hints": [
   "A method entry needs both keys, even with no parameters: `{\"name\": \"depot\", \"parameterTypes\": []}`.",
   "`Class.getName()` gives exactly the names the schema wants: `java.lang.String` for a class, `long` for a primitive.",
   "`m instanceof Constructor<?>` tells a constructor from a method. `Class.isInterface()` and a `HashSet` cover the two proxy rules."
  ],
  "done_when": "All ten tests in `MetadataFileTest` and `MetadataWriterTest` pass."
 },
 "drill": {
  "title": "Two entries from memory",
  "minutes": 4,
  "prompt": "Close this page. Write a `reachability-metadata.json` that registers (1) a JDK proxy over `com.example.library.CatalogClient` and `java.io.Closeable`, in that order, and (2) the `(java.lang.String, long)` constructor of `com.example.library.Loan`, active only once `com.example.library.LoanListener` is reached. Then check: how many top-level keys did you use?",
  "answer": {
   "lang": "json",
   "src": "{\n  \"reflection\": [\n    {\n      \"type\": { \"proxy\": [\"com.example.library.CatalogClient\", \"java.io.Closeable\"] }\n    },\n    {\n      \"condition\": { \"typeReached\": \"com.example.library.LoanListener\" },\n      \"type\": \"com.example.library.Loan\",\n      \"methods\": [\n        { \"name\": \"<init>\", \"parameterTypes\": [\"java.lang.String\", \"long\"] }\n      ]\n    }\n  ]\n}"
  }
 },
 "recap": [
  "Native image (GraalVM or Mandrel; a plain OpenJDK can't build one) analyzes the program from `main` and keeps only reachable code. It starts in milliseconds with a small RSS, but has no JIT, so peak throughput is lower (59% lower in Quarkus's benchmark), and builds take minutes and gigabytes.",
  "Whatever the analysis can't see (reflection by a run-time name, proxies, resources, JNI, serialization) must be listed in `META-INF/native-image/<groupId>/<artifactId>/reachability-metadata.json`.",
  "Schema v1.2.0 has only `reflection`, `resources`, `foreign` and `comment` at the top. A proxy is a reflection entry with `\"type\": {\"proxy\": [interfaces in order]}`, and a constructor is `<init>`.",
  "The build runs static initializers, and Quarkus does it for all classes by default: their values are frozen into the binary. Use `--initialize-at-run-time`, or compute per-copy values at start-up.",
  "In Quarkus, prefer `@RegisterForReflection` (with `targets` for a library's classes) and `@RegisterForProxy` to hand-written JSON, and test the native binary in your shared build.",
  "The limit: a native image can never run a class the build didn't see, and it gives up the JIT's peak speed. Keeping the full JVM while skipping warm-up needs another tool, the next lesson's."
 ],
 "closing": "We started with a pop-up stall packed at a factory, which opens at once and sells only what was packed. A native image is built the same way, from every call it can follow from `main`. Anything your code finds by name needs an entry on the list, and anything an initializer computes keeps the factory's value forever.\n\nNow search your code for `Class.forName(`, `getMethod(`, `newProxyInstance`, and `static final` fields set from the clock or a random number. Each is a question the native build will ask.\n\nNext, we'll keep the full JVM and skip the warm-up instead. What does CRaC save when it photographs a running JVM, and what must let go before the camera clicks?",
 "quiz": [
  {"q": "Code calls `Proxy.newProxyInstance(loader, new Class<?>[] {A.class, B.class}, h)`, and elsewhere the same with `{B.class, A.class}`. On a normal JVM, how many proxy classes exist, and what does that mean for native-image metadata?",
   "options": ["One class, so one proxy entry covers both", "Two classes, so you need two proxy entries, each with its own interface order", "None until the first method call", "Two classes, but the metadata only needs the set of interfaces, not their order"],
   "answer": 1,
   "from": "cls-04",
   "why": "The JDK defines one proxy class per ordered list of interfaces, so (A, B) and (B, A) are different classes; the demo prints `$Proxy0` and `$Proxy1`. Native-image metadata describes proxy classes the same way, as ordered lists, so each order needs its own entry."},
  {"q": "Which of these calls needs a reachability metadata entry in a native image?",
   "options": ["`Class.forName(\"tracker.ParcelScanned\")`, with the name written in the code", "`new ParcelScanned(...)`", "`Class.forName(msg.header(\"type\"))` in a message decoder", "A lambda passed to `stream().map(...)`"],
   "answer": 2,
   "why": "The analysis handles reflective calls whose arguments are constants, and it sees `new` and lambdas directly. A class name that arrives in a message header can't be known at build time, so the class, and the members used on it, must be listed."},
  {"q": "A Quarkus native service has `static final Instant BOOTED = Instant.now();` in an ordinary class, with default settings, and its health check reports `BOOTED`. What do copies started on different days show?",
   "options": ["The same time in every copy: the moment the native binary was built", "Each copy's own start time", "The build fails with an image-heap error", "`null`, because static fields aren't set in native images"],
   "answer": 0,
   "why": "Quarkus initializes all classes at build time by default, so the initializer runs once, inside the build, and the `Instant` is stored in the image heap. The builder rejects some objects, such as a `Random`, but a timestamp is an ordinary value. Mark the class with `--initialize-at-run-time`, or compute the value when the program starts."},
  {"q": "A colleague's `reachability-metadata.json` has a top-level `\"proxy\": [[\"tracker.DepotClient\", \"java.io.Closeable\"]]`, copied from an old example. With GraalVM's schema v1.2.0, what's the fix?",
   "options": ["Nothing, `proxy` is a valid top-level section", "Rename the file to `proxy-config.json`", "Replace it with `allPublicMethods: true`", "Move it into `reflection`, as `{\"type\": {\"proxy\": [\"tracker.DepotClient\", \"java.io.Closeable\"]}}`"],
   "answer": 3,
   "why": "Schema v1.2.0 allows only `reflection`, `resources`, `foreign` and `comment` at the top level. A proxy is a reflection entry whose `type` is an object with a `proxy` list. Legacy files such as `proxy-config.json` aren't supported in Quarkus 4.0, and `allPublicMethods` on an interface doesn't define a proxy class."},
  {"q": "A service reads messages all day at high load. It restarts about once a week, and a six-second start hurts nobody. Which runtime fits best?",
   "options": ["A native image, for the smallest RSS", "The normal JVM, with an AOT cache if you want a shorter start", "A native image with build-time initialization of everything", "A native image with profile-guided optimization in GraalVM Community Edition"],
   "answer": 1,
   "why": "This service lives on peak throughput and barely restarts, which is where the JIT wins: Quarkus's benchmark shows native at 59% lower peak. An AOT cache shortens the start with no code change and cost about 7% of peak in the same benchmark. Profile-guided optimization isn't available in GraalVM Community Edition at all."}
 ],
 "flashcards": [
  {"front": "What is native image's closed-world assumption?", "back": "All code is known at build time. The analysis keeps only what it can reach from `main`; anything used only through reflection, proxies or resource names must be listed in metadata."},
  {"front": "Where does `reachability-metadata.json` go?", "back": "In `META-INF/native-image/<groupId>/<artifactId>/` on the class path."},
  {"front": "How do you list a JDK dynamic proxy in schema v1.2.0?", "back": "As a reflection entry: `{\"type\": {\"proxy\": [\"tracker.DepotClient\", \"java.io.Closeable\"]}}`, with the interfaces in the order the code uses."},
  {"front": "How is a constructor written in a `methods` entry?", "back": "`{\"name\": \"<init>\", \"parameterTypes\": [\"java.lang.String\", \"long\"]}`: fully qualified class names, primitives by name."},
  {"front": "What does Quarkus do with static initializers in native mode by default?", "back": "It runs them at build time. The values they compute are stored in the image heap, and every start sees the same ones."},
  {"front": "What do you need to build a native image?", "back": "GraalVM (Oracle GraalVM or GraalVM Community Edition) or Mandrel. A plain OpenJDK has no `native-image` tool."},
  {"front": "`@RegisterForReflection(targets = {X.class})` on class `Config`: which class gets registered?", "back": "`X`, not `Config`. That's how you register a library's classes you can't annotate."}
 ],
 "terms": [
  {"term": "Native image", "plain": "A standalone executable built ahead of time from your class path by GraalVM or Mandrel."},
  {"term": "Closed-world assumption", "plain": "The rule that all code a native image will run is known at build time."},
  {"term": "Reflection", "plain": "Code that looks up classes, methods and fields by name while the program runs."},
  {"term": "Reachability metadata", "plain": "The list of classes, members, proxies and resources the build must keep because only dynamic code uses them."},
  {"term": "Image heap", "plain": "Objects created at build time, stored in the executable and mapped into memory at start-up."},
  {"term": "Build-time initialization", "plain": "Running a class's static initializer during the build instead of at each start."},
  {"term": "Tracing agent", "plain": "A JVM agent (`-agentlib:native-image-agent`) that records the reflection, proxies and resources a run uses."},
  {"term": "Mandrel", "plain": "A GraalVM-based distribution of native image tailored for Quarkus."}
 ],
 "explain_back": {
  "prompt": "Explain to a friend why a native image needs metadata for the event class your decoder creates by reflection, but not for a class your code creates with `new`, and what Quarkus gives you so you don't write the JSON by hand.",
  "answer": "The native build analyzes the program from `main` and keeps only code it can prove is reachable. A `new ParcelScanned(...)` is right there in the bytecode, so the analysis sees the class and its constructor. The decoder instead calls `Class.forName` with a name from the message header, then `getConstructor` and `getMethod`, so the build can't know which class or which members until the message arrives. Unless the class and those members are listed in reachability metadata, they're left out, and the call fails at run time with a registration error. In Quarkus, the extensions register what their libraries need, and I add `@RegisterForReflection` to my event classes, with `targets` for classes from a library, and `@RegisterForProxy` for proxies. Quarkus turns those into the metadata file during the build."
 },
 "deeper": {
  "minutes": 10,
  "body": "Some details for when you go native for real.\n\nConditions are precise. `\"condition\": {\"typeReached\": \"tracker.EventDecoder\"}` makes an entry active when that type is reached at run time, which the docs define as \"right before the class-initialization routine starts for that type\", or when one of its subtypes is reached. Writing `EventDecoder.class` doesn't reach it. Conditions mostly help library authors ship metadata that costs nothing in programs that never use the feature.\n\nResources use globs: `{\"resources\": [{\"glob\": \"META-INF/**/*.properties\"}, {\"bundle\": \"tracker.Messages\"}]}`. In Quarkus, use `quarkus.native.resources.includes` instead.\n\nThe heap needs a limit. Without an explicit maximum, a native image sets the maximum Java heap to 80% of the physical memory, according to the GraalVM memory docs. In a container, pass `-Xmx` (or `-XX:MaximumHeapSizePercent`) yourself. The default collector is Serial. `--gc=G1` needs Oracle GraalVM on Linux, and `--gc=epsilon` never frees memory, which only makes sense for short jobs.\n\nPGO, in Oracle GraalVM only, is a three-step build: `native-image --pgo-instrument ...` builds an instrumented binary, you run it on a real workload so it writes a `.iprof` profile when it exits, and `native-image --pgo=app.iprof ...` builds the optimized binary. That's the same idea as Leyden's training run, applied to compiled code.\n\nThe JDK is moving toward some of these gains without leaving the JVM. Lesson 2's AOT cache already ships linked classes and profiles, and JEP 544, in development for JDK 28, adds compiled code to the cache while keeping the JIT. Native image stays the option when the binary's size and start time, not the JVM's, are the limit."
 },
 "sources": [
  {"title": "GraalVM: Reachability Metadata", "url": "https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/ReachabilityMetadata.md"},
  {"title": "GraalVM: Class Initialization in Native Image", "url": "https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/ClassInitialization.md"},
  {"title": "Quarkus 3.40: Tips for writing native applications", "url": "https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/docs/src/main/asciidoc/writing-native-applications-tips.adoc"},
  {"title": "Quarkus: Building a native executable (includes the JVM, AOT and native benchmark table)", "url": "https://github.com/quarkusio/quarkus/blob/main/docs/src/main/asciidoc/building-native-image.adoc"}
 ]
}
out = ROOT / "content/lessons/boot-03.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
