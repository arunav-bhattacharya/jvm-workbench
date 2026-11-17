import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/bytecode/src"
P = "java/workbench/bytecode/l06"
K = "kotlin/workbench/bytecode/l06"
PRE = "labs/bytecode/preview"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :bytecode:demo -Pmain=workbench.bytecode.l06."

KT_RUN = lambda name, jar: f"kotlinc bytecode/preview/{name}.kt -jvm-target 21 -include-runtime -d build/{jar}.jar && java -jar build/{jar}.jar"


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


# ---- figure: a transform maps each element to zero, one or more elements ----
ins = ["lload 0", "ldc 32L", "lmul", "ldc 1000L", "ldiv", "lreturn"]
outs = ["lload 0", "ldc 40L", "lmul", "ldc 1000L", "ldiv", "lreturn"]
parts = ['<svg viewBox="0 0 680 300" role="img" aria-label="A class transform drops the debugTrace method and keeps seconds. Inside seconds, a code transform passes every instruction through unchanged except ldc 32L, which it replaces with ldc 40L.">']
parts.append('<text class="t-s t-m" x="20" y="22">class elements of Fade</text>')
parts.append('<rect class="box" x="20" y="34" width="150" height="34" rx="8"/><text class="t-s t-code" x="95" y="56" text-anchor="middle">method seconds</text>')
parts.append('<rect class="box-bad" x="190" y="34" width="170" height="34" rx="8"/><text class="t-s t-code" x="275" y="56" text-anchor="middle">method debugTrace</text>')
parts.append('<text class="t-s t-bad" x="470" y="56" text-anchor="middle">dropping(...): debugTrace removed</text>')
parts.append('<text class="t-s t-m" x="20" y="102">code elements of seconds: before, then after</text>')
for i, t in enumerate(ins):
    x = 20 + i * 108
    cls = "box-a" if i == 1 else "box"
    parts.append(f'<rect class="{cls}" x="{x}" y="114" width="100" height="34" rx="8"/><text class="t-s t-code" x="{x + 50}" y="136" text-anchor="middle">{t}</text>')
    parts.append(f'<line class="{"ln-a" if i == 1 else "ln-d"}" x1="{x + 50}" y1="148" x2="{x + 50}" y2="196" marker-end="url(#arr)"/>')
for i, t in enumerate(outs):
    x = 20 + i * 108
    cls = "box-ok" if i == 1 else "box"
    parts.append(f'<rect class="{cls}" x="{x}" y="200" width="100" height="34" rx="8"/><text class="t-s t-code" x="{x + 50}" y="222" text-anchor="middle">{t}</text>')
parts.append('<text class="t-s t-m" x="340" y="262" text-anchor="middle">each element: cob.with(element) passes it through, nothing drops it, other calls replace it</text>')
parts.append('<text class="t-s t-a" x="340" y="284" text-anchor="middle">ldc 32L was replaced; the other five passed through unchanged</text>')
parts.append('</svg>')
FIG = "\n".join(parts)

TOUR = {"lang": "java", "title": "ClassFileTour.java (JDK 24+)", "src": read(f"{PRE}/ClassFileTour.java"),
        "run": "java bytecode/preview/ClassFileTour.java", "file": f"{PRE}/ClassFileTour.java",
        "alt": {"lang": "kotlin", "title": "ClassFileTour.kt (JDK 24+)", "src": read(f"{PRE}/ClassFileTour.kt"),
                "run": KT_RUN("ClassFileTour", "cftour"), "file": f"{PRE}/ClassFileTour.kt"}}
FORGE = {"lang": "java", "title": "ClassFileForge.java (JDK 24+)", "src": read(f"{PRE}/ClassFileForge.java"),
         "run": "java bytecode/preview/ClassFileForge.java", "file": f"{PRE}/ClassFileForge.java",
         "alt": {"lang": "kotlin", "title": "ClassFileForge.kt (JDK 24+)", "src": read(f"{PRE}/ClassFileForge.kt"),
                 "run": KT_RUN("ClassFileForge", "cfforge"), "file": f"{PRE}/ClassFileForge.kt"}}

OPENING = """A theatre's prompt book follows a strict layout. The first page carries a stamp naming the edition of the house rules it follows. Then comes the glossary, a numbered list of every name the book uses, and then the cues. A company that wanted to print its own pages had to borrow a printing press from outside, and get a new one each time the house rules changed.

A class file is that kind of page, and its house rules change with every JDK release, every six months. In the last lesson, Byte Buddy wrote subclasses and handed their bytes to a class loader. It prints them with a press it carries inside, a copy of a library called ASM. Since JDK 24, Java has a press of its own: the ClassFile API.

The easy trap is trusting a page because it printed. A class can build, pass the JVM's checks and load, and still compute the wrong answer. In this lesson, we'll read a class file's first bytes by hand, read the same class with the ClassFile API, print a new class from scratch, and edit one safely. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_HDR = """DataInputStream in = new DataInputStream(new ByteArrayInputStream(bytes));
int magic = in.readInt();               // u4: 0xCAFEBABE
int minor = in.readUnsignedShort();     // u2
int major = in.readUnsignedShort();     // u2: 65 = Java 21, 69 = Java 25
int poolCount = in.readUnsignedShort(); // u2: entries are numbered 1 .. poolCount - 1"""
K_HDR = """val input = DataInputStream(ByteArrayInputStream(bytes))
val magic = input.readInt()                // u4: 0xCAFEBABE
val minor = input.readUnsignedShort()      // u2
val major = input.readUnsignedShort()      // u2: 65 = Java 21, 69 = Java 25
val poolCount = input.readUnsignedShort()  // u2: entries are numbered 1 .. poolCount - 1"""

S0 = """Every tool in this track reads or writes the same format: javap, the verifier (the JVM's check that bytecode is type-safe), `Proxy`, the lambda machinery, Byte Buddy, and the agents of the next lesson. A class file is an array of bytes with a fixed layout, set out in chapter 4 of the JVM specification. Here are the first ten bytes of `java/lang/Object.class` on JDK 25, as this section's demo prints them:

```text
ca fe ba be  00 00  00 45  00 73
magic        minor  major  constant_pool_count
```

The first four bytes are the magic number, `0xCAFEBABE`: the stamp that says "this is a class file". Then come two version numbers. The major version is 0x45, which is 69, and Java 25 wrote it. From Java 5 on, the Java version is the major version minus 44. A JVM refuses a class file whose major version is newer than its own, with `UnsupportedClassVersionError`. The labs' own classes say `00 41`, which is 65, because the build compiles them with `release 21`.

Then comes `constant_pool_count`, and after it the constant pool itself: lesson 2's glossary, a numbered table of every name and constant the class uses. Every number in the file is big-endian, biggest byte first, which is exactly how `DataInputStream` reads. So the first four fields take four lines:

""" + pair(J_HDR, K_HDR) + """

The glossary is the hard part. Each entry starts with a one-byte tag, and the tag decides how many bytes follow. A `Utf8` entry, a piece of text, has a two-byte length and then the text. A `Class` entry has two bytes: the number of the `Utf8` entry that holds the class's name. A `Methodref`, a reference to a method, has four. And a `Long` or `Double` entry takes up two numbers. Remember lesson 2's `javap -v` listing of `StackDemo`:

```text
   #7 = Long               1000l
   #9 = InvokeDynamic      #0:#10         // #0:makeConcatWithConstants:(JLjava/lang/String;)Ljava/lang/String;
```

There is no `#8`, because the 8-byte constant at `#7` sits in two seats. After the glossary come the access flags, then `this_class`, the number of the `Class` entry that names this class. Then come the superclass, the interfaces, the fields, the methods and the attributes. In the lab, you write this walk yourself and check it against a real class-file library.

**Each entry's size depends on its tag, so one wrong count shifts everything after it. Count `Long` and `Double` twice.**

That walk is the reason a library helps. Anything that writes or changes classes must get this format exactly right, and the format gains a new major version every six months, sometimes with new kinds of entries. Until JDK 24, the JDK had no public library for it. Frameworks bundled ASM, the long-standing class-file library (Byte Buddy carries its own copy), and needed a new release for each new class-file version. The JDK kept a private copy of ASM too; it's gone from the jdk-25-ga source.

Doing the walk by hand once teaches you the format. Doing it for every class, on every JDK, is a job for a press."""

# ---------------------------------------------------------------- section 1
J_PARSE = """ClassModel cm = ClassFile.of().parse(bytes);
System.out.println(cm.thisClass().asInternalName() + " major " + cm.majorVersion());
for (MethodModel m : cm.methods()) {
    long invokes = m.code()
            .map(code -> code.elementStream().filter(e -> e instanceof InvokeInstruction).count())
            .orElse(0L);
    System.out.println(m.methodName().stringValue() + m.methodType().stringValue() + " invokes=" + invokes);
}"""
K_PARSE = """val cm = ClassFile.of().parse(bytes)
println("${cm.thisClass().asInternalName()} major ${cm.majorVersion()}")
for (m in cm.methods()) {
    val invokes = m.code()
        .map { code -> code.elementStream().filter { it is InvokeInstruction }.count() }
        .orElse(0L)
    println("${m.methodName().stringValue()}${m.methodType().stringValue()} invokes=$invokes")
}"""

S1 = """The package `java.lang.classfile` is the JDK's own class-file library. It was a preview feature in JDK 22 (JEP 457) and JDK 23 (JEP 466), and became final in JDK 24 (JEP 484). So on JDK 25 you use it with no special flags. A preview feature is a complete design that you can only use with `--enable-preview`, while the JDK team collects feedback. The labs compile with `release 21`, which can't see the package, so this lesson's ClassFile API code lives in single-file programs under `labs/bytecode/preview/`. You run them with `java File.java` on JDK 24 or later. On JDK 21 they stop at once with `package java.lang.classfile does not exist`.

Everything starts at `ClassFile.of()`. Its `parse` method turns bytes into a `ClassModel`:

""" + pair(J_PARSE, K_PARSE) + """

A model is an immutable description of one part of a class file: the class, a field, a method, or a method's code. Picture the press reading a page into a stack of typed cards. The package documentation adds that a `ClassModel` "is inflated lazily; most parts of the classfile are not parsed until they are actually needed". So a broken method can parse fine, and throw `IllegalArgumentException` only when you open it.

Each model can also be read as a sequence of **elements**, its cards in order. A class's elements are its methods, fields and attributes. A method's code is a sequence of instructions, labels and other code elements. Each instruction is an object with a type you can test, such as `InvokeInstruction`, `ConstantInstruction` or `InvokeDynamicInstruction`. The rest of the API is built on this one idea. Reading walks the elements, building writes elements, and transforming maps elements to elements.

Let's point it at lesson 2's `StackDemo`, the class with the lighting fade. `ClassFileTour` parses it, counts the glossary entries by kind, and counts the invoke instructions in each method. On JDK 25 it prints:

```text
workbench/bytecode/l02/StackDemo extends java/lang/Object, major 65
constant pool: {ClassEntry=7, FieldRefEntry=1, InvokeDynamicEntry=1, LongEntry=2, MethodHandleEntry=1, MethodRefEntry=5, NameAndTypeEntry=7, StringEntry=2, Utf8Entry=43}
  <init>()V  invokes=1
  seconds(JI)J  invokes=0
  describe(Ljava/lang/String;J)Ljava/lang/String;  invokes=0
  main([Ljava/lang/String;)V  invokes=3
```

The two `LongEntry` cards are the 1000 and the 32 from the fade. `seconds(JI)J` does arithmetic and calls nothing. `describe` builds a string with `+`, and yet its count is 0. Keep that in mind for the Try it.

Names and types come back as glossary entries. `methodName()` is a `Utf8Entry`, which is why the code calls `stringValue()`. When you build a class, you go the other way. You pass symbolic descriptions from `java.lang.constant`, such as `ClassDesc.of("Fade")` for a class or `MethodTypeDesc.of(CD_long, CD_long)` for a method type, and the library creates the entries.

Reading is half of what a press does. The other half is printing."""

# ---------------------------------------------------------------- section 2
J_BUILD = """byte[] fade = ClassFile.of().build(ClassDesc.of("Fade"), clb -> clb
        .withFlags(ClassFile.ACC_PUBLIC | ClassFile.ACC_FINAL)
        .withMethodBody("seconds", MethodTypeDesc.of(CD_long, CD_long), ClassFile.ACC_PUBLIC | ClassFile.ACC_STATIC,
                cob -> cob
                        .lload(0)          // the number of steps, slots 0 and 1
                        .ldc(32L)          // one step, in milliseconds
                        .lmul()
                        .ldc(1_000L)
                        .ldiv()
                        .lreturn()));
Class<?> c = MethodHandles.lookup().defineClass(fade);   // load it next to this class"""
K_BUILD = """val fade = ClassFile.of().build(ClassDesc.of("Fade")) { clb ->
    clb.withFlags(ClassFile.ACC_PUBLIC or ClassFile.ACC_FINAL)
    clb.withMethodBody("seconds", MethodTypeDesc.of(CD_long, CD_long), ClassFile.ACC_PUBLIC or ClassFile.ACC_STATIC) { cob ->
        cob.lload(0)                       // the number of steps, slots 0 and 1
            .loadConstant(32L)             // one step, in milliseconds (Kotlin: see below)
            .lmul()
            .loadConstant(1_000L)
            .ldiv()
            .lreturn()
    }
}
val c = MethodHandles.lookup().defineClass(fade)               // load it next to this class"""

S2 = """To print a class, you don't create builder objects yourself. You pass lambdas, and the library hands each one the builder for its level: a `ClassBuilder` for the class, a `CodeBuilder` for a method body. A `CodeBuilder` has one method per instruction, so a method body reads like the javap listings of lesson 2. Here is lesson 2's fade again, as a class of its own. `Fade.seconds(steps)` says how long a fade of that many 32-millisecond steps runs, in whole seconds:

""" + pair(J_BUILD, K_BUILD) + """

Read it the way lesson 2's stagehand would. `lload(0)` puts the number of steps on the pile of cue cards; a `long` takes local slots 0 and 1. `ldc(32L)` pushes the step length, and `lmul` multiplies the top two cards. `ldc(1_000L)` and `ldiv` turn milliseconds into seconds, and `lreturn` hands back the `long` on top. Then `MethodHandles.lookup().defineClass` loads the bytes as a class, in the same package and class loader as the class that calls it. (The demo's `Fade` also gets an empty `debugTrace` method, for the next section.) The demo prints:

```text
built Fade: 198 bytes, verify errors []
Fade.seconds(12500) = 400
```

That's 400 seconds, the same fade that lesson 2's `StackDemo` printed.

The builder writes what you tell it to, including nonsense. A method declared to return an `int` that pushes a `String` builds without a complaint. Lesson 1 showed what happens when such a class loads: `defineClass` can succeed, and a `VerifyError` arrives later. `ClassFile.of().verify(bytes)` runs the verifier's checks on the bytes first and returns a list of errors. The verifier is the JVM's proofreader. It checks that every instruction finds values of the right type, and it never reads the plot:

```text
verify(Broken): [java.lang.VerifyError: Bad type on operand stack in Broken::answer() @2 (integer_type is not assignable from java/lang/String)]
```

An empty list proves less than it seems. Delete the `ldiv`, and the class still verifies. Two `long` values are left on the stack at `lreturn`, which is legal, and `seconds(12500)` returns 1000, the last value pushed. You'll try it in a moment.

**`verify` proves that generated code is type-safe, not that it's right. Test what it computes.**

Kotlin has one trap here. `ldc` takes a `java.lang.constant.ConstantDesc`, an interface that Java's `String` and `Long` implement. Kotlin's `String` and `Long` types don't show that interface, so `cob.ldc("forty-two")` doesn't compile in Kotlin. Use `loadConstant(32L)`, which has overloads for primitives, or pass a glossary entry: `cob.ldc(cob.constantPool().stringEntry("forty-two"))`.

We can print new pages now. The harder job is to edit a page that already exists without smudging the rest."""

# ---------------------------------------------------------------- section 3
J_TRANS = """CodeTransform slower = (cob, element) -> {
    if (element instanceof ConstantInstruction ci && Long.valueOf(32L).equals(ci.constantValue())) {
        cob.ldc(40L);             // replace
    } else {
        cob.with(element);        // pass through
    }
};
ClassTransform transform = ClassTransform
        .dropping(e -> e instanceof MethodModel m && m.methodName().stringValue().startsWith("debug"))
        .andThen(ClassTransform.transformingMethodBodies(slower));
byte[] v2 = cf.transformClass(cf.parse(fade), ClassDesc.of("FadeV2"), transform);"""
K_TRANS = """val slower = CodeTransform { cob, element ->
    if (element is ConstantInstruction && element.constantValue().equals(32L)) {
        cob.loadConstant(40L)     // replace
    } else {
        cob.with(element)         // pass through
    }
}
val transform = ClassTransform
    .dropping { it is MethodModel && it.methodName().stringValue().startsWith("debug") }
    .andThen(ClassTransform.transformingMethodBodies(slower))
val v2 = cf.transformClass(cf.parse(fade), ClassDesc.of("FadeV2"), transform)"""

S3 = """Changing an existing class is where elements pay off. The package documentation puts it in one sentence: "Transformation can be viewed as a 'flatMap' operation on the sequence of elements; for every element, we could pass it through unchanged, drop it, or replace it with one or more elements." (`flatMap` is the stream operation that turns each item into zero, one or more items.)

Picture copying a page of the prompt book line by line. For each line you can copy it as it is, leave it out, or write something else in its place. A `ClassTransform` sees a class's elements, and a `CodeTransform` sees the instructions of one method. Inside a transform, you hand each element to the builder: `builder.with(element)` passes it through, doing nothing drops it, and calling other builder methods replaces it. This transform drops every method whose name starts with `debug`, and makes every fade slower, with 40 ms steps instead of 32:

""" + pair(J_TRANS, K_TRANS) + """

The new class, `FadeV2`, has only `seconds` left, and the same 12,500 steps now take longer:

```text
FadeV2 methods [seconds], seconds(12500) = 500
```

Everything the transform passed through was copied unchanged. That's also the default: a transform that changes nothing reproduces the class.

The JDK prints its own classes on this press. `ProxyGenerator` moved from its internal ASM to `java.lang.classfile` in JDK 23, and the lambda class generator, `InnerClassLambdaMetafactory`, followed in JDK 24. So on JDK 25, the `$Proxy0` of lesson 4 and the `$$Lambda` classes of lesson 3 come from the code you just ran.

Who should use it? A tool that only needs to run on JDK 24 or later can drop its ASM dependency, because the API always matches the JDK it runs on. A library that must support older JDKs can't. Byte Buddy's regular jar targets Java 8 and its `-jdk5` jar targets Java 5, so it keeps its bundled ASM and bridges to the ClassFile API when it finds one. Its release notes for 1.16.0 say: "Include support for JDK Class File API".

**To edit a class, copy it element by element. Pass through everything you don't mean to change.**

Here's the limit of today's tool. Every class in this lesson was new: we printed `Fade`, then copied it into `FadeV2` under a new name. A class that is already loaded, with objects already using it, can't be replaced by defining another class. Changing that one takes an agent."""

L = {
 "id": "cls-06",
 "title": "Generating and transforming classes with the ClassFile API",
 "minutes": 35,
 "goal": "By the end you can read a class file's header and constant pool by hand, and with the ClassFile API (final in JDK 24) parse a class into a model, build a new class from builder lambdas, verify it before loading, and write a transform that drops or replaces elements.",
 "opening": OPENING,
 "warmup": {
  "q": "You read the first eight bytes of `java/lang/Object.class` from the JDK you're running. They are `ca fe ba be 00 00 00 45`. Which JDK is it?",
  "options": ["JDK 21", "JDK 25", "JDK 8", "You can't tell from the bytes"],
  "answer": 1,
  "why": "After the magic number `CAFEBABE` come the minor version (`00 00`) and the major version (`00 45`, which is 69). From Java 5 on, the Java version is major minus 44, so 69 is Java 25. JDK 21's own classes say `00 41` (65), and Java 8's say `00 34` (52). The first section reads these bytes with a small program."
 },
 "sections": [
  {
   "h": "Reading the page by hand: magic number, version and the glossary",
   "body": S0,
   "try": {
    "title": "Read three class-file headers",
    "minutes": 3,
    "steps": [
     "Before you run anything, predict the major version of `ClassFileHeader.class` (built by the labs), of `java.lang.Object` on the JDK you're using, and of `kotlin.Unit` from the Kotlin standard library.",
     "Run `ClassFileHeader`, then its Kotlin twin.",
     "If you have both JDK 21 and JDK 25 installed, run the Java version on each, from `labs/`: `java -cp bytecode/build/classes/java/demo:bytecode/build/classes/kotlin/demo workbench.bytecode.l06.ClassFileHeader`."
    ],
    "code": {"lang": "java", "title": "ClassFileHeader.java", "src": read(f"{lab}/demo/{P}/ClassFileHeader.java"), "run": RUN + "ClassFileHeader", "file": f"{lab}/demo/{P}/ClassFileHeader.java",
             "alt": {"lang": "kotlin", "title": "ClassFileHeader.kt", "src": read(f"{lab}/demo/{K}/ClassFileHeader.kt"), "run": RUN + "ClassFileHeaderKt", "file": f"{lab}/demo/{K}/ClassFileHeader.kt"}},
    "expect": "Every line starts with `ca fe ba be`. The labs' own classes, Java and Kotlin, are `version=65.0 (Java 21)`, because the build uses `release 21` and `jvmTarget 21`. `java.lang.Object` is `65.0 (Java 21)` with 123 pool entries on JDK 21, and `69.0 (Java 25)` with 114 on JDK 25, so the same program reports the JDK it runs on. `kotlin.Unit` is `52.0 (Java 8)`: the standard library is compiled for Java 8, so it runs everywhere."
   },
   "refs": [
    {"title": "JVM Specification SE 25, chapter 4: The class File Format", "url": "https://docs.oracle.com/javase/specs/jvms/se25/html/jvms-4.html", "kind": "docs"}
   ]
  },
  {
   "h": "Reading it with the ClassFile API: models and elements",
   "body": S1,
   "try": {
    "title": "Tour lesson 2's class with the ClassFile API",
    "minutes": 4,
    "steps": [
     "This needs JDK 24 or later. From `labs/`, make sure lesson 2's demo was built (`./gradlew :bytecode:demo -Pmain=workbench.bytecode.l02.StackDemo`), then run the command below. The Kotlin twin needs `kotlinc` running on JDK 24 or later.",
     "Compare the constant-pool counts with the `javap -v` listing you read in lesson 2.",
     "`describe` builds a string and calls nothing else, yet its count is 0. Before reading on: which instruction does it contain, and why didn't the filter count it?"
    ],
    "code": TOUR,
    "expect": "`workbench/bytecode/l02/StackDemo extends java/lang/Object, major 65`, a pool with `Utf8Entry=43`, `LongEntry=2` (1000 and 32) and one `InvokeDynamicEntry`, then four methods: `<init>()V invokes=1`, `seconds(JI)J invokes=0`, `describe(...) invokes=0` and `main(...) invokes=3`. `describe` contains an `invokedynamic`, lesson 3's string concatenation, which the API models as `InvokeDynamicInstruction`, a separate type from `InvokeInstruction`."
   },
   "refs": [
    {"title": "java.lang.classfile package (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/classfile/package-summary.html", "kind": "docs"}
   ]
  },
  {
   "h": "Printing a new class: builders, and a proofreader called verify",
   "body": S2,
   "try": {
    "title": "Build, verify, then break it",
    "minutes": 4,
    "steps": [
     "On JDK 24 or later, run `ClassFileForge` from `labs/` (command below), or build and run the Kotlin twin.",
     "Read the first three lines: the size of the generated class, its verify result, the fade length, and the verifier's message for `Broken`.",
     "In the `seconds` body, delete the `.ldiv()` line, and predict what `verify(fade)` reports and what `seconds(12500)` returns. Run it again."
    ],
    "code": FORGE,
    "expect": "`built Fade: 198 bytes, verify errors []`, `Fade.seconds(12500) = 400`, and `verify(Broken): [java.lang.VerifyError: Bad type on operand stack in Broken::answer() @2 (integer_type is not assignable from java/lang/String)]`. Without `ldiv`, the class is 197 bytes and still verifies with no errors, and `seconds(12500)` returns 1000. Two longs are left on the stack at `lreturn`, which the verifier allows, and the method returns the one on top, the last value pushed. The verifier proves the code is type-safe, not that it's right."
   }
  },
  {
   "h": "Editing a class safely: a transform keeps, drops or replaces each element",
   "body": S3,
   "figure": {"svg": FIG, "caption": "A transform walks the elements and decides, one at a time, to pass, drop or replace each one."},
   "try": {
    "title": "Write your own transform",
    "minutes": 4,
    "steps": [
     "Run `ClassFileForge` again and read the last line.",
     "Change the code transform so it also turns `1_000L` into `60_000L`, so that the method returns minutes, without touching the 32 branch. Predict the new `FadeV2.seconds(12500)` before you run it.",
     "Undo that, then remove the `.andThen(...)` part, keeping only `dropping`. Which number in the last line changes?"
    ],
    "code": FORGE,
    "expect": "Before your change: `FadeV2 methods [seconds], seconds(12500) = 500`. With both constants replaced: 12,500 x 40 / 60,000 = 8. The fade lasts 8 minutes and 20 seconds, and integer division quietly drops the 20. With only `dropping`, `FadeV2` still loses `debugTrace`, but `seconds` keeps the 32 and returns 400 again."
   }
  }
 ],
 "compare": {
  "title": "Reading a class's name in Java and Kotlin, by hand and with the API",
  "java": {"title": "ThisClass.java", "src": "// by hand (any JDK): walk the pool, then read this_class\nstatic String thisClass(byte[] bytes) {\n    return ClassFileFacts.thisClass(bytes);          // the lab's DataInputStream walk\n}\n\n// with the ClassFile API (JDK 24+)\nstatic String thisClassWithApi(byte[] bytes) {\n    return ClassFile.of().parse(bytes).thisClass().asInternalName();\n}"},
  "kotlin": {"title": "ThisClass.kt", "src": "// by hand (any JDK): walk the pool, then read this_class\nfun thisClass(bytes: ByteArray): String =\n    ClassFileFacts.thisClass(bytes)                  // the lab's DataInputStream walk\n\n// with the ClassFile API (JDK 24+)\nfun thisClassWithApi(bytes: ByteArray): String =\n    ClassFile.of().parse(bytes).thisClass().asInternalName()"},
  "note": "Same bytes, same answer. The API version is one line, because the library walks the pool for you, and only as far as it needs to. The language differences are small but real. Kotlin calls the API through ordinary SAM conversion for its `Consumer` and `CodeTransform` parameters, and writes access flags with `or` instead of `|`. Kotlin's `String` and `Long` types don't show Java's `ConstantDesc`, so `ldc(\"...\")` needs a constant-pool entry, or `loadConstant` for primitives. And compiling Kotlin against the API needs kotlinc to run on JDK 24 or later (or to point `-jdk-home` at one), whatever `-jvm-target` you choose."
 },
 "worked": {
  "title": "Find the jar that broke the start-up",
  "steps": [
   {"say": "The theatre's ticket app starts on JDK 21 and stops at once. A jar is a zip file of class files, and the app is built from several of them. Which part of the message tells you what to look for?", "code": "Error: LinkageError occurred while loading main class theatre.booking.SeatMap\n\tjava.lang.UnsupportedClassVersionError: theatre/booking/SeatMap has been compiled by a more recent version of the Java Runtime (class file version 69.0), this version of the Java Runtime only recognizes class file versions up to 65.0", "lang": "text"},
   {"say": "Class file version 69.0 is Java 25 (69 - 44), and the runtime only knows up to 65, Java 21. Something was compiled for JDK 25. Here one class is named, but a jar can mix versions, so check every class. Read each entry's header with the lab's code.", "code": "try (JarFile jar = new JarFile(path.toFile())) {\n    jar.stream()\n       .filter(e -> e.getName().endsWith(\".class\"))\n       .forEach(e -> {\n           try (InputStream in = jar.getInputStream(e)) {\n               // 1. read magic, minor, major from the first 10 bytes\n               ClassFileFacts.Header h = ClassFileFacts.header(in.readNBytes(10));\n               // 2. report anything newer than the runtime\n               if (h.major() > 65) System.out.println(e.getName() + \" -> Java \" + ClassFileFacts.javaVersion(h.major()));\n           } catch (IOException ex) {\n               throw new UncheckedIOException(ex);\n           }\n       });\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "JarFile(path.toFile()).use { jar ->\n    jar.stream()\n        .filter { it.name.endsWith(\".class\") }\n        .forEach { e ->\n            // 1. read magic, minor, major from the first 10 bytes\n            val h = jar.getInputStream(e).use { ClassFileFacts.header(it.readNBytes(10)) }\n            // 2. report anything newer than the runtime\n            if (h.major() > 65) println(\"${e.name} -> Java ${ClassFileFacts.javaVersion(h.major())}\")\n        }\n}"},
   {"say": "Two caveats. A multi-release jar, one that carries extra copies of classes for newer JDKs, keeps them under `META-INF/versions/25/`, and those are allowed: the JVM only loads them on JDK 25. So skip that prefix, or you'll get false alarms. And `module-info.class` has a version too. When the culprit is your own code, the fix is in the build: compile with `--release 21` (in Gradle, `options.release.set(21)`) and `jvmTarget = 21` for Kotlin, as the labs do, so the compilers also refuse APIs newer than JDK 21.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Read the constant pool by hand",
  "minutes": 15,
  "files": ["labs/bytecode/src/main/java/workbench/bytecode/l06/ClassFileFacts.java"],
  "run": "./gradlew :bytecode:test --tests 'workbench.bytecode.l06.*'",
  "steps": [
   "Run the tests once. All seven fail. Read the class-file layout and the tag table in the Javadoc of `ClassFileFacts`.",
   "Write `header`: wrap the bytes in a `DataInputStream`, read the `int` magic and throw `IllegalArgumentException` (with \"magic\" in the message) if it isn't `0xCAFEBABE`, then read three unsigned shorts. Write `javaVersion` as `major - 44`, rejecting anything below 49.",
   "Write a private pool walk: for `i` from 1 to `count - 1`, read the tag, then either keep the value (`readUTF()` for tag 1, the name index for tag 7) or skip the right number of bytes. After a tag 5 or 6, add one more to `i`.",
   "Write `referencedClasses` with the walk: the Utf8 string at each Class entry's name index. Write `thisClass`: after the walk, read `access_flags`, then `this_class`, and look up its name.",
   "Run the tests until all seven pass. The expected answers come from ASM, so a pass means your reader agrees with a production library on Java, Kotlin and JDK classes."
  ],
  "hints": [
   "A wrong byte count anywhere in the walk shifts everything after it, so the symptom is usually `unknown constant pool tag` far from the bug. Check the table entry for the last tag you handled.",
   "`DataInputStream.readUTF()` reads a two-byte length and then the bytes, in the class file's own \"modified UTF-8\". That's exactly a Utf8 entry, so you don't decode anything yourself.",
   "Forgetting the extra index after `Long` and `Double` passes for some classes and fails for `Fixture`, which has both."
  ],
  "done_when": "All seven tests in `ClassFileFactsTest` pass."
 },
 "drill": {
  "title": "The constant pool walk from memory",
  "minutes": 5,
  "prompt": "Close the page and the lab. Write the loop that walks a constant pool with a `DataInputStream`, given `count`. Handle Utf8, Class, the fixed-size entries and the two-index entries. Then check: which tags take two pool indexes, and which entry has a 3-byte body?",
  "answer": {
   "lang": "java",
   "src": "for (int i = 1; i < count; i++) {                 // index 0 is never used\n    int tag = in.readUnsignedByte();\n    switch (tag) {\n        case 1 -> utf8[i] = in.readUTF();             // Utf8: u2 length + bytes\n        case 7 -> classNameIndex[i] = in.readUnsignedShort();\n        case 8, 16, 19, 20 -> in.skipBytes(2);        // String, MethodType, Module, Package\n        case 15 -> in.skipBytes(3);                   // MethodHandle: u1 kind + u2 index\n        case 3, 4, 9, 10, 11, 12, 17, 18 -> in.skipBytes(4);\n        case 5, 6 -> { in.skipBytes(8); i++; }        // Long, Double: two indexes\n        default -> throw new IllegalArgumentException(\"tag \" + tag + \" at \" + i);\n    }\n}",
   "alt": {"lang": "kotlin", "src": "var i = 1                                           // index 0 is never used\nwhile (i < count) {\n    when (val tag = input.readUnsignedByte()) {\n        1 -> utf8[i] = input.readUTF()                // Utf8: u2 length + bytes\n        7 -> classNameIndex[i] = input.readUnsignedShort()\n        8, 16, 19, 20 -> input.skipBytes(2)           // String, MethodType, Module, Package\n        15 -> input.skipBytes(3)                      // MethodHandle: u1 kind + u2 index\n        3, 4, 9, 10, 11, 12, 17, 18 -> input.skipBytes(4)\n        5, 6 -> { input.skipBytes(8); i++ }           // Long, Double: two indexes\n        else -> throw IllegalArgumentException(\"tag $tag at $i\")\n    }\n    i++\n}"}
  }
 },
 "recap": [
  "A class file starts with `CAFEBABE`, the minor and major version (Java version = major - 44 from Java 5 on: 65 is 21, 69 is 25), then the constant pool.",
  "Each pool entry starts with a tag that fixes its size; `Long` and `Double` take two indexes. `this_class` comes right after the pool and the access flags.",
  "The ClassFile API (`java.lang.classfile`) was a preview in JDK 22 and 23 and became final in JDK 24 (JEP 484). Labs built with `release 21` can't use it, so its code runs as single-file programs on JDK 24 or later.",
  "`ClassFile.of().parse` gives a lazy, immutable `ClassModel`, which is also a sequence of elements, such as methods or instructions. `build` takes builder lambdas.",
  "`verify` checks type safety before loading, not correctness, and `transformClass` copies a class element by element: pass with `with`, drop by doing nothing, or replace.",
  "The limit: these tools make new classes. Changing a class that is already loaded, under objects that use it, needs an agent."
 ],
 "closing": "We started with a prompt book's strict layout: a stamp, a glossary, then the cues. We read that layout byte by byte. Then the JDK's own press read it as models and elements, printed a new `Fade`, proofread it with `verify`, and copied it into `FadeV2` line by line.\n\nNow look for a test in your project that only checks that generated code loads, or that a class verifies. Add one assertion on what the code computes.\n\nNext, we'll stop making new classes and change one that is already running. How does an agent slip a note into a class before it loads, or even after?",
 "quiz": [
  {
   "q": "A class file's major version is 61. Which is the oldest JDK that can load it?",
   "options": ["JDK 11", "JDK 17", "JDK 21", "JDK 16"],
   "answer": 1,
   "why": "From Java 5 on, the Java version is major minus 44, so 61 is Java 17. A JVM loads class files up to its own major version: JDK 17 and later load it, and JDK 16 rejects it with `UnsupportedClassVersionError`."
  },
  {
   "q": "Your pool walk handles every tag but forgets that `Long` takes two indexes. What happens on a class with a `long` constant?",
   "options": [
    "Nothing: the second index is empty, so skipping it is optional",
    "Every index after the long is off by one, and the loop reads one entry too many, past the end of the pool: names come out wrong, or the walk fails on an unknown tag",
    "`readUTF` throws at once",
    "Only the long's own value comes out wrong"
   ],
   "answer": 1,
   "why": "You skipped the right number of bytes, but the numbering is off by one. Every later entry gets an index one too small, so a `Class` entry's name index points at the wrong string, and the loop expects one more entry than the file has, so it reads the access flags as if they were a tag. The symptom shows up far from the cause, usually as an unknown tag or garbage names. That's why the lab's `Fixture` has both a `long` and a `double`."
  },
  {
   "q": "`ClassFile.of().verify(bytes)` returns an empty list for your generated class. What do you know?",
   "options": [
    "The class computes the right results",
    "The bytecode is type-safe for the verifier, for example every return finds the type its descriptor promises, but it may still compute the wrong thing",
    "The class has already been loaded",
    "The class will run on every JDK"
   ],
   "answer": 1,
   "why": "Verification checks types and stack shapes, not meaning. A fade method with a missing `ldiv` still verifies and returns the wrong number. A class verified today can also fail to load on an older JDK because of its version number."
  },
  {
   "q": "You want a build-time check, running on JDK 25, that fails if any class in the ticket app references `java/util/Random` (the seat lottery must use `SecureRandom`). Which tool fits best?",
   "options": [
    "A JDK dynamic proxy around every class",
    "`ClassFile.of().parse(bytes)` over every class file, checking the class entries in each constant pool",
    "A Java agent that retransforms every loaded class",
    "`Class.forName` on every class, with initialization"
   ],
   "answer": 1,
   "why": "Every class a class mentions has a `Class` entry in its constant pool, so parsing the files is enough. No class needs to be loaded, initialized or run. Proxies intercept calls while a program runs, agents change loaded classes, and `Class.forName` runs static initializers, the last thing a build check should do."
  },
  {
   "q": "From *Reading bytecode*: `javap -v` on `StackDemo` shows `#7 = Long 1000l` and then `#9 = InvokeDynamic ...`, with no entry 8. Why?",
   "options": [
    "javap hides unused entries",
    "The JIT optimized entry 8 away",
    "A `Long` (and a `Double`) entry takes two constant-pool indexes, so 8 is the second half of 7",
    "Entry 8 is kept for the class's own name"
   ],
   "answer": 2,
   "why": "The class-file format numbers 8-byte constants as two entries, and the next entry's index skips one. Any reader that walks the pool must add an extra step after each `Long` or `Double`, which is the bug the lab's fixture is designed to catch.",
   "from": "cls-02"
  }
 ],
 "flashcards": [
  {"front": "What are the first four fields of a class file?", "back": "u4 magic `0xCAFEBABE`, u2 minor version, u2 major version, u2 constant_pool_count."},
  {"front": "How do you get the Java version from a class file's major version?", "back": "Subtract 44 (from Java 5 on): 52 is 8, 61 is 17, 65 is 21, 69 is 25."},
  {"front": "Which constant-pool entries take two indexes?", "back": "`Long` (tag 5) and `Double` (tag 6)."},
  {"front": "Since which JDK is `java.lang.classfile` a final API, and under which JEP?", "back": "JDK 24, JEP 484. It was a preview in JDK 22 (JEP 457) and JDK 23 (JEP 466)."},
  {"front": "In a ClassFile API transform, how do you keep, drop and replace an element?", "back": "Keep: `builder.with(element)`. Drop: don't pass it on. Replace: call other builder methods instead."},
  {"front": "What does `ClassFile.of().verify(bytes)` guarantee when it returns an empty list?", "back": "That the bytecode passes the verifier's type checks. Not that it computes the right result."},
  {"front": "Why does `cob.ldc(\"x\")` not compile in Kotlin?", "back": "Kotlin's `String` type doesn't show Java's `ConstantDesc` interface. Use `cob.ldc(cob.constantPool().stringEntry(\"x\"))`, or `loadConstant` for primitives."}
 ],
 "terms": [
  {"term": "Magic number", "plain": "The first four bytes of every class file, `0xCAFEBABE`."},
  {"term": "Major version", "plain": "The class-file version number; minus 44, it gives the Java version that wrote it."},
  {"term": "ClassFile API", "plain": "The JDK's own library for reading, writing and transforming class files, in `java.lang.classfile`, final in JDK 24."},
  {"term": "Model", "plain": "An immutable description of part of a class file (class, method, field, code), parsed lazily."},
  {"term": "Element", "plain": "One item in a model's sequence: a method of a class, or an instruction of a method's code."},
  {"term": "Transform", "plain": "A function that sees each element and passes it on, drops it, or replaces it while copying a class."},
  {"term": "ClassDesc", "plain": "A symbolic description of a class (from `java.lang.constant`) used when building, such as `ClassDesc.of(\"Fade\")`."}
 ],
 "explain_back": {
  "prompt": "Explain to a teammate why a hand-written constant-pool walk is fiddly, what the ClassFile API's model, builder and transform each give you, and why the API's arrival in JDK 24 matters for tools that write classes.",
  "answer": "A class file stores every name and constant in a numbered pool, and each entry's size depends on its tag. You must handle every tag, and `Long` and `Double` take two indexes, so one wrong count misreads everything after it. The ClassFile API does that walk for you. `parse` gives an immutable, lazily parsed model of the class, its methods and their code, which you can read as sequences of typed elements. `build` takes lambdas that receive builders with one method per instruction, and `verify` checks type safety before you load the result, though not whether it computes the right thing. `transformClass` copies a class while you decide, element by element, to pass it through, drop it or replace it. Before JDK 24 the JDK had no public library, so tools bundled ASM and needed a new release for each class-file version. The API always matches the JDK it runs on, and the JDK now builds its own proxies and lambdas with it."
 },
 "deeper": {
  "minutes": 10,
  "body": "Three details from the API's documentation and this track's runs.\n\nModels are lazy, and that can surprise you. `parse` reads little more than the header. A method's code is inflated when you ask for it, so a broken method can parse fine and fail with `IllegalArgumentException` later, when you iterate its elements. If you run untrusted or generated bytes through the API, iterate or `verify` them up front.\n\nThe ClassFile API and Byte Buddy work at different levels. Byte Buddy works with types and methods (extend this class, intercept those methods with that delegate), and it runs on JDK 8. The ClassFile API works with the class file itself (these instructions, that constant), and it needs JDK 24. Byte Buddy's README says that \"as of 1.17.0, support will extend to new Java versions unless previously unknown class file features are discovered. This is possible through Byte Buddy's support of the Class File API.\" So on a new JDK, Byte Buddy can lean on the JDK's own reader and writer.\n\n`ConstantPool` is an `Iterable<PoolEntry>`, not a collection, so Java needs `StreamSupport` to stream it, while Kotlin's `Iterable` extensions work on it directly:\n\n```java\n// JDK 24+: every Class entry a class references, with the API\nSet<String> names = StreamSupport.stream(ClassFile.of().parse(bytes).constantPool().spliterator(), false)\n        .filter(e -> e instanceof ClassEntry)\n        .map(e -> ((ClassEntry) e).asInternalName())\n        .collect(Collectors.toCollection(TreeSet::new));\n```\n\n```kotlin\n// JDK 24+: every Class entry a class references, with the API\nval names = ClassFile.of().parse(bytes).constantPool()\n    .filterIsInstance<ClassEntry>()\n    .map { it.asInternalName() }\n    .toSortedSet()\n```"
 },
 "sources": [
  {"title": "java.lang.classfile package (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/classfile/package-summary.html"},
  {"title": "JEP 484: Class-File API", "url": "https://openjdk.org/jeps/484"},
  {"title": "JVM Specification SE 25, chapter 4: The class File Format", "url": "https://docs.oracle.com/javase/specs/jvms/se25/html/jvms-4.html"},
  {"title": "ClassFile.java at jdk-25-ga (OpenJDK source)", "url": "https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/classfile/ClassFile.java"}
 ]
}
# spread the correct answers over the option positions
for q, idx in zip(L["quiz"], [1, 2, 3, 0, 2]):
    right = q["options"].pop(q["answer"])
    q["options"].insert(idx, right)
    q["answer"] = idx
out = ROOT / "content/lessons/cls-06.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
