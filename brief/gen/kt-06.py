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


FIG = (
    '<svg viewBox="0 0 680 270" role="img" aria-label="Three compiler plugins and what each changes in the class file: all-open removes final, no-arg adds a hidden zero-argument constructor, serialization adds a generated serializer class">'
    '<text class="t-s t-m" x="165" y="28" text-anchor="middle">your source</text>'
    '<text class="t-s t-m" x="515" y="28" text-anchor="middle">what the plugin writes into the class file</text>'
    '<rect class="box-a" x="20" y="44" width="290" height="44" rx="8"/>'
    '<text class="t-s t-code" x="165" y="71" text-anchor="middle">@OpenForProxies class FeeService</text>'
    '<line class="ln" x1="314" y1="66" x2="362" y2="66" marker-end="url(#arr)"/>'
    '<rect class="box-ok" x="370" y="44" width="290" height="44" rx="8"/>'
    '<text class="t-s t-code" x="515" y="71" text-anchor="middle">public class FeeService (no final)</text>'
    '<rect class="box-a" x="20" y="108" width="290" height="44" rx="8"/>'
    '<text class="t-s t-code" x="165" y="135" text-anchor="middle">@NoArgEntity class Row(val id: String)</text>'
    '<line class="ln" x1="314" y1="130" x2="362" y2="130" marker-end="url(#arr)"/>'
    '<rect class="box-ok" x="370" y="108" width="290" height="44" rx="8"/>'
    '<text class="t-s t-code" x="515" y="135" text-anchor="middle">+ public Row(), hidden from Kotlin</text>'
    '<rect class="box-a" x="20" y="172" width="290" height="44" rx="8"/>'
    '<text class="t-s t-code" x="165" y="199" text-anchor="middle">@Serializable class Posted(...)</text>'
    '<line class="ln" x1="314" y1="194" x2="362" y2="194" marker-end="url(#arr)"/>'
    '<rect class="box-ok" x="370" y="172" width="290" height="44" rx="8"/>'
    '<text class="t-s t-code" x="515" y="199" text-anchor="middle">+ Posted$$serializer, serializer()</text>'
    '<text class="t-s t-m" x="340" y="252" text-anchor="middle">all three run inside kotlinc; KSP and kapt generate new source files instead</text>'
    '</svg>'
)

L = {
 "id": "kt-06",
 "title": "Compiler plugins: all-open, no-arg and kotlinx.serialization",
 "minutes": 35,
 "goal": "By the end you can say what each of the three plugins changes in the class file, configure all-open correctly for a Quarkus 3 service, avoid the no-arg initializer trap, and serialize a sealed event hierarchy with stable type names.",
 "warmup": {
  "q": "A Quarkus 3 service written in Kotlin has a bean annotated `@jakarta.enterprise.context.ApplicationScoped`, and no compiler plugins. What does `javap` show for the class?",
  "options": ["`public class`: CDI annotations make a class open", "`public final class`: Kotlin classes are final unless something opens them", "It depends on the JDK version", "The class doesn't compile until you add `open`"],
  "answer": 1,
  "why": "Kotlin makes classes and their members final by default, and an annotation is just data: it doesn't change modifiers unless a compiler plugin reads it. That's what all-open is for. Quarkus can sometimes work around final classes at build time, but the class file itself is final. Many people expect the first option because Java classes are open by default."
 },
 "sections": [
  {
   "h": "Kotlin classes are final, and framework proxies need to subclass them",
   "body": "Quarkus, Spring and Hibernate add behavior to your classes with **proxies**: classes they generate that extend yours and override each method, to do something before and after calling `super`. A `@Transactional` method gets an overriding method that opens a transaction, calls yours and commits. Write such a subclass by hand and the problem shows at once:\n\n```java\nclass AuditedSettlementService extends SettlementService {   // error: cannot inherit from final SettlementService\n    @Override public String settle(String batch) { return super.settle(batch); }\n}\n```\n\n```kotlin\nclass TimedSettlementService : SettlementService() {          // error: this type is final, so it cannot be extended.\n    override fun settle(batch: String): String =                // error: 'settle' in 'SettlementService' is final\n        super.settle(batch)                                     //        and cannot be overridden.\n}\n```\n\nKotlin classes and their members are final unless you write `open`. A framework that generates subclasses hits the same wall as your hand-written one, just later. You could write `open` on every bean and every method, and nobody keeps that up.\n\nA **compiler plugin** is a jar that the Kotlin compiler loads to change what it emits. The **all-open** plugin \"makes classes and their members open at compile time without requiring the open keyword\", for every class that carries an annotation you configure (or whose superclass does, or that uses a meta-annotation built on it). This lab module configures it for `workbench.kotlin.OpenForProxies`. `javap` on the demo's `SettlementService` then shows `public class` and `public java.lang.String settle(...)`, with no `final`. What it leaves alone is just as important: private members stay private, backing fields stay `private final`, and an unannotated `PlainHelper` stays `public final class`.\n\n`kotlin-spring` is all-open with a preset for Spring's annotations, such as `@Component` and `@Transactional`. Quarkus users need care. The `quarkus` preset inside the Kotlin 2.4.21 plugin lists only `javax.enterprise.context.ApplicationScoped` and `RequestScoped`, but Quarkus 3 uses the `jakarta` namespace. In a test run, a `jakarta`-annotated bean compiled with that preset stayed `public final class`. Name the annotations yourself, as the Quarkus Kotlin guide does for `jakarta.ws.rs.Path` and `jakarta.enterprise.context.ApplicationScoped`:\n\n```kotlin solo\n// build.gradle.kts of a Quarkus 3 service\nplugins {\n    kotlin(\"plugin.allopen\") version \"2.4.21\"\n}\n\nallOpen {\n    annotation(\"jakarta.ws.rs.Path\")\n    annotation(\"jakarta.enterprise.context.ApplicationScoped\")\n}\n```\n\nQuarkus's CDI container can also transform many final classes at build time (`quarkus.arc.transform-unproxyable-classes` is `true` by default), but its Kotlin guide still configures all-open, and so should you.",
   "figure": {"svg": FIG, "caption": "Each plugin reads an annotation at compile time and changes the class file: modifiers, a new constructor, or a whole new class."},
   "try": {
    "title": "Open a class without writing open",
    "minutes": 4,
    "steps": [
     "Run `AllOpenDemo`, then `AllOpenDemoJava`, which extends the same Kotlin class from Java.",
     "Run `javap -p -cp kotlin/build/classes/kotlin/demo workbench.kotlin.l06.demo.SettlementService` from `labs/`. Which members are still final?",
     "Delete `@OpenForProxies` above `SettlementService`. Predict the errors, run, and put it back."
    ],
    "code": demo("AllOpenDemo"),
    "expect": "The demo prints `SettlementService: open class; getFeeBps:open, secret:private, settle:open`, `PlainHelper: final class; help:final`, a timing line and `settled batch-17 at 125 bps`. `javap` shows `public class SettlementService`, `private final int feeBps` and `private int secret()`: only the field keeps its `final`. Without the marker, the build fails with `this type is final, so it cannot be extended.` and `'settle' in 'SettlementService' is final and cannot be overridden.`, and the Java twin would get `cannot inherit from final SettlementService`."
   },
   "refs": [{"title": "All-open compiler plugin (Kotlin docs)", "url": "https://kotlinlang.org/docs/all-open-plugin.html", "kind": "docs"},
            {"title": "Quarkus guide: using Kotlin (all-open configuration)", "url": "https://github.com/quarkusio/quarkus/blob/main/docs/src/main/asciidoc/kotlin.adoc", "kind": "docs"}]
  },
  {
   "h": "no-arg gives frameworks an empty constructor, and skips your initializers",
   "body": "Hibernate builds an entity the same way every time: call a constructor with no parameters, then set the fields from the row. Its documentation says an entity must \"be a non-`final` class, with a non-`private` constructor with no parameters\". A Kotlin class like `LedgerRow(val id: String, var amountMinor: Long)` has no such constructor. By hand, you'd add one:\n\n```java\n@Entity\npublic class LedgerRow {\n    @Id private String id;\n    private long amountMinor;\n    private String note = \"default-note\";\n\n    protected LedgerRow() { }                       // for Hibernate\n    public LedgerRow(String id, long amountMinor) { this.id = id; this.amountMinor = amountMinor; }\n}\n```\n\n```kotlin\nclass LedgerRow(val id: String, var amountMinor: Long) {\n    var note: String = \"default-note\"\n\n    constructor() : this(\"\", 0)                    // the hand-written version: invented defaults\n}\n```\n\nThe hand-written Kotlin constructor works, but it invents an empty id that any Kotlin caller can now create by mistake. The **no-arg** plugin generates the constructor for classes with an annotation you configure, and the docs say it's \"annotated with @Deprecated at the HIDDEN level, so you can call it from Java but not from Kotlin\". The demo shows both sides: Kotlin's `LedgerRow()` fails with `no value passed for parameter 'id'.`, and Java's `new LedgerRow()` compiles, with only a deprecation note from javac.\n\nNow the trap. The generated constructor doesn't run property initializers. The option that would run them, `invokeInitializers`, is \"disabled by default\". So after `new LedgerRow()`, `note` holds `null`, even though Kotlin declared it a non-null `String`, and the first `note.length` in Kotlin code throws a `NullPointerException`. For a JPA entity that's usually fine, because Hibernate sets every mapped column right afterwards. For anything else, turn `invokeInitializers` on or give the property no initializer.\n\nFor JPA, use `kotlin-jpa` rather than configuring no-arg yourself: it's no-arg with a preset for `@Entity`, `@Embeddable` and `@MappedSuperclass`, in both the `javax.persistence` and `jakarta.persistence` packages. Since Kotlin 2.3.20, the Gradle `org.jetbrains.kotlin.plugin.jpa` plugin also applies all-open with the JPA preset, so that, in the release notes' words, \"lazy associations work as expected instead of causing eager loading\". On older Kotlin versions you had to add all-open for entities yourself.",
   "try": {
    "title": "Build an entity the way an ORM does",
    "minutes": 3,
    "steps": [
     "Run `NoArgDemo`, then `NoArgDemoJava`. Predict `blank.note` before you look.",
     "Uncomment the wrong move in `NoArgDemo.kt`, predict, run, and comment it out again.",
     "In `NoArgDemo.kt`, add `println(blank.note.length)` at the end of `main`. Predict what happens, then run."
    ],
    "code": demo("NoArgDemo"),
    "expect": "Both show `amountMinor = 0` and a `null` note, and the Java twin also prints `getId() = null`: the generated constructor sets nothing and runs no initializer. The Kotlin call `LedgerRow()` fails with `no value passed for parameter 'id'.` and the same for `amountMinor`. The added line compiles, because `note` is declared `String`, and throws `NullPointerException` at run time."
   },
   "refs": [{"title": "No-arg compiler plugin (Kotlin docs)", "url": "https://kotlinlang.org/docs/no-arg-plugin.html", "kind": "docs"},
            {"title": "Kotlin-jpa plugin (Kotlin docs)", "url": "https://kotlinlang.org/docs/kotlin-jpa-plugin.html", "kind": "docs"}]
  },
  {
   "h": "kotlinx.serialization writes the serializer at compile time",
   "body": "Most JSON libraries on the JVM work by reflection: at run time they look at a class, find its constructor and properties, and guess how to fill them. Kotlin classes make that guessing harder, with default arguments and non-null types. kotlinx.serialization doesn't guess. \"When you annotate a class with @Serializable, the Kotlin serialization plugin generates a KSerializer for that class.\" The demo's `Posted` gets a nested class, `Posted$$serializer`, that implements `GeneratedSerializer<Posted>` with real `serialize` and `deserialize` methods, plus `Posted.serializer()` on the companion object. Without the plugin, `Posted.serializer()` is `unresolved reference 'serializer'.`\n\n```java\n// Java's usual approach, with Jackson: annotations read by reflection at run time\n@JsonTypeInfo(use = JsonTypeInfo.Id.NAME, property = \"type\")\n@JsonSubTypes({\n    @JsonSubTypes.Type(value = Posted.class, name = \"posted\"),\n    @JsonSubTypes.Type(value = Reversed.class, name = \"reversed\")\n})\npublic sealed interface LedgerEvent permits Posted, Reversed { String paymentId(); }\n\nString json = new ObjectMapper().writeValueAsString(events);\n```\n\n```kotlin\n@Serializable\nsealed interface LedgerEvent { val paymentId: String }\n\n@Serializable @SerialName(\"posted\")\ndata class Posted(override val paymentId: String, val amountMinor: Long, val currency: String = \"EUR\") : LedgerEvent\n\n@Serializable @SerialName(\"reversed\")\ndata class Reversed(override val paymentId: String, val reason: String? = null) : LedgerEvent\n\nprivate val json = Json { ignoreUnknownKeys = true; explicitNulls = false }\nval text = json.encodeToString(events)      // events: List<LedgerEvent>\n```\n\nA sealed hierarchy is \"closed polymorphism\": the plugin knows every subclass at compile time, so it can write and read a `\"type\"` field, the **class discriminator** that tells a decoder which subclass an object is, with no registration. Three details decide what the JSON looks like. The discriminator is written only when the static type is the base: `List<LedgerEvent>` gets `\"type\":\"posted\"`, and `Json.encodeToString(p)` with `p` typed `Posted` gets none. Its value is the fully qualified class name unless you set `@SerialName`, so without it a package rename changes your wire format. And the default `Json` leaves out properties that equal their default (`encodeDefaults` is off), writes nulls, and rejects unknown keys: `Encountered an unknown key 'acquirer'`.\n\nFor events that cross a Kafka topic, that last default matters most. A consumer with the default `Json` breaks the day a producer adds a field, so set `ignoreUnknownKeys = true`. Build one `Json` instance and reuse it: the docs say instances \"are immutable and thread-safe\", and that reusing them improves performance. The JSON format is Stable; HOCON, ProtoBuf, CBOR and Properties are still Experimental.",
   "try": {
    "title": "Read the JSON a sealed hierarchy produces",
    "minutes": 4,
    "steps": [
     "Run `SerializationDemo`. Before you do, predict which lines will contain `\"type\"`.",
     "Remove `@SerialName(\"posted\")` from `Posted` and run again. What is the type value now?",
     "Run `SerializationDemoJava`, which uses the generated serializer from Java through `Posted.Companion.serializer()`."
    ],
    "code": demo("SerializationDemo"),
    "expect": "The list prints `[{\"type\":\"posted\",\"paymentId\":\"pay_1\",\"amountMinor\":1999},{\"type\":\"reversed\",\"paymentId\":\"pay_1\"}]`: no `currency` (it equals its default) and no `reason` (null, with `explicitNulls = false`). The static-type `Posted` line has no `type`; the `LedgerEvent` line has one. The lenient instance ignores `acquirer`, and the default one fails with `Encountered an unknown key 'acquirer'`. Without `@SerialName` the type becomes `workbench.kotlin.l06.demo.Posted`. The Java twin prints the same JSON and the class name `Posted$$serializer`."
   },
   "refs": [{"title": "Serialize polymorphic classes (Kotlin docs)", "url": "https://kotlinlang.org/docs/serialization-polymorphism.html", "kind": "docs"},
            {"title": "Customize the Json instance (Kotlin docs)", "url": "https://kotlinlang.org/docs/serialization-json-configuration.html", "kind": "docs"}]
  },
  {
   "h": "KSP and kapt generate new source files instead",
   "body": "The three plugins above change the compiler's output from the inside. A second family of tools generates new source files from your annotations, the way Java annotation processors do: dependency injection (Dagger), database access (Room), mappers (MapStruct).\n\n**kapt** runs Java annotation processors on Kotlin code. The docs say it \"generates stub files from Kotlin source code and then runs the Java annotation processors on those stubs\". Those stubs are Java declarations of your Kotlin classes, written only so a Java processor can read them, and the migration guide calls them \"expensive\": they \"significantly increase build time\" and lose Kotlin-specific features. **KSP** is the Kotlin-native alternative, \"a source code generation framework for Kotlin\". Its processors read Kotlin declarations directly, and its README says they \"can run up to 2x faster\" than kapt. The limits are part of the design: KSP processors \"can't examine expressions or statements, and they can't modify the source code\". They only add new files.\n\nTwo version facts matter in 2026. KSP2 \"is no longer a compiler plugin\" and is built on the same compiler APIs as IntelliJ IDEA. And since KSP 2.3.0, KSP1 is deprecated and \"KSP version is no longer tied to the Kotlin compiler version\", so a KSP release number no longer has to match your Kotlin version.\n\nMy rule: use KSP whenever the library ships a KSP processor, and kapt only for processors that exist just for Java. Keep an eye on build time when you add kapt: every kapt module pays for the stub step on each build.\n\nA check to end on, and the answer follows from how the serialization plugin works: a module depends on the `kotlinx-serialization-json` library but doesn't apply `kotlin(\"plugin.serialization\")`. You mark a class `@Serializable` and call `Captured.serializer()`. What happens, and at which stage? (It fails at compile time with `unresolved reference 'serializer'.`: the annotation compiles because it's in the library, but nobody generates the companion function.)"
  }
 ],
 "analogy": "Compiler plugins are the print shop's finishing step. Your manuscript says \"open for proxies\" or \"needs a blank form\" in the margin, and the finisher acts on the note: it trims the `final` off, binds in an extra blank page (the no-arg constructor), or prints a matching order form for each document (the serializer). The reader of the finished book, the JVM, only sees the result. The analogy breaks with the blank page: a real finisher wouldn't hand you a form with required fields left empty, but no-arg does exactly that, which is why the initializer trap exists.",
 "in_your_world": "A Quarkus 3 payment service in Kotlin needs all three. All-open, configured with the `jakarta` annotations by name (`jakarta.ws.rs.Path`, `jakarta.enterprise.context.ApplicationScoped`), so ArC and RESTEasy can subclass your beans and resources; don't trust a preset that knows only `javax`. `kotlin-jpa` for Hibernate entities, which on Kotlin 2.3.20 and later also opens them for lazy-loading proxies. And kotlinx.serialization for the `PaymentEvent` messages on your Kafka topics, with a `@SerialName` on every subtype so a package rename can't break consumers, and `ignoreUnknownKeys = true` so a producer can add a field without taking down every consumer.",
 "mistake": "Relying on a preset that doesn't match your annotations, and finding out from a proxy error at startup or, worse, from interceptors that silently don't run. With Kotlin 2.4.21 the all-open plugin's `quarkus` preset knows only `javax.enterprise.context.ApplicationScoped` and `RequestScoped`, while Quarkus 3 code uses `jakarta.enterprise.context.ApplicationScoped`:\n\n```java\n// in Java the question doesn't exist: classes are open unless you write final\n@ApplicationScoped\npublic class FeeService { public long feeMinor(long amountMinor) { return amountMinor * 125 / 10_000; } }\n```\n\n```kotlin\n@ApplicationScoped              // jakarta.enterprise.context: not in the 2.4.21 quarkus preset\nclass FeeService {              // javap: public final class FeeService\n    fun feeMinor(amountMinor: Long): Long = amountMinor * 125 / 10_000\n}\n```\n\nThe fix is to list the annotations you use, with their full `jakarta` names, in `allOpen { annotation(...) }`, and to check one bean with `javap` after any build change.",
 "compare": {
  "title": "A proxy-ready service and entity: Java as written vs Kotlin with plugins",
  "java": {"title": "Beans.java", "src": "@ApplicationScoped\npublic class FeeService {                         // open by default in Java\n    public long feeMinor(long amountMinor) { return amountMinor * 125 / 10_000; }\n}\n\n@Entity\npublic class PaymentEntity {                      // open by default\n    @Id private String id;\n    private long amountMinor;\n    private String note = \"default-note\";        // runs in every constructor\n\n    protected PaymentEntity() { }                 // the no-arg constructor, written by hand\n    public PaymentEntity(String id, long amountMinor) { this.id = id; this.amountMinor = amountMinor; }\n}"},
  "kotlin": {"title": "Beans.kt", "src": "@ApplicationScoped                                 // all-open configured for this annotation\nclass FeeService {\n    fun feeMinor(amountMinor: Long): Long = amountMinor * 125 / 10_000\n}\n\n@Entity                                            // kotlin-jpa: no-arg + all-open for entities\nclass PaymentEntity(@Id val id: String, var amountMinor: Long) {\n    var note: String = \"default-note\"             // skipped by the generated no-arg constructor\n}"},
  "note": "Java gets proxy-ready classes for free: classes and methods are open unless marked `final`, and you write the no-arg constructor yourself, where field initializers run as usual. Kotlin's defaults point the other way, so the plugins put back what frameworks need, at compile time, driven by annotations. The class files end up close to the Java ones, with one difference that bites: Kotlin's generated no-arg constructor skips property initializers unless you enable `invokeInitializers`, so `note` is `null` on a fresh instance, while Java's hand-written constructor runs `note = \"default-note\"`."
 },
 "worked": {
  "title": "Version a Kafka event without breaking consumers",
  "steps": [
   {"say": "Version 1 of a payment event goes onto a topic. The consumer uses the default `Json`. Here are both sides, with the Java consumer using Jackson.",
    "code": "// Java consumer with Jackson: by default it also fails on unknown properties\nObjectMapper mapper = new ObjectMapper();\nCaptured c = mapper.readValue(record.value(), Captured.class);", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "@Serializable @SerialName(\"captured\")\ndata class Captured(override val paymentId: String, val amountMinor: Long) : PaymentEvent\n\nval event = Json.decodeFromString<PaymentEvent>(record.value())   // the default Json: strict"},
   {"say": "The producer team adds `acquirer` and deploys first. Every consumer with the default settings now fails on every message, because unknown keys \"result in an error\" by default.",
    "code": "// producer v2 writes {\"type\":\"captured\",\"paymentId\":\"pay_7\",\"amountMinor\":1999,\"acquirer\":\"acq-a\"}\nJson.decodeFromString<PaymentEvent>(v2)\n// SerializationException: ... Encountered an unknown key 'acquirer' at path: $", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "mapper.readValue(v2, Captured.class);\n// Jackson: UnrecognizedPropertyException, unless FAIL_ON_UNKNOWN_PROPERTIES is turned off"},
   {"say": "Configure the consumer once, in one shared instance: tolerate new keys, keep `@SerialName` stable, and add new fields with defaults so old messages still decode.",
    "code": "// 1. one instance, reused: immutable and thread-safe\nval events = Json { ignoreUnknownKeys = true; explicitNulls = false }\n\n// 2. a new field gets a default, so v1 messages without it still decode\n@Serializable @SerialName(\"captured\")\ndata class Captured(override val paymentId: String, val amountMinor: Long, val acquirer: String? = null) : PaymentEvent", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "ObjectMapper mapper = new ObjectMapper()\n        .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);"},
   {"say": "Check the other direction. A v1 consumer that doesn't know a new subtype, say `\"type\":\"chargeback\"`, still fails, and it should: `ignoreUnknownKeys` covers fields, not types. Deploy consumers before producers when you add a subtype.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "A serializable event hierarchy and proxy-ready classes",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/PaymentEvents.kt", f"{lab}/main/{P}/Beans.kt", f"{lab}/main/kotlin/workbench/kotlin/Annotations.kt"],
  "run": "./gradlew :kotlin:test --tests 'workbench.kotlin.l06.*'",
  "steps": [
   "Read `Annotations.kt` and the two plugin lines in `labs/kotlin/build.gradle.kts`. The annotations do nothing by themselves; the plugins look for their names.",
   "Run the tests. All seven fail.",
   "In `PaymentEvents.kt`, add `@Serializable` and `@SerialName` (TODO 1), create the shared `Json` (TODO 2), and write `encodeEvents` and `decodeEvents` (TODOs 3 and 4).",
   "In `Beans.kt`, mark `FeeService` with `@OpenForProxies` (TODO 5), and `PaymentEntity` with `@NoArgEntity` and `@OpenForProxies` (TODO 6).",
   "Run until all seven pass, including `EventsFromJavaTest`. Then run `javap -p -cp kotlin/build/classes/kotlin/main workbench.kotlin.l06.PaymentEntity` and find the constructor nobody wrote."
  ],
  "hints": [
   "`encodeToString` and `decodeFromString` are extension functions with reified types: `json.encodeToString(events)` and `json.decodeFromString<List<PaymentEvent>>(text)`, or let the return type infer it.",
   "The `\"type\"` field appears because the static type is `List<PaymentEvent>`, the sealed base. You don't configure it.",
   "`Json { ignoreUnknownKeys = true; explicitNulls = false }` covers both rules. Leave `encodeDefaults` alone: off is the default, and the test expects `currency` to be left out.",
   "The marker annotations live in package `workbench.kotlin`: import `workbench.kotlin.OpenForProxies` and `workbench.kotlin.NoArgEntity`."
  ],
  "done_when": "All seven tests in `PluginsTest` and `EventsFromJavaTest` pass."
 },
 "drill": {
  "title": "Write a serializable refund hierarchy from memory",
  "minutes": 4,
  "prompt": "Close this page. Write a sealed `RefundEvent` with two subtypes, `RefundRequested(refundId, amountMinor)` and `RefundSettled(refundId, settledAtEpochMs)`, serialized with the stable type names `refund_requested` and `refund_settled`, and a shared `Json` that tolerates new fields. Then write the Java version with Jackson annotations. Where does each version find the subtypes?",
  "answer": {"lang": "kotlin", "src": "@Serializable\nsealed interface RefundEvent { val refundId: String }\n\n@Serializable @SerialName(\"refund_requested\")\ndata class RefundRequested(override val refundId: String, val amountMinor: Long) : RefundEvent\n\n@Serializable @SerialName(\"refund_settled\")\ndata class RefundSettled(override val refundId: String, val settledAtEpochMs: Long) : RefundEvent\n\n// the plugin finds the subtypes at compile time, from the sealed hierarchy\nval refundJson = Json { ignoreUnknownKeys = true }",
             "alt": {"lang": "java", "title": "RefundEvent.java", "src": "// Jackson finds the subtypes at run time, from these annotations\n@JsonTypeInfo(use = JsonTypeInfo.Id.NAME, property = \"type\")\n@JsonSubTypes({\n    @JsonSubTypes.Type(value = RefundRequested.class, name = \"refund_requested\"),\n    @JsonSubTypes.Type(value = RefundSettled.class, name = \"refund_settled\")\n})\npublic sealed interface RefundEvent permits RefundRequested, RefundSettled { String refundId(); }\n\nrecord RefundRequested(String refundId, long amountMinor) implements RefundEvent {}\nrecord RefundSettled(String refundId, long settledAtEpochMs) implements RefundEvent {}\n\nObjectMapper mapper = new ObjectMapper()\n        .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);"}}
 },
 "recap": [
  "A compiler plugin changes what kotlinc emits, driven by annotations you configure. The annotations do nothing on their own.",
  "all-open removes `final` from annotated classes and their members (not private members, not fields), so proxies can subclass them. kotlin-spring and kotlin-jpa are presets.",
  "In Kotlin 2.4.21 the built-in `quarkus` preset knows only `javax` annotations: list the `jakarta` ones yourself.",
  "no-arg adds a zero-argument constructor, hidden from Kotlin, callable from Java and reflection. It skips property initializers unless `invokeInitializers` is on.",
  "kotlinx.serialization generates a `$$serializer` class at compile time. A sealed base gets a `\"type\"` discriminator: pin it with `@SerialName`, reuse one `Json`, and set `ignoreUnknownKeys` for evolving events.",
  "KSP and kapt generate new source files. Prefer KSP; kapt runs Java processors on generated stubs and costs build time."
 ],
 "quiz": [
  {"q": "A Quarkus 3 bean is annotated `@jakarta.enterprise.context.ApplicationScoped`, and the build relies on the all-open plugin's built-in `quarkus` preset (Kotlin 2.4.21). What does `javap` show for the class?",
   "options": ["`public class`, with open methods", "`public final class`: the preset lists only the `javax` annotations", "A compile error: the preset rejects `jakarta` annotations", "`public class`, but every method is still `final`"],
   "answer": 1, "why": "The preset in the 2.4.21 plugin names `javax.enterprise.context.ApplicationScoped` and `RequestScoped` only. A `jakarta`-annotated class matches nothing, so the plugin leaves it alone. Configure `annotation(\"jakarta.enterprise.context.ApplicationScoped\")` explicitly."},
  {"q": "An entity built with the default no-arg plugin settings has `var status: String = \"NEW\"`. What does `status` hold right after Hibernate calls the generated constructor, before it sets any column?",
   "options": ["`\"NEW\"`", "`\"\"`", "`null`, even though the type is `String`", "Nothing: the constructor throws because `status` isn't set"],
   "answer": 2, "why": "The generated constructor doesn't run property initializers unless `invokeInitializers` is enabled, and it is off by default. Hibernate normally overwrites the field from the row; any other code that reads it first sees `null` in a non-null property."},
  {"q": "`Captured` is a `@Serializable @SerialName(\"captured\")` subclass of a sealed `PaymentEvent`, and `c` is typed `Captured`. What does `Json.encodeToString(c)` produce?",
   "options": ["`{\"paymentId\":\"p\",\"amountMinor\":1}`: no discriminator, because the static type isn't the base", "`{\"type\":\"captured\",\"paymentId\":\"p\",\"amountMinor\":1}`", "The fully qualified class name in a `\"type\"` field", "A `SerializationException`: sealed subtypes must be encoded as the base"],
   "answer": 0, "why": "The docs say the type discriminator is included only when you use the base class as the static type. Encode `c` as a `PaymentEvent` (or inside a `List<PaymentEvent>`) to get `\"type\":\"captured\"`. The fully qualified name appears only when there is no `@SerialName`."},
  {"q": "Your service needs generated mappers from an annotation processor that exists only for Java. Which tool runs it on Kotlin classes?",
   "options": ["KSP", "all-open", "kotlinx.serialization", "kapt"],
   "answer": 3, "why": "kapt generates Java stubs from your Kotlin sources and runs Java annotation processors on them. KSP runs KSP processors, which a Java-only processor isn't. all-open and kotlinx.serialization change the compiler's output and don't run processors at all."},
  {"q": "From the patterns track: a framework proxy wraps `FeeService`, and inside `FeeService`, `charge()` calls `this.audit()`, where `audit` has an interceptor. With a Spring-style proxy that forwards to a separate target object, does the interceptor run for that inner call?",
   "options": ["Yes, because all-open made `audit` open", "No: `this` is the target, so the call never goes through the proxy", "Only if `audit` is private", "Only when the class is written in Java"],
   "answer": 1, "why": "all-open makes the proxy possible; it doesn't route calls through it. A forwarding proxy calls the target, and inside the target `this.audit()` is a plain call on the target. That's the self-invocation trap from the Decorator and Proxy lesson, and it's the same in Java and Kotlin.",
   "from": "pat-05"}
 ],
 "flashcards": [
  {"front": "Why does a Kotlin bean need all-open (or `open`) for CDI or Spring proxies?", "back": "Kotlin classes and members are final by default, and those proxies are generated subclasses that override your methods."},
  {"front": "What does all-open leave unchanged?", "back": "Private members, backing fields (still `final`), and every class without a configured annotation."},
  {"front": "Quarkus 3 and the built-in `quarkus` all-open preset in Kotlin 2.4.21: what goes wrong?", "back": "The preset lists only `javax.enterprise.context` annotations, so `jakarta`-annotated beans stay final. Name the `jakarta` annotations in `allOpen { }`."},
  {"front": "What does no-arg generate, and who can call it?", "back": "A zero-argument constructor marked `@Deprecated(level = HIDDEN)`: Java and reflection can call it, Kotlin code can't."},
  {"front": "Does no-arg's constructor run property initializers?", "back": "Not by default (`invokeInitializers` is off), so a non-null property can hold `null` on a fresh instance."},
  {"front": "When does kotlinx.serialization write the `\"type\"` discriminator?", "back": "Only when the static type is the polymorphic base, such as `List<PaymentEvent>`. Its value is the `@SerialName`, or else the fully qualified class name."},
  {"front": "KSP vs kapt in one line each?", "back": "kapt runs Java annotation processors on generated Java stubs (slow builds). KSP processors read Kotlin symbols directly, up to 2x faster, and can only add files."}
 ],
 "terms": [
  {"term": "Compiler plugin", "plain": "A jar the Kotlin compiler loads to change what it emits, usually driven by annotations."},
  {"term": "Proxy", "plain": "A class a framework generates that extends yours and overrides methods to add behavior such as transactions."},
  {"term": "all-open", "plain": "Compiler plugin that makes annotated classes and their members open, without writing `open`."},
  {"term": "no-arg", "plain": "Compiler plugin that adds a zero-argument constructor, hidden from Kotlin, for frameworks that need one."},
  {"term": "kotlin-jpa", "plain": "no-arg with a preset for JPA annotations; since Kotlin 2.3.20 its Gradle plugin also applies all-open for them."},
  {"term": "Class discriminator", "plain": "The `\"type\"` field that tells a decoder which subclass a JSON object is."},
  {"term": "KSP", "plain": "Kotlin Symbol Processing: a framework for processors that read Kotlin declarations and generate new source files."},
  {"term": "kapt", "plain": "Runs Java annotation processors on Kotlin code by first generating Java stubs of the Kotlin classes."}
 ],
 "explain_back": {
  "prompt": "A teammate's Quarkus 3 service has a Kotlin bean annotated `@ApplicationScoped` whose interceptor never fires, and the build uses the all-open `quarkus` preset. Explain what's going on in the class file and what you'd change.",
  "answer": "Kotlin compiles classes and their methods as final unless something opens them. Interceptors in CDI work through generated subclasses that override the bean's methods, and a final class or method can't be overridden. The all-open plugin is supposed to remove `final` from classes with certain annotations, but it only does that for the annotations it's told about. The built-in `quarkus` preset in the Kotlin 2.4.21 plugin lists only the old `javax.enterprise.context` annotations, and Quarkus 3 uses `jakarta.enterprise.context.ApplicationScoped`, so the preset doesn't match and the bean stays `public final class`. I'd configure all-open with the exact annotations the service uses, such as `annotation(\"jakarta.enterprise.context.ApplicationScoped\")` and `annotation(\"jakarta.ws.rs.Path\")`, rebuild, and check one bean with `javap` to see that `final` is gone from the class and its public methods."
 },
 "deeper": {
  "minutes": 8,
  "body": "The presets inside the 2.4.21 all-open plugin, read from the plugin's own classes, say more than the docs page. `spring` lists `@Component`, `@Transactional`, `@Async`, `@Cacheable`, `@SpringBootTest` and also `org.springframework.validation.annotation.Validated`, which the docs page leaves out. `micronaut` lists four AOP annotations, `jpa` lists `Entity`, `Embeddable` and `MappedSuperclass` in both namespaces, and `quarkus` lists only the two `javax` scopes. When a framework moves packages, presets lag behind, and listing annotations by name is the only setting you control.\n\nOn the command line the same plugins take `-P` options, which helps when you test a hypothesis with plain `kotlinc`: `-Xplugin=<allopen jar> -P plugin:org.jetbrains.kotlin.allopen:annotation=com.example.OpenForProxies`, and for no-arg `-P plugin:org.jetbrains.kotlin.noarg:invokeInitializers=true`. Maven users add `<plugin>all-open</plugin>` to the Kotlin Maven plugin with the `kotlin-maven-allopen` dependency. Since Kotlin 2.3.20, `kotlin-maven-noarg` also includes `kotlin-maven-allopen`.\n\nkotlinx.serialization has more for event streams. Open polymorphism, where subclasses live in other modules, needs a `SerializersModule` that registers each one. `classDiscriminator` renames the `\"type\"` field if your schema already uses that name. `coerceInputValues` turns invalid values, such as an unknown enum constant, into the property's default instead of failing. And `@JsonIgnoreUnknownKeys` (Experimental) relaxes unknown keys for one class instead of the whole `Json` instance.\n\nFinally, the generated code is plain JVM bytecode, so it's fast and free of run-time reflection, which also makes it a good fit for GraalVM native images. The startup track covers why reflection is the hard part there."
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
