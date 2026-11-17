import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/bytecode/src"
P = "java/workbench/bytecode/l03"
K = "kotlin/workbench/bytecode/l03"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :bytecode:demo -Pmain=workbench.bytecode.l03."


def demo(java, kt):
    return {"lang": "java", "title": f"{java}.java", "src": read(f"{lab}/demo/{P}/{java}.java"),
            "run": RUN + java, "file": f"{lab}/demo/{P}/{java}.java",
            "alt": {"lang": "kotlin", "title": f"{kt}.kt", "src": read(f"{lab}/demo/{K}/{kt}.kt"),
                    "run": RUN + kt + "Kt", "file": f"{lab}/demo/{K}/{kt}.kt"}}


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


FIG = """<svg viewBox="0 0 680 280" role="img" aria-label="The first time an invokedynamic instruction runs, the JVM calls its bootstrap method with the static arguments. LambdaMetafactory makes a hidden class and returns a ConstantCallSite. Every later run calls the call site's target directly.">
<rect class="box-a" x="20" y="30" width="230" height="56" rx="8"/>
<text class="t-s t-code" x="135" y="54" text-anchor="middle">invokedynamic #15</text>
<text class="t-s t-code" x="135" y="74" text-anchor="middle">applyAsInt:()IntBinaryOperator</text>
<rect class="box" x="300" y="20" width="360" height="76" rx="8"/>
<text class="t-s" x="480" y="42" text-anchor="middle">bootstrap method: ask the director (once)</text>
<text class="t-s t-code" x="480" y="62" text-anchor="middle">LambdaMetafactory.metafactory</text>
<text class="t-s t-m" x="480" y="82" text-anchor="middle">static args: (II)I, IndyTour.add, (II)I</text>
<line class="ln-a" x1="250" y1="50" x2="296" y2="50" marker-end="url(#arr)"/>
<text class="t-s t-a" x="273" y="40" text-anchor="middle">1st</text>
<rect class="box-b" x="300" y="120" width="360" height="44" rx="8"/>
<text class="t-s" x="480" y="147" text-anchor="middle">defines hidden class IndyTour$$Lambda</text>
<line class="ln" x1="480" y1="96" x2="480" y2="116" marker-end="url(#arr)"/>
<rect class="box-ok" x="300" y="190" width="360" height="44" rx="8"/>
<text class="t-s" x="480" y="217" text-anchor="middle">returns ConstantCallSite(target)</text>
<line class="ln" x1="480" y1="164" x2="480" y2="186" marker-end="url(#arr)"/>
<rect class="box-ok" x="20" y="190" width="230" height="44" rx="8"/>
<text class="t-s" x="135" y="217" text-anchor="middle">answer written in the margin</text>
<line class="ln" x1="300" y1="212" x2="254" y2="212" marker-end="url(#arr)"/>
<line class="ln-d" x1="135" y1="86" x2="135" y2="186" marker-end="url(#arr)"/>
<text class="t-s t-m" x="190" y="140" text-anchor="middle">every later run:</text>
<text class="t-s t-m" x="190" y="158" text-anchor="middle">call the target</text>
<text class="t-s t-m" x="340" y="264" text-anchor="middle">the target returns the lambda object: the same one if nothing is captured</text>
</svg>"""

OPENING = """Most cues in a prompt book are complete: "LX 14 GO". A few say only "ask the director". On the first night, the stage manager reaches that cue and asks. The director decides, and the answer is written into the margin. From then on, the stage manager reads the margin and never asks again, which suits the director fine.

The JVM has a cue like that, and it's the one javap couldn't finish for us in the last lesson: `invokedynamic`. It's behind every lambda you write, and behind every string you build with `+`. The first time such an instruction runs, library code decides what it calls, and the answer is kept for good.

It's easy to guess wrong about what that costs. Many people picture a lambda as a small inner class, or believe each lambda allocates on every call, so they avoid lambdas where they're cheap and miss the allocation where it's real. In this lesson, we'll watch a call site get linked once, take a lambda apart, see string `+` and records use the same trick, and then do the linking by hand. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
S0 = """Every other call instruction names its target. `invokestatic StackDemo.seconds:(JI)J` calls exactly that method, like a cue that says "LX 14 GO". `invokedynamic` names only a method name, a type, and a **bootstrap method**: a method that will decide the target the first time the instruction runs. Here is the method reference `IndyTour::add` in `javap -c -p`, and its entry from `javap -v`, on JDK 25:

```text
invokedynamic #15,  0   // InvokeDynamic #2:applyAsInt:()Ljava/util/function/IntBinaryOperator;

BootstrapMethods:
  2: REF_invokeStatic java/lang/invoke/LambdaMetafactory.metafactory:(...)Ljava/lang/invoke/CallSite;
    Method arguments:
      (II)I
      REF_invokeStatic workbench/bytecode/l03/IndyTour.add:(II)I
      (II)I
```

Read the type `()IntBinaryOperator` from the point of view of the code around it: take nothing off the operand stack, and put an `IntBinaryOperator` on it. How the instruction gets one isn't written anywhere in your class file.

That's the cue that says "ask the director", and the bootstrap method is the director. The first time the instruction runs, the JVM calls the bootstrap method with four things: a `Lookup` for your class (an object that carries your class's access rights), the name, the type, and the static arguments listed above.

The bootstrap method returns a `CallSite`, an object that holds a target of exactly that type. The target is a **method handle**, a typed reference to a method that the JVM can call directly, much like a function pointer. The JVM links the instruction to the call site. From then on, every run calls the target directly, and the bootstrap method never runs again for that instruction. The answer is in the margin, and the director gets the rest of the run off.

`LambdaMetafactory` and `StringConcatFactory` both return a `ConstantCallSite`, whose target can never change. Here the picture needs one correction. A real margin note is in pencil, and a director can change their mind. A `ConstantCallSite` is written in ink, and that's what lets the JIT compile straight through it, as if the instruction had named its target all along. For languages that do need to relink later, the JDK has `MutableCallSite`, and the Try it below relinks one by hand.

`invokedynamic` arrived in Java 7, for other languages that run on the JVM, and javac first used it for lambdas in Java 8. It moves a decision out of your class files and into the JDK. The bytecode says "join an `int` and a `String` with this recipe". The JDK you run on decides how, so a newer JDK can do it better, and your old class files pick that up without being recompiled.

**An invokedynamic is linked once, at first use. After that, it's a direct call.**

So the director is library code in the JDK. Let's see what it builds when the cue is a lambda."""

# ---------------------------------------------------------------- section 1
J_DELAY = """static IntUnaryOperator delay(int extra) {
    return s -> s + extra;               // a lambda that captures extra
}"""
K_DELAY = """fun delay(extra: Int): (Int) -> Int =
    { s -> s + extra }                   // a lambda that captures extra"""

S1 = """The theatre's lighting cues run on seconds, and sometimes a whole sequence has to run a little late. `delay(5)` returns a function that adds 5 seconds to any cue time. javac turns that lambda into two things: a private method that holds the body, and an `invokedynamic` that produces the object:

""" + pair(J_DELAY, K_DELAY) + """

Here is what javap showed for each compiler on JDK 25, trimmed to the lines that matter:

```text
javac, IndyTour.class:
   1: invokedynamic #11,  0   // InvokeDynamic #1:applyAsInt:(I)Ljava/util/function/IntUnaryOperator;
  private static int lambda$delay$1(int, int);            // (extra, s): captured value first
  BootstrapMethods 1: LambdaMetafactory.metafactory
      (I)I
      REF_invokeStatic workbench/bytecode/l03/IndyTour.lambda$delay$1:(II)I
      (I)I

kotlinc, IndyTourKt.class:
   1: invokedynamic #44,  0   // InvokeDynamic #1:invoke:(I)Lkotlin/jvm/functions/Function1;
  private static final int delay$lambda$0(int, int);
  BootstrapMethods 1: LambdaMetafactory.metafactory
      (Ljava/lang/Object;)Ljava/lang/Object;
      REF_invokeStatic workbench/bytecode/l03/IndyTourKt.delay$lambda$0:(II)I
      (Ljava/lang/Integer;)Ljava/lang/Integer;
```

Read the call-site type as a factory: `(I)IntUnaryOperator` means "give me the captured `int`, and I'll give you an operator". To **capture** is to store a value from the surrounding code inside the lambda, here `extra`. The body method takes the captured values first, then the lambda's own parameter.

The three static arguments are the interface method's type after erasure, the body, and the interface method's type as this lambda uses it. Kotlin's `Function1.invoke` is erased to `(Object)Object`, so the third argument, `(Integer)Integer`, tells the factory to insert the boxing and the casts.

At link time, `LambdaMetafactory` generates a class. On JDK 25 the demo printed its name as `IndyTour$$Lambda/0x00000000a3080210`. It's a **hidden class**, one defined with `Lookup.defineHiddenClass` (JDK 15) that no class loader can find by name, so `Class.forName` on that name throws `ClassNotFoundException`. It's also a nestmate of `IndyTour`, a class allowed to use `IndyTour`'s private members, which is how it may call the private body. Since JDK 24, the JDK writes these classes with the ClassFile API that lesson 6 covers.

`IndyTour` shows the allocation rule in two lines of output:

```text
captures nothing: same object both times? true
captures extra: same object? false, same class? true
```

A lambda that captures nothing is linked to one shared instance, so `greeter() == greeter()` is `true`, from the very first call. Two calls, one object. A capturing lambda gets a new object each time the lambda expression is evaluated, and all of those objects share one class. That's one small allocation each time `delay(...)` runs, not one per call of the operator it returns.

Kotlin compiles lambdas the same way, and has done so by default since Kotlin 2.0. The release notes list what you give up: such a lambda isn't serializable, and its `toString()` is less readable. Function references are different. In the Kotlin demo, `::addSeconds` stored as `(Int, Int) -> Int` compiled to an ordinary generated class, `IndyTourKt$main$ref$1`, and `isHidden` printed `false`.

**A lambda allocates once per evaluation if it captures, and never if it doesn't.**

A lambda is one kind of question for the director. String `+` asks another."""

# ---------------------------------------------------------------- section 2
J_CONCAT = """"concat: " + cue.seconds() + " s to " + cue.name() + ", record: " + cue"""
K_CONCAT = """"template: ${cue.seconds} s to ${cue.name}, data class: $cue\""""

S2 = """Since JDK 9 (JEP 280), javac compiles `+` on strings to one `invokedynamic` per expression, linked by `StringConcatFactory.makeConcatWithConstants`. Before that, javac wrote a chain of `StringBuilder` calls into every class file, and that choice stayed frozen there. The constant parts now travel as a recipe, a fill-in-the-blanks line in which `\\u0001` marks each value to be filled in. Here's the last line of `IndyTour` in both languages:

""" + pair(J_CONCAT, K_CONCAT) + """

```text
javac, IndyTour.class:
 195: invokestatic  #97    // Method java/lang/String.valueOf:(Ljava/lang/Object;)Ljava/lang/String;
 198: invokedynamic #103,  0   // InvokeDynamic #7:makeConcatWithConstants:(ILjava/lang/String;Ljava/lang/String;)Ljava/lang/String;
      BootstrapMethods 7, recipe: concat: \\u0001 s to \\u0001, record: \\u0001

kotlinc, IndyTourKt.class:
 188: invokedynamic #147,  0   // InvokeDynamic #7:makeConcatWithConstants:(ILjava/lang/String;Lworkbench/bytecode/l03/KCue;)Ljava/lang/String;
      BootstrapMethods 7, recipe: template: \\u0001 s to \\u0001, data class: \\u0001
```

The call-site type lists the values in order: an `int`, the cue's name and the cue. javac first turned the record into a `String` with `String.valueOf`, and kotlinc passed the data class object as it is. Kotlin templates compile this way when the JVM target is 9 or newer, which the labs use. With kotlinc's command-line default of Java 8, the same template becomes a `StringBuilder` chain, as lesson 2 found.

Records push the idea further. A record's `toString`, `hashCode` and `equals` are each a couple of instructions around an `invokedynamic`. The bootstrap is `java.lang.runtime.ObjectMethods.bootstrap` (JDK 16), and its static arguments describe the record:

```text
ObjectMethods.bootstrap
  Method arguments:
    workbench/bytecode/l03/IndyTour$Cue
    name;seconds
    REF_getField workbench/bytecode/l03/IndyTour$Cue.name:Ljava/lang/String;
    REF_getField workbench/bytecode/l03/IndyTour$Cue.seconds:I
```

The JDK builds the three methods from that description the first time each is called. A Kotlin `data class` takes the other road: kotlinc writes the `toString` body itself, as `getfield name`, `getfield seconds` and a concatenation `invokedynamic` with the recipe `KCue(name=\\u0001, seconds=\\u0001)`. Both print the same kind of text. The record carries a description, and the data class carries finished code.

Pattern-matching `switch` over a sealed type compiles to `invokedynamic typeSwitch`, linked by `java.lang.runtime.SwitchBootstraps`. javac 21 and later also use a related form, **condy** (`CONSTANT_Dynamic`), for enum case labels in such a switch. A condy entry is a constant whose value a bootstrap method works out on first use. Same idea, for a value instead of a call.

**String `+`, records and pattern switches all ask a bootstrap method. javap shows the recipe.**

Every bootstrap method so far was called by the JVM. Nothing stops your code from calling one."""

# ---------------------------------------------------------------- section 3
J_META = """CallSite site = LambdaMetafactory.metafactory(
        lookup,                                 // 1. caller: must be able to see the body
        "get",                                  // 2. interface method name
        methodType(Supplier.class),             // 3. factory type: captured values -> interface
        methodType(Object.class),               // 4. interface method type, erased
        lookup.findStatic(ByHandDemo.class, "banner", methodType(String.class)),  // 5. body
        methodType(String.class));              // 6. interface method type as this lambda uses it
Supplier<String> s = (Supplier<String>) site.getTarget().invoke();"""
K_META = """val site = LambdaMetafactory.metafactory(
    lookup,                                     // 1. caller: must be able to see the body
    "get",                                      // 2. interface method name
    methodType(Supplier::class.java),           // 3. factory type: captured values -> interface
    methodType(Any::class.java),                // 4. interface method type, erased
    lookup.findStatic(Banners::class.java, "banner", methodType(String::class.java)),  // 5. body
    methodType(String::class.java),             // 6. interface method type as this lambda uses it
)
val s = site.target.invoke() as Supplier<String>"""

S3 = """A bootstrap method is an ordinary public static method, so your code can play the JVM and ask the director itself. That's today's lab. `LambdaMetafactory.metafactory` takes six arguments, and `javap -v` has already shown you all of them. Here it turns a static method `banner()`, which returns `"curtain up in five minutes"`, into a `Supplier<String>`:

""" + pair(J_META, K_META) + """

The JVM supplies arguments 1 to 3 from the call site, and the static arguments are 4 to 6. `getTarget()` is the factory. Calling it does what the `invokedynamic` instruction would do on every run: it takes the captured values and returns a lambda object. For a lambda that captures nothing, call the factory once and keep the result. For one that captures, keep the factory and call it once per object, which is the shape the lab tests for.

The generated class is a nestmate of the lookup's class, so the demo printed `ByHandDemo$$Lambda/0x...`, exactly like a lambda javac compiled. The Kotlin twin printed `ByHandDemoKt$$Lambda/0x...`.

`StringConcatFactory.makeConcatWithConstants(lookup, name, type, recipe)` works the same way. The demo asks it for a `(int, long)String` handle with the recipe `row \\u0001 has \\u0001 seats`, calls it with 12 and 30, and gets `row 12 has 30 seats`. Both call sites came back as `ConstantCallSite`.

Why would you do this outside a lab? You rarely need to. Code that has a `Method` in hand at run time, such as a serializer or a router (code that picks which method to call by name, while the program runs), can turn it into an interface object once, and then call it as fast as a lambda. That beats paying for `Method.invoke`, the reflective call, every time.

Every call site in this lesson linked to a method that already existed. The next lesson's tool goes one step further: the JDK writes a whole new class, implementing any interface you name, while your program runs."""

L = {
 "id": "cls-03",
 "title": "invokedynamic: how lambdas and string concatenation compile",
 "minutes": 35,
 "goal": "By the end you can read an invokedynamic call site and its bootstrap method in javap, say what a lambda captures and when it allocates, and build a lambda and a concatenation by hand with LambdaMetafactory and StringConcatFactory.",
 "opening": OPENING,
 "warmup": {
  "q": "`static Supplier<String> greeter() { return () -> \"hello\"; }`. What does `greeter() == greeter()` print on a current JDK?",
  "options": [
   "`false`: every lambda expression creates a new object",
   "`true`: the lambda captures nothing, so its call site hands back one shared object",
   "It doesn't compile: you can't compare lambdas with `==`",
   "`true`, but only after the JIT has compiled `greeter`"
  ],
  "answer": 1,
  "why": "The lambda is an `invokedynamic` call site. The first time it runs, `LambdaMetafactory` links it, and for a lambda that captures nothing, the linked target returns the same instance every time. It prints `true` from the first call, before the JIT is involved. A capturing lambda such as `s -> s + extra` gets a new object each time the expression is evaluated. The section on taking a lambda apart shows both in one demo."
 },
 "sections": [
  {
   "h": "invokedynamic: a call whose target is decided once, at first use",
   "body": S0,
   "try": {
    "title": "Relink a call site by hand",
    "minutes": 3,
    "steps": [
     "Read `CallSiteDemo`. It builds a `MutableCallSite` aimed at `inSeconds`, calls through its `dynamicInvoker()`, changes the target to `inMinutes`, and calls again with the same 120.",
     "Predict the three lines it prints, then run it (or the Kotlin twin)."
    ],
    "code": demo("CallSiteDemo", "CallSiteDemo"),
    "expect": "`linked to inSeconds: 120 seconds`, then `relinked to inMinutes: 2 minutes` through the very same invoker, then a line saying `ConstantCallSite.setTarget` threw `UnsupportedOperationException`. An `invokedynamic` instruction calls through its call site the way the invoker does. Lambdas get the constant kind: written in ink, linked for good."
   },
   "refs": [
    {"title": "java.lang.invoke package (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/invoke/package-summary.html", "kind": "docs"}
   ]
  },
  {
   "h": "Taking a lambda apart: a body method, plus a hidden class built at first use",
   "body": S1,
   "figure": {"svg": FIG, "caption": "The director is asked once per call site. After linking, the instruction calls the target directly."},
   "try": {
    "title": "Tour the lambdas",
    "minutes": 5,
    "steps": [
     "Run `IndyTour`, then `IndyTourKt`. Compare the class names they print.",
     "From `labs/`, run `javap -c -p bytecode/build/classes/java/demo/workbench/bytecode/l03/IndyTour.class | grep -E 'invokedynamic|lambda'` and match each `invokedynamic` to a line of source.",
     "Do the same for `bytecode/build/classes/kotlin/demo/workbench/bytecode/l03/IndyTourKt.class`, and run `ls` on that folder. Which Kotlin construct got a class file of its own?"
    ],
    "code": demo("IndyTour", "IndyTour"),
    "expect": "Java: `IndyTour$$Lambda/0x...`, `hidden: true`, a nestmate of `IndyTour`, `Class.forName` fails, `same object both times? true` for `greeter`, and `same object? false, same class? true` for `delay`. Kotlin: the lambdas print `IndyTourKt$$Lambda/0x...` and `hidden: true`, but the function reference prints `IndyTourKt$main$ref$1` and `hidden: false`. That's the `IndyTourKt$main$ref$1.class` file in the folder. Both programs also contain several `makeConcatWithConstants` call sites, one for each string they build."
   },
   "refs": [
    {"title": "LambdaMetafactory (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/invoke/LambdaMetafactory.html", "kind": "docs"},
    {"title": "What's new in Kotlin 2.0.0: lambdas via invokedynamic", "url": "https://kotlinlang.org/docs/whatsnew20.html", "kind": "read"}
   ]
  },
  {
   "h": "String concatenation, records and switches ask a bootstrap method too",
   "body": S2,
   "try": {
    "title": "A record and a data class, side by side",
    "minutes": 4,
    "steps": [
     "From `labs/` (after running `IndyTour` and `IndyTourKt` once), run the two `javap` commands below.",
     "In the record, find which bootstrap method its `toString` uses and the string that lists its components.",
     "In the data class, find the recipe that `toString` passes to `makeConcatWithConstants`."
    ],
    "code": {"lang": "bash", "title": "terminal", "src": "javap -v 'bytecode/build/classes/java/demo/workbench/bytecode/l03/IndyTour$Cue.class' | grep -A6 BootstrapMethods\njavap -v bytecode/build/classes/kotlin/demo/workbench/bytecode/l03/KCue.class | grep -A3 BootstrapMethods", "run": ""},
    "expect": "The record's `toString`, `hashCode` and `equals` all use bootstrap 0, `ObjectMethods.bootstrap`, with the arguments `IndyTour$Cue`, `name;seconds` and two `REF_getField` handles. The data class has only a `StringConcatFactory.makeConcatWithConstants` bootstrap, with the recipe `KCue(name=\\u0001, seconds=\\u0001)`. Its `hashCode` and `equals` are plain bytecode that kotlinc wrote."
   },
   "refs": [
    {"title": "JEP 280: Indify String Concatenation", "url": "https://openjdk.org/jeps/280", "kind": "read"}
   ]
  },
  {
   "h": "Calling the bootstrap methods yourself",
   "body": S3,
   "try": {
    "title": "One lambda and one concatenation, by hand",
    "minutes": 3,
    "steps": [
     "Read `ByHandDemo`. Match each of the six `metafactory` arguments to the `javap -v` listing in the first section.",
     "Run it (or the Kotlin twin) and read the class and call-site names it prints."
    ],
    "code": demo("ByHandDemo", "ByHandDemo"),
    "expect": "`curtain up in five minutes  <- ...ByHandDemo$$Lambda/0x..., call site: ConstantCallSite`, then `row 12 has 30 seats  <- call site: ConstantCallSite`. The lambda class is hidden and named after the lookup's class, exactly like a javac lambda. The Kotlin twin prints `ByHandDemoKt$$Lambda`."
   }
  }
 ],
 "compare": {
  "title": "Lambdas and function references in Java and Kotlin",
  "java": {"title": "Cues.java", "src": "static int add(int a, int b) { return a + b; }\n\nIntBinaryOperator ref = Cues::add;            // invokedynamic -> hidden Cues$$Lambda\nIntUnaryOperator plus5 = s -> s + 5;          // invokedynamic, body in lambda$main$0\nint extra = 10;\nIntUnaryOperator later = s -> s + extra;      // invokedynamic with type (I)IntUnaryOperator\n\nString line = \"delay \" + extra + \" s\";       // invokedynamic makeConcatWithConstants"},
  "kotlin": {"title": "Cues.kt", "src": "fun add(a: Int, b: Int) = a + b\n\nval ref: (Int, Int) -> Int = ::add            // a generated class (CuesKt$main$ref$1 style)\nval plus5: (Int) -> Int = { s -> s + 5 }      // invokedynamic -> hidden CuesKt$$Lambda\nval extra = 10\nval later: (Int) -> Int = { s -> s + extra }  // invokedynamic with type (I)Function1\n\nval line = \"delay $extra s\"                   // invokedynamic makeConcatWithConstants (target 9+)"},
  "note": "Both compilers send lambdas through `LambdaMetafactory`, so both get hidden `$$Lambda` classes, a shared instance when nothing is captured, and one class per lambda expression. Two real differences show up in javap. Kotlin's function types are generic interfaces (`Function1<P, R>`), so an `(Int) -> Int` boxes its `Int` through `invoke(Object): Object`, while Java's `IntUnaryOperator` stays with plain `int`. And in this track's kotlinc 2.4.21 build, a function reference such as `::add` assigned to a function type compiled to an ordinary generated class instead of an `invokedynamic`. Kotlin's `inline` functions such as `forEach` and `map` avoid the lambda object entirely, which Java can't do."
 },
 "worked": {
  "title": "What does this lambda capture?",
  "steps": [
   {"say": "The show program fires a list of lighting cues, each shifted by an offset in seconds. `lights` is the object that talks to the lighting desk. Before you read on: does the lambda capture anything, and how often does it allocate?", "code": "class CueRunner {\n    private final Lights lights;\n\n    void run(List<Cue> cues, int offset) {\n        cues.forEach(c -> lights.fire(c.name(), c.seconds() + offset));\n    }\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "class KCueRunner(private val lights: KLights) {\n    fun run(cues: List<KCue>, offset: Int) {\n        cues.forEach { c -> lights.fire(c.name, c.seconds + offset) }\n    }\n}"},
   {"say": "Ask javap. This is what it printed for the Java class, compiled by JDK 25's javac. The call-site type lists the captured values: `this`, because `lights` is a field and is read through `this`, and the `int` offset. For the same reason, the body became an instance method rather than a static one.", "code": "// 1. the factory: takes a CueRunner and an int, returns a Consumer\ninvokedynamic #13,  0   // InvokeDynamic #0:accept:(LCueRunner;I)Ljava/util/function/Consumer;\n// 2. the body: an instance method, the captured int first, then the element\nprivate void lambda$run$0(int, CueRunner$Cue);", "lang": "text"},
   {"say": "So Java allocates one `Consumer` per call to `run`, once per list and not once per cue, and calls it once per element. The Kotlin version compiles to no lambda at all: `forEach` is an `inline` function, so kotlinc pasted the loop into `run`. Its bytecode is `Iterable.iterator`, `hasNext`, `next` and a direct `KLights.fire`. Store the same lambda in a `val` first, and Kotlin does what Java does. The comments show what javap printed for this version:", "code": "fun runStored(cues: List<KCue>, offset: Int) {\n    val fire: (KCue) -> Unit = { c -> lights.fire(c.name, c.seconds + offset) }\n    cues.forEach(fire)\n}\n// 3. invokedynamic #92,  0   // InvokeDynamic #0:invoke:(LKCueRunner;I)Lkotlin/jvm/functions/Function1;\n//    private static final kotlin.Unit runStored$lambda$0(KCueRunner, int, KCue);", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "void runStored(List<Cue> cues, int offset) {\n    Consumer<Cue> fire = c -> lights.fire(c.name(), c.seconds() + offset);\n    cues.forEach(fire);\n}\n// 3. invokedynamic #23,  0   // InvokeDynamic #1:accept:(LCueRunner;I)Ljava/util/function/Consumer;\n//    Java has no inline functions, so a lambda passed to forEach is always an object"},
   {"say": "The verdict: one small object per list of cues is nothing next to driving the lighting desk, so leave the code as it is. The habit worth keeping is reading the call-site type. When it starts with your own class, the lambda holds `this`, which also keeps that object reachable for as long as the lambda lives.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Build three lambdas and a concatenation by hand",
  "minutes": 14,
  "files": ["labs/bytecode/src/main/java/workbench/bytecode/l03/HandMadeLambdas.java"],
  "run": "./gradlew :bytecode:test --tests 'workbench.bytecode.l03.*'",
  "steps": [
   "Run the tests once. All six fail with `UnsupportedOperationException`. `HandMadeLambdas` works with cue times in seconds, and its two body methods, `addSeconds` and `addDelay`, are already written.",
   "Add `private static final MethodHandles.Lookup LOOKUP = MethodHandles.lookup();`. Write `adder()` with `LambdaMetafactory.metafactory`: name `applyAsInt`, factory type `()IntBinaryOperator`, both interface types `(II)I`, and `LOOKUP.findStatic(HandMadeLambdas.class, \"addSeconds\", ...)`. Invoke the factory once, store the object in a static field, and return it every time.",
   "Write `plusDelay(int)`. The factory type is `(int)IntUnaryOperator`, the interface types are `(I)I`, and the body is `addDelay`, whose first parameter receives the captured delay. Store the factory handle (`site.getTarget()`), not an object, and call `(IntUnaryOperator) factory.invokeExact(delay)` on each call.",
   "Write `lengthOf()` with `LOOKUP.findVirtual(String.class, \"length\", methodType(int.class))`. The erased type is `(Object)Object`, and the instantiated type is `(String)Integer`.",
   "Write `countdown()` with `StringConcatFactory.makeConcatWithConstants(LOOKUP, \"countdown\", methodType(String.class, long.class, String.class), \"\\u0001 seconds to \\u0001\")` and return the call site's target.",
   "Run the tests until all six pass."
  ],
  "hints": [
   "Bootstrap methods throw checked exceptions. Wrap them once in a small helper that rethrows as `ExceptionInInitializerError` or `IllegalStateException`. Mind the order of your static fields: lesson 1's rule applies.",
   "`LambdaConversionException: Type mismatch` usually means the instantiated type (the sixth argument) doesn't match the body's parameters after the captured ones. For `plusDelay` the body is `(int, int)int`, and the lambda's own part is `(int)int`.",
   "`invokeExact` needs the exact static type: cast the result to `IntUnaryOperator` and pass an `int`. `invoke` is more forgiving if you get stuck."
  ],
  "done_when": "All six tests in `HandMadeLambdasTest` pass."
 },
 "drill": {
  "title": "Spell out a metafactory call",
  "minutes": 5,
  "prompt": "Close the page. Write the code that turns a static method `static String banner()` into a `Supplier<String>` with `LambdaMetafactory.metafactory`, without a lambda or a method reference. Label the six arguments. Then say which arguments the JVM supplies and which come from the BootstrapMethods table.",
  "answer": {
   "lang": "java",
   "src": "MethodHandles.Lookup lookup = MethodHandles.lookup();\nCallSite site = LambdaMetafactory.metafactory(\n        lookup,                                   // 1. caller (the JVM supplies it)\n        \"get\",                                    // 2. interface method name (JVM, from the call site)\n        methodType(Supplier.class),               // 3. factory type (JVM, from the call site)\n        methodType(Object.class),                 // 4. erased interface type (static argument)\n        lookup.findStatic(Owner.class, \"banner\", methodType(String.class)),  // 5. body (static argument)\n        methodType(String.class));                // 6. instantiated type (static argument)\n@SuppressWarnings(\"unchecked\")\nSupplier<String> s = (Supplier<String>) site.getTarget().invoke();",
   "alt": {"lang": "kotlin", "src": "val lookup = MethodHandles.lookup()\nval site = LambdaMetafactory.metafactory(\n    lookup,                                       // 1. caller (the JVM supplies it)\n    \"get\",                                        // 2. interface method name (JVM, from the call site)\n    methodType(Supplier::class.java),             // 3. factory type (JVM, from the call site)\n    methodType(Any::class.java),                  // 4. erased interface type (static argument)\n    lookup.findStatic(Owner::class.java, \"banner\", methodType(String::class.java)),  // 5. body\n    methodType(String::class.java),               // 6. instantiated type (static argument)\n)\n@Suppress(\"UNCHECKED_CAST\")\nval s = site.target.invoke() as Supplier<String>"}
  }
 },
 "recap": [
  "`invokedynamic` names a method name, a type and a bootstrap method. The bootstrap method runs once per call site and returns a `CallSite`; afterwards the instruction calls its target directly.",
  "A lambda is a private body method plus an `invokedynamic`. The call-site type lists the captured values, and `LambdaMetafactory` makes a hidden `$$Lambda` class at first use.",
  "Capturing nothing gives one shared instance; capturing gives a new object per evaluation, all of one class. Reading a field captures `this`.",
  "String `+` (JDK 9+) and Kotlin templates (JVM target 9+) use `StringConcatFactory.makeConcatWithConstants` with a `\\u0001` recipe. Records use `ObjectMethods.bootstrap`; pattern switches use `SwitchBootstraps`, and enum labels in them use condy.",
  "Kotlin lambdas use `invokedynamic` by default since Kotlin 2.0, `inline` functions such as `forEach` create no lambda at all, and a function reference became a generated class in this track's build.",
  "The limit: every call site links to a method that already exists. To make a whole new class that implements an interface while the program runs, you need the next lesson's dynamic proxies."
 ],
 "closing": "We met the cue that says \"ask the director\": an `invokedynamic` whose bootstrap method decides once and writes the answer in ink. Behind it sat a private body method, a hidden `$$Lambda` class, a fill-in-the-blanks recipe for strings, and a description for each record.\n\nNow run `javap -c -p` on a class of yours that uses lambdas, and read each call-site type. Any that starts with your own class captures `this`, and any with parameters allocates each time it runs.\n\nNext, we'll put a stand-in in front of an object: a class the JDK writes while your program runs. What does that class look like, and what does each call through it cost?",
 "quiz": [
  {
   "q": "`IntUnaryOperator delay(int extra) { return s -> s + extra; }` is called 1,000 times with 1,000 different values. How many lambda classes and lambda objects are created?",
   "options": ["1,000 classes and 1,000 objects", "One class and 1,000 objects", "One class and one object", "No classes: lambdas are compiled into the enclosing class"],
   "answer": 1,
   "why": "One lambda expression is one call site, linked once, so `LambdaMetafactory` makes one hidden class. The lambda captures `extra`, so each evaluation calls the factory and gets a new object. The single shared instance only happens when nothing is captured."
  },
  {
   "q": "javap shows `invokedynamic #0:apply:(Ltheatre/Lights;)Ljava/util/function/Function;` for a lambda inside the class `Lights`. What does it tell you?",
   "options": [
    "The lambda takes a `Lights` as its argument",
    "The lambda captures `this` (a `Lights`), so each evaluation creates a new object that keeps the `Lights` object reachable",
    "The lambda is a method reference to a static method",
    "The lambda was compiled by kotlinc"
   ],
   "answer": 1,
   "why": "The call-site type is the factory: its parameters are the captured values, and it returns the interface. A leading `Lights` means the lambda captured `this`, usually because its body reads a field or calls an instance method. The lambda's own parameter types are in the bootstrap arguments, not in this type."
  },
  {
   "q": "A Kotlin library built with kotlinc on the command line, with no `-jvm-target`, uses many string templates. What does `javap -c` show for them?",
   "options": [
    "`invokedynamic makeConcatWithConstants`, as for Java",
    "`new StringBuilder`, `append` and `toString`: the default target is Java 8, which has no `StringConcatFactory`",
    "`String.format` calls",
    "`invokedynamic` with `LambdaMetafactory`"
   ],
   "answer": 1,
   "why": "kotlinc 2.4.21 without `-jvm-target` writes class-file version 52 (Java 8), and `StringConcatFactory` exists only from JDK 9. With target 9 or newer (the labs use 21), templates compile to `makeConcatWithConstants`."
  },
  {
   "q": "Which of these compiles to plain bytecode, with no `invokedynamic` at all?",
   "options": ["A record's `toString()`", "`\"id=\" + id`", "A Kotlin `data class`'s `equals()`", "A pattern-matching `switch` over a sealed interface"],
   "answer": 2,
   "why": "kotlinc writes a data class's `equals` and `hashCode` as ordinary bytecode, and only its `toString` uses a concatenation `invokedynamic`. A record's three methods use `ObjectMethods.bootstrap`, string `+` uses `StringConcatFactory`, and a pattern switch uses `SwitchBootstraps.typeSwitch`."
  },
  {
   "q": "From *Type erasure and reified type parameters*: a `Function<String, Integer>` lambda's bootstrap arguments are `(Ljava/lang/Object;)Ljava/lang/Object;`, the body, and `(Ljava/lang/String;)Ljava/lang/Integer;`. Why does the metafactory need both types?",
   "options": [
    "Because erasure made `Function.apply` `(Object)Object` in bytecode, so the class must implement that method, and the second type tells it which casts and boxing to insert for this lambda",
    "The first type is for Java callers, the second for Kotlin callers",
    "The second type is only used by the debugger",
    "One is the type before the JIT runs, the other after"
   ],
   "answer": 0,
   "why": "Generics don't exist in descriptors, so the interface method the JVM calls is `apply(Object): Object`. The lambda's body wants a `String` and returns an `int`. The instantiated type tells `LambdaMetafactory` to cast the argument to `String` and box the result to `Integer` inside the generated method.",
   "from": "gen-08"
  }
 ],
 "flashcards": [
  {"front": "When does an invokedynamic's bootstrap method run?", "back": "Once per call site, the first time the instruction runs. It returns a `CallSite`, and later runs call its target directly."},
  {"front": "What does the call-site type `(I)Ljava/util/function/IntUnaryOperator;` on a lambda mean?", "back": "The lambda captures one `int`. The call site is a factory: give it the int, get an `IntUnaryOperator`."},
  {"front": "`() -> \"hello\"` is evaluated twice. Same object?", "back": "Yes. A non-capturing lambda's call site returns one shared instance."},
  {"front": "What kind of class is `Foo$$Lambda/0x...`, and can `Class.forName` find it?", "back": "A hidden class defined by `LambdaMetafactory` as a nestmate of `Foo`. `Class.forName` throws `ClassNotFoundException`."},
  {"front": "What is `\\u0001` in a `makeConcatWithConstants` recipe?", "back": "A slot for the next value. `\"\\u0001 seconds to \\u0001\"` takes two values."},
  {"front": "Which bootstrap builds a record's toString, equals and hashCode?", "back": "`java.lang.runtime.ObjectMethods.bootstrap` (JDK 16), given the record class, the component names and getter handles."},
  {"front": "Does Kotlin's `list.forEach { ... }` create a lambda object?", "back": "No. `forEach` is `inline`, so kotlinc copies the loop and the lambda body into the caller."}
 ],
 "terms": [
  {"term": "invokedynamic", "plain": "A call instruction whose target a bootstrap method chooses the first time it runs."},
  {"term": "Bootstrap method", "plain": "A static method, named in the BootstrapMethods table, that links an invokedynamic call site and returns a CallSite."},
  {"term": "CallSite", "plain": "An object holding the method handle an invokedynamic calls. ConstantCallSite can't be relinked; MutableCallSite can."},
  {"term": "Method handle", "plain": "A typed reference to a method that the JVM can call directly, much like a function pointer."},
  {"term": "LambdaMetafactory", "plain": "The JDK bootstrap method that turns a lambda's body method into an object implementing a functional interface."},
  {"term": "Hidden class", "plain": "A class defined with `Lookup.defineHiddenClass` (JDK 15) that no class loader can find by name."},
  {"term": "Capture", "plain": "Storing values from the surrounding code inside a lambda, such as a local variable or `this`."},
  {"term": "Condy", "plain": "`CONSTANT_Dynamic`: a constant-pool entry whose value a bootstrap method works out on first use."}
 ],
 "explain_back": {
  "prompt": "Explain to a teammate what happens, from javac to the first call, when Java code says `IntUnaryOperator later = s -> s + extra;`, and why the second time the line runs is cheaper than the first.",
  "answer": "javac moves the body into a private static method, `lambda$...$0(int extra, int s)`, with the captured `extra` first. Where the lambda appears, it emits an `invokedynamic` whose type is `(I)IntUnaryOperator`, plus a BootstrapMethods entry that points at `LambdaMetafactory.metafactory` with the erased interface type, the body and the instantiated type. The first time the line runs, the JVM calls the metafactory, which makes a hidden `$$Lambda` class whose `applyAsInt` calls the body, and returns a `ConstantCallSite` whose target constructs that class. The JVM links the instruction to it. The second time, there's no bootstrap call and no class to make: the instruction calls the target, which allocates one small object holding `extra`. If the lambda captured nothing, the target would just return the same instance every time."
 },
 "deeper": {
  "minutes": 10,
  "body": "Condy is easy to see. Compile this with javac 21 or later and run `javap -v`:\n\n```java\nsealed interface Shape permits Circle, Square {}\nrecord Circle(int r) implements Shape {}\nenum Square implements Shape { UNIT }\n\nstatic String name(Shape s) {\n    return switch (s) {\n        case Circle c -> \"circle \" + c.r();\n        case Square.UNIT -> \"unit square\";\n    };\n}\n```\n\n```kotlin\n// kotlinc compiles this `when` to an instanceof check and an enum comparison: no typeSwitch\nsealed interface Shape\ndata class Circle(val r: Int) : Shape\nenum class Square : Shape { UNIT }\n\nfun name(s: Shape) = when (s) {\n    is Circle -> \"circle ${s.r}\"\n    Square.UNIT -> \"unit square\"\n}\n```\n\nThe `switch` becomes `invokedynamic typeSwitch:(Ljava/lang/Object;I)I` with `SwitchBootstraps.typeSwitch`. Among its static arguments is a `Dynamic` constant-pool entry, shown as `invoke:Ljava/lang/Enum$EnumDesc;`, whose own bootstrap is `ConstantBootstraps.invoke` applied to `Enum$EnumDesc.of`. The enum label is built lazily, the first time the switch needs it, instead of forcing `Square` to initialize when the class loads.\n\nThe lambda factory changed tools recently. At jdk-23-ga, `InnerClassLambdaMetafactory` imports the JDK's internal copy of ASM, a library for writing class files; at jdk-24-ga it imports `java.lang.classfile`. Your class files didn't change at all. That's the point of `invokedynamic`: the JDK swapped its strategy underneath, and every lambda compiled since Java 8 picked it up."
 },
 "sources": [
  {"title": "LambdaMetafactory (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/invoke/LambdaMetafactory.html"},
  {"title": "StringConcatFactory (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/invoke/StringConcatFactory.html"},
  {"title": "JEP 280: Indify String Concatenation", "url": "https://openjdk.org/jeps/280"},
  {"title": "ObjectMethods (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/runtime/ObjectMethods.html"},
  {"title": "What's new in Kotlin 2.0.0", "url": "https://kotlinlang.org/docs/whatsnew20.html"}
 ]
}
# spread the correct answers over the option positions
for q, idx in zip(L["quiz"], [1, 3, 2, 0, 0]):
    right = q["options"].pop(q["answer"])
    q["options"].insert(idx, right)
    q["answer"] = idx
out = ROOT / "content/lessons/cls-03.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
