import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/ksp/src"
app = "labs/ksp/app/src/l01"
P = "kotlin/workbench/ksp/l01"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :ksp:demo -Pmain=workbench.ksp.l01.demo."


def demo(name):
    """Kotlin demo with its runnable Java twin."""
    k = f"{lab}/demo/kotlin/workbench/ksp/l01/demo/{name}.kt"
    j = f"{lab}/demo/java/workbench/ksp/l01/demo/{name}Java.java"
    return {"lang": "kotlin", "title": f"{name}.kt", "src": read(k), "run": RUN + name + "Kt", "file": k,
            "alt": {"lang": "java", "title": f"{name}Java.java", "src": read(j), "run": RUN + name + "Java", "file": j}}


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


FIG = (
    '<svg viewBox="0 0 700 290" role="img" aria-label="Where KSP runs: your source files go to the kspL01Kotlin task, '
    'which writes new card files into build/generated/ksp/l01; the compileL01Kotlin task then compiles your files and the '
    'cards together into class files">'
    '<rect class="box" x="20" y="30" width="200" height="64" rx="8"/>'
    '<text class="t" x="120" y="56" text-anchor="middle">your classes, src/l01</text>'
    '<text class="t-s t-m" x="120" y="78" text-anchor="middle">sealed boxes with labels</text>'
    '<line class="ln" x1="224" y1="62" x2="252" y2="62" marker-end="url(#arr)"/>'
    '<rect class="box-a" x="258" y="30" width="184" height="64" rx="8"/>'
    '<text class="t t-code" x="350" y="56" text-anchor="middle">kspL01Kotlin</text>'
    '<text class="t-s t-m" x="350" y="78" text-anchor="middle">the helper reads labels</text>'
    '<line class="ln" x1="446" y1="62" x2="474" y2="62" marker-end="url(#arr)"/>'
    '<rect class="box-b" x="480" y="30" width="200" height="64" rx="8"/>'
    '<text class="t-s t-code" x="580" y="56" text-anchor="middle">build/generated/ksp/l01</text>'
    '<text class="t-s t-m" x="580" y="78" text-anchor="middle">new cards, one per class</text>'
    '<line class="ln" x1="120" y1="98" x2="250" y2="146" marker-end="url(#arr)"/>'
    '<line class="ln" x1="580" y1="98" x2="450" y2="146" marker-end="url(#arr)"/>'
    '<rect class="box-a" x="180" y="150" width="340" height="64" rx="8"/>'
    '<text class="t t-code" x="350" y="176" text-anchor="middle">compileL01Kotlin</text>'
    '<text class="t-s t-m" x="350" y="198" text-anchor="middle">compiles your classes and the cards together</text>'
    '<line class="ln" x1="350" y1="216" x2="350" y2="236" marker-end="url(#arr)"/>'
    '<rect class="box-ok" x="240" y="240" width="220" height="40" rx="8"/>'
    '<text class="t-s" x="350" y="265" text-anchor="middle">class files, ready to run</text>'
    '</svg>'
)

# ---------------------------------------------------------------- opening
OPENING = """Picture a family packing their home for a move. Every box gets a card taped to it that lists what's inside, so nothing goes missing on the way. MoveMate is a small program that helps them, and it prints the same kind of card for each kind of thing being moved: `Lamp: name=desk lamp, bulbs=1, shade=null`.

We wrote those cards by hand, one small function per class. Then the lamps gained a property, `watts`, and nobody touched the lamp's card. The program compiled, ran, and printed the old list, politely and without a word of complaint. It's an easy trap: a card and its class live in different places, and only a person remembers to keep them in step.

Part 4 ended on the same idea, when a container that connected a program's objects at every start moved that work into a small file generated during the build. In this lesson, we'll try three ways to keep the cards right, and meet KSP, a tool that writes such code while your program is built. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_CARD = """record Lamp(String name, int bulbs, String shade) {}

static String inventoryCard(Lamp lamp) {
    return "Lamp: name=" + lamp.name() + ", bulbs=" + lamp.bulbs() + ", shade=" + lamp.shade();
}"""
K_CARD = """data class Lamp(val name: String, val bulbs: Int, val shade: String?)

fun Lamp.inventoryCard(): String =
    "Lamp: name=$name, bulbs=$bulbs, shade=$shade\""""

S0 = """MoveMate has four kinds of thing to move: boxes, lamps, bookshelves and plants. Each one is a small class, and each class has a matching card function that we wrote by hand. Here is the lamp's, in both languages:

""" + pair(J_CARD, K_CARD) + """

Both versions do the same two things. The class lists the properties, and a separate function repeats that list as text. Two Kotlin features carry the weight. A data class writes its constructor, getters and `toString` for you, as Java's record has done since Java 16. And an extension function, `fun Lamp.inventoryCard()`, is called like a member, `lamp.inventoryCard()`, without changing the class. Java's version stays a static method that takes the lamp.

The hand-written card has real strengths. It's plain code that anyone can read, it runs as fast as code can, and the compiler checks every name in it. Rename `bulbs` and the card stops compiling, so you fix it at once.

Adding a property is a different story. The lamps gained `watts`, and the `DriftDemo` in the Try it runs the new `Lamp` with the old card:

```text
the lamp: Lamp(name=desk lamp, bulbs=1, shade=null, watts=40)
its card: Lamp: name=desk lamp, bulbs=1, shade=null
```

The lamp knows it draws 40 watts, and its card keeps that a secret. The build passed, the program ran, and nothing printed a warning. The compiler checks that every name in the card exists, and all three still do. It cannot check that the card says everything, because nothing in the code says that it should.

That gap has a name: the card has **drifted** from its class. Drift happens to any code that repeats information kept somewhere else, and every class you add is one more chance. MoveMate has four classes today; a real program may have forty.

**Code that repeats a class's shape by hand drifts from it. Something has to keep the copy in step.**

The question is who. One answer is to stop writing the card at all, and let the program work it out from the object while it runs."""

# ---------------------------------------------------------------- section 1
J_REFLECT = """static String reflectionCard(Object thing) throws IllegalAccessException {
    Class<?> type = thing.getClass();
    if (!type.isAnnotationPresent(Inventory.class))
        throw new IllegalArgumentException(type.getSimpleName() + " has no @Inventory note");
    StringJoiner pairs = new StringJoiner(", ");
    for (Field field : type.getDeclaredFields()) {
        if (Modifier.isStatic(field.getModifiers()) || field.isSynthetic()) continue;
        field.setAccessible(true);                       // the fields are private
        pairs.add(field.getName() + "=" + field.get(thing));
    }
    return type.getSimpleName() + ": " + pairs;
}"""
K_REFLECT = """fun reflectionCard(thing: Any): String {
    val type = thing.javaClass
    require(type.isAnnotationPresent(Inventory::class.java)) { "${type.simpleName} has no @Inventory note" }
    val pairs = type.declaredFields
        .filter { !Modifier.isStatic(it.modifiers) && !it.isSynthetic }
        .joinToString(", ") { field ->
            field.isAccessible = true                    // the fields behind properties are private
            "${field.name}=${field.get(thing)}"
        }
    return "${type.simpleName}: $pairs"
}"""

S1 = """**Reflection** is a program looking at its own classes while it runs. It asks an object for its class, the class for its fields, and each field for its value. Every JVM has it built in, in the `java.lang.reflect` package. Here is the whole card, by reflection:

""" + pair(J_REFLECT, K_REFLECT) + """

The two versions match almost line for line, because Kotlin uses the same Java reflection here. Read the Kotlin one aloud: "check that the class carries the `@Inventory` note, then for every field that isn't static, open it up, and print its name and its value."

That sentence uses a word that needs a plain meaning. An **annotation** is a note you attach to a class, a function or a property, written with `@`, such as `@Inventory`. By itself it does nothing at all. It waits for a tool that reads it. `@Inventory` is MoveMate's sticky note on a box: "make an inventory card for this one." Here the tool is our own function, which reads the note while the program runs. So `@Inventory` is declared with `RUNTIME` retention, which keeps it in the class file for that purpose.

Reflection fixes the drift. A class that gains a property gets it on its reflection card at once, with no card to update. The lab's tests check that with a `Rug` nobody wrote a card for, `Rug: colour=red, metres=2.0`, and check that reflection gives the same four cards as the hand-written ones. That's its honest credit: it never forgets a property.

Now the price. The `ReflectionCostDemo` gives both versions the same lamp, checks that the two cards match, then times them. On the course's build machine, four cores busy with other builds at the time, it printed:

```text
the same card: true
first call:     hand-written 18,045,284 ns   reflection 47,526,401 ns
round 1 per call: hand-written        64 ns   reflection       395 ns
round 2 per call: hand-written        27 ns   reflection       217 ns
round 3 per call: hand-written        24 ns   reflection       241 ns
```

Correct first: the same card both ways. The first call of each pays for one-time setup inside the JVM, and reflection's setup costs more, about 48 ms against 18 ms here. Once the JVM has warmed up, a reflection card costs about 220 ns against about 25 ns by hand. That's roughly nine times as much, on every call, for as long as the program runs. A few hundred nanoseconds won't hurt MoveMate. A program that prints a million cards, or starts on a small phone, feels it.

Cost is the first flaw. The second is timing. Hand `reflectionCard` a `Wardrobe` without the note and it fails with `Wardrobe has no @Inventory note`, but only when that line runs, perhaps on moving day itself. The third is quieter. The Javadoc, Java's official API documentation, says that `getDeclaredFields()` returns fields that "are not sorted and are not in any particular order". HotSpot, the usual JVM, returns them in declaration order today, so our cards come out right by habit, not by promise.

In the moving-house picture, reflection means unpacking every box at the new house and checking what's inside, each time someone asks for a list. It works. It's slow, and a box with a missing note turns up only when you open it.

A third way keeps the speed of the hand-written card and the memory of reflection. Let a program write the cards for us, once, while the program is built."""

# ---------------------------------------------------------------- section 2
# what ./gradlew :ksp:app:kspL01Kotlin wrote (copied from a run; build output isn't read here)
GENERATED = """// Generated by InventoryProcessor from Lamp. Do not edit.
package workbench.ksp.app.l01

fun Lamp.inventoryCard(): String =
    "Lamp: name=$name, bulbs=$bulbs, shade=$shade\""""
J_USE = """// Java calling the card that KSP generated in Kotlin
Lamp lamp = new Lamp("desk lamp", 1, null);
System.out.println(LampInventoryCardKt.inventoryCard(lamp));"""
K_USE = """// Kotlin calling the same generated card
val lamp = Lamp("desk lamp", 1, null)
println(lamp.inventoryCard())"""

S2 = """First, two moments in a program's life. Compile time is when the compiler turns your source files into class files, the bytecode the JVM runs. Run time is later, when the JVM runs those class files. The build is everything a tool such as Gradle does to get from source files to a program you can run, and compiling is one step of it.

The hand-written card was written before the build, by a person. The reflection card is worked out at run time, by the program. The third way does the work during the build, by a program. That's **code generation**: one program writes source code, which is then compiled together with yours.

The program that writes the code is an **annotation processor**. It runs during the build, finds the declarations that carry a given annotation, and writes new source files from what it reads. A declaration is a named thing you declared in the code: a class, a property, a function, a parameter. MoveMate's processor looks for `@Inventory` and writes one card per class.

**KSP**, short for Kotlin Symbol Processing, is an open-source tool from Google that runs such processors on Kotlin code. (A symbol is any named thing in your code, which is what a processor reads.) Its docs call it "a source code generation framework for Kotlin". With it, "you can create processors that inspect static information about your source code and generate new code from it". Static information is what you can know without running the code: names, types and annotations.

Here is the moving-house picture, part by part. Your source files are sealed boxes. The label on top lists what's inside: the class name, the properties with their types, the functions and their parameters. Those are the declarations. The annotation is the sticky note on a box. The processor is a helper with a clipboard who walks through the house, finds every box with that note, reads its label, and writes a new card. The cards travel with the move: they're compiled together with your code.

The picture breaks in one place, and it matters. A real helper could lift a flap and peek inside a box. KSP truly can't, as the next section explains.

Let's watch a ready-made processor at work. The lab's real-build playground, `labs/ksp/app`, is an ordinary Gradle project with KSP switched on. Its lesson 1 folder holds the four MoveMate classes, each marked `@Inventory`, and no card functions at all. From `labs/`, run KSP on it alone with `./gradlew :ksp:app:kspL01Kotlin`. The task runs the processor you'll write yourself in the next lesson, and it writes four new files. Open `labs/ksp/app/build/generated/ksp/l01/kotlin/workbench/ksp/app/l01/LampInventoryCard.kt`:

```kotlin solo
""" + GENERATED + """
```

That's the hand-written card, line for line, written by a program that has no way to forget a property. Add `watts` to `Lamp` and run the task again, and the card gains `watts=$watts`, because the helper reads every label afresh on each build.

**Generated code is checked like hand-written code and runs as fast. Only the writing moves, from a person to the build.**

You may wonder whether the generated card is somehow special. It isn't. It's an ordinary Kotlin file, so Java can call it like any other Kotlin code:

""" + pair(J_USE, K_USE) + """

So where exactly in the build does the helper work, and what is it not allowed to touch?"""

# ---------------------------------------------------------------- section 3
J_PROC = """// Closest Java equivalent: a javac annotation processor (javax.annotation.processing, since Java 6)
@SupportedAnnotationTypes("workbench.ksp.annotations.Inventory")
@SupportedSourceVersion(SourceVersion.RELEASE_21)
public class InventoryProcessor extends AbstractProcessor {
    @Override
    public boolean process(Set<? extends TypeElement> annotations, RoundEnvironment roundEnv) {
        TypeElement inventory = processingEnv.getElementUtils().getTypeElement("workbench.ksp.annotations.Inventory");
        for (Element element : roundEnv.getElementsAnnotatedWith(inventory)) {
            // read the element's label, then write a file with processingEnv.getFiler()
        }
        return false;
    }
}"""
K_PROC = """// A KSP processor, the shape lesson 2 builds
class InventoryProcessor(private val codeGenerator: CodeGenerator) : SymbolProcessor {
    override fun process(resolver: Resolver): List<KSAnnotated> {
        for (symbol in resolver.getSymbolsWithAnnotation("workbench.ksp.annotations.Inventory")) {
            // read the symbol's label, then write a file with codeGenerator.createNewFile(...)
        }
        return emptyList()
    }
}"""

S3 = """KSP runs as its own Gradle task, one step of the build, just before the Kotlin compiler. For the lesson 1 folder the task is `kspL01Kotlin`, and the compile task is `compileL01Kotlin`; in an ordinary project with one source folder they're called `kspKotlin` and `compileKotlin`. Gradle's `-m` flag lists the tasks a command would run, in order, without running them:

```text
$ ./gradlew :ksp:app:compileL01Kotlin -m
:ksp:compileSolutionKotlin SKIPPED
:ksp:l02SolutionJar SKIPPED
:ksp:app:kspL01Kotlin SKIPPED
:ksp:app:compileL01Kotlin SKIPPED
```

Read it from the top. Gradle first compiles the processor and packs it into a jar, the zip file a Java library ships in (`l02SolutionJar`), because a processor is a program that must exist before it can run. Then KSP runs it on your files, and only then does the Kotlin compiler start.

The figure draws the same order. KSP writes its files into `build/generated/ksp/l01/kotlin`, a folder it adds to the compile's inputs, and the compiler compiles them together with yours. That's why `MoveMate.kt` can call `inventoryCard()` although no file in `src/l01` defines it. (An IDE, the editor you write code in, marks that call red until the first build has run KSP.)

KSP isn't part of the Kotlin compiler. Its KSP2 notes say it "is no longer a compiler plugin", and that it "runs in Gradle daemon", the background process Gradle keeps alive between builds. KSP's version numbers no longer follow Kotlin's either: these labs run KSP 2.3.14 with Kotlin 2.4.21.

Now the two limits, in the docs' own words: KSP-based processors "can't examine expressions or statements, and they can't modify the source code."

The first limit means the helper reads labels and never what's packed. It sees `fun areaCm2(): Int`, a function's name and its return type, but not the multiplication inside it. It sees that a parameter has a default value, but not what the value is. Lesson 3 of this track proves this with a demo.

The second limit means the helper never relabels or repacks a box. A processor can't add a function to `Lamp`; it can only write a new file. That's why the card is an extension function in a file of its own, and not a member of `Lamp`.

**KSP reads declarations, never bodies, and it adds new files, never edits yours.**

Java has had this idea for a long time. Since Java 6, javac has run annotation processors written against `javax.annotation.processing`, and many Java libraries generate code that way. KSP is Kotlin's own, faster way to do the same job for Kotlin code. It reads Kotlin's features, such as nullable types and default values, directly. An older bridge, kapt, runs Java's processors on Kotlin by first writing Java copies of your classes, which is slow; lesson 9 of this track returns to it. Both kinds of processor have the same shape:

""" + pair(J_PROC, K_PROC) + """

Lesson 2 builds the Kotlin one, line by line.

Put the three ways side by side in the picture, with one more. A hand-written card is a person keeping a list. Reflection is unpacking every box at the new house, each time. A processor is the helper who writes the cards before the van leaves. A compiler plugin, from the last lesson of Advanced Kotlin, changes what the compiler writes into a class. It's a mover who repacks boxes: more power, and more risk. KSP stays a helper on purpose.

Next, you'll stop watching the helper and write one."""

# ---------------------------------------------------------------- closing
CLOSING = """We started with a family's boxes and a lamp card that kept quiet about 40 watts. A hand-written card drifted, reflection unpacked every box at run time and paid for it on every call, and a ready-made processor wrote the card during the build, from the label, every time.

In your own code, look for a function that lists a class's properties by hand: a `toString`, a copy method, a form, a mapper. Each one is a card waiting to drift.

Next, we'll write that processor ourselves, starting from an empty file. What does KSP need before it will run your code at all?"""

L = {
 "id": "ksp-01",
 "title": "Code that writes code: what KSP is and where it runs",
 "minutes": 35,
 "goal": "By the end you can say what an annotation processor does and when it runs, weigh a hand-written card, a reflection card and a generated one by what each costs, run a ready-made KSP processor in a real build and open the file it wrote, and name the two things KSP cannot do.",
 "opening": OPENING,
 "warmup": {
  "q": "MoveMate's `Lamp` gains a property, `watts`, and nobody touches its hand-written `inventoryCard()` function. What happens when you build and run the program?",
  "options": ["The compiler reports that the card no longer matches the class", "It builds and runs, and the card leaves out watts without any warning", "It builds, then throws an exception when it prints the card", "The card shows watts by itself, because it's an extension function"],
  "answer": 1,
  "why": "Nothing connects the card's text to the class's list of properties except a person's memory. The card still names three properties that exist, so it compiles, runs and prints an incomplete card. The first option is what many people expect, but the compiler checks that the names in the card exist, not that the card mentions every property. The first section runs exactly this, in the `DriftDemo`."
 },
 "sections": [
  {
   "h": "Four cards written by hand, and the one that went stale",
   "body": S0,
   "try": {
    "title": "Watch a card drift",
    "minutes": 3,
    "steps": [
     "Read `DriftDemo`: the new `Lamp` has `watts`, the card is the old one. Predict both printed lines, then run it from `labs/`.",
     "Run the Java twin, `DriftDemoJava`, where a record gained a component the same way.",
     "In `DriftDemo.kt`, rename `bulbs` to `bulbCount` in the class only. Predict what the build says this time, then undo it."
    ],
    "code": demo("DriftDemo"),
    "expect": "`the lamp: Lamp(name=desk lamp, bulbs=1, shade=null, watts=40)` and `its card: Lamp: name=desk lamp, bulbs=1, shade=null`, and the Java twin prints the same card after `Lamp[name=desk lamp, bulbs=1, shade=null, watts=40]`. The build is green and nothing warns. The rename is different: the card no longer compiles, because `bulbs` no longer exists. The compiler catches a name that disappears, never a name that's missing."
   }
  },
  {
   "h": "Reflection: working out the card while the program runs",
   "body": S1,
   "try": {
    "title": "Time the card both ways",
    "minutes": 4,
    "steps": [
     "Run `ReflectionCostDemo`. It uses the reference `reflectionCard` until you finish the lab; add `-Pmine=l01` afterwards to time yours.",
     "Check the third line first: are the two cards the same? Then compare the per-call times in round 3.",
     "Run it twice more, and the Java twin `ReflectionCostDemoJava` once. Which numbers stay about the same, and which jump around?"
    ],
    "code": demo("ReflectionCostDemo"),
    "expect": "`the same card: true`, then a first call of a few to a few tens of milliseconds for each, reflection's the larger, and warm per-call times of roughly 15 to 60 ns by hand against roughly 200 to 400 ns by reflection. The first-call numbers jump around from run to run, because they measure one-time setup inside a busy machine. The warm ratio, about eight to ten times, stays steady. Your machine will give its own numbers."
   },
   "refs": [{"title": "Class.getDeclaredFields (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Class.html", "kind": "docs"}]
  },
  {
   "h": "Code that writes code: a processor writes the cards during the build",
   "body": S2,
   "try": {
    "title": "Run a ready-made processor in a real build",
    "minutes": 5,
    "steps": [
     "From `labs/`, run `./gradlew :ksp:app:kspL01Kotlin`. Then list `labs/ksp/app/build/generated/ksp/l01/kotlin/workbench/ksp/app/l01/`. Predict how many files you'll find, and why that many.",
     "Open `PlantInventoryCard.kt` and compare it with the given `Box` card in `labs/ksp/src/main/kotlin/workbench/ksp/l01/HandCards.kt`.",
     "Run the app's `MoveMate.kt` below with `./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l01.MoveMateKt`, then the Java twin with `-Pmain=workbench.ksp.app.l01.MoveMateJava`.",
     "Add `val watts: Int = 60` to `Lamp` in `labs/ksp/app/src/l01/kotlin/workbench/ksp/app/l01/MoveMate.kt`, run `./gradlew :ksp:app:kspL01Kotlin` again and reopen `LampInventoryCard.kt`. Then undo the change."
    ],
    "code": {"lang": "kotlin", "title": "MoveMate.kt", "src": read(f"{app}/kotlin/workbench/ksp/app/l01/MoveMate.kt"),
             "run": "./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l01.MoveMateKt",
             "file": f"{app}/kotlin/workbench/ksp/app/l01/MoveMate.kt",
             "alt": {"lang": "java", "title": "MoveMateJava.java", "src": read(f"{app}/java/workbench/ksp/app/l01/MoveMateJava.java"),
                     "run": "./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l01.MoveMateJava",
                     "file": f"{app}/java/workbench/ksp/app/l01/MoveMateJava.java"}},
    "expect": "Four files, one per class with `@Inventory`: `BookshelfInventoryCard.kt`, `BoxInventoryCard.kt`, `LampInventoryCard.kt` and `PlantInventoryCard.kt`, each written exactly like the given `Box` card. Both demos print the same four cards, starting with `Box: label=kitchen 1, room=kitchen, weightGrams=5200, fragile=true`. With `watts` added, the generated card ends `shade=$shade, watts=$watts` with no card written by anyone. If you run the Java twin before undoing, javac stops at `new Lamp(\"desk lamp\", 1, null)`: Java has no default arguments, so a Java call must pass `watts` too. The compiler checks calls; it was never checking cards."
   },
   "refs": [{"title": "KSP overview (Kotlin docs)", "url": "https://kotlinlang.org/docs/ksp-overview.html", "kind": "docs"}]
  },
  {
   "h": "Where KSP runs in the build, and the two things it cannot do",
   "body": S3,
   "figure": {"svg": FIG, "caption": "KSP runs as its own task before the Kotlin compiler; the files it writes are compiled together with yours."},
   "try": {
    "title": "Change the label, watch the card follow",
    "minutes": 3,
    "steps": [
     "Run `GeneratedCardDemo`. It compiles the new `Lamp` in memory with the ready-made processor and prints the card file it wrote.",
     "In the demo's source string, give `Lamp` one more property, `val colour: String`, and pass `\"white\"` to it in `deskLampCard()`. Predict the new card, then run it.",
     "Now add `val price = watts * 2` inside the class body instead, as a property that isn't in the constructor. Predict whether the card shows it, then run."
    ],
    "code": {"lang": "kotlin", "title": "GeneratedCardDemo.kt", "src": read(f"{lab}/demo/kotlin/workbench/ksp/l01/demo/GeneratedCardDemo.kt"),
             "run": RUN + "GeneratedCardDemoKt", "file": f"{lab}/demo/kotlin/workbench/ksp/l01/demo/GeneratedCardDemo.kt", "solo": True},
    "expect": "First `exit code: OK`, the file `movemate/LampInventoryCard.kt` with `watts=$watts` in the template, and `deskLampCard() returns: Lamp: name=desk lamp, bulbs=1, shade=null, watts=40`. With `colour`, the card gains `colour=$colour` and prints `colour=white`. The property in the body doesn't appear: the card lists the primary constructor's properties only, because that's the label the processor reads. The demo takes about 10 s, most of it starting the compiler."
   },
   "refs": [{"title": "KSP2 introduction (google/ksp)", "url": "https://github.com/google/ksp/blob/main/docs/ksp2.md", "kind": "docs"}]
  }
 ],
 "compare": {
  "title": "The lamp's card three ways, in Java and Kotlin",
  "java": {"title": "Cards.java", "src": "// 1. by hand: fast, checked by the compiler, and it drifts\nstatic String inventoryCard(Lamp lamp) {\n    return \"Lamp: name=\" + lamp.name() + \", bulbs=\" + lamp.bulbs() + \", shade=\" + lamp.shade();\n}\n\n// 2. by reflection, at run time: a record promises its components' order\nstatic String reflectionCard(Record thing) throws ReflectiveOperationException {\n    StringJoiner pairs = new StringJoiner(\", \");\n    for (RecordComponent c : thing.getClass().getRecordComponents()) {\n        pairs.add(c.getName() + \"=\" + c.getAccessor().invoke(thing));\n    }\n    return thing.getClass().getSimpleName() + \": \" + pairs;\n}\n\n// 3. by a javac annotation processor during the build: it writes\n//    LampInventoryCard.java, and the program calls LampInventoryCard.inventoryCard(lamp)"},
  "kotlin": {"title": "Cards.kt", "src": "// 1. by hand: fast, checked by the compiler, and it drifts\nfun Lamp.inventoryCard(): String =\n    \"Lamp: name=$name, bulbs=$bulbs, shade=$shade\"\n\n// 2. by reflection, at run time: fields in whatever order getDeclaredFields() gives\nfun reflectionCard(thing: Any): String =\n    thing.javaClass.simpleName + \": \" + thing.javaClass.declaredFields\n        .filter { !Modifier.isStatic(it.modifiers) }\n        .joinToString(\", \") { it.isAccessible = true; \"${it.name}=${it.get(thing)}\" }\n\n// 3. by a KSP processor during the build: it writes LampInventoryCard.kt holding\n//    the same function as 1, and the program calls lamp.inventoryCard()"},
  "note": "The three ways line up in both languages. One real difference sits in the middle. A Java record promises the order of its components: `getRecordComponents()` returns them in the order they're declared in the record header. A Kotlin data class is an ordinary class to the JVM, so reflection falls back on `getDeclaredFields()`, whose Javadoc promises no order at all. The other difference is in the third way. A javac processor writes a Java helper class that you call with the object as an argument. A KSP processor can write an extension function, so the generated card reads like a member, `lamp.inventoryCard()`. Neither tool can add a real member to the class."
 },
 "worked": {
  "title": "Guard the hand-written cards with a test, and see why it isn't enough",
  "steps": [
   {"say": "Before reaching for a processor, a careful team might guard the hand-written cards with a test: for each class, build one sample object and compare its hand-written card with the reflection card. Reflection becomes the referee.",
    "code": "// 1. one sample per class\nprivate val samples = listOf(\n    Lamp(\"desk lamp\", 1, null, 40),\n    Plant(\"fern\", 2.5),\n)\n\n@Test\nfun `every hand-written card lists every property`() {\n    // 2. the referee: the same card, worked out by reflection\n    assertThat(samples[0].inventoryCard()).isEqualTo(reflectionCard(samples[0]))\n    assertThat(samples[1].inventoryCard()).isEqualTo(reflectionCard(samples[1]))\n}",
    "lang": "kotlin",
    "alt_lang": "java", "alt_code": "// 1. one sample per class\nprivate final Lamp lamp = new Lamp(\"desk lamp\", 1, null, 40);\nprivate final Plant plant = new Plant(\"fern\", 2.5, 7);\n\n@Test\nvoid everyHandWrittenCardListsEveryProperty() throws Exception {\n    // 2. the referee: the same card, worked out by reflection\n    assertThat(Cards.inventoryCard(lamp)).isEqualTo(Cards.reflectionCard(lamp));\n    assertThat(Cards.inventoryCard(plant)).isEqualTo(Cards.reflectionCard(plant));\n}"},
   {"say": "With the stale lamp card, the first assertion fails, and AssertJ prints both cards, the one with `watts=40` and the one without. The drift is caught by the tests, before moving day. That's a real improvement, and a cheap one.", "code": "", "lang": ""},
   {"say": "Now MoveMate gains a fifth class, `Rug`, and whoever adds it forgets to add a sample to this test. The test passes, and the rug's card can drift as freely as the lamp's did. The drift has moved from the card into the test: the list of samples is one more thing a person must keep in step.", "code": "", "lang": ""},
   {"say": "A processor ends the chase. It finds every class with `@Inventory` itself, on every build, so there is no list for anyone to forget. The cards follow the labels because nobody writes them. That's the job the rest of this track teaches, starting with the next lesson.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Do the helper's job by hand, then by reflection",
  "minutes": 12,
  "files": [f"{lab}/main/{P}/HandCards.kt", f"{lab}/main/{P}/ReflectionCards.kt", f"{lab}/main/{P}/MoveMate.kt", f"{lab}/main/{P}/ReadyMadeProcessor.kt"],
  "run": "./gradlew :ksp:test --tests 'workbench.ksp.l01.*'",
  "steps": [
   "Open `MoveMate.kt` (given): four classes, each with `@Inventory`. Today you're the helper, so you'll make its five moves yourself. Every lab in this track names the same five moves: Find, Check, Read, Write, Prove.",
   "1. Find: list the classes that carry `@Inventory`. 2. Check: all four are classes, so each one can have a card. 3. Read: for `Lamp` and `Plant`, write down the primary constructor's properties, in order.",
   "4. Write: in `HandCards.kt`, replace the two `TODO`s with the cards for `Lamp` and `Plant`, in exactly the format of the given `Box` card.",
   "Now let the program make the same moves while it runs: write `reflectionCard` in `ReflectionCards.kt`. Find and Check become `isAnnotationPresent`, Read becomes `declaredFields`, and Write becomes `joinToString`. A class without the note must fail with `<Name> has no @Inventory note`.",
   "5. Prove: run the tests until all nine pass. `CardsAgreeTest` compiles the same four classes in memory with the ready-made processor (`ReadyMadeProcessor.kt`, given; you'll write it yourself in lesson 2) and checks that its cards, yours and reflection's all agree.",
   "Then prove it in the real build: run `./gradlew :ksp:app:kspL01Kotlin` and open `labs/ksp/app/build/generated/ksp/l01/kotlin/workbench/ksp/app/l01/PlantInventoryCard.kt`. Compare it with your hand-written Plant card.",
   "From memory: close the files and write, on paper, the card for `data class Rug(val colour: String, val metres: Double)` and the folder KSP would put it in. Check the card against `Rug: colour=red, metres=2.0` in `ReflectionCardTest`."
  ],
  "hints": [
   "A card is one string template: `\"Lamp: name=$name, bulbs=$bulbs, shade=$shade\"`. A `null` shade prints as `null` by itself.",
   "`declaredFields` also returns static fields, such as the one a companion object adds. Skip them with `Modifier.isStatic(field.modifiers)`, and skip `field.isSynthetic` ones too.",
   "The fields behind Kotlin properties are private. Set `field.isAccessible = true` before `field.get(thing)`.",
   "For the refusal, `require(type.isAnnotationPresent(Inventory::class.java)) { \"${type.simpleName} has no @Inventory note\" }` throws the `IllegalArgumentException` the test expects."
  ],
  "done_when": "All nine tests in `HandCardsTest`, `ReflectionCardTest` and `CardsAgreeTest` pass."
 },
 "drill": {
  "title": "Write the card and find its file from memory",
  "minutes": 4,
  "prompt": "Close this page. For `class Bookshelf(val shelves: Int, val books: List<String>)`, write the inventory card by hand in Kotlin, as an extension function, and in Java, as a static method on a record. Then write the full path where the playground's KSP task puts the generated Bookshelf card for lesson 1. Compare with the answer.",
  "answer": {"lang": "kotlin", "src": "fun Bookshelf.inventoryCard(): String =\n    \"Bookshelf: shelves=$shelves, books=$books\"\n\n// the generated one, after ./gradlew :ksp:app:kspL01Kotlin:\n// labs/ksp/app/build/generated/ksp/l01/kotlin/workbench/ksp/app/l01/BookshelfInventoryCard.kt",
             "alt": {"lang": "java", "title": "Cards.java", "src": "record Bookshelf(int shelves, List<String> books) {}\n\nstatic String inventoryCard(Bookshelf shelf) {\n    return \"Bookshelf: shelves=\" + shelf.shelves() + \", books=\" + shelf.books();\n}"}}
 },
 "recap": [
  "A hand-written card is fast and checked by the compiler, but it drifts: add a property and the card leaves it out, with no warning.",
  "Reflection works the card out at run time from the object's fields. It never drifts, but it costs on every call (about 220 ns against 25 ns, on a busy machine), finds a missing note only when that line runs, and relies on a field order the Javadoc doesn't promise.",
  "An annotation is a note in the code. An annotation processor runs during the build, finds the declarations carrying a note, and writes new source files that are compiled with yours: code generation.",
  "KSP runs processors on Kotlin code as its own Gradle task (`kspKotlin`, here `kspL01Kotlin`) before the Kotlin compiler, and its files land in `build/generated/ksp/<source set>/kotlin/`.",
  "The limits: KSP reads declarations, never expressions or bodies, and it only adds new files; it never edits yours. Java has had javac annotation processors since Java 6, and KSP is the Kotlin-native way to do the same job."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "Which parts of this class can a KSP processor read?\n\n```kotlin\nclass Mirror(val widthCm: Int, val heightCm: Int) {\n    fun areaCm2(): Int = widthCm * heightCm\n}\n```",
   "options": ["Only the class name: types are worked out later by the compiler", "The class, both properties with their types, and `areaCm2(): Int`, but not `widthCm * heightCm`", "Everything, including the multiplication, as a tree of expressions", "Nothing until `compileKotlin` has turned it into class files"],
   "answer": 1, "why": "KSP sees declarations: names, types, parameters, annotations. It can't see expressions or statements, so the body of `areaCm2` is closed to it. It runs before the compiler, on source files, so the last option has the order backwards. The third is what a compiler plugin can see, and KSP deliberately can't."},
  {"q": "MoveMate needs a `card()` function that reads like a member of `Lamp`. What does a KSP processor do?",
   "options": ["It adds `fun card()` inside `class Lamp` in `Lamp.kt`", "It edits the compiled `Lamp.class` after `compileKotlin`", "It asks the compiler to add the member while it compiles", "It writes a new file with an extension function, `fun Lamp.card()`"],
   "answer": 3, "why": "KSP can't modify existing code; it only creates new files, which are compiled with yours. An extension function in a new file is the usual way to make generated code read like a member. Changing a class or its class file is a compiler plugin's job."},
  {"q": "After `./gradlew :ksp:app:kspL01Kotlin`, where is the generated `LampInventoryCard.kt`?",
   "options": ["`labs/ksp/app/build/generated/ksp/l01/kotlin/workbench/ksp/app/l01/`", "`labs/ksp/app/src/l01/kotlin/workbench/ksp/app/l01/`, next to `MoveMate.kt`", "`labs/ksp/app/build/classes/kotlin/l01/`", "Nowhere on disk: KSP hands it to the compiler in memory"],
   "answer": 0, "why": "KSP writes generated sources under `build/generated/ksp/<source set>/kotlin/`, in the package's folders, and adds that folder to the compile. It never writes into `src`, which belongs to you, and class files come later, from the compiler."},
  {"q": "Pick the tool. A test helper prints every property of whatever object a test hands it, a few dozen times per test run, including objects from libraries you can't annotate.",
   "options": ["A KSP processor, because generated code is faster", "A hand-written card for each class", "Reflection: it works on any object at run time, and a few dozen calls cost almost nothing", "A compiler plugin that adds a card to every class"],
   "answer": 2, "why": "A processor only sees source code it is run on, marked with its annotation, so library classes are out of reach, and hand-written cards can't cover unknown classes. At a few dozen calls, reflection's few hundred nanoseconds are invisible. Reflection's costs matter in hot paths and at start-up, not in a test helper."},
  {"q": "From Part 4's capstone: the container moved its wiring from reflection at every start to a registry generated during the build. What did that trade give up?",
   "options": ["Speed: generated wiring is slower on every call", "Choosing parts at start-up: the set of components is fixed when you build", "Type checking: generated code isn't checked by the compiler", "Thread safety: the generated holders can't be shared between threads"],
   "answer": 1, "why": "Work that depends only on the classes can move to the build, but then the set of parts is fixed when you build; nothing can pick a component from a setting or a plugin folder at start-up unless the generator wrote code for it. Generated code is compiled and checked like any code, and it's faster, which is why the move was worth it.",
   "from": "cap4-03"}
 ],
 "flashcards": [
  {"front": "What is an annotation processor?", "back": "A program that runs during the build, finds declarations that carry a given annotation, and writes new source files that are compiled together with yours."},
  {"front": "What does KSP stand for, and what does it run?", "back": "Kotlin Symbol Processing. It runs annotation processors written against its own API on Kotlin (and Java) source code during the build."},
  {"front": "Which Gradle task runs KSP, and when?", "back": "`kspKotlin` for the main source set (`kspL01Kotlin` in the lab), before `compileKotlin`, which then compiles your files and the generated ones together."},
  {"front": "Where do KSP's generated Kotlin files go?", "back": "`build/generated/ksp/<source set>/kotlin/<package folders>/`, for example `build/generated/ksp/main/kotlin/...` in an ordinary project."},
  {"front": "What are KSP's two limits?", "back": "It can't see expressions or statements (function bodies, default values), and it can't modify existing code: it only adds new files."},
  {"front": "Why does the reflection card need `@Inventory` with RUNTIME retention, while KSP doesn't?", "back": "Reflection looks for the annotation while the program runs, so it must survive into the class file. KSP reads source files, so SOURCE retention is enough for it."},
  {"front": "Hand-written card vs reflection card: one cost each?", "back": "The hand-written card drifts when the class changes. The reflection card costs on every call (here about 220 ns against 25 ns) and finds mistakes only when it runs."}
 ],
 "terms": [
  {"term": "Annotation", "plain": "A note attached to a class, function or property with `@`. It does nothing until a tool reads it."},
  {"term": "Build", "plain": "Everything a tool such as Gradle does to turn source files into a program you can run; compiling is one step."},
  {"term": "Compile time", "plain": "When the compiler turns source files into class files, before the program runs."},
  {"term": "Run time", "plain": "When the JVM runs the compiled program."},
  {"term": "Reflection", "plain": "A program inspecting its own classes, fields and annotations while it runs, through `java.lang.reflect`."},
  {"term": "Code generation", "plain": "One program writing source code that is then compiled together with yours."},
  {"term": "Annotation processor", "plain": "A program that runs during the build, reads annotated declarations and writes new source files."},
  {"term": "KSP", "plain": "Kotlin Symbol Processing: the tool that runs annotation processors on Kotlin code, as a Gradle task before the Kotlin compiler."}
 ],
 "explain_back": {
  "prompt": "A teammate asks: \"Why add a build step for these cards? Reflection already works.\" Explain the three ways to produce MoveMate's cards and when you'd pick each.",
  "answer": "A hand-written card is plain code: fast, readable and checked by the compiler, but it repeats the class's list of properties, so when someone adds a property the card goes stale without any warning. Reflection reads the object's fields while the program runs, so it never goes stale, but it pays for that on every call (several times slower in our measurement), it finds a class without the annotation only when that line runs, and it relies on a field order Java doesn't promise. A processor does the reading once, during the build: KSP runs it before the Kotlin compiler, it reads each annotated class's declarations and writes an ordinary card function, which is then compiled and runs as fast as a hand-written one. It can't change existing code or see inside function bodies, so it writes new files such as extension functions. I'd keep reflection for small, rare jobs on classes I can't annotate, and use a processor when the same boilerplate repeats across many classes, runs often, or must be checked at build time."
 },
 "deeper": {
  "minutes": 8,
  "body": "Three facts for a curious day.\n\nFirst, the Java side changed recently. Since JDK 23, javac no longer runs annotation processors that it merely finds on the class path. The release notes say processing \"is only run with some explicit configuration of annotation processing or with an explicit request to run annotation processing on the javac command line\", and `-proc:full` restores the old behavior. Gradle passes processors explicitly through its `annotationProcessor` configuration, so Gradle builds don't notice. Plain `javac` scripts that relied on discovery do.\n\nSecond, kapt. It lets Kotlin projects run Java annotation processors by first generating Java stubs, Java copies of your Kotlin classes with the bodies replaced, so the Java processor has something it can read. The migration guide calls that step \"expensive\": it \"significantly increases build time\" and loses Kotlin details such as nullability. KSP's README says KSP processors \"can run up to 2x faster\" than kapt. That figure comes from early benchmarks with Room, a database library, when KSP was announced in 2021, so read it as one measurement, not a law. Lesson 9 of this track weighs the two in a real build.\n\nThird, treat generated files as output, not source. Each one says `Do not edit` because KSP rewrites it whenever the class it came from changes, and a clean build deletes it. If a generated file is wrong, fix the processor or the annotated class. Read generated files often, though: they're the quickest way to see what a processor really does, and lesson 8 turns that habit into tests."
 },
 "sources": [
  {"title": "KSP overview (Kotlin docs)", "url": "https://kotlinlang.org/docs/ksp-overview.html"},
  {"title": "KSP2 introduction (google/ksp)", "url": "https://github.com/google/ksp/blob/main/docs/ksp2.md"},
  {"title": "Processor (Java SE 25 API, javax.annotation.processing)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.compiler/javax/annotation/processing/Processor.html"},
  {"title": "Class (Java SE 25 API), getDeclaredFields and getRecordComponents", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Class.html"},
  {"title": "Announcing Kotlin Symbol Processing (Android Developers Blog, 2021)", "url": "https://android-developers.googleblog.com/2021/02/announcing-kotlin-symbol-processing-ksp.html"}
 ]
}
out = ROOT / "content/lessons/ksp-01.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
