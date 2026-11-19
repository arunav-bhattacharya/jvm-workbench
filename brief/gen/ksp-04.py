import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
read = lambda p: (ROOT / p).read_text()
APP = "labs/ksp/app/src/l04"
LAB = "labs/ksp/src"
DEMO = "./gradlew :ksp:demo -Pmain=workbench.ksp.l04.demo."
APPDEMO = "./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l04."


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


def app_demo(kt, java):
    """A Kotlin program in the real-build playground and its runnable Java twin."""
    return {"lang": "kotlin", "title": f"{kt}.kt", "src": read(f"{APP}/kotlin/workbench/ksp/app/l04/{kt}.kt"),
            "run": APPDEMO + kt + "Kt", "file": f"{APP}/kotlin/workbench/ksp/app/l04/{kt}.kt",
            "alt": {"lang": "java", "title": f"{java}.java", "src": read(f"{APP}/java/workbench/ksp/app/l04/{java}.java"),
                    "run": APPDEMO + java, "file": f"{APP}/java/workbench/ksp/app/l04/{java}.java"}}


FIG = (
    '<svg viewBox="0 0 700 330" role="img" aria-label="Five KotlinPoet specs on the left, each with an arrow to the part of LampBuilder.kt it prints on the right: the file with its imports, the class, the fields, the setters and build">'
    '<text class="t-s t-m" x="160" y="24" text-anchor="middle">what the processor builds</text>'
    '<text class="t-s t-m" x="530" y="24" text-anchor="middle">what KotlinPoet prints in LampBuilder.kt</text>'
    '<rect class="box-a" x="20" y="38" width="280" height="40" rx="8"/>'
    '<text class="t-s t-code" x="160" y="63" text-anchor="middle">FileSpec.builder(LampBuilder)</text>'
    '<rect class="box" x="370" y="38" width="320" height="40" rx="8"/>'
    '<text class="t-s t-code" x="530" y="63" text-anchor="middle">package movemate, import kotlin.Int ...</text>'
    '<line class="ln" x1="304" y1="58" x2="364" y2="58" marker-end="url(#arr)"/>'
    '<rect class="box-a" x="20" y="92" width="280" height="40" rx="8"/>'
    '<text class="t-s t-code" x="160" y="117" text-anchor="middle">TypeSpec.classBuilder(LampBuilder)</text>'
    '<rect class="box" x="370" y="92" width="320" height="40" rx="8"/>'
    '<text class="t-s t-code" x="530" y="117" text-anchor="middle">public class LampBuilder {</text>'
    '<line class="ln" x1="304" y1="112" x2="364" y2="112" marker-end="url(#arr)"/>'
    '<rect class="box-b" x="20" y="146" width="280" height="40" rx="8"/>'
    '<text class="t-s t-code" x="160" y="171" text-anchor="middle">PropertySpec, copy(nullable = true)</text>'
    '<rect class="box" x="370" y="146" width="320" height="40" rx="8"/>'
    '<text class="t-s t-code" x="530" y="171" text-anchor="middle">private var shade: String? = null</text>'
    '<line class="ln" x1="304" y1="166" x2="364" y2="166" marker-end="url(#arr)"/>'
    '<rect class="box-b" x="20" y="200" width="280" height="40" rx="8"/>'
    '<text class="t-s t-code" x="160" y="225" text-anchor="middle">FunSpec + addParameter, %N</text>'
    '<rect class="box" x="370" y="200" width="320" height="40" rx="8"/>'
    '<text class="t-s t-code" x="530" y="225" text-anchor="middle">public fun name(name: String): LampBuilder</text>'
    '<line class="ln" x1="304" y1="220" x2="364" y2="220" marker-end="url(#arr)"/>'
    '<rect class="box-b" x="20" y="254" width="280" height="40" rx="8"/>'
    '<text class="t-s t-code" x="160" y="279" text-anchor="middle">FunSpec build(), CodeBlock %T %N %S</text>'
    '<rect class="box" x="370" y="254" width="320" height="40" rx="8"/>'
    '<text class="t-s t-code" x="530" y="279" text-anchor="middle">public fun build(): Lamp = Lamp(...)</text>'
    '<line class="ln" x1="304" y1="274" x2="364" y2="274" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="350" y="318" text-anchor="middle">addOriginatingKSFile ties the file to Lamp.kt; writeTo hands it to KSP</text>'
    '</svg>'
)

# ---------------------------------------------------------------- opening
OPENING = """A family is packing for a move. Every box is sealed, and its label lists what's inside. In this track your source files are those boxes. A KSP processor is a helper with a clipboard: it reads the labels and writes new cards that travel with the move. In the last lesson, the helper learned to copy a label out neatly, `Lamp(name: String, bulbs: Int, shade: String?)`, for a person to read.

Today the card has a stricter reader. We'll generate a builder for each class: a small class that collects an object's values one call at a time and then builds it, `LampBuilder().name("desk lamp").bulbs(1).shade(null).build()`. Its reader is the Kotlin compiler, which has never once forgiven a missing import. Lesson 2 wrote its cards with a string template, text with values pasted in, so we'll start there. It works for `Lamp`, and then three of four ordinary classes fail to compile.

In this lesson, we'll watch that happen, swap the handwriting for a label printer called KotlinPoet, and read what it prints. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_TEMPLATE = """// Closest Java equivalent: a javac annotation processor that writes text through the Filer
JavaFileObject file = processingEnv.getFiler().createSourceFile(pkg + "." + name + "Builder", type);
try (Writer out = file.openWriter()) {
    out.write("package " + pkg + ";\\n\\n");
    out.write("public class " + name + "Builder {\\n");
    for (VariableElement p : params) {
        out.write("    private " + p.asType() + " " + p.getSimpleName() + ";\\n");
    }
    // ... the setters and build(), line by line
    out.write("}\\n");
}"""
K_TEMPLATE = """// Naive: a builder from a string template
val text = buildString {
    appendLine("package $pkg")
    appendLine()
    appendLine("class ${name}Builder {")
    for (p in params) {
        appendLine("    private var ${p.name!!.asString()}: ${p.type.resolve()}? = null")
    }
    // ... the setters and build(), line by line
    appendLine("}")
}
codeGenerator.createNewFile(Dependencies(false, cls.containingFile!!), pkg, "${name}Builder")
    .use { it.write(text.toByteArray()) }"""

S0 = """First, the job. MoveMate is the small app this track builds for the family's move. One of its classes is `data class Lamp(val name: String, val bulbs: Int, val shade: String?)`, marked with the annotation `@Builder`. An annotation is the sticky note on the box: here it says "make a builder for this one". For each class with that note, our processor should write `LampBuilder`. It needs one private field per constructor parameter, each starting empty, and one setter per field that returns the builder, so that calls chain. Last comes `build()`, which calls `Lamp`'s constructor.

The quickest way to write that file is lesson 2's way. Build the text line by line, then hand it to KSP's `CodeGenerator`, the object that creates new files. Java has had annotation processors, programs that run inside the compiler and write new source files, since Java 6. KSP is Kotlin's own way to do that job for Kotlin code, and faster than running Java's processors on Kotlin through kapt. Here is the heart of the template version, next to its closest Java equivalent:

""" + pair(J_TEMPLATE, K_TEMPLATE) + """

`p.type.resolve()` turns the type as written into a `KSType`, and pasting a `KSType` into a string prints its name. For `Lamp`, the result compiles and the builder works. It has one smudge: `shade` is already `String?`, the template adds its own `?`, and the field comes out as `String??`. The compiler lets it through with a sigh, `w: LampBuilder.kt:6:31 Redundant '?'.`

Now four ordinary classes, each compiled on its own. The Try it below printed:

```text
=== a type from another package: COMPILATION_ERROR
e: LoadBuilder.kt:4:24 Unresolved reference 'Box'.
=== a nullable list of nullable boxes: OK
w: ShelfBuilder.kt:4:35 Redundant '?'.
=== a nested class: COMPILATION_ERROR
e: DrawerBuilder.kt:9:18 Unresolved reference 'Drawer'.
=== a property named in: COMPILATION_ERROR
e: CrateBuilder.kt:4:17 Syntax error: Expecting property name or receiver type.
... and 11 more
```

Look at the shape of those lines: a file, a line and a column, and no `[ksp]`. KSP wrote all five files without a word. The Kotlin compiler found the problems afterwards, because a generated file is compiled exactly like one of yours.

That explains every failure. `Load` lives in package `movemate.van` and uses `movemate.Box`, so `LoadBuilder.kt` needs `import movemate.Box`, and the template wrote no imports at all. A `KSType` prints a short display name, `Box` or `List<Box?>?`, which reads well but is not promised to be valid source in another file. `Drawer` is nested inside `Kitchen`, so from outside its name is `Kitchen.Drawer`. And `in` is a hard keyword: a property may be called `in` only when it's written with backticks, `` `in` ``.

In the moving-house picture, the template is handwriting on the card. It abbreviates without saying what the abbreviation means (no import) and smudges a mark (`??`). It forgets which room a box sits in (`Kitchen`), and it writes a word the reader takes for an instruction (`in`).

You could fix each slip by hand: qualified names everywhere, a list of keywords to escape, a check before every `?`. Each fix is fair, and together they add up to a small program that prints Kotlin code.

**Generated code is ordinary source code. Print it with a tool that knows Kotlin.**

That tool already exists, and it's called KotlinPoet."""

# ---------------------------------------------------------------- section 1
J_GREET = """// Closest Java equivalent: JavaPoet, KotlinPoet's older sibling for Java
MethodSpec greet = MethodSpec.methodBuilder("greet")
        .addModifiers(Modifier.PUBLIC)
        .returns(String.class)
        .addStatement("return $S", "Hello from Lamp")
        .build();
// prints:  public String greet() {
//            return "Hello from Lamp";
//          }"""
K_GREET = """val greet = FunSpec.builder("greet")
    .returns(STRING)
    .addStatement("return %S", "Hello from Lamp")
    .build()
// prints:  public fun greet(): kotlin.String = "Hello from Lamp\""""

S1 = """KotlinPoet is a library from Square, here in version 2.4.0, that writes Kotlin source files from objects instead of strings. You describe what the file holds, such as a class with these properties and these functions. KotlinPoet prints it, with the imports, the indentation and the escaping done for you. In the picture, it's the label printer that replaces handwriting.

Each piece of code has its own description, called a spec. `FileSpec` describes a whole file, `TypeSpec` a class, `PropertySpec` a property, `FunSpec` a function, and `ParameterSpec` a parameter. You make each one with its builder and finish it with `build()`. Here is the smallest useful spec, one function, in both libraries:

""" + pair(J_GREET, K_GREET) + """

KotlinPoet's single line of output shows three habits. KotlinPoet writes `public` itself; its docs say it generates "explicit visibility modifiers" to maximize portability. It turned a body of one `return` into an expression body. And printed on its own, a spec spells out `kotlin.String`. Inside a `FileSpec`, the same type prints as `String`, with `import kotlin.String` at the top of the file.

The string `"return %S"` is a format string: code text with placeholders, which KotlinPoet fills from the arguments that follow it. Four placeholders do nearly all the work in this lesson:

| Placeholder | Takes | Prints |
|---|---|---|
| `%T` | a type: `ClassName`, `TypeName` | its name, and adds the import |
| `%N` | a name: a string or a spec | the name, with backticks if it needs them |
| `%S` | a string | a string literal, quoted, with `"` and `$` escaped |
| `%L` | anything | the value as it is, with no escaping |

`%S` given `Write $room on each "fragile" box` prints `"Write ${'$'}room on each \\"fragile\\" box"`, which is the same text as a Kotlin string, `$` and all. `%L` would paste it raw and break the file, and an unescaped `$room` would quietly read a variable named `room`. Each placeholder knows the one rule its kind of value needs, which is exactly what the handwriting kept forgetting.

**Pass types with `%T` and names with `%N`. Never paste them into the format string.**

The figure shows the whole builder as specs: five calls on the left, the part of `LampBuilder.kt` each one prints on the right. KotlinPoet, though, speaks in `ClassName` and `TypeName`, while our processor holds KSP symbols. The next step joins the two."""

ASIDE1 = {
    "title": "Is there a JavaPoet for Java processors?",
    "body": "Yes, and it came first. Square's JavaPoet is the original, and its README says it has been deprecated since 2020-10-10; it points users to Palantir's fork, package `com.palantir.javapoet`, whose latest release is 0.23.0. The shapes match KotlinPoet's (`TypeSpec`, `MethodSpec`, `FieldSpec`, `JavaFile`) with `$` instead of `%` in format strings: `$T`, `$N`, `$S`, `$L`. `JavaFile.writeTo(filer)` passes the originating elements to javac's `Filer`, the same job `writeTo(codeGenerator, ...)` does for KSP. The Java twins in this lesson use those names.",
}

# ---------------------------------------------------------------- section 2
J_SETTER = """// Closest Java equivalent: a javac annotation processor with JavaPoet
MethodSpec setterMethod(VariableElement param, ClassName builder) {
    String name = param.getSimpleName().toString();
    return MethodSpec.methodBuilder(name)
            .addModifiers(Modifier.PUBLIC)
            .addParameter(TypeName.get(param.asType()), name)
            .returns(builder)
            .addStatement("this.$N = $N", name, name)
            .addStatement("return this")
            .build();
}"""
K_SETTER = """fun setterFunction(param: KSValueParameter, builder: ClassName): FunSpec {
    val name = nameOf(param)
    return FunSpec.builder(name)
        .addParameter(name, param.type.toTypeName())
        .returns(builder)
        .addStatement("this.%N = %N", name, name)
        .addStatement("return this")
        .build()
}"""
J_WRITE = """// javac: the class is the originating element, and the Filer writes the file
TypeSpec builderType = TypeSpec.classBuilder(builder)
        // ... fields, setters, build()
        .addOriginatingElement(type)
        .build();
JavaFile.builder(packageName, builderType).build().writeTo(processingEnv.getFiler());"""
K_WRITE = """// KSP: the class's source file is the originating file, and writeTo hands it to the CodeGenerator
val builderType = TypeSpec.classBuilder(builder)
    // ... properties, setters, build()
    .addOriginatingKSFile(cls.containingFile!!)
    .build()
FileSpec.builder(builder).addType(builderType).build().writeTo(codeGenerator, aggregating = false)"""

S2 = """kotlinpoet-ksp is KotlinPoet's small companion for processors, also version 2.4.0. It adds extension functions that turn KSP symbols into KotlinPoet names, and a `writeTo` that hands a finished file to KSP. The builder processor uses four of them.

`cls.toClassName()` turns a `KSClassDeclaration`, the symbol for a class, into a `ClassName`: a package plus one or more simple names. For the nested drawer that's package `movemate` with the names `Kitchen` and `Drawer`, and `%T` prints `Kitchen.Drawer`. String surgery on `movemate.Kitchen.Drawer` can't tell you whether `Kitchen` is a package or a class. `ClassName` knows. The builder's own name comes from the same parts, `simpleNames.joinToString("")` plus `Builder`, so the drawer gets `KitchenDrawerBuilder`.

`param.type.toTypeName()` turns a `KSTypeReference`, the type as written in the source, into a `TypeName`, with every type argument and every `?` in place: `List<Box?>?`. To do that it resolves the type, the step lesson 3 called expensive, and if the type can't be resolved it throws (lesson 5 deals with that). The field needs the same type made nullable, and `copy(nullable = true)` does it without doubling anything: `String` becomes `String?`, and `String?` stays `String?`. That's the smudge from the template, gone.

Here is the setter in both languages:

""" + pair(J_SETTER, K_SETTER) + """

Read the Kotlin version aloud: a function named after the parameter, taking one parameter with the same name and type, and returning the builder. Its body sets the field and returns `this`. Both names go through `%N`, so `in` comes out as `` `in` `` in all three places.

The last two calls hand the file to KSP:

""" + pair(J_WRITE, K_WRITE) + """

The originating file is the source file an output was made from, here `Lamp.kt`. `aggregating = false` says that this output depends on its originating files and nothing else. Together they are KotlinPoet's way of writing lesson 2's `Dependencies(false, file)`: `writeTo` collects the originating files from the file's top-level specs and builds the `Dependencies` itself. `aggregating` has no default, so you decide every time. A wrong decision doesn't show on a clean build or in a test. It shows later, after an ordinary edit, as a generated file that has quietly disappeared. Lesson 7 makes that happen on purpose.

In the picture, the originating file is the note clipped to each card that says which box it came from. When that box is repacked next weekend, the helper knows exactly which card to redo.

Our processor is complete. Let's run it in a real build and read what it wrote."""

# ---------------------------------------------------------------- section 3
J_BUILT = """// The same builder for a Java record Lamp(String name, int bulbs, String shade)
public class LampBuilder {
  private String name;
  private Integer bulbs;
  private String shade;

  public LampBuilder name(String name) {
    this.name = name;
    return this;
  }

  // bulbs(...) and shade(...) have the same shape

  public Lamp build() {
    if (name == null) throw new IllegalStateException("LampBuilder: name was not set");
    if (bulbs == null) throw new IllegalStateException("LampBuilder: bulbs was not set");
    return new Lamp(name, bulbs, shade);
  }
}"""
K_BUILT = """// Generated by BuilderProcessor from Lamp. Do not edit.
package movemate

import kotlin.Int
import kotlin.String

public class LampBuilder {
  private var name: String? = null

  private var bulbs: Int? = null

  private var shade: String? = null

  public fun name(name: String): LampBuilder {
    this.name = name
    return this
  }

  public fun bulbs(bulbs: Int): LampBuilder {
    this.bulbs = bulbs
    return this
  }

  public fun shade(shade: String?): LampBuilder {
    this.shade = shade
    return this
  }

  public fun build(): Lamp = Lamp(
    name = name ?: error("LampBuilder: name was not set"),
    bulbs = bulbs ?: error("LampBuilder: bulbs was not set"),
    shade = shade,
  )
}"""

S3 = """Here is `LampBuilder.kt` exactly as the lab's processor writes it, next to the builder a Java developer would write for a Java `Lamp`:

""" + pair(J_BUILT, K_BUILT) + """

Read it from the top. The file says where it came from and which package it's in, then imports `kotlin.Int` and `kotlin.String`, which KotlinPoet always writes although Kotlin would find them anyway. `LampBuilder` holds three empty slots. Each setter fills one slot and hands the builder back, so the calls chain. `build()` calls `Lamp` with named arguments. A slot that must be filled either has a value or stops the program with a message that names the builder and the slot. `shade`, which may be null, goes in as it is. The two-space indent and the blank line between members are KotlinPoet's house style, which is why the lab's first test compares the whole text.

Is it worth a library? The template's text took 23 lines and got one of five cases clean. The KotlinPoet functions take 48 lines, twice as many, and get all five right, plus the `Bag` and `fun` cases from the Try its. The gain isn't fewer lines. It's the cases you never had to think of.

Now the limits. KotlinPoet models declarations, not expressions. Its docs put it plainly: "the body of methods and constructors is not modeled." A body is a format string such as `"%N = %N ?: error(%S),\\n"`. KotlinPoet checks the names and types you pass in, and nothing about what the code means. If `build()` passed the arguments in the wrong order, KotlinPoet would print it faithfully and the compiler would object. That's why every test in this lesson's lab compiles the generated code and calls it.

This is also where the picture breaks. A label printer prints exactly the words you type. KotlinPoet edits as it prints: it adds imports, `public` and backticks, and turns a one-line `return` into an expression body. So read its output at least once before you trust it.

The second limit is KSP's, and our builder inherits it. Lesson 3 showed that a parameter's `hasDefault` says that a default exists, never what it is. So `PlantBuilder` can't fill in `waterEveryDays = 7`, and it asks you instead: `PlantBuilder().kind("fern").potLitres(2.5).build()` stops with `PlantBuilder: waterEveryDays was not set`. The label says "spare bulb included", and the helper can't open the box to see which bulb.

**KotlinPoet checks the shape of the code, not its meaning. Compile and call what you generate.**

There's one thing this builder can't do yet: say no. Give it an interface, and the `!!` in `constructorParameters` is waiting for it."""

# ---------------------------------------------------------------- closing
CLOSING = """We started with a handwritten builder that worked for `Lamp` and broke on four ordinary classes. A label printer fixed each slip: imports from `%T`, honest nullable types from `toTypeName()` and `copy(nullable = true)`, `Kitchen.Drawer` from `toClassName()`, and backticks from `%N`.

In a processor of your own, search for a `$` inside a string that becomes generated code. Each one marks a place where a type or a name should be a placeholder.

Next, we'll feed the builder classes it can't build, an interface, an object and a private constructor, and teach it to say so on the exact file and line. What should a processor do when the label is wrong?"""

L = {
 "id": "ksp-04",
 "title": "Generating code with KotlinPoet",
 "minutes": 40,
 "goal": "By the end you can generate a Kotlin file with KotlinPoet (a class, a property, a function and a parameter), turn KSP symbols into KotlinPoet names with `toClassName()` and `toTypeName()`, choose between `%T`, `%N`, `%S` and `%L`, and hand the file to KSP with its originating file.",
 "opening": OPENING,
 "warmup": {
  "q": "A processor writes `private var first: Box? = null` into a generated file in package `movemate.van`. `Box` is declared in package `movemate` of the same module. What happens when the build compiles the generated file?",
  "options": ["It compiles: generated code can see every class in the module",
              "It fails with `Unresolved reference 'Box'`: a generated file needs imports like any other file",
              "KSP refuses to write the file, with an error from `[ksp]`",
              "It compiles with a warning about a missing import"],
  "answer": 1,
  "why": "A generated file is ordinary source code, compiled together with yours, so it follows the same rules: a type from another package needs an import or its full name. KSP doesn't check generated code at all; the error comes from the Kotlin compiler afterwards, as `e: LoadBuilder.kt:4:24 Unresolved reference 'Box'.` The first option is tempting because both files live in one module, but a module is not a package."
 },
 "sections": [
  {
   "h": "A builder from a string template, and four classes that break it",
   "body": S0,
   "try": {
    "title": "Watch the template break",
    "minutes": 4,
    "steps": [
     "Open `labs/ksp/src/demo/kotlin/workbench/ksp/l04/demo/TemplateBuilderDemo.kt` and read `TemplateBuilderProcessor` at the top. It writes the builder as text, one `appendLine` at a time.",
     "Predict which of the five cases will compile. Then run it from `labs/`: `" + DEMO + "TemplateBuilderDemoKt`.",
     "Add a sixth case to `cases`: a `Bag.kt` in package `movemate` holding `@Builder class Bag(val items: Map<String, List<Box>>)` (copy the import from the `Shelf` case). Predict, then run again."
    ],
    "expect": "The demo prints each generated file, then the compiler's first lines about it. `Lamp` and `Shelf` compile, each with `Redundant '?'`. `Load`, `Drawer` and `Crate` fail with the errors in this section; `Crate` alone gets 14. The `Bag` case compiles: every name in `Map<String, List<Box>>` happens to be visible from package `movemate` without an import. A template fails only on some inputs, which is why it so often passes the first test you write. On a busy machine the run takes 10 to 30 seconds, most of it the first compilation in memory.",
    "refs": [{"title": "KSP quickstart, with a string-template processor (Kotlin docs)", "url": "https://kotlinlang.org/docs/ksp-quickstart.html", "kind": "docs"}]
   }
  },
  {
   "h": "KotlinPoet builds the file from specs and four placeholders",
   "body": S1,
   "aside": ASIDE1,
   "figure": {"svg": FIG, "caption": "Each spec the processor builds becomes one part of the printed file; the originating file and writeTo connect the result to KSP."},
   "try": {
    "title": "Print the same classes with KotlinPoet",
    "minutes": 4,
    "steps": [
     "Open `PoetBuilderDemo.kt`, next to the template demo. It compiles the same classes with the lab's reference processor, prints each generated file, then calls every builder from a small `Use.kt`.",
     "Predict the import lines of `LoadBuilder.kt` and the type of the field in `ShelfBuilder.kt`. Then run `" + DEMO + "PoetBuilderDemoKt`.",
     "In the demo's `Crate`, add a second property, `` val `fun`: String ``, and in `Use.kt` add `` .`fun`(\"glue\") `` to the Crate line, before `.build()`. Predict how KotlinPoet writes the new setter, then run."
    ],
    "expect": "`LoadBuilder.kt` starts with `import movemate.Box`, and `ShelfBuilder` holds `private var boxes: List<Box?>? = null`, with one `?` at each level. Every builder compiles, and the last lines print `Lamp(name=desk lamp, bulbs=1, shade=null)`, `plates`, `[null, Box(label=cups, room=kitchen, weightGrams=900, fragile=false)]`, `Drawer(label=spoons)` and `hall`. With the new property, KotlinPoet writes ``public fun `fun`(`fun`: String): CrateBuilder``: `%N` met a keyword and added backticks.",
    "refs": [{"title": "KotlinPoet documentation", "url": "https://square.github.io/kotlinpoet/", "kind": "docs"},
             {"title": "%N for names (KotlinPoet docs)", "url": "https://square.github.io/kotlinpoet/n-for-names/", "kind": "docs"}]
   }
  },
  {
   "h": "kotlinpoet-ksp turns KSP symbols into KotlinPoet names",
   "body": S2,
   "try": {
    "title": "Run the builder processor in a real build",
    "minutes": 4,
    "steps": [
     "From `labs/`, run `./gradlew :ksp:app:kspL04Kotlin`. It runs the reference processor on the classes in `labs/ksp/app/src/l04`, the same way a real project would.",
     "Open `labs/ksp/app/build/generated/ksp/l04/kotlin/workbench/ksp/app/l04/van/LoadBuilder.kt`, then `KitchenDrawerBuilder.kt` and `CrateBuilder.kt` one folder up. Find the import, the nested name and the backticks.",
     "Run the two programs below. They call the generated builders from Kotlin and from Java."
    ],
    "code": app_demo("MoveDay", "MoveDayJava"),
    "expect": "Seven builders appear under `build/generated/ksp/l04/kotlin/`, one per `@Builder` class. Both programs print the same six lines: the lamp, the plates box, `load: first=plates, spares=2`, `Drawer(label=spoons, handles=2)`, `crate: in=hall, object=mirror` and `PlantBuilder: waterEveryDays was not set`. The Java version calls `.in(\"hall\")` and `.object(\"mirror\")` with no backticks, because neither word is a keyword in Java.",
    "refs": [{"title": "KSP interop: toClassName, toTypeName and writeTo (KotlinPoet docs)", "url": "https://square.github.io/kotlinpoet/interop-ksp/", "kind": "docs"}]
   }
  },
  {
   "h": "Reading the generated builder aloud, and where it stops",
   "body": S3
  }
 ],
 "compare": {
  "title": "The builder class, assembled with JavaPoet and with KotlinPoet",
  "java": {"title": "BuilderProcessor.java (javac, JavaPoet)", "src": """// Closest Java equivalent: a javac annotation processor with JavaPoet
TypeSpec builderType(TypeElement type, List<? extends VariableElement> params) {
    String pkg = processingEnv.getElementUtils().getPackageOf(type).getQualifiedName().toString();
    ClassName builder = ClassName.get(pkg, type.getSimpleName() + "Builder");
    TypeSpec.Builder spec = TypeSpec.classBuilder(builder).addModifiers(Modifier.PUBLIC);
    for (VariableElement p : params) {
        TypeName empty = TypeName.get(p.asType()).box();   // int becomes Integer, which can be null
        spec.addField(FieldSpec.builder(empty, p.getSimpleName().toString(), Modifier.PRIVATE).build());
        spec.addMethod(setterMethod(p, builder));
    }
    return spec.addMethod(buildMethod(type, params, builder))
            .addOriginatingElement(type)
            .build();
}
// then: JavaFile.builder(pkg, builderType(type, params)).build().writeTo(processingEnv.getFiler());"""},
  "kotlin": {"title": "BuilderProcessor.kt (KSP, KotlinPoet)", "src": """fun builderType(cls: KSClassDeclaration): TypeSpec {
    val builder = builderName(cls)
    val params = constructorParameters(cls)
    return TypeSpec.classBuilder(builder)
        .addProperties(params.map(::builderProperty))      // private var name: String? = null
        .addFunctions(params.map { setterFunction(it, builder) })
        .addFunction(buildFunction(cls, builder))
        .addOriginatingKSFile(cls.containingFile!!)
        .build()
}
// then: builderFile(cls).writeTo(codeGenerator, aggregating = false)"""},
  "note": "The plan is the same call for call: a class, one field and one setter per parameter, `build()`, and the input the output came from. Three differences matter. JavaPoet needs `addModifiers(Modifier.PUBLIC)`, while KotlinPoet writes `public` itself. To let a Java field start empty, `box()` turns `int` into `Integer`; Kotlin says the same with `copy(nullable = true)`, and its `TypeName` keeps the `?` right on every type argument too. And the originating input differs in size: javac's `Filer` takes elements (the class), KSP takes files (`Lamp.kt`). Gradle's incremental Java processing sorts whole processors into isolating and aggregating, while KSP decides per output, which lesson 7 takes apart."
 },
 "worked": {
  "title": "Generate one more function: Lamp.toBuilder()",
  "steps": [
   {"say": "A user of `LampBuilder` asks for the other direction: start from an existing `Lamp`, change one value, build again. Start, as always, from the text you want KotlinPoet to print.",
    "code": "public fun Lamp.toBuilder(): LampBuilder = LampBuilder().name(name).bulbs(bulbs).shade(shade)\n\n// in use: copy a lamp with two bulbs\nval brighter = Lamp(\"desk lamp\", 1, null).toBuilder().bulbs(2).build()", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "public static LampBuilder toBuilder(Lamp lamp) {\n    return new LampBuilder().name(lamp.name()).bulbs(lamp.bulbs()).shade(lamp.shade());\n}\n\n// in use: copy a lamp with two bulbs\nLamp brighter = toBuilder(new Lamp(\"desk lamp\", 1, null)).bulbs(2).build();"},
   {"say": "The function first: its name, a receiver and the return type. The receiver makes it an extension function, which Java doesn't have, so the Java twin is a static method that takes the lamp as a parameter.",
    "code": "// 1. the function: name, receiver, return type\nval toBuilder = FunSpec.builder(\"toBuilder\")\n    .receiver(cls.toClassName())\n    .returns(builder)", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "// 1. the method: name, modifiers, parameter, return type\nMethodSpec.Builder toBuilder = MethodSpec.methodBuilder(\"toBuilder\")\n        .addModifiers(Modifier.PUBLIC, Modifier.STATIC)\n        .addParameter(ClassName.get(type), \"lamp\")\n        .returns(builder);"},
   {"say": "Then the body: one chained call per property. `%T` writes the builder's type, and `%N` writes each name, backticks included when a name needs them.",
    "code": "// 2. the body: start a builder, then one setter call per property\nval body = CodeBlock.builder().add(\"return %T()\", builder)\nfor (param in constructorParameters(cls)) {\n    body.add(\".%N(%N)\", nameOf(param), nameOf(param))\n}\ntoBuilder.addCode(body.build())", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "// 2. the body: start a builder, then one setter call per record component\nCodeBlock.Builder body = CodeBlock.builder().add(\"return new $T()\", builder);\nfor (VariableElement p : params) {\n    String name = p.getSimpleName().toString();\n    body.add(\".$N(lamp.$N())\", name, name);\n}\ntoBuilder.addStatement(body.build());"},
   {"say": "Add it to the file with `addFunction(toBuilder.build())` and run. KotlinPoet prints exactly the line from step 1, and `brighter` comes out as `Lamp(name=desk lamp, bulbs=2, shade=null)`. This works only because every parameter of `Lamp` is also a property (`val`), so `name` can be read back. A plain constructor parameter has nothing to read: that is one more thing a careful processor checks before it writes, the subject of the next lesson.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "The @Builder processor, written with KotlinPoet",
  "minutes": 15,
  "files": [f"{LAB}/main/kotlin/workbench/ksp/l04/BuilderProcessor.kt", f"{LAB}/test/kotlin/workbench/ksp/l04/BuilderProcessorTest.kt", f"{APP}/kotlin/workbench/ksp/app/l04/MoveMate.kt"],
  "run": "./gradlew :ksp:test --tests 'workbench.ksp.l04.*'",
  "steps": [
   "Open `BuilderProcessor.kt` in `labs/ksp/src/main/kotlin/workbench/ksp/l04/` and run the tests first. All five fail with `KSP generated no movemate/LampBuilder.kt` and the warning `l04 not done yet: builderFile: ...`.",
   "Find and Check are given, in `processBuilders`: it asks the Resolver, the helper's clipboard that KSP passes to `process`, for every `@Builder` symbol and skips anything that isn't a class declaration. Read them; lesson 5 makes Check strict.",
   "Read is given too: `constructorParameters(cls)` lists the parameters, and inside each spec `param.type.toTypeName()` turns a type into a KotlinPoet `TypeName`.",
   "Write, the property: fill in `builderProperty` so it prints `private var name: String? = null`. Then the function and its parameter: `setterFunction`. Then the class: `builderType`, with the originating file. Then the file: `builderFile`, with the comment line from its KDoc. `buildFunction` is given; read how it uses `%T`, `%N` and `%S`.",
   "Prove: run the tests until all five pass. Then run it in the real build with your processor, `./gradlew :ksp:app:kspL04Kotlin -Pmine=l04`, open `labs/ksp/app/build/generated/ksp/l04/kotlin/workbench/ksp/app/l04/LampBuilder.kt`, and run `./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l04.MoveDayKt -Pmine=l04`. While your processor is unfinished, use only the `kspL04Kotlin` task: the app's code calls the builders, so compiling it fails until they exist.",
   "From memory: do the drill below without looking at your code."
  ],
  "hints": [
   "`PropertySpec.builder(name, type, KModifier.PRIVATE).mutable(true).initializer(\"null\").build()`. `initializer` takes a format string, so `\"null\"` prints the word `null`.",
   "In `setterFunction`, `addParameter(name, type)` adds the parameter, `returns(builder)` the return type, and two `addStatement` calls the body. Use `%N` for both names in `\"this.%N = %N\"`.",
   "`builderType` is `TypeSpec.classBuilder(builder)`, then `addProperties`, `addFunctions`, `addFunction(buildFunction(cls, builder))`, `addOriginatingKSFile(cls.containingFile!!)` and `build()`.",
   "If the first test fails on whitespace, compare with the expected text in the test. KotlinPoet adds the blank lines and the two-space indent itself; don't add your own `\\n`."
  ],
  "done_when": "All five tests in `BuilderProcessorTest` pass, and `./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l04.MoveDayKt -Pmine=l04` prints the same six lines as the reference."
 },
 "drill": {
  "title": "A property and a setter, from memory",
  "minutes": 5,
  "prompt": "Close this page. For a `KSValueParameter` called `param` and a builder `ClassName` called `builder`, write the KotlinPoet code for the field `private var name: String? = null` and for the setter `public fun name(name: String): LampBuilder`, which sets the field and returns the builder. Then write the JavaPoet version for a `VariableElement`. Which placeholder carries the names, and why?",
  "answer": {"lang": "kotlin", "src": "val name = param.name!!.asString()\n\n// the field: the parameter's type made nullable, starting empty\nval field = PropertySpec.builder(name, param.type.toTypeName().copy(nullable = true), KModifier.PRIVATE)\n    .mutable(true)\n    .initializer(\"null\")\n    .build()\n\n// the setter: %N for names, so a keyword gets backticks\nval setter = FunSpec.builder(name)\n    .addParameter(name, param.type.toTypeName())\n    .returns(builder)\n    .addStatement(\"this.%N = %N\", name, name)\n    .addStatement(\"return this\")\n    .build()",
             "alt": {"lang": "java", "title": "JavaPoet", "src": "String name = param.getSimpleName().toString();\n\n// the field: boxed, so it can start as null\nFieldSpec field = FieldSpec.builder(TypeName.get(param.asType()).box(), name, Modifier.PRIVATE).build();\n\n// the setter: $N for names\nMethodSpec setter = MethodSpec.methodBuilder(name)\n        .addModifiers(Modifier.PUBLIC)\n        .addParameter(TypeName.get(param.asType()), name)\n        .returns(builder)\n        .addStatement(\"this.$N = $N\", name, name)\n        .addStatement(\"return this\")\n        .build();"}}
 },
 "recap": [
  "Generated code is ordinary source code, compiled with yours: it needs imports, correct types and legal names. A string template gets them wrong on ordinary classes, and the compiler, not KSP, reports it.",
  "KotlinPoet builds a file from specs (`FileSpec`, `TypeSpec`, `PropertySpec`, `FunSpec`, `ParameterSpec`) and format strings with placeholders: `%T` for types (imported), `%N` for names (escaped), `%S` for strings (quoted), `%L` for literals (as is).",
  "kotlinpoet-ksp converts KSP symbols: `toClassName()` gets package and nesting right, `toTypeName()` keeps every `?` and type argument, and `copy(nullable = true)` makes a type nullable without doubling the `?`.",
  "`addOriginatingKSFile` plus `writeTo(codeGenerator, aggregating = false)` hands the file to KSP with the source file it came from; a wrong choice shows only on a later incremental build.",
  "The limit: KotlinPoet models declarations, not expressions, so bodies are still format strings and the compiler is the referee. And KSP can't see default values, so the builder can't fill them in."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "In `CodeBlock.of(\"return %? (\", cls.toClassName())`, the class is the nested `Kitchen.Drawer` from another package. Which placeholder belongs in place of `%?`?",
   "options": ["`%T`: it prints the type's name and adds the import", "`%N`: it prints a name with backticks if needed", "`%S`: it quotes the value", "`%L`: it pastes the value as it is"],
   "answer": 0, "why": "`%T` is the type placeholder: it prints `Kitchen.Drawer` and adds `import movemate.Kitchen` to the file when needed. `%L` would paste the `ClassName`'s text without arranging the import, so the code might not compile in another package. `%N` is for names of properties, functions and parameters, and `%S` would turn the type into a string literal."},
  {"q": "A constructor parameter is declared `val tags: List<String>?`. What does `param.type.toTypeName().copy(nullable = true)` print as a field type?",
   "options": ["`List<String>??`", "`List<String?>?`", "`List<String>?`", "`List<String>`"],
   "answer": 2, "why": "`toTypeName()` keeps the type as declared, `List<String>?`, and `copy(nullable = true)` sets the outer type's nullability, which is already on, so nothing doubles. It doesn't touch the type argument, so `String` stays non-null. The first option is what the string template printed for `Lamp.shade`: `String??`, which the compiler flags as `Redundant '?'`."},
  {"q": "A processor tags its builder with `addOriginatingKSFile(...)` but calls `writeTo(codeGenerator, aggregating = false)` for a file that lists every `@Builder` class in the module. Where does the mistake show first?",
   "options": ["The processor doesn't compile: `aggregating` is checked against the content", "In the kctfork tests, which compile in memory", "Nowhere: KSP corrects the flag from the content", "On a later incremental build, as a list that silently misses classes"],
   "answer": 3, "why": "`aggregating` describes what the output depends on, and nothing checks it against what the file contains. A list of every class depends on every file, so it must be aggregating. Declared isolating, it is regenerated only from the files that changed, and the other classes drop out. A clean build and kctfork (which starts fresh each time) both look fine; lesson 7 reproduces the failure."},
  {"q": "What does `%S` print for the Kotlin string `Write $room on each \"fragile\" box`?",
   "options": ["`\"Write ${'$'}room on each \\\"fragile\\\" box\"`", "`Write $room on each \"fragile\" box`, unquoted", "`\"Write $room on each \\\"fragile\\\" box\"`, so `$room` becomes a template", "It throws, because `$` isn't allowed in `%S`"],
   "answer": 0, "why": "`%S` writes a string literal that means exactly the text you passed: it adds quotes and escapes `\"` and `$`, which in Kotlin source would otherwise start a template. Unquoted output is what `%L` gives. If you want a real string template in the generated code, KotlinPoet has `%P`, which doesn't escape `$`."},
  {"q": "From lesson 3: `toTypeName()` on a parameter's `KSTypeReference` resolves the type before it converts it. What does resolving do, and why did lesson 3 call it the expensive step?",
   "options": ["It reads the type's name as written, which is free", "It loads the class with reflection while the processor runs", "It asks the compiler what the written name refers to, possibly across other files, and KSP records that lookup for incremental builds", "It compiles the generated file early to check the type"],
   "answer": 2, "why": "A `KSTypeReference` is the type as written; `resolve()` finds the declaration it refers to, including type arguments and nullability, which can mean analysing other files. KSP's docs call type resolution one of the most expensive operations in its API, and each resolution adds a dependency that incremental builds track. Nothing runs or loads with reflection: KSP only reads declarations.",
   "from": "ksp-03"}
 ],
 "flashcards": [
  {"front": "`%T`, `%N`, `%S`, `%L`: what does each take?", "back": "`%T` a type (adds the import), `%N` a name (adds backticks when needed), `%S` a string (quoted and escaped), `%L` any value, pasted as it is."},
  {"front": "What does `toClassName()` give for the nested class `movemate.Kitchen.Drawer`?", "back": "A `ClassName` with package `movemate` and simple names `Kitchen` and `Drawer`, printed as `Kitchen.Drawer`."},
  {"front": "Why make a field nullable with `copy(nullable = true)` rather than by adding `?` to the text?", "back": "`copy` sets nullability, so an already nullable type stays `String?`. Adding `?` to the text doubles it: `String??`."},
  {"front": "Who reports an error inside generated code, KSP or the compiler?", "back": "The Kotlin compiler, after KSP has written the file: `e: file:///.../LoadBuilder.kt:4:24 ...`, with a column and no `[ksp]`."},
  {"front": "What does `writeTo(codeGenerator, aggregating = false)` use for the output's `Dependencies`?", "back": "The originating files tagged with `addOriginatingKSFile` on the file's top-level specs, plus your `aggregating` choice, which has no default."},
  {"front": "Does KotlinPoet check the code inside a function body?", "back": "No. Bodies are format strings; KotlinPoet checks names and types, and the compiler checks the meaning later."}
 ],
 "terms": [
  {"term": "Builder", "plain": "A small class that collects an object's values one call at a time, then creates the object with `build()`."},
  {"term": "String template", "plain": "Text with values pasted in, here used to write source code by hand."},
  {"term": "KotlinPoet", "plain": "A library that writes Kotlin source files from descriptions (specs), with imports, escaping and formatting done for you."},
  {"term": "Spec", "plain": "KotlinPoet's description of one piece of code: `FileSpec`, `TypeSpec`, `PropertySpec`, `FunSpec`, `ParameterSpec`."},
  {"term": "Placeholder", "plain": "A marker in a format string, such as `%T` or `%N`, that KotlinPoet replaces with a correctly written argument."},
  {"term": "kotlinpoet-ksp", "plain": "KotlinPoet's companion library that turns KSP symbols into KotlinPoet names and writes files through KSP."},
  {"term": "Originating file", "plain": "The source file a generated output was made from; KSP uses it to know which outputs to redo when a file changes."},
  {"term": "JavaPoet", "plain": "The Java counterpart of KotlinPoet for javac annotation processors; Square's original is deprecated, Palantir's fork carries on."}
 ],
 "explain_back": {
  "prompt": "A teammate's processor writes a builder with a string template. It works in their tests, but in the real project the build fails with `Unresolved reference 'Box'` in the generated file, although `Box` exists. Explain what is going on and what KotlinPoet would do differently.",
  "answer": "The generated builder is an ordinary Kotlin file, and the compiler reads it like any other. It lives in one package and uses `Box` from another, so it needs an import, and the template never writes imports. Their tests passed because all their test classes sat in one package, where the short name happened to work. The template pastes `KSType`'s display name, which is meant for people, not for another file. With KotlinPoet you pass the type itself, as a `TypeName` from `toTypeName()`, through the `%T` placeholder. KotlinPoet then prints the short name and adds the matching import at the top of the file. The same approach fixes nullable types with `copy(nullable = true)`, nested classes with `toClassName()`, and keyword names with `%N`. The compiler still has the last word, so a test should compile the generated file and call it."
 },
 "deeper": {
  "minutes": 8,
  "body": "Three more placeholders and behaviours are worth knowing. `%P` writes a string template: like `%S`, but it leaves `$` alone, so `$name` stays a template in the generated code. `%M` writes a member reference from a `MemberName`, for example `MemberName(\"kotlin.collections\", \"mutableMapOf\")`, and adds the import for it. When two types share a simple name, say `move.Box` and `storage.Box` in one generated file, KotlinPoet 2.4.0 imports both under aliases (`import move.Box as MoveBox`) instead of guessing.\n\nGeneric classes need one more step. A class such as `Shelf<T : Comparable<T>>` uses its type parameter in its properties, and KotlinPoet has to know which `T` is meant. The tool is a `TypeParameterResolver`, made with `toTypeParameterResolver()` on the class's type parameters and passed to `toTypeName(...)`. Since 2.4.0 the default resolver also finds type parameters from the enclosing declarations instead of throwing, so older blog posts that say it throws describe an earlier version.\n\nKotlinPoet 2.0 changed how long lines wrap: spaces no longer wrap by default, `♢` marks a space where a line may break, and `·` is now an ordinary space. Golden-file tests, which compare a whole generated file with a stored copy, will notice such changes across KotlinPoet upgrades. Pair each golden test with one that compiles and calls the generated code, as this lesson's lab does."
 },
 "sources": [
  {"title": "KotlinPoet documentation", "url": "https://square.github.io/kotlinpoet/"},
  {"title": "KotlinPoet: KSP interop (toClassName, toTypeName, writeTo)", "url": "https://square.github.io/kotlinpoet/interop-ksp/"},
  {"title": "KotlinPoet: %N for names", "url": "https://square.github.io/kotlinpoet/n-for-names/"},
  {"title": "KSP quickstart (Kotlin docs)", "url": "https://kotlinlang.org/docs/ksp-quickstart.html"},
  {"title": "Palantir JavaPoet (the maintained JavaPoet fork)", "url": "https://github.com/palantir/javapoet"}
 ]
}
out = ROOT / "content/lessons/ksp-04.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
