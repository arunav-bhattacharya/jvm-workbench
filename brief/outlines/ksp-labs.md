# KSP labs: how the modules work (for the ksp track and the cap5 capstone)

Read this before writing a lab for the ksp track (labs/ksp) or the injector capstone (labs/injector). Everything
below was run on this machine with Gradle 9.8.2, JDK 21, Kotlin 2.4.21 and KSP 2.3.14. The quoted outputs are
copied from real runs, not written from memory.

The short version: you add files only under your own lesson's folders. You never edit a Gradle file. Gradle
discovers each lesson from its folders, builds a small processor jar per lesson, and runs it on that lesson's own
source set in the real-build playground.

## 1. Layout

```
labs/ksp/                                  project :ksp, the processors (the learner writes these)
  src/main/kotlin/workbench/ksp/lNN/       exercises: stubs (see "Stub style")
  src/main/resources/workbench/ksp/lNN/SymbolProcessorProvider       one line: the provider class
  src/solution/kotlin/workbench/ksp/lNN/   reference answers, same class names and public signatures
  src/solution/resources/workbench/ksp/lNN/SymbolProcessorProvider   the same line
  src/test/kotlin/workbench/ksp/lNN/       kctfork tests; `test` runs them on src/main, `solutionTest` on src/solution
  src/test/kotlin/workbench/ksp/KspCompile.kt   shared test helper, keep it
  src/demo/kotlin/workbench/ksp/lNN/demo/  Try-it programs (they may use kctfork)
  src/demo/kotlin/workbench/ksp/DemoLauncher.kt   keep it (see pitfall 5)
  annotations/                             project :ksp:annotations, plain Kotlin annotations
    src/main/kotlin/workbench/ksp/annotations/lNN/
  app/                                     project :ksp:app, a normal project with the real KSP Gradle plugin
    src/lNN/kotlin/workbench/ksp/app/lNN/  one source set per lesson: the code KSP runs on
    src/lNN/processors.txt                 optional: other lessons' processors to run here too
    src/lNN/ksp.properties                 optional: processor options for this source set
    src/test/kotlin/workbench/ksp/app/lNN/ the app's JUnit tests (one test source set that sees every lesson)
labs/injector/                             the same three projects for cap5: :injector, :injector:annotations,
                                           :injector:app, packages workbench.injector.lNN,
                                           workbench.injector.annotations, workbench.injector.app.lNN
```

The `smoke` folders (`workbench/ksp/smoke`, `workbench/injector/smoke`, `app/src/smoke`) are a complete example
that proves the pipeline. Copy from them, keep them or delete them. Every place the word "lesson" appears below,
`smoke` works the same way (a "unit" is `lNN` or `smoke`).

The Gradle wiring is one function, `processorLab(lab)` at the end of `labs/build.gradle.kts`, called once for
`ksp` and once for `injector`. The three `build.gradle.kts` files in each lab hold comments only.

## 2. Commands (run from labs/)

| What | Command |
|---|---|
| Tests on your processor (src/main) | `./gradlew :ksp:test --tests 'workbench.ksp.l02.*'` |
| Same tests on the reference answer | `./gradlew :ksp:solutionTest --tests 'workbench.ksp.l02.*'` |
| A demo (reference processor) | `./gradlew :ksp:demo -Pmain=workbench.ksp.l02.demo.CardDemoKt` |
| The same demo with your processor | add `-Pmine=l02` (or `-Pprocessors=mine`) |
| Run lesson 2's processor in the real build, nothing else | `./gradlew :ksp:app:kspL02Kotlin` |
| ... with your processor | `./gradlew :ksp:app:kspL02Kotlin -Pmine=l02` |
| Build and test the whole playground (reference processors) | `./gradlew :ksp:app:test` |
| ... with your processor for some lessons | `./gradlew :ksp:app:test -Pmine=l02,l04` |
| ... with your processors for every lesson | `./gradlew :ksp:app:test -Pprocessors=mine` |
| Watch incremental processing | `./gradlew :ksp:app:compileL07Kotlin -Pksp.incremental.log=true` |
| A main function in the app | `./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.smoke.GreeterKt` |
| Build one lesson's processor jar to look inside | `./gradlew :ksp:l02SolutionJar` (or `l02MineJar`), see `labs/ksp/build/processors/` |

The injector capstone uses the same commands with `:injector`, `:injector:app` and `workbench.injector...`.

Task names come from the source set name: source set `l02` gives `kspL02Kotlin`, `compileL02Kotlin`, and output
in `labs/ksp/app/build/generated/ksp/l02/kotlin/`. The smoke example's are `kspSmokeKotlin` and
`build/generated/ksp/smoke/kotlin/`. There is no lesson code in the app's `main` source set, so
`:ksp:app:kspKotlin` does nothing (NO-SOURCE). Use the lesson's own task. (The ksp outline's lesson 1 names
`./gradlew :ksp:app:kspKotlin`; in this layout that is `./gradlew :ksp:app:kspL01Kotlin`.)

The lesson's `lab.run` stays the house form: `./gradlew :ksp:test --tests 'workbench.ksp.lNN.*'`.

## 3. How to add lesson NN (checklist)

No Gradle edits. Copy the smoke files and rename.

1. Annotations: `labs/ksp/annotations/src/main/kotlin/workbench/ksp/annotations/lNN/<Name>.kt`. Use your own
   lesson's sub-package so parallel writers never touch the same file. Use the same annotation as an earlier
   lesson only when you mean it (then you share the file and must not change it). `SOURCE` retention is enough
   for classes in the module being processed. Use `BINARY` if a processor must see the annotation on classes
   that come from a compiled library.
2. Processor stub: `labs/ksp/src/main/kotlin/workbench/ksp/lNN/`, following "Stub style" below.
3. Reference answer: `labs/ksp/src/solution/kotlin/workbench/ksp/lNN/`, with the same public classes and
   signatures. No `internal`.
4. Services files, one line each, the same in both:
   `labs/ksp/src/main/resources/workbench/ksp/lNN/SymbolProcessorProvider` and
   `labs/ksp/src/solution/resources/workbench/ksp/lNN/SymbolProcessorProvider`, containing for example
   `workbench.ksp.lNN.CardProcessorProvider`. Put one provider per line if the lesson has two processors.
   Gradle moves the file to `META-INF/services/com.google.devtools.ksp.processing.SymbolProcessorProvider` inside
   the lesson's jar. If only one of the two exists, configuration fails with:
   `labs/ksp/src/solution/resources/workbench/ksp/lNN/SymbolProcessorProvider is missing: every processor unit needs that file in both src/main and src/solution`.
   A lesson without a processor (lesson 1's hand-written cards, lesson 8's test harness) has no services file.
5. Everything the processor loads while KSP runs must be inside `workbench/ksp/lNN/` (the jar holds only that
   package) or in a dependency (KSP API, KotlinPoet, kotlinpoet-ksp, the annotations project, the stdlib). If
   the lesson builds on an earlier lab, copy that code into your package as given code, as the outline says.
6. Tests: `labs/ksp/src/test/kotlin/workbench/ksp/lNN/*Test.kt` using `compileWithKsp` (section 5).
7. Demos: `labs/ksp/src/demo/kotlin/workbench/ksp/lNN/demo/`.
8. Real build: `labs/ksp/app/src/lNN/kotlin/workbench/ksp/app/lNN/` with the MoveMate classes your processor
   reads. Tests that call the generated code go in `labs/ksp/app/src/test/kotlin/workbench/ksp/app/lNN/`.
   Optional files:
   - `labs/ksp/app/src/lNN/processors.txt`: other lessons whose processors also run on this source set, for
     example `l02` (lesson 6's receipts need lesson 2's card processor in round 2; lesson 1, which has no
     processor of its own, lists `l02` to show the ready-made card processor). Separate entries with spaces,
     commas or new lines. `#` starts a comment. Your own lesson's processor always runs if it exists.
   - `labs/ksp/app/src/lNN/ksp.properties`: `key=value` lines that become `environment.options` for this source
     set's KSP task only (lesson 7's `movemate.listName=MovingDayList`). This is the per-lesson equivalent of
     `ksp { arg(...) }`, which would reach every lesson. Options belong to the source set, not to the
     processor: a processor that runs on another lesson's source set through `processors.txt` does not get them
     (checked). Like `arg()`, `processorLab` puts each value into both settings of the KSP task,
     `processorOptions` (what the processors read, `@Internal`) and `apOptions` (an `@Input`), so changing a
     value makes the next build run KSP again, over every file. No `--rerun` is needed (checked with lesson 7's
     `movemate.listName`).
9. Check (from labs/):
   ```
   ./gradlew :ksp:solutionTest --tests 'workbench.ksp.lNN.*' --console=plain     # must pass
   ./gradlew :ksp:test --tests 'workbench.ksp.lNN.*' --console=plain --continue  # must fail on the stub
   ./gradlew :ksp:app:test --console=plain                                      # must pass (reference processors)
   ./gradlew :ksp:app:kspLNNKotlin -Pmine=lNN --console=plain                    # must pass on the stub (a warning)
   ./gradlew :ksp:demo -Pmain=<each demo class> --console=plain                  # must run, under 10 s
   ```
   CI runs `./gradlew solutionTest` and `./gradlew testClasses demoClasses` for every project. `:ksp:app:solutionTest`
   runs the app's tests with the reference processors, so it covers your app code too.

If a lesson truly needs another library, stop and say so in your final message. Don't edit `labs/build.gradle.kts`.

## 4. Stub style: an unfinished processor must never break the build

In the real build every lesson's jar is separate, but `-Pprocessors=mine` runs all of the learner's processors,
finished or not. So a stub must not throw out of `process()`. If `TODO()` escapes, the task fails:

```
> Task :ksp:app:kspL99Kotlin FAILED
e: [ksp] kotlin.NotImplementedError: An operation is not implemented: find the classes annotated @Card and write a card() function for each
...
> A failure occurred while executing com.google.devtools.ksp.gradle.KspAAWorkerAction
   > An operation is not implemented: find the classes annotated @Card and write a card() function for each
```

The recommended stub keeps the house rule (exercise bodies are `TODO("...")`) and adds one given wrapper in
`process()` that turns `NotImplementedError` into a KSP warning and generates nothing:

```kotlin
package workbench.ksp.l02

class InventoryProcessorProvider : SymbolProcessorProvider {
    override fun create(environment: SymbolProcessorEnvironment): SymbolProcessor =
        InventoryProcessor(environment.codeGenerator, environment.logger)
}

class InventoryProcessor(
    private val codeGenerator: CodeGenerator,
    private val logger: KSPLogger,
) : SymbolProcessor {

    override val apiFeatures: ApiFeatures = buildApiFeatures {   // see pitfall 3
        enableBackingFields = true
        enableContextParameters = true
    }

    // Given code: while the lab is unfinished this logs a warning and generates nothing,
    // so a real build with -Pmine still runs.
    override fun process(resolver: Resolver): List<KSAnnotated> = try {
        processCards(resolver)
    } catch (e: NotImplementedError) {
        logger.warn("l02 not done yet: ${e.message?.substringAfter("not implemented: ")}")
        emptyList()
    }

    /** 1. Find ... 2. Check ... 3. Read ... 4. Write ... (the five moves, as KDoc) */
    fun processCards(resolver: Resolver): List<KSAnnotated> {
        TODO("find the classes annotated @Inventory and write one card function for each")
    }
}
```

The solution has the same classes, the same wrapper and a real `processCards`. Split the exercise into several
public functions if the lab has several steps (each with its own `TODO`). The wrapper catches only
`NotImplementedError`. A real bug in a half-done processor still shows its stack trace, which is what the learner
needs. If the exercise lives in `finish()`, wrap it the same way.

What the learner sees with the stub:

- Real build (`./gradlew :ksp:app:kspL99Kotlin -Pmine=l99`, verified with a throwaway lesson):
  `w: [ksp] l99 not done yet: find the classes annotated @Card and write a card() function for each`, then
  `BUILD SUCCESSFUL`.
- Test (`:ksp:test`): the test fails with the helper's message
  ```
  java.lang.AssertionError: KSP generated no movemate/LampCard.kt. Generated: []. Messages:
  w: [ksp] l99 not done yet: find the classes annotated @Card and write a card() function for each
  ```
- App code that calls a declaration the stub didn't generate cannot compile, with
  `e: file:///.../labs/ksp/app/src/l98/kotlin/workbench/ksp/app/l98/Plant.kt:8:35 Unresolved reference 'card' on receiver of type 'Plant'.`
  That is expected and can't be avoided. It is why the learner commands use `-Pmine=lNN` (only the lessons you
  name use your jars) and the KSP-only task `kspLNNKotlin`, which always succeeds on a stub. Say so in the lab
  steps. `-Pprocessors=mine` with `:ksp:app:test` works once every lesson whose app code calls generated code
  is finished.

## 5. The kctfork test pattern

Tests compile Kotlin source strings in memory: KSP2 runs the processors you pass, then the Kotlin compiler
compiles the sources together with what was generated. Pass the provider directly. The services files are not
used in tests, so only that lesson's processor runs.

`src/test/kotlin/workbench/ksp/KspCompile.kt` (shared, keep it; the injector copy is in package
`workbench.injector`) gives you:

```kotlin
fun compileWithKsp(vararg sources: SourceFile, processors: List<SymbolProcessorProvider>,
                   options: Map<String, String> = emptyMap()): KspResult

class KspResult {
    val exitCode: KotlinCompilation.ExitCode     // OK, COMPILATION_ERROR (logger.error or bad code), INTERNAL_ERROR (processor threw)
    val messages: String                         // everything printed, one message per line
    val generated: Map<String, String>           // generated Kotlin files: "movemate/LampHello.kt" to text
    fun generated(path: String): String          // one file; fails listing what WAS generated, plus the messages
    fun loadClass(name: String): Class<*>        // yours or generated, through the result's class loader
    fun callTopLevel(fileClass: String, function: String): Any?   // ("movemate.LampHelloKt", "helloFromLamp")
    val result: JvmCompilationResult             // the raw kctfork result, for anything else
}
```

It sets `inheritClassPath = true` (the compiled sources see the annotations, the stdlib and the processors under
test), `jvmTarget = "21"`, a quiet `messageOutputStream`, and a work folder per compilation:
`labs/ksp/build/kctfork/<test|solutionTest>/<nnn>-<test-method>/`. Open `ksp/sources/kotlin/` in that folder to
read exactly what a test generated. The folders are cleared at the start of each test task.
`processorOptions` maps to `environment.options`, as `ksp { arg(...) }` would in Gradle.

The complete example, `labs/ksp/src/test/kotlin/workbench/ksp/smoke/HelloProcessorTest.kt`, passes under both
`:ksp:test` and `:ksp:solutionTest`:

```kotlin
package workbench.ksp.smoke

import com.tschuchort.compiletesting.KotlinCompilation.ExitCode
import com.tschuchort.compiletesting.SourceFile
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import workbench.ksp.compileWithKsp

class HelloProcessorTest {

    @Test
    fun `generates helloFrom for a class annotated @Hello`() {
        val lamp = SourceFile.kotlin(
            "Lamp.kt",
            """
            package movemate

            import workbench.ksp.annotations.smoke.Hello

            @Hello
            class Lamp
            """,
        )

        val run = compileWithKsp(lamp, processors = listOf(HelloProcessorProvider()))

        // 1. the exit code
        assertThat(run.exitCode).isEqualTo(ExitCode.OK)
        // 2. the generated source text
        assertThat(run.generated("movemate/LampHello.kt")).isEqualTo(
            """
            |// Generated by HelloProcessor from Lamp. Do not edit.
            |package movemate
            |
            |import kotlin.String
            |
            |public fun helloFromLamp(): String = "Hello from Lamp"
            |
            """.trimMargin(),
        )
        // 3. load and call the generated code through the result's class loader
        assertThat(run.callTopLevel("movemate.LampHelloKt", "helloFromLamp")).isEqualTo("Hello from Lamp")
    }

    @Test
    fun `reports an error on the line of an interface annotated @Hello`() {
        val shape = SourceFile.kotlin(
            "Shape.kt",
            """
            package movemate

            import workbench.ksp.annotations.smoke.Hello

            @Hello
            interface Shape
            """,
        )

        val run = compileWithKsp(shape, processors = listOf(HelloProcessorProvider()))

        // 4. the messages: the error names the file and the line (6, `interface Shape`, not the @Hello line)
        assertThat(run.exitCode).isEqualTo(ExitCode.COMPILATION_ERROR)
        assertThat(run.messages)
            .containsPattern("""e: \[ksp] \S*/Shape\.kt:6: @Hello goes on a class, but Shape is an interface""")
        assertThat(run.generated).isEmpty()
    }
}
```

Reading generated sources and messages:

- `SourceFile.kotlin(name, text)` trims the indent, so line 1 is `package movemate`. Count lines from there.
- Generated paths are relative to KSP's Kotlin output folder: `<package as folders>/<file name>.kt`. A top-level
  function in `LampHello.kt` lives in class `movemate.LampHelloKt`. An `object` is reached through its
  `INSTANCE` field (the injector helper has `callOnObject("movemate.RouteFactory", "create")`).
- KotlinPoet writes `public` explicitly, adds `import kotlin.String`, ends the file with a newline and indents by
  two spaces. Compare whole files with `isEqualTo` only when the exact text is the point (a golden file). Otherwise
  use `contains`.
- `messages` for the error case above, as printed (the path is the test's work folder):
  ```
  e: Error occurred in KSP, check log for detail
  e: [ksp] /home/user/jvm-workbench/labs/ksp/build/kctfork/test/001-reports-an-error-on-the-line-of-an-interface-annotated-Hello/sources/Shape.kt:6: @Hello goes on a class, but Shape is an interface
  ```
  Assert on the end of the path (`\S*/Shape\.kt:6:`), never on the whole string. Prefixes: `e:` error, `w:`
  warning, `i:` info. A message logged without a node has no path: `w: [ksp] l99 not done yet: ...`.
- `diagnosticMessages` on `result` holds the same entries with a severity and without the `[ksp] ` prefix.
- Errors point at the declaration's own line, not at its annotation's line. For a constructor parameter it is
  the parameter's line (`labs/injector/src/test/.../FactoryProcessorTest.kt` checks `Truck.kt:7`).

Timing (this machine, `:ksp:test` with two tests): the first compilation in a test JVM costs 4 to 7 s, because
it loads KSP2 and the Kotlin compiler. Every later one costs 0.3 to 0.8 s (measured: 6.7 s, then 0.76, 0.68,
0.45, 0.42, 0.40 s). The smoke suite reports 3.9 s and 3.2 s for its two tests: the first stops at a KSP error,
the second pays for loading the compiler's code generator. With Gradle startup, `./gradlew :ksp:test` takes
about 20 s for the smoke suite. So the first test of a lesson may go over the brief's "under 5 s". That's
expected and safe: the per-test timeout is 20 s. Put several classes in one compilation when one scenario can
cover them, and don't compile in a loop.

## 6. Demos

Demos run the reference processors (`src/solution`), so a Try-it works before the lab is done. `-Pmine=lNN`,
where lNN is the lesson in the `-Pmain` class's package, or `-Pprocessors=mine`, runs `src/main` instead. A demo
can use kctfork exactly as a test does. Copy `labs/ksp/src/demo/kotlin/workbench/ksp/smoke/demo/HelloDemo.kt`.
Its output:

```
> Task :ksp:demo
exit code: OK
--- movemate/LampHello.kt
// Generated by HelloProcessor from Lamp. Do not edit.
package movemate

import kotlin.String

public fun helloFromLamp(): String = "Hello from Lamp"
--- helloFromLamp() returns: Hello from Lamp
```

A kctfork demo takes about 8 to 10 s, most of it the first compilation. The demo's work folder is
`labs/ksp/build/kctfork/demo/`. Every demo starts through `DemoLauncher` (see pitfall 5): write a normal
`fun main()`. No `exitProcess` is needed.

## 7. The real-build playground (labs/ksp/app)

`:ksp:app` applies `com.google.devtools.ksp` and is set up the way a real project would use a processor, with
one twist: each lesson is its own source set, so lessons never collide (two processors both generating
`LampBuilder`, lesson 7's aggregate seeing other lessons' classes, and so on).

- Each folder `src/lNN` becomes source set `lNN`. KSP runs on it through configuration `kspLNN` with that lesson's
  processor jar, plus the lessons in `src/lNN/processors.txt`.
- `:ksp` publishes each lesson's jar twice, as Gradle variants with the capabilities
  `workbench.ksp.processors:lNN-solution` (from src/solution) and `workbench.ksp.processors:lNN-mine` (from
  src/main). They carry their runtime dependencies (KotlinPoet, kotlinpoet-ksp, the KSP API, the annotations
  project). The app asks for one of them per lesson. Each jar holds only `workbench/ksp/lNN/**` and the lesson's
  services file, as `META-INF/services/com.google.devtools.ksp.processing.SymbolProcessorProvider`.
- Solution or mine: solution by default, so the app always builds. `-Pprocessors=mine` picks every lesson's
  `-mine` jar. `-Pmine=l02,l04` picks it for those lessons only, wherever they run, including in another
  lesson's source set that lists them in `processors.txt`. Anything else is rejected while the build is
  configured. For example, `-Pprocessors=yours` gives
  `-Pprocessors must be 'solution' (the default) or 'mine', not 'yours'`.
- The app's tests (`src/test`) see every lesson's classes, generated ones included.
- `:ksp:app:solutionTest` runs the same tests as `:ksp:app:test`. The app has no answers of its own, and that way
  CI's `./gradlew solutionTest` builds the app with the reference processors.

The smoke example in the app: `src/smoke/kotlin/workbench/ksp/app/smoke/Greeter.kt` is `@Hello class Greeter`
with `fun greet() = helloFromGreeter() + "!"`. KSP writes
`labs/ksp/app/build/generated/ksp/smoke/kotlin/workbench/ksp/app/smoke/GreeterHello.kt`, and
`src/test/.../GreeterTest.kt` calls both functions.

## 8. Exact output formats in a real Gradle build

`logger.error(message, node)`: a temporary `@Hello interface Shape` in `labs/ksp/app/src/smoke` and
`./gradlew :ksp:app:kspSmokeKotlin --console=plain` printed:

```
> Task :ksp:app:kspSmokeKotlin FAILED
e: [ksp] /home/user/jvm-workbench/labs/ksp/app/src/smoke/kotlin/workbench/ksp/app/smoke/Shape.kt:6: @Hello goes on a class, but Shape is an interface
e: [ksp] Greeter.kt:11: Unresolved reference 'helloFromGreeter'.

FAILURE: Build failed with an exception.

* What went wrong:
Execution failed for task ':ksp:app:kspSmokeKotlin' (registered by plugin 'org.jetbrains.kotlin.jvm').
> A failure occurred while executing com.google.devtools.ksp.gradle.KspAAWorkerAction
   > KSP failed with exit code: PROCESSING_ERROR
```

So the line is `e: [ksp] <absolute path>:<line>: <message>`, with no column, and the line is the declaration's.
The second error is a follow-on (pitfall 6). `logger.warn(message)` without a node prints
`w: [ksp] <message>`, and the build goes on. `logger.info` and `logger.logging` don't show at the default log level.

## 9. Incremental processing, for real

KSP is incremental by default. `-Pksp.incremental.log=true` writes logs to
`labs/ksp/app/build/kspCaches/<source set>/logs/`: `kspDirtySet.log`, `kspSourceToOutputs.log`,
`kspLookupGraph.log`, `symbolTrackerTrace.log` and `enumClassTrackerTrace.log`. Each run rewrites them, so they
always describe the last run. There is no `logs` folder without the flag.

The experiment: the smoke source set with two `@Hello` classes (`Greeter.kt` and a temporary `Mover.kt`). After
one build, one comment line was appended to `Greeter.kt` and
`./gradlew :ksp:app:compileSmokeKotlin -Pksp.incremental.log=true` was run again. `kspDirtySet.log`:

```
All Files
  src/smoke/kotlin/workbench/ksp/app/smoke/Mover.kt
  src/smoke/kotlin/workbench/ksp/app/smoke/Greeter.kt
Modified
  src/smoke/kotlin/workbench/ksp/app/smoke/Greeter.kt
Removed
Disappeared Outputs
Affected By CP
Affected By new syms
Affected By sealed
CP changes
Dirty:
  src/smoke/kotlin/workbench/ksp/app/smoke/Greeter.kt

Dirty / All: 50.00%
```

`kspSourceToOutputs.log`:

```
Accumulated source to outputs map
  src/smoke/kotlin/workbench/ksp/app/smoke/Mover.kt:
    build/generated/ksp/smoke/kotlin/workbench/ksp/app/smoke/MoverHello.kt
  src/smoke/kotlin/workbench/ksp/app/smoke/Greeter.kt:
    build/generated/ksp/smoke/kotlin/workbench/ksp/app/smoke/GreeterHello.kt
  <This is a virtual key for unassociated outputs; DO NOT USE>:
  <This is a virtual key for removed outputs; DO NOT USE>:

Reprocessed sources and their outputs
  src/smoke/kotlin/workbench/ksp/app/smoke/Greeter.kt:
    build/generated/ksp/smoke/kotlin/workbench/ksp/app/smoke/GreeterHello.kt

All reprocessed outputs
  build/generated/ksp/smoke/kotlin/workbench/ksp/app/smoke/GreeterHello.kt
```

`kspLookupGraph.log` lists what each reprocessed file looked up, for example
`src/smoke/kotlin/workbench/ksp/app/smoke/Greeter.kt -> workbench.ksp.annotations.smoke.Hello`. On the first
build (or after a failed one) every file is dirty (`Dirty / All: 100.00%`).

Two traps for an incremental Try-it:

- `touch Greeter.kt` alone changes nothing: Gradle compares file contents, and both `kspSmokeKotlin` and
  `compileSmokeKotlin` were `UP-TO-DATE`. Tell the learner to change the text (add a comment).
- `labs/gradle.properties` turns on the build cache (`org.gradle.caching=true`), and the KSP task is a
  `@CacheableTask`. After an edit is undone, Gradle can restore the outputs `FROM-CACHE` without running KSP, so
  no new log is written. Make a fresh edit, or add `--no-build-cache`.

## 10. Versions, and what is pinned

| Artifact | Version | Where |
|---|---|---|
| KSP Gradle plugin `com.google.devtools.ksp` | 2.3.14 | `plugins { ... apply false }` in labs/build.gradle.kts, applied to `:ksp:app` and `:injector:app` |
| `com.google.devtools.ksp:symbol-processing-api` | 2.3.14 | `implementation` of `:ksp` and `:injector` |
| `com.squareup:kotlinpoet`, `com.squareup:kotlinpoet-ksp` | 2.4.0 | same |
| `dev.zacsweers.kctfork:core`, `dev.zacsweers.kctfork:ksp` | 0.14.0 | `testImplementation` and `demoImplementation` |
| Kotlin, JUnit, AssertJ | 2.4.21, 6.1.3, 3.27.7 | the shared setup |

The versions live in the `versions` map in labs/build.gradle.kts (`ksp`, `kotlinpoet`, `kctfork`). The plugin
version in the `plugins` block can't read that map, so keep the two equal by hand.

Pinned: in `:ksp` and `:injector`, every `com.google.devtools.ksp` artifact resolves to 2.3.14
(`resolutionStrategy.eachDependency`, "one KSP version for the API and the kctfork runtime"). kctfork 0.14.0 was
built against KSP 2.3.12 and brings `symbol-processing`, `symbol-processing-common-deps` and
`symbol-processing-aa-embeddable` at 2.3.12, while our API is 2.3.14. Without the pin, any test source with a
property fails with
`java.lang.NoSuchMethodError: 'boolean ksp.com.google.devtools.ksp.common.visitor.CollectAnnotatedSymbolsVisitor.getEnableNewFeatures()'`
(INTERNAL_ERROR). The testing researcher found and verified that failure. The pin was in place before my first
test run, and with it a class with a property (the injector smoke's `Truck(val driver: String)`) works.

Not pinned, and worth knowing: kctfork compiles the in-memory sources with its own `kotlin-compiler-embeddable`
2.4.20, while the Gradle build uses 2.4.21. Nothing in the smoke labs noticed the difference.

## 11. Pitfalls we hit (with the text you will see)

1. KSP artifact skew in tests: the `NoSuchMethodError` above. Fixed by the pin. Never add a KSP artifact at a
   different version.
2. `validate()` without arguments is deprecated in KSP 2.3.14. The compiler warns:
   `'fun KSNode.validate(predicate: (KSNode?, KSNode) -> Boolean = ...): Boolean' is deprecated. KSNode.validate(predicate) is deprecated in favor of KSNode.validate(predicate, apiFeatures).`
   Write `symbol.validate(apiFeatures = apiFeatures)` inside the processor (`SymbolProcessor` has an
   `apiFeatures` property).
3. Without an `apiFeatures` override, every run prints three info notes, which clutter `messages` in tests:
   ```
   i: [ksp] Processor 'workbench.ksp.smoke.HelloProcessor' has not opted in for upcoming features yet. It might break in a future version of KSP. ...
   i: [ksp] Note that 'SymbolProcessorEnvironment.registerProcessorForNewFeatures' is deprecated; processors should instead migrate to configuring 'SymbolProcessor.apiFeatures'.
   i: [ksp] Processor 'workbench.ksp.smoke.HelloProcessor' has not enabled the following API features: enableBackingFields, enableContextParameters. ...
   ```
   The house pattern overrides `apiFeatures` with `buildApiFeatures { enableBackingFields = true;
   enableContextParameters = true }`. KSP's own note says processors "should eventually enable all features".
   Both smoke processors do this and are quiet.
4. Errors land on the declaration's line, not the annotation's line: `@Hello` on line 5 and `interface Shape` on
   line 6 report `Shape.kt:6`. My first test expected 5 and failed. Write tests (and lesson prose) for the
   declaration's line.
5. A demo that uses kctfork never exits. It prints its output, then hangs: the Kotlin compiler leaves a
   non-daemon thread, `"ApplicationImpl pooled thread 1"`, running after `main` returns. The first injector demo
   ran for 13 minutes before I killed it. The fix is built in: the `:ksp:demo` and `:injector:demo` tasks start
   your class through `workbench.<lab>.DemoLauncher`, which calls its `main` and then exits. Don't delete
   `DemoLauncher.kt`. If you run a kctfork program any other way, end it with `exitProcess(0)`.
6. After a processor error, KSP also prints follow-on errors for code that uses generated declarations:
   `e: [ksp] Greeter.kt:11: Unresolved reference 'helloFromGreeter'.` (file name only, no folder). Fix the first
   error. In lesson prose, show learners which line is the real one.
7. `TODO()` escaping `process()` fails the real build (output in section 4). In kctfork it gives
   `INTERNAL_ERROR`. Use the stub wrapper.
8. With `-Pprocessors=mine`, an unfinished lesson whose app code calls generated declarations fails
   `compileLNNKotlin` with `Unresolved reference ...`. Use `-Pmine=lNN` or `kspLNNKotlin` while part-way.
9. A helper class outside `workbench/ksp/lNN/` passes the kctfork tests (they see the whole classpath) but is
   missing from the lesson's jar in the real build. Keep everything the processor needs in the lesson package.
10. kctfork 0.14.0 API: `configureKsp(useKsp2 = true)` no longer exists (KSP2 is the only mode since 0.10.0).
    Use `configureKsp { symbolProcessorProviders += ... }`. Setting `symbolProcessorProviders` before
    `configureKsp`/`useKsp2()` throws `IllegalStateException: KSP not configured` (from the testing
    researcher's notes). The helper does it in the right order. The Kotlin package is still
    `com.tschuchort.compiletesting`.
11. `KotlinCompilation` needs an opt-in to `ExperimentalCompilerApi`. The build adds it for the test and demo
    compilations, so don't add `@OptIn` yourself.
12. kctfork cannot test incremental behaviour: it deletes its caches and outputs on every `compile()`. Use the
    app and `ksp.incremental.log` for that (lessons 7 and cap5-03).

## 12. The injector capstone

Same machinery, packages `workbench.injector.lNN` (processors), `workbench.injector.annotations` (the cap5
outline's `@Inject`, `@Singleton`, `@Component`, `@Module`, `@Provides`, `@Named`) and `workbench.injector.app.lNN`
(the app). Its smoke example is `@Factory` (`workbench.injector.annotations.smoke.Factory`): a class with a no-arg
constructor gets `public object <Name>Factory { public fun create(): <Name> = <Name>() }`. A constructor parameter
is an error on the parameter's line (`Truck.kt:7: Truck needs a driver, and the smoke factory only builds classes
whose constructor takes no parameters`). The capstone's three lessons all use one set of annotations, so they can
share files in `workbench.injector.annotations`. Isolation comes from the per-lesson jars and source sets, not
from the annotation package. If two lessons need different shapes of the same annotation, use `.lNN`
sub-packages. If cap5-02 or cap5-03 builds on cap5-01's processors, copy them into its own package as given code,
or list `l01` in `app/src/l02/processors.txt`.
