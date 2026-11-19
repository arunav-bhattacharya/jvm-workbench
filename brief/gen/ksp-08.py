import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/ksp/src"
app = "labs/ksp/app/src/l08"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :ksp:demo -Pmain=workbench.ksp.l08.demo."


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


def app_code():
    """The lesson 8 playground's Packing.kt, with its Java twin calling the same generated builders and cards."""
    k = f"{app}/kotlin/workbench/ksp/app/l08/Packing.kt"
    j = f"{app}/java/workbench/ksp/app/l08/PackingJava.java"
    return {"lang": "kotlin", "title": "Packing.kt", "src": read(k),
            "run": "./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l08.PackingKt", "file": k,
            "alt": {"lang": "java", "title": "PackingJava.java", "src": read(j),
                    "run": "./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l08.PackingJava", "file": j}}


def kdemo(name):
    """A kctfork demo: Kotlin only (a processor run in memory has no Java twin)."""
    f = f"{lab}/demo/kotlin/workbench/ksp/l08/demo/{name}.kt"
    return {"lang": "kotlin", "title": f"{name}.kt", "src": read(f), "run": RUN + name + "Kt", "file": f, "solo": True}


FIG = (
    '<svg viewBox="0 0 700 300" role="img" aria-label="The test bench: a few lines of source in a string go to '
    'ProcessorBench.run, which trims the indent and hands them to kctfork. kctfork runs KSP2 and the Kotlin compiler in '
    'memory and returns what happened: an exit code, the messages, the generated files and a class loader. The four '
    'checks read those: the exit code, the generated text against a golden file, the messages by file and line, and a '
    'call into the generated code.">'
    '<rect class="box" x="20" y="24" width="200" height="56" rx="8"/>'
    '<text class="t-s t-code" x="120" y="48" text-anchor="middle">Source("Lamp.kt", ...)</text>'
    '<text class="t-s t-m" x="120" y="68" text-anchor="middle">a few lines, in a string</text>'
    '<line class="ln" x1="224" y1="52" x2="246" y2="52" marker-end="url(#arr)"/>'
    '<rect class="box-a" x="250" y="24" width="200" height="56" rx="8"/>'
    '<text class="t-s t-code" x="350" y="48" text-anchor="middle">ProcessorBench.run</text>'
    '<text class="t-s t-m" x="350" y="68" text-anchor="middle">trims, then compiles</text>'
    '<line class="ln" x1="454" y1="52" x2="476" y2="52" marker-end="url(#arr)"/>'
    '<rect class="box-b" x="480" y="24" width="200" height="56" rx="8"/>'
    '<text class="t-s t-code" x="580" y="48" text-anchor="middle">kctfork: KSP2, kotlinc</text>'
    '<text class="t-s t-m" x="580" y="68" text-anchor="middle">in memory, a fresh room</text>'
    '<line class="ln" x1="580" y1="84" x2="480" y2="124" marker-end="url(#arr)"/>'
    '<rect class="box-ok" x="200" y="128" width="300" height="56" rx="8"/>'
    '<text class="t-s t-code" x="350" y="152" text-anchor="middle">Compiled</text>'
    '<text class="t-s t-m" x="350" y="172" text-anchor="middle">exit code, messages, files, class loader</text>'
    '<line class="ln" x1="260" y1="188" x2="95" y2="228" marker-end="url(#arr)"/>'
    '<line class="ln" x1="320" y1="188" x2="267" y2="228" marker-end="url(#arr)"/>'
    '<line class="ln" x1="380" y1="188" x2="439" y2="228" marker-end="url(#arr)"/>'
    '<line class="ln" x1="440" y1="188" x2="611" y2="228" marker-end="url(#arr)"/>'
    '<rect class="box" x="20" y="232" width="150" height="52" rx="8"/>'
    '<text class="t-s" x="95" y="254" text-anchor="middle">1. exit code</text>'
    '<text class="t-s t-m" x="95" y="273" text-anchor="middle">OK, or which error</text>'
    '<rect class="box" x="192" y="232" width="150" height="52" rx="8"/>'
    '<text class="t-s" x="267" y="254" text-anchor="middle">2. generated text</text>'
    '<text class="t-s t-m" x="267" y="273" text-anchor="middle">a golden file</text>'
    '<rect class="box" x="364" y="232" width="150" height="52" rx="8"/>'
    '<text class="t-s" x="439" y="254" text-anchor="middle">3. messages</text>'
    '<text class="t-s t-m" x="439" y="273" text-anchor="middle">by file and line</text>'
    '<rect class="box" x="536" y="232" width="150" height="52" rx="8"/>'
    '<text class="t-s" x="611" y="254" text-anchor="middle">4. call the code</text>'
    '<text class="t-s t-m" x="611" y="273" text-anchor="middle">the class loader</text>'
    '</svg>'
)

# ---------------------------------------------------------------- opening
OPENING = """Before moving day, a careful family does a practice pack. One empty room, a few boxes, the helper with his clipboard, and a good look at the cards he writes. If he labels the lamp wrong, they want to find out today, in that room, not at the new house with the van gone.

Since the first lab of this track, you've run tests that someone else wrote: a few lines of Kotlin compiled in memory, then checks on what came out. Lesson 7 ended on their limit, because they never run a second, incremental build. Now you'll write that kind of test yourself, the way the author of a processor library does. The trap is a test that looks thorough and checks almost nothing: it passes, the processor is broken, and a lamp with no shade fails on a user's machine.

In this lesson, we'll build a small test bench of our own, make the four checks every processor test makes, keep golden files, pin errors to their file and line, and name what an in-memory test can't see. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_BENCH = """// Closest Java equivalent: Google's compile-testing runs javac with your processor, in memory
JavaFileObject lamp = JavaFileObjects.forSourceString("movemate.Lamp", \"\"\"
        package movemate;

        @Builder
        public class Lamp { ... }
        \"\"\");
Compilation compilation = Compiler.javac()
        .withProcessors(new BuilderProcessor())    // passed directly: no services file
        .compile(lamp);"""
K_BENCH = """val bench = ProcessorBench(KctforkCompiler)      // kctfork, plugged in from src/test
val run = bench.run(
    Source(
        "Lamp.kt",
        \"\"\"
        package movemate

        import workbench.ksp.annotations.Builder

        @Builder
        data class Lamp(val name: String, val bulbs: Int, val shade: String?)
        \"\"\",
    ),
    processors = listOf(BuilderProcessorProvider()), // passed directly: no services file
)"""

S0 = """A processor test needs four things. It needs a few lines of source code, and KSP to run the processor on them. It needs the Kotlin compiler, to compile the sources together with whatever was generated. And it needs a way to look at the results. A real Gradle build does all four, and takes seconds and a whole project per test. So processor tests run the compiler in memory instead, inside the test's own JVM.

The library that does it here is **kctfork**, a community fork of Kotlin Compile Testing. It runs KSP2 and the Kotlin compiler on source code held in strings, in a fresh folder per compile, and hands back what happened. Its Maven group is `dev.zacsweers.kctfork`, and its classes still live in the old package, `com.tschuchort.compiletesting`. Java has had annotation processors, programs that javac runs while it compiles, since Java 6, and KSP is Kotlin's own way to do that job for Kotlin code. Java's processors have a test library of the same kind, Google's compile-testing, and kctfork describes itself as "in the spirit of" it.

Every test that calls kctfork by hand repeats the same dozen lines. A **test harness** is the reusable code around a test that does the setting up, the running and the collecting, so that each test states only what's special about it. This lesson's lab is one, `ProcessorBench`, and its tests use it on two processors from earlier lessons:

""" + pair(J_BENCH, K_BENCH) + """

Both versions hand the processor over directly, so the services file from lesson 2 plays no part in a test. The bench does one quiet favour first: it trims each source's indent. Then line 1 is the `package` line, and a message's line number matches what you count in the test.

The result carries what the four checks need. One part is a **class loader**, the JVM object that finds compiled classes and loads them into the running program. kctfork's class loader sees your source classes and the generated ones, and that's how a test can call `LampBuilder` although the test itself was compiled long before `LampBuilder` existed.

You may wonder why the compiler is a parameter of the bench. The plain reason is the build: kctfork is on this project's test and demo class paths only, and the bench lives in `src/main`, so it can't create a kctfork compile itself. Instead the bench asks for the one thing it needs, any `InMemoryCompiler`, and the tests hand it one. Giving an object what it needs, instead of letting it build its own, is called **dependency injection**, and this is it in miniature; the capstone after this track builds it at full size. That split pays for itself: the bench's message parsing and golden files are tested with no compiler at all, in milliseconds. A compile costs more. The first one in a test JVM takes 4 to 7 seconds while the compiler loads, and later ones under a second.

In the picture, this is the practice pack: a few boxes in an empty room, the same helper, and a look at his cards. The picture breaks in one useful place. kctfork tidies the room after every practice pack, deleting its caches, so it never sees a second build. A compile that ran tells you almost nothing yet, though. The checks do the work."""

# ---------------------------------------------------------------- section 1
J_CHECKS = """// Closest Java equivalent: the same checks with compile-testing and Truth
Compilation compilation = javac().withProcessors(new BuilderProcessor()).compile(lamp);
assertThat(compilation).succeededWithoutWarnings();                      // 1 and 3
assertThat(compilation).generatedSourceFile("movemate.LampBuilder")      // 2, against a stored file
        .hasSourceEquivalentTo(JavaFileObjects.forResource("golden/LampBuilder.java"));
// 4: compile-testing's checks stop at the compile; call the generated builder
//    from a test in a module whose own build runs the processor"""
K_CHECKS = """val run = bench.run(lamp, processors = listOf(BuilderProcessorProvider()))
assertThat(run.exitCode).isEqualTo("OK")                                         // 1. the exit code
assertMatchesGolden(run.generated("movemate/LampBuilder.kt"),                    // 2. the text
    goldenDir.resolve("LampBuilder.kt.golden"))
assertThat(run.messages).isEmpty()                                               // 3. the messages
val builder = run.newInstance("movemate.LampBuilder")                            // 4. call the code
run.call(builder, "name", "desk lamp")
run.call(builder, "bulbs", 1)
run.call(builder, "shade", null)
assertThat(run.call(builder, "build").toString()).isEqualTo("Lamp(name=desk lamp, bulbs=1, shade=null)")"""

S1 = """Every processor test makes some of four checks. The **exit code** says how the compile ended: `OK`, `COMPILATION_ERROR` when a processor called `logger.error` or the code didn't compile, or `INTERNAL_ERROR` when a processor threw. The **generated text** is what the processor wrote. The **messages** are what it and the compiler printed. Last, **calling the generated code** runs it through the class loader. Which of them does a test really need? Let's plant a bug and find out.

The lab's builder processor turns each parameter's type into KotlinPoet's `TypeName` through one function, and the demo passes it a broken one that drops the question mark: `typeOf = { it.toTypeName().copy(nullable = false) }`. For `Lamp`, that turns `shade(shade: String?)` into `shade(shade: String)`. `WeakTestsDemo` runs that builder through the four checks, weakest first:

```text
check 1, the exit code is OK:            passes   (OK)
check 2, the text contains LampBuilder:  passes
check 3, the golden file:                FAILS at line 18
    expected: public fun shade(shade: String?): LampBuilder = apply { this.shade = shade }
    actual:   public fun shade(shade: String): LampBuilder = apply { this.shade = shade }
check 4, call shade(null):               FAILS with NullPointerException: Parameter specified as non-null is null: method movemate.LampBuilder.shade, parameter shade
```

The first two checks pass, and they pass honestly: the broken builder compiles, and it does contain `class LampBuilder`. A test made of those two proves that the processor didn't crash. The bug would reach the first family whose lamp has no shade.

The third check is a **golden file**: a stored copy of the output you expect, compared with the real output on every run, with a way to rewrite it on purpose. The bench's `checkGolden` writes a missing golden file and fails once, so a person reads the new text before it becomes the standard. It reports the first line that differs, counting from 1, and `UPDATE_GOLDEN=true ./gradlew :ksp:test ...` rewrites every file it checks. A golden file is a proofreader with no sense of proportion: it flags a moved space as loudly as a lost question mark. A KotlinPoet upgrade that changes how it formats code will fail every golden file you have, as KotlinPoet 2.4.0 did when it changed how annotation arrays are written.

The fourth check calls `shade(null)` through the class loader and gets the generated code's own exception. That one checks behaviour, and formatting can't fool it. Here are the four checks in one test, for KSP and for javac:

""" + pair(J_CHECKS, K_CHECKS) + """

**A test that only compiles proves the processor didn't crash. Call the code it wrote.**

Pair each golden file with at least one call into the generated code. The golden file catches any change; the call tells you whether the change matters. The two tests left are the unhappy ones, the inputs your processor must refuse."""

# ---------------------------------------------------------------- section 2
J_ERR = """// Closest Java equivalent: compile-testing finds an error by its text, file and line
assertThat(compilation).failed();
assertThat(compilation).hadErrorContaining("@Builder goes on a class, but Shape is an interface")
        .inFile(bad)
        .onLine(6);"""
K_ERR = """assertThat(run.exitCode).isEqualTo("COMPILATION_ERROR")
assertThat(run.errors).contains(
    Message('e', "Bad.kt", 6, "@Builder goes on a class, but Shape is an interface"),
    Message('e', "Bad.kt", 9, "@Builder goes on a class, but Van is an object"),
    Message('e', "Bad.kt", 12, "SafeBuilder can't call Safe's private constructor. Make the constructor public or internal."),
)"""

S2 = """Lesson 5 taught the builder to refuse bad input with an error on the exact box. A test of that has three things to pin down: the compile failed, the message says the right thing, and it points at the right file and line. The last part is the one people skip, and it's the one users feel.

Here is what kctfork printed for `@Builder interface Shape`, with the interface on line 6:

```text
e: Error occurred in KSP, check log for detail
e: [ksp] /…/sources/Shape.kt:6: @Builder goes on a class, but Shape is an interface
```

And here is the Kotlin compiler on a user's file that passes an `Int` to `shade`:

```text
e: file:///…/sources/Use.kt:5:16 Argument type mismatch: actual type is 'Int', but 'String?' was expected.
```

Three shapes of message, then. KSP's own has `[ksp]`, an absolute path, a line and no column. The compiler's has `file://`, a line and a column. And a line with no location at all, like kctfork's summary `Error occurred in KSP`. The paths point into a temporary folder that changes with every run, so a test must never compare them. The bench's `parseMessage` splits each line into a `Message`: the severity, the file name only, the line and the text. It skips lines that aren't messages, such as a stack trace. Then a test can say exactly what it means:

""" + pair(J_ERR, K_ERR) + """

That Kotlin test compiles one file with three bad classes and expects three errors in one build, each on its own line. The lines are 6, 9 and 12, the lines of `interface Shape`, `object Van` and `class Safe`, not the lines of their `@Builder` notes. KSP reports a declaration's own line, and so does javac, which is why compile-testing's `onLine(6)` finds the same line. Count from the `package` line, which is line 1 because the bench trimmed the indent.

**An error test checks the text and the line. A message on the wrong line is a bug the user feels.**

In the picture, the helper's note must say which box, not "somewhere in the hall". The same note in a real build points at your real file. The practice room, though, can't show everything about moving day."""

# ---------------------------------------------------------------- section 3
J_KIT = """// A TestKit test, sketched (this lab has no TestKit dependency)
BuildResult result = GradleRunner.create()
        .withProjectDir(projectDir)               // a tiny build the test writes on disk
        .withArguments("compileKotlin", "-Pksp.incremental.log=true")
        .build();
assertEquals(TaskOutcome.SUCCESS, result.task(":kspKotlin").getOutcome());"""
K_KIT = """// A TestKit test, sketched (this lab has no TestKit dependency)
val result = GradleRunner.create()
    .withProjectDir(projectDir)                   // a tiny build the test writes on disk
    .withArguments("compileKotlin", "-Pksp.incremental.log=true")
    .build()
assertThat(result.task(":kspKotlin")?.outcome).isEqualTo(TaskOutcome.SUCCESS)"""

S3 = """An in-memory test is fast because it skips the build, and so it can't see anything that lives in the build. Lesson 7's bugs are the clearest case. kctfork deletes its caches and runs a clean pass on every compile, so a wrong `Dependencies` passes every kctfork test you can write. The services file is another: tests hand the provider over directly, so a missing services file passes them all, and the real build then fails with `e: [ksp] No providers found in processor classpath.` Options come through the real build too, and lesson 7 showed that a new value reaches the processor only when it's a tracked input of the task. And a multiplatform project's per-target KSP tasks exist only in Gradle.

For those, there's **Gradle TestKit**: Gradle's own library for running a real build from a test. In the Gradle docs' words, "builds run in a separate process from your tests". A TestKit test writes a tiny project to a folder, runs Gradle on it, and checks the tasks and the files:

""" + pair(J_KIT, K_KIT) + """

Each such test costs a Gradle daemon and a real KSP run: seconds, where kctfork costs a fraction of one. So a library keeps a handful of them, for the services file, one edit-and-rebuild for each aggregating output, and the options. This course's lab has no TestKit dependency. The playground in `labs/ksp/app` plays that part by hand, as lesson 7's Try-its did.

When a test fails and you don't know why, debug in this order. First, read the generated file: the kctfork work folder keeps it, under `ksp/sources/kotlin/`, and most surprises are visible there. Second, add a temporary `logger.warn("...")`: a warning shows at Gradle's default log level, and `logger.info` only with `--info`. Third, a debugger. A kctfork test is an ordinary JUnit test, so debug it like one. In a real build, KSP2 runs inside the Gradle daemon, so KSP's docs suggest starting Gradle with `-Dorg.gradle.debug=true` and attaching to it.

**Test a processor's logic in memory, and its wiring in a real build.**

In the picture, the practice pack checks the helper's cards; only moving day checks that the van turns up. Together they cover the move."""

# ---------------------------------------------------------------- closing
CLOSING = """We started with a practice pack in an empty room and a lamp with no shade. The bench compiled a few lines in memory, and four checks looked at the result: the exit code and a `contains` passed a broken builder, while a golden file and one call with `null` caught it. Errors came back as a file, a line and a text, and the real build covered what the room couldn't.

In a processor test of your own, find each test that stops at `exitCode` or `contains`, and add a call into the generated code.

Next, we'll step back and choose. When is reflection good enough, when does a job need a compiler plugin, and when is kapt still the only helper there is?"""

L = {
 "id": "ksp-08",
 "title": "Testing a processor",
 "minutes": 40,
 "goal": "By the end you can write a small reusable test bench for a processor, make the four checks every processor test makes (exit code, generated text with golden files, messages by file and line, a call into the generated code), and say which bugs need a real Gradle build to show.",
 "opening": OPENING,
 "warmup": {
  "q": "A builder processor's test checks two things: the compile succeeds, and the generated text contains `class LampBuilder`. A bug makes the processor drop the `?` from `shade: String?`, so the builder has `shade(shade: String)`. What does the test do?",
  "options": ["It fails: the generated code doesn't compile", "It passes: the builder compiles and still contains `class LampBuilder`", "It fails: KSP reports an error for the nullable parameter", "It passes only when `Lamp` is a data class"],
  "answer": 1,
  "why": "A builder with a non-null `shade` is valid Kotlin, so the compile succeeds and the text check finds its class. Nothing fails until someone calls `shade(null)`. Section 2 runs exactly this bug through all four checks: a golden file and one call into the code catch it."
 },
 "sections": [
  {
   "h": "A practice pack in an empty room: compiling a few lines in memory",
   "body": S0,
   "try": {
    "title": "Read what a test generated",
    "minutes": 3,
    "steps": [
     "From `labs/`, run the reference bench's tests: `./gradlew :ksp:solutionTest --tests 'workbench.ksp.l08.*'`.",
     "Open `labs/ksp/build/kctfork/solutionTest/`. Each compile left a folder named `l08-<nnn>`. Find the one whose `ksp/sources/kotlin/movemate/` holds `BookshelfBuilder.kt` and read it.",
     "In the same folder, find `sources/Bookshelf.kt`. Its first line is `package movemate`: that's line 1 when you count lines in a message."
    ],
    "expect": "Ten tests pass. The work folders keep every source the tests compiled and every file KSP generated, so `BookshelfBuilder.kt` is there with `private var books: List<String>? = null` and `public fun boughtOn(boughtOn: LocalDate?): BookshelfBuilder`. The folders are cleared at the start of the next test run."
   },
   "refs": [{"title": "kctfork README (Kotlin Compile Testing fork)", "url": "https://github.com/ZacSweers/kotlin-compile-testing", "kind": "docs"}]
  },
  {
   "h": "Four checks, weakest first: a builder bug that two of them miss",
   "body": S1,
   "figure": {"svg": FIG, "caption": "The bench: source strings in, a compile in memory, and four checks on what came out."},
   "try": {
    "title": "Plant a bug and see which checks notice",
    "minutes": 4,
    "steps": [
     "Run `WeakTestsDemo` and read the four verdicts. Which two would a quick test have stopped at?",
     "In `WeakTestsDemo.kt`, change `copy(nullable = false)` to `copy()`, so the builder keeps its question marks. Predict the four verdicts, then run it again.",
     "Change it back. Once your bench passes the lab, run the demo with `-Pmine=l08`: it uses your `checkGolden` and your `call`."
    ],
    "code": kdemo("WeakTestsDemo"),
    "expect": "With the bug, checks 1 and 2 pass, check 3 fails at line 18 with `shade(shade: String?)` expected and `shade(shade: String)` actual, and check 4 fails with `NullPointerException: Parameter specified as non-null is null: method movemate.LampBuilder.shade, parameter shade`. With `copy()`, checks 1, 2 and 4 pass, and check 3 prints `Matches`."
   },
   "refs": [{"title": "Gradle TestKit (Gradle docs)", "url": "https://docs.gradle.org/current/userguide/test_kit.html", "kind": "docs"}]
  },
  {
   "h": "Errors by file and line: pinning down what the processor refuses",
   "body": S2,
   "try": {
    "title": "Read the same error in a real build",
    "minutes": 4,
    "steps": [
     "Run `./gradlew :ksp:app:kspL08Kotlin` and open `labs/ksp/app/build/generated/ksp/l08/kotlin/workbench/ksp/app/l08/LampBuilder.kt`. Compare it with `labs/ksp/src/test/resources/workbench/ksp/l08/golden/LampBuilder.kt.golden`: only the package differs.",
     "Run the program below, or its Java twin.",
     "Create `labs/ksp/app/src/l08/kotlin/workbench/ksp/app/l08/Shape.kt` with the package line, `import workbench.ksp.annotations.Builder`, a blank line, `@Builder` and `interface Shape`, so the interface is on line 6. Run the KSP task again and read the error line.",
     "Delete `Shape.kt` and run the task once more."
    ],
    "code": app_code(),
    "expect": "The program prints `Lamp: name=desk lamp, bulbs=1, shade=null` and `Bookshelf: shelves=3, books=[Dune, Emma]`. With `Shape.kt`, the task fails with `e: [ksp] /…/labs/ksp/app/src/l08/kotlin/workbench/ksp/app/l08/Shape.kt:6: @Builder goes on a class, but Shape is an interface` and `KSP failed with exit code: PROCESSING_ERROR`: the same text and line as in the test, with your real path instead of a temporary one."
   },
   "refs": [{"title": "Messager (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.compiler/javax/annotation/processing/Messager.html", "kind": "docs"}]
  },
  {
   "h": "What a practice pack can't show: the real build, TestKit and debugging",
   "body": S3,
   "try": {
    "title": "Check the wiring that tests skip",
    "minutes": 3,
    "steps": [
     "Build lesson 8's processor jar: `./gradlew :ksp:l08SolutionJar`. List it with `unzip -l ksp/build/processors/ksp-l08-solution.jar` and print its services file with `unzip -p ksp/build/processors/ksp-l08-solution.jar META-INF/services/com.google.devtools.ksp.processing.SymbolProcessorProvider`.",
     "Run `./gradlew :ksp:app:kspL08Kotlin --rerun --info` and look for the lines that start with `i: [ksp]`."
    ],
    "expect": "The jar holds the lesson's classes and `META-INF/services/com.google.devtools.ksp.processing.SymbolProcessorProvider`, with two lines: `workbench.ksp.l08.InventoryProcessorProvider` and `workbench.ksp.l08.BuilderProcessorProvider`. With `--info`, KSP prints `i: [ksp] loaded provider(s): [workbench.ksp.l08.InventoryProcessorProvider, workbench.ksp.l08.BuilderProcessorProvider]`. None of this exists in a kctfork test."
   },
   "refs": [{"title": "KSP2 introduction: runs in the Gradle daemon, debugging (google/ksp docs)", "url": "https://github.com/google/ksp/blob/main/docs/ksp2.md", "kind": "docs"}]
  }
 ],
 "compare": {
  "title": "One error test: compile-testing for a javac processor, the bench for a KSP processor",
  "java": {"title": "BuilderProcessorTest.java", "src": "// Closest Java equivalent: Google's compile-testing with Truth\nimport static com.google.testing.compile.CompilationSubject.assertThat;\nimport static com.google.testing.compile.Compiler.javac;\n\nclass BuilderProcessorTest {\n    @Test\n    void reportsAnInterfaceOnItsOwnLine() {\n        JavaFileObject bad = JavaFileObjects.forSourceString(\"movemate.Shape\", \"\"\"\n                package movemate;\n\n                import movemate.annotations.Builder;\n\n                @Builder\n                interface Shape {}\n                \"\"\");\n\n        Compilation compilation = javac().withProcessors(new BuilderProcessor()).compile(bad);\n\n        assertThat(compilation).failed();                                         // 1. the outcome\n        assertThat(compilation)\n                .hadErrorContaining(\"@Builder goes on a class, but Shape is an interface\")  // 3. the text\n                .inFile(bad)\n                .onLine(6);                                                         //    and the line\n        // 2 and 4: generatedSourceFile(...) for the text; calling the code is not among its checks\n    }\n}"},
  "kotlin": {"title": "BuilderProcessorTest.kt", "src": "class BuilderProcessorTest {\n    private val bench = ProcessorBench(KctforkCompiler)\n\n    @Test\n    fun `reports an interface on its own line`() {\n        val run = bench.run(\n            Source(\n                \"Shape.kt\",\n                \"\"\"\n                package movemate\n\n                import workbench.ksp.annotations.Builder\n\n                @Builder\n                interface Shape\n                \"\"\",\n            ),\n            processors = listOf(BuilderProcessorProvider()),\n        )\n\n        assertThat(run.exitCode).isEqualTo(\"COMPILATION_ERROR\")                    // 1. the outcome\n        assertThat(run.errors)                                                       // 3. text and line\n            .contains(Message('e', \"Shape.kt\", 6, \"@Builder goes on a class, but Shape is an interface\"))\n        assertThat(run.generated).isEmpty()                                          // 2. nothing written\n    }\n}"},
  "note": "The two tests have the same shape: source in a string, the processor passed directly, then the outcome, the text and the line. compile-testing came first and kctfork follows its spirit. The differences are in the details. compile-testing works through Truth subjects (`failed()`, `hadErrorContaining(...).inFile(...).onLine(...)`), while the bench parses messages into plain `Message` values that any assertion library can compare. Both report the declaration's line, 6 here, not the annotation's. And the kctfork result carries a class loader, so a Kotlin test can call the generated code in the same test, the fourth check; compile-testing's documented checks stop at the compile."
 },
 "worked": {
  "title": "Turn a bug report into a test that fails first",
  "steps": [
   {"say": "The report: \"The builder breaks for my class with a private constructor: the build fails, but the message points at line 1.\" Before touching the processor, reproduce it on the bench, with the class on a line you can count.",
    "code": "val safe = Source(\n    \"Safe.kt\",\n    \"\"\"\n    package movemate\n\n    import workbench.ksp.annotations.Builder\n\n    @Builder\n    class Safe private constructor(val code: String)\n    \"\"\",\n)\nval run = bench.run(safe, processors = listOf(BuilderProcessorProvider()))", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "JavaFileObject safe = JavaFileObjects.forSourceString(\"movemate.Safe\", \"\"\"\n        package movemate;\n\n        import movemate.annotations.Builder;\n\n        @Builder\n        public class Safe { private Safe(String code) {} }\n        \"\"\");\nCompilation compilation = javac().withProcessors(new BuilderProcessor()).compile(safe);"},
   {"say": "Write the assertion the user wanted: the error, its text, and line 6, the line of `class Safe`. Run it and watch it fail with the processor as it is. A test that has never failed hasn't proved anything yet.",
    "code": "assertThat(run.exitCode).isEqualTo(\"COMPILATION_ERROR\")\nassertThat(run.errors).contains(\n    Message('e', \"Safe.kt\", 6, \"SafeBuilder can't call Safe's private constructor. Make the constructor public or internal.\"),\n)", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "assertThat(compilation).failed();\nassertThat(compilation)\n        .hadErrorContaining(\"SafeBuilder can't call Safe's private constructor\")\n        .inFile(safe)\n        .onLine(6);"},
   {"say": "Fix the processor: the error must be logged on the class symbol, `logger.error(message, symbol)`, not without a node and not on a file. The javac twin passes the element to `printMessage`.",
    "code": "if (constructor.isPrivate()) {\n    logger.error(\"${name}Builder can't call $name's private constructor. Make the constructor public or internal.\", symbol)\n    return null\n}", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "if (constructor.getModifiers().contains(Modifier.PRIVATE)) {\n    messager.printMessage(Diagnostic.Kind.ERROR,\n            name + \"Builder can't call \" + name + \"'s private constructor. Make the constructor public or internal.\",\n            type);\n    return;\n}"},
   {"say": "Run the test until it passes, and keep it. The bug can't come back without a red test, and the next reader of the suite learns what a private constructor should produce, on which line.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "A reusable test bench for processors, with golden files",
  "minutes": 15,
  "files": [f"{lab}/main/kotlin/workbench/ksp/l08/ProcessorBench.kt", f"{lab}/main/kotlin/workbench/ksp/l08/GivenProcessors.kt", f"{lab}/test/kotlin/workbench/ksp/l08/BuilderProcessorTest.kt", f"{lab}/test/resources/workbench/ksp/l08/golden/LampBuilder.kt.golden"],
  "run": "./gradlew :ksp:test --tests 'workbench.ksp.l08.*'",
  "steps": [
   "Read `GivenProcessors.kt`: copies of lesson 2's card processor and lessons 4 and 5's builder processor, given, so this lesson stands on its own. You won't change them; you'll test them.",
   "Read `ProcessorBench.kt`. Given: `Source`, the `InMemoryCompiler` interface, `Compiled`, `Message`, `newInstance`, the three `Regex` values and `GoldenResult`. Five functions are yours. Then read `KctforkCompiler.kt` in `src/test`: the compiler the tests plug in.",
   "Run the tests: all ten fail with `NotImplementedError`. This lab is the fifth move, Prove. Each check you build proves one of the other four moves: the messages prove Check, the generated text proves Read and Write, a call into the code proves Write from end to end, and the exit code proves the processor finished.",
   "Write `run` (trim each source, compile, wrap) and `generated` (walk the folder; paths with `/`). Then `parseMessage`: try the three `Regex` values in order, and keep only the file name of a path.",
   "Write `call`, modelled on `newInstance`: find the method by name and parameter count. A `String` target is a class name: call a static method with no receiver, or a Kotlin `object`'s method on its `INSTANCE` field.",
   "Write `checkGolden`: write the file when it's missing or `update` is true, and otherwise report the first line that differs, counting from 1.",
   "Prove: run until all ten tests pass. Then change one character in `LampBuilder.kt.golden`, run the tests and read the failure, and put it back with `UPDATE_GOLDEN=true ./gradlew :ksp:test --tests 'workbench.ksp.l08.*'`. That run fails once with `Wrote the golden file ...`; the next run passes.",
   "From memory: close the files and write, on paper, one test for the card processor with all four checks. Then compare it with the drill's answer."
  ],
  "hints": [
   "`Source.copy(text = text.trimIndent())` keeps the file name. The `Compiled` from the compiler goes straight into `BenchRun(...)`.",
   "`compiled.generatedDir.walk().filter { it.isFile }`, then `relativeTo(generatedDir).invariantSeparatorsPath` gives `movemate/LampBuilder.kt` on every system.",
   "`Regex.matchEntire(line)?.destructured` gives the groups. In the KSP pattern the location group is optional, so an empty path means no file and no line.",
   "`Modifier.isStatic(method.modifiers)` tells a top-level function from an object's method. Wrap the call in `unwrapped { ... }`, so a test sees the generated code's own exception.",
   "`String.lines()` keeps a last empty line after a final newline, so a missing last line compares `\"line two\"` with `\"\"`. `getOrNull` handles files of different lengths."
  ],
  "done_when": "All ten tests in `ProcessorBenchTest` and `BuilderProcessorTest` pass, and a one-character change to a golden file fails with its line number."
 },
 "drill": {
  "title": "Write the four checks from memory",
  "minutes": 5,
  "prompt": "Close this page. Using the bench, write one test for the card processor on `@Inventory data class Lamp(val name: String, val bulbs: Int, val shade: String?)`: check the exit code, check the generated `movemate/LampInventoryCard.kt` against a golden file, check that there are no messages, and call the card on a lamp with no shade. Then write the compile-testing version of the first three checks for a javac card processor.",
  "answer": {"lang": "kotlin", "src": "@Test\nfun `the card for a lamp with no shade`() {\n    val run = bench.run(lamp, processors = listOf(InventoryProcessorProvider()))\n\n    assertThat(run.exitCode).isEqualTo(\"OK\")                                     // 1. exit code\n    assertMatchesGolden(run.generated(\"movemate/LampInventoryCard.kt\"),         // 2. generated text\n        goldenDir.resolve(\"LampInventoryCard.kt.golden\"))\n    assertThat(run.messages).isEmpty()                                           // 3. messages\n    val lampWithNoShade = run.newInstance(\"movemate.Lamp\", \"desk lamp\", 1, null) // 4. call the code\n    assertThat(run.call(\"movemate.LampInventoryCardKt\", \"inventoryCard\", lampWithNoShade))\n        .isEqualTo(\"Lamp: name=desk lamp, bulbs=1, shade=null\")\n}",
             "alt": {"lang": "java", "title": "CardProcessorTest.java", "src": "// Closest Java equivalent: compile-testing with Truth\n@Test\nvoid theCardForALamp() {\n    Compilation compilation = javac().withProcessors(new CardProcessor()).compile(lamp);\n\n    assertThat(compilation).succeededWithoutWarnings();                 // 1 and 3\n    assertThat(compilation).generatedSourceFile(\"movemate.LampInventoryCard\")\n            .hasSourceEquivalentTo(JavaFileObjects.forResource(\"golden/LampInventoryCard.java\"));  // 2\n    // 4: call the card from a test in a module whose build runs the processor\n}"}}
 },
 "recap": [
  "A processor test compiles a few lines in memory: kctfork runs KSP2 and the Kotlin compiler in the test's JVM, as compile-testing runs javac. The processor is passed directly, so the services file plays no part.",
  "The four checks are the exit code, the generated text, the messages by file and line, and a call into the generated code through the result's class loader. The first two alone passed a builder that had lost a question mark.",
  "A golden file stores the expected output and reports the first differing line. Write a missing one and review it once, rewrite on purpose with `UPDATE_GOLDEN=true`, and pair it with a call into the code, because formatting changes fail it too.",
  "Error tests pin the text and the line: KSP and javac report the declaration's line, counted from the `package` line once the indent is trimmed. Never compare paths; they point into a temporary folder.",
  "The limit: an in-memory test runs a fresh, clean build every time, so it can't see wrong Dependencies, a broken services file or untracked options. Those need a real build, by hand in the playground or with Gradle TestKit."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "A builder test checks `exitCode == OK` and that the generated text contains `fun build()`. Which bug can it catch?",
   "options": ["A builder whose `shade` setter takes `String` instead of `String?`", "A processor that throws while it reads the class", "A builder that sets the wrong property in `build()`", "A missing services file"],
   "answer": 1, "why": "A processor that throws ends the compile with `INTERNAL_ERROR`, so the exit-code check fails. The wrong nullability and the wrong property both compile and contain `fun build()`: only a golden file or a call into the code catches them. Tests pass the provider directly, so no in-memory test sees the services file."},
  {"q": "After a KotlinPoet upgrade, every golden-file test fails. Each diff is one moved line break, and all the call-the-code tests pass. What do you do?",
   "options": ["Delete the golden files: they are too brittle to keep", "Pin KotlinPoet to the old version for good", "Read the diffs, confirm only formatting changed, and rewrite the files with `UPDATE_GOLDEN=true`", "Change the processor until the old text comes back"],
   "answer": 2, "why": "Golden files fail on any change, which is their job; the behavioural tests tell you whether it matters. Here nothing a user would notice changed, so review the diff once and accept it on purpose. Deleting them throws away the check that caught the lost question mark."},
  {"q": "In a kctfork test, `@Builder` is on line 5 and `interface Shape` on line 6, counted from the `package` line. The processor logs `logger.error(message, symbol)`. Which line does the message carry?",
   "options": ["5, the line of the annotation", "6, the line of the declaration", "1, the start of the file", "No line: kctfork removes locations"],
   "answer": 1, "why": "KSP reports a declaration's own line, and javac does the same, which is why compile-testing's `onLine(6)` would match. kctfork keeps the location; only the folder is temporary, so a test compares the file name and line, not the path."},
  {"q": "From lesson 7: a master list is written with `Dependencies(aggregating = false, *files)`. Can a kctfork test catch that it shrinks when a new file is added?",
   "options": ["Yes, with `kspIncremental = true` and two compiles", "Yes, if the test compiles the new file in a second `SourceFile`", "No: every kctfork compile deletes its caches and runs a clean build, which writes a correct list", "No, because kctfork ignores Dependencies, though a second compile would show it"],
   "answer": 2, "why": "kctfork wipes its KSP caches and outputs on every compile and passes no changed-file sets, so each compile is a clean build, and a clean build lists every class. The mistake appears only on an incremental build: in the playground with `ksp.incremental.log=true`, or in a Gradle TestKit test.",
   "from": "ksp-07"},
  {"q": "A test calls a generated builder's `shade(null)` through reflection, and the parameter is non-null. Without the bench's unwrapping, what does the test see?",
   "options": ["`NullPointerException`", "`InvocationTargetException`, with the `NullPointerException` as its cause", "`IllegalArgumentException` from the class loader", "Nothing: reflection skips Kotlin's null checks"],
   "answer": 1, "why": "`Method.invoke` wraps whatever the called code throws in an `InvocationTargetException`. Kotlin's null check inside the generated `shade` throws the `NullPointerException`. The bench rethrows the cause, so a test can assert on the real exception, as `WeakTestsDemo` prints it."}
 ],
 "flashcards": [
  {"front": "What does kctfork do in a processor test?", "back": "It runs KSP2 and the Kotlin compiler in the test's JVM on source code in strings, and returns the exit code, the messages, the generated files and a class loader."},
  {"front": "What are the four checks a processor test makes?", "back": "The exit code, the generated text (often a golden file), the messages by file and line, and a call into the generated code."},
  {"front": "What do `COMPILATION_ERROR` and `INTERNAL_ERROR` mean in a kctfork result?", "back": "`COMPILATION_ERROR`: a processor called `logger.error`, or the code didn't compile. `INTERNAL_ERROR`: a processor threw."},
  {"front": "What is a golden file?", "back": "A stored copy of the expected output, compared with the real output on every run, with a way to rewrite it on purpose after you've read the diff."},
  {"front": "Why must a test call the generated code and not only read it?", "back": "Code can compile and look right and still be wrong: a builder that lost a `?` compiles, and only `shade(null)` shows the bug."},
  {"front": "What can't an in-memory processor test see?", "back": "Anything in the build: incremental behaviour and wrong Dependencies, the services file, how options are wired, multiplatform tasks. Use a real build or Gradle TestKit."},
  {"front": "What's the javac twin of asserting an error's line in kctfork?", "back": "compile-testing: `assertThat(compilation).hadErrorContaining(\"...\").inFile(file).onLine(6)`."}
 ],
 "terms": [
  {"term": "Test harness", "plain": "Reusable code around tests that sets up, runs and collects, so each test states only what's special about it."},
  {"term": "kctfork", "plain": "A library that runs KSP2 and the Kotlin compiler inside a test, on source code held in strings."},
  {"term": "compile-testing", "plain": "Google's library that runs javac with your annotation processors inside a test, and checks the result."},
  {"term": "Class loader", "plain": "The JVM object that finds compiled classes and loads them into the running program."},
  {"term": "Golden file", "plain": "A stored copy of the expected output, compared with the real output on every test run."},
  {"term": "Exit code", "plain": "How a compile ended: OK, a compilation error, or an internal error from a processor that threw."},
  {"term": "Gradle TestKit", "plain": "Gradle's library for running a real build from a test, in a separate process."}
 ],
 "explain_back": {
  "prompt": "A teammate's processor tests all look like this: compile a class, assert the exit code is OK, assert the output contains the class name. They say the processor is well tested. Explain what those tests prove, what they miss, and what you would add.",
  "answer": "Those tests prove that the processor ran without crashing on the inputs they use, and that it wrote a file with the right name in it. They miss almost every real bug, because generated code can compile and still be wrong: a builder that drops a question mark from `shade: String?` passes both checks and fails the first time someone passes `null`. I'd add the other two checks. First, call the generated code through the result's class loader, with the awkward values: a null, an empty list, a missing required field. Second, test the refusals: give the processor an interface or a private constructor, and assert the exit code, the message text and the file and line, which is the declaration's line. Golden files help too, as long as each one sits next to a call into the code, because formatting changes fail them. And I'd say plainly what in-memory tests can't see: incremental builds and the services file need a real build, in a playground or with Gradle TestKit."
 },
 "deeper": {
  "minutes": 8,
  "body": "The bench splits the compiler from the checks, and the same idea works inside a processor. Split it in two: one half turns KS symbols into a plain data model (the class name, the parameters and their types), the other turns that model into a `FileSpec`. The second half can then be tested with `fileSpec.toString()` and no compiler at all, in milliseconds, and the compile tests shrink to a few that check the wiring.\n\nA few kctfork details are worth knowing before you read older blog posts. Since version 0.10.0 it supports KSP2 only, and `configureKsp(useKsp2 = true)` no longer compiles: write `configureKsp { symbolProcessorProviders += ... }`. Setting providers before KSP is configured throws `IllegalStateException: KSP not configured`, which is exactly what the README's snippet does. `kspWithCompilation` does nothing on KSP2. kctfork compiles with its own Kotlin compiler, 2.4.20 in version 0.14.0, while this course builds with 2.4.21, and it was built against KSP 2.3.12, which is why the lab's build pins every KSP artifact to 2.3.14. Without that pin, any source with a property fails with a `NoSuchMethodError`.\n\nOn the Java side, compile-testing's documented examples live in its `package-info.java`, and its checks cover the outcome (`succeeded()`, `failed()`), the messages (`hadErrorContaining(...).inFile(...).onLine(...)`, also `atColumn` and `onLineContaining`) and the generated files (`generatedSourceFile(...)`, `hasSourceEquivalentTo(...)`). It passes processors to javac directly, so JDK 23's change, which stopped javac from running processors it merely finds on the class path, doesn't affect it."
 },
 "sources": [
  {"title": "kctfork: Kotlin Compile Testing fork (GitHub)", "url": "https://github.com/ZacSweers/kotlin-compile-testing"},
  {"title": "Google compile-testing (GitHub)", "url": "https://github.com/google/compile-testing"},
  {"title": "Gradle TestKit (Gradle docs)", "url": "https://docs.gradle.org/current/userguide/test_kit.html"},
  {"title": "KSP2 introduction (google/ksp docs)", "url": "https://github.com/google/ksp/blob/main/docs/ksp2.md"}
 ]
}
out = ROOT / "content/lessons/ksp-08.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
