import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")

INTRO = """By the end of this track you can write a KSP processor for Kotlin code from an empty file and know why each line is there. You'll find the classes that carry an annotation, refuse the ones you can't handle with a message on the exact file and line, read their declarations and types, write new code with KotlinPoet, survive several rounds and incremental builds, test the processor the way a library author does, and decide when KSP is the wrong tool. KSP, Kotlin Symbol Processing, is Kotlin's own way to do what Java's annotation processors have done since Java 6: read your code during the build and write new code next to it.

One picture runs through all nine lessons: a family moving house. Your source files are sealed boxes. The label on top lists what's inside, the declarations, and the packing stays sealed. An annotation is a sticky note on a box. A processor is a helper with a clipboard, the Resolver, who reads labels, never opens or repacks a box, and writes new cards and lists that travel with the move. The running example is MoveMate, a small app that helps the family, with the same four classes everywhere: `Box`, `Lamp`, `Bookshelf` and `Plant`, and the same card, `Lamp: name=desk lamp, bulbs=1, shade=null`. You need basic Kotlin and Java, and nothing else: every term is defined where it first appears.

The versions are Kotlin 2.4.21, KSP 2.3.14 (KSP2), KotlinPoet and kotlinpoet-ksp 2.4.0, kctfork 0.14.0 for the in-memory tests, Gradle 9.8.2, JUnit 6.1.3 and AssertJ 3.27.7. Install JDK 25; the labs compile with release 21. The outputs quoted in the lessons were copied from real runs of these versions.

The labs live in `labs/ksp`. You write each lesson's processor in `src/main/kotlin/workbench/ksp/lNN`, and every lab follows the same five moves: Find, Check, Read, Write, Prove. From `labs/`, run your lab's tests with `./gradlew :ksp:test --tests 'workbench.ksp.lNN.*'`, and the reference answers with `./gradlew :ksp:solutionTest --tests 'workbench.ksp.lNN.*'`. Demos run with `./gradlew :ksp:demo -Pmain=<class>`, using the reference processors until you add `-Pmine=lNN`. The real build is `labs/ksp/app`, one source set per lesson: `./gradlew :ksp:app:kspLNNKotlin -Pmine=lNN` runs your processor in it, its output lands in `labs/ksp/app/build/generated/ksp/lNN/`, and `-Pksp.incremental.log=true` writes KSP's incremental logs to `labs/ksp/app/build/kspCaches/lNN/logs/`. An unfinished processor only prints a warning, so the real build always runs."""

CHEAT = """## The one idea

A processor runs during the build, before the Kotlin compiler. It reads declarations (names, types, annotations, signatures, never bodies), and it adds new files that are compiled with yours. It never changes a file you wrote. Everything else in the track is how to do those two things correctly, quickly and testably.

## Picture it: a family moving house

| Mechanism | Picture it | In the code | Where the picture breaks |
|---|---|---|---|
| Source file, declarations (lessons 1, 3) | a sealed box, and the label on top | `KSFile`, `KSClassDeclaration`, `KSPropertyDeclaration`, `KSFunctionDeclaration` | the label also lists named things packed inside; only the how (expressions, default values) stays sealed |
| Annotation (1, 2) | a sticky note: "make a card for this one" | `@Inventory`, found by its full name | notes go on label lines too (properties, parameters), and carry values with defaults |
| Processor and provider (2) | the helper, and the moving company that sends him | `SymbolProcessor`, created once by `SymbolProcessorProvider` | KSP finds the company through a services file, or not at all |
| Resolver (2, 3) | the clipboard: "every box with this note" | `resolver.getSymbolsWithAnnotation(fqName)` | a fresh clipboard each pass; an old one is no good |
| Generated file (1, 2, 4) | a new card or list that travels with the move | `codeGenerator.createNewFile(...)`, or KotlinPoet's `writeTo` | the cards are boxes too: next pass, every helper reads them |
| Logger message (2, 5) | the helper's note: "box 7 has a note but no label" | `logger.error(message, symbol)` | a thrown exception is the helper dropping everything: no note, no `onError()` |
| KotlinPoet (4) | a label printer instead of handwriting | `FileSpec`, `TypeSpec`, `%T %N %S %L` | it prints declarations; bodies are still format strings |
| Rounds (6) | another walk through the house for the new cards | `process()` once per round | a walk happens only if the last one wrote something |
| Deferral (5, 6) | a box set aside: its label mentions something not packed yet | return it from `process()`; `validate(apiFeatures = apiFeatures)` | the pile is shared by every helper, and in 2.3.14 a box left there at the end gets no word at all |
| Isolating output (7) | one box's own card, redone when that box is repacked | `Dependencies(aggregating = false, file)` | KSP knows a box was repacked only from what you declared |
| Aggregating output (7) | the master list on the fridge | `Dependencies(aggregating = true, *files)` | the whole list is rewritten from every box, never patched |
| Processor options (7) | the job sheet the company hands the helper | `ksp { arg(k, v) }`, `environment.options` | one sheet for every helper in the module |
| Testing (8) | a practice pack in an empty room | kctfork, four checks | the room is emptied after each pack, so it never sees an incremental build |
| Reflection (1, 9) | unpacking and checking boxes at the new house, every time | `javaClass.declaredFields` | it costs a fifth of a microsecond, not an afternoon |
| Compiler plugin (9) | the mover who repacks boxes | all-open, no-arg, kotlinx.serialization | more power, and the class you read is no longer the class that runs |
| kapt (9) | a helper who reads only Java, so every label is copied out in Java first | `kapt(...)`, Java stubs | the copies lose words, such as default values |
| Multiplatform (9) | moving into several houses on one day | `kspJvm`, `kspJs`, `kspCommonMainMetadata` | a shared box gets a card in every house |

## The five moves

| Move | KSP | Lesson |
|---|---|---|
| 1. Find | `resolver.getSymbolsWithAnnotation("workbench.ksp.annotations.Inventory")`: the full name; a short name finds nothing | 2 |
| 2. Check | `if (symbol !is KSClassDeclaration or classKind != ClassKind.CLASS) logger.error("...", symbol)`; check every symbol, report every problem | 2, 5 |
| 3. Read | `primaryConstructor?.parameters`, `type.resolve()`, `isMarkedNullable`, `annotations` and their `arguments` | 3 |
| 4. Write | KotlinPoet `FileSpec`, then `writeTo(codeGenerator, Dependencies(...))` with the right files and category | 4, 7 |
| 5. Prove | kctfork tests (exit code, text, messages, a call), then the real build | 8 |

## The KSP API on one page

```kotlin
class CardProcessorProvider : SymbolProcessorProvider {                    // listed in the services file
    override fun create(environment: SymbolProcessorEnvironment): SymbolProcessor =
        CardProcessor(environment.codeGenerator, environment.logger, environment.options)
}

class CardProcessor(
    private val codeGenerator: CodeGenerator,
    private val logger: KSPLogger,
    private val options: Map<String, String>,                              // ksp { arg("k", "v") }
) : SymbolProcessor {
    override val apiFeatures = buildApiFeatures { enableBackingFields = true; enableContextParameters = true }

    override fun process(resolver: Resolver): List<KSAnnotated> {          // once per round
        val (ready, later) = resolver.getSymbolsWithAnnotation("workbench.ksp.annotations.Inventory")
            .partition { it.validate(apiFeatures = apiFeatures) }
        for (symbol in ready) {
            if (symbol !is KSClassDeclaration || symbol.classKind != ClassKind.CLASS) {
                logger.error("@Inventory goes on a class, but ...", symbol)  // file and declaration line
                continue
            }
            cardFile(symbol).writeTo(codeGenerator, Dependencies(aggregating = false, symbol.containingFile!!))
        }
        return later                                                       // deferred to the next round
    }

    override fun finish() { /* after the last round: report anything still deferred */ }
}
```

- Services file: `src/main/resources/META-INF/services/com.google.devtools.ksp.processing.SymbolProcessorProvider`, one provider class per line. Missing: `e: [ksp] No providers found in processor classpath.`
- Symbols: `KSFile`, `KSClassDeclaration` (`classKind`, `modifiers`, `primaryConstructor`, `getDeclaredProperties()`), `KSPropertyDeclaration`, `KSFunctionDeclaration`, `KSValueParameter` (`name`, `type`, `isVal`, `hasDefault`). `origin` is `KOTLIN`, `JAVA`, `KOTLIN_LIB`, `JAVA_LIB` or `SYNTHETIC`.
- Types: a `KSTypeReference` is the type as written; `resolve()` gives the `KSType` (`declaration`, `arguments`, `isMarkedNullable`, `isError`). Resolving is expensive: once per reference. A Java type can be a platform type, `(String..String?)`.
- Annotation arguments: `annotation.arguments`, by name. A `String` or `Boolean` arrives as itself, a class as a `KSType`, an enum value as the entry's `KSClassDeclaration`. Unwritten arguments are there with their defaults, and `isDefault()` is true.
- Visitors: `KSVisitorVoid(apiFeatures)`, not the deprecated `KSVisitorVoid()`. The same goes for `validate(apiFeatures = apiFeatures)`.
- KotlinPoet: `%T` a type (imported), `%N` a name (escaped), `%S` a string (quoted, `$` escaped), `%L` a literal (as is), `%M` a member (imported), `%P` a string template. kotlinpoet-ksp: `toClassName()`, `toTypeName()`, `copy(nullable = true)`, `addOriginatingKSFile(file)`, `writeTo(codeGenerator, aggregating = ...)`.
- Rounds: a round runs only if the last one wrote a file; `process()` returns what to defer; `finish()` runs once at the end, `onError()` after a `logger.error`. A file written twice: `kotlin.io.FileAlreadyExistsException`.
- Dependencies: `Dependencies(false, file)` for an output from one file, `Dependencies(true, *files)` for one that any file can change, `Dependencies.ALL_FILES` to turn incremental processing off for it.

## KSP and javac's annotation processing, side by side

| KSP | javac (`javax.annotation.processing`) |
|---|---|
| `SymbolProcessorProvider.create(environment)` | a public no-argument constructor, then `init(ProcessingEnvironment)` |
| `process(resolver): List<KSAnnotated>`: returns symbols to defer | `process(annotations, roundEnv): boolean`: returns whether it claims them |
| every processor sees every symbol | `@SupportedAnnotationTypes`, and claiming |
| `resolver.getSymbolsWithAnnotation(fqName)` | `roundEnv.getElementsAnnotatedWith(type)` |
| `KSClassDeclaration`, `KSPropertyDeclaration`, `KSFunctionDeclaration`, `KSValueParameter` | `TypeElement`, `VariableElement`, `ExecutableElement` |
| `classKind == ClassKind.CLASS` | `getKind() == ElementKind.CLASS` |
| `KSTypeReference.resolve()` gives a `KSType`; `a.isAssignableFrom(b)` | `TypeMirror`, already resolved; `types.isAssignable(b, a)`, the other way round |
| `KSAnnotation.arguments` | `element.getAnnotation(Room.class)` or `AnnotationMirror` |
| `codeGenerator.createNewFile(Dependencies(...), pkg, name, ext)` | `filer.createSourceFile(name, originatingElements...)`, `createResource(...)` |
| `logger.error(message, symbol)` | `messager.printMessage(Diagnostic.Kind.ERROR, message, element)` |
| `environment.options`, from `ksp { arg(k, v) }` | `processingEnv.getOptions()`, from `-Ak=v`, declared in `@SupportedOptions` |
| rounds end when one writes nothing; `finish()` | an extra last round with `processingOver()` true |
| isolating or aggregating per output, in `Dependencies` | isolating or aggregating per processor, in `META-INF/gradle/incremental.annotation.processors` |
| `META-INF/services/com.google.devtools.ksp.processing.SymbolProcessorProvider` | `META-INF/services/javax.annotation.processing.Processor` |
| KotlinPoet | JavaPoet |
| kctfork | Google's compile-testing |

## What the build prints

- A processor error: `e: [ksp] /abs/path/Shape.kt:6: @Builder goes on a class, but Shape is an interface`: an absolute path, the declaration's line (not the annotation's), no column. The task then fails with `KSP failed with exit code: PROCESSING_ERROR`.
- Follow-on errors such as `e: [ksp] MovingDay.kt:14: Unresolved reference 'MovingDayList'.` come after a failed run: fix the first error.
- A compiler error in generated or user code: `e: file:///.../Use.kt:5:16 ...`, with a column.
- `logger.warn` shows at Gradle's default level; `logger.info` only with `--info`.
- Incremental logs, with `-Pksp.incremental.log=true`: `build/kspCaches/<source set>/logs/kspDirtySet.log` (the `Dirty:` files and `Dirty / All`) and `kspSourceToOutputs.log` (each source's outputs, and the virtual `AnyChanges` key of aggregating outputs).

## Where KSP 2.3.14 disagrees with its own docs

- A symbol still deferred when processing ends gets no error and no warning: check in `finish()` and report it yourself.
- `onError()` runs after `logger.error`, not after a thrown exception; `logger.exception(e)` prints `e: [ksp]` and doesn't fail the build.
- The quickstart's `KSVisitorVoid()` and `validate()` are deprecated since 2.3.12: use `apiFeatures` everywhere.
- KSP1 is gone: `ksp.useKSP2=false` fails the build. KSP2 runs in the Gradle daemon, and its version isn't tied to Kotlin's.
- "Up to 2x faster than kapt" is a 2021 Room benchmark, not a law.
- A lambda `CommandLineArgumentProvider` isn't a tracked task input, and option values from one can't contain spaces.

## Testing a processor: the four checks

| Check | Catches | Bench call |
|---|---|---|
| 1. exit code | a crash (`INTERNAL_ERROR`) or a reported error (`COMPILATION_ERROR`) | `run.exitCode` |
| 2. generated text | any change, through a golden file (`UPDATE_GOLDEN=true` to rewrite on purpose) | `checkGolden(run.generated(path), file)` |
| 3. messages | the wrong text or the wrong line | `run.errors` as `Message(severity, file, line, text)` |
| 4. call the code | code that compiles and is still wrong | `run.newInstance(...)`, `run.call(...)` |

In-memory tests never see incremental builds, the services file or option wiring: those need a real build or Gradle TestKit.

## Choosing the tool

| The job | Tool |
|---|---|
| must change a class you wrote (remove `final`, add a constructor, a serializer inside it) | a compiler plugin |
| runs a few times, on a few classes, or on classes that arrive while the program runs | reflection |
| new code next to your classes, repeated work, mistakes that should stop the build | KSP |
| only a Java processor exists | kapt, until a KSP version does; one kapt processor keeps stubs in its module |"""

RECAP = [
 "An annotation processor runs during the build, reads declarations and writes new source files that compile with yours. KSP is Kotlin's own, running as a Gradle task (`kspKotlin`) before the compiler; Java has had javac processors since Java 6.",
 "KSP's two limits shape everything: it never sees bodies or expressions, and it only adds files. Anything that must change a class you wrote is a compiler plugin's job.",
 "A processor is a provider, a processor and a services file. Find symbols by the annotation's full name, check each one and report problems with `logger.error(message, symbol)` on the declaration's line, then read and write.",
 "Read types through `KSTypeReference.resolve()` once, keep every `?` and type argument, and write code with KotlinPoet's `%T %N %S %L` and kotlinpoet-ksp's `toTypeName()`, never with string templates.",
 "`process()` runs once per round and returns what to defer; rounds go on while they write files, and in KSP 2.3.14 a symbol deferred to the end is dropped silently, so check in `finish()`.",
 "Every output names its source files in `Dependencies`: isolating for one class's file, aggregating for a list of many. A wrong choice is silent until an incremental build, where a list shrinks or vanishes.",
 "Test like a library author: compile in memory with kctfork, then check the exit code, the generated text, the messages by file and line, and a call into the generated code. Real builds test the wiring.",
 "Choose with evidence: reflection for a few calls on a few classes, KSP for repeated work and build-time checks, a compiler plugin to change classes, kapt only for Java-only processors, and per-target configurations in multiplatform modules."
]

QUIZ = [
 {"q": "Which of these can a KSP processor do?",
  "options": ["Read the expression inside `fun totalWeight(): Int`", "Add a member function to an existing class", "Write a new file with an extension function for that class", "Change the default value of a constructor parameter"],
  "answer": 2, "why": "KSP reads declarations and adds new files; it never sees bodies or default values, and it never changes existing code. An extension function in a new file is how a processor gives a class new behaviour. Adding a member needs a compiler plugin."},
 {"q": "A processor calls `resolver.getSymbolsWithAnnotation(\"Inventory\")`, and the project has `@Inventory` classes. What does it get?",
  "options": ["Every class with an annotation named Inventory", "Nothing: the call needs the fully qualified name", "An error that the name is ambiguous", "Only the classes in the default package"],
  "answer": 1, "why": "The lookup takes the annotation's fully qualified name, here `workbench.ksp.annotations.Inventory`. A short name silently finds nothing, and the trouble shows up later as `Unresolved reference` errors for cards that were never written."},
 {"q": "A property is declared `val shade: String?`. Which call tells the processor it is nullable?",
  "options": ["`property.type.toString()`", "`property.type.resolve().isMarkedNullable`", "`property.hasDefault`", "`property.isMutable`"],
  "answer": 1, "why": "`type` is a `KSTypeReference`, the type as written; `resolve()` gives the `KSType`, which knows its nullability and arguments. Resolving costs time, so do it once per reference. `toString()` is a display form, not reliable code."},
 {"q": "In a KotlinPoet format string, which placeholder writes a type and adds its import?",
  "options": ["`%S`", "`%L`", "`%T`", "`%N`"],
  "answer": 2, "why": "`%T` emits a type and imports it if it can. `%N` is for names and escapes keywords, `%S` quotes and escapes a string, and `%L` writes a literal as it is."},
 {"q": "A processor finds an interface where it needs a class. What should it do?",
  "options": ["`throw IllegalStateException(\"not a class\")`", "`logger.error(\"@Builder goes on a class, but Shape is an interface\", symbol)` and carry on with the other symbols", "`logger.exception(e)`, so the build fails", "Skip the symbol without a word"],
  "answer": 1, "why": "`logger.error` on the symbol points at the user's file and the declaration's line, lets the processor report every problem in one build, and fails the build at the end. A thrown exception points into the processor, skips `onError()` in KSP 2.3.14, and stops everything. `logger.exception` doesn't fail the build at all."},
 {"q": "A processor returns the same symbol from `process()` in every round, because its type never becomes valid. What does KSP 2.3.14 do at the end?",
  "options": ["Logs an error for the symbol, as the docs say", "Logs a warning", "Drops it silently, calls `finish()`, and the build can pass", "Keeps running rounds until a timeout"],
  "answer": 2, "why": "Processing stops when a round writes no file, and 2.3.14 reports nothing about symbols still deferred, although the multi-round docs promise an error. A careful processor checks in `finish()` and reports each leftover with `logger.error` on the symbol."},
 {"q": "A processor writes one `Index.kt` naming every `@Indexed` class, with `Dependencies(aggregating = false, *files)`. What happens after a new `@Indexed` class is added in a new file?",
  "options": ["The index lists every class, the new one too", "The index is rewritten with only the new class, and the build passes", "KSP fails with a Dependencies error", "The index keeps the old classes until a clean build adds the new one"],
  "answer": 1, "why": "A new file is tied to no output, so only that file is dirty, and the processor sees one class. Only an aggregating output, `Dependencies(aggregating = true, ...)`, is redone for new files. Clean builds and in-memory tests never show the mistake."},
 {"q": "A builder test checks that the compile succeeded and that the text contains `class LampBuilder`. The processor drops the `?` from `shade: String?`. Which check would catch it?",
  "options": ["Checking the exit code again with `--info`", "Calling `shade(null)` on the generated builder through the class loader", "Checking that the text contains `fun build()`", "Running the test twice"],
  "answer": 1, "why": "The broken builder is valid code, so it compiles and contains its class and `build()`. Calling the code with `null` fails with `NullPointerException: Parameter specified as non-null is null`. A golden file would catch it too, by the changed line."},
 {"q": "A team wants each `@Serializable` class to contain its own generated serializer. Which tool does that?",
  "options": ["A KSP processor", "A compiler plugin, kotlinx.serialization", "kapt", "Reflection at start-up"],
  "answer": 1, "why": "The serializer goes inside the class, with a `serializer()` function on its companion, which changes a class you wrote. Only a compiler plugin can do that. A KSP processor could write a separate serializer class next to it, which is a different design."},
 {"q": "A module runs Moshi's codegen with KSP and one Java-only processor with kapt. Why is the build still slow?",
  "options": ["KSP and kapt can't run in one module", "kapt still writes Java stubs of every class in the module for the one processor left", "KSP processes kapt's stubs again", "Moshi runs twice"],
  "answer": 1, "why": "kapt runs Java processors on Java stubs of the module's Kotlin classes, and writing the stubs is the cost. As long as one kapt processor remains in a module, the stubs are written there. KSP and kapt can run side by side, which is how a migration goes one library at a time."}
]

T = {"id": "ksp", "intro": INTRO, "cheatsheet": CHEAT, "recap": RECAP, "quiz": QUIZ}
out = ROOT / "content/tracks/ksp.json"
out.write_text(json.dumps(T, indent=1, ensure_ascii=False) + "\n")
print(out)
