import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/bytecode/src"
P = "java/workbench/bytecode/l06"
K = "kotlin/workbench/bytecode/l06"
PRE = "labs/bytecode/preview"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :bytecode:demo -Pmain=workbench.bytecode.l06."

KT_RUN = lambda name, jar: f"kotlinc bytecode/preview/{name}.kt -jvm-target 21 -include-runtime -d build/{jar}.jar && java -jar build/{jar}.jar"

# ---- figure: a transform maps each element to zero, one or more elements ----
ins = ["lload 0", "ldc 290L", "lmul", "ldc 10000L", "ldiv", "lreturn"]
outs = ["lload 0", "ldc 310L", "lmul", "ldc 10000L", "ldiv", "lreturn"]
parts = ['<svg viewBox="0 0 680 300" role="img" aria-label="A class transform drops the debugTrace method and keeps fee. Inside fee, a code transform passes every instruction through unchanged except ldc 290L, which it replaces with ldc 310L.">']
parts.append('<text class="t-s t-m" x="20" y="22">class elements of FeeRule</text>')
parts.append('<rect class="box" x="20" y="34" width="150" height="34" rx="8"/><text class="t-s t-code" x="95" y="56" text-anchor="middle">method fee</text>')
parts.append('<rect class="box-bad" x="190" y="34" width="170" height="34" rx="8"/><text class="t-s t-code" x="275" y="56" text-anchor="middle">method debugTrace</text>')
parts.append('<text class="t-s t-bad" x="470" y="56" text-anchor="middle">dropping(...): debugTrace removed</text>')
parts.append('<text class="t-s t-m" x="20" y="102">code elements of fee: before</text>')
for i, t in enumerate(ins):
    x = 20 + i * 108
    cls = "box-a" if i == 1 else "box"
    parts.append(f'<rect class="{cls}" x="{x}" y="114" width="100" height="34" rx="8"/><text class="t-s t-code" x="{x + 50}" y="136" text-anchor="middle">{t}</text>')
    parts.append(f'<line class="{"ln-a" if i == 1 else "ln-d"}" x1="{x + 50}" y1="148" x2="{x + 50}" y2="196" marker-end="url(#arr)"/>')
parts.append('<text class="t-s t-m" x="20" y="176">  </text>')
for i, t in enumerate(outs):
    x = 20 + i * 108
    cls = "box-ok" if i == 1 else "box"
    parts.append(f'<rect class="{cls}" x="{x}" y="200" width="100" height="34" rx="8"/><text class="t-s t-code" x="{x + 50}" y="222" text-anchor="middle">{t}</text>')
parts.append('<text class="t-s t-m" x="340" y="262" text-anchor="middle">each element: cob.with(element) passes it through, nothing drops it, other calls replace it</text>')
parts.append('<text class="t-s t-a" x="340" y="284" text-anchor="middle">ldc 290L was replaced; the other five passed through unchanged</text>')
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

L = {
 "id": "cls-06",
 "title": "Generating and transforming classes with the ClassFile API",
 "minutes": 35,
 "goal": "By the end you can read a class file's header and constant pool by hand, and with the ClassFile API (final in JDK 24) parse a class into a model, build a new class from builder lambdas, verify it before loading, and write a transform that drops or replaces elements.",
 "warmup": {
  "q": "You read the first eight bytes of `java/lang/Object.class` from the JDK you're running. They are `ca fe ba be 00 00 00 45`. Which JDK is it?",
  "options": ["JDK 21", "JDK 25", "JDK 8", "You can't tell from the bytes"],
  "answer": 1,
  "why": "After the magic number `CAFEBABE` come the minor version (`00 00`) and the major version (`00 45`, which is 69). From Java 5 on, the Java version is major minus 44, so 69 is Java 25. JDK 21's own classes say `00 41` (65), and Java 8 is `00 34` (52)."
 },
 "sections": [
  {
   "h": "A class file is a byte array with a fixed layout",
   "body": "Every tool in this track reads or writes the same format. That includes javap, the verifier, `Proxy`, `LambdaMetafactory`, Byte Buddy and agents. Here is the start of `java/lang/Object.class` on JDK 21, printed by this section's demo:\n\n```text\nca fe ba be  00 00  00 41  00 7c\nmagic        minor  major  constant_pool_count\n```\n\nThe magic number `0xCAFEBABE` marks a class file. The major version is 0x41, which is 65, and Java 21 wrote it. From Java 5 on, the Java version is the major version minus 44. Then comes `constant_pool_count`, and after it the constant pool itself, the table of names and constants from lesson 2. All numbers are big-endian. `DataInputStream` reads them, so the first fields take four lines:\n\n```java\nDataInputStream in = new DataInputStream(new ByteArrayInputStream(bytes));\nint magic = in.readInt();               // u4: 0xCAFEBABE\nint minor = in.readUnsignedShort();     // u2\nint major = in.readUnsignedShort();     // u2: 65 = Java 21, 69 = Java 25\nint poolCount = in.readUnsignedShort(); // u2: entries are numbered 1 .. poolCount - 1\n```\n\n```kotlin\nval input = DataInputStream(ByteArrayInputStream(bytes))\nval magic = input.readInt()                // u4: 0xCAFEBABE\nval minor = input.readUnsignedShort()      // u2\nval major = input.readUnsignedShort()      // u2: 65 = Java 21, 69 = Java 25\nval poolCount = input.readUnsignedShort()  // u2: entries are numbered 1 .. poolCount - 1\n```\n\nThe constant pool is harder. Each entry starts with a one-byte tag, and the tag decides how many bytes follow: a `Utf8` entry has a length, a `Class` entry has two bytes, a `Methodref` has four. A `Long` or `Double` entry takes two pool indexes, which is why lesson 2's pool had no entry 8. After the pool come the access flags, then `this_class`, an index that points at a `Class` entry, then the superclass, interfaces, fields, methods and attributes. In the lab you write this walk yourself and check it against a real class-file library.\n\nThat is the problem the ClassFile API solves. Any framework that generates or changes classes has to read and write this format exactly. The format also gains a major version with every JDK release, every six months, and sometimes new entry kinds or attributes. Until JDK 24 the JDK had no public library for it. Frameworks bundled ASM (Byte Buddy contains its own copy) and had to ship a new release for each new class-file version. The JDK carried a private copy of ASM too, and it's gone from the jdk-25-ga source tree.",
   "try": {
    "title": "Read three class-file headers",
    "minutes": 3,
    "steps": [
     "Before you run anything, predict the major version of `ClassFileHeader.class` (built by the labs), of `java.lang.Object` on the JDK you're using, and of `kotlin.Unit` in the Kotlin standard library.",
     "Run `ClassFileHeader`, then its Kotlin twin.",
     "If you have both JDK 21 and JDK 25 installed, run the Java version on each: `java -cp bytecode/build/classes/java/demo:bytecode/build/classes/kotlin/demo workbench.bytecode.l06.ClassFileHeader`."
    ],
    "code": {"lang": "java", "title": "ClassFileHeader.java", "src": read(f"{lab}/demo/{P}/ClassFileHeader.java"), "run": RUN + "ClassFileHeader", "file": f"{lab}/demo/{P}/ClassFileHeader.java",
             "alt": {"lang": "kotlin", "title": "ClassFileHeader.kt", "src": read(f"{lab}/demo/{K}/ClassFileHeader.kt"), "run": RUN + "ClassFileHeaderKt", "file": f"{lab}/demo/{K}/ClassFileHeader.kt"}},
    "expect": "Every line starts with `ca fe ba be`. The labs' own classes (Java and Kotlin) are `version=65.0 (Java 21)`, because the build uses `release 21` and `jvmTarget 21`. `java.lang.Object` is 65 on JDK 21 and 69 on JDK 25, so the same program reports the JDK it runs on. `kotlin.Unit` is `52.0 (Java 8)`: the standard library is compiled for Java 8, so it runs everywhere."
   },
   "refs": [
    {"title": "JVM Specification SE 25, chapter 4: The class File Format", "url": "https://docs.oracle.com/javase/specs/jvms/se25/html/jvms-4.html", "kind": "docs"}
   ]
  },
  {
   "h": "The ClassFile API parses bytes into an immutable model",
   "body": "The package `java.lang.classfile` is the JDK's own class-file library. It was a preview feature in JDK 22 (JEP 457) and JDK 23 (JEP 466), and became final in JDK 24 (JEP 484). The labs compile with `release 21`, so this lesson's ClassFile API code lives in single-file programs under `labs/bytecode/preview/`, which you run with `java File.java` on JDK 24 or later. On JDK 21 they fail with `package java.lang.classfile does not exist`.\n\nEverything starts at `ClassFile.of()`. Its `parse` method turns bytes into a `ClassModel`:\n\n```java\nClassModel cm = ClassFile.of().parse(bytes);\nSystem.out.println(cm.thisClass().asInternalName() + \" major \" + cm.majorVersion());\nfor (MethodModel m : cm.methods()) {\n    long invokes = m.code()\n            .map(code -> code.elementStream().filter(e -> e instanceof InvokeInstruction).count())\n            .orElse(0L);\n    System.out.println(m.methodName().stringValue() + m.methodType().stringValue() + \" invokes=\" + invokes);\n}\n```\n\n```kotlin\nval cm = ClassFile.of().parse(bytes)\nprintln(\"${cm.thisClass().asInternalName()} major ${cm.majorVersion()}\")\nfor (m in cm.methods()) {\n    val invokes = m.code()\n        .map { code -> code.elementStream().filter { it is InvokeInstruction }.count() }\n        .orElse(0L)\n    println(\"${m.methodName().stringValue()}${m.methodType().stringValue()} invokes=$invokes\")\n}\n```\n\nA model is an immutable description of one part of a class file. There are models for the class, each field, each method, and each method's code. The package documentation adds two properties. A `ClassModel` \"is inflated lazily; most parts of the classfile are not parsed until they are actually needed\". So a malformed method can parse fine and throw `IllegalArgumentException` only when you open it.\n\nEach model can also be read as a sequence of **elements**. A class's elements are its methods, fields and attributes. A method's code is a sequence of instructions, labels and other code elements. Each instruction is an object with a type you can match on, such as `InvokeInstruction`, `ConstantInstruction` or `InvokeDynamicInstruction`. The rest of the API is built on that: reading walks elements, building emits elements, and transforming maps elements to elements.\n\nNames and types come back as constant-pool entries (`methodName()` is a `Utf8Entry`, which is why the code calls `stringValue()`). When you build, you pass symbolic descriptions from `java.lang.constant`, such as `ClassDesc.of(\"FeeRule\")` and `MethodTypeDesc.of(CD_long, CD_long)`, and the library creates the entries.",
   "try": {
    "title": "Tour lesson 2's class with the ClassFile API",
    "minutes": 4,
    "steps": [
     "This needs JDK 24 or later. From `labs/`, make sure lesson 2's demo was built (`./gradlew :bytecode:demo -Pmain=workbench.bytecode.l02.StackDemo`), then run the command below. The Kotlin twin needs `kotlinc` running on JDK 24 or later.",
     "Compare the constant-pool counts with the `javap -v` listing you read in lesson 2.",
     "`describe` builds a string and calls nothing else, yet its count is 0. Before reading on: which instruction does it contain, and why didn't the filter count it?"
    ],
    "code": TOUR,
    "expect": "`workbench/bytecode/l02/StackDemo extends java/lang/Object, major 65`, a pool with `Utf8Entry=43`, `LongEntry=2` (10000 and 125000) and one `InvokeDynamicEntry`, then four methods: `<init>()V invokes=1`, `feeMinor(JI)J invokes=0`, `describe(...) invokes=0` and `main(...) invokes=3`. `describe` contains an `invokedynamic`, which the API models as `InvokeDynamicInstruction`, a separate type from `InvokeInstruction`."
   },
   "refs": [
    {"title": "java.lang.classfile package (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/classfile/package-summary.html", "kind": "docs"}
   ]
  },
  {
   "h": "Builders write a class from lambdas, and verify checks it before you load it",
   "body": "To generate a class you don't create builder objects yourself. You pass lambdas, and the library hands each one the builder for that level: a `ClassBuilder` for the class, a `CodeBuilder` for a method body. The `CodeBuilder` has one method per instruction, so a method body reads like the javap listings from lesson 2:\n\n```java\nbyte[] feeRule = ClassFile.of().build(ClassDesc.of(\"FeeRule\"), clb -> clb\n        .withFlags(ClassFile.ACC_PUBLIC | ClassFile.ACC_FINAL)\n        .withMethodBody(\"fee\", MethodTypeDesc.of(CD_long, CD_long), ClassFile.ACC_PUBLIC | ClassFile.ACC_STATIC,\n                cob -> cob\n                        .lload(0)          // the amount, slots 0 and 1\n                        .ldc(290L)         // basis points\n                        .lmul()\n                        .ldc(10_000L)\n                        .ldiv()\n                        .lreturn()));\nClass<?> c = MethodHandles.lookup().defineClass(feeRule);   // load it next to this class\n```\n\n```kotlin\nval feeRule = ClassFile.of().build(ClassDesc.of(\"FeeRule\")) { clb ->\n    clb.withFlags(ClassFile.ACC_PUBLIC or ClassFile.ACC_FINAL)\n    clb.withMethodBody(\"fee\", MethodTypeDesc.of(CD_long, CD_long), ClassFile.ACC_PUBLIC or ClassFile.ACC_STATIC) { cob ->\n        cob.lload(0)                       // the amount, slots 0 and 1\n            .loadConstant(290L)            // basis points (Kotlin: see below)\n            .lmul()\n            .loadConstant(10_000L)\n            .ldiv()\n            .lreturn()\n    }\n}\nval c = MethodHandles.lookup().defineClass(feeRule)            // load it next to this class\n```\n\n`fee(125000)` returns 3625, the fee you computed by hand in lesson 2. `MethodHandles.lookup().defineClass` loads the bytes as a class in the same package and loader as the calling class.\n\nThe builder writes what you tell it to, including nonsense. A method declared to return `int` that pushes a `String` builds without complaint. Lesson 1 showed what happens when you load such a class: `defineClass` can succeed and the `VerifyError` comes later. `ClassFile.of().verify(bytes)` runs the verifier's checks on the bytes before any of that, and returns a list of errors:\n\n```text\nverify(FeeRule): []\nverify(Broken):  [java.lang.VerifyError: Bad type on operand stack in Broken::answer() @2\n                  (integer_type is not assignable from java/lang/String)]\n```\n\nKotlin has one trap here. `ldc` takes a `java.lang.constant.ConstantDesc`, and Java's `String` and `Long` implement that interface. Kotlin's `String` and `Long` types don't show it, so `cob.ldc(\"forty-two\")` doesn't compile in Kotlin. Use `loadConstant(310L)`, which has overloads for primitives, or pass a constant-pool entry: `cob.ldc(cob.constantPool().stringEntry(\"forty-two\"))`.",
   "try": {
    "title": "Build, verify, then break it",
    "minutes": 4,
    "steps": [
     "On JDK 24 or later, run `ClassFileForge` from `labs/` (command below), or build and run the Kotlin twin.",
     "Read the first three lines: the size of the generated class, its verify result, the fee, and the verifier's message for `Broken`.",
     "In the `fee` body, delete the `.ldiv()` line and predict what `verify(feeRule)` reports. Run it again."
    ],
    "code": FORGE,
    "expect": "`built FeeRule: 197 bytes, verify errors []`, `FeeRule.fee(125000) = 3625`, and `verify(Broken): [java.lang.VerifyError: Bad type on operand stack in Broken::answer() @2 (integer_type is not assignable from java/lang/String)]`. Without `ldiv`, two longs are still on the stack at `lreturn`. That's legal for the verifier, which only checks the type on top, so `verify` reports no error and `fee(125000)` returns 10000 (the last value pushed). The verifier proves the code is type-safe, not that it's right."
   }
  },
  {
   "h": "A transform is a flatMap over elements",
   "body": "Changing an existing class is where the element model pays off. The package documentation puts it in one sentence: \"Transformation can be viewed as a 'flatMap' operation on the sequence of elements; for every element, we could pass it through unchanged, drop it, or replace it with one or more elements.\"\n\nA `ClassTransform` sees class elements, and a `CodeTransform` sees the instructions of one method. Inside a transform you hand each element to the builder: `builder.with(element)` passes it through, calling nothing drops it, and calling other builder methods replaces it. This one drops every `debug...` method and changes the rate constant in every method body:\n\n```java\nCodeTransform newRate = (cob, element) -> {\n    if (element instanceof ConstantInstruction ci && Long.valueOf(290L).equals(ci.constantValue())) {\n        cob.ldc(310L);            // replace\n    } else {\n        cob.with(element);        // pass through\n    }\n};\nClassTransform transform = ClassTransform\n        .dropping(e -> e instanceof MethodModel m && m.methodName().stringValue().startsWith(\"debug\"))\n        .andThen(ClassTransform.transformingMethodBodies(newRate));\nbyte[] v2 = cf.transformClass(cf.parse(feeRule), ClassDesc.of(\"FeeRuleV2\"), transform);\n```\n\n```kotlin\nval newRate = CodeTransform { cob, element ->\n    if (element is ConstantInstruction && element.constantValue().equals(290L)) {\n        cob.loadConstant(310L)    // replace\n    } else {\n        cob.with(element)         // pass through\n    }\n}\nval transform = ClassTransform\n    .dropping { it is MethodModel && it.methodName().stringValue().startsWith(\"debug\") }\n    .andThen(ClassTransform.transformingMethodBodies(newRate))\nval v2 = cf.transformClass(cf.parse(feeRule), ClassDesc.of(\"FeeRuleV2\"), transform)\n```\n\nThe result, `FeeRuleV2`, has only `fee`, and `fee(125000)` returns 3875. Everything the transform passed through is copied, and that's also the default: a transform that does nothing reproduces the class.\n\nThe JDK writes its own generated classes with this API. `ProxyGenerator` switched from the internal ASM to `java.lang.classfile` in JDK 23, and the lambda spinner `InnerClassLambdaMetafactory` in JDK 24. So the `$Proxy0` from lesson 4 and the `$$Lambda` classes from lesson 3 are built by the code you just ran.\n\nWho should use it? Tools that only need to run on JDK 24 and later can drop their ASM dependency, because the API always matches the JDK it runs on. Libraries that must support older JDKs can't do that. Byte Buddy, whose regular jar targets Java 8 and whose `-jdk5` jar targets Java 5, keeps its bundled ASM and bridges to the ClassFile API when it's there (release notes for 1.16.0: \"Include support for JDK Class File API\"). Lesson 7 runs transforms on classes that are already loaded, which is what agents do.",
   "figure": {"svg": FIG, "caption": "A transform walks the elements and decides, one at a time, to pass, drop or replace each one."},
   "try": {
    "title": "Write your own transform",
    "minutes": 4,
    "steps": [
     "Run `ClassFileForge` again and read the last line.",
     "Change the code transform so it also turns `10_000L` into `1_000L`, without touching the 290 branch. Predict the new `FeeRuleV2.fee(125000)` before you run it.",
     "Remove the `.andThen(...)` part, keeping only `dropping`. Which line of the output changes?"
    ],
    "code": FORGE,
    "expect": "Before your change: `FeeRuleV2 methods [fee], fee(125000) = 3875`. With both constants replaced: 125000 x 310 / 1000 = 38750. With only `dropping`, `FeeRuleV2` still loses `debugTrace`, but `fee` keeps the 290 constant and returns 3625 again."
   }
  }
 ],
 "analogy": "A class file is a filled-in form with a strict layout: boxes in a fixed order, a numbered glossary at the front (the constant pool), and every later box that needs a name writes a glossary number instead. Reading by hand means walking the glossary line by line, remembering that some entries take two lines. The ClassFile API is a clerk who reads the form into a folder of typed cards (models and elements), lets you hand back a new folder card by card (builders), and copies a form while you say \"keep, drop, or replace\" for each card (transforms). The analogy breaks at checking: a clerk would notice a nonsense answer. The builder writes whatever you hand it, and only `verify` asks whether the result is type-safe, never whether it's correct.",
 "in_your_world": "You meet the class-file format first in a deploy failure: `UnsupportedClassVersionError: ... class file version 69.0, this version of the Java Runtime only recognizes class file versions up to 65.0`. A library or a module was compiled for JDK 25 and your service image still runs JDK 21. Reading the header of every class in the jars (the lab's `header` does it) finds the culprit in a minute. Later you may write a build-time check that no class in the payments service references a banned class, such as `java.util.Random` in token generation. That check is the lab's `referencedClasses` over every class file, or twenty lines of ClassFile API code on JDK 25.",
 "mistake": "The common mistake is treating `verify` (or a class that loads) as proof the generated code is right. The verifier checks types and stack shapes: that `lreturn` finds a `long`, that a method returns what its descriptor promises. A builder that leaves an extra value on the stack, pushes the wrong constant or forgets a division can still pass, as the `ldiv` experiment showed. People make the mistake because a `VerifyError` feels like the compiler's error checking. The fix is to test generated classes like any code: load them, call them with known inputs, and assert the results, as the lab's tests do against an independent reader.",
 "compare": {
  "title": "Reading a class's name in Java and Kotlin, by hand and with the API",
  "java": {"title": "ThisClass.java", "src": "// by hand (any JDK): walk the pool, then read this_class\nstatic String thisClass(byte[] bytes) {\n    return ClassFileFacts.thisClass(bytes);          // the lab's DataInputStream walk\n}\n\n// with the ClassFile API (JDK 24+)\nstatic String thisClassWithApi(byte[] bytes) {\n    return ClassFile.of().parse(bytes).thisClass().asInternalName();\n}"},
  "kotlin": {"title": "ThisClass.kt", "src": "// by hand (any JDK): walk the pool, then read this_class\nfun thisClass(bytes: ByteArray): String =\n    ClassFileFacts.thisClass(bytes)                  // the lab's DataInputStream walk\n\n// with the ClassFile API (JDK 24+)\nfun thisClassWithApi(bytes: ByteArray): String =\n    ClassFile.of().parse(bytes).thisClass().asInternalName()"},
  "note": "Same bytes, same answer, and the API version is one line because the library does the pool walk for you, lazily. The language differences are small but real. Kotlin calls the API through ordinary SAM conversion for its `Consumer` and `CodeTransform` parameters, and uses `or` instead of `|` for access flags. Kotlin's mapped `String` and `Long` types don't expose Java's `ConstantDesc`, so `ldc(\"...\")` needs a constant-pool entry or `loadConstant` instead. Compiling Kotlin against the API also needs kotlinc to run on (or point `-jdk-home` at) JDK 24 or later, whatever `-jvm-target` you choose."
 },
 "worked": {
  "title": "Find the jar that broke the deploy",
  "steps": [
   {"say": "The payments service starts on JDK 21 and dies at once. Which part of the message tells you what to look for?", "code": "Error: LinkageError occurred while loading main class com.acme.fx.RateTable\n    java.lang.UnsupportedClassVersionError: com/acme/fx/RateTable has been compiled by a more\n    recent version of the Java Runtime (class file version 69.0), this version of the Java Runtime\n    only recognizes class file versions up to 65.0", "lang": "text"},
   {"say": "Class file version 69.0 is Java 25 (69 - 44). Something in the image was compiled for JDK 25. Here only one class is named, but a jar can mix versions, so check every class. Read each entry's header, with the lab's code.", "code": "try (JarFile jar = new JarFile(path.toFile())) {\n    jar.stream()\n       .filter(e -> e.getName().endsWith(\".class\"))\n       .forEach(e -> {\n           try (InputStream in = jar.getInputStream(e)) {\n               // 1. read magic, minor, major from the first 10 bytes\n               ClassFileFacts.Header h = ClassFileFacts.header(in.readNBytes(10));\n               // 2. report anything newer than the runtime\n               if (h.major() > 65) System.out.println(e.getName() + \" -> Java \" + ClassFileFacts.javaVersion(h.major()));\n           } catch (IOException ex) {\n               throw new UncheckedIOException(ex);\n           }\n       });\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "JarFile(path.toFile()).use { jar ->\n    jar.stream()\n        .filter { it.name.endsWith(\".class\") }\n        .forEach { e ->\n            // 1. read magic, minor, major from the first 10 bytes\n            val h = jar.getInputStream(e).use { ClassFileFacts.header(it.readNBytes(10)) }\n            // 2. report anything newer than the runtime\n            if (h.major() > 65) println(\"${e.name} -> Java ${ClassFileFacts.javaVersion(h.major())}\")\n        }\n}"},
   {"say": "Two caveats. A multi-release jar keeps newer classes under `META-INF/versions/25/`, and those are allowed: the JVM only loads them on JDK 25. So skip that prefix, or you'll get false alarms. And `module-info.class` has a version too. When the culprit is your own module, the fix is in the build: compile with `--release 21` (Gradle: `options.release.set(21)`) and `jvmTarget = 21` for Kotlin, as the labs do, so the compilers also refuse JDK 22+ APIs.", "code": "", "lang": ""}
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
   "Write a private pool walk: for `i` from 1 to `count - 1`, read the tag and either keep the value (`readUTF()` for tag 1, the name index for tag 7) or skip the right number of bytes. After a tag 5 or 6, add one to `i`.",
   "Write `referencedClasses` with the walk: the Utf8 string at each Class entry's name index. Write `thisClass`: after the walk, read `access_flags`, then `this_class`, and look up its name.",
   "Run the tests until all seven pass. The expected answers come from ASM, so a pass means your reader agrees with a production library on Java, Kotlin and JDK classes."
  ],
  "hints": [
   "A wrong byte count anywhere in the walk shifts everything after it, so the symptom is usually `unknown constant pool tag` far from the bug. Check the table entry for the last tag you handled.",
   "`DataInputStream.readUTF()` reads a two-byte length and then the bytes in the class file's own \"modified UTF-8\". That's exactly a Utf8 entry, so you don't decode anything yourself.",
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
  "A class file starts with `CAFEBABE`, minor and major version (Java version = major - 44 from Java 5 on: 65 is 21, 69 is 25), then the constant pool.",
  "Pool entries start with a tag that fixes their size; `Long` and `Double` take two indexes. `this_class` comes right after the pool and the access flags.",
  "The ClassFile API (`java.lang.classfile`) was preview in JDK 22 and 23 and became final in JDK 24 (JEP 484). Labs on `release 21` can't use it, so its code runs as JDK 25 single-file programs.",
  "`ClassFile.of().parse` gives a lazy, immutable `ClassModel`; models are also sequences of elements, such as methods or instructions.",
  "`build` takes builder lambdas, `verify` checks type safety before loading (not correctness), and `transformClass` maps elements: pass with `with`, drop by doing nothing, or replace.",
  "The JDK builds proxies (since 23) and lambdas (since 24) with it. Libraries that support old JDKs, like Byte Buddy, keep their own ASM and bridge to it."
 ],
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
    "`readUTF` throws immediately",
    "Only the long's value is wrong"
   ],
   "answer": 1,
   "why": "You skipped the right number of bytes, but the numbering is off by one. Every later entry gets an index one too small, so a `Class` entry's name index points at the wrong string, and the loop expects one more entry than the file has, so it reads the access flags as if they were a tag. The symptom is far from the cause, usually an unknown tag or garbage names. That's why the lab's `Fixture` has both a `long` and a `double`."
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
   "why": "Verification checks types and stack shapes, not meaning. A fee method with a missing `ldiv` still verifies and returns the wrong number. A class verified today can also fail to load on an older JDK because of its version number."
  },
  {
   "q": "You want a build-time check, running on JDK 25, that fails if any class in your service references `java/util/Random`. Which tool fits best?",
   "options": [
    "A JDK dynamic proxy around every class",
    "`ClassFile.of().parse(bytes)` over every class file, checking the class entries in each constant pool",
    "A Java agent that retransforms every loaded class",
    "`Class.forName` on every class with initialization"
   ],
   "answer": 1,
   "why": "Every class a class mentions has a `Class` entry in its constant pool, so parsing the files is enough. No class needs to be loaded, initialized or run. Proxies intercept calls at run time, agents change loaded classes, and `Class.forName` runs static initializers, which is the last thing a build check should do."
  },
  {
   "q": "From *Reading bytecode*: javap shows `#7 = Long 10000l` and then `#9 = InvokeDynamic ...`, with no entry 8. Why?",
   "options": [
    "javap hides unused entries",
    "Entry 8 was optimized away by the JIT",
    "A `Long` (and a `Double`) entry takes two constant-pool indexes, so 8 is the second half of 7",
    "Entry 8 is reserved for the class's own name"
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
  {"front": "Why does `cob.ldc(\"x\")` not compile in Kotlin?", "back": "Kotlin's `String` type doesn't expose Java's `ConstantDesc` interface. Use `cob.ldc(cob.constantPool().stringEntry(\"x\"))` or `loadConstant` for primitives."}
 ],
 "terms": [
  {"term": "Magic number", "plain": "The first four bytes of every class file, `0xCAFEBABE`."},
  {"term": "Major version", "plain": "The class-file version number; minus 44 it gives the Java version that wrote it."},
  {"term": "ClassFile API", "plain": "The JDK's own library for reading, writing and transforming class files, in `java.lang.classfile`, final in JDK 24."},
  {"term": "Model", "plain": "An immutable description of part of a class file (class, method, field, code), parsed lazily."},
  {"term": "Element", "plain": "One item in a model's sequence: a method of a class, or an instruction of a method's code."},
  {"term": "Transform", "plain": "A function that sees each element and passes it on, drops it, or replaces it while copying a class."},
  {"term": "ClassDesc", "plain": "A symbolic description of a class (from `java.lang.constant`) used when building, such as `ClassDesc.of(\"FeeRule\")`."}
 ],
 "explain_back": {
  "prompt": "Explain to a teammate why a hand-written constant-pool walk is fiddly, what the ClassFile API's model, builder and transform each give you, and why the API's arrival in JDK 24 matters for frameworks.",
  "answer": "A class file stores every name and constant in a numbered pool, and each entry's size depends on its tag. You must handle every tag, and `Long` and `Double` take two indexes, so one wrong count misreads everything after it. The ClassFile API does that walk for you. `parse` gives an immutable, lazily parsed model of the class, its methods and their code, which you can read as sequences of typed elements. `build` takes lambdas that receive builders with one method per instruction, and `verify` checks type safety before you load the result. `transformClass` copies a class while you decide, element by element, to pass it through, drop it or replace it. Before JDK 24 the JDK had no public library, so frameworks bundled ASM and needed a new release for each class-file version. The API always matches the JDK it runs on, and the JDK now builds its own proxies and lambdas with it."
 },
 "deeper": {
  "minutes": 10,
  "body": "Three details from the API's documentation and this track's runs.\n\nModels are lazy, and that can surprise you. `parse` reads little more than the header. A method's code is inflated when you ask for it, so a malformed method can parse fine and fail with `IllegalArgumentException` later, when you iterate its elements. If you run untrusted or generated bytes through the API, iterate or `verify` them up front.\n\nThe ClassFile API and Byte Buddy are complements. Byte Buddy works at the level of types and methods (subclass this, intercept those methods with that delegate), and it runs on JDK 8. The ClassFile API works at the level of the class file (these instructions, that constant), and it needs JDK 24. Byte Buddy's README says that \"as of 1.17.0, support will extend to new Java versions unless previously unknown class file features are discovered. This is possible through Byte Buddy's support of the Class File API.\" So on a new JDK, Byte Buddy can lean on the JDK's own reader and writer.\n\n`ConstantPool` is `Iterable<PoolEntry>`, not a collection, so Java needs `StreamSupport` to stream it, while Kotlin's `Iterable` extensions work directly:\n\n```java\n// JDK 24+: every Class entry a class references, with the API\nSet<String> names = StreamSupport.stream(ClassFile.of().parse(bytes).constantPool().spliterator(), false)\n        .filter(e -> e instanceof ClassEntry)\n        .map(e -> ((ClassEntry) e).asInternalName())\n        .collect(Collectors.toCollection(TreeSet::new));\n```\n\n```kotlin\n// JDK 24+: every Class entry a class references, with the API\nval names = ClassFile.of().parse(bytes).constantPool()\n    .filterIsInstance<ClassEntry>()\n    .map { it.asInternalName() }\n    .toSortedSet()\n```"
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
