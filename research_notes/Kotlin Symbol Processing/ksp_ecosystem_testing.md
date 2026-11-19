# KSP around the edges: KotlinPoet, testing, the javac mapping, the ecosystem (Kotlin 2.4.21, KSP 2.3.14, KotlinPoet 2.4.0, kctfork 0.14.0)

Scope: everything around KSP's own API. That means generating code with KotlinPoet, testing processors (kctfork, compile-testing, TestKit, golden files), a precise mapping from KSP to `javax.annotation.processing` (JSR 269) for the Java half of each pair, kapt, the library ecosystem as of November 2026, when KSP is the wrong tool, performance and caching, and the mistakes processor authors make, with the symptom each one produces. A sibling file covers KSP's API and mechanics (Resolver, KS* symbols, rounds, validation, `ApiFeatures`). These notes touch that material only where the mapping or a mistake needs it.

**How the claims were checked.**
- **[Local]**: I ran it in this session on OpenJDK 21.0.12 and 25.0.5, with Gradle 9.8.2 (the labs' wrapper distribution), Kotlin Gradle plugin 2.4.21 and KSP Gradle plugin 2.3.14. The kctfork tests used `dev.zacsweers.kctfork:core`/`:ksp` 0.14.0 with KotlinPoet 2.4.0 and JUnit 6.1.3. The Java side used `com.google.testing.compile:compile-testing:0.24.0` and plain `javac`. The scratch projects live outside the repo.
- **[Source]**: I read the file in a published `-sources.jar` from Maven Central for that exact version (kctfork 0.14.0, kotlinpoet-ksp 2.4.0, kotlinpoet-jvm 2.4.0, compile-testing 0.24.0, Palantir javapoet 0.23.0), or at a git tag on raw.githubusercontent.com (google/ksp `2.3.14`, square/kotlinpoet `2.4.0`, kctfork `0.14.0`).
- **[Docs]**: an official page fetched in this session (2026-11-19). The page date is given where the page shows one.
- **[Unverified]**: not checked here.

Versions on Maven Central, checked 2026-11-19: `symbol-processing-api` **2.3.14** (published 2026-11-13), kctfork **0.14.0** (CHANGELOG date 2026-09-15; its POM pins KSP **2.3.12** and `kotlin-compiler-embeddable` **2.4.20**), kotlinpoet / kotlinpoet-ksp **2.4.0** (changelog date 2026-09-07, "New: KSP 2.3.11"), compile-testing **0.24.0**, Palantir JavaPoet **0.23.0**, Square JavaPoet **1.13.0** (last release 2020).

---

## Summary

- **kctfork 0.14.0 is KSP2-only, and `configureKsp(useKsp2 = true)` no longer compiles.** The parameter was removed in 0.10.0 together with KSP1 support. The current shape is `useKsp2()` followed by `symbolProcessorProviders += provider`, or `configureKsp { symbolProcessorProviders += provider }`. If you set `symbolProcessorProviders` before calling `useKsp2()`/`configureKsp`, the call throws `java.lang.IllegalStateException: KSP not configured`. The README snippet does exactly that. [Source + Local]
- **Version skew breaks the lab stack out of the box.** If the processor depends on `symbol-processing-api:2.3.14` while kctfork 0.14.0 brings `symbol-processing-aa-embeddable`, `symbol-processing-common-deps` and `symbol-processing` at 2.3.12, Gradle upgrades only the API. Any source with a property then fails with `java.lang.NoSuchMethodError: 'boolean ksp.com.google.devtools.ksp.common.visitor.CollectAnnotatedSymbolsVisitor.getEnableNewFeatures()'`, and the exit code is `INTERNAL_ERROR`. Forcing every `com.google.devtools.ksp` artifact to 2.3.14 fixed it: all 16 probe tests passed. [Local]
- **Errors name the declaration's line, not the annotation's line,** in both KSP2 and javac. In kctfork, `logger.error("…", node)` appears in `result.messages` as `e: [ksp] /tmp/Kotlin-Compilation…/sources/Wardrobe.kt:4: @Box can only be applied to classes`, and the exit code is `COMPILATION_ERROR`. A processor that throws gives `INTERNAL_ERROR`. [Local]
- **Skipping originating files only shows up on an incremental build.** With `writeTo(codeGenerator, aggregating = false)` and no `addOriginatingKSFile`, a clean build works. After editing only `A.kt`, KSP reprocessed only `A.kt` and deleted `BLabel.kt` (it logs it under "removed outputs"). The build then failed with `Unresolved reference 'BLabel'`. With originating files, only `A.kt` was reprocessed and `BLabel.kt` survived. [Local, Gradle, `ksp.incremental.log=true`]
- **A processor that defers forever gets no error in KSP 2.3.14.** The round loop stops when a round writes no file, then calls `finish()`, and the deferred symbols are simply dropped (exit `OK`). The kotlinlang page claims KSP "logs an error for each processor with remaining deferred symbols". That is not what 2.3.14 does. [Source at tag 2.3.14 + Local]
- **Missing services file:** `e: [ksp] No providers found in processor classpath.` and `:app:kspKotlin` fails. With a typo in the file, the failure is `com.google.devtools.ksp.processing.SymbolProcessorProvider: Provider move.proc.LabelProvidr not found`. A processor added to its own module's `ksp` configuration gives Gradle's `Circular dependency between the following tasks`. [Local]
- **javac since JDK 23 does not run processors it finds on the class path.** On JDK 25, a processor jar on `-cp` was silently ignored, and the build failed later with `cannot find symbol` for the generated class. `--processor-path`, `-processor` or `-proc:full` turn processing on. JDK 21 still runs it and prints a note. [Local + Docs: JDK 23 release notes]
- **KotlinPoet 2.4.0 handles name clashes with import aliases.** Using `move.Box` and `storage.Box` in one file gave `import move.Box as MoveBox` / `import storage.Box as StorageBox`. It also escapes keywords (`` `in` ``), escapes `$` in `%S` (`${'$'}`), and writes nested types as `Kitchen.Drawer`. In 2.4.0, `KSType.toTypeName()` with the default resolver resolves type parameters instead of throwing. [Local + Docs: changelog]
- **The ecosystem is moving two ways.** Big processors went KSP-first or KSP-only: Room 3.0 is KSP-only, and Dagger/Hilt KSP is "stable as of Dagger 2.60+". Others are leaving KSP for K2 compiler plugins: Koin Annotations (`koin-ksp-compiler` deprecated), Arrow Optics ("Since version 2.3.0, we recommend using the compiler plug-in") and Kotlin DataFrame (KSP plugin deprecated). [Docs, dates below]
- **Caching:** with KSP 2.3.14 on Gradle 9.8.2, the configuration cache was stored and reused with no problems, and after `clean` the `:app:kspKotlin` task came `FROM-CACHE`. The KSP plugin adds `build/generated/ksp/main/kotlin` and `…/java` to the Kotlin `main` source set. [Local]

---

## 1. KotlinPoet for KSP

### 1.1 Why string templates break

The quickstart processor writes code as a raw string (`codeGenerator.createNewFile(…)` plus a `"""fun helloWorld() …"""` template) [Docs: ksp-quickstart, 2026-11-17]. That works for a hello-world and breaks on real input:

- **Imports.** A template must spell out every import, or use fully qualified names everywhere. KotlinPoet: "KotlinPoet has rich built-in support for types, including automatic generation of `import` statements. Just use **`%T`** to reference **types**" [Docs: square/kotlinpoet `docs/t-for-types.md` at 2.4.0].
- **Nested and generic types.** `"${decl.simpleName}"` loses the outer class (`Drawer` instead of `Kitchen.Drawer`). A nested class's qualified name `move.Kitchen.Drawer` cannot be split into package and class names by string surgery: is `Kitchen` a package or a class? `ClassName("move", "Kitchen", "Drawer")` knows. [Local: it emitted `import move.Kitchen` … `Kitchen.Drawer`]
- **Nullability and type arguments.** `KSType.toString()` gives a display form (`List<Item>`), and that string is not a reliable piece of source code. `toTypeName()` keeps `?` at every level. [Local: `LIST.parameterizedBy(item.copy(nullable = true)).copy(nullable = true)` printed `List<Item?>?`]
- **Name clashes.** Two `Box` types from different packages can't both be imported by simple name. KotlinPoet 2.4.0 aliased both: `import move.Box as MoveBox` / `import storage.Box as StorageBox` [Local]. (2.1.0 changelog: "Prevent aliased imports from colliding with existing imports.")
- **Keywords and escaping.** A property named `in`, or a string containing `$` or `"`, produces source that won't compile. `%N` "automatically escap[es] names that contain illegal identifier characters with double ticks" [Docs: `n-for-names.md`]. `%S` "escapes the value as a *string*, wraps it with double quotes… `%S` will also escape all dollar signs (`$`), use `%P` for string templates" [Source: CodeBlock.kt KDoc]. [Local: `` `in`: Kitchen.Drawer `` and `println("Total: ${'$'}5 for \"fragile\" box")`]

KotlinPoet still does not model expressions: "the _body_ of methods and constructors is not modeled. There's no expression class, no statement class or syntax tree nodes. Instead, KotlinPoet uses strings for code blocks" [Docs: `code-control-flow.md`]. Bodies are format strings with placeholders.

### 1.2 The model, with 2.4.0 signatures [Source: kotlinpoet-jvm-2.4.0-sources.jar]

```kotlin
FileSpec.builder(packageName: String, fileName: String): FileSpec.Builder
FileSpec.builder(className: ClassName): FileSpec.Builder
TypeSpec.classBuilder(name: String) / classBuilder(className: ClassName)      // also objectBuilder, interfaceBuilder, enumBuilder
FunSpec.builder(name: String); FunSpec.constructorBuilder()
PropertySpec.builder(name: String, type: TypeName, vararg modifiers: KModifier)  // overloads for Type and KClass<*>
ParameterSpec.builder(name: String, type: TypeName, vararg modifiers: KModifier)
CodeBlock.of(format: String, vararg args: Any?): CodeBlock
ClassName(packageName: String, vararg simpleNames: String); ClassName.nestedClass(name: String)
ClassName.parameterizedBy(vararg typeArguments: TypeName): ParameterizedTypeName  // import ParameterizedTypeName.Companion.parameterizedBy
TypeName.copy(nullable: Boolean = this.isNullable, annotations: List<AnnotationSpec> = …): TypeName
FileSpec.writeTo(out: Appendable) / writeTo(directory: Path) / writeTo(directory: File) / writeTo(filer: Filer)
```

There is no data-class builder. Use `classBuilder(...).addModifiers(KModifier.DATA)` [Source: no `dataClassBuilder` in TypeSpec.kt]. KotlinPoet emits explicit `public`: "In order to maximize portability, KotlinPoet generates code with explicit visibility modifiers" [Docs: `index.md`]. It also turns a one-statement `return` body into an expression body [Local: `public fun describe(box: KitchenBox): String = "KitchenBox: " + …`].

### 1.3 Placeholders [Source: CodeBlock.kt KDoc, 2.4.0]

- `%T`: "emits a *type* reference. Types will be imported if possible."
- `%N`: "emits a *name*, using name collision avoidance where necessary. Arguments for names may be strings…, parameters, properties, functions, and types."
- `%S`: a string literal, quoted and escaped, `$` included.
- `%P`: "Similar to `%S`, but doesn't escape dollar signs (`$`) to allow creation of string templates."
- `%L`: "emits a *literal* value with no escaping. Arguments for literals may be strings, primitives, type declarations, annotations and even other code blocks."
- `%M`: "emits a *member* reference… the import will be resolved if possible" (needs a `MemberName`). [Local: `%M` with `MemberName("kotlin.collections", "mutableMapOf")` added `import kotlin.collections.mutableMapOf`]
- `%%`, `♢`, `·`, `⇥`, `⇤`, `«`, `»`. Since 2.0.0: "spaces in generated code don't wrap by default anymore… The newly introduced `♢` character can be used to mark spaces that are safe to wrap… The `·` character has been preserved for compatibility, but its behavior is now equivalent to a regular space character" [Docs: changelog 2.0.0, 2024-10-23]. Older blog posts that tell you to use `·` to stop wrapping describe 1.x behaviour.
- Positional (`%2L`) and named (`%count:L` with `addNamed`) arguments exist. "Only one style may be used for each operation on a code block" [Docs: `code-block-format-strings.md`].

### 1.4 kotlinpoet-ksp interop, exact 2.4.0 signatures [Source: kotlinpoet-ksp-2.4.0-sources.jar]

```kotlin
// package com.squareup.kotlinpoet.ksp
public fun KSClassDeclaration.toClassName(): ClassName
public fun KSTypeAlias.toClassName(): ClassName
public fun KSType.toClassName(): ClassName            // throws if the type has type arguments
public fun KSType.toClassNameOrNull(): ClassName?
public fun KSType.toTypeName(typeParamResolver: TypeParameterResolver = TypeParameterResolver.EMPTY): TypeName
public fun KSTypeReference.toTypeName(typeParamResolver: TypeParameterResolver = TypeParameterResolver.EMPTY): TypeName
public fun KSTypeArgument.toTypeName(typeParamResolver: TypeParameterResolver = TypeParameterResolver.EMPTY): TypeName
public fun KSTypeParameter.toTypeVariableName(typeParamResolver: TypeParameterResolver = TypeParameterResolver.EMPTY): TypeVariableName
public fun List<KSTypeParameter>.toTypeParameterResolver(
    parent: TypeParameterResolver? = null, sourceTypeHint: String = "<unknown>"): TypeParameterResolver
public fun KSAnnotation.toAnnotationSpec(omitDefaultValues: Boolean = false): AnnotationSpec
public fun Modifier.toKModifier(): KModifier?
public fun Visibility.toKModifier(): KModifier?

public fun TypeSpec.Builder.addOriginatingKSFile(ksFile: KSFile): TypeSpec.Builder      // also FunSpec.Builder,
public fun FileSpec.originatingKSFiles(): List<KSFile>                                 // PropertySpec.Builder, TypeAliasSpec.Builder
public fun FileSpec.writeTo(codeGenerator: CodeGenerator, aggregating: Boolean,
    originatingKSFiles: Iterable<KSFile> = originatingKSFiles())
public fun FileSpec.writeTo(codeGenerator: CodeGenerator, dependencies: Dependencies)
public fun FileSpec.kspDependencies(aggregating: Boolean,
    originatingKSFiles: Iterable<KSFile> = originatingKSFiles()): Dependencies
```

Facts that matter:
- **`aggregating` is required.** "`FileSpec.writeTo(CodeGenerator, ...)` also requires you to specify if your processor is _aggregating_ or not via required parameter by the same name" [Docs: `interop-ksp.md`].
- **Originating files are collected automatically, but only from top-level members.** "calling the `FileSpec.writeTo(CodeGenerator, ...)` function will automatically collect and de-dupe these originating `KSFile` references and automatically assemble them in the underlying `Dependencies`" [Docs: `interop-ksp.md`]. `FileSpec.originatingKSFiles()` walks `members` (the top-level funs, properties, types and typealiases) and does not descend into nested types [Source: OriginatingKSFiles.kt]. There is no `FileSpec.Builder.addOriginatingKSFile`, so tag the top-level `TypeSpec`.
- `writeTo(codeGenerator, dependencies)` is literally `codeGenerator.createNewFile(dependencies, packageName, name)` plus a UTF-8 `OutputStreamWriter` [Source].
- **The `kotlinpoet-ksp` POM declares no dependency on `symbol-processing-api`**, only `kotlinpoet-jvm` and `kotlin-stdlib`. The processor module must declare the KSP API itself [Source: kotlinpoet-ksp-2.4.0.pom].
- **Error messages** [Source: utils.kt, KsTypes.kt]:
  - On an unresolved type: `java.lang.IllegalArgumentException: Error type '<ERROR TYPE: GeneratedLater>' is not resolvable in the current round of processing.` [Local: thrown from `toTypeName()` on `class Shelf(val box: GeneratedLater)`. The exit code was `INTERNAL_ERROR`.] Check `isError` or `validate()` and defer, before converting.
  - `KSType.toClassName()` on `List<Item>`: `"KSType '$this' has type arguments, which are not supported for ClassName conversion. Use KSType.toTypeName()."`
  - On a local class: `"Local/anonymous classes are not supported!"`
- **TypeParameterResolver.** "In order for these elements to resolve these in KSP, you must be able to reference these type parameters by their _index_… The canonical way to create an instance of this is to call `toTypeParameterResolver()` on a `List<KSTypeParameter>`" [Docs: `interop-ksp.md`]. Compose class and function resolvers with `parent =`. **2.4.0 change:** "`KSType.toTypeName()` with the default `TypeParameterResolver.EMPTY` now resolves type parameters from their enclosing declarations instead of throwing. (#2368)" [Docs: changelog]. [Local: for `class Shelf<T : Comparable<T>>(val item: T, val spare: List<T>?)`, both `EMPTY` and the explicit resolver printed `T` and `kotlin.collections.List<T>?`. `fun <E> swap(e: E, t: T)` with `parent = classParams` gave `[E, T]`.] Lessons written against older blog posts will say this throws. In 2.4.0 it does not.
- `Modifier.toKModifier()` and `getVisibility().toKModifier()` convert modifiers. The docs' example turns `internal inline val` into `[KModifier.INLINE]` and `KModifier.INTERNAL` [Docs: `interop-ksp.md`].
- `:interop:javapoet` "has been discontinued and is not published starting with this release" (2.3.0, 2026-03-27) [Docs: changelog].

### 1.5 What goes wrong if you skip the originating files [Local, Gradle 9.8.2 + KSP 2.3.14]

Setup: `app` has `A.kt` (`@Box class A`), `B.kt` (`@Box class B`) and `Main.kt`, which uses `ALabel` and `BLabel`. The processor writes `<Name>Label` per class with `writeTo(env.codeGenerator, aggregating = false)`. The `ksp.incremental.log=true` logs are under `app/build/kspCaches/main/logs/`.

| Step | With `addOriginatingKSFile(s.containingFile!!)` | Without it |
|---|---|---|
| Clean build | OK. `kspSourceToOutputs.log` maps `A.kt → ALabel.kt`, `B.kt → BLabel.kt` | OK. Both outputs sit under `<This is a virtual key for unassociated outputs; DO NOT USE>` |
| Edit only `A.kt`, build | `Dirty: src/main/kotlin/move/A.kt`, `Dirty / All: 33.33%`. Only `ALabel` is regenerated, and `BLabel` is kept | Also only A is reprocessed (`round: [A]`), but `BLabel.kt` moves to `<This is a virtual key for removed outputs…>` and is deleted. `:app:compileKotlin FAILED`: `Unresolved reference 'BLabel'.` |

The lesson: **the bug never shows on a clean build or in kctfork.** It appears as a mysterious "Unresolved reference" to generated code after an ordinary edit, and it goes away after `./gradlew clean`. KSP's own doc says the same in general terms: "When generating an output, the processor must declare the root sources that contribute to that output" [Docs: ksp-incremental, 2026-11-17].

### 1.6 JavaPoet, the Java counterpart

- Square's JavaPoet is deprecated: "As of 2020-10-10, Square's JavaPoet project is deprecated… one option is Palantir's JavaPoet" (coordinates `com.palantir.javapoet:javapoet`, package `com.palantir.javapoet`) [Docs: square/javapoet README]. Palantir's README lists the changes: "Changed package name to `com.palantir.javapoet`", "Made implementation-specific fields `private` and instead added getter methods", plus record and `sealed` support [Docs: palantir/javapoet README]. Latest on Central: 0.23.0.
- The shapes are the same as KotlinPoet's, with `$` instead of `%`: `MethodSpec.methodBuilder("main")…addStatement("$T.out.println($S)", System.class, "Hello, JavaPoet!")`, `TypeSpec.classBuilder(…)`, `JavaFile.builder("com.example.helloworld", helloWorld).build().writeTo(System.out)`, and placeholders `$T $N $S $L` [Docs: README].
- `JavaFile.writeTo(Filer)` (Palantir 0.23.0) calls `filer.createSourceFile(fileName, originatingElements…)` with the elements collected from `typeSpec.originatingElements()`. They are added with `TypeSpec.Builder.addOriginatingElement(Element)`. On failure it deletes the half-written file [Source: JavaFile.java]. This is the exact counterpart of kotlinpoet-ksp's `addOriginatingKSFile` + `writeTo(codeGenerator, …)`.
- KotlinPoet can also write to a javac `Filer`, which is how kapt processors emit Kotlin. `FileSpec.writeTo(filer: Filer)` gathers `originatingElements` and calls `filer.createResource(StandardLocation.SOURCE_OUTPUT, packageName, "$name.$extension", …)` [Source: FileSpec.kt].

---

## 2. Testing processors

### 2.1 kctfork 0.14.0: the exact KSP2 API shape [Source: ksp-0.14.0-sources.jar, core-0.14.0-sources.jar; Local]

Coordinates: `testImplementation("dev.zacsweers.kctfork:core:0.14.0")` and `testImplementation("dev.zacsweers.kctfork:ksp:0.14.0")`. **The Kotlin package is still `com.tschuchort.compiletesting`**, not `dev.zacsweers…`. `KotlinCompilation` and `AbstractKotlinCompilation` are annotated `@ExperimentalCompilerApi`, which is `@RequiresOptIn` at the default (error) level. Add `@OptIn(ExperimentalCompilerApi::class)` or the compiler option `optIn.add("org.jetbrains.kotlin.compiler.plugin.ExperimentalCompilerApi")`.

```kotlin
// in com.tschuchort.compiletesting (ksp module), 0.14.0
fun KotlinCompilation.useKsp2()                                   // registers the "ksp2" precursor tool
fun KotlinCompilation.configureKsp(body: KspTool.() -> Unit)      // calls useKsp2(), then body
var KotlinCompilation.symbolProcessorProviders: MutableList<SymbolProcessorProvider>
var KotlinCompilation.kspProcessorOptions: MutableMap<String, String>   // kspArgs is @Deprecated
var KotlinCompilation.kspIncremental / kspIncrementalLog / kspAllWarningsAsErrors / kspWithCompilation: Boolean
var KotlinCompilation.kspLoggingLevels: Set<CompilerMessageSeverity>
val KotlinCompilation.kspSourcesDir: File                         // = workingDir/ksp/sources
val JvmCompilationResult.sourcesGeneratedBySymbolProcessor: Sequence<File>
// KspTool (receiver of configureKsp): symbolProcessorProviders, processorOptions, incremental,
//   incrementalLog, allWarningsAsErrors, withCompilation, loggingLevels
```

**History you will meet in blog posts.** Through 0.9.0 the signature was `fun KotlinCompilation.configureKsp(useKsp2: Boolean = false, body: KspTool.() -> Unit)` [Source: ksp-0.9.0-sources.jar]. In 0.10.0 (2025-10-05) it became `configureKsp(body)`, and the changelog says "Remove support for KSP1. Only KSP2 is supported now" [Source: 0.10.0 jar + CHANGELOG]. So `configureKsp(useKsp2 = true) { … }` **does not compile on 0.14.0**.

The test as I ran it (it passed) [Local]:

```kotlin
@OptIn(ExperimentalCompilerApi::class)
class LabelProcessorTest {
  @Test fun `generates a label object`() {
    val compilation = KotlinCompilation().apply {
      sources = listOf(
        SourceFile.kotlin("Box.kt", """
          package move
          annotation class Box
        """),
        SourceFile.kotlin("KitchenBox.kt", """
          package move

          @Box
          data class KitchenBox(val label: String, val fragile: Boolean)
        """))
      inheritClassPath = true                        // compiled sources see the test classpath
      messageOutputStream = ByteArrayOutputStream()  // default is System.out
      useKsp2()
      symbolProcessorProviders += LabelProvider()
      // equivalent: configureKsp { symbolProcessorProviders += LabelProvider(); processorOptions["k"] = "v" }
    }
    val result = compilation.compile()
    assertThat(result.exitCode).isEqualTo(KotlinCompilation.ExitCode.OK)

    val generated = compilation.kspSourcesDir.resolve("kotlin/move/KitchenBoxLabel.kt")
    assertThat(generated.readText()).contains("public object KitchenBoxLabel")

    val boxClass = result.classLoader.loadClass("move.KitchenBox")
    val box = boxClass.getConstructor(String::class.java, Boolean::class.javaPrimitiveType).newInstance("Plates", true)
    val label = result.classLoader.loadClass("move.KitchenBoxLabel")
    val text = label.getMethod("describe", boxClass).invoke(label.getField("INSTANCE").get(null), box)
    assertThat(text).isEqualTo("KitchenBox: Plates, true")
  }
}
```

Observed shapes [Local]:
- `kspSourcesDir` = `/tmp/Kotlin-Compilation<random>/ksp/sources`. The generated file was at `kotlin/move/KitchenBoxLabel.kt`. Java output goes to `java/` and resources to `resources/` [Source: Ksp2.kt]. `result.sourcesGeneratedBySymbolProcessor.map { it.name }` gave `[KitchenBoxLabel.kt]`. `result.outputDirectory` is `…/classes`.
- `result.classLoader` is a `URLClassLoader` over `classpaths + outputDirectory`, with the test's loader as parent [Source: CompilationResult.kt].
- The `ExitCode` enum is `OK, INTERNAL_ERROR, COMPILATION_ERROR, SCRIPT_EXECUTION_ERROR`. `logger.error(...)` gives `COMPILATION_ERROR`. An exception thrown from `process()` (including KotlinPoet's error-type exception and `FileAlreadyExistsException`) gives `INTERNAL_ERROR`, with the exception text and stack trace in `messages`. This matches kctfork's own test `failedKspTest`, which asserts `ExitCode.INTERNAL_ERROR` and `messages.contains("intentional fail")` [Source: KspTest.kt at tag 0.14.0].
- `result.messages` is a String. `result.diagnosticMessages` is a `List<DiagnosticMessage(severity, message)>`. `messagesWithSeverity(DiagnosticSeverity.WARNING)` filters by severity.

### 2.2 Testing that an error names the right file and line [Local]

```kotlin
val bad = SourceFile.kotlin("Wardrobe.kt", """
    package move

    @Box
    interface Wardrobe
""")
// processor: env.logger.error("@Box can only be applied to classes", symbol)
```
`result.messages` contained:
```
e: Error occurred in KSP, check log for detail
e: [ksp] /tmp/Kotlin-Compilation11934283814644167893/sources/Wardrobe.kt:4: @Box can only be applied to classes
```
In `diagnosticMessages` the same entry is `ERROR: /tmp/…/sources/Wardrobe.kt:4: @Box…` (no `[ksp] ` prefix). The format comes from kctfork's `TestKSPLogger`: `"$PREFIX${location.filePath}:${location.lineNumber}: $message"`, and with no location just `"[ksp] $message"` [Source]. The path is a random temp dir, so assert on the suffix:
`assertThat(result.messages).contains("Wardrobe.kt:4: @Box can only be applied to classes")`.
**Line 4 is the `interface` line, not the `@Box` line (3).** A second probe with `@Box` / `internal` / `interface Attic` on lines 3, 4 and 5 reported line 5. `@Box interface Cellar` on line 7 reported 7. javac and compile-testing do the same (§2.6).

### 2.3 Known problems and traps with kctfork + KSP2

1. **KSP artifact skew → `NoSuchMethodError`** [Local]. The lab versions (processor on API 2.3.14, kctfork pinned to 2.3.12) produced `java.lang.NoSuchMethodError: 'boolean ksp.com.google.devtools.ksp.common.visitor.CollectAnnotatedSymbolsVisitor.getEnableNewFeatures()'` from `getSymbolsWithAnnotation` whenever a class had a property. Tests with no properties passed, so the failure looks random. Fix used:
   ```kotlin
   configurations.configureEach {
     resolutionStrategy.eachDependency {
       if (requested.group == "com.google.devtools.ksp") useVersion("2.3.14")
     }
   }
   ```
   After this fix all 16 probes passed, with kctfork's 2.4.20 compiler running KSP 2.3.14. The alternative is to keep the processor on API 2.3.12. kctfork's README warns about the same class of problem for compiler artifacts: "they have to be the same version as the one used by Kotlin-Compile-Testing or there will be a transitive dependency conflict" [Docs: README].
2. **The README is out of date for 0.14.0** [Source]. Its `symbolProcessorProviders = listOf(MySymbolProcessorProvider())` (a) is set before KSP is enabled, so it throws `IllegalStateException: KSP not configured` [Local], and (b) assigns a `List` to a `MutableList` property. Its `compilerPlugins = …` is now `compilerPluginRegistrars`.
3. **Incremental processing can't be tested in kctfork.** Each run deletes and recreates `kspCachesDir`, `kspSourcesDir`, `kspClassesDir` and the output dirs (`.also { it.deleteRecursively(); it.mkdirs() }`), and passes no modified or removed file sets [Source: Ksp2.kt]. `kspIncremental = true` changes nothing across two `compile()` calls. Use Gradle TestKit for §1.5-style tests.
4. **`kspWithCompilation` is a no-op on KSP2.** The getter is hard-wired to `false`, and the setter body is the comment `// Irrelevant/unavailable on KSP 2` [Source].
5. **The in-memory compile uses Kotlin 2.4.20**, the `kotlin-compiler-embeddable` version kctfork depends on, even though the project builds with 2.4.21 [Source: core POM].
6. **Fixed bugs you may see in old threads** [Docs: CHANGELOG]: 0.11.0 (2025-10-22) "Feed generated `.java` files from KSP into the subsequent kotlin compilation". 0.12.1 (2026-01-04) "Clear KSP2's `KSPCoreEnvironment` as it leaks memory across multiple runs in tests". 0.13.0 "remove the memory leak patch as it's now fixed upstream".
7. **Noise in `messages`.** KSP 2.3.14 adds INFO lines for every processor that hasn't configured `apiFeatures`, for example `i: [ksp] Processor 'lab.LabelProcessor' has not enabled the following API features: enableBackingFields, enableContextParameters. It might break in a future version of KSP…`, and `i: [ksp] Note that 'SymbolProcessorEnvironment.registerProcessorForNewFeatures' is deprecated…`. An anonymous `object : SymbolProcessor` shows as `Processor 'null'` [Local]. Assert with `contains`, never equality on the whole string. (The sibling file covers `ApiFeatures`.)
8. **Cost.** The first compile in a test JVM took 7.2 s and later ones 0.1 to 1.3 s each (14 tests, 15.6 s suite, 4-core machine) [Local].

### 2.4 Alternatives

- **Gradle TestKit.** "The GradleRunner uses the Tooling API to execute builds. This means that builds run in a separate process from your tests" [Docs: test_kit.html, Gradle 9.9.2 docs]. It is slower (a Gradle daemon plus a real `kspKotlin` task), but it is the only way to test the things kctfork cannot see: incremental behaviour and originating files (§1.5), the services file and processor-classpath wiring, `ksp { arg(...) }`, KMP per-target configurations, and build-cache/configuration-cache compatibility. Use a handful of TestKit tests for those and kctfork for everything else.
- **Golden-file (snapshot) tests.** Compare `kspSourcesDir.resolve("kotlin/move/KitchenBoxLabel.kt").readText()` with `src/test/resources/golden/KitchenBoxLabel.kt`. Better still, split the processor into "KS symbols → plain data model" and "data model → `FileSpec`", then unit-test the second half with `fileSpec.toString()` and no compiler at all. Golden files catch accidental output changes, but they are brittle across KotlinPoet upgrades (2.4.0 changed annotation array syntax to `[]` and expression-body indentation [Docs: changelog]). Pair each one with at least one behavioural test that loads the generated class.
- compile-testing for Java is the model for all of this. kctfork describes itself as "in the spirit of Google Compile Testing" [Docs: README].

### 2.5 The Java side: google/compile-testing 0.24.0 [Source + Local]

Its README is now one line ("A library for testing javac compilation with or without annotation processors. See the javadoc for usage examples."). The examples are in `package-info.java`. Verified API: `Compiler.javac()`, `withProcessors(Processor...)`, `withOptions(...)`, `compile(JavaFileObject...)`, `JavaFileObjects.forSourceString(fullyQualifiedName, source)`, and `CompilationSubject.assertThat(compilation)` with `.succeeded()`, `.succeededWithoutWarnings()`, `.failed()`, `.hadErrorContaining(s).inFile(file).onLine(n)` (also `.atColumn(n)`, `.onLineContaining(s)`), `.generatedSourceFile("move.KitchenBoxLabel").contentsAsUtf8String().contains(…)` and `.hasSourceEquivalentTo(…)`. Dependencies: Truth 1.4.5 and Guava 33.7.2-jre (POM).

```java
JavaFileObject wardrobe = JavaFileObjects.forSourceString("move.Wardrobe", """
    package move;

    @Box
    interface Wardrobe {}
    """);
Compilation compilation = javac().withProcessors(new BoxProcessor()).compile(wardrobe);
assertThat(compilation).failed();
assertThat(compilation).hadErrorContaining("@Box can only be applied to classes").inFile(wardrobe).onLine(4);
```
This passed on JDK 21 with JUnit 6. `onLine(3)` failed with `Expected an error containing "@Box can only be applied to classes" in move/Wardrobe.java on line:\n   3: @Box\nbut found it on line(s):\n   4: interface Wardrobe {}` [Local]. compile-testing uses the in-process javac API and passes processors directly, so the JDK 23 discovery change (§3.6) does not affect it.

---

## 3. KSP ↔ Java annotation processing (JSR 269)

The official KSP page "Java annotation processing to KSP reference" (kotlinlang.org/docs/ksp-reference.html, 2026-08-12) maps the model types. The table below adds the processing infrastructure. Javadoc quotes are from the Java SE 25 API (docs.oracle.com).

| KSP | javax.annotation.processing / javax.lang.model | Notes |
|---|---|---|
| `SymbolProcessorProvider.create(environment)` + `SymbolProcessor.process(resolver): List<KSAnnotated>`, `finish()`, `onError()` | `Processor` / `AbstractProcessor` with `init(ProcessingEnvironment)` and `process(Set<? extends TypeElement>, RoundEnvironment): boolean` | javac needs a "public no-argument constructor". KSP uses a factory instead. KSP processors return deferred symbols, while javac returns "claimed" |
| (nothing: every processor sees every file) | `@SupportedAnnotationTypes("move.Box")` / `getSupportedAnnotationTypes()` | KSP has no claiming. `AbstractProcessor`: "If the class is not so annotated, an empty set is returned." |
| `environment.kotlinVersion`, `apiVersion`, `compilerVersion`, `kspVersion` | `getSupportedSourceVersion()` / `@SupportedSourceVersion` | `AbstractProcessor` default: "If the class is not so annotated, `SourceVersion.RELEASE_6` is returned." This gives two warnings (§3.6) |
| `SymbolProcessorEnvironment` (`options`, `codeGenerator`, `logger`, versions, `platforms`) | `ProcessingEnvironment` (`getOptions`, `getFiler`, `getMessager`, `getElementUtils`, `getTypeUtils`) | Elements/Types utilities map to `Resolver` plus extension functions |
| `environment.options` (from `ksp { arg("k","v") }`) | `getOptions()`, `-Akey=value`, `getSupportedOptions()` | javac warns about options no processor declares. KSP does not |
| `resolver.getSymbolsWithAnnotation("move.Box")` | `roundEnv.getElementsAnnotatedWith(TypeElement)` or `(Class<? extends Annotation>)` | Both take the **qualified** name or type |
| `KSClassDeclaration` / `KSPropertyDeclaration`, `KSValueParameter` / `KSFunctionDeclaration` | `TypeElement` / `VariableElement` / `ExecutableElement` | ksp-reference: "VariableElement → KSValueParameter/KSPropertyDeclaration" |
| `KSType` (`isAssignableFrom`, `==`, `isMarkedNullable`) | `TypeMirror` + `Types.isAssignable(t1, t2)`, `isSameType` | ksp-reference: "isAssignable → ksType.isAssignableFrom" and "isSameType → ksType.equals". **The argument order is flipped.** |
| `codeGenerator.createNewFile(Dependencies(aggregating, *files), pkg, name, ext = "kt")` | `filer.createSourceFile(name, originatingElements…)` | Both: create once per run. Both: originating inputs drive incrementality |
| `logger.error(msg, node)` / `warn` / `info` / `logging` / `exception(t)` | `messager.printMessage(Diagnostic.Kind.ERROR, msg, element)` (plus overloads for `AnnotationMirror` and `AnnotationValue`) | |
| Rounds end when a round generates no file. Defer by returning symbols. `finish()` at the end | Rounds until no new files, then a final round where `processingOver()` is true | javac has no built-in deferral |
| `META-INF/services/com.google.devtools.ksp.processing.SymbolProcessorProvider` | `META-INF/services/javax.annotation.processing.Processor` | AutoService generates the javac one. `auto-service-ksp` can run under KSP |
| Per-output `Dependencies(aggregating = …)` | Gradle: per-processor `META-INF/gradle/incremental.annotation.processors` (`isolating` / `aggregating` / `dynamic`) | KSP: "Unlike Gradle annotation processing, KSP applies the categorization to individual outputs" |
| `ksp(...)` / `kspTest(...)` / `ksp<Target>` configuration | Gradle `annotationProcessor(...)`. javac: `-processor`, `--processor-path`, `-proc:full` | |

### 3.1 Processor lifecycle and environment
- `Processor` Javadoc: "Each implementation of a `Processor` must provide a public no-argument constructor… the tool calls the `init` method with an appropriate `ProcessingEnvironment`… the tool calls `getSupportedAnnotationTypes`, `getSupportedOptions`, and `getSupportedSourceVersion`. These methods are only called once per run, not on each round… a new `Processor` object is not created for each round." KSP, for comparison: "KSP creates a processor instance only once. You can store information in the processor instance and reuse it across multiple rounds… Do not store a Resolver and reuse it across rounds" [Docs: ksp-multi-round, 2026-11-17].
- `ProcessingEnvironment.getOptions()`: "Returns the processor-specific options passed to the annotation processing tool… a command-line implementation may distinguish processor-specific options by prefixing them with a known string like "-A"". [Local: an undeclared `-Adup` gave `warning: The following options were not recognized by any processor: '[dup]'`]
- `getMessager()`: "Returns the messager used to report errors, warnings, and other notices." `getFiler()`: "Returns the filer used to create new source, class, or auxiliary files." `getElementUtils()` / `getTypeUtils()`: "utility methods for operating on elements" and "on types".
- Discovery and claiming (no KSP equivalent): "Which processors the tool asks to run is a function of the interfaces of the annotations present on the root elements, what annotation interfaces a processor supports, and whether or not a processor claims the annotation interfaces it processes" [Processor Javadoc]. And: "Note that if a processor supports "*" and returns `true`, all annotations are claimed."

### 3.2 Symbols and types
- `getElementsAnnotatedWith(TypeElement a)`: "Returns the elements annotated with the given annotation interface. The annotation may appear directly or be inherited."
- `TypeElement`: "Represents a class or interface program element." `VariableElement`: "Represents a field, enum constant, method or constructor parameter, local variable, resource variable, or exception parameter." `ExecutableElement`: "Represents a method, constructor, or initializer (static or instance) of a class or interface, including annotation interface elements."
- `TypeMirror`: "Types should be compared using the utility methods in `Types`. There is no guarantee that any particular type will always be represented by the same object." `Element`: "Elements should be compared using the `equals(Object)` method."
- The KSP reference also notes that "KSP requires explicit type resolution". `KSTypeReference` must be `resolve()`d, while `TypeMirror`s arrive already resolved. "Type resolution is one of the most expensive operations in the KSP API" [Docs: ksp-kotlin-model].

### 3.3 Writing files
- `Filer` Javadoc: "During each run of an annotation processing tool, a file with a given pathname may be created only once… Any subsequent attempt to create the same file during a run will throw a `FilerException`". On originating elements: "the originating elements are intended to have the granularity of compilation units… essentially file-level granularity… This information may be used in an incremental environment to determine the need to rerun processors or remove generated files." The javadoc's example is `filer.createSourceFile("GeneratedFromUserSource", eltUtils.getTypeElement("UserSource"))`.
- New files are processed in the next round "after the `close` method has been called on the `Writer` or `OutputStream`".
- KSP `CodeGenerator.createNewFile` KDoc (2.3.14): "Sources of corresponding [KSNode]s which are obtained directly from [Resolver] need to be specified… If a [KSFile] is indirectly obtained through other [KSNode]s, it hasn't to be specified for the given output…" It also says `extensionName`: "If "kt" or "java", this file will participate in subsequent compilation." On `Dependencies.ALL_FILES`: "Associating an output to [ALL_SOURCES] essentially disables incremental processing, as the tiniest change will clobber all files." [Source]

### 3.4 Messages
- `Messager`: "Elements, annotations, and annotation values can be passed to provide a location hint for the message. However, such location hints may be unavailable or only approximate. Printing a message with an error kind will raise an error."
- [Local, JDK 25] `printMessage(ERROR, "@Box can only be applied to classes", e)` printed `app/Wardrobe.java:4: error: @Box can only be applied to classes`, the source line, and a caret under `interface`.
- KSP: "When a processor reports an error, KSP calls `SymbolProcessor.onError()` instead of `SymbolProcessor.finish()`. Processing stops after the current round completes" [Docs: ksp-multi-round]. javac: "If a processor raises an error, the current round will run to completion and the subsequent round will indicate an error was raised" (`RoundEnvironment.errorRaised()`).

### 3.5 Rounds and deferral
- javac: "If a processor was asked to process on a given round, it will be asked to process on subsequent rounds, including the last round, even if there are no annotations for it to process." `processingOver()`: "Returns `true` if types generated by this round will not be subject to a subsequent round of annotation processing." [Local: the Java `BoxProcessor` logged `round: annotations=[move.Box] over=false`, then `annotations=[] over=false` (the round that saw its generated file), then `annotations=[] over=true`. That is three rounds.]
- KSP: "To defer symbols to the next round, return them from `SymbolProcessor.process()`… Multiple-round processing ends when an entire round generates no new files." `getSymbolsWithAnnotation()` "returns only symbols from newly generated files and symbols deferred from the previous round" [Docs: ksp-multi-round]. KSP has no extra empty `processingOver` round. `finish()` is the end hook. javac has no deferral mechanism, so Java processors keep the names of elements they couldn't handle and look them up again next round (for example with `Elements.getTypeElement`).
- **Docs versus implementation:** kotlinlang says "If deferred symbols remain unprocessed, KSP logs an error for each processor with remaining deferred symbols." KSP 2.3.14's `KotlinSymbolProcessing.execute` breaks out of the loop on `if (logger.hasError || codeGenerator.generatedFile.isEmpty())` and then calls `finish()`. I found no error path for leftover deferred symbols [Source: tag 2.3.14]. [Local: a processor that returned every symbol every round ran 1 round, `finish()` was called, exit `OK`, no diagnostic.]

### 3.6 Registration, discovery and how javac is told to run a processor
- KSP: "In the `resources/META-INF/services` directory, create a `com.google.devtools.ksp.processing.SymbolProcessorProvider` file and add the provider's fully qualified name" [Docs: ksp-quickstart]. Consumers use `ksp(project(":processor"))`, with "`kspTest(...)` configuration" for tests [same page].
- javac: `META-INF/services/javax.annotation.processing.Processor`. AutoService "will generate the file `META-INF/services/javax.annotation.processing.Processor` in the output classes folder" [Docs: google/auto service README]. The same README adds "if this metadata file is included in a jar, and that jar is on javac's classpath, then `javac` will automatically load it". **That is no longer true by default on JDK 23+**, see the next bullet.
- **JDK 23 change:** "As of JDK 23, annotation processing is only run with some explicit configuration of annotation processing or with an explicit request to run annotation processing on the javac command line… In JDK 21 and 22, javac prints a note identifying such invocations. To preserve the old behavior, "-proc:full" can be passed to javac" [Docs: Oracle JDK 23 release notes, JDK-8321314]. [Local] JDK 21 with the jar on `-cp` ran the processor and printed `Note: Annotation processing is enabled because one or more processors were found on the class path. A future release of javac may disable annotation processing unless at least one processor is specified by name (-processor), or a search path is specified (--processor-path, --processor-module-path), or annotation processing is enabled explicitly (-proc:only, -proc:full).` JDK 25 with the same command did not run it and failed with `error: cannot find symbol … KitchenBoxLabel`. `--processor-path`, `-processor move.BoxProcessor` or `-proc:full` all worked.
- A processor with no `@SupportedSourceVersion` produced, on JDK 25: `warning: No SupportedSourceVersion annotation found on move.BoxProcessor, returning RELEASE_6.` and `warning: Supported source version 'RELEASE_6' from annotation processor 'move.BoxProcessor' less than -source '25'` [Local]. The Java lab processors should declare `@SupportedSourceVersion(SourceVersion.RELEASE_21)` or override `getSupportedSourceVersion()` to return `SourceVersion.latestSupported()`.
- Gradle: "Gradle ignores annotation processors on the compile classpath," and the `annotationProcessor` configuration "Represents annotation processors used during the compilation of a project's source code" [Docs: Gradle Java plugin, 9.9.2 docs]. Gradle passes the processor path explicitly, so the JDK 23 change doesn't affect Gradle builds that use `annotationProcessor`.
- **auto-service-ksp** (`dev.zacsweers.autoservice:auto-service-ksp:1.2.0`, 2024-06) still worked with KSP 2.3.14. Applied with `ksp(...)` in the processor module plus `implementation("com.google.auto.service:auto-service-annotations:1.1.1")`, it generated `META-INF/services/com.google.devtools.ksp.processing.SymbolProcessorProvider` containing `move.proc.LabelProvider` [Local]. Its README: "NOTE: It's important that you _don't_ use compileOnly here".
- Real artifacts often ship both registrations. `moshi-kotlin-codegen-1.15.2.jar` contains `META-INF/services/javax.annotation.processing.Processor` (`…codegen.apt.JsonClassCodegenProcessor`), `META-INF/services/com.google.devtools.ksp.processing.SymbolProcessorProvider` (`…codegen.ksp.JsonClassSymbolProcessorProvider`) and `META-INF/gradle/incremental.annotation.processors` (`…JsonClassCodegenProcessor,ISOLATING`) [Local]. Android's guide says the same: most libraries "ship their annotation processor and KSP processor in the same artifact" [Docs: developer.android.com/build/migrate-to-ksp, updated 2026-11-12].

### 3.7 Incremental: Gradle's categories versus KSP Dependencies
- Gradle: "All annotation processors need to opt in to this feature, otherwise they will trigger a full recompilation… register your processor for incremental compilation using a file in the processor's META-INF directory. The format is one line per processor, with the fully qualified name of the processor class and its case-insensitive category separated by a comma" (example: `org.gradle.EntityProcessor,isolating`). Isolating processors "must provide exactly one originating element for each file generated with the Filer API. If zero or many originating elements are provided, Gradle will recompile all source files." For aggregating ones, "Gradle will always reprocess (but not recompile) all annotated files that the processor was registered for." Both kinds "must generate their files using the Filer API" and "can only read `CLASS` or `RUNTIME` retention annotations." Also: "Incremental annotation processing will be deactivated if a custom executable or javaHome is configured on the compile task." [Docs: Gradle Java plugin page]
- [Local, Gradle 9.8.2] With no descriptor, `--info` showed `Full recompilation is required because move.BoxProcessor is not incremental.` After adding `move.BoxProcessor,isolating`, the next build showed `Incremental compilation of 1 classes completed in 0.023 secs.`
- KSP: "KSP classifies generated outputs into two types: aggregating and isolating. Unlike Gradle annotation processing, KSP applies the categorization to individual outputs rather than entire processors." Aggregating outputs: "Any input change, including a file removal, triggers a rebuild of all aggregating outputs". Isolating outputs: "Multiple source files can be associated with a single output." Incremental processing "is enabled by default", and `ksp.incremental=false` turns it off [Docs: ksp-incremental]. This is a difference from Gradle, where an isolating file has exactly one originating element.

### 3.8 kapt: Java processors on Kotlin via stubs
- "It generates stub files from Kotlin source code and then runs the Java annotation processors on those stubs. This enables Java-based annotation processing in your Kotlin projects for libraries like MapStruct and Data Binding" [Docs: kotlinlang kapt, 2026-08-07]. On `correctErrorTypes`: "By default, kapt replaces every unknown type (including types for the generated classes) with `NonExistentClass`" [same page]. Android: "This stub generation is an expensive operation and has a significant impact on build speed", and "If a module has any kapt processors remaining, stubs are still generated in that module" [Docs: migrate-to-ksp]. Android also says "Kapt is now in maintenance mode". The kotlinlang kapt page no longer carries that sentence.
- [Local] The same Java `BoxProcessor` run by kapt 2.4.21 on `@Box data class KitchenBox(val label: String, val fragile: Boolean = false)` produced `build/tmp/kapt3/stubs/main/move/KitchenBox.java`. Every method body is replaced (`return null;`, `return false;`, `return 0;`), constructors become `super();`, nullability becomes `@org.jetbrains.annotations.NotNull()`, the default value of `fragile` is gone, `component1/2`, `copy`, `equals`, `hashCode` and `toString` are visible, and a `@kotlin.Metadata(…)` blob carries the Kotlin facts. kapt also wrote `error/NonExistentClass.java`, and the generated `KitchenBoxLabel.java` went to `build/generated/source/kapt/main/`. The warning named the wrapper: `…from annotation processor 'org.jetbrains.kotlin.kapt.base.ProcessorWrapper' less than -source '21'`.
- Mixing: "KSP processors are not able to resolve types generated by other Javac/KAPT processors" [Docs: dagger.dev/dev-guide/ksp].

---

## 4. The ecosystem, November 2026 (all checked 2026-11-19)

| Library | KSP artifact / status | What it generates | Source |
|---|---|---|---|
| **Room 2.x** | `androidx.room:room-compiler` 2.8.5 (2026-09-09). One artifact for javac, kapt and KSP. 2.7.0: "Kotlin Code Generation on KSP has been turned ON by default if processing is done via KSP. For KAPT or Java only projects, Room will still generate Java sources." and "Support for KSP2 is also added and is recommended" | Implementations of `@Database` and `@Dao` types (generated class names not checked) | developer.android.com/jetpack/androidx/releases/room (updated 2026-11-06) |
| **Room 3.0** | `androidx.room3:room3-compiler` 3.0.0 (2026-07-01), 3.0.3 (2026-09-09). **KSP only**: "Room 3.0 only generates Kotlin code and is only a Kotlin Symbol Processor (KSP)… configuration of annotation processor via KAPT or JavaAP is no longer possible in Room 3.0. Note that KSP is able to process Java sources" | Kotlin only. New package `androidx.room3` | …/releases/room3 (updated 2026-11-18) |
| **Dagger / Hilt** | `ksp("com.google.dagger:dagger-compiler:2.60.1")`, `ksp("com.google.dagger:hilt-compiler:2.60.1")` (2.60.1 on Central 2026-07-06). "Dagger's KSP support is stable as of Dagger 2.60+ and KSP 2.3.9+." SPI plugins must move to the new Dagger SPI. "KSP support for `androidx.hilt:hilt-compiler` is available in version 1.4.x" (1.4.0 is out) | Component implementations and factories (details not checked here) | dagger.dev/dev-guide/ksp, dagger.dev/hilt/gradle-setup |
| **Moshi codegen** | `ksp("com.squareup.moshi:moshi-kotlin-codegen:1.15.2")` (2024-12-05). Same jar serves kapt. [Local: works on KSP 2.3.14.] The master README shows `2.0.0-alpha.1` (changelog 2026-01-28), but Central's metadata lists 1.15.2 as newest [could not confirm 2.0.0-alpha.1 on Central] | `<Name>JsonAdapter` per `@JsonClass(generateAdapter = true)` class, plus a proguard file `META-INF/proguard/moshi-<fqcn>.pro` [Local] | github.com/square/moshi README |
| **Koin Annotations** | **KSP processor deprecated**: "`koin-ksp-compiler` is deprecated and will be removed in a future Koin version. The annotations are not deprecated… processed by the Koin Compiler Plugin." Keep KSP only if "your project can't move to Kotlin 2.3.20 or later yet". `koin-compiler-plugin` 1.2.3 on Central (2026-11-05). `koin-ksp-compiler` last updated 2025-11-26 | KSP: "generates visible source files… and uses generated extensions such as `AppModule().module` to start Koin". Plugin: "replaces `single<UserRepository>()` (or the `@Singleton` class) with the equivalent of `single { UserRepository(get(), get()) }`" during compilation | insert-koin.io/docs/setup/annotations-ksp (Koin 4.2 docs) |
| **kotlin-inject** | `ksp("me.tatarka.inject:kotlin-inject-compiler-ksp:0.9.0")` (Central 2026-01-07). KSP only. 0.9.0: "KSP1 support removed" | "An implementation of this component will be generated for you", plus a `.create()` extension | github.com/evant/kotlin-inject |
| **Micronaut** | `ksp("io.micronaut:micronaut-inject-kotlin")` (5.2.25 on Central 2026-11-17). Docs (5.2.x branch) still say "Micronaut framework 4 includes experimental support for KSP", and "KSP doesn't see the changes in the classes made by other compiler plugins, which breaks integration with the `allopen` plugin" (workaround: the `kotlin.allopen.annotations` KSP option) | Bean definitions and introspections [Unverified] | micronaut-core `src/main/docs/guide/languageSupport/kotlin/ksp.adoc` @5.2.x |
| **Arrow Optics** | `ksp("io.arrow-kt:arrow-optics-ksp-plugin:2.3.0")` still exists, but "Since version 2.3.0, we recommend using the compiler plug-in" (`id("io.arrow-kt.optics")`). With KSP: "you need to have a companion object declaration in each class, even if it's empty. This is due to limitations in KSP itself" | Lenses, prisms etc. as companion extensions (`Person.address`) | arrow-kt.io/learn/quickstart/setup, …/immutable-data/intro |
| **Lyricist** | `cafe.adriel.lyricist:lyricist-processor` 1.9.0 (2026-07-21). "Code generation with KSP" | `LocalStrings`, `rememberStrings()`, `ProvideStrings()`. Options via `ksp { arg("lyricist.packageName", …) }` | github.com/adrielcafe/lyricist |
| **Glide** | Separate artifact `com.github.bumptech.glide:ksp` (5.0.10 on Central 2026-11-16). Docs: "The KSP processor does not support Glide's deprecated generated API" | Glue for your `@GlideModule` classes [Unverified] | bumptech.github.io/glide/doc/download-setup.html |
| **Kotlin DataFrame** | KSP plugin **deprecated**: "Gradle and KSP plugins… are now deprecated. Their latest release is 1.0.0-Beta4 and will not have future releases." The compiler plugin replaces them | (was) extension properties for `@DataSchema` | kotlin.github.io/dataframe/migration-from-plugins.html (2026-11-02) |
| **kotlinx.serialization** | Not KSP. "Kotlin serialization consists of a compiler plugin, that generates visitor code for serializable classes" | A serializer nested in your class [Unverified: class name not checked] | github.com/Kotlin/kotlinx.serialization README |
| Others on kotlinlang's list | Kotshi, RxHttp, Ktorfit (2.7.5), Mockative (3.3.2), Kotest, Epoxy (5.2.1), Paris, DeeplinkDispatch, SealedX | | kotlinlang.org/docs/ksp-overview.html (2026-11-12) |

**Still on kapt or javac:** Android **Data Binding** ("KSP support for Data Binding is not planned" [Docs: migrate-to-ksp]). MapStruct (named by the kapt page as a kapt use case; I did not check for a KSP port [Unverified]). **Auto Factory / AutoValue** and any other plain javac processor (kotlinlang's table lists "Auto Factory: Not yet supported"; Dagger's page uses AutoFactory as the example of a kapt processor that blocks migration).

**Stale table warning:** kotlinlang's supported-libraries table, on a page dated 2026-11-12, still says "Dagger: Alpha" and "Hilt: In progress". dagger.dev says stable since 2.60. The same overview says "The latest KSP version, 2.3.12", while Central has 2.3.14 (2026-11-13). It requires KGP 2.3.20–2.4.x, Gradle 8.13+ and JDK 17+.

---

## 5. When KSP is the wrong tool

- **You need to change existing code.** KSP-based processors "can't examine expressions or statements, and they can't modify the source code" [Docs: ksp-overview]. The archived "Why KSP" page put it this way: "while kotlinc can examine expressions and statements and can even modify code, KSP cannot" (Kotlin 1.9-era docs, last modified 2022-09-06, w3cub mirror). Jobs that rewrite or add members to your own classes are compiler plugins:
  - kotlinx.serialization (generated serializer inside the class),
  - Compose ("The Compose compiler has been merged into the Kotlin repository since Kotlin 2.0.0" [Docs: compose-compiler-migration-guide]),
  - all-open ("makes classes and their members open at compile time without requiring the open keyword"),
  - no-arg ("generates a zero-argument constructor for classes with a specific annotation… annotated with `@Deprecated` at the HIDDEN level, so you can call it from Java but not from Kotlin") [Docs: kotlinlang plugin pages].
  Arrow's KSP variant needs a hand-written empty `companion object` because KSP cannot add one. Koin and DataFrame moved to compiler plugins. Micronaut's KSP path can't see what all-open did.
- **Run-time reflection is good enough.** Moshi itself offers both: "When you use Kotlin with Moshi you may use reflection, codegen, or both… Prefer codegen for better performance and to avoid the `kotlin-reflect` dependency; prefer reflection to convert both private and protected properties", and "the reflection adapter… depends on the `kotlin-reflect` library which is a 2.5 MiB .jar file" [Docs: Moshi README]. Other cases: a test helper that prints every property of an object, a small CLI that reads `@Option` annotations at startup, or a plugin registry with a handful of `ServiceLoader` entries. If the reflection runs once at startup on a few classes, a processor adds build time, a module and a test harness for no visible gain.
- **Build-time cost.** KSP2 "runs in Gradle daemon… Gradle daemon usually has a lower default heap limit. You may need to increase it… `org.gradle.jvmargs=-Xmx4096M -XX:MaxMetaspaceSize=1024m`" [Docs: google/ksp `docs/ksp2.md`]. A processor needs its own module, since it can't live in the module it processes (§7). Every consumer module gets a `kspKotlin` task.
- **IDE visibility.** [Local] The KSP Gradle plugin adds `app/build/generated/ksp/main/kotlin` and `…/java` to the Kotlin `main` source set (printed from `kotlin.sourceSets["main"].kotlin.srcDirs`). The old quickstart said: "Generated source files are registered automatically since KSP 1.8.0-1.0.9" (archived docs). The files exist only after `kspKotlin` runs, so the current quickstart warns: "Your IDE highlights `helloWorld()` as an undefined reference. This is expected: KSP generates the `helloWorld()` function when you build and run the project" [Docs]. Whether IntelliJ indexes `build/generated/ksp` without a Gradle sync and a build: **[Unverified]**, not testable here.
- **Kotlin Multiplatform.** "Since KSP 2.3.12, the catch-all `ksp(...)` configuration causes a build error in multiplatform projects" [Docs: ksp-multiplatform]. [Local, KSP 2.3.14] The error is `The 'ksp' configuration is deprecated in Kotlin Multiplatform projects. Please use target-specific configurations like 'kspJvm' instead.` With `add("kspJvm", project(":processor"))`, the task is `kspKotlinJvm`. It processed both `commonMain` and `jvmMain` classes into `build/generated/ksp/jvm/jvmMain/kotlin/`. The google/ksp README lists `ksp<Target>`, `ksp<Target>Test` and `kspCommonMainMetadata`, and notes the escape hatch `ksp.allow.all.target.configuration=true` ("with a warning instead of an error"). With only a JVM target, no metadata KSP task was created [Local]. Koin's docs name "a KSP configuration per Kotlin Multiplatform target" as a reason to prefer its compiler plugin.

---

## 6. Performance, build cache, configuration cache

- **"Up to 2x":** "Compared to KAPT, annotation processors that use KSP can run up to 2x faster" [Docs: google/ksp README]. Android: "KSP analyzes Kotlin code directly, which is up to 2x faster" [Docs: migrate-to-ksp, 2026-11-12]. Micronaut quotes "up to 2 times faster". None of these pages links a benchmark.
- **The one published benchmark** (historical, KSP1): "The stub generation costs roughly 1/3 of a full kotlinc analysis… For example, Glide… Almost all of the build overhead resides in the stub generation phase. Switching to KSP would immediately reduce the time spent in the compiler by 25%." And: "While the total Kotlin compilation time of the project is 21.55 seconds on our test device, it took 8.67 seconds for kapt to generate the code, and it took 1.15 seconds for our KSP implementation" (a simplified Glide on the Tachiyomi project) [Docs: archived "Why KSP", last modified 2022-09-06]. The current kotlinlang site redirects `ksp-why-ksp.html` to the overview, so cite this as historical.
- **Partial migration saves little:** "the majority of performance improvement will occur only when all usages of kapt are removed from the module" [Docs: migrate-to-ksp].
- **Tuning flags** [Docs: google/ksp README]: `ksp.experimental.psi.resolution` ("may improve build times, but expect crashes"; Dagger suggests trying it). `ksp.classloader.cache.processors` ("can substantially reduce build time in large multi-module projects", off by default because static state lives longer). `ksp.project.isolation.enabled` (Isolated Projects code paths).
- **Caches** [Local, Gradle 9.8.2 + KSP 2.3.14]: `--configuration-cache` printed `Configuration cache entry stored.` and then `Configuration cache entry reused.`, and the problems report held only a Kotlin deprecation warning. After `clean`, `--build-cache` gave `:app:kspKotlin FROM-CACHE` and `:app:compileKotlin FROM-CACHE`.
- **Incremental, measured:** after editing one of three files, `kspDirtySet.log` reported `Dirty / All: 33.33%` with correct originating files [Local].

---

## 7. Common mistakes and what the user sees

| Mistake | Symptom (exact where verified) |
|---|---|
| Forgot `META-INF/services/com.google.devtools.ksp.processing.SymbolProcessorProvider` | `e: [ksp] No providers found in processor classpath.` then `Execution failed for task ':app:kspKotlin'`. The cause line read `> com/google/devtools/ksp/impl/KotlinSymbolProcessing$ExitCode` [Local] |
| Typo in the services file | `> com.google.devtools.ksp.processing.SymbolProcessorProvider: Provider move.proc.LabelProvidr not found` [Local] |
| Java: forgot `META-INF/services/javax.annotation.processing.Processor`, or relied on class-path discovery on JDK 23+ | Silence, then `error: cannot find symbol` for the generated class [Local, JDK 25] |
| Processor in the module it processes (`ksp(project(":app"))` inside `:app`) | `Circular dependency between the following tasks: :app:classes … :app:kspKotlin … :app:jar …` [Local] |
| Version skew between `symbol-processing-api` and KSP runtime (lab: kctfork) | `java.lang.NoSuchMethodError: …CollectAnnotatedSymbolsVisitor.getEnableNewFeatures()`, `INTERNAL_ERROR` [Local] |
| `KSType ==` used when assignability was meant | No error, just wrong answers. For `open class Item; class Pan : Item()`: `Pan == Item` false, `Item.isAssignableFrom(Pan)` true. `Item? == Item` false. `Item.isAssignableFrom(Item?)` false. `List<Item> == Item` false [Local]. javac's `Types.isAssignable(t1, t2)` asks if t1 can be assigned to t2, while KSP's `a.isAssignableFrom(b)` asks if b can be assigned to a |
| `getSymbolsWithAnnotation("Box")` (simple name) | Silently empty: `simple=0 fqn=1` [Local]. Nothing is generated, then `Unresolved reference` downstream |
| Same file generated twice (e.g. one file per annotation, two annotated classes with the same name in different packages written to one package, or a second round writing it again) | KSP: `kotlin.io.FileAlreadyExistsException: /tmp/…/ksp/sources/kotlin/move/Same.kt`, `INTERNAL_ERROR` [Local]. javac: `error: javax.annotation.processing.FilerException: Attempt to recreate a file for type move.KitchenBoxLabel` [Local] |
| No or incomplete originating files (`Dependencies(false)` or no `addOriginatingKSFile`) | Clean builds pass, incremental builds fail: generated `BLabel.kt` is deleted and the build reports `Unresolved reference 'BLabel'` [Local, §1.5]. With `Dependencies.ALL_FILES`, every change reprocesses everything ("essentially disables incremental processing") |
| Aggregating output marked isolating (e.g. one `Inventory.kt` listing all `@Box` classes, written with `aggregating = false`) | A newly added `@Box` file doesn't show up in the index until a clean build, because only aggregating outputs are rebuilt "by a new source file". [Inferred from the KSP docs; not run here] |
| Deferring forever (returning symbols that never validate) | No error. Processing stops when a round writes nothing, `finish()` runs, exit `OK`, nothing generated [Local + Source]. Downstream: `Unresolved reference`. Log a `logger.error` in `finish()` for symbols that are still deferred, with the symbol as location |
| Converting an error type (a type generated later, or a typo) | `IllegalArgumentException: Error type '<ERROR TYPE: GeneratedLater>' is not resolvable in the current round of processing.` [Local]. Check `isError` or `validate()` first and defer |
| Resolving too eagerly (calling `resolve()` on every reference, in `validate()` and filters) | Slower builds ("one of the most expensive operations"). Every resolution adds a traced file dependency, so incremental runs reprocess more files. Inspect `KSTypeReference.element` / `referencedName()` first [Docs: ksp-kotlin-model] |
| Reading a `KClass` annotation argument through `getAnnotationsByType(Room::class)` | `room.kind` (enum) works, but `room.contents` throws `com.google.devtools.ksp.KSTypeNotPresentException: java.lang.ClassNotFoundException: move.Pan`. The exception's `ksType` gives the `KSType` (`Pan`) [Local]. Read `KSAnnotation.arguments` instead |
| Assuming enum annotation arguments are `KSType` | In KSP 2.3.14, `arguments` gives `KClass` values as `KSType` and **enum values (Kotlin and Java, e.g. `TimeUnit.HOURS`) as `KSClassDeclaration` with `classKind == ENUM_ENTRY`** [Local] |
| Java: no `@SupportedSourceVersion` | `warning: No SupportedSourceVersion annotation found on move.BoxProcessor, returning RELEASE_6.` + `…less than -source '25'` [Local] |
| Java: forgot `@SupportedOptions` | `warning: The following options were not recognized by any processor: '[dup]'` [Local] |
| KMP: plain `ksp(...)` | `The 'ksp' configuration is deprecated in Kotlin Multiplatform projects. Please use target-specific configurations like 'kspJvm' instead.` (build fails) [Local] |
| Gradle Java: no `incremental.annotation.processors` descriptor | `--info`: `Full recompilation is required because move.BoxProcessor is not incremental.` [Local] |

---

## Lab ideas

Each lab is one annotation, one small processor and one or two kctfork tests. Each has a Java twin: a javac processor plus a compile-testing test.

1. **`@Box` → `KitchenBoxLabel`** (the probe above). Generates `object <Name>Label { fun describe(box: <Name>): String }`. The test loads it through `result.classLoader` and asserts `"KitchenBox: Plates, true"`. Drills: provider, services file, `getSymbolsWithAnnotation` with a qualified name, `toClassName()`, `FileSpec`/`TypeSpec`/`FunSpec`, `%S` vs `%L`.
2. **`@Box` misuse.** Same processor rejects interfaces and objects with `logger.error(msg, decl)`. The test asserts `COMPILATION_ERROR` and `messages` contains `"Wardrobe.kt:4: @Box can only be applied to classes"`. Drills: error location, exit codes, declaration-line versus annotation-line.
3. **`@Room(kind = RoomKind.KITCHEN, contents = Pan::class)` → `KitchenPlanRoute`.** Reads annotation arguments and generates `val room = RoomKind.KITCHEN; val firstItem = ::Pan`. Tests cover one Kotlin enum and one Java enum (`TimeUnit`). Drills: enum argument = `KSClassDeclaration`/`ENUM_ENTRY`, `KClass` = `KSType`, why `getAnnotationsByType` throws `KSTypeNotPresentException`.
4. **`@Inventory` aggregation.** Generates one `MoveInventory.kt` listing every `@Box` class (`val all: List<KClass<*>>`). The test compiles three boxes and checks the list. A TestKit test adds a fourth file incrementally and sees it appear. Drills: aggregating versus isolating, `Dependencies(aggregating = true, *files)`.
5. **Copy-with builder for a recipe card.** `@Builder data class RecipeCard(val title: String, val servings: Int, val notes: String?)` → `RecipeCardBuilder` with nullable fields and `build()`. Tests a missing required field and that `notes` stays nullable. Drills: `toTypeName()`, `copy(nullable = true)`, `PropertySpec.mutable()`, `ParameterSpec`.
6. **Generic shelf.** `@Shelf class Shelf<T : Comparable<T>>(val items: List<T>)` → `fun <T : Comparable<T>> Shelf<T>.sorted(): List<T>`. The test checks the generated signature text and calls it. Drills: `toTypeParameterResolver`, `toTypeVariableName`, `ParameterizedTypeName`, 2.4.0's `EMPTY` behaviour.
7. **To-do priority enum map.** `@TodoList enum class Chores { DISHES, LAUNDRY }` with `@Priority(3)` on entries → `val Chores.priority: Int` via a `when`. Drills: enum entries as `KSClassDeclaration`, `beginControlFlow`/`%T.%N`, extension properties.
8. **Name-clash drill.** Two `Box` types (`move.Box`, `storage.Box`) used in one generated `Packer.kt`. A golden-file test asserts the `import … as MoveBox` aliases. Drills: why string templates fail, `%T` imports, golden files.
9. **Deferral.** `@LabelFor(KitchenBoxLabel::class)` refers to a class that lab 1's processor generates. Run both processors in one compilation. The second must defer until round 2. Variant: break it so it defers forever, and add a `finish()` check that logs an error. Drills: `validate()`/`isError`, multi-round, the missing built-in error.
10. **Stale-output hunt (TestKit).** A tiny Gradle build where the processor forgets `addOriginatingKSFile`. Build, edit `A.kt`, build again, and watch `Unresolved reference 'BLabel'`. Fix it and repeat. Drills: incremental processing, `ksp.incremental.log`, why kctfork can't catch this.
11. **Options.** `ksp { arg("label.prefix", "Move: ") }` changes the generated text. The test sets `kspProcessorOptions["label.prefix"]`. The Java twin uses `-Alabel.prefix=` and `@SupportedOptions`. Drills: `environment.options` versus `getOptions()`, javac's unrecognized-option warning.
12. **Java twin of lab 1 with discovery.** Build the Java `BoxProcessor` jar and run `javac` on JDK 21 and 25 with `-cp` only, then with `--processor-path`. Drills: services file, JDK 23 discovery change, `@SupportedSourceVersion` warnings, `FilerException` on duplicates.

---

## Notes for the lesson writer

1. **kctfork:** the group is `dev.zacsweers.kctfork` but the package is `com.tschuchort.compiletesting`. It is KSP2-only since 0.10.0. Write `useKsp2()` + `symbolProcessorProviders += …` or `configureKsp { … }`. **Never write `configureKsp(useKsp2 = true)`**, it doesn't compile on 0.14.0. Opt in to `ExperimentalCompilerApi`. Align every `com.google.devtools.ksp` artifact to one version, or tests fail with `NoSuchMethodError`.
2. kctfork's README is stale for 0.14.0 (`compilerPlugins`, providers set before KSP is enabled). Don't copy it.
3. kctfork cannot test incremental behaviour. It wipes its KSP caches every run. Originating-file bugs need Gradle.
4. **`KSPLogger.error` gives `COMPILATION_ERROR`, a thrown exception gives `INTERNAL_ERROR`.** Both KSP2 and javac report the declaration's line (the `class`/`interface` line), not the annotation's line.
5. **KSP 2.3.14 does not report never-processed deferred symbols.** kotlinlang says it does. Don't repeat that claim without saying it is what the docs say, not what 2.3.14 does.
6. **`Types.isAssignable(t1, t2)` and `KSType.isAssignableFrom(other)` read in opposite directions.** `isSameType` maps to `KSType.equals`, and nullability is part of equality (`Item? != Item`).
7. Enum annotation arguments arrive as `KSClassDeclaration` (`ENUM_ENTRY`) in KSP2, and `KClass` arguments as `KSType`. Older articles (KSP1) say enums arrive as `KSType`.
8. **KotlinPoet 2.x:** spaces don't wrap. `·` is now an ordinary space and `♢` is the wrapping space. In 2.4.0, `toTypeName()` with the default resolver no longer throws on type parameters. Square's JavaPoet is deprecated, so for the Java twin use Palantir's `com.palantir.javapoet` (fields became getters, e.g. `javaFile.packageName()`).
9. `FileSpec.writeTo(codeGenerator, aggregating)` has no default for `aggregating`. Originating files are collected only from top-level specs. kotlinpoet-ksp does not bring the KSP API with it.
10. **JDK 23+ javac ignores processors on the class path** unless `-proc:full`, `-processor` or `--processor-path` is given. AutoService's README sentence about "javac's classpath" is outdated. Gradle's `annotationProcessor` path is unaffected.
11. Gradle's isolating/aggregating is **per processor**, and an isolating file needs **exactly one** originating element. KSP's is **per output**, and an isolating output may have several source files.
12. **Version facts drift:** kotlinlang's KSP pages say 2.3.12 is latest and call Dagger "Alpha" and Hilt "In progress". Central has 2.3.14, and dagger.dev says stable since 2.60 (KSP 2.3.9+). The quickstart mixes plugin 2.3.12 with API 2.3.6, but the labs should use one version (2.3.14) everywhere. kotlinlang's `ksp-why-ksp`, `ksp-faq` and `ksp-examples` now redirect to the overview, and `ksp-additional-details` to `ksp-kotlin-model`.
13. **"Up to 2x faster" is a vendor claim with no linked benchmark.** The only numbers (8.67 s kapt vs 1.15 s KSP for Glide-like codegen, 25% less compiler time) come from the 2022 KSP1 doc. Present them as such.
14. **Room 3 is KSP-only and Kotlin-only.** Room 2.x still supports kapt and javac. Koin Annotations, Arrow Optics and Kotlin DataFrame now prefer **compiler plugins**. Don't present KSP as the only direction the ecosystem is moving.
15. KMP: plain `ksp(...)` is a build **error** since KSP 2.3.12. Use `add("kspJvm", …)` and friends. `kspJvm` also processes `commonMain` sources for that target.
16. `KSNode.validate()` without `apiFeatures` is deprecated in 2.3.14. Lab processors that call it print a compile warning. The sibling file covers the replacement.

---

## Verified URLs (fetched 2026-11-19)

- KotlinPoet docs sources @2.4.0: `https://raw.githubusercontent.com/square/kotlinpoet/2.4.0/docs/{interop-ksp,index,t-for-types,n-for-names,s-for-strings,l-for-literals,p-for-string-templates,code-block-format-strings,code-control-flow,changelog}.md` (the rendered site square.github.io/kotlinpoet answered HTTP 200 to curl)
- Maven Central sources jars: `com/squareup/kotlinpoet-ksp/2.4.0`, `com/squareup/kotlinpoet-jvm/2.4.0`, `dev/zacsweers/kctfork/{core,ksp}/0.14.0` (+ `ksp/0.9.0`, `ksp/0.10.0`), `com/google/testing/compile/compile-testing/0.24.0`, `com/palantir/javapoet/javapoet/0.23.0`
- kctfork: `https://raw.githubusercontent.com/ZacSweers/kotlin-compile-testing/main/README.md`, `…/0.14.0/CHANGELOG.md`, `…/0.14.0/ksp/src/test/kotlin/com/tschuchort/compiletesting/KspTest.kt`
- google/ksp @2.3.14: `kotlin-analysis-api/src/main/kotlin/com/google/devtools/ksp/impl/KotlinSymbolProcessing.kt`, `api/src/main/kotlin/com/google/devtools/ksp/processing/CodeGenerator.kt`. @main: `README.md`, `docs/ksp2.md`
- kotlinlang.org/docs: `ksp-overview.html` (2026-11-12), `ksp-quickstart.html`, `ksp-incremental.html`, `ksp-multi-round.html`, `ksp-multiplatform.html`, `ksp-kapt-migration.html` (all 2026-11-17), `ksp-reference.html` (2026-08-12), `ksp-kotlin-model.html`, `kapt.html` (2026-08-07), `all-open-plugin.html`, `no-arg-plugin.html`, `compose-compiler-migration-guide.html`. Archived: `https://docs.w3cub.com/kotlin~1.9/docs/ksp-why-ksp`, `…/ksp-quickstart`
- Oracle Java SE 25 API: `https://docs.oracle.com/en/java/javase/25/docs/api/java.compiler/javax/annotation/processing/{Processor,AbstractProcessor,ProcessingEnvironment,Filer,Messager,RoundEnvironment,SupportedAnnotationTypes}.html`, `…/javax/lang/model/{type/TypeMirror,element/Element,element/TypeElement,element/VariableElement,element/ExecutableElement,util/Types}.html`. JDK 23 notes: `https://www.oracle.com/java/technologies/javase/23-relnote-issues.html`
- Gradle (docs version 9.9.2): `https://docs.gradle.org/current/userguide/java_plugin.html`, `…/test_kit.html`, `…/upgrading_version_4.html`
- Libraries: `https://dagger.dev/dev-guide/ksp`, `https://dagger.dev/hilt/gradle-setup`, `https://developer.android.com/build/migrate-to-ksp`, `https://developer.android.com/jetpack/androidx/releases/room`, `…/room3`, `https://developer.android.com/training/dependency-injection/hilt-android`, `https://raw.githubusercontent.com/square/moshi/master/{README,CHANGELOG}.md`, `https://insert-koin.io/docs/setup/annotations-ksp`, `https://insert-koin.io/docs/intro/koin-compiler-plugin`, `https://raw.githubusercontent.com/evant/kotlin-inject/main/{README,CHANGELOG}.md`, `https://raw.githubusercontent.com/micronaut-projects/micronaut-core/5.2.x/src/main/docs/guide/languageSupport/kotlin/{ksp,kaptOrKsp}.adoc`, `https://arrow-kt.io/learn/quickstart/setup/`, `https://arrow-kt.io/learn/immutable-data/intro/`, `https://raw.githubusercontent.com/adrielcafe/lyricist/main/README.md`, `https://bumptech.github.io/glide/doc/download-setup.html`, `https://kotlin.github.io/dataframe/migration-from-plugins.html`, `https://raw.githubusercontent.com/Kotlin/kotlinx.serialization/master/README.md`, `https://raw.githubusercontent.com/google/auto/main/service/README.md`, `https://raw.githubusercontent.com/ZacSweers/auto-service-ksp/main/README.md`, `https://raw.githubusercontent.com/square/javapoet/master/README.md`, `https://raw.githubusercontent.com/palantir/javapoet/develop/README.md`, `https://raw.githubusercontent.com/google/compile-testing/master/README.md`
