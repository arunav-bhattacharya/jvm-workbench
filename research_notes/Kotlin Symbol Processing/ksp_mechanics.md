# How KSP works, end to end (KSP 2.3.14, Kotlin 2.4.21)

Scope: what Kotlin Symbol Processing is, where it runs in a Gradle build, the processor API with exact 2.3.14 signatures, the symbol model, rounds and deferral, incremental processing, options, Java sources, several processors in one build, kapt vs KSP, and the exact text KSP prints. At the end: misconceptions, the moving-house picture mapping, and notes for lesson writers.

Versions: Kotlin Gradle plugin 2.4.21, KSP `com.google.devtools.ksp` 2.3.14 (Maven Central, published 2026-11-13), Gradle 9.8.2, OpenJDK 21.0.12. KotlinPoet 2.4.0 and kctfork 0.14.0 exist on Maven Central (checked), but they are not covered here.

**Summary.** KSP is a separate Gradle task (`kspKotlin`, `kspTestKotlin`, `kspKotlinJvm`, ...) that runs **before** `compileKotlin`. It reads your Kotlin and Java sources as a tree of declarations (classes, properties, function signatures, annotations, types), hands that tree to your processors, and adds the files they write (`build/generated/ksp/main/kotlin/...`) to the compilation that follows. It cannot see expressions or statements and it cannot change existing code. Since 2.3.0 there is only KSP2. KSP2 is not a compiler plugin, runs inside the Gradle daemon, and has its own version numbers (2.3.14 works with KGP 2.3.20 to 2.4.x). Processing runs in rounds: a round happens only if the previous round generated at least one file. Each round, `getSymbolsWithAnnotation` returns only symbols from new files plus deferred symbols. Incremental processing reruns processors only on "dirty" files, and the processor's `Dependencies` decide which files are dirty. Wrong `Dependencies` make the build silently produce wrong output. I reproduced both failure modes (a missing entry and a deleted file).

Several things I measured on 2.3.14 contradict the current kotlinlang docs or older tutorials:
1. Symbols that are still deferred when processing ends produce **no error and no warning** (the docs say an error is logged).
2. `onError()` is **not** called when a processor throws (the docs and the KDoc say it is).
3. `KSVisitorVoid()` and `KSNode.validate()`, exactly as the official quickstart writes them, have been **deprecated since 2.3.12** and compile with warnings. 2.3.14 adds the new `SymbolProcessor.apiFeatures` property.
4. `logger.exception(e)` prints `e: [ksp] ...` but does **not** fail the build.
5. `compilerVersion` reports **2.4.20** (the compiler bundled inside KSP), not 2.4.21.
6. A lambda `CommandLineArgumentProvider` is not tracked as a task input, so changing its value leaves `kspKotlin` UP-TO-DATE.

**How claims were checked.**
- **[Local]**: I ran it in a probe build in this session. The layout: `annotations` + `processor` (two providers: `ProbeProcessor` and `Observer`) + `app` (Kotlin and Java sources) + `kmp` (jvm + js), with Gradle 9.8.2, KGP 2.4.21 and KSP 2.3.14. Paths below write the probe root as `<probe>`. The probe lived in the session scratchpad and is not in the repo.
- **[Source]**: I read the 2.3.14 sources jars from Maven Central: `https://repo1.maven.org/maven2/com/google/devtools/ksp/<artifact>/2.3.14/<artifact>-2.3.14-sources.jar` for `symbol-processing-api`, `symbol-processing-gradle-plugin`, `symbol-processing-common-deps` and `symbol-processing-aa` (the KSP2 engine). The same files live on GitHub under `google/ksp/api/...`, `gradle-plugin/...`, `common-deps/...`, `kotlin-analysis-api/...`. Older API jars (2.3.11, 2.3.12, 2.3.13) and Gradle plugin jars (2.3.0, 2.3.3, 2.3.6, 2.3.9, 2.3.11) were diffed to date the changes.
- **[Docs]**: kotlinlang pages fetched today, both rendered and as raw markdown from `JetBrains/kotlin-web-site` master.
- **[Release notes]**: GitHub release pages read through a fetch tool. They are paraphrased unless in quotes.
- **[Unverified]**: claims I could not confirm.

**Doc map (changed recently).** The kotlinlang KSP section now has: overview, quickstart, `ksp-kotlin-model`, `ksp-kapt-migration`, `ksp-reference`, `ksp-incremental`, `ksp-multi-round`, `ksp-multiplatform`, `ksp-command-line`. The old `ksp-why-ksp.html`, `ksp-faq.html` and `ksp-examples.html` now redirect to `ksp-overview.html`, `ksp-additional-details.html` redirects to `ksp-kotlin-model.html`, and `ksp2.html` returns 404. The KSP2 introduction now exists only in the GitHub repo, as `docs/ksp2.md`. The overview's requirements table still says "The latest KSP version, 2.3.12" (it lags behind 2.3.14). The google/ksp README still links the dead FAQ and why-ksp URLs.

---

## 0. Version facts and recent changes

| Fact | Evidence |
|---|---|
| KSP 2.3.0 (Maven 2025-10-21) dropped the `<kotlin>-<ksp>` version format. The old line continued in parallel for a while (`2.2.21-2.0.5`, Maven 2026-02-02). | Maven `Last-Modified` headers. 2.3.0 notes: "KSP version is no longer tied to the Kotlin compiler version (moving away from the old - format)." (the fetch tool stripped the `<...>` placeholder), "It is independent of Kotlin now", "We wanted to match the Kotlin language version". https://github.com/google/ksp/releases/tag/2.3.0 |
| 2.3.0 notes: "KSP1 has been deprecated" and "KSP is no longer a compiler plugin (like KSP1)." In practice KSP1 is **gone** from 2.3.x: `ksp.useKSP2=false` is a configuration error. | [Local] The error reads "KSP1 is no longer available. Please use KSP2 instead and do not explicitly set ksp.useKsp2 to false via the DSL or the Gradle property. The ksp.useKSP2 property will be removed in the future." The same code is in the 2.3.0 to 2.3.14 Gradle plugins [Source]. README: "KSP 1.x has been removed and is no longer supported." https://github.com/google/ksp/blob/main/README.md |
| Supported range per docs: KGP 2.3.20 to 2.4.x, AGP 8.13.0+, Gradle 8.13+ ("For AGP 9.0 or later, use Gradle 9.x"), JDK 17+. | https://kotlinlang.org/docs/ksp-overview.html (table headed "The latest KSP version, 2.3.12") |
| 2.3.12 (2026-09-09): opt-in backing fields (`KSBackingField`, `KSVisitorNext`, `registerProcessorForNewFeatures`). **Deprecates `KSVisitorVoid()` and `KSNode.validate()` without a feature flag.** | [Release notes] https://github.com/google/ksp/releases/tag/2.3.12. [Source] diff of the 2.3.11 and 2.3.12 API jars: 2.3.11 has no `@Deprecated` on either. |
| 2.3.13 (2026-10-30): context parameters API (`KSContextParameter`). Opt-in `ksp.classloader.cache.processors`. "Returns last-round dismissible errors when KSP fails" (see §10). Its own notes say it "has a regression described in issue 3286". | [Release notes] https://github.com/google/ksp/releases/tag/2.3.13 |
| 2.3.14 (2026-11-13): **new `SymbolProcessor.apiFeatures` + `buildApiFeatures {}`**. `registerProcessorForNewFeatures` is now deprecated. Fixes #3286. Skips the session and processor execution in incremental builds when nothing is dirty (#3256). `KSAnnotation.arguments` vararg fix (#3271), `defaultArguments` alignment (#3233). | [Release notes] https://github.com/google/ksp/releases/tag/2.3.14. [Source] the 2.3.13 to 2.3.14 diff adds `ApiFeatures.kt`, `ApiFeaturesBuilder.kt` and `KSApiFeatures.kt`. |

---

## 1. What KSP is, and where it runs in a Gradle build

**Definition.** "Kotlin Symbol Processing (KSP) is a source code generation framework for Kotlin. With the KSP API, you can create processors that inspect static information about your source code and generate new code from it. The most common use case is generating code based on annotations." Also: "KSP-based processors can't examine expressions or statements, and they can't modify the source code." And: "KSP models declarations and type information, but doesn't give processors access to expressions or function bodies." https://kotlinlang.org/docs/ksp-overview.html

The overview's three steps: "KSP processors analyze source code and resources." / "The processors generate source files or other outputs." / "The Kotlin compiler compiles the original source code together with the generated code." (same URL)

**KSP2 is not a compiler plugin.** "KSP2 is a new implementation of the KSP API. Unlike KSP 1.x, it is no longer a compiler plugin and is built on the same set of Kotlin compiler APIs shared with IntelliJ IDEA, Android Lint, etc." And: "Unlike KSP1, which runs in KotlinCompileDaemon, KSP2 runs in Gradle daemon." The page advises raising the heap, for example "`org.gradle.jvmargs=-Xmx4096M -XX:MaxMetaspaceSize=1024m`", and debugging with `-Dorg.gradle.debug=true`. https://github.com/google/ksp/blob/main/docs/ksp2.md. [Source] The Gradle task submits a `KspAAWorkerAction` with `workerExecutor.noIsolation()`, so it runs in the daemon JVM. `--debug` output shows KSP lines as `[QUIET] [system.out]` [Local].

**Plugin id and the dependency configuration.**
```kotlin
plugins {
    kotlin("jvm") version "2.4.21"
    id("com.google.devtools.ksp") version "2.3.14"
}
dependencies {
    implementation(project(":annotations"))
    ksp(project(":processor"))        // main source set
    kspTest(project(":processor"))    // test source set
}
```
- Processor module: `implementation("com.google.devtools.ksp:symbol-processing-api:2.3.14")`. The provider is registered in `src/main/resources/META-INF/services/com.google.devtools.ksp.processing.SymbolProcessorProvider` with one fully qualified class name per line. https://kotlinlang.org/docs/ksp-quickstart.html. (The quickstart hard-codes `symbol-processing-api:2.3.6`. Use 2.3.14.)
- "The `ksp(...)` configuration applies the processor only to application sources. To process test sources, add the processor with the `kspTest(...)` configuration." (quickstart)
- **KMP:** use `add("kspJvm", ...)`, `add("kspJs", ...)`, `add("kspCommonMainMetadata", ...)`, `add("kspJvmTest", ...)`, and so on. Plain `ksp(...)` in a multiplatform module is a **build error**. [Local] "The 'ksp' configuration is deprecated in Kotlin Multiplatform projects. Please use target-specific configurations like 'kspJvm' instead." With `-Pksp.allow.all.target.configuration=true` the same text is only a warning and `ksp` applies to every compilation [Local]. The docs say: "Since KSP 2.3.12, the catch-all `ksp(...)` configuration causes a build error in multiplatform projects. Earlier versions report it as deprecated." https://kotlinlang.org/docs/ksp-multiplatform.html. But the 2.3.0 Gradle-plugin source already has the same `throw InvalidUserCodeException(msg)` [Source]. I did not run 2.3.0 to 2.3.11 [Unverified behaviour].

**Task names.** [Source] `KspSubplugin.applyToCompilation`: `val kspTaskName = kotlinCompileProvider.name.replaceFirst("compile", "ksp")`.

| Compile task | KSP task | Verified |
|---|---|---|
| `compileKotlin` | `kspKotlin` | [Local] |
| `compileTestKotlin` | `kspTestKotlin` | [Local] |
| KMP `compileKotlinJvm` / `compileTestKotlinJvm` | `kspKotlinJvm` / `kspTestKotlinJvm` | [Local] |
| KMP `compileKotlinJs` / `compileTestKotlinJs` | `kspKotlinJs` / `kspTestKotlinJs` | [Local] |
| KMP `compileCommonMainKotlinMetadata` | `kspCommonMainKotlinMetadata` | [Local] |
| KMP native, for example `compileKotlinLinuxX64` | `kspKotlinLinuxX64` | [Source], not run (no Native toolchain) |

A KSP task is registered for **every** compilation, even one with no processor. It then deletes its output directories and does nothing [Source: `if (kspConfig.processorClasspath.isEmpty) {...deleteRecursively(); return}`]. [Local] `kspTestKotlin` existed before any `kspTest` dependency. `kspTestKotlinJvm` "ran" with no processors. The KMP doc says otherwise: "The remaining compilations don't have corresponding KSP tasks because KSP isn't configured for them." It is wrong about task existence, though true that no processing happens. When there are no source files, the task is skipped (`@SkipWhenEmpty` on `sourceRoots`) [Source].

**Where generated sources land.** [Source] `getKspOutputDir = buildDirectory.dir("generated/ksp/$target/$sourceSetName")`, with subfolders `kotlin/`, `java/`, `classes/`, `resources/`. Caches go to `build/kspCaches/$target/$sourceSetName`. On single-platform JVM the target name is empty, so:
- `app/build/generated/ksp/main/kotlin/probe/app/PersonCard.kt` and `app/build/generated/ksp/test/kotlin/...` [Local]
- KMP: `build/generated/ksp/jvm/jvmMain/kotlin`, `build/generated/ksp/js/jsMain/kotlin`, `build/generated/ksp/metadata/commonMain/kotlin`. Caches: `build/kspCaches/jvm/jvmMain`, and so on [Local].
- The file extension picks the folder: `"kt"` goes to `kotlin/`, `"java"` to `java/`, `"class"` to `classes/`, and anything else to `resources/` [Source: `CodeGeneratorImpl.extensionToDirectory`]. [Local] `createNewFile(..., "META-INF", "packing-list", "txt")` landed in `generated/ksp/main/resources/META-INF/packing-list.txt`. A `.java` file landed in `generated/ksp/main/java/...`. Both ended up in `app.jar` (`probe/gen/JavaLabel.class`, `META-INF/packing-list.txt`).

**How the output joins compilation.** [Source] `KspSubplugin`:
- The `kotlin/` and `java/` output dirs are added as source dirs of the compilation's default source set (`builtBy(kspTask)`), so `compileKotlin` depends on `kspKotlin`.
- `classes/` is added to the Kotlin compile `libraries` and to the compilation outputs.
- Generated `.java` files are added to `compileJava`.
- `resources/` is added to `processResources`.
- In KMP common (metadata) compilations, generated sources go only into the metadata compile task. The source comment says "Do not add generated sources to common source sets."

[Local] Task order in the log: `:app:kspKotlin` → `:app:compileKotlin` → `:app:compileJava`. The IDE flags references to generated code until the first build: "Your IDE highlights `helloWorld()` as an undefined reference. This is expected" (quickstart).

**Gradle properties that exist in 2.3.14** (complete list of `gradleProperty(...)` reads in the plugin [Source]). Defaults are from the source and match the README table https://github.com/google/ksp/blob/main/README.md:

| Property | Default | Notes |
|---|---|---|
| `ksp.incremental` | `true` | `false` deletes the caches dir and reprocesses everything. |
| `ksp.incremental.log` | `false` | Writes logs to `build/kspCaches/<...>/logs/` (§5). |
| `ksp.incremental.log.graph.origin` | unset | Fully qualified symbol name. Writes `kspLookupGraphOrigin.dot` [Local]. |
| `ksp.allow.all.target.configuration` | `false` | Allows `ksp(...)` in KMP (warning instead of error). |
| `ksp.project.isolation.enabled` | `false` | Also forced on by Gradle isolated projects. |
| `ksp.experimental.psi.resolution` | `false` | README: "Enabling this may improve build times, but expect crashes." |
| `ksp.experimental.metadata.own.sources.only` | `false` | KMP metadata compilations process only their own source sets. |
| `ksp.ksp2.profiling.mode` | `false` | For KSP developers. |
| `ksp.classloader.cache.processors` | `false` | Shares processor classloaders across modules. Static state lives longer. |
| `ksp.useKSP2` | `true` | Only accepted value is true. Setting `false` fails configuration [Local]. |
| `kotlin.native.enableKlibsCrossCompilation` | `true` | Owned by KGP, read by KSP. |

KSP1-era properties such as `ksp.incremental.intermodule` are not read anywhere in the 2.3.14 plugin [Source: grep]. The `ksp {}` extension also has `allWarningsAsErrors` (default false), `excludeProcessor(fqn)`, `excludedSources`, `arg(...)`, and deprecated no-ops `blockOtherCompilerPlugins` and `allowSourcesFromOtherPlugins` [Source: `KspExtension.kt`]. Command line: "You can also use the `-Dksp.logging` JVM system property to set the logging level. Valid values are `error`, `warn` (or `warning`), `info`, and `debug`." https://kotlinlang.org/docs/ksp-command-line.html. The command-line entry points are `com.google.devtools.ksp.cmdline.KSPJvmMain` / `KSPJsMain` / `KSPNativeMain` / `KSPCommonMain` (same page).

---

## 2. The API, with exact 2.3.14 signatures [Source: symbol-processing-api-2.3.14]

```kotlin
// com.google.devtools.ksp.processing
fun interface SymbolProcessorProvider {
    fun create(environment: SymbolProcessorEnvironment): SymbolProcessor
}

class SymbolProcessorEnvironment(          // a final class, not an interface
    val options: Map<String, String>,      // "passed from command line, Gradle, etc."
    val kotlinVersion: KotlinVersion,      // "language version of compilation environment."
    val codeGenerator: CodeGenerator,
    val logger: KSPLogger,
    val apiVersion: KotlinVersion,
    val compilerVersion: KotlinVersion,
    val platforms: List<PlatformInfo>,     // "There can be multiple platforms in a metadata compilation."
    val kspVersion: KotlinVersion,
    @Deprecated(...) val registerProcessorForNewFeatures: (SymbolProcessor) -> Unit,  // deprecated in 2.3.14
)  // + secondary constructors kept for binary compatibility

interface SymbolProcessor {
    fun process(resolver: Resolver): List<KSAnnotated>
    fun finish() {}
    fun onError() {}
    val apiFeatures: ApiFeatures get() = KSApiFeatures.DEFAULT   // NEW in 2.3.14 (both flags false)
}
```
`process` KDoc: "@return A list of deferred symbols that the processor can't process. Only symbols that can't be processed at this round should be returned. Symbols in compiled code (libraries) are always valid and are ignored if returned in the deferral list."

**What the environment actually contains** [Local, KGP 2.4.21, `jvmToolchain(21)`]:
`options={probe.mode=normal, probe.fixed=42, probe.cmd=fromProvider} kotlinVersion=2.4.0 apiVersion=2.4.0 compilerVersion=2.4.20 kspVersion=2.0.0 platforms=[JVM(jvmTarget=21, jvmDefault=enable)]`.
- `kotlinVersion`/`apiVersion` are the language and API versions (KGP major.minor by default), not the plugin version.
- `compilerVersion` is the Kotlin compiler **bundled inside KSP** (`KotlinCompilerVersion.getVersion()` in `KotlinSymbolProcessing.kt` [Source]), so it is 2.4.20, not 2.4.21.
- `kspVersion` is hard-coded `KotlinVersion(2, 0)` [Source], so it does not say 2.3.14.
- In `kspCommonMainKotlinMetadata`, `platforms=[JVM(jvmTarget=1.8, jvmDefault=disable), JS, wasm-js (JS), wasm-wasi (WASI), Native]`. In `kspKotlinJs`, `[JS]` [Local].
- `PlatformInfo` subtypes: `JvmPlatformInfo` (`jvmTarget`, `jvmDefaultMode`), `JsPlatformInfo`, `NativePlatformInfo` (`targetName`), `UnknownPlatformInfo`.

**API features (new in 2.3.14).** `interface ApiFeatures { val enableBackingFields: Boolean; val enableContextParameters: Boolean }` (both default `false`), `data class KSApiFeatures(...)` with `DEFAULT`, and `fun buildApiFeatures(builderAction: MutableApiFeatures.() -> Unit): ApiFeatures`. Processors that don't override `apiFeatures` get three `i:` messages at `--info`, for example "Processor 'probe.processor.Observer' has not opted in for upcoming features yet. It might break in a future version of KSP." [Local]. The source of the opt-in warning is `computeFeatureOptInWarnings` in `KotlinSymbolProcessing.kt`.

**Resolver** (members; all `fun` unless noted):
```kotlin
fun getNewFiles(): Sequence<KSFile>
fun getAllFiles(): Sequence<KSFile>
fun getSymbolsWithAnnotation(annotationName: String, inDepth: Boolean = false): Sequence<KSAnnotated>
fun getClassDeclarationByName(name: KSName): KSClassDeclaration?
fun getFunctionDeclarationsByName(name: KSName, includeTopLevel: Boolean = false): Sequence<KSFunctionDeclaration>
fun getPropertyDeclarationByName(name: KSName, includeTopLevel: Boolean = false): KSPropertyDeclaration?
fun getTypeArgument(typeRef: KSTypeReference, variance: Variance): KSTypeArgument
fun getKSNameFromString(name: String): KSName
fun createKSTypeReferenceFromKSType(type: KSType): KSTypeReference
val builtIns: KSBuiltIns   // anyType, nothingType, unitType, numberType, byteType, shortType, intType,
                           // longType, floatType, doubleType, charType, booleanType, stringType,
                           // iterableType, annotationType, arrayType
fun overrides(overrider: KSDeclaration, overridee: KSDeclaration): Boolean          // + overload with containingClass
@KspExperimental fun mapToJvmSignature(declaration: KSDeclaration): String?
@KspExperimental fun getJvmName(declaration: KSFunctionDeclaration): String?        // + KSPropertyAccessor overload
@KspExperimental fun getOwnerJvmClassName(...): String?
@KspExperimental fun getJvmCheckedException(...): Sequence<KSType>
@KspExperimental fun getDeclarationsFromPackage(packageName: String): Sequence<KSDeclaration>
@KspExperimental fun mapJavaNameToKotlin(javaName: KSName): KSName?                 // + mapKotlinNameToJava
@KspExperimental fun getDeclarationsInSourceOrder(container: KSDeclarationContainer): Sequence<KSDeclaration>
@KspExperimental fun effectiveJavaModifiers(declaration: KSDeclaration): Set<Modifier>
@KspExperimental fun getJavaWildcard(reference: KSTypeReference): KSTypeReference
@KspExperimental fun isJavaRawType(type: KSType): Boolean
@KspExperimental fun getPackageAnnotations(packageName: String): Sequence<KSAnnotation>
@KspExperimental fun getPackagesWithAnnotation(annotationName: String): Sequence<String>
@KspExperimental fun getModuleName(): KSName
```
Top-level extensions in `com.google.devtools.ksp` (utils.kt): `Resolver.getClassDeclarationByName(name: String)`, `inline fun <reified T> Resolver.getClassDeclarationByName()`, and String overloads of the function/property lookups.

KDoc quotes:
- `getAllFiles`: "all input files including generated files from previous rounds. Note that when incremental processing is enabled, only dirty files up for processing will be returned."
- `getNewFiles`: "new files generated from the last round of processing in the module." [Local] In **round 1**, `getNewFiles()` returns the source files (all of them on a clean build, only dirty ones on an incremental build). It is not empty.
- `getSymbolsWithAnnotation`: "Note that in multi-round processing, only deferred symbols from the last round and symbols from newly generated files will be returned by this function." `inDepth`: "whether to check symbols in depth, i.e., check symbols from local declarations. This operation can be expensive if true." [Local] A `@Card class LocalBox` declared inside a function appeared only with `inDepth = true`. The name is a fully qualified annotation name. A typealias to the annotation is expanded [Source: `ResolverAAImpl.getSymbolsWithAnnotation`].
- `getClassDeclarationByName`: "This returns the exact platform class when given a platform name. Note that java.lang.String isn't compatible with kotlin.String in the type system." [Local] `"java.lang.String"` → `java.lang.String` origin `JAVA_LIB`. `getClassDeclarationByName<String>()` → `kotlin.String` origin `KOTLIN_LIB`. A missing name → `null`.

**CodeGenerator.**
```kotlin
fun createNewFile(dependencies: Dependencies, packageName: String, fileName: String,
                  extensionName: String = "kt"): OutputStream
fun createNewFileByPath(dependencies: Dependencies, path: String, extensionName: String = "kt"): OutputStream
fun associate(sources: List<KSFile>, packageName: String, fileName: String, extensionName: String = "kt")
fun associateByPath(sources: List<KSFile>, path: String, extensionName: String = "kt")
fun associateWithClasses(classes: List<KSClassDeclaration>, packageName: String, fileName: String, extensionName: String = "kt")
fun associateWithFunctions(...) = Unit;  fun associateWithProperties(...) = Unit   // default no-ops in the interface
val generatedFile: Collection<File>
```
- Class KDoc: "Files created by [CodeGenerator] are considered in incremental processing. Kotlin and Java files will be compiled together with other source files in the module. Files created without using this API will not participate in incremental processing nor subsequent compilations."
- `extensionName`: "If "kt" or "java", this file will participate in subsequent compilation. Otherwise its creation is only considered in incremental processing."
- `packageName` "corresponds to the relative path of the generated file; using either '.'or '/' as separator."
- **Creating the same file twice** throws `kotlin.io.FileAlreadyExistsException(file)` [Source: `if (path in fileMap) throw FileAlreadyExistsException(file)`]. The map lives for the whole run, so a second `createNewFile` in a later round also throws. [Local] It prints `e: [ksp] kotlin.io.FileAlreadyExistsException: <probe>/app/build/generated/ksp/main/kotlin/probe/gen/Extra.kt` and the build fails with that path as the cause. A path that escapes the base dir throws `IllegalStateException("requested path is outside the bounds of the required directory")` [Source].
- `generatedFile` lists only the files created **in the current round** (the streams are cleared by `closeFiles()` at the end of each round) [Source + Local].

**Dependencies.**
```kotlin
class Dependencies private constructor(val isAllSources: Boolean, val aggregating: Boolean, val originatingFiles: List<KSFile>) {
    constructor(aggregating: Boolean, vararg sources: KSFile)
    companion object { val ALL_FILES: Dependencies }   // = Dependencies(true, true, emptyList())
}
```
- `aggregating`: "whether the output should be invalidated by a new source file or a change in any of the existing files. Namely, whenever there is new information."
- `ALL_FILES` KDoc (it misnames itself `ALL_SOURCES`): "Associating an output to [ALL_SOURCES] essentially disables incremental processing, as the tiniest change will clobber all files. This should not be used in processors which care about processing speed."
- Implementation [Source: `CodeGeneratorImpl.createNewFile`]: isolating → the given files. Aggregating → the given files + a virtual `<AnyChanges is a virtual file; DO NOT USE.>` key. `ALL_FILES` → all sources + that key.
- Which files to list: "Sources of corresponding [KSNode]s which are obtained directly from [Resolver] need to be specified. Namely, the containing files of those [KSNode]s who are obtained from: Resolver.getAllFiles, Resolver.getSymbolsWithAnnotation, Resolver.getClassDeclarationByName". Files reached through other nodes need not be listed: "KSP traces dependencies automatically" (CodeGenerator KDoc).

**KSPLogger.**
```kotlin
interface KSPLogger {
    fun logging(message: String, symbol: KSNode? = null)
    fun info(message: String, symbol: KSNode? = null)
    fun warn(message: String, symbol: KSNode? = null)
    fun error(message: String, symbol: KSNode? = null)
    fun exception(e: Throwable)
}
```
**Exactly when the build fails** [Source: `KotlinSymbolProcessing.execute()` wraps the logger; Local for each case]:
- `error(...)` sets `hasError`. The current round finishes (later processors in the same round still run). No new round starts. `onError()` is called on every processor and `finish()` is not. KSP returns `PROCESSING_ERROR`. Gradle fails with `KSP failed with exit code: PROCESSING_ERROR` [Local].
- `warn(...)` sets `hasError` only when `ksp { allWarningsAsErrors = true }`. [Local] A warning logged in the processor's constructor with that flag on meant **zero rounds** ran: `onError() after 0 rounds`, build failed.
- `exception(e)` only **prints** `e: [ksp] <e.toString()>`. It does **not** set `hasError`. The build succeeds and `finish()` runs [Local].
- A **thrown** exception escapes `execute()`. Processing stops at once, later processors don't run, and **`onError()` is not called** [Local]. Gradle prints `e: [ksp] java.lang.IllegalStateException: boom...` and fails with the exception message as the cause.
- An `error` logged in `finish()` [Source] still sets `hasError`, so the build fails. `onError()` is not called (that branch was already passed). [Unverified by run]
- No provider on the processor classpath: `e: [ksp] No providers found in processor classpath.` and the build fails [Local].

---

## 3. The symbol model

**Hierarchy** [Source]. `KSNode { origin; location; parent; accept(visitor, data) }`.
- `KSAnnotated : KSNode` (`annotations: Sequence<KSAnnotation>`)
- `KSDeclarationContainer : KSNode` (`declarations`)
- `KSFile : KSDeclarationContainer, KSAnnotated` (`packageName`, `fileName`, `filePath`)
- `KSDeclaration : KSModifierListOwner, KSAnnotated, KSExpectActual` (`simpleName`, `qualifiedName?`, `typeParameters`, `packageName`, `parentDeclaration?`, `containingFile?`, `docString?`)
- `KSClassDeclaration`, `KSFunctionDeclaration`, `KSPropertyDeclaration`, `KSTypeAlias`, `KSTypeParameter` and `KSBackingField` are all `KSDeclaration`s.
- `KSValueParameter`, `KSTypeReference`, `KSTypeArgument` and `KSValueArgument` are `KSAnnotated`. `KSAnnotation` is a plain `KSNode`.
- `KSType` is **not** a `KSNode`. It is a resolved type value.

The reference page maps Java's annotation-processing API: `TypeElement` → `KSClassDeclaration`, `ExecutableElement` → `KSFunctionDeclaration`, `VariableElement` → `KSValueParameter` / `KSPropertyDeclaration`, `PackageElement` → `KSFile` ("KSP doesn't model packages as program elements"). https://kotlinlang.org/docs/ksp-reference.html

**KSClassDeclaration**: `classKind: ClassKind` (`INTERFACE, CLASS, ENUM_CLASS, ENUM_ENTRY, OBJECT, ANNOTATION_CLASS`), `primaryConstructor: KSFunctionDeclaration?`, `superTypes: Sequence<KSTypeReference>`, `isCompanionObject`, `getSealedSubclasses()`, `getAllFunctions()`, `getAllProperties()`, `asType(typeArguments)`, `asStarProjectedType()`. `getDeclaredProperties()`, `getDeclaredFunctions()` and `getConstructors()` are **extensions** in utils.kt that filter `declarations`. They are cheap and cover the class's own members only.

[Local] Probe output (lightly trimmed):
```
describe probe.app.Person kind=CLASS origin=KOTLIN modifiers=[DATA]
  primaryConstructor=name: String hasDefault=false isVal=true, nickname: String? hasDefault=true isVal=true, tags: List<String?> hasDefault=true isVal=true
  superTypes(refs)=Named resolved=Named
  prop nickname: ref='String?' resolved='String?' isMarkedNullable=true nullability=NULLABLE decl=kotlin.String notNull='String'
  prop tags: ref='List<String?>' args=[INVARIANT:String?] decl=kotlin.collections.List star='List<*>'
  prop display: ... hasBackingField=false        (custom getter)
  prop visits: ... isMutable=true hasBackingField=true
  fun greet(greeting: String hasDefault=true): String kind=MEMBER declarationsInside=[local]
  fun component1(): String ... origin=SYNTHETIC      (also component2, component3, copy; no equals/hashCode/toString)
  fun <init>(name: String hasDefault=false, ...): Person kind=MEMBER modifiers=[FINAL] origin=KOTLIN
  annotation shortName=Card type=probe.Card arguments=[label=people(origin=KOTLIN), fragile=false(origin=SYNTHETIC)] defaultArguments=[label=, fragile=false]
describe probe.app.Employee ... declaredProperties=[role, display] allProperties=[role, display, id]   (id inherited from Base)
describe probe.app.Shape kind=INTERFACE modifiers=[SEALED] superTypes=Any ... sealedSubclasses=[Circle, Dot]
```
The things to teach from this output:
- **`getAllProperties` includes inherited properties; `getDeclaredProperties` does not.**
- `hasDefault` tells you a default exists, **never what it is**.
- Constructors are functions named `<init>` (`isConstructor()` checks the name). The KSP2 doc says "Constructors do not have FQN" https://github.com/google/ksp/blob/main/docs/ksp2api.md.
- Data-class `componentN`/`copy` are present with `Origin.SYNTHETIC` (ksp2api.md: "KSP2: `componentN` and `copy` are always present").
- Annotation `arguments` include unspecified parameters with their default values, marked `origin=SYNTHETIC`. `KSValueArgument.isDefault()` is literally `origin == Origin.SYNTHETIC` [Source].
- Annotation argument values can be "Boolean; Byte; Char; Short; Int; Long; Float; Double; String; KSType for annotation arguments of type kotlin.reflect.KClass; KSClassDeclaration for annotation arguments of type Enum ...; KSAnnotation for embedded annotation arguments; Array or Collection of a possible type listed above" (`KSValueArgument.value` KDoc).

**KSFunctionDeclaration**: `functionKind` (`TOP_LEVEL, MEMBER, STATIC, ANONYMOUS, LAMBDA`), `isAbstract`, `extensionReceiver?`, `returnType: KSTypeReference?` ("Can be null if an error occurred during resolution"), `parameters: List<KSValueParameter>`, `contextParameters` (2.3.13+), `findOverridee()`, `asMemberOf(containing: KSType): KSFunction`.

**KSValueParameter**: `name: KSName?`, `type: KSTypeReference`, `isVararg`, `isNoInline`, `isCrossInline`, `isVal`, `isVar`, `hasDefault` ("True if it has a default value").

**KSPropertyDeclaration**: "A property declaration, can also be used to denote a variable declaration." It has `getter?`, `setter?`, `extensionReceiver?`, `type: KSTypeReference`, `isMutable`, `hasBackingField`, `backingField?` (opt-in), `isDelegated()`, `findOverridee()`, `asMemberOf(containing)`.

**KSTypeReference vs KSType.** `KSTypeReference` is the type **as written**: "A [KSTypeReference] combines a [KSReferenceElement] with annotations and modifiers." It has `element: KSReferenceElement?` and `fun resolve(): KSType`, whose KDoc says "Calling [resolve] is expensive and should be avoided if possible." `KSType` members: `declaration`, `nullability` (`NULLABLE, NOT_NULL, PLATFORM`), `arguments`, `annotations`, `isAssignableFrom(that)`, `isMutabilityFlexible()`, `isCovarianceFlexible()`, `replace(arguments)`, `starProjection()`, `makeNullable()`, `makeNotNullable()`, `isMarkedNullable` ("True if the type is explicitly marked as nullable type, i.e. has question mark in type declaration."), `isError` ("the type can't be resolved by compiler"), `isFunctionType`, `isSuspendFunctionType`.

[Local] These are the results:
- `Any.isAssignableFrom(String)=true`
- `String.isAssignableFrom(Any)=false`
- `String?.isAssignableFrom(String)=true`
- `String.isAssignableFrom(String?)=false`
- `Iterable<*>.isAssignableFrom(List<*>)=true`
- `List.asStarProjectedType()` prints `List<*>`
- `String.starProjection()` is `String`

The docs on cost: "This additional analysis makes type resolution one of the most expensive operations in the KSP API." And: "To avoid unnecessary resolutions, KSP generally doesn't resolve type references implicitly." "When possible, inspect the `KSReferenceElement` before resolving the type. For example, use `KSClassifierReference.referencedName()` to filter references that aren't relevant to your processor." "If a processor generates code that references the same types as the source code, it doesn't need to resolve those types." https://kotlinlang.org/docs/ksp-kotlin-model.html. That page's demo prints `birthday: writtenName=SqlDate, arguments=0` without resolving and `birthday: declaration=java.sql.Date, nullability=NULLABLE` with resolving.

**Calls documented as expensive** [Source KDoc]: `KSTypeReference.resolve()`; `getAllFunctions()`, `getAllProperties()` and `getSealedSubclasses()` ("requires type resolution which is expensive"); `getAllSuperTypes()`; `findOverridee()`; `Resolver.overrides(...)`; `getSymbolsWithAnnotation(inDepth = true)`; `get*ByName(includeTopLevel = true)`; `getDeclarationsInSourceOrder` ("Note that this is SLOW. AVOID IF POSSIBLE."). `getSealedSubclasses` also has an **incremental** cost: files that call it are always dirty (§5).

**KSAnnotation**: `annotationType: KSTypeReference`, `arguments: List<KSValueArgument>`, `defaultArguments: List<KSValueArgument>`, `shortName: KSName` ("equivalent to the simple name of the declaration of the annotation class", so it is ambiguous; resolve `annotationType` to check the real annotation), `useSiteTarget: AnnotationUseSiteTarget?`. Experimental helpers: `KSAnnotated.getAnnotationsByType(KClass)` and `isAnnotationPresent(KClass)` (`@KspExperimental`, they build reflection proxies).

**Modifier**: `PUBLIC, PRIVATE, INTERNAL, PROTECTED, IN, OUT, OVERRIDE, LATEINIT, ENUM, SEALED, ANNOTATION, DATA, INNER, FUN, VALUE, SUSPEND, TAILREC, OPERATOR, INFIX, INLINE, EXTERNAL, ABSTRACT, FINAL, OPEN, CONST, VARARG, NOINLINE, CROSSINLINE, REIFIED, EXPECT, ACTUAL, JAVA_DEFAULT, JAVA_NATIVE, JAVA_STATIC, JAVA_STRICT, JAVA_SYNCHRONIZED, JAVA_TRANSIENT, JAVA_VOLATILE`. KDoc (typo included): "Modifiers you can get from a declaration are explict modifiers as they are declared in source code. ... you should rely on helper functions like isOpen() for modifier related logic." [Local] Kotlin `data class Person` → `[DATA]` only, with no PUBLIC/FINAL because they are implicit. A Java `public class` → `[PUBLIC]`. Synthetic `component1` → `[PUBLIC, FINAL, OPERATOR, OVERRIDE]`. Use `getVisibility()`, `isPublic()`, `isOpen()` and `isAbstract()` from utils.

**Origin**: `KOTLIN, KOTLIN_LIB, JAVA, JAVA_LIB, SYNTHETIC` (exactly these five) [Source]. [Local] Source Kotlin → `KOTLIN`, source Java → `JAVA`, `kotlin.collections.List` → `KOTLIN_LIB`, `java.lang.Thread` → `JAVA_LIB`, data-class `copy` → `SYNTHETIC`.

**Location**: `sealed class Location`, `data class FileLocation(val filePath: String, val lineNumber: Int)`, `object NonExistLocation` [Source]. There is no column. [Local] `Person`'s location is `FileLocation(filePath=<probe>/app/src/main/kotlin/probe/app/Model.kt, lineNumber=10)`, the line of `data class Person(`, **not** line 8 where `@Card` is. Library classes give `NonExistLocation`, which prints as `com.google.devtools.ksp.symbol.NonExistLocation@762ff63b` because it is not a data object, and their `containingFile` is `null` ("can be null if symbol does not come from a source file, i.e. from a class file").

**Visitors** [Source]:
- `interface KSVisitor<D, R>`, plus `interface KSVisitorNext<D, R> : KSVisitor<D, R>`, which adds `visitBackingField` and `visitContextParameter`.
- `open class KSVisitorVoid(val apiFeatures: ApiFeatures) : KSVisitorNext<Unit, Unit>`. **Every method is an empty body, so it never descends into children by itself.**
- `abstract class KSEmptyVisitor<D, R>(apiFeatures)`: everything falls back to `abstract fun defaultHandler(node, data): R`.
- `abstract class KSDefaultVisitor<D, R>(apiFeatures) : KSEmptyVisitor`: "A visitor that delegates to super types for methods that are not overridden". For example, `visitClassDeclaration` calls `visitDeclaration` and `visitDeclarationContainer`.
- `KSTopDownVisitor` walks children (supertypes, type parameters, declarations).
- `KSValidateVisitor` is the engine behind `validate()`.
- 2.3.14 deprecates the no-arg and `Boolean` constructors of all of these. [Local] The compiler warning for `class OldStyleVisitor : KSVisitorVoid()` reads: `w: file:///…/OldStyle.kt:8:25 'constructor(): KSVisitorVoid' is deprecated. KSVisitorVoid() is deprecated in favor of KSVisitorVoid(apiFeatures) which supports configuring API features such as backing fields and context parameters.` It continues: "Your SymbolProcessor should override its parent SymbolProcessor.apiFeatures property, share that property across all KSP interactions, ... In an upcoming KSP version, KSVisitorNext will be deprecated and implementations should move back to KSVisitor."
- `inner class CardVisitor : KSVisitorVoid(apiFeatures)` inside the processor compiles and works [Local].

**What KSP cannot see or do.**
- It cannot see expressions, statements or function bodies (docs quoted in §1).
- [Local] It **can** see named declarations inside bodies. `greet()`'s `declarations` contained the local `val local`, and a local class is found with `inDepth = true`. Initializer and default-value expressions are not visible.
- It cannot modify code. "they can't modify the source code" (overview). The API has no mutation method at all [Source]. The only outputs are new files via `CodeGenerator`, plus log messages. To "add" a method to a user class, generate an extension function or a companion type in a new file (the probe generates `fun Person.card()`).

---

## 4. Rounds and deferral

**The loop, as written in 2.3.14** [Source: `symbol-processing-aa` `com/google/devtools/ksp/impl/KotlinSymbolProcessing.kt`, `execute()`]:
1. All providers' `create(environment)` are called **once**, in ServiceLoader order. Docs: "KSP creates a processor instance only once. You can store information in the processor instance and reuse it across multiple rounds." https://kotlinlang.org/docs/ksp-multi-round.html
2. `while (!logger.hasError)`: build a **new** `Resolver`, then call `process(resolver)` on **every** processor in order. Each result is filtered to `origin == KOTLIN || origin == JAVA` (so library symbols are dropped) and stored as that processor's deferred list.
3. `if (logger.hasError || codeGenerator.generatedFile.isEmpty()) break`. **The next round happens only if some processor created at least one file in this round.**
4. The generated `.kt`/`.java` files are parsed. They become the next round's `getNewFiles()` and the source of its `getSymbolsWithAnnotation` results (together with the deferred symbols). Other extensions (txt, class) are not parsed [Local: `packing-list.txt` was not in `newFiles`].
5. After the loop: if `hasError`, run a type check on the last round's new files (§10), then `onError()` on all processors. Otherwise `finish()` on all processors and update the incremental caches.

Docs: "Use only the `Resolver` instance passed to the processor in the current round. Do not store a `Resolver` and reuse it across rounds." and "not all KSP symbols can be reused across rounds" (multi-round page). [Source] Between rounds KSP drops its caches: "Now that caches are dropped, KtSymbols and KS* are invalid. They need to be restored from deferred."

**[Local] Trace of a clean build.** Sources: `Person`, `Employee`, `Shape`, `Box(val content: probe.gen.GeneratedContent)`, Java `JavaCrate`. The processor writes `GeneratedContent.kt` and `Extra.kt` (`@probe.Card class Extra`) in round 1. The `Observer` is a second processor.
```
w: [ksp] round 1: newFiles=[Main.kt, Rooms.kt, Model.kt, Box.kt, JavaCrate.java] allFiles=[...same...]
w: [ksp] round 1: @Card (inDepth=false)=[Person, Employee, Shape, Box, JavaCrate] (inDepth=true)=[LocalBox, Person, Employee, Shape, Box, JavaCrate]
w: [ksp] round 1: valid=[Person, Employee, Shape, JavaCrate] invalid(deferred)=[Box]
w: [ksp] [observer] round 1 newFiles=[Main.kt, Rooms.kt, Model.kt, Box.kt, JavaCrate.java] cards=[Person, Employee, Shape, Box, JavaCrate]
w: [ksp] round 2: newFiles=[GeneratedContent.kt, Extra.kt, PersonCard.kt, EmployeeCard.kt, ShapeCard.kt, JavaCrateCard.kt, MasterList.kt] allFiles=[...12 files...]
w: [ksp] round 2: @Card (inDepth=false)=[Extra, Box] (inDepth=true)=[Extra, Box]
w: [ksp] round 2: valid=[Extra, Box] invalid(deferred)=[]
w: [ksp] [observer] round 2 newFiles=[...] cards=[Extra, Box]
w: [ksp] round 3: newFiles=[ExtraCard.kt, BoxCard.kt] ...
w: [ksp] round 3: @Card (inDepth=false)=[] (inDepth=true)=[]
w: [ksp] finish() after 3 rounds; ...
w: [ksp] [observer] finish() after 3 rounds
```
What this shows:
- (a) `Box` fails `validate()` in round 1 because `GeneratedContent` doesn't exist yet. It is deferred and passes in round 2.
- (b) The generated `Extra` (annotated) is picked up in round 2.
- (c) Round 3 runs only because round 2 wrote `ExtraCard.kt`/`BoxCard.kt`. Round 3 generates nothing, so the loop stops.
- (d) **Deferred symbols are shared**: the `Observer` deferred nothing, yet its round-2 `cards` contained `Box` (deferred by `ProbeProcessor`). [Source] `AAResolutionStrategy` merges `deferredSymbols.values.flatten()` into every annotation lookup.
- (e) A deferred symbol comes back for **every** annotation it carries. A deferred `Person` (which also has `@Listed`) reappeared in the next round's `getSymbolsWithAnnotation("probe.Listed")`. Code that writes a file per lookup result then threw `FileAlreadyExistsException` [Local].

**validate().**
- 2.3.14 signatures [Source]: `fun KSNode.validate(predicate: (KSNode?, KSNode) -> Boolean = { _, _ -> true }, apiFeatures: ApiFeatures): Boolean` is the current one. The deprecated forms are `validate(predicate)` and `validate(predicate, enableNewFeatures: Boolean)`.
- Call it as `symbol.validate(apiFeatures = apiFeatures)`. Plain `it.validate()` resolves to the deprecated overload and warns: `'fun KSNode.validate(predicate: (KSNode?, KSNode) -> Boolean = ...): Boolean' is deprecated. KSNode.validate(predicate) is deprecated in favor of KSNode.validate(predicate, apiFeatures).` [Local].
- What it checks [Source: `KSValidateVisitor`]: it resolves every type reference reachable from the node and returns false if any is `isError`. That covers the class's star-projected type, supertypes, type parameters, annotations and their arguments, member declarations, function return and parameter types, and property types. It walks the class's whole member tree, which is why it is costly.
- Docs: "To defer invalid symbols, filter them with `KSAnnotated.validate()`". Also: "Validation often requires type resolution, which can be expensive. Check only the information required to process the symbol." And: "When implementing custom validation, use `KSType.isError` to determine whether a type is valid." "Defer symbols only when: Additional information is required before the symbol can be processed. The symbol originates from source code." "Don't defer symbols from the classpath. KSP filters them out automatically." (multi-round page)
- Use it when your output needs a type that another processor (or your own earlier round) generates. Don't use it as a general "is this code OK" check; the compiler checks that later.

**What happens to symbols still deferred at the end.**
- Docs: "Multiple-round processing ends when an entire round generates no new files. If deferred symbols remain unprocessed, KSP logs an error for each processor with remaining deferred symbols." (multi-round page).
- **2.3.14 does not do this.** [Local] A processor that returned `Person` from every `process()` call printed `round 3: deferring forever: [Person]`, then `finish() after 3 rounds`, then `BUILD SUCCESSFUL`. There was **no message at any log level**: I grepped the `--info` output for "deferred" and "unable" and found only my own lines. [Source] The 2.3.14 engine has no code that reports leftover deferrals. The only matches for "deferred" in `symbol-processing-aa` are the bookkeeping above. (KSP1 used to log `Unable to process:...` as a warning [Unverified, from memory of KSP1 sources; KSP1 is not shipped in 2.3.x].)
- Lesson rule: if a symbol can never become valid, report `logger.error(..., symbol)` yourself, for example in the round where nothing new appears or in `finish()`.

**finish() and onError() order.** Exactly one of them runs, on all processors, in provider order, after the last round: `onError()` if `hasError`, else `finish()` [Source + Local]. Neither runs after a thrown exception [Local]. Files created in `finish()` **are compiled** (they are in the output dir) but are **never processed**, because no round follows [Local: `MasterList` written in `finish()` compiled and printed]. Docs: "When a processor reports an error, KSP calls `SymbolProcessor.onError()` instead of `SymbolProcessor.finish()`. Processing stops after the current round completes." "Other processors continue processing normally during that round." (multi-round page) Both match [Local]: after `Employee` was reported in round 1, the processor still wrote other cards, the `Observer` still ran round 1, and both got `onError() after 1 rounds`.

---

## 5. Incremental processing

Docs: "KSP supports incremental processing. It reprocesses a file only when one or more of its dependencies change." and "Incremental processing is enabled by default." https://kotlinlang.org/docs/ksp-incremental.html

**Root sources.** "KSP requires processors to declare only a minimal set of _root sources_." A root source is a source file whose symbols are obtained directly from `Resolver.getAllFiles()`, `getSymbolsWithAnnotation()`, `getClassDeclarationByName()` or `getDeclarationsFromPackage()`. "KSP automatically tracks these dependencies" for anything reached from there. "Processors can only move from one file to another by resolving types, so these are the only cross-file dependencies that KSP needs to track." (incremental page)

**Isolating vs aggregating.** "Unlike Gradle annotation processing, KSP applies the categorization to individual outputs rather than entire processors." "Aggregating outputs can be affected by changes in any source file. For example, an output that collects all symbols with a particular annotation." "Any input change, including a file removal, triggers a rebuild of all aggregating outputs and reprocessing of all corresponding registered, new, or modified source files." "Isolating outputs depend only on their specified sources. For example, a class generated to implement a specific interface is isolating." (incremental page)

**How KSP decides what is dirty** [Docs + Source `IncrementalContextBase`]:
- The initial set is the modified files, the removed files, files affected by classpath changes, **files that called `getSealedSubclasses` (always)**, and the outputs under the virtual keys (aggregating, unassociated, and disappeared outputs).
- This set then propagates through **resolution tracing** (a file that resolved a type depends on the files that can change the result) and **shared outputs** (every source of a dirty output becomes dirty), "until no new dirty files appear."
- Then only the dirty files are offered to the processors (`getAllFiles`, `getNewFiles` and `getSymbolsWithAnnotation` in round 1).
- Outputs of clean files are restored from `build/kspCaches/<...>/backups/`. The Gradle task deletes the whole output dir before every run: "Clean stale files for now. TODO: support incremental processing." [Source: `KspAAWorkerAction`]. A backup copy of each output was observed under `kspCaches/main/backups/kotlin/...` [Local].
- 2.3.14: if nothing is dirty, KSP restores outputs and returns **without creating processors** (`tryEarlyExitIfClean`) [Source].
- Gradle itself marks `kspKotlin` UP-TO-DATE when inputs are byte-identical [Local: `touch Main.kt` gave `UP-TO-DATE`].
- The processor classpath is a `@Classpath` input that is not `@Incremental`. So editing the processor or changing `ksp {}` args reruns the task non-incrementally, which in practice means full reprocessing [Source; Unverified that every such change empties the caches].

**[Local] Measured dirty sets** (probe, `ksp.incremental.log=true`). Before getting clean numbers I removed my `getSealedSubclasses` call, because it kept `Model.kt` permanently dirty ("Affected By sealed").
1. Append a comment to `Box.kt`. Dirty = `Rooms.kt`, `Model.kt`, `Box.kt` ("Dirty / All: 60.00%"). `Box.kt` is the modified file. `Rooms.kt` and `Model.kt` are dirty because they feed the aggregating `MasterList`. `JavaCrate.java` and `Main.kt` were not reprocessed: `JavaCrateCard.kt` is isolating and was restored from backup.
2. Add `Attic.kt` with `@Listed class Attic` (aggregating list). Dirty = `Rooms.kt`, `Attic.kt`, `Model.kt` (50%). `MasterList.all` = `[Kitchen, Garage, Attic, Person]`. Correct.

**What wrong Dependencies do (both reproduced) [Local].**
- **Missing entries (aggregating output declared isolating).** `MasterList` was written with `Dependencies(false, *filesOfListedClasses)`. After adding `Attic.kt`, only `Attic.kt` was dirty (16.67%). The processor saw only `Attic`, so the regenerated file was `val all = listOf("probe.app.Attic")` and the program printed `[probe.app.Attic]`. Kitchen, Garage and Person were silently lost, with `BUILD SUCCESSFUL`.
- **Deleted output (no sources declared).** Cards were written with `Dependencies(false)` (no files). After editing `Box.kt`, `JavaCrate.java` was clean, so its card was not regenerated. KSP listed `JavaCrateCard.kt` under `<This is a virtual key for removed outputs; DO NOT USE>` and deleted it. `compileKotlin` then failed: `e: file://<probe>/app/src/main/kotlin/probe/app/Main.kt:12:32 None of the following candidates is applicable:` followed by the remaining `card()` candidates.
- [Source] A comment in `updateCachesAndOutputs` describes the other common misuse: "associating a non-root source, instead of the ones obtained from root functions ... to an output", which KSP partly works around by restoring backups.
- A processor that assumes a symbol is always present in round 1 crashes on incremental runs. Mine did, with `NoSuchElementException` from `first { }`, because `Box.kt` was clean and not offered. After a failed run, the caches are not updated, and the next run is a full rebuild [Local + Source: "Called on errors, where writing half-updated caches ... would corrupt the next incremental run"].

**`Dependencies.ALL_FILES`**: every source plus the "any change" key, so any change makes every file dirty. It is the safe-but-slow choice (KDoc quoted in §2).

**Seeing what was reprocessed.**
- Set `ksp.incremental.log=true` in `gradle.properties`. The docs name `build/kspCaches/<source set>/logs/kspDirtySet.log` and `build/kspCaches/<source set>/logs/kspSourceToOutputs.log`, plus `kspLookupGraphOrigin.dot` with `ksp.incremental.log.graph.origin=<fully-qualified-name>` (incremental page).
- [Local] On JVM the directory is `app/build/kspCaches/main/logs/`. In KMP it is `build/kspCaches/<target>/<sourceSet>/logs/`, for example `jvm/jvmMain`.
- 2.3.14 also writes `kspLookupGraph.log`, `symbolTrackerTrace.log` and `enumClassTrackerTrace.log` (added in 2.3.10: "debugging features for incremental compilation" [Release notes]).
- The files are **overwritten each build**, which is why the docs tell you to copy them between builds.
- `kspDirtySet.log` sections are `All Files`, `Modified`, `Removed`, `Disappeared Outputs`, `Affected By CP`, `Affected By new syms`, `Affected By sealed`, `CP changes`, `Dirty:` and `Dirty / All: NN.NN%`.
- `kspSourceToOutputs.log` sections are "Accumulated source to outputs map", "Reprocessed sources and their outputs" and "All reprocessed outputs". The virtual keys appear in it, for example `<AnyChanges is a virtual file; DO NOT USE.>` mapping to `MasterList.kt`.
- Paths in these logs are relative to the module (`src/main/kotlin/probe/app/Box.kt`, `build/generated/ksp/main/kotlin/...`).

---

## 6. Processor options

- `ksp { arg("key", "value") }` and `arg("key", provider: Provider<String>)`. A key containing `=` throws `GradleException("'=' is not allowed in custom option's name.")` [Source: `KspExtension`].
- `ksp { arg(CommandLineArgumentProvider) }`: each string must match `(\S+)=(\S+)`. [Local] A value with a space fails at execution: `Processor arguments not in the format \S+=\S+: probe.cmd=has space`. So values can't contain whitespace or be empty.
- **Input tracking trap [Local].** A lambda `CommandLineArgumentProvider { listOf("probe.cmd=$v") }` is not seen as a changed input. Changing `v` from `aaa` to `bbb` left `kspKotlin UP-TO-DATE` with the old option. A class provider with `@get:Input val value: String` reruns correctly (`ccc`, `ccc` UP-TO-DATE, then `ddd` reran). Plain `arg(k, v)` values are an `@Input` map (`apOptions`), so changing them reruns the task [Source + Local].
- The processor reads them with `environment.options["key"]` (a `Map<String, String>`). [Local] `options={probe.mode=normal, probe.fixed=42, probe.cmd=fromProvider}`. A missing key gives `null`, so give it a default.
- On the command line the flag is `-processor-options=key1=value1:key2=value2`. Pairs are split on `File.pathSeparatorChar` (`:` on Unix, `;` on Windows) and then on `=` [Source: `kspJvmArgParserHelp.kt` lists `-processor-options=Map<String, String>`; `parseMap` in `KSPConfig.kt`]. The kotlinlang command-line page doesn't list it. I didn't run it.

---

## 7. Java sources

- KSP processes `.java` files in the same source set (Gradle registers `javaSourceRoots`). Their symbols have `Origin.JAVA`.
- [Local] For `@probe.Card public class JavaCrate { private final String label; public int weight; ... public String getLabel() ... }`:
  - `kind=CLASS origin=JAVA modifiers=[PUBLIC]` and `primaryConstructor=null` (Java has no primary constructor; the constructor appears as `<init>` in the declarations).
  - **Fields come back as properties**, including the private field: `declaredProperties=[label, weight]`.
  - `getLabel()` is an ordinary function.
  - `String` comes back as a platform type: `ref='(String..String?)' nullability=PLATFORM isMarkedNullable=false`, and `makeNotNullable()` → `String`.
  - The logger location for a Java node is `JavaCrate.java:4`, the class line.
- `java.lang.String` in Java **sources** is seen as `kotlin.String` (Resolver KDoc: "when processors get a class or type from a Java source file, the conversion is done automatically"). That is not the case for `getClassDeclarationByName("java.lang.String")` [Local, §2].
- Generated `.java` files are compiled by `compileJava` and are processed in the next round like `.kt` files [Local: `JavaLabel.java` in round 2 `newFiles`].
- KSP2 behaviour differences for Java (vararg, array variance, transient/volatile modifiers) are listed in https://github.com/google/ksp/blob/main/docs/ksp2api.md. 2.3.12 notes: "Java fields are now modeled as properties that always have backing fields" (under the opt-in) [Release notes, paraphrase].
- Limits:
  - Nullability of Java types is `PLATFORM` unless annotated. I didn't test `@Nullable` [Unverified].
  - Bodies are invisible, the same as for Kotlin.
  - `getJvmCheckedException` on class files returns empty ("Checked exceptions from class files are not supported yet" [Source]).
  - KSP is not a Java annotation processor: Java-only processors (`javax.annotation.processing`) still need kapt or `annotationProcessor`.

---

## 8. Several processors in one build

- [Source] `KspAAWorkerAction` loads every `SymbolProcessorProvider` on the processor classpath with `ServiceLoader`, minus `excludeProcessor(...)` entries. With `--info` it prints `i: [ksp] loaded provider(s): [probe.processor.ProbeProvider, probe.processor.ObserverProvider]` [Local].
- **Order:** within each round, processors run in that list order. [Local] Swapping the two lines of the services file swapped the order in every round. The docs make **no ordering promise**. Ordering across jars depends on classpath order [Unverified]. Don't rely on it.
- **Visibility:** a processor never sees files that another processor created in the *same* round. They appear in everyone's `getNewFiles()` and annotation lookups in the *next* round [Local: the Observer ran first in round 1 and saw Probe's files only in round 2]. As shown in §4, deferred symbols are pooled across processors.
- An `error` from one processor does not stop the others in that round. A thrown exception does: the processors after it in that round never run [Local].
- One `SymbolProcessorEnvironment` and one `CodeGenerator` are shared by all processors [Source]. Two processors writing the same path collide with `FileAlreadyExistsException`.

---

## 9. kapt vs KSP

- **Official migration guide** (https://kotlinlang.org/docs/ksp-kapt-migration.html): "kapt lets you use Java annotation processors in Kotlin. It translates Kotlin source code into Java "stubs" and then runs the annotation processors on those stubs. However, this process is expensive, significantly increases build time, and loses some Kotlin-specific features in translation." "In contrast, KSP is an alternative to kapt designed specifically for Kotlin. KSP reduces build time by analyzing Kotlin source directly and exposing Kotlin-specific information like nullability." "KSP and kapt can run alongside each other, so you can migrate your project in stages, one library or module at a time." The migration itself is: replace `kapt(...)` with `ksp(...)` and remove `id("org.jetbrains.kotlin.kapt")`. "For most libraries, this replacement is enough."
- **The "2x" claim and its sources.** The current kotlinlang pages no longer give a number.
  - google/ksp README: "Compared to KAPT, annotation processors that use KSP can run up to 2x faster." https://github.com/google/ksp/blob/main/README.md
  - Android Developers, "Migrate from kapt to KSP": "KSP analyzes Kotlin code directly, which is up to 2x faster." and "This stub generation is an expensive operation and has a significant impact on build speed." https://developer.android.com/build/migrate-to-ksp
  - The original measurement is the KSP **alpha** announcement (2021-02, KSP1 era): "initial benchmarks with the Room library show that KSP is approximately 2x faster than KAPT." https://android-developers.googleblog.com/2021/02/announcing-kotlin-symbol-processing-ksp.html
  - Teach it as "up to 2x, from a 2021 Room benchmark", not as a guarantee. No KSP2-era benchmark was found [Unverified].
- **Status of kapt.** Android: "Kapt is now in maintenance mode, and we recommend that you migrate from kapt to KSP for all processors that support it." Also: "If a module has any kapt processors remaining, stubs are still generated in that module." (same Android page). The kotlinlang kapt page (https://kotlinlang.org/docs/kapt.html) no longer says "maintenance mode" in today's version. It describes kapt as generating "stub files from Kotlin source code" and running "the Java annotation processors on those stubs", "for libraries like MapStruct and Data Binding."
- **When kapt is still needed:** any processor that only exists as a Java annotation processor. For example, Data Binding (Android: "KSP support for Data Binding is not planned") and MapStruct (named on the kapt page). The kotlinlang overview's support table still lists "Auto Factory: Not yet supported", "Hilt: In progress" and "Dagger: Alpha" (https://kotlinlang.org/docs/ksp-overview.html). Check each library's own docs, because the table may lag.

---

## 10. Exact error and log formats in Gradle output

**The logger** [Source: `symbol-processing-common-deps` `KspGradleLogger.kt`]. It writes to `System.out` with these prefixes: `v: [ksp] ` (logging), `i: [ksp] ` (info), `w: [ksp] ` (warn), `e: [ksp] ` (error and exception). With a node whose location is a `FileLocation`, the message is `"${filePath}:${lineNumber}: $message"` (absolute path, line, **no column**, no `file://`). Without a node, or with a library node, it is the bare message. `exception(e)` prints `"e: [ksp] $e"` (the `toString()`, with no stack trace).

**Visibility by Gradle log level** [Source: thresholds compared with the Gradle `LogLevel` ordinal; Local]:

| Gradle flag | `logging` | `info` | `warn` | `error` |
|---|---|---|---|---|
| default (lifecycle) | hidden | hidden | shown | shown |
| `--info` | hidden | shown | shown | shown |
| `--debug` | shown | shown | shown | shown |
| `-q` | hidden | hidden | **hidden** | shown |

Verified for default, `--info`, `--debug` and `-q` (warnings disappeared). `error` under `-q` is from source only.

**Verbatim samples [Local]** (the probe root path is replaced with `<probe>`):
```
> Task :app:kspKotlin
w: [ksp] <probe>/app/src/main/kotlin/probe/app/Model.kt:10: describe probe.app.Person kind=CLASS ...
e: [ksp] <probe>/app/src/main/kotlin/probe/app/Model.kt:26: Employee cannot be packed: it has no @Card label
e: [ksp] Main.kt:9: Unresolved reference 'card' on receiver of type 'Person'.
e: [ksp] Main.kt:10: Unresolved reference 'GeneratedContent'.
e: [ksp] Box.kt:4: Unresolved reference 'gen'.
w: [ksp] onError() after 1 rounds
w: [ksp] [observer] onError() after 1 rounds

FAILURE: Build failed with an exception.

* What went wrong:
Execution failed for task ':app:kspKotlin' (registered by plugin 'org.jetbrains.kotlin.jvm').
> A failure occurred while executing com.google.devtools.ksp.gradle.KspAAWorkerAction
   > KSP failed with exit code: PROCESSING_ERROR
```
- The `Unresolved reference` lines are **follow-on diagnostics, not your bug.** When a run fails, KSP type-checks the last round's new files and prints the errors with **file name only** (`runTypeCheck` → `KspDiagnostics` [Source]; this is the 2.3.13 "last-round dismissible errors" change). They show up because the code that refers to generated declarations was checked before those declarations existed.
- Thrown exception: `e: [ksp] java.lang.IllegalStateException: boom from ProbeProcessor in round 1`, then the same FAILURE block with `   > boom from ProbeProcessor in round 1` as the cause.
- Duplicate file: `e: [ksp] kotlin.io.FileAlreadyExistsException: <probe>/app/build/generated/ksp/main/kotlin/probe/gen/Extra.kt`, with the path as the cause.
- No providers: `e: [ksp] No providers found in processor classpath.`, then `A failure occurred while executing com.google.devtools.ksp.gradle.KspAAWorkerAction`.
- **Compiler errors in generated code** look different. They come from `compileKotlin`, with `file://`, a column, and the generated path: `e: file://<probe>/app/build/generated/ksp/main/kotlin/probe/gen/Broken.kt:3:17 Initializer type mismatch: expected 'Int', actual 'String'.` Then `> A failure occurred while executing org.jetbrains.kotlin.compilerRunner.btapi.BuildToolsApiCompilationWork` / `   > Kotlin compiler: INITIALIZER_TYPE_MISMATCH`. KSP itself does not type-check generated code on a successful run.
- Deprecation warnings when **compiling a processor** (`:processor:compileKotlin`) are ordinary Kotlin warnings (`w: file:///…:8:25 'constructor(): KSVisitorVoid' is deprecated. ...`), see §3.
- Info-level lines seen with `--info`: `i: [ksp] loaded provider(s): [...]` and the three "has not opted in" / "registerProcessorForNewFeatures is deprecated" / "has not enabled the following API features: enableBackingFields, enableContextParameters" messages.
- The command-line runner uses `CommandLineKSPLogger`, which prints the bare message to `System.err`, with no prefix and no location [Source]. Output from kctfork-based tests may therefore look different [Unverified].

---

## 11. Misconceptions a newcomer has

1. **"KSP is a compiler plugin running inside kotlinc."** In 2.3.x it is a separate Gradle task (`kspKotlin`) in the Gradle daemon. It runs before `compileKotlin` and hands over files. KSP1 (the compiler plugin) can't be enabled any more.
2. **"My processor can add a method to my class."** It can only create new files. Generate an extension function, a companion type or a separate class. Existing code is read-only.
3. **"KSP reads my code."** It reads **declarations and types**: names, signatures, modifiers, annotations, supertypes and nested or local declarations. It sees no expressions, statements, initializers or default values (only `hasDefault`).
4. **"`process()` returns what I processed."** It returns what you **could not** process yet (deferred). Return `emptyList()` when done.
5. **"`process()` runs once."** It runs once per round, on the same instance, for every processor, for as long as rounds keep generating files. Code that writes a file each time it is called will hit `FileAlreadyExistsException` or duplicate work.
6. **"`getSymbolsWithAnnotation` returns every annotated symbol in the project."** It returns symbols from this round's new files plus the pooled deferred ones. In incremental builds that means **dirty files only**.
7. **"If I keep deferring, KSP will tell me."** In 2.3.14 leftovers are silently dropped and `finish()` runs. Report them yourself.
8. **"`logger.error` stops everything immediately."** The round finishes and other processors still run; then `onError()` runs and the build fails. A **thrown** exception stops at once and skips `onError()`. `logger.exception` doesn't fail the build at all.
9. **"`Dependencies` is optional bookkeeping."** It decides what is regenerated. Wrong values give silently wrong output (a master list missing entries) or deleted outputs, with the build still green until the compiler trips over the missing code.
10. **"KSP's version must match Kotlin's (`2.x.y-1.0.z`)."** Since 2.3.0 the numbers are independent. KSP 2.3.14 supports KGP 2.3.20 to 2.4.x, and `kspVersion`/`compilerVersion` in the environment don't even report 2.3.14/2.4.21.
11. **"Processors see each other's output right away / run in parallel."** They run sequentially in ServiceLoader order and see others' files only in the next round.
12. **"The `Unresolved reference` errors under `[ksp]` mean my generator is broken."** They are follow-on checks printed after a failed processing run. Fix the first `e: [ksp] <path>:<line>:` error.

---

## 12. Picture mapping: MOVING HOUSE

The picture: source files are sealed boxes. The label on top lists the contents (declarations). The packing inside (bodies) stays sealed. An annotation is a sticky note. The processor is a helper with a clipboard (the Resolver) who writes new cards and lists (generated files) that travel with the move, but never opens or relabels boxes. Deferral is setting a box aside. Isolating outputs are per-box cards, and aggregating outputs are the master list.

| Mechanism | Maps onto the picture as | Where the picture breaks |
|---|---|---|
| `KSFile` / declarations | A box and its label: class names, property names with types, function signatures. | The label also lists **named items packed inside**: local classes and variables are visible (`declarations`, `inDepth = true`). Only the *how* (expressions) is sealed. `hasDefault` says "a spare is included" but not what it is. |
| Library classes (`KOTLIN_LIB`/`JAVA_LIB`) | Boxes already unpacked in the new house: you can read their labels. | They have no location (`NonExistLocation`) or file, never come back as "new", and can't be set aside (deferral filters them out). |
| Annotation | Sticky note on a box. | Notes can go on label lines too (properties, functions, parameters), and they carry fields with default values (`arguments`, `SYNTHETIC` defaults). The helper finds notes by **full name** (`probe.Card`), not by the short word written on them (`shortName` is ambiguous). |
| `Resolver` | The clipboard listing boxes with a given note. | You get a **fresh clipboard each pass**. An old one is invalid ("Do not store a Resolver"). In incremental runs it lists only boxes that were repacked or touched. |
| `resolve()` | Looking up what a label word refers to ("contains `GeneratedContent`", so go find that box). | Each lookup is slow, and **each lookup is recorded** (resolution tracing): the helper now depends on that other box for incremental purposes. |
| Generated files | New cards and lists that travel with the move. They get compiled. | The cards are themselves new boxes: next pass, every helper reads their labels and notes (multi-round). A card written in `finish()` travels but nobody reads it. |
| Never opens or relabels | True: no API changes source. | The helper *can* shout about a specific box (`logger.error(msg, node)` points to `File.kt:line`). |
| Rounds | Passes through the house. | A new pass happens **only if someone wrote a new card in the last pass**. "Nothing new" ends the move, even with boxes still set aside. |
| Deferral | Setting a box aside because its label mentions something not packed yet (`isError`). | The set-aside pile is **shared by all helpers**. A set-aside box returns under **every** note it carries. If the van leaves with boxes still set aside, 2.3.14 says nothing. |
| `validate()` | Checking that every word on the label refers to an existing box. | It checks the whole label tree (members too) and is expensive. The docs say check only what you need. |
| Several processors | Several helpers in a fixed order (services-file order) on each pass. | They are not working side by side: helper B never sees helper A's cards from the same pass. |
| Errors | `logger.error`: "stop after this pass". Everyone finishes the pass, then gets `onError()`. | A **thrown** exception is a helper dropping everything: the move stops mid-pass, later helpers don't go, and nobody gets `onError()`. `logger.exception` is only a note in the logbook. The move continues. |
| Incremental, isolating | Repack one box: only its card is redone. | KSP decides what counts as "repacked" from your `Dependencies` **plus every label lookup you made**. A card attached to no box is thrown away the next time its box isn't re-read (reproduced). |
| Incremental, aggregating | The master list is redone and every box on it is re-read. | Only if you *said* it was a master list (`aggregating = true`). Declared as an isolating card, adding a box makes the new list contain **only the new box** (reproduced). Calling `getSealedSubclasses` puts that box on the "always re-read" list. |
| kapt | Photocopying every box into a Java-language replica (stubs) for helpers who only read Java. | The copies lose Kotlin details (nullability and so on). As long as one Java-only helper remains in a room (module), every box in that room still gets photocopied. |
| Java sources | Boxes labeled in another language that the same helper can read (`Origin.JAVA`). | Some words are fuzzy: `(String..String?)` is a platform type with unknown nullability. Private fields show up on the label as properties. |
| KMP | Moving to several houses at once: each house gets its own pass and its own cards (`kspKotlinJvm`, `kspKotlinJs`, `kspCommonMainKotlinMetadata`). | A common box is read once per house: `SharedBox` got a card in each of `metadata/commonMain`, `jvm/jvmMain` and `js/jsMain`. |

---

## 13. Notes for the lesson writer

### The 10 facts most likely to be stated wrongly
1. **Leftover deferrals are silent in 2.3.14.** No error and no warning; `finish()` runs and the build passes [Local]. The kotlinlang multi-round page says an error is logged. Teach "report it yourself."
2. **`onError()` is not called after a thrown exception**, only after `logger.error` (or a warning under `allWarningsAsErrors`) [Local]. The KDoc and docs say "error or exception."
3. **Use the 2.3.14 forms:** `override val apiFeatures = buildApiFeatures { ... }`, `KSVisitorVoid(apiFeatures)` and `symbol.validate(apiFeatures = apiFeatures)`. The quickstart's `KSVisitorVoid()` and `it.validate()` still work but have been **deprecated since 2.3.12** (new `apiFeatures` wording in 2.3.14).
4. **KSP1 is not "deprecated but available". It is gone in 2.3.x.** `ksp.useKSP2=false` fails configuration. KSP2 is not a compiler plugin and runs in the Gradle daemon.
5. **Versions are decoupled.** KSP 2.3.14 is not "for Kotlin 2.3". It runs with KGP 2.4.21. `environment.compilerVersion` = 2.4.20 (bundled compiler) and `kspVersion` = 2.0.0.
6. **`process()` returns the deferred symbols**, it runs once per round, and a round happens only if the previous round generated a file. In round 1, `getNewFiles()` = the (dirty) source files.
7. **Output paths:** `build/generated/ksp/main/kotlin/` (`test/kotlin` for tests). KMP uses `build/generated/ksp/<target>/<sourceSet>/kotlin` (for example `jvm/jvmMain`). Logs go to `build/kspCaches/main/logs/kspDirtySet.log`, not under `generated`.
8. **`logger.exception` doesn't fail the build**, and `logger.info` is invisible without `--info`. `-q` hides even warnings. The location format is `<absolute path>:<line>:`, with no column.
9. **Dependencies matter:** an all-symbols list must be `aggregating = true`. Otherwise adding a file shrinks the list to just that file [Local]. Outputs with no sources can be deleted on a later incremental build [Local].
10. **`ksp(...)` in a KMP module is a hard error.** Use `kspJvm`, `kspJs`, `kspCommonMainMetadata`, and so on. In single-platform modules `ksp`/`kspTest` are correct. Lambda `CommandLineArgumentProvider`s are not tracked as task inputs.

Runner-up facts: `getAllProperties` includes inherited properties and `getDeclaredProperties` doesn't. `FileLocation` points at the declaration line, not the annotation line. Data-class `copy`/`componentN` show up as `SYNTHETIC` functions. A Java `private` field is visible as a property. `getSymbolsWithAnnotation` needs the fully qualified name.

### A minimal 2.3.14 processor without deprecation warnings [Local, compiled and ran]
```kotlin
class CardProvider : SymbolProcessorProvider {
    override fun create(environment: SymbolProcessorEnvironment) = CardProcessor(environment)
}
class CardProcessor(private val env: SymbolProcessorEnvironment) : SymbolProcessor {
    override val apiFeatures = buildApiFeatures { enableBackingFields = true; enableContextParameters = true }
    override fun process(resolver: Resolver): List<KSAnnotated> {
        val (ready, notYet) = resolver.getSymbolsWithAnnotation("probe.Card")
            .partition { it.validate(apiFeatures = apiFeatures) }
        ready.filterIsInstance<KSClassDeclaration>().forEach { it.accept(CardVisitor(), Unit) }
        return notYet
    }
    inner class CardVisitor : KSVisitorVoid(apiFeatures) {
        override fun visitClassDeclaration(classDeclaration: KSClassDeclaration, data: Unit) {
            val name = classDeclaration.simpleName.asString()
            val pkg = classDeclaration.packageName.asString()
            env.codeGenerator.createNewFile(Dependencies(false, classDeclaration.containingFile!!), pkg, "${name}Card")
                .use { it.write("package $pkg\n\nfun $name.card() = \"$name card\"\n".toByteArray()) }
        }
    }
}
```
Imports: `com.google.devtools.ksp.buildApiFeatures`, `com.google.devtools.ksp.validate`, `com.google.devtools.ksp.processing.*`, `com.google.devtools.ksp.symbol.*`. Enabling both features changed nothing visible for ordinary classes in the probe. With backing fields enabled, `getSymbolsWithAnnotation` may also return `KSBackingField` for field-targeted annotations [Release notes 2.3.12].

### Demo ideas (each shows a mechanism with visible output; all were run on the probe)
1. **Round tracer.** `logger.warn("round ${++round}: new=${resolver.getNewFiles().map { it.fileName }.toList()}")`, with one round-1 file that is itself annotated. Output: three `w: [ksp] round N` lines, the last one generating nothing. Shows rounds, getNewFiles and the stop condition.
2. **Set a box aside.** `@Card class Box(val content: probe.gen.GeneratedContent)`, with the processor writing `GeneratedContent` in round 1. Print `valid`/`invalid` each round: round 1 `invalid=[Box]`, round 2 `valid=[Extra, Box]`.
3. **Forever deferred.** Return the same symbol every round. Output: `finish() after 3 rounds`, `BUILD SUCCESSFUL`, and no complaint. Follow-up exercise: add your own `logger.error` for leftovers.
4. **The label, not the packing.** Describe `data class Person(val nickname: String? = null) { fun greet(g: String = "Hi"): String { val local = ...; return local } }`. Output shows `hasDefault=true` with no value, `declarations=[local]`, and `component1 ... origin=SYNTHETIC`. Nothing from the body's expressions.
5. **A note pointing at a box.** `logger.error("Employee cannot be packed", cls)` → `e: [ksp] /…/Model.kt:26: Employee cannot be packed...`, followed by follow-on `Unresolved reference` lines, `onError()` on both processors, and `KSP failed with exit code: PROCESSING_ERROR`. Contrast with `throw IllegalStateException("boom")`: no `onError()`.
6. **Master list gone wrong.** Write `MasterList` once with `Dependencies(true, ...)` and once with `Dependencies(false, ...)`, then add `Attic.kt`. Aggregating prints `[Kitchen, Garage, Attic, Person]`; isolating prints `[Attic]`. Open `build/kspCaches/main/logs/kspDirtySet.log` to see `Dirty / All: 50.00%` vs `16.67%`.
7. **Only its card is redone.** With `ksp.incremental.log=true`, append a comment to one file and read the `Dirty:` list. `JavaCrate.java` and `Main.kt` are absent and their cards come back from `kspCaches/main/backups`. Then add a `getSealedSubclasses()` call and watch "Affected By sealed" make that file dirty on every build.
8. **Helpers in order.** Two providers in one services file, each logging `round N`. Swap the two lines and the order flips. Helper B sees helper A's round-1 files only in round 2.
9. **Same card twice.** Call `createNewFile(..., "probe.gen", "Extra")` twice → `e: [ksp] kotlin.io.FileAlreadyExistsException: …/generated/ksp/main/kotlin/probe/gen/Extra.kt`.
10. **Stale options.** `arg(CommandLineArgumentProvider { listOf("probe.cmd=$v") })`: run with `-PcmdValue=aaa`, then `bbb`, and get `kspKotlin UP-TO-DATE` with the old value. Switch to a class with `@get:Input` and it reruns.
11. **Java box.** An annotated Java class shows `origin=JAVA`, a private field as a property, and `(String..String?)` with `nullability=PLATFORM`.
12. **Where things land.** Write a `.kt`, a `.java` and a `.txt` file. List `build/generated/ksp/main/{kotlin,java,resources}` and `unzip -l build/libs/app.jar`: the `.class` from the Java file and `META-INF/packing-list.txt` are in the jar.

### Remaining [Unverified] items
- KMP `ksp(...)` behaviour in versions 2.3.0 to 2.3.11. The source has the same throw; I didn't run those versions.
- `logger.error` from inside `finish()` (from source: the build fails and `onError` is not called).
- `error` output under `-q` (from source: shown).
- Ordering of providers that come from different jars.
- KSP1's old "Unable to process" wording.
- Running `KSPJvmMain` with `-processor-options` (the syntax is from source only).
- How `@Nullable`-annotated Java types map.
- Any KSP2-era kapt-vs-KSP benchmark.
- Native task names (`kspKotlinLinuxX64` is from source; not run).
