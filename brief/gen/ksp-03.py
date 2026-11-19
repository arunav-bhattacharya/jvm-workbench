import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/ksp/src"
app = "labs/ksp/app/src/l03"
P = "kotlin/workbench/ksp/l03"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :ksp:demo -Pmain=workbench.ksp.l03.demo."


def kdemo(name):
    """A kctfork demo: Kotlin only (a processor run in memory has no Java twin)."""
    f = f"{lab}/demo/kotlin/workbench/ksp/l03/demo/{name}.kt"
    return {"lang": "kotlin", "title": f"{name}.kt", "src": read(f), "run": RUN + name + "Kt", "file": f, "solo": True}


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


FIG = (
    '<svg viewBox="0 0 700 320" role="img" aria-label="The symbol tree of a class: a KSFile holds the KSClassDeclaration '
    'Lamp, which carries a KSAnnotation and holds a KSPropertyDeclaration and the constructor, a KSFunctionDeclaration; '
    'the constructor holds the KSValueParameter shade, whose KSTypeReference String? turns into a KSType by resolve()">'
    '<rect class="box" x="20" y="20" width="220" height="40" rx="8"/>'
    '<text class="t-s t-code" x="130" y="45" text-anchor="middle">KSFile  MoveMate.kt</text>'
    '<path class="ln" d="M40 60 V100 H58"/>'
    '<rect class="box-a" x="60" y="80" width="240" height="40" rx="8"/>'
    '<text class="t-s t-code" x="180" y="105" text-anchor="middle">KSClassDeclaration  Lamp</text>'
    '<path class="ln-d" d="M300 92 H436"/>'
    '<rect class="box-dim" x="440" y="72" width="240" height="40" rx="8"/>'
    '<text class="t-s t-code" x="560" y="97" text-anchor="middle">KSAnnotation  @Label</text>'
    '<path class="ln" d="M300 110 H400 V156 H436"/>'
    '<rect class="box" x="440" y="136" width="240" height="40" rx="8"/>'
    '<text class="t-s t-code" x="560" y="161" text-anchor="middle">KSPropertyDeclaration  shade</text>'
    '<path class="ln" d="M80 120 V160 H98"/>'
    '<rect class="box" x="100" y="140" width="260" height="40" rx="8"/>'
    '<text class="t-s t-code" x="230" y="165" text-anchor="middle">KSFunctionDeclaration  &lt;init&gt;</text>'
    '<path class="ln" d="M120 180 V220 H138"/>'
    '<rect class="box" x="140" y="200" width="240" height="40" rx="8"/>'
    '<text class="t-s t-code" x="260" y="225" text-anchor="middle">KSValueParameter  shade</text>'
    '<path class="ln" d="M160 240 V280 H178"/>'
    '<rect class="box-b" x="180" y="260" width="220" height="40" rx="8"/>'
    '<text class="t-s t-code" x="290" y="285" text-anchor="middle">KSTypeReference  String?</text>'
    '<line class="ln-a" x1="404" y1="280" x2="436" y2="280" marker-end="url(#arr)"/>'
    '<text class="t-s t-a t-code" x="420" y="254" text-anchor="middle">resolve()</text>'
    '<rect class="box-ok" x="440" y="230" width="240" height="80" rx="8"/>'
    '<text class="t t-code" x="560" y="254" text-anchor="middle">KSType</text>'
    '<text class="t-s t-code" x="560" y="276" text-anchor="middle">declaration = String</text>'
    '<text class="t-s t-code" x="560" y="296" text-anchor="middle">nullability = NULLABLE</text>'
    '</svg>'
)

# ---------------------------------------------------------------- opening
OPENING = """Picture the helper reading box labels before the move. "Desk lamp, one bulb, no shade" is easy. "Bookshelf, three shelves, a list of books" needs a word about what the list holds. Some labels use a shorthand that only makes sense once you look it up, and a few are written in another language.

In the last lesson, our processor read one thing from each label, the names of the constructor's properties, and wrote a card. A label holds much more: the type of each property, whether it may be missing (null), whether it has a default, and notes stuck on single lines. The easy trap is to print a type with `toString()`. It looks right on easy classes, and on the first tricky one it prints `[typealias Litres]`.

In this lesson, we'll walk the whole tree of a class's label, print its typed shape correctly, read the values written on its sticky notes, and read a Java class too. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
TREE = """file Rooms.kt  package=movemate
  class Plant  kind=CLASS  modifiers=[DATA]  origin=KOTLIN
    property kind: String
    property potLitres: Double
    property waterEveryDays: Int
    function component1(): String  origin=SYNTHETIC
    function component2(): Double  origin=SYNTHETIC
    function component3(): Int  origin=SYNTHETIC
    function copy(kind: String (hasDefault), potLitres: Double (hasDefault), waterEveryDays: Int (hasDefault)): Plant  origin=SYNTHETIC
    function <init>(kind: String, potLitres: Double, waterEveryDays: Int (hasDefault)): Plant  origin=KOTLIN
  class Mirror  kind=CLASS  modifiers=[]  origin=KOTLIN
    property widthCm: Int
    property heightCm: Int
    property glass: String
    function areaCm2(): Int  origin=KOTLIN
      property area: Int
    function <init>(widthCm: Int, heightCm: Int, glass: String): Mirror  origin=KOTLIN"""
J_WALK = """// Closest Java equivalent: a class's members in a javac processor
for (Element member : cls.getEnclosedElements()) {
    switch (member.getKind()) {
        case FIELD -> messager.printMessage(Diagnostic.Kind.NOTE,
                "field " + member.getSimpleName() + ": " + member.asType());
        case CONSTRUCTOR, METHOD -> messager.printMessage(Diagnostic.Kind.NOTE,
                "method " + member.getSimpleName() + ((ExecutableElement) member).getParameters());
        default -> { }
    }
}"""
K_WALK = """for (member in cls.declarations) {
    when (member) {
        is KSPropertyDeclaration -> logger.warn("property ${member.simpleName.asString()}: ${member.type}")
        is KSFunctionDeclaration -> logger.warn("function ${member.simpleName.asString()}" +
            member.parameters.map { it.name?.asString() })
        else -> {}
    }
}"""

S0 = """A processor is the program that KSP, Kotlin Symbol Processing, runs during the build: it reads the classes that carry an annotation and writes new files. Everything KSP knows about your code comes as a tree of **symbols**, one node for each named thing. A **declaration** is a symbol you wrote yourself, such as a class or a function. Each file is the root of its own small tree. A `KSFile` holds `KSClassDeclaration`s. Each class holds its properties (`KSPropertyDeclaration`), its functions (`KSFunctionDeclaration`) and any classes nested inside it, and each function holds its parameters (`KSValueParameter`). In the moving-house picture, the file is a box, and this tree is everything written on its label.

`TreeDemo` prints that tree for a small Kotlin file with `Plant` and `Mirror`, and for a Java file we'll meet in the last section:

```text
""" + TREE + """
```

Let's read it from the top. `kind=CLASS` comes from `classKind`, which tells a class from an `INTERFACE`, an `OBJECT` or an `ENUM_CLASS`; lesson 2's Check move used it. `modifiers=[DATA]` lists only the modifiers written in the source. Plant is public and final too, but nobody wrote those words, so they're not on the list. `origin=KOTLIN` says the symbol came from Kotlin source.

The functions hold two surprises. The constructor is a function named `<init>`; for a class with a primary constructor, `primaryConstructor` gives you the same node directly. And `component1` to `component3` and `copy` are listed too, marked `origin=SYNTHETIC`. Nobody wrote them, but a data class will have them, so KSP shows them.

Now look for what's missing. `waterEveryDays: Int (hasDefault)` says the parameter has a default value, and nothing more: the `7` is an expression, and KSP shows no expressions. `areaCm2(): Int` is there with its name and return type, and inside it `property area: Int`, because a local `val` is a named declaration too. The multiplication `widthCm * heightCm` is nowhere. That's lesson 1's limit, now proved: the helper reads labels, never what's packed.

javac builds the same kind of tree from `Element`s: a `TypeElement` for a class, an `ExecutableElement` for a method or constructor, and a `VariableElement` for a field or parameter. Walking a class's members looks much the same in both:

""" + pair(J_WALK, K_WALK) + """

One difference shows already. Java has no primary constructors and no data classes, so the Kotlin label says more than any javac processor could ever read from Java code.

**KSP gives you every declaration and its type, and never an expression. Plan your processor around what the label says.**

The tree prints types as text, such as `Int` and `String`. Printing them right is harder than it looks."""

# ---------------------------------------------------------------- section 1
TABLE = """parameter                toString()                name only  typeText
Crate.shade              String?                   String     String?
Crate.books              List<String>              List       List<String>
Crate.water              [typealias Litres]        Litres     Litres
Crate.sizes              Map<String, List<Int?>>?  Map        Map<String, List<Int?>>?
Crate.odds               List<*>                   List       List<*>
Crate.onDrop             Function1<Int, Unit>      Function1  Function1<Int, Unit>
MovingCrate.label        (String..String?)         String     String!
MovingCrate.weightGrams  Int                       Int        Int"""
J_TYPE = """// Closest Java equivalent: printing a javac TypeMirror (javax.lang.model.type)
static String typeText(TypeMirror type) {
    if (type instanceof DeclaredType declared) {                  // a class type, maybe with arguments
        String name = declared.asElement().getSimpleName().toString();
        List<? extends TypeMirror> arguments = declared.getTypeArguments();
        if (arguments.isEmpty()) return name;
        return name + arguments.stream().map(Labels::typeText).collect(Collectors.joining(", ", "<", ">"));
    }
    return type.toString();                                       // int, boolean and the other primitives
}"""
K_TYPE = """// the core of typeText; the lab adds the * and ! cases
fun typeText(ref: KSTypeReference): String {
    val type = ref.resolve()                                      // the expensive step
    val name = type.declaration.simpleName.asString()
    val arguments = if (type.arguments.isEmpty()) "" else
        type.arguments.joinToString(", ", "<", ">") { typeText(it.type!!) }   // the same, all the way down
    val mark = if (type.nullability == Nullability.NULLABLE) "?" else ""
    return name + arguments + mark
}"""

S1 = """Each parameter's type arrives as a `KSTypeReference`, the type as it's written in the source: `String?`, or `Litres`, not yet looked up. Calling `resolve()` turns it into a `KSType`, the type the compiler means, with its declaration (the class it names), its nullability and its type arguments. Resolving is a real lookup through imports, packages and type aliases. KSP's docs call it "one of the most expensive operations in the KSP API", so KSP resolves nothing until you ask.

In the picture, `resolve()` is the helper looking up a word on the label to see what it refers to: is `Litres` a box in this house, or shorthand for something else? Each lookup takes time. Here the picture breaks a little, too: unlike a person, KSP writes down every lookup a processor makes, because a later build needs to know which boxes each card depended on (lesson 7).

The label we want is the class's typed shape, `Lamp(name: String, bulbs: Int, shade: String?)`. Two quick attempts come to mind: print the reference with `toString()`, or resolve it and print the declaration's name. `ShapeDemo` tries both, on a crate with tricky types and on a small Java class, next to the lab's `typeText`:

```text
""" + TABLE + """
```

The name-only column fails at once. It drops every `?` and every `<...>`, so `shade` becomes a `String` that can never be empty, which the first lamp without a shade will quickly disprove, and `sizes` loses its key and value types along with its `?`. The `toString()` column looks right on easy types, and that's what makes it a trap. On the type alias, a second name for a type (`typealias Litres = Double`), it prints `[typealias Litres]`. On the Java class it prints `(String..String?)`. KSP's `toString()` is a display form for people reading logs, not a promise about Kotlin syntax.

So we build the text ourselves from what `KSType` says, in three steps. First the name, `type.declaration.simpleName`. Then the type arguments, each printed the same way, because `List<Int?>` holds a type that needs exactly the same treatment: a recursive function. Then the nullability mark. Here is the core of it, with javac's closest equivalent first:

""" + pair(J_TYPE, K_TYPE) + """

Two cases are left for the lab. A star projection, `List<*>` (a list of something unknown), has a type argument with no type at all: its `type` is null, so `it.type!!` would crash, and the argument's `variance` says `STAR`. And a **platform type** is a type from Java, where nothing says whether `null` is allowed; its nullability is `PLATFORM`, and Kotlin writes it `String!`. Printing `Function1<Int, Unit>` for `(Int) -> Unit` is fine for a label: both name the same type, and Kotlin simply has a shorter way to write it.

The Java twin can't print `?` at all. A javac `TypeMirror` knows nothing about nullability, because Java's type system has none; Java code marks it with annotations such as `@Nullable` instead. That's one of the Kotlin facts a KSP processor keeps and a Java processor never sees.

**Resolve each reference once, then build the text from the resolved type: name, arguments, mark. toString() is for your eyes, not for your output.**

Each line of the label now prints right. Some boxes also carry notes with values written on them."""

# ---------------------------------------------------------------- section 2
J_ANN = """public enum Care { NORMAL, GENTLE, UPRIGHT }

@Target(ElementType.TYPE)
@Retention(RetentionPolicy.SOURCE)
public @interface Handling {
    Care care() default Care.NORMAL;
    boolean stackable() default true;
    Class<?> packWith() default Object.class;
}"""
K_ANN = """enum class Care { NORMAL, GENTLE, UPRIGHT }

@Target(AnnotationTarget.CLASS)
@Retention(AnnotationRetention.SOURCE)
annotation class Handling(
    val care: Care = Care.NORMAL,
    val stackable: Boolean = true,
    val packWith: KClass<*> = Any::class,
)"""
J_ARGS = """// Closest Java equivalent: reading annotation values in a javac processor
Map<? extends ExecutableElement, ? extends AnnotationValue> written = handling.getElementValues();
Map<? extends ExecutableElement, ? extends AnnotationValue> all =
        processingEnv.getElementUtils().getElementValuesWithDefaults(handling);
for (var entry : all.entrySet()) {
    String name = entry.getKey().getSimpleName().toString();       // care, stackable, packWith
    Object value = entry.getValue().getValue();   // an enum: a VariableElement; a class: a TypeMirror
    boolean isDefault = !written.containsKey(entry.getKey());
}"""
K_ARGS = """val handling = annotationNamed(cls, "workbench.ksp.annotations.l03.Handling") ?: return null
fun argument(name: String) = handling.arguments.first { it.name?.asString() == name }   // by name

val care = argument("care").value as KSClassDeclaration       // an enum value: the entry's declaration
val stackable = argument("stackable").value as Boolean        // a Boolean: itself
val packWith = argument("packWith").value as KSType           // a class: a KSType
val chosen = !argument("stackable").isDefault()               // false when the source didn't write it"""
BOOKSHELF = """--- movemate/BookshelfLabel.kt
// Generated by LabelProcessor from Bookshelf. Do not edit.
package movemate

object BookshelfLabel {
    const val SHAPE: String = "Bookshelf(shelves: Int, books: List<String>)"
    const val ROOM: String = "study"
    const val HANDLING: String = "care=UPRIGHT, stackable=true (default), packWith=Lamp"
}"""

S2 = """An annotation, a note written with `@` on a declaration, can carry values, called its **arguments**: `@Room("study")` says which room a box goes to. MoveMate's lesson 3 note, `@Handling`, has three, each of a different kind and each with a default:

""" + pair(J_ANN, K_ANN) + """

The two declarations line up closely. Java writes each argument as a method with a `default`; Kotlin writes it as a constructor property with a default value. One difference: Java's "no particular class" is usually `Object.class`, and Kotlin's here is `Any::class`.

KSP gives each annotation on a symbol as a `KSAnnotation`, and its `arguments` as a list of `KSValueArgument`, each with a `name` and a `value`. What kind of object the value is depends on the argument's type. A `String` or a `Boolean` arrives as itself. A class argument (`KClass`) arrives as a `KSType`. An enum value arrives as a `KSClassDeclaration`, the declaration of the enum entry, so its `simpleName` is `UPRIGHT`.

Running it showed two details worth remembering. The list holds every parameter of the annotation, including the ones the source didn't write, filled in with their defaults; such an argument has `origin=SYNTHETIC`, which `isDefault()` checks. And the list isn't in declaration order. KSP lists the written arguments first, in the order they were written, and the defaults after them. So look arguments up by name, never by position:

""" + pair(J_ARGS, K_ARGS) + """

javac draws the same line differently: `getElementValues()` holds only what was written, and `getElementValuesWithDefaults` fills in the rest, so a default is whatever the first map lacks.

Finding the annotation itself needs one more bit of care. Its `shortName` is the name as written, `Room`, and another package could have a `Room` of its own. The lab's given `annotationNamed` compares the short name first, which costs nothing, and resolves `annotationType` to its full name only when the short name matches: the cheap check first, then the expensive one, as KSP's docs advise.

`LabelDemo` runs the whole lesson 3 processor on a lamp and on a bookshelf marked `@Room("study") @Handling(care = Care.UPRIGHT, packWith = Lamp::class)`. Here is the bookshelf's label:

```text
""" + BOOKSHELF + """
```

`stackable` wasn't written, so it says `true (default)`. The lamp's label has a `SHAPE` line and nothing else, because the lamp carries neither note.

**Look annotation arguments up by name, and ask isDefault() before you assume the user chose a value.**

So far every label was written in Kotlin. MoveMate also has one box from a Java team."""

# ---------------------------------------------------------------- section 3
JAVA_TREE = """file MovingCrate.java  package=movemate
  class MovingCrate  kind=CLASS  modifiers=[PUBLIC]  origin=JAVA
    property label: (String..String?)
    function getLabel(): (String..String?)  origin=JAVA
    function <init>(label: (String..String?)): MovingCrate  origin=JAVA"""
J_VISIT = """// Closest Java equivalent: a javac element visitor (javax.lang.model.util, JDK 16+)
class TreePrinter extends SimpleElementVisitor14<Void, Void> {
    @Override
    public Void visitType(TypeElement type, Void unused) {
        line("class " + type.getSimpleName());
        type.getEnclosedElements().forEach(child -> child.accept(this, null));  // go to the children yourself
        return null;
    }

    @Override
    public Void visitVariable(VariableElement field, Void unused) {
        line("field " + field.getSimpleName() + ": " + field.asType());
        return null;
    }
}
// start the walk: element.accept(new TreePrinter(), null)"""
K_VISIT = """inner class TreePrinter : KSVisitorVoid(apiFeatures) {
    override fun visitClassDeclaration(classDeclaration: KSClassDeclaration, data: Unit) {
        line("class ${classDeclaration.simpleName.asString()}")
        classDeclaration.declarations.forEach { it.accept(this, Unit) }   // go to the children yourself
    }

    override fun visitPropertyDeclaration(property: KSPropertyDeclaration, data: Unit) {
        line("property ${property.simpleName.asString()}: ${property.type}")
    }
}
// start the walk: file.accept(TreePrinter(), Unit)"""

S3 = """KSP reads Java source files in the same module too, through the same API. Their symbols say `origin=JAVA`. Here is the rest of `TreeDemo`'s output, for a small Java class:

```text
""" + JAVA_TREE + """
```

Three things differ from a Kotlin class, and the label meets two of them. Java has no primary constructor, so `primaryConstructor` is null, and the label falls back to the first constructor that `getConstructors()` finds. Java fields come back as properties, even the private `label`. And a Java `String` is a platform type, `(String..String?)`: Kotlin can't tell whether it may be null, so the label prints `String!`. A Java `int`, which can never be null, comes back as a plain `Int`.

In the picture, this is a box labeled in another language. The same helper can read it, but a few words are fuzzy, and the helper says so with a `!` instead of guessing.

The real build needs no extra setup for it. The lesson 3 playground keeps `MovingCrate.java` next to the Kotlin classes, and `./gradlew :ksp:app:kspL03Kotlin` writes `MovingCrateLabel.kt` for it: a Kotlin file describing a Java class, which Java code then reads as `MovingCrateLabel.SHAPE`.

Now the visitor that `TreeDemo` used. A **visitor** is an object with one function per kind of node: `visitFile`, `visitClassDeclaration`, `visitFunctionDeclaration` and so on. Calling `node.accept(visitor, data)` makes KSP call the function that matches the node's kind, so the visitor never needs a chain of `is` checks. Both compilers offer the same pattern:

""" + pair(J_VISIT, K_VISIT) + """

`KSVisitorVoid` does nothing by default. Each of its functions has an empty body, so the visitor goes only where your code sends it, by calling `accept` on the children. javac's `SimpleElementVisitor14` behaves the same way; its sibling `ElementScanner14` is the one that visits every child for you.

Write it as `KSVisitorVoid(apiFeatures)`, passing the processor's `apiFeatures`. The official quickstart still writes `KSVisitorVoid()`, and that spelling has been deprecated since KSP 2.3.12. On 2.3.14 it compiles with the warning `'constructor(): KSVisitorVoid' is deprecated`. The same goes for `validate()` without arguments, which lesson 5 meets.

A visitor earns its keep when one walk must handle many kinds of node, as `TreeDemo` does. The lab's labels only ever look at a class and its constructor, so plain functions read better there.

**A visitor sends each node to the function for its kind. Use one when the walk is the job, and plain functions when you know where you're going.**

That's the whole label read: the tree, the types, the notes, and the boxes from Java."""

# ---------------------------------------------------------------- closing
CLOSING = """We started with a helper reading labels: some easy, some in shorthand, one in another language. The tree gave us every declaration and no expression, `resolve()` turned each written type into the type it means, the notes gave their values by name, and the Java crate got a `String!` where Kotlin couldn't know more.

In your own code, find a place that prints or compares types as strings, a log line or a generated file, and check what it does with a `?`, a type alias and a Java type.

Next, we'll stop writing generated code as strings. What happens to a string template when the type it prints lives in another package and needs an import?"""

L = {
 "id": "ksp-03",
 "title": "Reading declarations, types and annotations",
 "minutes": 40,
 "goal": "By the end you can walk a class's declarations in KSP (kind, modifiers, constructor parameters, properties and functions), turn a type reference into correct text with its type arguments and nullability, read annotation arguments of each kind together with their defaults, and handle a Java class in the same module.",
 "opening": OPENING,
 "warmup": {
  "q": "A processor reads the parameter `waterEveryDays` of `data class Plant(val kind: String, val waterEveryDays: Int = 7)`. What can it learn about the default value?",
  "options": ["That it's 7", "That there is a default (`hasDefault` is true), but not what it is", "Nothing: KSP can't tell a parameter with a default from one without", "The text `7`, as a string"],
  "answer": 1,
  "why": "KSP shows declarations, and a default value is an expression, so it only tells you that one exists. `TreeDemo` in the first section prints `waterEveryDays: Int (hasDefault)` and nothing more. The first and last options would need KSP to see inside the code, which it never does."
 },
 "sections": [
  {
   "h": "The label from top to bottom: a file, its classes and their members",
   "body": S0,
   "try": {
    "title": "Print a file's symbol tree",
    "minutes": 4,
    "steps": [
     "Run `TreeDemo` from `labs/`. It takes about 10 s. The walk is written as a visitor, which the last section explains; read the output first.",
     "Find the line for `areaCm2`. Which of its parts appear, and which part of its body appears at all?",
     "In the Kotlin source string, give `Mirror` a default, `val glass: String = \"plain\"`, and make `Plant` an ordinary class instead of a data class. Predict both changes in the output, then run it again."
    ],
    "code": kdemo("TreeDemo"),
    "expect": "The output in this section, then the Java file. `areaCm2(): Int` shows its name and return type, and `property area: Int` under it, because a local `val` is a declaration; the multiplication never appears. With the default, Mirror's constructor line shows `glass: String (hasDefault)`, without the value. Without `data`, Plant's `modifiers` becomes `[]`, and `component1` to `component3` and `copy` disappear, because only a data class gets them."
   }
  },
  {
   "h": "Printing a type correctly: references, resolved types, nullability and arguments",
   "body": S1,
   "figure": {"svg": FIG, "caption": "A class's label as KSP models it: declarations down to a type reference, which resolve() turns into the type it names."},
   "try": {
    "title": "Print a type three ways",
    "minutes": 4,
    "steps": [
     "Run `ShapeDemo`. It prints the table in this section, using the reference `typeText`; with `-Pmine=l03` it uses yours, or prints `(not done yet)`.",
     "Add a parameter `val spare: Crate?` to `Crate` in the source string. Predict all three columns for it, then run again.",
     "Once your lab passes, run it with `-Pmine=l03` and check that your column matches the reference one, row for row."
    ],
    "code": kdemo("ShapeDemo"),
    "expect": "The table in this section. `spare` prints `Crate?`, `Crate` and `Crate?`: a class can name itself, and only the name-only column loses the `?`. With your finished lab, the `typeText` column is identical, including `List<*>` and `String!`."
   },
   "refs": [{"title": "Kotlin model and type resolution (Kotlin docs)", "url": "https://kotlinlang.org/docs/ksp-kotlin-model.html", "kind": "docs"}]
  },
  {
   "h": "Reading the values on a sticky note: annotation arguments and their defaults",
   "body": S2,
   "try": {
    "title": "Read the notes' values",
    "minutes": 4,
    "steps": [
     "Run `LabelDemo` and read the two label files it prints.",
     "In the source string, change the bookshelf's note to `@Handling(stackable = false)`. Predict the `HANDLING` line, then run it.",
     "Now remove `@Room(\"study\")` from the bookshelf. Predict which lines its label keeps."
    ],
    "code": kdemo("LabelDemo"),
    "expect": "First the labels in this section, ending with `--- BookshelfLabel.HANDLING is: care=UPRIGHT, stackable=true (default), packWith=Lamp`. With `stackable = false` only, the line reads `care=NORMAL (default), stackable=false, packWith=Any (default)`: the two unwritten arguments come back with their defaults, marked. Without `@Room`, the label keeps `SHAPE` and `HANDLING` and loses `ROOM`."
   },
   "refs": [{"title": "Java annotation processing to KSP reference (Kotlin docs)", "url": "https://kotlinlang.org/docs/ksp-reference.html", "kind": "docs"}]
  },
  {
   "h": "A Java box, and a visitor that walks any box",
   "body": S3,
   "try": {
    "title": "Read a Java class in the real build",
    "minutes": 4,
    "steps": [
     "From `labs/`, run `./gradlew :ksp:app:kspL03Kotlin` and open `labs/ksp/app/build/generated/ksp/l03/kotlin/workbench/ksp/app/l03/MovingCrateLabel.kt`.",
     "Run `./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l03.MoveMateKt`, then the Java twin with `-Pmain=workbench.ksp.app.l03.MoveMateJava`.",
     "In `labs/ksp/app/src/l03/java/workbench/ksp/app/l03/MovingCrate.java`, change both `int weightGrams` to `Integer weightGrams` (the field and the constructor parameter) and `getWeightGrams()` to return `Integer`. Predict the new shape, run the KSP task again, then undo the change."
    ],
    "code": {"lang": "kotlin", "title": "MoveMate.kt", "src": read(f"{app}/kotlin/workbench/ksp/app/l03/MoveMate.kt"),
             "run": "./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l03.MoveMateKt",
             "file": f"{app}/kotlin/workbench/ksp/app/l03/MoveMate.kt",
             "alt": {"lang": "java", "title": "MoveMateJava.java", "src": read(f"{app}/java/workbench/ksp/app/l03/MoveMateJava.java"),
                     "run": "./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l03.MoveMateJava",
                     "file": f"{app}/java/workbench/ksp/app/l03/MoveMateJava.java"}},
    "expect": "The file holds `const val SHAPE: String = \"MovingCrate(label: String!, weightGrams: Int)\"`. Both demos print five labels, from `Lamp(name: String, bulbs: Int, shade: String?)` to `MovingCrate(label: String!, weightGrams: Int)`, and the Java twin reads them as plain static fields such as `LampLabel.SHAPE`. With `Integer`, the shape becomes `MovingCrate(label: String!, weightGrams: Int!)`: a boxed `Integer` may be null, so it's a platform type too."
   },
   "refs": [{"title": "SimpleElementVisitor14 (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.compiler/javax/lang/model/util/SimpleElementVisitor14.html", "kind": "docs"}]
  }
 ],
 "compare": {
  "title": "Reading a parameter's type and an annotation's values: javac and KSP",
  "java": {"title": "LabelProcessor.java", "src": "// Closest Java equivalent: javac's model (javax.lang.model)\nExecutableElement constructor = ElementFilter.constructorsIn(cls.getEnclosedElements()).get(0);\nfor (VariableElement parameter : constructor.getParameters()) {\n    TypeMirror type = parameter.asType();              // already resolved, no nullability at all\n    line(parameter.getSimpleName() + \": \" + typeText(type));\n}\n\nfor (AnnotationMirror note : cls.getAnnotationMirrors()) {\n    var all = processingEnv.getElementUtils().getElementValuesWithDefaults(note);\n    for (var entry : all.entrySet()) {\n        Object value = entry.getValue().getValue();    // enum: VariableElement, class: TypeMirror\n        line(entry.getKey().getSimpleName() + \"=\" + value);\n    }\n}"},
  "kotlin": {"title": "LabelProcessor.kt", "src": "val constructor = cls.primaryConstructor ?: cls.getConstructors().first()\nfor (parameter in constructor.parameters) {\n    val type = parameter.type.resolve()                // resolved on request, with its nullability\n    line(\"${parameter.name!!.asString()}: ${typeText(parameter.type)}\")\n}\n\nfor (note in cls.annotations) {\n    for (argument in note.arguments) {                 // defaults included, after the written ones\n        val value = argument.value                     // enum: KSClassDeclaration, class: KSType\n        line(\"${argument.name?.asString()}=$value\" + if (argument.isDefault()) \" (default)\" else \"\")\n    }\n}"},
  "note": "The two models match almost one to one: `TypeElement` to `KSClassDeclaration`, `ExecutableElement` to `KSFunctionDeclaration`, `VariableElement` to `KSValueParameter` or `KSPropertyDeclaration`, `AnnotationMirror` to `KSAnnotation`. Three differences are real. A javac `TypeMirror` arrives already resolved, while KSP hands you a reference and resolves it only when you call `resolve()`, because resolving is expensive. A `TypeMirror` has no nullability, because Java has none, while a `KSType` says `NULLABLE`, `NOT_NULL` or, for Java types, `PLATFORM`. And the value kinds differ: javac gives an enum constant as a `VariableElement`, KSP 2 gives the enum entry's `KSClassDeclaration`; both give a class as a type (`TypeMirror`, `KSType`). Kotlin's version also gets the primary constructor directly; Java has to pick one."
 },
 "worked": {
  "title": "Print `Map<String, List<Int?>>?` by hand, the way typeText does",
  "steps": [
   {"say": "Start at the outside. Resolve the reference once and read the three facts the label needs: the declaration's name, the type arguments, and the nullability.",
    "code": "// 1. the outer type\nval type = ref.resolve()\ntype.declaration.simpleName.asString()   // \"Map\"\ntype.arguments                           // [String, List<Int?>], both INVARIANT\ntype.nullability                         // NULLABLE", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "// 1. the outer type (javac: already resolved)\nDeclaredType type = (DeclaredType) parameter.asType();\ntype.asElement().getSimpleName();         // Map\ntype.getTypeArguments();                  // [java.lang.String, java.util.List<java.lang.Integer>]\n// no nullability: Java's types don't carry any"},
   {"say": "The first argument is simple: `String`, no arguments, `NOT_NULL`, so it prints `String`. The second is a `List` with one argument, `Int`, whose nullability is `NULLABLE`, so the inner call prints `Int?` and the list prints `List<Int?>`. Each argument goes through the same function, which is why it's recursive.",
    "code": "// 2. each argument, with the same function\ntypeText(stringRef)     // \"String\"\ntypeText(listRef)       // \"List\" + \"<\" + typeText(intRef) + \">\" = \"List<Int?>\"", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "// 2. each argument, with the same function\ntypeText(stringMirror)  // \"String\"\ntypeText(listMirror)    // \"List\" + \"<\" + typeText(integerMirror) + \">\" = \"List<Integer>\""},
   {"say": "Put the outer parts back together: the name, the arguments joined with `, ` inside `<` and `>`, and the mark for the outer nullability. The result is `Map<String, List<Int?>>?`, the type exactly as written. The Java twin prints `Map<String, List<Integer>>`, with no marks, because javac never had them to give.",
    "code": "// 3. assemble\n\"Map\" + \"<String, List<Int?>>\" + \"?\"   // \"Map<String, List<Int?>>?\"", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "// 3. assemble\n\"Map\" + \"<String, List<Integer>>\"   // \"Map<String, List<Integer>>\""},
   {"say": "Count the resolutions: four, one per reference, for `Map`, `String`, `List` and `Int`. Each is a lookup, and KSP records each one, because an incremental build, one that redoes only what changed, must know which files this label read (lesson 7). That's the reason for the rule: resolve each reference once, and only the ones you need.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "The @Label processor: read the typed shape and the notes",
  "minutes": 15,
  "files": [f"{lab}/main/{P}/LabelProcessor.kt", "labs/ksp/annotations/src/main/kotlin/workbench/ksp/annotations/l03/Handling.kt", f"{app}/kotlin/workbench/ksp/app/l03/MoveMate.kt", f"{app}/java/workbench/ksp/app/l03/MovingCrate.java"],
  "run": "./gradlew :ksp:test --tests 'workbench.ksp.l03.*'",
  "steps": [
   "Read `LabelProcessor.kt`. Moves 1 (Find), 2 (Check) and 4 (Write) are given, written the way you wrote them in lesson 2, and so are `labelSource` and `annotationNamed`. Your part is move 3, Read: the four functions at the end of the file.",
   "Run `./gradlew :ksp:app:kspL03Kotlin -Pmine=l03`. It prints `w: [ksp] l03 not done yet: 3. Read: the class name and each constructor parameter ...` and the build passes (add `--rerun` if the task says `UP-TO-DATE` and prints nothing).",
   "3. Read, the type: write `typeText`. Resolve the reference, then print the declaration's simple name, the type arguments in `<...>` by calling `typeText` again on each (a `*` for `Variance.STAR`, whose type is null), and the mark: `?` for `NULLABLE`, `!` for `PLATFORM`, nothing for `NOT_NULL`.",
   "3. Read, the shape: write `shapeOf`. Use `primaryConstructor`, or `getConstructors().firstOrNull()` for a Java class. Print each parameter as `name: type`, add ` = ...` when `hasDefault`, and start it with `@Fragile ` when `annotationNamed(parameter, \"workbench.ksp.annotations.Fragile\")` finds the note.",
   "3. Read, the notes: write `roomOf` (the `name` argument of `@Room`) and `handlingOf` (care, stackable and packWith, in that order, each followed by ` (default)` when `isDefault()` is true).",
   "5. Prove: run the tests until all five pass. Then run `./gradlew :ksp:app:kspL03Kotlin -Pmine=l03`, open `labs/ksp/app/build/generated/ksp/l03/kotlin/workbench/ksp/app/l03/MovingCrateLabel.kt`, and run `./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l03.MoveMateKt -Pmine=l03`.",
   "From memory: close the file and write `typeText` again on paper, all four cases. Then compare it with yours."
  ],
  "hints": [
   "`ref.resolve()` gives a `KSType`: `declaration.simpleName.asString()` is the name, `arguments` the type arguments, `nullability` the mark.",
   "A `KSTypeArgument` has a `variance` and a `type`, which is a `KSTypeReference?`. Call `typeText(arg.type!!)` for every variance except `Variance.STAR`, and put `out ` or `in ` in front for `COVARIANT` and `CONTRAVARIANT`.",
   "An enum argument's `value` is a `KSClassDeclaration`, so `(value as KSClassDeclaration).simpleName.asString()` gives `UPRIGHT`. A class argument's `value` is a `KSType`; read its `declaration.simpleName`.",
   "`isDefault()` is an extension function: `import com.google.devtools.ksp.isDefault`. `getConstructors()` is one too: `import com.google.devtools.ksp.getConstructors`.",
   "Look arguments up by name, `annotation.arguments.first { it.name?.asString() == \"care\" }`, because the written ones come before the defaults."
  ],
  "done_when": "All five tests in `LabelProcessorTest` pass."
 },
 "drill": {
  "title": "Print a type from memory",
  "minutes": 5,
  "prompt": "Close this page. Write `typeText(ref: KSTypeReference): String` from memory: the name, the type arguments (recursively, with `*` for a star), and `?`, `!` or nothing for the nullability. Then write the javac version for a `TypeMirror`, and say in one sentence why it has no `?`. Compare with the answer.",
  "answer": {"lang": "kotlin", "src": "fun typeText(ref: KSTypeReference): String {\n    val type = ref.resolve()\n    val arguments = if (type.arguments.isEmpty()) \"\" else type.arguments.joinToString(\", \", \"<\", \">\") { arg ->\n        when (arg.variance) {\n            Variance.STAR -> \"*\"\n            Variance.COVARIANT -> \"out \" + typeText(arg.type!!)\n            Variance.CONTRAVARIANT -> \"in \" + typeText(arg.type!!)\n            Variance.INVARIANT -> typeText(arg.type!!)\n        }\n    }\n    val mark = when (type.nullability) {\n        Nullability.NULLABLE -> \"?\"\n        Nullability.PLATFORM -> \"!\"\n        Nullability.NOT_NULL -> \"\"\n    }\n    return type.declaration.simpleName.asString() + arguments + mark\n}",
             "alt": {"lang": "java", "title": "Labels.java", "src": "// no ?: Java's type system has no nullability, so a TypeMirror can't carry it\nstatic String typeText(TypeMirror type) {\n    if (type instanceof DeclaredType declared) {\n        String name = declared.asElement().getSimpleName().toString();\n        List<? extends TypeMirror> arguments = declared.getTypeArguments();\n        if (arguments.isEmpty()) return name;\n        return name + arguments.stream().map(Labels::typeText).collect(Collectors.joining(\", \", \"<\", \">\"));\n    }\n    if (type instanceof WildcardType) return \"?\";   // Java's star\n    return type.toString();                           // primitives\n}"}}
 },
 "recap": [
  "KSP shows a tree of declarations: `KSFile`, `KSClassDeclaration` (with `classKind`, the modifiers written in the source, and `primaryConstructor`), `KSPropertyDeclaration`, `KSFunctionDeclaration` and `KSValueParameter`. A data class's `copy` and `componentN` appear as `SYNTHETIC`.",
  "A `KSTypeReference` is the type as written; `resolve()` gives the `KSType` it means, with its declaration, arguments and nullability. Resolving is expensive, so resolve each reference once.",
  "Build a type's text yourself: the name, each argument the same way (a star has no type), then `?`, nothing, or `!` for a Java platform type. `toString()` prints `[typealias Litres]` and `(String..String?)`.",
  "Annotation arguments arrive as themselves (String, Boolean), as a `KSType` (a class) or as the entry's `KSClassDeclaration` (an enum value). Defaults are in the list with `isDefault()` true, after the written ones, so look them up by name.",
  "Java sources in the module are read too (`origin=JAVA`): no primary constructor, private fields as properties, and platform types.",
  "The limit: KSP never shows an expression. `hasDefault` says a default exists, never its value, and a function's body is closed to it."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "`fun areaCm2(): Int { val area = widthCm * heightCm; return area }`. What does a processor see under `areaCm2` when it walks its declarations?",
   "options": ["Nothing: a function's insides are invisible", "A property `area: Int`, but not `widthCm * heightCm`", "`val area = widthCm * heightCm` as an expression tree", "The `return area` statement"],
   "answer": 1, "why": "A local `val` is a named declaration, so it shows up in the function's `declarations`, with its type. Its initializer is an expression, and KSP shows no expressions or statements, so the multiplication and the `return` stay out of reach."},
  {"q": "A parameter is declared `val water: Litres`, with `typealias Litres = Double`. What does `parameter.type.toString()` print in KSP 2.3.14?",
   "options": ["`Double`", "`Litres`", "`kotlin.Double`", "`[typealias Litres]`"],
   "answer": 3, "why": "`toString()` is a display form, and for a type alias it prints `[typealias Litres]`. Resolving and reading `declaration.simpleName` gives `Litres`, the name as written, which is what a label wants; following the alias to `Double` is a separate step. Never generate code from `toString()`."},
  {"q": "`@Handling(stackable = false)` sits on a class. What does `annotation.arguments` hold?",
   "options": ["Only `stackable`, because the others weren't written", "`stackable` first, then `care` and `packWith` with their defaults and `isDefault()` true", "`care`, `stackable`, `packWith` in declaration order, all with `isDefault()` false", "`care` and `packWith` only, because `false` is a default"],
   "answer": 1, "why": "KSP fills in every parameter, so defaults are in the list, marked with `origin=SYNTHETIC`, which `isDefault()` checks. The written arguments come first, then the defaults, which is why the lab looks arguments up by name. `stackable = false` was written, so it isn't a default, even though it differs from the declared default only in value."},
  {"q": "A Java constructor parameter is declared `String label`. What is the nullability of its resolved `KSType`?",
   "options": ["`NOT_NULL`, because it has no `?`", "`NULLABLE`, because Java objects can be null", "`PLATFORM`: Kotlin can't know, and writes it `String!`", "KSP can't read Java parameters"],
   "answer": 2, "why": "A type from Java carries no nullability, so KSP reports `PLATFORM`, and its `toString()` shows `(String..String?)`, a range from not-null to nullable. Kotlin writes such a type `String!`. A Java `int` is different: it can never be null, so it arrives as a plain `Int`."},
  {"q": "From lesson 2 of this track: `@Label` is on line 8 and `class Mirror(...)` on line 9, and the processor calls `logger.error(message, symbol)` for `Mirror`. Which line does the message name?",
   "options": ["Line 9", "Line 8", "Line 1", "Both lines 8 and 9"],
   "answer": 0, "why": "KSP reports a symbol's own location, and a class declaration's location is its `class` line, not the line of its annotation. That's why the error tests look for the declaration's line, such as `Truck.kt:6` in this lesson's lab and `Shape.kt:6` in lesson 2's.",
   "from": "ksp-02"}
 ],
 "flashcards": [
  {"front": "`KSTypeReference` vs `KSType`?", "back": "A reference is the type as written in the source. `resolve()` turns it into a `KSType`, the type it means, with its declaration, arguments and nullability."},
  {"front": "Why doesn't KSP resolve types for you?", "back": "Resolving is one of the most expensive operations in its API, and KSP records each one for incremental builds, so it waits until you call `resolve()`."},
  {"front": "What does KSP tell you about the default in `val waterEveryDays: Int = 7`?", "back": "`hasDefault == true`, and never the value 7: a default value is an expression, and KSP shows no expressions."},
  {"front": "In KSP 2, what is an enum annotation argument's value? And a class argument's?", "back": "An enum value is the entry's `KSClassDeclaration` (`classKind == ENUM_ENTRY`). A `KClass` argument is a `KSType`."},
  {"front": "How do you tell a default annotation argument from a written one?", "back": "`argument.isDefault()`, true for `origin == SYNTHETIC`. Defaults come after the written arguments in the list, so look arguments up by name."},
  {"front": "What does a Java `String` parameter look like to KSP?", "back": "A platform type: nullability `PLATFORM`, `toString()` `(String..String?)`, written `String!` in Kotlin. A Java `int` is a plain `Int`."},
  {"front": "Does `KSVisitorVoid` visit a node's children by itself?", "back": "No: every visit function is empty, so you call `accept` on the children yourself. Build it as `KSVisitorVoid(apiFeatures)`; `KSVisitorVoid()` is deprecated since 2.3.12."}
 ],
 "terms": [
  {"term": "Symbol", "plain": "A node in KSP's model of the code, one for each named thing: a file, a class, a function, a parameter."},
  {"term": "Declaration", "plain": "A symbol you wrote yourself, such as a class (`KSClassDeclaration`) or a function (`KSFunctionDeclaration`)."},
  {"term": "KSTypeReference", "plain": "A type as written in the source, before it is looked up."},
  {"term": "KSType", "plain": "A resolved type: the class it names, its type arguments and its nullability."},
  {"term": "Platform type", "plain": "A type from Java, whose nullability Kotlin can't know; written `String!`."},
  {"term": "Annotation argument", "plain": "A value written on an annotation, such as the `\"study\"` in `@Room(\"study\")`, or its default when not written."},
  {"term": "Type alias", "plain": "A second name for an existing type, such as `typealias Litres = Double`."},
  {"term": "Visitor", "plain": "An object with one function per kind of node; `node.accept(visitor, data)` calls the matching one."}
 ],
 "explain_back": {
  "prompt": "A teammate's processor builds its labels with `parameter.type.toString()`, and the tests pass. Explain why that's still a bug waiting to happen, and what `typeText` does instead.",
  "answer": "`toString()` on a type reference is KSP's display form for people reading logs. It happens to look like Kotlin for simple types, so tests with `String` and `List<String>` pass, but it isn't a promise. On a type alias it prints `[typealias Litres]`, and on a Java type it prints `(String..String?)`, neither of which is how anyone writes the type. `typeText` resolves the reference once to get the `KSType` it means, then builds the text from its parts: the declaration's simple name, the type arguments printed by the same function (with `*` for a star, which has no type), and the nullability mark, `?` for nullable, `!` for a Java platform type, nothing for not-null. That way the output depends only on facts the API guarantees, and each reference is resolved just once, which matters because resolving is expensive."
 },
 "deeper": {
  "minutes": 10,
  "body": "A few more facts about the label, for the day you need them.\n\n`getDeclaredProperties()` lists only the class's own properties, while `getAllProperties()` includes inherited ones too, and needs type resolution to find them, so it costs more. The same split exists for functions. Both `getDeclared...` helpers are extension functions in `com.google.devtools.ksp` that filter `declarations`.\n\nYou can often avoid resolving at all. A reference's `element` is the type as written, and for a class name, `(ref.element as? KSClassifierReference)?.referencedName()` gives the written name without a lookup. KSP's docs suggest filtering that way first, and resolving only the references you still care about, because every resolution is both slow and recorded as a dependency for incremental builds.\n\nNested classes need care. `simpleName` of `Kitchen.Drawer` is just `Drawer`, and splitting `qualifiedName` at dots can't tell a package from an outer class. For a label, drop the package from the qualified name; for generated code, lesson 4's KotlinPoet does it properly.\n\nComparing types has a trap for Java hands. KSP's `a.isAssignableFrom(b)` asks whether a `b` can be stored in an `a`, so `Any.isAssignableFrom(String)` is true. javac's `Types.isAssignable(t1, t2)` asks whether a `t1` can be stored in a `t2`, so the arguments come in the opposite order. And `==` on `KSType` includes nullability: `String?` is not equal to `String`.\n\nFinally, `getAnnotationsByType(Room::class)` looks convenient, because it hands you a real annotation instance. But it's marked experimental, and reading a class argument through it throws `KSTypeNotPresentException`, because the class it names may not be compiled yet. Read `KSAnnotation.arguments`, as this lesson does."
 },
 "sources": [
  {"title": "Kotlin model and type resolution (Kotlin docs)", "url": "https://kotlinlang.org/docs/ksp-kotlin-model.html"},
  {"title": "Java annotation processing to KSP reference (Kotlin docs)", "url": "https://kotlinlang.org/docs/ksp-reference.html"},
  {"title": "TypeMirror (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.compiler/javax/lang/model/type/TypeMirror.html"},
  {"title": "Elements.getElementValuesWithDefaults (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.compiler/javax/lang/model/util/Elements.html"}
 ]
}
out = ROOT / "content/lessons/ksp-03.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
