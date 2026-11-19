# Track: ksp, "Kotlin Symbol Processing (KSP)" (lab: labs/ksp, package workbench.ksp.lNN)

Part 5, "Code generation with KSP": this track, then the capstone cap5 (brief/outlines/cap5.md).
The user asked for this part in their own words: write it as if the reader has no knowledge of what KSP is
or how it works; build the intuition for it and for how and where it is used well; give good labs to get a
real grasp of it and build muscle memory.

## Read first

1. brief/REWRITE.md (the book voice, the lesson shape: opening, closing, sections, recap, humor dose) and the
   venkat-voice skill it names. New lessons are written straight in that voice; there is no older version.
2. brief/VOICE.md and brief/BRIEF.md (the lesson contract, the Java and Kotlin pair rule, banned words,
   sources, quiz "from" rule). site/validate.py must pass with no errors.
3. brief/outlines/ksp-labs.md: how the KSP lab modules work (labs/ksp, labs/ksp/annotations, labs/ksp/app),
   the kctfork test pattern, the stub style, the commands, the exact log and error formats. Copy its patterns.
4. Research notes, your source of truth: research_notes/Kotlin Symbol Processing/ksp_mechanics.md (the API,
   rounds, deferral, incremental, options, kapt) and ksp_ecosystem_testing.md (KotlinPoet, kctfork, the javac
   annotation processing mapping, real libraries, mistakes, lab ideas). Anything marked [Unverified] must not be
   stated as fact. Prove claims with the labs: a demo's real output beats a quote.
5. Two finished lessons for tone and length: content/lessons/conc-02.json and content/lessons/kt-06.json (the
   kt-06 lesson already has one short KSP section; this track is the full story).

## The reader

A complete newcomer to KSP and to annotation processing. They read basic Kotlin and Java. They have never
written a Gradle plugin, never seen a compiler API, and don't know the words "symbol", "annotation processor",
"code generation" or "round". Define each one in a plain sentence the first time it appears in each lesson.
They have finished Parts 1 to 4, so you may call back to the Part 4 capstone (cap4: a small dependency
injection container that finds and wires classes by reflection while the program runs) and to kt-06 (compiler
plugins), always with a one-sentence reminder, never as required knowledge.

## One picture for the whole track: moving house

Set it up in plain words before using it: a family packs their home into boxes before moving day.

- Your source files are sealed boxes. The label on top lists what is inside: the class name, the properties
  with their types, the function names and parameters. Those are the declarations. The packing inside (the
  function bodies, the expressions) stays sealed.
- An annotation is a sticky note on a box: "make an inventory card for this one".
- A processor is a helper with a clipboard. The clipboard is the Resolver: "show me every box with this sticky
  note". The helper reads labels, never opens a box, never relabels or repacks one (KSP can't see bodies and
  can't change existing code), and writes NEW cards and lists (generated files) that travel with the move and
  get compiled with your code.
- The moving company that sends the helper is the provider (SymbolProcessorProvider); the job sheet you hand it
  is the processor options (ksp { arg(...) }); the helper's notes to you ("box 7 has a sticky note but no
  label") are KSPLogger messages, pointing at the exact box (file and line).
- Rounds: after a pass, the helpers check the new cards and boxes they just made for sticky notes too.
  Deferral: a box whose label mentions something not packed yet (a type another processor will generate) is set
  aside until the next pass.
- Incremental builds: next weekend you repack one box. Its own card is redone (isolating output), but the
  master list of all boxes must be redone too (aggregating output). A helper who forgot to write down which
  boxes a card came from (Dependencies) leaves a stale card behind.
- kapt is a helper who can only read labels written in Java, so every label is first copied out in Java
  (stubs): that copying is the slowness. Reflection is unpacking and checking boxes at the new house, every
  time the program starts. A compiler plugin (kt-06) is a mover who repacks boxes: more power, more risk.
- KotlinPoet is a label printer instead of handwriting: it knows the right abbreviations (imports), spells
  nullable and generic types correctly, and never smudges.
- Testing a processor is a practice pack in an empty room: compile a few lines in memory and look at the cards.

Say where the picture breaks each time it does (for example: a real helper could peek inside a box; KSP truly
cannot). Map each mechanism part by part, out loud, once per lesson.

## The running example: MoveMate

One small app that helps a family move house runs through every lesson and lab. Its classes (use these names
and shapes, so lessons agree; a lesson may add a class when it needs one):

```kotlin
data class Box(val label: String, val room: String, val weightGrams: Int, val fragile: Boolean = false)
data class Lamp(val name: String, val bulbs: Int, val shade: String?)
class Bookshelf(val shelves: Int, val books: List<String>)
data class Plant(val kind: String, val potLitres: Double, val waterEveryDays: Int = 7)
```

Generated outputs used across the track (keep the formats identical everywhere):
- Inventory card (`@Inventory`): `fun Lamp.inventoryCard(): String` returning
  `Lamp: name=desk lamp, bulbs=1, shade=null` (class simple name, a colon, then `prop=value` pairs in
  declaration order of the primary constructor properties, joined with ", ").
- Label (`@Label`, lesson 3): the typed shape, for example `Lamp(name: String, bulbs: Int, shade: String?)`.
- Builder (`@Builder`, lessons 4 and 5): `LampBuilder` with one setter per constructor property returning the
  builder, and `build()`.
- Master list (lesson 7): one aggregating file listing every `@Inventory` class.

No money, payments, banks or accounts anywhere in this part.

## Both languages

Labs are Kotlin (KSP processors are written in Kotlin in practice). Every code sample in the prose still comes
as a Java and Kotlin pair. For processor code the Java twin is the closest Java equivalent, a javac annotation
processor (javax.annotation.processing: AbstractProcessor, RoundEnvironment, Filer, Messager, Elements and
TypeMirror, JavaPoet for KotlinPoet), with a first-line comment that says so, for example
`// Closest Java equivalent: a javac annotation processor`. For code that USES generated code, the Java twin is
Java calling the same generated Kotlin (it compiles to ordinary classes), or a Java class with an
APT-generated helper. Use the research notes' mapping table; never invent javax API names. Where nothing fits,
use a `solo` fence (at most 3 per lesson). Say once per lesson, plainly, that Java has had annotation processors
since Java 6 and that KSP is Kotlin's own, faster way to do the same job for Kotlin code.

## Versions

Kotlin 2.4.21, KSP 2.3.14 (KSP2), KotlinPoet and kotlinpoet-ksp 2.4.0, kctfork 0.14.0, Gradle 9.8.2, JUnit
6.1.3, AssertJ 3.27.7, JDK 25 running the build with release 21. ksp-labs.md lists anything pinned. Don't add
dependencies beyond those in labs/ksp/build.gradle.kts without saying why in your final message.

## Labs: build the muscle memory

Every lesson's lab is a processor the reader writes in labs/ksp/src/main/kotlin/workbench/ksp/lNN, with the
reference answer in src/solution, tests in src/test (kctfork: compile small source strings with the processor,
check the generated text, the messages, and call the generated code), demos in src/demo, and the real-build
playground in labs/ksp/app. Each lesson's package is self-contained: if a lesson builds on the previous lab, copy
what it needs into its own package as given code and say so in the lab steps.

Muscle memory comes from repetition with small changes. Every lab follows the same five moves, named the same
way in every lesson's lab steps so the reader learns the rhythm:
1. Find: ask the Resolver for the annotated symbols.
2. Check: reject what you can't handle, with a logger error on the exact symbol.
3. Read: walk the declaration you need (properties, types, annotation arguments).
4. Write: generate the file (strings in lessons 1 and 2, KotlinPoet from lesson 4), with correct Dependencies.
5. Prove: run the tests, then run it in a real build (labs/ksp/app) and open the generated file.
Each lab also has one "from memory" step: write a small piece again without looking (the drill can be this).
Stubs follow ksp-labs.md's stub style so an unfinished processor never breaks the app build.

## Lessons

- ksp-01 Code that writes code: what KSP is and where it runs. Opening: MoveMate prints an inventory card for
  each kind of thing being moved; we write `inventoryCard()` by hand for Box, Lamp, Bookshelf and Plant, then
  add a property to Lamp and forget the card: the card is now wrong and nothing complains (fail in public, with
  real output). Three ways out, each with one honest word of credit and one flaw: keep writing by hand (drift),
  reflection while the program runs (works; show it with real output and a timing; costs run time, no check
  until it runs, needs every box unpacked at the new house), generate the code during the build. Define
  annotation, build, compile time, run time, code generation, annotation processor, KSP. Then watch a ready-made
  processor (the track's solution processor for `@Inventory`) run in labs/ksp/app: `./gradlew :ksp:app:kspKotlin`,
  open build/generated/ksp/..., read the card function. Where KSP sits: a Gradle task that runs before the Kotlin
  compile; its output joins the compile. The two limits, stated as facts with the docs' words: KSP reads
  declarations, not bodies; it adds new files, never edits yours. The Java side: javac annotation processors,
  which Java has had since Java 6; KSP is the Kotlin-native helper (kapt in one sentence; lesson 9 returns to
  it). Lab: the reader first does the helper's job by hand (write the exact card function for two classes so the
  given tests pass), then writes the reflection version, then compares both to the generated card in the app;
  tests check all three agree. Muscle memory: the card format and where generated files live.
- ksp-02 Your first processor: from a sticky note to a generated file. The smallest processor that works,
  built rung by rung: a provider and a processor that only logs "round 1" (and see it in the build output), then
  `resolver.getSymbolsWithAnnotation(fully qualified name)` and logging each class name, then writing one file
  per class with `codeGenerator.createNewFile(Dependencies(false, file), package, name)` and a plain string
  template. The services file under META-INF/services and what happens without it (the exact symptom). Why the
  processor lives in its own module (it must be compiled before it can run on your code). `Dependencies` in one
  sentence here, with a promise to return in lesson 7. Generating the same file twice: the exact error. Java
  twin: AbstractProcessor, getElementsAnnotatedWith, Filer. Lab: the `@Inventory` processor with string
  templates (the five moves), tests via kctfork, a demo that prints the generated file, then run it in the app
  with `-Pprocessors=mine`.
- ksp-03 Reading the labels: declarations, types and annotation arguments. The symbol tree from KSFile down:
  KSClassDeclaration (classKind, modifiers such as data, primaryConstructor and its parameters with hasDefault),
  KSPropertyDeclaration, KSFunctionDeclaration, KSTypeReference versus KSType (resolve(), and why resolving is
  the expensive step), nullability, generic arguments (`List<String>`), annotation arguments (`@Room("kitchen")`,
  a Boolean, an enum, a KClass argument, and their defaults), visitors in one section. A Java class in the same
  module is visible too (Origin.JAVA). Prove the limit: the processor sees `fun totalWeight(): Int` but not the
  expression inside it. Java twin: TypeElement, VariableElement, ExecutableElement, TypeMirror, AnnotationMirror.
  Lab: the `@Label` processor printing the typed shape `Lamp(name: String, bulbs: Int, shade: String?)` for
  tricky classes (nullable, generics, default values, a property with `@Fragile`, a Java class), then reading
  `@Room` arguments. Muscle memory: resolve a type and print it correctly.
- ksp-04 Writing code that compiles: KotlinPoet. Start where lesson 2 stopped: extend the string template to
  generate a builder and let it fail in public (a type from another package needs an import, `List<Box?>?`, a
  nested class, a property named `object` or `in`). Then KotlinPoet: FileSpec, TypeSpec, FunSpec, PropertySpec,
  CodeBlock and the %T %N %S %L placeholders; kotlinpoet-ksp's toClassName() and toTypeName(); writeTo with the
  right originating files. Read the generated code aloud. Java twin: JavaPoet (TypeSpec, MethodSpec, JavaFile).
  Lab: the `@Builder` processor generating `LampBuilder` with KotlinPoet; tests compile and use the builder for
  each MoveMate class plus edge cases (nullable, defaults, generics, a type from another package). Muscle
  memory: the KotlinPoet calls for a class, a property, a function and a parameter.
- ksp-05 When the label is wrong: errors, validation and messages that help. The builder processor meets bad
  input (an interface, an object, a class with a private constructor, no primary constructor). The ladder: a
  crash with a stack trace from inside the processor (show it), then a vague error, then `logger.error(message,
  symbol)` pointing at the exact file and line (show the real Gradle line from ksp-labs.md), then reporting every
  problem in one build instead of stopping at the first, then warnings versus errors. validate() for symbols whose
  types can't be resolved yet, introduced here with a promise for lesson 6. What a good message says (what is
  wrong, where, how to fix it). Java twin: Messager.printMessage(Diagnostic.Kind.ERROR, message, element). Lab:
  add the checks to the builder processor; tests assert the compile fails, the message text, and the file and
  line. Muscle memory: check before you read.
- ksp-06 Several passes: rounds, generated code and deferral. A processor whose output carries a sticky note
  (for example `@Moving` on a class generates a `<Name>Receipt` data class annotated `@Inventory`, which needs
  its own card in the next round), and a class whose property type is generated by another processor, so it
  can't be resolved in round 1. What a round is; how generated files are processed in the next round; returning
  deferred symbols from process(); validate(); what happens when a symbol stays deferred to the end (the exact
  behaviour from the notes, proved in a test); finish(). Log the round number to make the passes visible.
  Java twin: javac rounds and processingOver(). Lab: both processors, with tests that count rounds from the log
  and check the final outputs, plus one test for the never-resolved case.
- ksp-07 Incremental builds: isolating and aggregating outputs, and processor options. Lesson 2's promise
  about Dependencies, paid off. The master list: one file listing every `@Inventory` class. Show in labs/ksp/app
  with ksp.incremental.log what happens when one source file changes, first with correct Dependencies, then
  with a deliberately wrong declaration that leaves a stale list (real log output; the demo must actually show
  it). Isolating versus aggregating in plain words; Dependencies.ALL_FILES; KotlinPoet's originating files.
  Processor options: `ksp { arg("movemate.listName", "MovingDayList") }` read from environment.options, with a
  clear error when a required option is missing. Java twin: Gradle's isolating and aggregating annotation
  processor categories (META-INF/gradle/incremental.annotation.processors) and getOptions(). Lab: the master
  list processor with correct Dependencies and an option; tests for the list and the option; a Try-it in the app
  for the incremental log.
- ksp-08 Testing a processor like a library author. The reader has run tests since lesson 2; now they write
  their own. Compile source strings in memory with kctfork; check the exit code, the messages, the generated
  text (golden files: a stored expected file compared on each run, with a way to update it), and load and call
  the generated code through the result's class loader. Testing errors by file and line. When a real Gradle
  build test (TestKit) is worth its cost (incremental behaviour, the services file). Debugging: logging, and
  reading the generated file first. Java twin: Google's compile-testing. Lab: a small reusable test harness the
  reader writes in src/main (compile, read generated files, collect errors with line numbers, call a generated
  function), checked by tests that run it against the earlier processors; plus golden-file tests for the builder.
  Muscle memory: the four checks every processor test makes.
- ksp-09 Choosing the tool: KSP, reflection, kapt and compiler plugins in the real world. A decision lesson
  with evidence. Replace MoveMate's reflection-based cards with generated ones and measure (first call and many
  calls, labeled as loaded-machine numbers). When reflection is fine; when a compiler plugin is needed (it must
  change your code, as kotlinx.serialization and all-open do: link to kt-06); when kapt is still needed (a
  processor that only exists for Java) and how to migrate a library from kapt to KSP in Gradle. Real libraries
  that ship KSP processors, as a short aside after the idea (Room, Moshi, Dagger and Hilt, Koin Annotations,
  kotlin-inject, others from the notes, each in one plain sentence). KSP2 and version notes; multiplatform in
  one section (per-target ksp configurations). Lab: port a small javac annotation processor (given, in Java) to a
  KSP processor that generates the same output, with tests comparing both outputs; this drills the mapping
  between the two APIs. Close the track by handing off to the capstone.

## Videos

One video per lesson, made later with the venkat-style-video skill (brief/VIDEO.md). Register nothing yourself.
In your final message, suggest for each lesson the one section a video should attach to and the moment in it
that most needs a moving picture.

## Track file

The writer of the last batch writes content/tracks/ksp.json (intro, cheatsheet, recap, quiz) in the same voice,
following the other track files. The intro states versions, the lab commands, and the moving-house picture.
