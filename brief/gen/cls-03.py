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


FIG = """<svg viewBox="0 0 680 280" role="img" aria-label="The first time an invokedynamic instruction runs, the JVM calls its bootstrap method with the static arguments. LambdaMetafactory spins a hidden class and returns a ConstantCallSite. Every later run calls the call site's target directly.">
<rect class="box-a" x="20" y="30" width="230" height="56" rx="8"/>
<text class="t-s t-code" x="135" y="54" text-anchor="middle">invokedynamic #2</text>
<text class="t-s t-code" x="135" y="74" text-anchor="middle">applyAsInt:()IntBinaryOperator</text>
<rect class="box" x="300" y="20" width="360" height="76" rx="8"/>
<text class="t-s" x="480" y="42" text-anchor="middle">bootstrap method (runs once)</text>
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
<text class="t-s" x="135" y="217" text-anchor="middle">call site linked for good</text>
<line class="ln" x1="300" y1="212" x2="254" y2="212" marker-end="url(#arr)"/>
<line class="ln-d" x1="135" y1="86" x2="135" y2="186" marker-end="url(#arr)"/>
<text class="t-s t-m" x="190" y="140" text-anchor="middle">every later run:</text>
<text class="t-s t-m" x="190" y="158" text-anchor="middle">call the target</text>
<text class="t-s t-m" x="340" y="264" text-anchor="middle">the target returns the lambda object: the same one if nothing is captured</text>
</svg>"""

L = {
 "id": "cls-03",
 "title": "invokedynamic: how lambdas and string concatenation compile",
 "minutes": 35,
 "goal": "By the end you can read an invokedynamic call site and its bootstrap method in javap, say what a lambda captures and when it allocates, and build a lambda and a concatenation by hand with LambdaMetafactory and StringConcatFactory.",
 "warmup": {
  "q": "`static Supplier<String> greeter() { return () -> \"hello\"; }`. What does `greeter() == greeter()` print on a current JDK?",
  "options": [
   "`false`: every lambda expression creates a new object",
   "`true`: the lambda captures nothing, so its call site hands back one shared object",
   "It doesn't compile: you can't compare lambdas with `==`",
   "`true`, but only after the JIT has compiled `greeter`"
  ],
  "answer": 1,
  "why": "The lambda is an `invokedynamic` call site. The first time it runs, `LambdaMetafactory` links it, and for a lambda that captures nothing the linked target returns the same instance every time. It prints `true` from the first call, in the interpreter. A capturing lambda such as `x -> x + fee` gets a new object per evaluation."
 },
 "sections": [
  {
   "h": "An invokedynamic call site is linked once, by library code",
   "body": "Every other invoke instruction names its target: `invokestatic StackDemo.feeMinor:(JI)J` calls exactly that method. `invokedynamic` names only a method name, a type, and a **bootstrap method** that will decide the target. Here is the method reference `IndyTour::add` in `javap -c -p`, and the matching entry from `javap -v`:\n\n```text\ninvokedynamic #15, 0   // InvokeDynamic #2:applyAsInt:()Ljava/util/function/IntBinaryOperator;\n\nBootstrapMethods:\n  2: REF_invokeStatic java/lang/invoke/LambdaMetafactory.metafactory:(...)Ljava/lang/invoke/CallSite;\n    Method arguments:\n      (II)I\n      REF_invokeStatic workbench/bytecode/l03/IndyTour.add:(II)I\n      (II)I\n```\n\nThe type `()IntBinaryOperator` says what this instruction does for the code around it: take nothing off the stack and push an `IntBinaryOperator`. How it gets one is not in your class file.\n\nThe first time the instruction runs, the JVM calls the bootstrap method with a `Lookup` for your class (an object that carries your class's access rights), the name, the type and the static arguments listed above. The bootstrap method returns a `CallSite`, an object holding a target `MethodHandle` of exactly that type. A method handle is a typed reference to a method that the JVM can call directly, much like a function pointer. The JVM links the instruction to it. From then on, every execution calls the target directly, and the bootstrap method never runs again for that call site.\n\n`LambdaMetafactory` and `StringConcatFactory` both return a `ConstantCallSite`, whose target can never change, so the JIT can inline straight through it. `MutableCallSite` exists for language runtimes that need to relink later.\n\n`invokedynamic` arrived in Java 7 for other JVM languages, and javac first used it for lambdas in Java 8. The design moves the strategy out of your class files and into the JDK. The bytecode says \"concatenate a `long` and a `String` with this recipe\". How that's done is decided by the JDK you run on, so a newer JDK can do it better without you recompiling.",
   "try": {
    "title": "Relink a call site by hand",
    "minutes": 3,
    "steps": [
     "Read `CallSiteDemo`. It builds a `MutableCallSite`, calls through its `dynamicInvoker()`, changes the target, and calls again.",
     "Predict the three lines it prints, then run it (or the Kotlin twin)."
    ],
    "code": demo("CallSiteDemo", "CallSiteDemo"),
    "expect": "`linked to eur: 3625.50 EUR`, then `relinked to usd: $3625.50` through the very same invoker, then a line saying `ConstantCallSite.setTarget` threw `UnsupportedOperationException`. An `invokedynamic` instruction calls through its call site the way the invoker does. Lambdas get the constant kind, linked for good."
   },
   "refs": [
    {"title": "java.lang.invoke package (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/invoke/package-summary.html", "kind": "docs"}
   ]
  },
  {
   "h": "A lambda is a hidden class that LambdaMetafactory spins at first use",
   "body": "javac turns a lambda into two things: a private method holding the body, and an `invokedynamic` that produces the object.\n\n```java\nstatic IntUnaryOperator plus(int fee) { return x -> x + fee; }\n```\n\n```kotlin\nfun plus(fee: Int): (Int) -> Int = { x -> x + fee }\n```\n\n```text\njavac:   invokedynamic #1:applyAsInt:(I)Ljava/util/function/IntUnaryOperator;\n         private static int lambda$plus$1(int, int)          // (fee, x): captures first\n         bootstrap args: (I)I, lambda$plus$1:(II)I, (I)I\n\nkotlinc: invokedynamic #1:invoke:(I)Lkotlin/jvm/functions/Function1;\n         private static final int plus$lambda$0(int, int)\n         bootstrap args: (Ljava/lang/Object;)Ljava/lang/Object;, plus$lambda$0:(II)I,\n                         (Ljava/lang/Integer;)Ljava/lang/Integer;\n```\n\nRead the call site type as a factory: `(I)IntUnaryOperator` means \"give me the captured `int`, and I'll give you an operator\". The body method takes the captured values first, then the lambda's own parameters. The three static arguments are the interface method's erased type, the body, and the interface method's type as this lambda uses it. Kotlin's `Function1.invoke` is erased to `(Object)Object`, so the third argument, `(Integer)Integer`, tells the metafactory to insert boxing and casts.\n\nAt link time `LambdaMetafactory` generates a class named like `IndyTour$$Lambda/0x00000007c0000a08`. It's a **hidden class**, defined with `Lookup.defineHiddenClass` as a nestmate of `IndyTour`: a class allowed to use `IndyTour`'s private members, which is how it may call the private body. `Class.forName` on its name throws `ClassNotFoundException`. Since JDK 24 the JDK writes these classes with the ClassFile API from lesson 6.\n\nThe demo shows the allocation rule. A lambda that captures nothing is linked to a single shared instance, so `greeter() == greeter()` is `true`. A capturing lambda gets a new object each time the expression is evaluated, but every object shares one class. That's one small allocation per evaluation, not per call of the lambda.\n\nKotlin compiles lambdas the same way, which has been the default since Kotlin 2.0. The release notes list what you give up: such a lambda isn't serializable, and its `toString()` is less readable. Function references differ. In the demo, `::addMinor` stored as `(Int, Int) -> Int` compiled to an ordinary generated class, `IndyTourKt$main$ref$1`, and `isHidden` is `false`.",
   "figure": {"svg": FIG, "caption": "The bootstrap method runs once per call site. After linking, the instruction calls the target directly."},
   "try": {
    "title": "Tour the lambdas",
    "minutes": 5,
    "steps": [
     "Run `IndyTour`, then `IndyTourKt`. Compare the class names they print.",
     "From `labs/`, run `javap -c -p bytecode/build/classes/java/demo/workbench/bytecode/l03/IndyTour.class | grep -E 'invokedynamic|lambda'` and match each `invokedynamic` to a line of source.",
     "Do the same for `bytecode/build/classes/kotlin/demo/workbench/bytecode/l03/IndyTourKt.class`, and run `ls` on that folder. Which Kotlin construct got a class file of its own?"
    ],
    "code": demo("IndyTour", "IndyTour"),
    "expect": "Java: `IndyTour$$Lambda/0x...`, `hidden: true`, a nestmate of `IndyTour`, `Class.forName` fails, `same object both times? true` for `greeter`, and `same object? false, same class? true` for `plus`. Kotlin: the lambdas print `IndyTourKt$$Lambda/0x...` and `hidden: true`, but the function reference prints `IndyTourKt$main$ref$1` and `hidden: false`. It's the `IndyTourKt$main$ref$1.class` file in the folder. Both programs also contain several `makeConcatWithConstants` call sites, one per string they build."
   },
   "refs": [
    {"title": "LambdaMetafactory (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/invoke/LambdaMetafactory.html", "kind": "docs"},
    {"title": "What's new in Kotlin 2.0.0: lambdas via invokedynamic", "url": "https://kotlinlang.org/docs/whatsnew20.html", "kind": "read"}
   ]
  },
  {
   "h": "String concatenation, records and switches go through bootstrap methods too",
   "body": "Since JDK 9 (JEP 280), javac compiles `+` on strings to one `invokedynamic` per expression, linked by `StringConcatFactory.makeConcatWithConstants`. The constant parts travel as a recipe string, with `\\u0001` marking each argument:\n\n```java\n\"concat: \" + fee.amountMinor() + \" \" + fee.currency() + \", record: \" + fee\n```\n\n```kotlin\n\"template: ${fee.amountMinor} ${fee.currency}, data class: $fee\"\n```\n\n```text\ninvokedynamic makeConcatWithConstants:(JLjava/lang/String;Ljava/lang/String;)Ljava/lang/String;\nrecipe: concat: \\u0001 \\u0001, record: \\u0001\n```\n\nThe call site type lists the dynamic values in order. Here javac first turned the record into a `String` with `String.valueOf`, and kotlinc passed the data class object as is. Kotlin templates compile the same way when the JVM target is 9 or newer, which is what the labs use. With kotlinc's command-line default of Java 8, the same template becomes a `StringBuilder` chain.\n\nRecords push the idea further. A record's `toString`, `hashCode` and `equals` are each two instructions and an `invokedynamic`. The bootstrap is `java.lang.runtime.ObjectMethods.bootstrap` (JDK 16), and its static arguments describe the record:\n\n```text\nObjectMethods.bootstrap\n  Method arguments:\n    workbench/bytecode/l03/IndyTour$Fee\n    currency;amountMinor\n    REF_getField IndyTour$Fee.currency:Ljava/lang/String;\n    REF_getField IndyTour$Fee.amountMinor:J\n```\n\nThe JDK builds the three methods from that description at first use. A Kotlin `data class` takes the other road: kotlinc writes the `toString` body itself, `getfield currency`, `getfield amountMinor`, then a concatenation `invokedynamic`. Both print the same kind of text. The record carries a description, while the data class carries finished code.\n\nPattern-matching `switch` over a sealed type compiles to `invokedynamic typeSwitch` with `java.lang.runtime.SwitchBootstraps`. javac 21 also emits the constant form, **condy** (`CONSTANT_Dynamic`), for enum case labels in such a switch. A condy entry is a constant whose value a bootstrap method computes on first use, through `ConstantBootstraps`. Same idea, for values instead of calls.",
   "try": {
    "title": "A record and a data class, side by side",
    "minutes": 4,
    "steps": [
     "From `labs/` (after running `IndyTour` and `IndyTourKt` once), run the two `javap` commands below.",
     "In the record, find which bootstrap method its `toString` uses and the string that lists its components.",
     "In the data class, find the recipe that `toString` passes to `makeConcatWithConstants`."
    ],
    "code": {"lang": "bash", "title": "terminal", "src": "javap -v 'bytecode/build/classes/java/demo/workbench/bytecode/l03/IndyTour$Fee.class' | grep -A6 BootstrapMethods\njavap -v bytecode/build/classes/kotlin/demo/workbench/bytecode/l03/KFee.class | grep -A3 BootstrapMethods", "run": ""},
    "expect": "The record's `toString`, `hashCode` and `equals` all use bootstrap 0, `ObjectMethods.bootstrap`, with the arguments `IndyTour$Fee`, `currency;amountMinor` and two `REF_getField` handles. The data class has only a `StringConcatFactory.makeConcatWithConstants` bootstrap, with a recipe like `KFee(currency=\\u0001, amountMinor=\\u0001)`. Its `hashCode` and `equals` are plain bytecode that kotlinc wrote."
   },
   "refs": [
    {"title": "JEP 280: Indify String Concatenation", "url": "https://openjdk.org/jeps/280", "kind": "read"}
   ]
  },
  {
   "h": "You can call the bootstrap methods yourself",
   "body": "A bootstrap method is a public static method, so your code can call it too. That is today's lab. `LambdaMetafactory.metafactory` takes six arguments, and `javap -v` already showed you all of them:\n\n```java\nCallSite site = LambdaMetafactory.metafactory(\n        lookup,                                 // 1. caller: must be able to see the body\n        \"get\",                                  // 2. interface method name\n        methodType(Supplier.class),             // 3. factory type: captured values -> interface\n        methodType(Object.class),               // 4. interface method type, erased\n        lookup.findStatic(ByHandDemo.class, \"banner\", methodType(String.class)),  // 5. body\n        methodType(String.class));              // 6. interface method type as this lambda uses it\nSupplier<String> s = (Supplier<String>) site.getTarget().invoke();\n```\n\n```kotlin\nval site = LambdaMetafactory.metafactory(\n    lookup,                                     // 1. caller: must be able to see the body\n    \"get\",                                      // 2. interface method name\n    methodType(Supplier::class.java),           // 3. factory type: captured values -> interface\n    methodType(Any::class.java),                // 4. interface method type, erased\n    lookup.findStatic(Banners::class.java, \"banner\", methodType(String::class.java)),  // 5. body\n    methodType(String::class.java),             // 6. interface method type as this lambda uses it\n)\nval s = site.target.invoke() as Supplier<String>\n```\n\nThe JVM supplies arguments 1 to 3 from the call site; the static arguments are 4 to 6. `getTarget()` is the factory. Calling it runs what the `invokedynamic` instruction would run on every execution: it takes the captured values and returns a lambda object. For a non-capturing lambda, call it once and keep the result. For a capturing one, keep the factory and call it once per object, which is the shape the lab tests for. The generated class is a nestmate of the lookup's class, so the hidden class in the demo is named `ByHandDemo$$Lambda`.\n\n`StringConcatFactory.makeConcatWithConstants(lookup, name, type, recipe)` works the same way and returns a call site whose target formats the arguments.\n\nWhy do this outside a lab? You rarely need to. Code that has a `Method` in hand at run time, such as a serializer or a router, can turn it into an interface instance once and then call it at the speed of a lambda, instead of paying for `Method.invoke` on every call. Lesson 4 measures that cost against a JDK proxy.",
   "try": {
    "title": "One lambda and one concatenation, by hand",
    "minutes": 3,
    "steps": [
     "Read `ByHandDemo`. Match each of the six `metafactory` arguments to the `javap -v` listing in section 1.",
     "Run it (or the Kotlin twin) and read the class and call-site names it prints."
    ],
    "code": demo("ByHandDemo", "ByHandDemo"),
    "expect": "`settlement batch 42  <- ...ByHandDemo$$Lambda/0x..., call site: ConstantCallSite` and `batch 42 has 1250 payments  <- call site: ConstantCallSite`. The lambda class is hidden and named after the lookup's class, exactly like a javac lambda. The Kotlin twin prints `ByHandDemoKt$$Lambda`."
   }
  }
 ],
 "analogy": "An invokedynamic call site is a phone extension that isn't wired to anyone yet. The first time anyone dials it, the switchboard (the bootstrap method) reads the note taped to the phone, which is the static arguments, decides who should answer, and wires the extension straight to that desk. Every later call rings the desk directly, and the switchboard never hears about it again. For a lambda that captures nothing, the desk always hands back the same printed form. For one that captures, it fills in a fresh copy each time. The analogy breaks because real wiring can be redone at will; a lambda's call site is a `ConstantCallSite`, wired once for the life of the class.",
 "in_your_world": "In a Kafka consumer, `batch.forEach(p -> ledger.post(p.id(), convert(p, rate)))` creates one small `Consumer` per poll, capturing `this` and `rate`, and calls it once per record. That's nothing to worry about. A lambda created inside a per-record inner loop allocates per record, and only then is it worth a look. The same reading helps with framework code: Quarkus and Hibernate stack traces are full of `$$Lambda` frames, and those are hidden classes linked by `LambdaMetafactory`, not classes you can find on the class path. And if a library jar was built with an old Kotlin JVM target, its string templates are `StringBuilder` chains rather than `invokedynamic`. `javap -v` tells you which in five seconds.",
 "mistake": "The common mistake is guessing what a lambda costs instead of reading what it captures. People avoid lambdas in hot paths because \"each lambda allocates\". Then they miss the real allocation: a lambda that reads a field captures `this`, so it allocates on every evaluation, even though it looks like it captures nothing. The fix is to check the call site type in `javap -c -p`. `()Ljava/util/function/Supplier;` captures nothing and is a shared instance. `(LFxPoster;J)Ljava/util/function/Consumer;` captures `this` and a `long`, so it's a new object each time the expression runs. Then measure (the performance track shows how) before rewriting anything.",
 "compare": {
  "title": "Lambdas and function references in Java and Kotlin",
  "java": {"title": "Fees.java", "src": "static int add(int a, int b) { return a + b; }\n\nIntBinaryOperator ref = Fees::add;            // invokedynamic -> hidden Fees$$Lambda\nIntUnaryOperator plus30 = x -> x + 30;        // invokedynamic, body in lambda$main$0\nint fee = 45;\nIntUnaryOperator plusFee = x -> x + fee;      // invokedynamic with type (I)IntUnaryOperator\n\nString line = \"fee \" + fee + \" EUR\";         // invokedynamic makeConcatWithConstants"},
  "kotlin": {"title": "Fees.kt", "src": "fun add(a: Int, b: Int) = a + b\n\nval ref: (Int, Int) -> Int = ::add            // a generated class (FeesKt$main$ref$1 style)\nval plus30: (Int) -> Int = { x -> x + 30 }    // invokedynamic -> hidden FeesKt$$Lambda\nval fee = 45\nval plusFee: (Int) -> Int = { x -> x + fee }  // invokedynamic with type (I)Function1\n\nval line = \"fee $fee EUR\"                     // invokedynamic makeConcatWithConstants (target 9+)"},
  "note": "Both compilers send lambdas through `LambdaMetafactory`, so both get hidden `$$Lambda` classes, shared instances when nothing is captured, and one class per lambda expression. Two real differences show up in javap. Kotlin's function types are generic interfaces (`Function1<P, R>`), so an `(Int) -> Int` boxes its `Int` through `invoke(Object): Object`, while Java's `IntUnaryOperator` stays primitive. And in this track's kotlinc 2.4.21 run, a function reference such as `::add` assigned to a function type compiled to an ordinary generated class instead of an `invokedynamic`. Kotlin's `inline` functions such as `forEach` and `map` avoid the lambda object entirely, which Java can't do."
 },
 "worked": {
  "title": "What does this consumer's lambda capture?",
  "steps": [
   {"say": "A settlement consumer converts each payment with an FX rate and posts it. Before reading on: does the lambda capture anything, and how often does it allocate?", "code": "class FxPoster {\n    private final Ledger ledger;\n\n    void handle(List<Payment> batch, long rateMicros) {\n        batch.forEach(p -> ledger.post(p.id(), p.amountMinor() * rateMicros / 1_000_000));\n    }\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "class KFxPoster(private val ledger: KLedger) {\n    fun handle(batch: List<KPayment>, rateMicros: Long) {\n        batch.forEach { p -> ledger.post(p.id, p.amountMinor * rateMicros / 1_000_000) }\n    }\n}"},
   {"say": "Ask javap. The Java call site type is the list of captured values: `this` (because `ledger` is a field, read through `this`) and the `long` rate. The body became an instance method for the same reason.", "code": "// 1. the factory: takes FxPoster and long, returns a Consumer\ninvokedynamic #0:accept:(LFxPoster;J)Ljava/util/function/Consumer;\n// 2. the body: an instance method, the captured long first, then the element\nprivate void lambda$handle$0(long, FxPoster$Payment);", "lang": "text"},
   {"say": "So Java allocates one `Consumer` per call to `handle`, once per batch and not once per payment, and calls it once per element. The Kotlin version compiles to no lambda at all: `forEach` is an `inline` function, so kotlinc pasted the loop into `handle`. Its bytecode is `Iterable.iterator`, `hasNext`, `next` and a direct `KLedger.post`. Store the same lambda in a `val` first and Kotlin does what Java does:", "code": "val post: (KPayment) -> Unit = { p -> ledger.post(p.id, p.amountMinor * rateMicros / 1_000_000) }\nbatch.forEach(post)\n// 3. invokedynamic #0:invoke:(LKFxPoster;J)Lkotlin/jvm/functions/Function1;\n//    private static final kotlin.Unit handleBoxed$lambda$0(KFxPoster, long, KPayment)", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "Consumer<Payment> post = p -> ledger.post(p.id(), p.amountMinor() * rateMicros / 1_000_000);\nbatch.forEach(post);\n// 3. same call site as before: invokedynamic accept:(LFxPoster;J)Ljava/util/function/Consumer;\n//    Java has no inline functions, so a lambda passed to forEach is always an object"},
   {"say": "The verdict: one small object per batch is noise next to a 120 ms ledger call, so leave the code as it is. The habit worth keeping is reading the call site type. When it starts with your class, the lambda holds `this`, which also keeps that object reachable for as long as the lambda lives.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Build three lambdas and a concatenation by hand",
  "minutes": 14,
  "files": ["labs/bytecode/src/main/java/workbench/bytecode/l03/HandMadeLambdas.java"],
  "run": "./gradlew :bytecode:test --tests 'workbench.bytecode.l03.*'",
  "steps": [
   "Run the tests once. All six fail with `UnsupportedOperationException`.",
   "Add `private static final MethodHandles.Lookup LOOKUP = MethodHandles.lookup();`. Write `adder()` with `LambdaMetafactory.metafactory`: name `applyAsInt`, factory type `()IntBinaryOperator`, both interface types `(II)I`, and `LOOKUP.findStatic(HandMadeLambdas.class, \"addMinor\", ...)`. Invoke the factory once, store the object in a static field, and return it every time.",
   "Write `plusFee(int)`. The factory type is `(int)IntUnaryOperator`, the interface types are `(I)I`, and the body is `addFee`, whose first parameter receives the captured fee. Store the factory handle (`site.getTarget()`), not an object, and call `(IntUnaryOperator) factory.invokeExact(feeMinor)` on each call.",
   "Write `lengthOf()` with `LOOKUP.findVirtual(String.class, \"length\", methodType(int.class))`. The erased type is `(Object)Object`, and the instantiated type is `(String)Integer`.",
   "Write `receipt()` with `StringConcatFactory.makeConcatWithConstants(LOOKUP, \"receipt\", methodType(String.class, long.class, String.class), \"paid \\u0001 to \\u0001\")` and return the call site's target.",
   "Run the tests until all six pass."
  ],
  "hints": [
   "Bootstrap methods throw checked exceptions. Wrap them once in a small helper that rethrows as `ExceptionInInitializerError` or `IllegalStateException`. Mind the order of your static fields: lesson 1's rule applies.",
   "`LambdaConversionException: Type mismatch` usually means the instantiated type (the sixth argument) doesn't match the body's parameters after the captured ones. For `plusFee` the body is `(int, int)int`, and the lambda's own part is `(int)int`.",
   "`invokeExact` needs the exact static type: cast the result to `IntUnaryOperator` and pass an `int`. `invoke` is more forgiving if you get stuck."
  ],
  "done_when": "All six tests in `HandMadeLambdasTest` pass."
 },
 "drill": {
  "title": "Spell out a metafactory call",
  "minutes": 5,
  "prompt": "Close the page. Write the code that turns a static method `static String banner()` into a `Supplier<String>` with `LambdaMetafactory.metafactory`, without a lambda or method reference. Label the six arguments. Then say which arguments the JVM supplies and which come from the BootstrapMethods table.",
  "answer": {
   "lang": "java",
   "src": "MethodHandles.Lookup lookup = MethodHandles.lookup();\nCallSite site = LambdaMetafactory.metafactory(\n        lookup,                                   // 1. caller (JVM supplies it)\n        \"get\",                                    // 2. interface method name (JVM, from the call site)\n        methodType(Supplier.class),               // 3. factory type (JVM, from the call site)\n        methodType(Object.class),                 // 4. erased interface type (static argument)\n        lookup.findStatic(Owner.class, \"banner\", methodType(String.class)),  // 5. body (static argument)\n        methodType(String.class));                // 6. instantiated type (static argument)\n@SuppressWarnings(\"unchecked\")\nSupplier<String> s = (Supplier<String>) site.getTarget().invoke();",
   "alt": {"lang": "kotlin", "src": "val lookup = MethodHandles.lookup()\nval site = LambdaMetafactory.metafactory(\n    lookup,                                       // 1. caller (JVM supplies it)\n    \"get\",                                        // 2. interface method name (JVM, from the call site)\n    methodType(Supplier::class.java),             // 3. factory type (JVM, from the call site)\n    methodType(Any::class.java),                  // 4. erased interface type (static argument)\n    lookup.findStatic(Owner::class.java, \"banner\", methodType(String::class.java)),  // 5. body\n    methodType(String::class.java),               // 6. instantiated type (static argument)\n)\n@Suppress(\"UNCHECKED_CAST\")\nval s = site.target.invoke() as Supplier<String>"}
  }
 },
 "recap": [
  "`invokedynamic` names a method name, a type and a bootstrap method. The bootstrap method runs once per call site and returns a `CallSite`; afterwards the instruction calls its target directly.",
  "A lambda is a private body method plus an `invokedynamic`. The call site type lists the captured values, and `LambdaMetafactory` spins a hidden `$$Lambda` class at first use.",
  "Capturing nothing gives one shared instance; capturing gives a new object per evaluation, all of one class. Reading a field captures `this`.",
  "String `+` and Kotlin templates (JVM target 9+) use `StringConcatFactory.makeConcatWithConstants` with a `\\u0001` recipe. Records use `ObjectMethods.bootstrap`; pattern switches use `SwitchBootstraps`, and enum labels in them use condy.",
  "Kotlin lambdas use `invokedynamic` by default since Kotlin 2.0, `inline` functions such as `forEach` create no lambda at all, and a function reference became a generated class in this track's run.",
  "Bootstrap methods are public: `LambdaMetafactory.metafactory` takes caller, name, factory type, erased type, body and instantiated type."
 ],
 "quiz": [
  {
   "q": "`IntUnaryOperator plus(int fee) { return x -> x + fee; }` is called 1,000 times with 1,000 different fees. How many lambda classes and objects are created?",
   "options": ["1,000 classes and 1,000 objects", "One class and 1,000 objects", "One class and one object", "No classes: lambdas are compiled into the enclosing class"],
   "answer": 1,
   "why": "One lambda expression is one call site, linked once, so `LambdaMetafactory` spins one hidden class. The lambda captures `fee`, so each evaluation calls the factory and gets a new object. The shared single instance only happens when nothing is captured."
  },
  {
   "q": "javap shows `invokedynamic #0:apply:(Lcom/acme/RateService;)Ljava/util/function/Function;` for a lambda inside `RateService`. What does it tell you?",
   "options": [
    "The lambda takes a `RateService` as its argument",
    "The lambda captures `this` (a `RateService`), so each evaluation creates a new object that keeps the service reachable",
    "The lambda is a method reference to a static method",
    "The lambda was compiled by kotlinc"
   ],
   "answer": 1,
   "why": "The call site type is the factory: its parameters are the captured values and it returns the interface. A leading `RateService` means the lambda captured `this`, usually because its body reads a field or calls an instance method. The lambda's own parameter types are in the bootstrap arguments, not in this type."
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
   "why": "kotlinc 2.4.21 without `-jvm-target` writes class-file version 52 (Java 8), and `StringConcatFactory` only exists from JDK 9. With target 9 or newer (the labs use 21), templates compile to `makeConcatWithConstants`."
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
  {"front": "When does an invokedynamic's bootstrap method run?", "back": "Once per call site, the first time the instruction executes. It returns a `CallSite`, and later executions call its target directly."},
  {"front": "What does the call site type `(I)Ljava/util/function/IntUnaryOperator;` on a lambda mean?", "back": "The lambda captures one `int`. The call site is a factory: give it the int, get an `IntUnaryOperator`."},
  {"front": "`() -> \"hello\"` is evaluated twice. Same object?", "back": "Yes. A non-capturing lambda's call site returns one shared instance."},
  {"front": "What kind of class is `Foo$$Lambda/0x...`, and can `Class.forName` find it?", "back": "A hidden class defined by `LambdaMetafactory` as a nestmate of `Foo`. `Class.forName` throws `ClassNotFoundException`."},
  {"front": "What is `\\u0001` in a `makeConcatWithConstants` recipe?", "back": "A slot for the next dynamic argument. `\"paid \\u0001 to \\u0001\"` takes two values."},
  {"front": "Which bootstrap builds a record's toString, equals and hashCode?", "back": "`java.lang.runtime.ObjectMethods.bootstrap` (JDK 16), given the record class, the component names and getter handles."},
  {"front": "Does Kotlin's `list.forEach { ... }` create a lambda object?", "back": "No. `forEach` is `inline`, so kotlinc copies the loop and the lambda body into the caller."}
 ],
 "terms": [
  {"term": "invokedynamic", "plain": "A call instruction whose target a bootstrap method chooses the first time it runs."},
  {"term": "Bootstrap method", "plain": "A static method, named in the BootstrapMethods table, that links an invokedynamic call site and returns a CallSite."},
  {"term": "CallSite", "plain": "An object holding the method handle an invokedynamic calls. ConstantCallSite can't be relinked; MutableCallSite can."},
  {"term": "LambdaMetafactory", "plain": "The JDK bootstrap method that turns a lambda's body method into an object implementing a functional interface."},
  {"term": "Hidden class", "plain": "A class defined with `Lookup.defineHiddenClass` (JDK 15) that no class loader can find by name."},
  {"term": "Capture", "plain": "Values from the surrounding scope that a lambda stores, such as a local variable or `this`."},
  {"term": "Condy", "plain": "`CONSTANT_Dynamic`: a constant-pool entry whose value a bootstrap method computes on first use."}
 ],
 "explain_back": {
  "prompt": "Explain to a teammate what happens, from javac to the first call, when Java code says `IntUnaryOperator plus = x -> x + fee;`, and why the second time the line runs is cheaper than the first.",
  "answer": "javac moves the body into a private static method, `lambda$...$0(int fee, int x)`, with the captured `fee` first. Where the lambda appears, it emits an `invokedynamic` whose type is `(I)IntUnaryOperator`, plus a BootstrapMethods entry pointing at `LambdaMetafactory.metafactory` with the erased interface type, the body and the instantiated type. The first time the line runs, the JVM calls the metafactory, which spins a hidden `$$Lambda` class that implements `applyAsInt` by calling the body, and returns a `ConstantCallSite` whose target constructs that class. The JVM links the instruction to it. The second time, there's no bootstrap and no class generation: the instruction calls the target, which allocates one object holding `fee`. If the lambda captured nothing, it would just return the same instance."
 },
 "deeper": {
  "minutes": 10,
  "body": "Condy is easy to see. Compile this with javac 21 and run `javap -v`:\n\n```java\nsealed interface Shape permits Circle, Square {}\nrecord Circle(int r) implements Shape {}\nenum Square implements Shape { UNIT }\n\nstatic String name(Shape s) {\n    return switch (s) {\n        case Circle c -> \"circle \" + c.r();\n        case Square.UNIT -> \"unit square\";\n    };\n}\n```\n\n```kotlin\n// kotlinc compiles this `when` to an instanceof check and an enum comparison: no typeSwitch\nsealed interface Shape\ndata class Circle(val r: Int) : Shape\nenum class Square : Shape { UNIT }\n\nfun name(s: Shape) = when (s) {\n    is Circle -> \"circle ${s.r}\"\n    Square.UNIT -> \"unit square\"\n}\n```\n\nThe `switch` becomes `invokedynamic typeSwitch:(Ljava/lang/Object;I)I` with `SwitchBootstraps.typeSwitch`. Among its static arguments is a `Dynamic` constant-pool entry, shown as `invoke:Ljava/lang/Enum$EnumDesc;`, whose own bootstrap is `ConstantBootstraps.invoke` applied to `Enum$EnumDesc.of`. The enum label is built lazily, the first time the switch needs it, instead of forcing `Square` to initialize when the class loads.\n\nThe lambda spinner changed tools recently. At jdk-23-ga, `InnerClassLambdaMetafactory` imports the JDK's internal copy of ASM; at jdk-24-ga it imports `java.lang.classfile`. Your class files didn't change at all. That's the point of `invokedynamic`: the JDK swapped its strategy underneath, and every lambda compiled since Java 8 picked it up."
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
