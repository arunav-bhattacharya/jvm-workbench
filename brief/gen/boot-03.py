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


FIG = (
    '<svg viewBox="0 0 700 250" role="img" aria-label="Native image build: the analysis starts at main and keeps reachable code; '
    'classes reached only by reflection or proxies are kept only if the metadata file lists them.">'
    '<text class="t-s t-m" x="20" y="22">build time (minutes)</text>'
    '<rect class="box-a" x="20" y="36" width="110" height="40" rx="8"/>'
    '<text class="t t-code" x="75" y="61" text-anchor="middle">main()</text>'
    '<line class="ln" x1="130" y1="56" x2="172" y2="56" marker-end="url(#arr)"/>'
    '<rect class="box" x="175" y="36" width="130" height="40" rx="8"/>'
    '<text class="t-s" x="240" y="61" text-anchor="middle">PaymentService</text>'
    '<line class="ln" x1="305" y1="56" x2="347" y2="56" marker-end="url(#arr)"/>'
    '<rect class="box" x="350" y="36" width="120" height="40" rx="8"/>'
    '<text class="t-s" x="410" y="61" text-anchor="middle">EventDecoder</text>'
    '<line class="ln-d" x1="410" y1="76" x2="410" y2="112"/>'
    '<text class="t-s t-bad" x="520" y="100" text-anchor="middle">Class.forName(header)</text>'
    '<rect class="box-ok" x="300" y="116" width="220" height="40" rx="8"/>'
    '<text class="t-s" x="410" y="141" text-anchor="middle">PaymentAuthorized: listed</text>'
    '<rect class="box-dim" x="540" y="116" width="150" height="40" rx="8"/>'
    '<text class="t-s" x="615" y="141" text-anchor="middle">RefundIssued: not listed</text>'
    '<rect class="box-b" x="20" y="116" width="250" height="40" rx="8"/>'
    '<text class="t-s t-code" x="145" y="141" text-anchor="middle">reachability-metadata.json</text>'
    '<line class="ln-a" x1="270" y1="136" x2="297" y2="136" marker-end="url(#arr)"/>'
    '<line class="ln-d" x1="20" y1="176" x2="690" y2="176"/>'
    '<text class="t-s t-m" x="20" y="198">run time (milliseconds)</text>'
    '<rect class="box-ok" x="300" y="206" width="220" height="34" rx="8"/>'
    '<text class="t-s" x="410" y="228" text-anchor="middle">decodes as on the JVM</text>'
    '<rect class="box-bad" x="540" y="206" width="150" height="34" rx="8"/>'
    '<text class="t-s" x="615" y="228" text-anchor="middle">registration error</text>'
    '<line class="ln" x1="410" y1="156" x2="410" y2="204" marker-end="url(#arr)"/>'
    '<line class="ln-bad" x1="615" y1="156" x2="615" y2="204" marker-end="url(#arr)"/>'
    '</svg>'
)

S1 = """Lesson 2's AOT cache makes the JVM start faster, but it is still a JVM: it maps classes, links what training missed, interprets, and waits for the JIT. In Quarkus's benchmark below, the first request still took 1,859 ms with the cache. Native image removes that work from the start by doing it all in the build.

`native-image`, from GraalVM or from Mandrel (the distribution "tailored for Quarkus"), takes your class path and builds one executable for one OS and CPU, in three steps. First it analyzes: starting at `main`, it follows every method call and field access it can see, and works out which classes can show up at each call. Second it runs static initializers where it can, and saves the objects they created into the **image heap**, a section of the executable that is mapped into memory at start-up. Third it compiles every reachable method to machine code. Code the analysis never reached is left out, and so are the JDK classes nothing uses. This is the **closed-world assumption**: everything the program will ever run is known when you build it.

The binary runs on a small runtime, SubstrateVM, with no class loading, no bytecode verification, no interpreter and no JIT. That is why it starts fast and stays small. The Quarkus docs publish a tuned benchmark (Quarkus 3.34.3, JDK 25.0.2):

| | JVM | JVM + AOT cache | Native (Mandrel) |
|---|---|---|---|
| Time to first request | 4,417 ms | 1,859 ms | 581 ms |
| Peak throughput | 13,265 tps | 12,389 tps | 5,411 tps |
| RSS | 304 MiB | 240 MiB | 95 MiB |
| Build | about 30 s | build plus a training run | 3 to 10 min, 4 to 8 GB of RAM |

Peak throughput is 59% lower. With no JIT there are no run-time profiles, and GraalVM's own docs say that "without profiling information, it is difficult to generate machine code of the same quality as a JIT compiler". Profile-guided optimization (PGO: building again with profiles recorded from a test run) narrows the gap, but "PGO is not available in GraalVM Community Edition". The default garbage collector is Serial, a single-threaded collector "optimized for low footprint and small Java heap sizes"; G1 is available only in Oracle GraalVM, on Linux.

The other price is everything the analysis can't see: reflection, dynamic proxies, resources loaded by name, JNI (calls into native C code) and serialization. The analysis copes with constants. GraalVM works out reflective calls at build time "given that all the call arguments are constant", so `Class.forName("com.acme.pay.Fees")` with a literal just works. `Class.forName(record.headers().get("type"))` does not: the class name arrives with the Kafka message, and the build can't know it. You have to tell the build, or the call fails at run time. Current GraalVM throws `MissingReflectionRegistrationError`, which "extends `java.lang.Error` and should not be handled"."""

S2 = """You tell the build in `reachability-metadata.json`, placed in `META-INF/native-image/<groupId>/<artifactId>/` on the class path. The current schema is v1.2.0, and its top level has four keys: `reflection`, `resources`, `foreign` and `comment`. Proxies, serialization and JNI all live inside `reflection` entries.

A reflection entry names a type and the members your code uses:

```json
{
  "reflection": [
    {
      "condition": { "typeReached": "com.acme.pay.EventDecoder" },
      "type": "com.acme.pay.PaymentAuthorized",
      "methods": [
        { "name": "<init>", "parameterTypes": ["java.lang.String", "java.lang.String", "long"] },
        { "name": "paymentId", "parameterTypes": [] }
      ]
    }
  ]
}
```

A constructor is called `<init>`. Parameter types are fully qualified, primitives by name (`long`, `int`), and every method needs `parameterTypes`, even an empty one. Instead of listing members you can set `allDeclaredConstructors` or `allPublicMethods`, which keeps more code in the binary. The optional `condition` switches the entry on only once `EventDecoder` is reached at run time, which means just before its initializer starts; `EventDecoder.class` on its own doesn't count.

A JDK dynamic proxy is a reflection entry whose type is an ordered list of interfaces:

```json
{ "reflection": [ { "type": { "proxy": ["com.acme.pay.CardIssuerClient", "java.lang.AutoCloseable"] } } ] }
```

The order is part of the proxy's identity: a proxy for (A, B) is a different class from one for (B, A). If the proxy gets serialized, add `"serializable": true`; the docs say proxies "can only be registered for serialization via the JSON files".

Two warnings about documentation. The older schema, v1.1.0, had separate top-level `jni` and `serialization` sections, and some GraalVM prose still shows a top-level `jni` array; v1.2.0 rejects it. The current Quarkus main-branch docs say to use "a `proxy` section", which v1.2.0 also rejects. Check your file against the schema of the GraalVM you build with.

You rarely write all of it by hand. The tracing agent watches a run on a normal JVM and writes what it saw: `java -agentlib:native-image-agent=config-output-dir=build/ni-config -jar app.jar`. Like an AOT training run, it only sees the code paths you exercise, so drive it with your integration tests and then read what it wrote. To make gaps fail loudly, build with `--exact-reachability-metadata` and run the tests with `-XX:MissingRegistrationReportingMode=Exit`."""

S3 = """Class initialization is the other half of the story. GraalVM's docs give the numbers: "the simple 'Hello, World!' application requires more than 300 classes to be initialized", and in code compiled ahead of time, the check "is this class initialized yet?" on every access "can reduce performance by more than twofold". So the builder runs static initializers **at build time** where it can, and stores what they produced in the image heap.

Plain GraalVM initializes most JDK classes at build time, and your classes only when it can prove that safe. An initializer that calls native code (`System.out.println` counts), makes a virtual call it can't pin to one target, or reaches a substituted method stays at run time. Quarkus goes further: "By default, Quarkus initializes all classes at build time."

So your static initializer runs on the build machine, once, and its results are frozen into the binary:

```java
static final Instant STARTED_AT = Instant.now();   // the build's time, on every start
static final Random JITTER = new Random();         // the builder refuses this one
```

```kotlin
val startedAt: Instant = Instant.now()             // the build's time, on every start
val jitter = Random()                              // the builder refuses this one
```

The builder catches some of these. Quarkus lists two errors you are likely to meet: "Detected an instance of Random/SplittableRandom class in the image heap. Instances created during image generation have cached seed values", and "No instances are allowed in the image heap for a class that is initialized or reinitialized at image runtime: sun.security.provider.NativePRNG". Don't count on it for the rest. A timestamp, a hostname, a token fetched at start: whatever an initializer computes, every container started from that image sees the value from the build.

The fix is to initialize that class at run time:

```properties
quarkus.native.additional-build-args=--initialize-at-run-time=com.acme.pay.InstanceInfo\\\\,com.acme.pay.RetryJitter
```

Quarkus needs the comma escaped. With plain `native-image` the options are `--initialize-at-run-time=` and `--initialize-at-build-time=`, and `-H:+PrintClassInitialization` reports what was initialized where. Better still, keep per-instance values out of static initializers, and compute them in a method that runs at start-up."""

S4 = """In a Quarkus app you rarely touch the JSON. Quarkus extensions know what their libraries reflect on, and Quarkus generates `reachability-metadata.json` itself. Your part is the classes only your code knows about, and annotations are the way to declare them:

```java
@RegisterForReflection
public record PaymentAuthorized(String paymentId, String currency, long amountMinor) { }

@RegisterForReflection(targets = {IssuerResponse.class, IssuerError.class})   // a library's classes
public class IssuerReflectionConfig { }

@RegisterForProxy(targets = {CardIssuerClient.class, AutoCloseable.class})    // order matters
public class IssuerProxyConfig { }
```

```kotlin
@RegisterForReflection
data class PaymentAuthorized(val paymentId: String, val currency: String, val amountMinor: Long)

@RegisterForReflection(targets = [IssuerResponse::class, IssuerError::class])  // a library's classes
class IssuerReflectionConfig

@RegisterForProxy(targets = [CardIssuerClient::class, AutoCloseable::class])   // order matters
class IssuerProxyConfig
```

`@RegisterForReflection` registers methods and fields by default, plus any nested classes unless you set `ignoreNested = true`. With `targets` it registers the listed classes and not the class it sits on, which is how you cover a library's classes that you can't annotate. `serialization = true` adds Java serialization. `@RegisterForProxy` takes the interfaces in order, and the Quarkus docs repeat that "the order of the specified proxy interfaces is significant". Resources go in `application.properties`: `quarkus.native.resources.includes=templates/**,rates/*.csv`.

When you do need JSON, put it in `src/main/resources/META-INF/native-image/<group-id>/<artifact-id>/`; the current docs warn that Quarkus overwrites a file placed directly in `META-INF/native-image/`. The Quarkus 3.x guides still show the older separate files, `reflect-config.json` and `proxy-config.json`, while the 4.0 guides say those legacy files "are not supported". Write the unified `reachability-metadata.json` and the file survives the upgrade.

`./mvnw verify -Dnative` builds the binary and runs your `@QuarkusIntegrationTest`s against it. Because a native build takes minutes and gigabytes, most teams run it in CI and develop in JVM mode. Quarkus's own advice is "Start with JVM mode. Move to native when you have a concrete need." Lesson 4 of this track turns that into a decision table.

Check before the lab: your event classes live in a shared `payment-events` JAR that another team owns, so you can't annotate them. Which annotation do you add, and on which class? (`@RegisterForReflection(targets = {...})` on any class in your own code, listing their classes; the class carrying the annotation is not registered itself.)"""

L = {
 "id": "boot-03",
 "title": "GraalVM native image and Quarkus native",
 "minutes": 40,
 "goal": "By the end you can explain what the closed-world assumption costs, write reachability metadata for reflection and proxies by hand, use Quarkus's annotations instead, and spot static initializers that break when the build runs them.",
 "warmup": {
  "q": "Quarkus's perf lab ran one service in JVM mode and as a native binary. The native binary answered its first request in 581 ms instead of 4,417 ms. What happened to its peak throughput?",
  "options": ["It went up, because all the code was compiled ahead of time", "It stayed about the same", "It fell by about 59%", "It can't be measured, because native binaries have no JIT"],
  "answer": 2,
  "why": "Native peak throughput was 5,411 tps against 13,265 tps on the JVM. Ahead-of-time code is compiled without the run-time profiles the JIT uses, so it is less specialized. Native wins start-up and memory (95 MiB against 304 MiB RSS), not peak speed. Profile-guided optimization helps, but only in Oracle GraalVM."
 },
 "sections": [
  {
   "h": "Native image builds a closed world",
   "body": S1,
   "figure": {"svg": FIG, "caption": "The analysis follows calls from main. A class reached only through a name in the data is in the binary only if the metadata lists it."},
   "try": {
    "title": "A class name that only exists at run time",
    "minutes": 3,
    "steps": [
     "Read `DynamicLookupDemo`. It calls a static no-argument method chosen by two strings.",
     "Run it as is, then with `-Pargs='java.util.UUID randomUUID'`. Any class on the class path works on the JVM.",
     "Ask yourself which classes a build would have to keep to support every possible argument. That is why the build needs a list.",
     "Optional, needs a GraalVM JDK: run the class with `java -agentlib:native-image-agent=config-output-dir=build/ni -cp startup/build/classes/java/demo workbench.startup.l03.demo.DynamicLookupDemo java.util.UUID randomUUID` and look at the JSON the agent wrote into `build/ni`."
    ],
    "code": demo("DynamicLookupDemo"),
    "expect": "The first run prints today's date and the entry `{ \"type\": \"java.time.LocalDate\", \"methods\": [ { \"name\": \"now\", \"parameterTypes\": [] } ] }`. The second prints a random UUID and an entry for `java.util.UUID` and `randomUUID`. On the JVM both just work. A native image would work only for the class and method its metadata listed."
   },
   "refs": [
    {"title": "GraalVM: Reachability Metadata", "url": "https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/ReachabilityMetadata.md", "kind": "docs"}
   ]
  },
  {
   "h": "Reflection and proxies need reachability metadata",
   "body": S2,
   "try": {
    "title": "The order of proxy interfaces",
    "minutes": 3,
    "steps": [
     "Read `ProxyOrderDemo`. It builds three proxies: (IssuerApi, AutoCloseable), (AutoCloseable, IssuerApi), and the first pair again.",
     "Predict the two `same class` lines before you run it.",
     "Run it, then the Kotlin twin."
    ],
    "code": demo("ProxyOrderDemo"),
    "expect": "The first two proxies are different classes, `jdk.proxy1.$Proxy0` and `jdk.proxy1.$Proxy1`, so `same class for (A, B) and (B, A)?` prints `false`. The repeat of the first pair reuses `$Proxy0` and prints `true`. The JVM caches one proxy class per ordered interface list, which is why the metadata lists interfaces in order."
   },
   "refs": [
    {"title": "Reachability metadata schema v1.2.0 (JSON schema)", "url": "https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/assets/reachability-metadata-schema-v1.2.0.json", "kind": "docs"}
   ]
  },
  {
   "h": "The build is your program's first run",
   "body": S3,
   "try": {
    "title": "Values that would be frozen at build time",
    "minutes": 3,
    "steps": [
     "Read `BuildTimeInitDemo`. Two static fields are set in a class initializer.",
     "Run it twice and compare the output of the two runs.",
     "Now imagine the class was initialized at build time, the Quarkus default. Which line would be the same on every start of every pod, and which one would stop the build?"
    ],
    "code": demo("BuildTimeInitDemo"),
    "expect": "On the JVM each run prints a new `started at` time and a new jitter value, because the initializer runs at every start. Initialized at build time, `started at` would print the build's timestamp forever, in every container. The `Random` in the image heap is one of the cases the builder refuses, with the \"cached seed values\" error."
   },
   "refs": [
    {"title": "GraalVM: Class Initialization in Native Image", "url": "https://github.com/oracle/graal/blob/master/docs/reference-manual/native-image/ClassInitialization.md", "kind": "docs"}
   ]
  },
  {
   "h": "Quarkus writes most of the metadata for you",
   "body": S4,
   "refs": [
    {"title": "Quarkus 3.40: Tips for writing native applications", "url": "https://raw.githubusercontent.com/quarkusio/quarkus/3.40.1.1/docs/src/main/asciidoc/writing-native-applications-tips.adoc", "kind": "docs"}
   ]
  }
 ],
 "analogy": "A JVM is a library with every book on the shelves: you can ask for any title, at any time. A native image is a printed booklet with only the pages someone proved you will read, bound in one cover. It is thin and opens instantly. But if your code looks up a page by a name that arrives in a message, the page has to be on the list you gave the printer, or it isn't in the booklet. Build-time initialization is the printer filling in the blanks on some pages before binding, so a date written there is the printing date. The analogy breaks on speed: a booklet is read faster than a library is searched, but a native binary runs hot code slower than a warmed JVM, because no one rewrites the pages after watching how you read.",
 "in_your_world": "A Kafka consumer in a payments service is the classic native trap: the deserializer picks the event class from a header, Jackson creates it and calls its accessors by reflection, and a REST client to the card issuer is a dynamic proxy. In Quarkus the extensions register what they know about, and you add `@RegisterForReflection` to your event classes, or `targets = [...]` for event classes from a shared schema library you can't annotate. Look for static state that must differ per pod: an instance id for idempotency keys, a start timestamp in health output, a `SecureRandom` for nonces. Under build-time initialization they'd be the same in every pod, and some won't even build. Native pays off for scale-to-zero functions and for packing many small services on a node. For a consumer that runs all day at high throughput, the 59% lower peak in Quarkus's benchmark is usually the deciding number.",
 "mistake": "The usual mistake is copying a metadata snippet from an old blog post or from a different GraalVM version and trusting it. A top-level `\"proxy\"` or `\"jni\"` array, or a `reflect-config.json` dropped into a Quarkus 4 project, either fails schema v1.2.0 or is ignored, and the proxy or class it was meant to cover fails at run time in the one code path your smoke test didn't hit. Write proxies as reflection entries with `\"type\": {\"proxy\": [...]}`, prefer `@RegisterForReflection` and `@RegisterForProxy` in Quarkus, and run the native integration tests with `-XX:MissingRegistrationReportingMode=Exit` so a gap fails the build instead of a payment.",
 "compare": {
  "title": "The same event class registered from Java and from Kotlin",
  "java": {"title": "PaymentAuthorized.java", "src": "@RegisterForReflection\npublic record PaymentAuthorized(String paymentId, String currency, long amountMinor) { }\n\n// the same thing by hand in reachability-metadata.json:\n// { \"type\": \"com.acme.pay.PaymentAuthorized\",\n//   \"methods\": [\n//     { \"name\": \"<init>\", \"parameterTypes\": [\"java.lang.String\", \"java.lang.String\", \"long\"] },\n//     { \"name\": \"paymentId\", \"parameterTypes\": [] } ] }"},
  "kotlin": {"title": "PaymentAuthorized.kt", "src": "@RegisterForReflection\ndata class PaymentAuthorized(val paymentId: String, val currency: String, val amountMinor: Long)\n\n// the same thing by hand: the accessor is a getter on the JVM\n// { \"type\": \"com.acme.pay.PaymentAuthorized\",\n//   \"methods\": [\n//     { \"name\": \"<init>\", \"parameterTypes\": [\"java.lang.String\", \"java.lang.String\", \"long\"] },\n//     { \"name\": \"getPaymentId\", \"parameterTypes\": [] } ] }"},
  "note": "The annotation is the same, and Quarkus reads it the same way from both languages. What differs is the bytecode it describes. A Java record has an accessor named `paymentId()`. A Kotlin `val paymentId` compiles to a private field and a method named `getPaymentId()`. Hand-written metadata names JVM members, so the two entries differ even though the sources look alike. A non-null Kotlin `Long` is the primitive `long` in the constructor's signature; `Long?` would be `java.lang.Long`. Annotation arrays are `{...}` with `.class` in Java and `[...]` with `::class` in Kotlin."
 },
 "worked": {
  "title": "Write the metadata for a Kafka event decoder",
  "steps": [
   {"say": "Here is the decoder. Find every reflective call and, for each, the exact member it needs. Ignore code that uses classes by name in source, such as `new` or a direct method call: the analysis sees those.",
    "code": "Object decode(ConsumerRecord<String, String> rec) throws ReflectiveOperationException {\n    Class<?> type = Class.forName(new String(rec.headers().lastHeader(\"type\").value()));   // 1\n    Object event = type.getConstructor(String.class, String.class, long.class)                 // 2\n            .newInstance(rec.key(), currencyOf(rec), amountOf(rec));\n    audit.log(type.getMethod(\"paymentId\").invoke(event));                                     // 3\n    return event;\n}",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "fun decode(rec: ConsumerRecord<String, String>): Any {\n    val type = Class.forName(String(rec.headers().lastHeader(\"type\").value()))              // 1\n    val event = type.getConstructor(String::class.java, String::class.java, Long::class.javaPrimitiveType)  // 2\n        .newInstance(rec.key(), currencyOf(rec), amountOf(rec))\n    audit.log(type.getMethod(\"paymentId\").invoke(event))                                     // 3\n    return event\n}"},
   {"say": "Three needs: (1) the class by name, for every event type the topic can carry; (2) its `(String, String, long)` constructor; (3) its `paymentId()` method. Say the topic carries `PaymentAuthorized` and `PaymentCaptured`. Each gets one entry. The condition limits them to images where the decoder is used.",
    "code": "{\n  \"reflection\": [\n    {\n      \"condition\": { \"typeReached\": \"com.acme.pay.EventDecoder\" },\n      \"type\": \"com.acme.pay.PaymentAuthorized\",\n      \"methods\": [\n        { \"name\": \"<init>\", \"parameterTypes\": [\"java.lang.String\", \"java.lang.String\", \"long\"] },\n        { \"name\": \"paymentId\", \"parameterTypes\": [] }\n      ]\n    },\n    {\n      \"condition\": { \"typeReached\": \"com.acme.pay.EventDecoder\" },\n      \"type\": \"com.acme.pay.PaymentCaptured\",\n      \"methods\": [\n        { \"name\": \"<init>\", \"parameterTypes\": [\"java.lang.String\", \"java.lang.String\", \"long\"] },\n        { \"name\": \"paymentId\", \"parameterTypes\": [] }\n      ]\n    }\n  ]\n}",
    "lang": "json"},
   {"say": "Put the file at `src/main/resources/META-INF/native-image/com.acme/pay-events/reachability-metadata.json`, the `<groupId>/<artifactId>` folder. In a Quarkus app, the annotation does the same job and moves with the class when someone renames it. That is the version to prefer.",
    "code": "@RegisterForReflection\npublic record PaymentAuthorized(String paymentId, String currency, long amountMinor) { }\n\n@RegisterForReflection\npublic record PaymentCaptured(String paymentId, String currency, long amountMinor) { }",
    "lang": "java", "alt_lang": "kotlin",
    "alt_code": "@RegisterForReflection\ndata class PaymentAuthorized(val paymentId: String, val currency: String, val amountMinor: Long)\n\n@RegisterForReflection\ndata class PaymentCaptured(val paymentId: String, val currency: String, val amountMinor: Long)"},
   {"say": "Prove it in CI. Build the native binary and run the integration tests against it with missing registrations turned into a hard exit. A new event type that nobody registered now fails the pipeline, not a refund at 3 a.m.",
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
   "Run the tests once. Eight of ten fail. Two `MetadataFileTest` checks pass already: the empty stub file has a valid shape.",
   "Read `EventDecoder` and `IssuerClients`. Write down every reflective call: which class, which constructor (with its parameter types), which methods, and which proxy interfaces in which order.",
   "Edit `reachability-metadata.json` by hand. Add one reflection entry for `workbench.startup.l03.PaymentAuthorized` with its `<init>` and the three accessors from `EventDecoder.ACCESSORS`, and one entry whose type is `{\"proxy\": [...]}`. Run `MetadataFileTest` until it passes.",
   "Implement `MetadataWriter.reflection` and `MetadataWriter.proxy`, so the same entries can be generated from `Class` objects. Run all ten tests."
  ],
  "hints": [
   "A method entry needs both keys, even with no parameters: `{\"name\": \"currency\", \"parameterTypes\": []}`.",
   "`Class.getName()` gives exactly the names the schema wants: `java.lang.String` for a class, `long` for a primitive.",
   "`m instanceof Constructor<?>` tells a constructor from a method. `Class.isInterface()` and a `HashSet` cover the two proxy rules."
  ],
  "done_when": "All ten tests in `MetadataFileTest` and `MetadataWriterTest` pass."
 },
 "drill": {
  "title": "Two entries from memory",
  "minutes": 4,
  "prompt": "Close this page. Write a `reachability-metadata.json` that registers (1) a JDK proxy over `com.acme.ledger.LedgerClient` and `java.io.Closeable`, in that order, and (2) the `(java.lang.String, long)` constructor of `com.acme.ledger.Refund`, active only when `com.acme.ledger.RefundListener` is reached. Check: how many top-level keys did you use?",
  "answer": {
   "lang": "json",
   "src": "{\n  \"reflection\": [\n    {\n      \"type\": { \"proxy\": [\"com.acme.ledger.LedgerClient\", \"java.io.Closeable\"] }\n    },\n    {\n      \"condition\": { \"typeReached\": \"com.acme.ledger.RefundListener\" },\n      \"type\": \"com.acme.ledger.Refund\",\n      \"methods\": [\n        { \"name\": \"<init>\", \"parameterTypes\": [\"java.lang.String\", \"long\"] }\n      ]\n    }\n  ]\n}"
  }
 },
 "recap": [
  "Native image analyzes from `main` at build time and keeps only reachable code: fast start and small RSS, but no JIT, so lower peak throughput (59% lower in Quarkus's benchmark), and builds that take minutes and gigabytes.",
  "Whatever the analysis can't see (reflection by a run-time name, proxies, resources, JNI, serialization) must be declared in `META-INF/native-image/<groupId>/<artifactId>/reachability-metadata.json`.",
  "Schema v1.2.0 has only `reflection`, `resources`, `foreign` and `comment` at the top. A proxy is a reflection entry with `\"type\": {\"proxy\": [interfaces in order]}`; constructors are `<init>`.",
  "Quarkus initializes all classes at build time by default: static initializers run on the build machine and their values are frozen into the binary. Use `--initialize-at-run-time` for classes that must run at start.",
  "In Quarkus prefer `@RegisterForReflection` (with `targets` for library classes) and `@RegisterForProxy` over hand-written JSON, and test the native binary in CI."
 ],
 "quiz": [
  {"q": "Code calls `Proxy.newProxyInstance(loader, new Class<?>[] {A.class, B.class}, h)` and elsewhere the same with `{B.class, A.class}`. On HotSpot, how many proxy classes exist, and what does that mean for native-image metadata?",
   "options": ["One class, so one proxy entry covers both", "Two classes, so you need two proxy entries, each with its own interface order", "None until the first method call", "Two classes, but metadata only needs the set of interfaces, not the order"],
   "answer": 1,
   "from": "cls-04",
   "why": "A proxy class is defined per ordered list of interfaces, so (A, B) and (B, A) are different classes; the demo prints `$Proxy0` and `$Proxy1`. Native-image metadata describes proxy classes the same way, as an ordered list, so each order needs its own entry."},
  {"q": "Which of these calls needs a reachability metadata entry in a native image?",
   "options": ["`Class.forName(\"com.acme.pay.Fees\")` with a string literal", "`new Fees()`", "`Class.forName(rec.headers().lastHeader(\"type\").value())` in a Kafka deserializer", "A lambda passed to `stream().map(...)`"],
   "answer": 2,
   "why": "The analysis handles reflective calls whose arguments are constants, and it sees `new` and lambdas directly. A class name that arrives in a message header can't be known at build time, so the class and the members used on it must be listed."},
  {"q": "A Quarkus native service has `static final Instant BOOTED = Instant.now();` in a class with default settings, and its health endpoint reports `BOOTED`. What do pods started on different days show?",
   "options": ["Each pod's own start time", "The same time in every pod: when the native binary was built", "The build fails with an image-heap error", "`null`, because static fields are not set in native images"],
   "answer": 1,
   "why": "Quarkus initializes all classes at build time by default, so the initializer runs once inside the build and the `Instant` is stored in the image heap. The builder rejects some objects, such as a `Random`, but a timestamp is an ordinary value. Mark the class with `--initialize-at-run-time` or compute the value when the app starts."},
  {"q": "A colleague's `reachability-metadata.json` has a top-level `\"proxy\": [[\"com.acme.Client\", \"java.io.Closeable\"]]` copied from an old example. With GraalVM's schema v1.2.0, what's the fix?",
   "options": ["Nothing, `proxy` is a valid top-level section", "Rename the file to `proxy-config.json`", "Move it into `reflection` as `{\"type\": {\"proxy\": [\"com.acme.Client\", \"java.io.Closeable\"]}}`", "Replace it with `allPublicMethods: true`"],
   "answer": 2,
   "why": "Schema v1.2.0 allows only `reflection`, `resources`, `foreign` and `comment` at the top level. Proxies are reflection entries whose `type` is an object with a `proxy` list. Legacy files like `proxy-config.json` are not supported in Quarkus 4.0."},
  {"q": "A Kafka consumer runs all day on three pods at high throughput. Pods restart about once a week, and a six-second start-up hurts nobody. Which runtime fits best?",
   "options": ["A native image, for the smallest RSS", "The JVM, optionally with an AOT cache to trim start-up", "A native image with build-time initialization of everything", "CRaC, to restore a warmed snapshot"],
   "answer": 1,
   "why": "This service lives on peak throughput and barely restarts, which is where the JIT wins: Quarkus's benchmark shows native at 59% lower peak. An AOT cache cuts start-up with no code change and costs only about 7% of peak in the same benchmark. Native and CRaC solve start-up problems this service doesn't have."}
 ],
 "flashcards": [
  {"front": "What is native image's closed-world assumption?", "back": "All code is known at build time. The analysis keeps only what it can reach from `main`; anything used only through reflection, proxies or resource names must be declared in metadata."},
  {"front": "Where does `reachability-metadata.json` go?", "back": "In `META-INF/native-image/<groupId>/<artifactId>/` on the class path."},
  {"front": "How do you declare a JDK dynamic proxy in schema v1.2.0?", "back": "A reflection entry: `{\"type\": {\"proxy\": [\"com.acme.Client\", \"java.io.Closeable\"]}}`, interfaces in the order the code uses."},
  {"front": "How is a constructor written in a `methods` entry?", "back": "`{\"name\": \"<init>\", \"parameterTypes\": [\"java.lang.String\", \"long\"]}`: fully qualified class names, primitives by name."},
  {"front": "What does Quarkus do with static initializers in native mode by default?", "back": "It runs them at build time. The values they compute are stored in the image heap and are the same on every start."},
  {"front": "How do you make one class initialize at run time in a Quarkus native build?", "back": "`quarkus.native.additional-build-args=--initialize-at-run-time=com.acme.Foo`, escaping commas between classes as `\\\\,`."},
  {"front": "`@RegisterForReflection(targets = {X.class})` on class `Config`: which class gets registered?", "back": "`X`, not `Config`. That's how you register a library's classes you can't annotate."}
 ],
 "terms": [
  {"term": "Native image", "plain": "A standalone executable built ahead of time from your class path by GraalVM or Mandrel."},
  {"term": "Closed-world assumption", "plain": "The rule that all code a native image will run is known at build time."},
  {"term": "Reachability metadata", "plain": "The list of classes, members, proxies and resources the build must keep because only dynamic code uses them."},
  {"term": "Image heap", "plain": "Objects created at build time, stored in the executable and mapped at start-up."},
  {"term": "Build-time initialization", "plain": "Running a class's static initializer during the build instead of at each start."},
  {"term": "Tracing agent", "plain": "A JVM agent (`-agentlib:native-image-agent`) that records the reflection, proxies and resources a run uses."},
  {"term": "Mandrel", "plain": "A GraalVM-based distribution of native image tailored for Quarkus, without the polyglot parts."}
 ],
 "explain_back": {
  "prompt": "Explain to a teammate why a native image needs metadata for the event class your Kafka deserializer creates by reflection, but not for a class your code creates with `new`, and what Quarkus gives you so you don't write the JSON by hand.",
  "answer": "The native build analyzes the program from `main` and keeps only code it can prove is reachable. A `new PaymentAuthorized(...)` is right there in the bytecode, so the analysis sees the class and its constructor. The deserializer instead calls `Class.forName` with a name from the message header and then `getConstructor` and `getMethod`, so the build can't know which class or which members until the message arrives. Unless the class and those members are listed in reachability metadata, they're left out, and the call fails at run time with a registration error. In Quarkus, the extensions register what their libraries need, and I add `@RegisterForReflection` to my event classes, or use `targets` for classes from a library, and `@RegisterForProxy` for proxies. Quarkus turns those into the metadata file during the build."
 },
 "deeper": {
  "minutes": 10,
  "body": "Some details for when you go native for real.\n\nConditions are precise. `\"condition\": {\"typeReached\": \"com.acme.EventDecoder\"}` makes an entry active when that type is reached at run time, which the docs define as \"right before the class-initialization routine starts for that type\", or when one of its subtypes is reached. Writing `EventDecoder.class` does not reach it. Conditions mostly help library authors ship metadata that costs nothing in apps that never use the feature.\n\nResources use globs: `{\"resources\": [{\"glob\": \"META-INF/**/*.properties\"}, {\"bundle\": \"com.acme.Messages\"}]}`. In Quarkus, use `quarkus.native.resources.includes` instead.\n\nThe heap needs a limit. Without an explicit maximum, a native image sets the maximum Java heap to 80% of the physical memory size, according to the GraalVM memory docs. In a container, pass `-Xmx` (or `-XX:MaximumHeapSizePercent`) yourself. The default collector is Serial. `--gc=G1` needs Oracle GraalVM on Linux, and `--gc=epsilon` never frees memory, which only makes sense for short jobs.\n\nPGO, in Oracle GraalVM only, is a three-step build: `native-image --pgo-instrument ...` builds an instrumented binary, you run it on a real workload so it writes a `.iprof` profile on exit, and `native-image --pgo=app.iprof ...` builds the optimized binary. That is the same idea as Leyden's training run, applied to compiled code.\n\nThe JDK is moving toward some of these benefits without leaving the JVM. Lesson 2's AOT cache already ships linked classes and profiles, and JEP 544, in development for JDK 28, adds compiled code to the cache while keeping the JIT. Native image stays the option when the binary's size and start time, not the JVM's, are the limit."
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
