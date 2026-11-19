import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
read = lambda p: (ROOT / p).read_text()
APP = "labs/ksp/app/src/l05"
LAB = "labs/ksp/src"
DEMO = "./gradlew :ksp:demo -Pmain=workbench.ksp.l05.demo."
APPDEMO = "./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l05."


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


def app_demo(kt, java):
    """A Kotlin program in the real-build playground and its runnable Java twin."""
    return {"lang": "kotlin", "title": f"{kt}.kt", "src": read(f"{APP}/kotlin/workbench/ksp/app/l05/{kt}.kt"),
            "run": APPDEMO + kt + "Kt", "file": f"{APP}/kotlin/workbench/ksp/app/l05/{kt}.kt",
            "alt": {"lang": "java", "title": f"{java}.java", "src": read(f"{APP}/java/workbench/ksp/app/l05/{java}.java"),
                    "run": APPDEMO + java, "file": f"{APP}/java/workbench/ksp/app/l05/{java}.java"}}


def rung(i, cls, title, message):
    x, y = 20 + 110 * i, 252 - 58 * i
    cx = x + 115
    arrow = "" if i == 4 else f'<line class="ln" x1="{x + 175}" y1="{y - 2}" x2="{x + 175}" y2="{y - 16}" marker-end="url(#arr)"/>'
    return (f'<rect class="{cls}" x="{x}" y="{y}" width="230" height="40" rx="8"/>'
            f'<text class="t-s" x="{cx}" y="{y + 16}" text-anchor="middle">{title}</text>'
            f'<text class="t-s t-code" x="{cx}" y="{y + 32}" text-anchor="middle">{message}</text>' + arrow)


FIG = (
    '<svg viewBox="0 0 700 330" role="img" aria-label="A ladder of five rungs, from a crash with no file and line, through a vague error and a precise error on the symbol, to every problem in one build and a warning">'
    + rung(0, "box-bad", "1. the processor crashes", "NullPointerException")
    + rung(1, "box-dim", "2. a vague error", "@Builder can't build this")
    + rung(2, "box-b", "3. an error on the symbol", "Wardrobe.kt:6: ... an interface")
    + rung(3, "box-a", "4. every problem, one build", "4 messages, 1 failed build")
    + rung(4, "box-ok", "5. a warning, build goes on", "Plant.kt:9: ... default value")
    + '<text class="t-s t-m" x="350" y="318" text-anchor="middle">each rung changes one thing: a check, a symbol, no early stop, a second kind of message</text>'
    '</svg>'
)

# ---------------------------------------------------------------- opening
OPENING = """Back to the move. A family is packing sealed boxes, each with a label, and a helper with a clipboard reads the labels and writes new cards. A good helper does more than carry boxes. When something is wrong, they tell you which box, and what to do about it. A bad one drops the clipboard and walks off the job.

In the last lesson, our helper learned to print a builder for each class marked `@Builder`, with KotlinPoet doing the careful spelling. Every class we gave it had a primary constructor to call. Real code is less polite: someone puts `@Builder` on an interface, an `object`, or a class with a private constructor. Lesson 4's processor meets the interface, and the whole build stops with `java.lang.NullPointerException (no error message)`. Which is accurate, and no help at all.

In this lesson, we'll climb from that crash to a message that names the file, the line, what's wrong and how to fix it. Then we'll report every problem in one build, and set aside what can't be read yet. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_CRASH = """// Closest Java equivalent: a javac processor that assumes every element is a class with a constructor
TypeElement type = (TypeElement) element;
ExecutableElement constructor = ElementFilter.constructorsIn(type.getEnclosedElements()).get(0);
// an interface has no constructor, so get(0) throws, deep inside the processor"""
K_CRASH = """// Naive: lesson 4 assumed every @Builder class has a primary constructor
fun constructorParameters(cls: KSClassDeclaration): List<KSValueParameter> =
    cls.primaryConstructor!!.parameters"""

S0 = """Let's give lesson 4's processor something it didn't expect. A symbol is KSP's object for one declaration in your code: a class, a property, a function or a parameter. The `@Builder` annotation may go on any class-like declaration, and to Kotlin an interface, an `object` and an `enum class` are all class-like. So this compiles, and the processor gets its symbol:

```text
@Builder
interface Wardrobe
```

KSP hands the processor a `KSClassDeclaration` whose `classKind` is `INTERFACE`. An interface has no constructor at all, so `primaryConstructor` is `null`. Lesson 4 read it without looking:

""" + pair(J_CRASH, K_CRASH) + """

Here is the real build, `./gradlew :ksp:app:kspL04Kotlin`, with that interface added to lesson 4's playground:

```text
> Task :ksp:app:kspL04Kotlin FAILED
e: [ksp] java.lang.NullPointerException

* What went wrong:
Execution failed for task ':ksp:app:kspL04Kotlin' (registered by plugin 'org.jetbrains.kotlin.jvm').
> A failure occurred while executing com.google.devtools.ksp.gradle.KspAAWorkerAction
   > java.lang.NullPointerException (no error message)
```

No file, no line, no class name. Run it again with `--stacktrace`, and well over a hundred lines into the output you find the cause, `at workbench.ksp.l04.BuilderProcessorKt.constructorParameters(BuilderProcessor.kt:88)`. A stack trace is the list of method calls that were running when an exception was thrown, newest first. Every frame in it points into the processor, the helper's own code, and none of them at `Wardrobe.kt`, where the user made the mistake.

A thrown exception does more harm than a bad message. It stops KSP on the spot: the rest of the round doesn't run, other processors in the build never get their turn, and none of them is told. KSP's docs say `onError()`, the method a processor overrides to clean up after a failed run, is called after an error or an exception. In KSP 2.3.14 a thrown exception skips it.

In the picture, the helper dropped the clipboard in the hallway. The move is over, and the only clue is where the clipboard landed.

**A crash shows where the processor broke, not where the user went wrong. Check before you read.**

The first fix, then, is a check. The harder question is what the check should say."""

# ---------------------------------------------------------------- section 1
J_REPORT = """// Closest Java equivalent: a javac annotation processor reporting through the Messager
Messager messager = processingEnv.getMessager();

// rung 2, vague: no element, so javac can't say where
messager.printMessage(Diagnostic.Kind.ERROR, "@Builder can't build this");

// rung 3, precise: what is wrong and how to fix it, on the element itself
messager.printMessage(Diagnostic.Kind.ERROR,
        "@Builder needs a class to build, but " + element.getSimpleName() + " is an interface. "
                + "Put @Builder on a class.",
        element);"""
K_REPORT = """// rung 2, vague: no symbol, so KSP can't say where
logger.error("@Builder can't build this")

// rung 3, precise: what is wrong and how to fix it, on the symbol itself
logger.error(
    "@Builder needs a class to build, but ${describe(cls)}. Put @Builder on a class with a primary constructor.",
    cls,
)"""

S1 = """A processor talks to you through `KSPLogger`, which KSP passes in when it creates the processor. It has `error`, `warn`, `info` and `logging`, from loudest to quietest, and each takes a message and, optionally, a symbol. Gradle shows `warn` and `error` by default; `info` needs `--info`. Java's annotation processors, which javac has run since Java 6, have the same tool, the `Messager`, with `printMessage(kind, message, element)`. KSP is Kotlin's own, faster way to do their job for Kotlin code. Here are two rungs of the ladder in both languages:

""" + pair(J_REPORT, K_REPORT) + """

The vague rung is already better than the crash: the build fails with a sentence instead of an exception. But the Try it shows what that sentence looks like with three bad classes in the build:

```text
=== 2. a check with a vague message: COMPILATION_ERROR
e: [ksp] @Builder can't build this
=== 3. a precise message on the symbol: COMPILATION_ERROR
e: [ksp] Crate.kt:6: Crate has no primary constructor
```

"This" could be any of them. Give the logger the symbol, and KSP adds the where: the file and the line, in front of your message. In a real Gradle build the path is absolute, `e: [ksp] /…/labs/ksp/app/src/l05/kotlin/workbench/ksp/app/l05/Wardrobe.kt:6: ...`, and there's no column. A good editor turns that path into a link.

Look closely at the line number. In the lab's test, `@Builder` sits on line 5 and `interface Wardrobe` on line 6, and KSP reports line 6. The location of a symbol is its declaration's line, not its annotation's. In the picture, the helper's note goes on the box itself, not on the sticky note. Tests that expect the annotation's line fail, and the lab's tests count from the declaration.

The symbol says where, so your words only have to say two things: what is wrong, and how to fix it. "@Builder needs a class to build, but Wardrobe is an interface. Put @Builder on a class with a primary constructor." Read it as the user would, with no idea how the processor works. It names the annotation, the class and its kind, and the next step, and it uses no word from KSP's API.

**Every error names its symbol. The symbol is the where; your sentence is the what and the how.**

Rung 3 still has a flaw, and the output shows it: it reported `Crate` and stopped, though `Wardrobe` and `Settings` were just as wrong."""

# ---------------------------------------------------------------- section 2
J_LOOP = """// Closest Java equivalent: report each bad element, then keep going
for (Element element : roundEnv.getElementsAnnotatedWith(Builder.class)) {
    if (!check(element)) continue;        // reported; the next element still gets its turn
    writeBuilder((TypeElement) element);
}
return false;"""
K_LOOP = """fun processBuilders(resolver: Resolver): List<KSAnnotated> {
    val symbols = resolver.getSymbolsWithAnnotation(Builder::class.qualifiedName!!).toList()
    val (ready, later) = symbols.partition { it.validate(apiFeatures = apiFeatures) }
    for (symbol in ready) {
        if (!check(symbol)) continue          // reported; the next symbol still gets its turn
        builderFile(symbol as KSClassDeclaration).writeTo(codeGenerator, aggregating = false)
    }
    return later
}"""

S2 = """A processor that stops at the first problem makes the user play a slow game: fix one class, rebuild, meet the next error, fix that, rebuild again. Three bad classes cost three builds. Stopping early was our choice, though, not KSP's. `logger.error` doesn't stop anything: it marks the run as failed, and the round goes on. Every processor finishes the round, and then KSP starts no new one. It calls `onError()` on each processor instead of `finish()`, and Gradle fails the task with `KSP failed with exit code: PROCESSING_ERROR`.

So the fix for rung 3 is one word, `continue` instead of `return`:

""" + pair(J_LOOP, K_LOOP) + """

javac works the same way: its `RoundEnvironment` docs say that if a processor raises an error, the current round runs to completion. Here is lesson 5's processor in the real build, with `Wardrobe` and `Crate` added to the playground (paths shortened):

```text
> Task :ksp:app:kspL05Kotlin FAILED
e: [ksp] /…/l05/Wardrobe.kt:6: @Builder needs a class to build, but Wardrobe is an interface. Put @Builder on a class with a primary constructor.
e: [ksp] /…/l05/Wardrobe.kt:9: Crate has no primary constructor, so CrateBuilder doesn't know what to pass. Declare the properties in one: class Crate(val label: String).

> A failure occurred while executing com.google.devtools.ksp.gradle.KspAAWorkerAction
   > KSP failed with exit code: PROCESSING_ERROR
```

Two problems, one build. The good classes still got their builders in that round, as the lab's test checks, even though the build failed. In the picture, the helper walks the whole house and leaves a note on every bad box before calling you, instead of calling you once per box.

Not every problem should fail the build. `Plant`'s `waterEveryDays = 7` is legal Kotlin, and the builder works; it just can't use the default, because KSP shows a default exists and never its value. That calls for a warning, `logger.warn(message, param)`, on the parameter's own line: `w: [ksp] /…/l05/MoveMate.kt:21: PlantBuilder can't see the default value of waterEveryDays, so build() will require it. Set it on the builder.` The build goes on. Use an error when the output would be wrong or missing, and a warning when it works but surprises. Two cautions: `-q` hides warnings completely, and `ksp { allWarningsAsErrors = true }` turns them into errors.

One quiet trap sits in `logger.exception(e)`, which sounds like the polite way to report a caught exception. In KSP 2.3.14 it prints `e: [ksp]` and the exception's text, and the build passes. If you mean "fail", call `logger.error`.

**Report every problem you can see, then let the build fail once.**

Every check so far looked at things KSP can see right away. One kind of problem can't be checked yet at all."""

# ---------------------------------------------------------------- section 3
J_VALID = """// Closest Java equivalent: javac has no validate(); look for error types yourself
boolean ready = ElementFilter.fieldsIn(type.getEnclosedElements()).stream()
        .noneMatch(field -> field.asType().getKind() == TypeKind.ERROR);
if (!ready) waiting.add(type.getQualifiedName().toString());   // look it up again next round"""
K_VALID = """val symbols = resolver.getSymbolsWithAnnotation(Builder::class.qualifiedName!!).toList()
val (ready, later) = symbols.partition { it.validate(apiFeatures = apiFeatures) }
// ... check and write the ready ones, as before
return later        // KSP offers these again in the next round"""

S3 = """Here is a class whose label mentions a type that doesn't exist. It may be a typo, or a type that another processor hasn't written yet:

```text
@Builder
class Parcel(val label: String, val sticker: Sticker)
```

KSP doesn't stop at the unknown `Sticker`; it hands the processor a type it calls an error type, one the compiler can't resolve. The checks pass, because `Parcel` is a class with a public primary constructor. Then KotlinPoet's `toTypeName()` meets the error type and throws:

```text
=== without validate(): lesson 4's processor: INTERNAL_ERROR
java.lang.IllegalArgumentException: Error type '<ERROR TYPE: Sticker>' is not resolvable in the current round of processing.
```

It's a crash again, inside our processor, and the message even says what to do: wait. `validate()` is KSP's check for exactly this. It walks every type a declaration mentions (its supertypes, its properties' types, its functions' parameters) and returns `false` if any of them can't be resolved yet. The symbols that fail go back to KSP as the return value of `process()`, and KSP offers them again in the next round. Setting a symbol aside like this is called deferral:

""" + pair(J_VALID, K_VALID) + """

In KSP 2.3.14, write `validate(apiFeatures = apiFeatures)`, passing the processor's own `apiFeatures`. Plain `validate()`, the spelling in the official quickstart, has been deprecated since 2.3.12 and compiles with a warning. With validation in place, the same input gives:

```text
=== with validate(): the lab's processor: COMPILATION_ERROR
e: Parcel.kt:6:46 Unresolved reference 'Sticker'.
```

That's no crash. The error comes from the compiler, on the user's own line, about the user's own typo. In the picture, the helper set the box aside, because its label mentions something that isn't packed yet. The picture breaks a little here: a real helper could open the box and look. KSP can't, so it can only wait for the missing type to appear. `validate()` resolves the whole declaration tree, so it costs something; KSP's docs advise checking only what your output needs.

Our builder needs a second round only when someone else writes `Sticker`. Lesson 6 builds exactly that case, and finds a catch in what KSP 2.3.14 does with a symbol that stays set aside to the end.

Checks catch only what you thought of. Put `@Builder` on `abstract class Furniture(val legs: Int)`: it is a class, its constructor is public, and every check passes. Then the compiler rejects the generated code, `e: FurnitureBuilder.kt:14:35 Cannot create an instance of an abstract class.`, pointing at a file the user never wrote. Each such case is one more check, written before you read."""

# ---------------------------------------------------------------- closing
CLOSING = """We started with a helper who dropped the clipboard at the first interface, and a build that said only `NullPointerException`. Now every bad box gets its own note, `Wardrobe.kt:6: ...`, all in one pass. A box with an unknown word on its label waits instead of crashing the move.

In a processor of your own, search for `!!` and for `as` casts on anything you got from the Resolver. Each one is a place where a check belongs, before the read.

Next, we'll give deferral a real job: a processor whose output carries its own sticky note, and a class that can't be read until a later pass. What happens to a symbol that stays set aside forever?"""

L = {
 "id": "ksp-05",
 "title": "Errors, validation and helpful messages",
 "minutes": 40,
 "goal": "By the end you can turn a crash inside a processor into a `logger.error` on the exact file and line, report every problem in one build, choose between an error and a warning, write a message that says what is wrong and how to fix it, and set aside a symbol that can't be read yet with `validate()`.",
 "opening": OPENING,
 "warmup": {
  "q": "A processor finds three bad `@Builder` classes. For the first one it calls `logger.error(message, symbol)` and then carries on with its loop. What happens next?",
  "options": ["KSP stops the processor at once, so the other two classes are never looked at",
              "The round goes on: the processor checks the other classes and writes what it can, then the build fails once",
              "The error is only printed, and the build passes",
              "KSP retries the bad class in the next round"],
  "answer": 1,
  "why": "`logger.error` marks the run as failed but stops nothing. The round runs to the end, then KSP starts no new round, calls `onError()` and fails the Gradle task with `PROCESSING_ERROR`. A thrown exception is what stops everything at once, which is why the first option is tempting: it describes a crash, not an error report. The third option describes `logger.exception(e)`, which in KSP 2.3.14 prints but doesn't fail the build."
 },
 "sections": [
  {
   "h": "Lesson 4's builder meets an interface and crashes",
   "body": S0,
   "try": {
    "title": "Crash the lesson 4 processor in a real build",
    "minutes": 3,
    "steps": [
     "Create `labs/ksp/app/src/l04/kotlin/workbench/ksp/app/l04/Wardrobe.kt` with `package workbench.ksp.app.l04`, `import workbench.ksp.annotations.Builder`, and `@Builder interface Wardrobe` on two lines.",
     "Predict what the build will tell you. Then run `./gradlew :ksp:app:kspL04Kotlin` from `labs/`.",
     "Run it again with `--stacktrace` and search the output for `Caused by: java.lang.NullPointerException`. Which file do the frames below it name? Then delete `Wardrobe.kt`."
    ],
    "expect": "The task fails with `e: [ksp] java.lang.NullPointerException` and `> java.lang.NullPointerException (no error message)`: no file, no line, no class. With `--stacktrace`, the `Caused by` block lists `constructorParameters(BuilderProcessor.kt:88)`, then `builderType`, `builderFile` and `processBuilders`, all inside the processor. `Wardrobe.kt` appears nowhere in the stack trace. Once the file is gone, the task passes again."
   }
  },
  {
   "h": "From a vague error to the exact file and line",
   "body": S1,
   "figure": {"svg": FIG, "caption": "The ladder this lesson climbs: each rung changes one thing about how the processor reports a problem."},
   "try": {
    "title": "Climb the ladder in one run",
    "minutes": 4,
    "steps": [
     "Open `labs/ksp/src/demo/kotlin/workbench/ksp/l05/demo/ErrorLadderDemo.kt`. Rungs 1 to 3 are small processors in that file (`Crashing`, `Vague`, `Precise`); rung 4 is the lab's processor. All four get the same three bad classes and a `Plant` with a default value.",
     "Predict what each rung prints. Then run `" + DEMO + "ErrorLadderDemoKt`.",
     "In `Vague`, pass `cls` as a second argument to `logger.error` and run again. What does the message gain, and what does it still lack?"
    ],
    "expect": "Rung 1 ends with `INTERNAL_ERROR` and `java.lang.NullPointerException` plus frames inside `BuilderProcessor.kt`. Rung 2 prints `e: [ksp] @Builder can't build this`, rung 3 `e: [ksp] Crate.kt:6: Crate has no primary constructor`, and both stop there. Rung 4 prints a warning for `Plant.kt:9` and three errors, `Crate.kt:6`, `Wardrobe.kt:6` and `Wardrobe.kt:9`, each saying what is wrong and how to fix it. With `cls` added, rung 2 gains `Crate.kt:6:` but still doesn't say what is wrong. The demo shortens the paths to file names; the run takes about 10 seconds.",
    "refs": [{"title": "Messager (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.compiler/javax/annotation/processing/Messager.html", "kind": "docs"}]
   }
  },
  {
   "h": "Every problem in one build, and warnings for what you can't do",
   "body": S2,
   "try": {
    "title": "Read your messages in a real build",
    "minutes": 4,
    "steps": [
     "Run `./gradlew :ksp:app:kspL05Kotlin` from `labs/`. Note the two warnings, then run the programs below, which use the builders from Kotlin and from Java.",
     "Create `labs/ksp/app/src/l05/kotlin/workbench/ksp/app/l05/Wardrobe.kt` with a `@Builder interface Wardrobe` and a `@Builder class Crate { constructor(label: String) }` (package `workbench.ksp.app.l05`, `import workbench.ksp.annotations.Builder`). Predict the messages, then run `kspL05Kotlin` again.",
     "Delete `Wardrobe.kt`, and run `kspL05Kotlin` once more. Do the warnings come back?"
    ],
    "code": app_demo("Checks", "ChecksJava"),
    "expect": "The first run prints `w: [ksp] /…/MoveMate.kt:9: BoxBuilder can't see the default value of fragile ...` and the same for `waterEveryDays` on line 21, then `BUILD SUCCESSFUL`. Both programs print the fern plant and the plates box. With `Wardrobe.kt` added, the task fails with the two errors shown in this section, both in one build. The warnings may not repeat on later runs: KSP rereads only files that changed (lesson 7), so `MoveMate.kt` isn't processed again until you edit it.",
    "refs": [{"title": "RoundEnvironment (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.compiler/javax/annotation/processing/RoundEnvironment.html", "kind": "docs"}]
   }
  },
  {
   "h": "Setting aside what can't be read yet with validate()",
   "body": S3,
   "try": {
    "title": "Crash on an unknown type, then set it aside",
    "minutes": 3,
    "steps": [
     "Open `SetAsideDemo.kt` next to the ladder demo. It compiles `Parcel(val label: String, val sticker: Sticker)` twice: with lesson 4's processor, then with the lab's.",
     "Predict both outcomes. Then run `" + DEMO + "SetAsideDemoKt`.",
     "In the demo's source string, add `class Sticker(val text: String)` below `Parcel` and run again. What changes for each processor?"
    ],
    "expect": "Without `validate()`, the run ends with `INTERNAL_ERROR` and `IllegalArgumentException: Error type '<ERROR TYPE: Sticker>' is not resolvable in the current round of processing.` With it, there is no crash: KSP sets `Parcel` aside, processing ends, and the compiler reports `e: Parcel.kt:6:46 Unresolved reference 'Sticker'.` on the user's line. Once `Sticker` exists, both processors write `ParcelBuilder` and both runs end `OK`.",
    "refs": [{"title": "Multiple round processing (KSP docs)", "url": "https://kotlinlang.org/docs/ksp-multi-round.html", "kind": "docs"}]
   }
  }
 ],
 "compare": {
  "title": "Checking a symbol and reporting on it: javac's Messager and KSP's KSPLogger",
  "java": {"title": "BuilderProcessor.java (javac)", "src": """// Closest Java equivalent: a javac annotation processor
boolean check(Element element) {
    Messager messager = processingEnv.getMessager();
    if (element.getKind() != ElementKind.CLASS) {
        messager.printMessage(Diagnostic.Kind.ERROR,
                "@Builder needs a class to build, but " + element.getSimpleName() + " is not a class. "
                        + "Put @Builder on a class.", element);
        return false;
    }
    List<ExecutableElement> constructors = ElementFilter.constructorsIn(element.getEnclosedElements());
    if (constructors.stream().allMatch(c -> c.getModifiers().contains(Modifier.PRIVATE))) {
        messager.printMessage(Diagnostic.Kind.ERROR,
                element.getSimpleName() + "Builder can't call a private constructor. Make one public.",
                constructors.get(0));
        return false;
    }
    return true;
}"""},
  "kotlin": {"title": "BuilderProcessor.kt (KSP)", "src": """fun check(symbol: KSAnnotated): Boolean {
    if (symbol !is KSClassDeclaration || symbol.classKind != ClassKind.CLASS) {
        logger.error("@Builder needs a class to build, but ${describe(symbol)}. " +
            "Put @Builder on a class with a primary constructor.", symbol)
        return false
    }
    val name = symbol.simpleName.asString()
    val builder = builderName(symbol).simpleName
    val constructor = symbol.primaryConstructor
    if (constructor == null) {
        logger.error("$name has no primary constructor, so $builder doesn't know what to pass. " +
            "Declare the properties in one: class $name(val label: String).", symbol)
        return false
    }
    if (constructor.isPrivate()) {
        logger.error("$builder can't call $name's constructor, because it is private. " +
            "Make it internal or public, or remove @Builder.", constructor)
        return false
    }
    for (param in constructor.parameters.filter { it.hasDefault }) {
        logger.warn("$builder can't see the default value of ${nameOf(param)}, so build() will require it. " +
            "Set it on the builder.", param)
    }
    return true
}"""},
  "note": "Both report on an element, both land on the declaration's line, and both let the round finish after an error. The differences are in the details. javac prints `Wardrobe.java:4: error: ...` followed by the source line and a caret under the declaration; KSP prints the absolute path and the line, with no column and no source line. Java has no primary constructor, so the Java check looks through every constructor, where Kotlin asks for exactly one. And Kotlin's default values give the KSP version a warning with no Java twin: a Java constructor parameter can't have a default at all."
 },
 "worked": {
  "title": "Turn an unhelpful message into a good one, and pin it with a test",
  "steps": [
   {"say": "A teammate's processor reports a private constructor like this. Read it as a user who has never seen the processor's code, and list what's missing.",
    "code": "// before: true, but no class, no line, no next step\nif (constructor.isPrivate()) {\n    logger.error(\"constructor is private\")\n    return false\n}", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "// before: true, but no class, no line, no next step\nif (constructor.getModifiers().contains(Modifier.PRIVATE)) {\n    messager.printMessage(Diagnostic.Kind.ERROR, \"constructor is private\");\n    return false;\n}"},
   {"say": "Ask the three questions. Where? Pass the constructor as the symbol, so KSP adds the file and line. What? Name the builder and the class. How to fix it? Give the user a choice of next steps.",
    "code": "if (constructor.isPrivate()) {\n    logger.error(\n        \"$builder can't call $name's constructor, because it is private. \" +\n            \"Make it internal or public, or remove @Builder.\",\n        constructor,                       // where: Crate.kt:11\n    )\n    return false\n}", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "if (constructor.getModifiers().contains(Modifier.PRIVATE)) {\n    messager.printMessage(Diagnostic.Kind.ERROR,\n            builder + \" can't call \" + name + \"'s constructor, because it is private. \"\n                    + \"Make it public, or remove @Builder.\",\n            constructor);                  // where: the constructor's line\n    return false;\n}"},
   {"say": "Now pin it with a test, so the message never drifts back. The test compiles a small source in memory and checks the end of the path, the line and the text. The Java twin uses Google's compile-testing library, which has the same three checks built in.",
    "code": "val safe = SourceFile.kotlin(\"Crate.kt\", \"\"\"\n    package movemate\n\n    import workbench.ksp.annotations.Builder\n\n    @Builder\n    class Crate {\n        constructor(label: String)\n    }\n\n    @Builder\n    class Safe private constructor(val code: String)\n    \"\"\")\nval run = compileWithKsp(safe, processors = listOf(BuilderProcessorProvider()))\nassertThat(run.messages).containsPattern(\n    \"\"\"e: \\[ksp] \\S*/Crate\\.kt:11: SafeBuilder can't call Safe's constructor, because it is private\\.\"\"\")", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "JavaFileObject safe = JavaFileObjects.forSourceString(\"movemate.Safe\", \"\"\"\n    package movemate;\n    import workbench.ksp.annotations.Builder;\n    @Builder\n    public class Safe {\n        private Safe(String code) {}\n    }\n    \"\"\");\nCompilation compilation = javac().withProcessors(new BuilderProcessor()).compile(safe);\nassertThat(compilation).failed();\nassertThat(compilation).hadErrorContaining(\"can't call a private constructor\").inFile(safe).onLine(5);"},
   {"say": "Run it and watch it pass. Then change `:11:` to `:10:`, the line of `@Builder`, and watch it fail: KSP reports the declaration's line, not the annotation's. Put it back. The lab's tests check every message this way, which is how you'll know your `check` says exactly what it should.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Checks and messages for the @Builder processor",
  "minutes": 14,
  "files": [f"{LAB}/main/kotlin/workbench/ksp/l05/BuilderProcessor.kt", f"{LAB}/test/kotlin/workbench/ksp/l05/BuilderChecksTest.kt", f"{APP}/kotlin/workbench/ksp/app/l05/MoveMate.kt"],
  "run": "./gradlew :ksp:test --tests 'workbench.ksp.l05.*'",
  "steps": [
   "Open `BuilderProcessor.kt` in `labs/ksp/src/main/kotlin/workbench/ksp/l05/`. Lesson 4's processor is copied there as given code (`describe`, `builderFile` and the specs below it). Run the tests: all five fail, and the messages include `l05 not done yet: processBuilders: ...`.",
   "Find: in `processBuilders`, ask the Resolver, the clipboard KSP passes to `process`, for the `@Builder` symbols, as in lesson 4. Split them with `partition { it.validate(apiFeatures = apiFeatures) }`; the ones that aren't valid are what `processBuilders` returns.",
   "Check: write `check(symbol)`. Its KDoc lists the four rules in order and the exact message for each. Report each error on the exact symbol (the class, or the constructor when it is private) and each default-value warning on its parameter, and return `false` only for errors.",
   "Read and Write: for each valid symbol that passes `check`, call `builderFile(symbol as KSClassDeclaration).writeTo(codeGenerator, aggregating = false)`. After a failed check, `continue`: don't `return`.",
   "Prove: run the tests until all five pass. Then add a `@Builder interface Wardrobe` to `labs/ksp/app/src/l05/kotlin/workbench/ksp/app/l05/`, run `./gradlew :ksp:app:kspL05Kotlin -Pmine=l05`, read your own message with its full path, and delete the file again.",
   "From memory: do the drill below without looking at your code."
  ],
  "hints": [
   "The class check is `symbol !is KSClassDeclaration || symbol.classKind != ClassKind.CLASS`. `describe(symbol)` gives the middle of the message: `Wardrobe is an interface`.",
   "`symbol.primaryConstructor` is `null` both for an interface and for a class with only secondary constructors; by the time you test it, the first check has already ruled out interfaces.",
   "`isPrivate()` is an extension from `com.google.devtools.ksp`, already imported. Report the private case on `constructor`, not on the class: the test expects `Crate.kt:11`, the line where `Safe` and its constructor are declared.",
   "If the test for every problem finds fewer than five errors, look for a `return` inside your loop: one bad class is ending the round's work for the others."
  ],
  "done_when": "All five tests in `BuilderChecksTest` pass, and the real build prints your error for `Wardrobe` with its full path and line."
 },
 "drill": {
  "title": "Two checks, from memory",
  "minutes": 5,
  "prompt": "Close this page. Write `check(symbol: KSAnnotated): Boolean` with two rules: the symbol must be a class (`ClassKind.CLASS`), and its primary constructor must not be private. Each error says what is wrong and how to fix it, on the right symbol. Then write the javac version with `Messager`. Where does each message point?",
  "answer": {"lang": "kotlin", "src": "fun check(symbol: KSAnnotated): Boolean {\n    if (symbol !is KSClassDeclaration || symbol.classKind != ClassKind.CLASS) {\n        logger.error(\"@Builder needs a class to build, but ${describe(symbol)}. \" +\n            \"Put @Builder on a class with a primary constructor.\", symbol)      // the declaration's line\n        return false\n    }\n    val constructor = symbol.primaryConstructor ?: return true      // a missing constructor is another rule\n    if (constructor.isPrivate()) {\n        logger.error(\"${symbol.simpleName.asString()}Builder can't call the constructor, because it is private. \" +\n            \"Make it internal or public.\", constructor)                       // the constructor's line\n        return false\n    }\n    return true\n}",
             "alt": {"lang": "java", "title": "Messager", "src": "boolean check(Element element) {\n    Messager messager = processingEnv.getMessager();\n    if (element.getKind() != ElementKind.CLASS) {\n        messager.printMessage(Diagnostic.Kind.ERROR,\n                \"@Builder needs a class to build, but \" + element.getSimpleName() + \" is not a class.\",\n                element);                                                     // the declaration's line\n        return false;\n    }\n    for (ExecutableElement c : ElementFilter.constructorsIn(element.getEnclosedElements())) {\n        if (c.getModifiers().contains(Modifier.PRIVATE)) {\n            messager.printMessage(Diagnostic.Kind.ERROR,\n                    \"The builder can't call a private constructor. Make it public.\", c);   // the constructor's line\n            return false;\n        }\n    }\n    return true;\n}"}}
 },
 "recap": [
  "A thrown exception stops KSP at once and points into the processor, not at the user's code: `NullPointerException (no error message)`, no file, no line, and in KSP 2.3.14 no `onError()`.",
  "`logger.error(message, symbol)` prints `e: [ksp] <absolute path>:<line>: message`, on the declaration's line, not the annotation's. Without a symbol there is no where.",
  "`logger.error` doesn't stop the round: check every symbol, report each problem, write what you can, and the build fails once with `PROCESSING_ERROR`. Use `logger.warn` for what works but surprises; `logger.exception` doesn't fail the build.",
  "A good message says what is wrong and how to fix it, in the user's words; the symbol says where.",
  "`validate(apiFeatures = apiFeatures)` finds symbols whose types can't be resolved yet; return them from `process()` instead of handing an error type to KotlinPoet.",
  "The limit: checks catch only what you thought of. An abstract class passes every check here, and the compiler then rejects the generated builder in a file the user never wrote."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "In a source file, line 5 is `@Builder` and line 6 is `interface Wardrobe`. The processor calls `logger.error(message, symbol)` with Wardrobe's symbol. Which location does KSP print?",
   "options": ["`Wardrobe.kt:5`, the annotation's line", "`Wardrobe.kt:6`, the declaration's line", "`Wardrobe.kt:5:1`, with a column", "No location: interfaces have none"],
   "answer": 1, "why": "A symbol's location is its declaration's line, so the error lands on `interface Wardrobe`. KSP prints a path and a line but never a column. The first option is the common guess, and the reason tests written for the annotation's line fail."},
  {"q": "A processor throws `IllegalStateException` for the first bad class it meets. A second processor runs after it in the same build. What happens?",
   "options": ["Both processors finish the round, then the build fails", "The second processor runs, then `onError()` is called on both", "KSP stops at once: the second processor never runs, and in 2.3.14 no `onError()` is called", "KSP turns the exception into a warning and goes on"],
   "answer": 2, "why": "A thrown exception escapes KSP's round loop, so processing ends on the spot: later processors in that round don't run, and KSP 2.3.14 skips `onError()`, although its docs say it is called after an exception too. Gradle fails with the exception's message. `logger.error` is what lets the round finish, which is the first two options."},
  {"q": "A processor catches an exception and reports it with `logger.exception(e)`. What does the build do in KSP 2.3.14?",
   "options": ["It prints `e: [ksp]` and the exception's text, and the build passes", "It fails with `PROCESSING_ERROR`, like `logger.error`", "It hides the message unless Gradle runs with `--info`", "It rethrows the exception and fails with its stack trace"],
   "answer": 0, "why": "`logger.exception` only prints. It doesn't mark the run as failed, so `finish()` runs and the build passes. The `e:` prefix makes it look like an error, which is the trap. If the problem should fail the build, call `logger.error(message, symbol)`."},
  {"q": "`@Builder class Parcel(val label: String, val sticker: Sticker)`, and no `Sticker` exists anywhere. The processor sets invalid symbols aside with `validate()`. What does the user see?",
   "options": ["`IllegalArgumentException: Error type '<ERROR TYPE: Sticker>' ...` from inside the processor", "Nothing: the build passes and `ParcelBuilder` is generated", "A KSP error that says `Parcel` is invalid", "No KSP message; the compiler reports `Unresolved reference 'Sticker'` on `Parcel`'s line"],
   "answer": 3, "why": "`validate()` returns false, so `Parcel` is returned from `process()` and never reaches KotlinPoet. No new file appears, so processing ends after that round, and the compiler then reports the unknown type in the user's own source. The first option is what happens without `validate()`. Lesson 6 looks at what KSP itself says about a symbol that is still set aside at the end."},
  {"q": "From lesson 4: `PlantBuilder` requires `waterEveryDays` although `Plant` declares `waterEveryDays: Int = 7`. Why can't the processor use the default?",
   "options": ["KotlinPoet can't write default values", "KSP reads declarations, not expressions: it shows that a default exists, never its value", "Defaults exist only while the program runs, so no build tool can see them", "The builder could, but only with a `@Default` annotation"],
   "answer": 1, "why": "A default value is an expression, and KSP doesn't model expressions: `hasDefault` is all a processor learns. KotlinPoet could print a default if the processor knew one. The compiler does see the expression; KSP's model leaves it out on purpose. That is why lesson 5 reports the default as a warning on the parameter's line.",
   "from": "ksp-04"}
 ],
 "flashcards": [
  {"front": "What does a processor that throws an exception do to a KSP build?", "back": "Processing stops at once; later processors don't run, `onError()` is skipped (KSP 2.3.14), and Gradle fails with the exception's message, with no file or line."},
  {"front": "What does `logger.error(\"...\", symbol)` print in a Gradle build?", "back": "`e: [ksp] <absolute path>:<line>: ...`: an absolute path and the declaration's line, with no column."},
  {"front": "Does `logger.error` stop the round?", "back": "No. The round finishes and files are still written; then no new round starts, `onError()` runs instead of `finish()`, and the build fails with `PROCESSING_ERROR`."},
  {"front": "Error or warning for \"this works, but the builder can't use the default\"?", "back": "A warning (`logger.warn` on the parameter): the output is correct, just surprising. Errors are for output that would be wrong or missing."},
  {"front": "What makes `validate()` return false?", "back": "A type somewhere in the declaration (supertypes, property types, parameter types) that can't be resolved yet, an error type."},
  {"front": "How do you call `validate()` without a deprecation warning in KSP 2.3.14?", "back": "`symbol.validate(apiFeatures = apiFeatures)`, passing the processor's own `apiFeatures`. Plain `validate()` is deprecated since 2.3.12."},
  {"front": "What does `logger.exception(e)` do to the build in KSP 2.3.14?", "back": "Nothing: it prints `e: [ksp]` and the exception's text, and the build passes."}
 ],
 "terms": [
  {"term": "Symbol", "plain": "KSP's object for one declaration in your code: a class, a property, a function or a parameter."},
  {"term": "Stack trace", "plain": "The list of method calls that were running when an exception was thrown, newest first."},
  {"term": "KSPLogger", "plain": "The processor's way to report: `error`, `warn`, `info` and `logging`, each optionally on a symbol."},
  {"term": "Location", "plain": "Where a symbol is declared: a file and the declaration's line, which KSP prints before a message."},
  {"term": "Error type", "plain": "A type the compiler can't resolve, such as a typo or a type another processor hasn't written yet."},
  {"term": "validate()", "plain": "KSP's check that every type a declaration mentions can be resolved; false means the symbol isn't ready."},
  {"term": "Deferral", "plain": "Returning a symbol from `process()` so that KSP offers it again in the next round."},
  {"term": "onError()", "plain": "The method KSP calls on every processor after a round in which `logger.error` was used, instead of `finish()`."}
 ],
 "explain_back": {
  "prompt": "A teammate's processor fails the build with `java.lang.NullPointerException (no error message)` whenever someone puts its annotation on the wrong kind of class. Explain why that output can't help the user, and walk through how you'd change the processor.",
  "answer": "The processor read something it never checked, such as a primary constructor that an interface doesn't have, and the `!!` threw. A thrown exception stops KSP at once, and the only clue is a stack trace that points into the processor's own code, never at the user's file. So the user can't tell which class is wrong, or why. First I'd check before reading: is it a class, does it have a primary constructor, is that constructor callable? For each failed check I'd call `logger.error(message, symbol)` with the symbol, so KSP prints the file and the declaration's line. The message would say what is wrong and how to fix it, in the user's words. I'd `continue` instead of returning, so one build reports every bad class, and use `logger.warn` for things that work but surprise. Types that can't be resolved yet I'd catch with `validate(apiFeatures = apiFeatures)` and return from `process()`. Then a test would pin each message: the end of the path, the line, and the text."
 },
 "deeper": {
  "minutes": 8,
  "body": "When a run fails, KSP 2.3.13 and later also print follow-on errors from a quick type check of the round's new files, for example `e: [ksp] Greeter.kt:11: Unresolved reference 'helloFromGreeter'.` from the lab's smoke example, with a file name only and no folder. They are not your bug: code that uses a generated declaration was checked before the declaration existed. Fix the first error with a full path, and the follow-ons disappear.\n\nThe log levels map to Gradle's own. At the default level you see `warn` and `error`; `--info` adds `info`, and `--debug` adds `logging`. With `-q`, warnings disappear completely, so a processor that warns about something important should consider an error, or the `ksp { allWarningsAsErrors = true }` switch for teams that want warnings to stop the build.\n\nWhen a processor looks at things outside its own source set, the location can be missing. A class that comes from a compiled library has no file, so its location is `NonExistLocation` and its `containingFile` is `null`. A message logged on such a symbol has no path in front, and code that writes `containingFile!!` on a library class crashes. Check `symbol.origin` (`KOTLIN` and `JAVA` mean source code) before you rely on a file.\n\nOn the Java side, javac's `Messager` can also report on an annotation or one of its values, with the overloads `printMessage(kind, message, element, annotationMirror)` and `printMessage(kind, message, element, annotationMirror, annotationValue)`. Its Javadoc warns that such location hints \"may be unavailable or only approximate\"."
 },
 "sources": [
  {"title": "Multiple round processing: errors, onError and deferral (KSP docs)", "url": "https://kotlinlang.org/docs/ksp-multi-round.html"},
  {"title": "Java annotation processing to KSP reference (Kotlin docs)", "url": "https://kotlinlang.org/docs/ksp-reference.html"},
  {"title": "Messager (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.compiler/javax/annotation/processing/Messager.html"},
  {"title": "KotlinPoet: KSP interop, including error types (KotlinPoet docs)", "url": "https://square.github.io/kotlinpoet/interop-ksp/"}
 ]
}
out = ROOT / "content/lessons/ksp-05.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
