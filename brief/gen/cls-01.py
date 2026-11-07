import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/bytecode/src"
P = "java/workbench/bytecode/l01"
K = "kotlin/workbench/bytecode/l01"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :bytecode:demo -Pmain=workbench.bytecode.l01."


def demo(java, kt, title=None):
    """Try-it code object for a Java demo and its Kotlin twin (FooKt)."""
    return {"lang": "java", "title": f"{java}.java", "src": read(f"{lab}/demo/{P}/{java}.java"),
            "run": RUN + java, "file": f"{lab}/demo/{P}/{java}.java",
            "alt": {"lang": "kotlin", "title": f"{kt}.kt", "src": read(f"{lab}/demo/{K}/{kt}.kt"),
                    "run": RUN + kt + "Kt", "file": f"{lab}/demo/{K}/{kt}.kt"}}


FIG = """<svg viewBox="0 0 680 270" role="img" aria-label="Three phases: loading, then linking (verify, prepare, resolve), then initialization, which runs the static initializer. Constant reads, X.class, arrays and forName with false stop before initialization; new, static calls, non-constant static reads, reflection and subclass initialization trigger it.">
<rect class="box" x="20" y="40" width="170" height="90" rx="8"/>
<text class="t" x="105" y="68" text-anchor="middle">Loading</text>
<text class="t-s t-m" x="105" y="92" text-anchor="middle">find the bytes</text>
<text class="t-s t-code" x="105" y="112" text-anchor="middle">defineClass</text>
<line class="ln" x1="190" y1="85" x2="216" y2="85" marker-end="url(#arr)"/>
<rect class="box-a" x="220" y="40" width="250" height="90" rx="8"/>
<text class="t" x="345" y="62" text-anchor="middle">Linking</text>
<rect class="box" x="230" y="76" width="72" height="40" rx="8"/>
<text class="t-s" x="266" y="101" text-anchor="middle">verify</text>
<rect class="box" x="309" y="76" width="72" height="40" rx="8"/>
<text class="t-s" x="345" y="101" text-anchor="middle">prepare</text>
<rect class="box" x="388" y="76" width="72" height="40" rx="8"/>
<text class="t-s" x="424" y="101" text-anchor="middle">resolve</text>
<line class="ln" x1="470" y1="85" x2="496" y2="85" marker-end="url(#arr)"/>
<rect class="box-ok" x="500" y="40" width="160" height="90" rx="8"/>
<text class="t" x="580" y="68" text-anchor="middle">Initialization</text>
<text class="t-s t-code" x="580" y="92" text-anchor="middle">runs &lt;clinit&gt;</text>
<text class="t-s t-m" x="580" y="112" text-anchor="middle">once, under a lock</text>
<text class="t-s t-m" x="345" y="148" text-anchor="middle">statics exist, set to 0 / false / null</text>
<rect class="box-dim" x="20" y="166" width="450" height="38" rx="8"/>
<text class="t-s" x="245" y="190" text-anchor="middle">constants, X.class, new X[3], forName(n, false, l): stop before init</text>
<line class="ln-d" x1="345" y1="166" x2="345" y2="156"/>
<rect class="box-b" x="190" y="218" width="470" height="38" rx="8"/>
<text class="t-s" x="425" y="242" text-anchor="middle">new X(), static call, non-constant static read, reflection, subclass</text>
<line class="ln-a" x1="580" y1="218" x2="580" y2="134" marker-end="url(#arr)"/>
</svg>"""

L = {
 "id": "cls-01",
 "title": "Class loading: loaders, delegation, linking and initialization",
 "minutes": 35,
 "goal": "By the end you can say which loader defines a class and why, predict exactly when a static initializer runs, and read a NoClassDefFoundError or a class that \"cannot be cast to\" itself for what it really means.",
 "warmup": {
  "q": "`Limits` has `static final int MAX_MINOR = 500_000;`, `static final Integer CAP = 500_000;` and a `static {}` block that prints \"init\". Another class prints `Limits.MAX_MINOR`, then `Limits.CAP`. When does \"init\" appear?",
  "options": [
   "Before the first value, because touching any member of a class initializes it",
   "Between the two values: reading `MAX_MINOR` doesn't initialize `Limits`, reading `CAP` does",
   "Never, because both fields are `static final`",
   "Twice, once per field"
  ],
  "answer": 1,
  "why": "`MAX_MINOR` is a constant variable: a `static final` primitive with a constant initializer. javac copies `500000` into the caller's class file, so the caller never touches `Limits` at run time. `CAP` is boxed (`Integer.valueOf` runs), so it is not a constant, and reading it runs `Limits`'s static initializer. A class initializes at most once, so \"init\" can't print twice."
 },
 "sections": [
  {
   "h": "Every class has a defining loader, and it is part of the class's identity",
   "body": "Ask three classes who loaded them and you get three different answers:\n\n```java\nSystem.out.println(String.class.getClassLoader());              // null\nSystem.out.println(java.sql.Connection.class.getClassLoader());  // ...ClassLoaders$PlatformClassLoader@<hash>\nSystem.out.println(PaymentApp.class.getClassLoader());          // ...ClassLoaders$AppClassLoader@<hash>\n```\n\n```kotlin\nprintln(String::class.java.classLoader)                // null\nprintln(java.sql.Connection::class.java.classLoader)   // ...ClassLoaders$PlatformClassLoader@<hash>\nprintln(PaymentApp::class.java.classLoader)            // ...ClassLoaders$AppClassLoader@<hash>\n```\n\nThe JDK has three built-in class loaders. The bootstrap loader is part of the JVM and loads `java.base`; the `ClassLoader` Javadoc says it is \"typically represented as `null`\". The platform loader loads the other Java SE and JDK modules, such as `java.sql` and `java.net.http`. The app loader (also called the system loader) loads your class path: your code, Quarkus, the Kafka client, the Kotlin standard library. Each one has the next as its parent: app, then platform, then bootstrap. JDK 21 and JDK 25 print the same chain.\n\nWhen code asks a loader for a class, the default `loadClass` does three things in order. It checks whether this loader already has the name (`findLoadedClass`). If not, it asks its parent, which asks its own parent first. Only when every parent fails does it call its own `findClass`. So `java.lang.String` always comes from the bootstrap loader, even if some jar on your class path contains a class with that name. This is **parent-first delegation**. It's why a stray jar can't replace a JDK class.\n\nThe loader that finally calls `defineClass` is the class's defining loader, and it is part of the class's identity. At run time a class is the pair (binary name, defining loader). Two loaders that each define `com.acme.Money` from the same bytes produce two classes that happen to share a name. You'll build exactly that in the lab, and section 4 shows what it does to a cast.\n\nKotlin adds nothing special here. `kotlin.Unit` is an ordinary class in an ordinary jar, so the app loader defines it like any other library class.",
   "try": {
    "title": "Who loaded what",
    "minutes": 3,
    "steps": [
     "Before you run it, write down the loader and module you expect for `String`, `java.sql.Connection`, the demo class itself and `kotlin.Unit`.",
     "Run `LoaderTour` from `labs/` with the command below, then run the Kotlin twin.",
     "Compare the two \"classes loaded so far\" numbers. Why might they differ?"
    ],
    "code": demo("LoaderTour", "LoaderTour"),
    "expect": "`String` has the bootstrap loader (printed as `null`, shown here as bootstrap) in `java.base`, `java.sql.Connection` has the platform loader in `java.sql`, and both the demo class and `kotlin.Unit` have the app loader in the unnamed module (`module=null`). The chain is `app -> platform -> bootstrap`. Both programs report roughly a thousand loaded classes; the Kotlin one loads a few more because it touches more of the standard library."
   },
   "refs": [
    {"title": "ClassLoader (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/ClassLoader.html", "kind": "docs"}
   ]
  },
  {
   "h": "Loading, linking and initialization are three steps, and only the last runs your code",
   "body": "Loading a class and running its `static {}` block are separate events. Chapter 5 of the JVM specification splits the work into three phases, and HotSpot runs each one as late as it is allowed to.\n\n1. Loading finds the bytes (in a jar, a directory, or generated in memory) and turns them into a `Class` object with `defineClass`.\n2. Linking checks and prepares the class. Verification proves the bytecode is type-safe. Preparation creates the static fields and sets them to their defaults: `0`, `false`, `null`. Resolution turns symbolic references in the constant pool (\"method `charge` in class `Ledger`\") into direct ones, and may do it lazily, one reference at a time.\n3. Initialization runs the class's static initializer, which javac names `<clinit>`: every static field initializer and `static {}` block, in source order.\n\nTwo small experiments show the gaps between the phases. A generated class with broken bytecode was accepted by `ClassLoader.defineClass` on JDK 25, and the `VerifyError` appeared only when code first asked for its methods. A class that referenced a deleted `Helper` class loaded and ran fine. It failed with `NoClassDefFoundError` only when the branch that used `Helper` executed.\n\nInitialization is the phase your code can see, and its triggers are precise. JLS section 12.4.1 lists them: creating an instance, calling a static method, assigning a static field, or reading a static field that is not a **constant variable**. Initializing a class first initializes its superclass. Reflection such as `Class.forName(name)` or a reflective static field read counts too.\n\nThese do not initialize a class:\n\n- reading a `static final` primitive or `String` that has a constant initializer, because javac copied the value into your class file;\n- `Limits.class`, `new Limits[3]` and `Class.forName(name, false, loader)`;\n- reading an inherited static field through a subclass name: `Child.parentValue` initializes only `Parent`, the class that declares the field.\n\nThe constant rule surprises people most. `static final int MAX_MINOR = 500_000` is a constant variable. `static final Integer CAP = 500_000` is not, because boxing calls `Integer.valueOf`. Reading the first leaves `Limits` alone. Reading the second runs `<clinit>`. Kotlin draws the same line between `const val` and a plain `val`.",
   "figure": {"svg": FIG, "caption": "A class can be loaded and linked long before it is initialized. Only the triggers in the bottom box run its static initializer."},
   "try": {
    "title": "The initialization puzzle",
    "minutes": 5,
    "steps": [
     "Read `InitPuzzle` (or `InitPuzzle.kt`). For each of the eight steps, write down whether a `<clinit>` line prints after it, and which one.",
     "Run it and check your list.",
     "Change `CAP` to `static final int CAP = 500_000;` (in Kotlin, make it `const val`). Predict step 4, then run again."
    ],
    "code": demo("InitPuzzle", "InitPuzzle"),
    "expect": "Step 1 prints only `Parent.<clinit>`: the field belongs to `Parent`. Step 2 prints only `Child.<clinit>`, because `Parent` is already done. Step 4 prints `Limits.<clinit>`, step 8 prints `Lazy.<clinit>`, and steps 3, 5, 6 and 7 print nothing. After the change, step 4 prints nothing too and `Limits` is never initialized at all. The Kotlin twin shows the same pattern with `KParent`, `KChild`, `KLimits` and `KLazy`."
   },
   "refs": [
    {"title": "JVM Specification SE 25, chapter 5: Loading, Linking, and Initializing", "url": "https://docs.oracle.com/javase/specs/jvms/se25/html/jvms-5.html", "kind": "docs"},
    {"title": "JLS SE 25, section 12.4.1: When initialization occurs", "url": "https://docs.oracle.com/javase/specs/jls/se25/html/jls-12.html#jls-12.4.1", "kind": "docs"}
   ]
  },
  {
   "h": "A static initializer runs once, top to bottom, under a lock",
   "body": "`<clinit>` is ordinary code, with three properties that cause real outages.\n\nIt runs in source order. In this class the constructor runs before the line that sets `DEFAULT_BPS`:\n\n```java\npublic final class FeeSchedule {\n    public static final FeeSchedule INSTANCE = new FeeSchedule();   // runs first\n    private static final int DEFAULT_BPS =\n            Integer.parseInt(System.getProperty(\"fees.default.bps\", \"350\"));\n\n    private final int fallbackBps = DEFAULT_BPS;                   // still 0 here\n}\n```\n\n```kotlin\nclass FeeSchedule private constructor() {\n    val fallbackBps = DEFAULT_BPS                                 // still 0 here\n\n    companion object {\n        @JvmField val INSTANCE = FeeSchedule()                    // runs first\n        private val DEFAULT_BPS = System.getProperty(\"fees.default.bps\", \"350\").toInt()\n    }\n}\n```\n\nThe thread running `<clinit>` may read the class's statics while it is still running, so the constructor sees the default `0`. Every unknown country now pays a 0 bps fee, and nothing throws. The JVM did exactly what the source says. With a constant initializer (`= 350`) the bug disappears, because javac inlines it. That's why this bug tends to arrive the day someone makes a constant configurable. The lab has it for you to fix.\n\nIt runs once, and a failure is permanent. If `<clinit>` throws, the first caller gets `ExceptionInInitializerError`. The JVM marks the class as failed, and every later use from any thread gets `NoClassDefFoundError: Could not initialize class ...`. It never retries. On JDK 21 the cause of that second error even names the original exception and the thread it happened in. In a long log you often see the `NoClassDefFoundError` hundreds of times and the real cause once, near the top.\n\nIt runs under a lock. One thread runs `<clinit>` and every other thread that needs the class waits. That lock is what makes the holder idiom from the memory model track safe, and it can deadlock. If `FxRates`'s initializer reads `Fees`, `Fees`'s initializer reads `FxRates`, and two threads start one each, each thread holds one class's lock and waits for the other's. The threads report `RUNNABLE`, not `BLOCKED`. `ThreadMXBean.findDeadlockedThreads()` returns nothing, and `jstack` prints `waiting on the Class initialization monitor for ...` with no \"Found one Java-level deadlock\" section. Search thread dumps for that phrase when a service hangs at startup.\n\nKeep static initializers boring. Constants and small immutable maps are fine. File reads, network calls and reads of other classes' statics belong in a lazy method or in a bean that the container starts.",
   "try": {
    "title": "Deadlock two classes",
    "minutes": 4,
    "steps": [
     "Run `InitDeadlockDemo` (or the Kotlin twin). It starts two threads and waits one second.",
     "Read the state and top frame it prints for each thread, and what the deadlock detector says.",
     "Optional: run it with `-Pargs=wait`, then run the printed `jstack` command in a second terminal and search for `Class initialization monitor`.",
     "Fix it: make `Fees.CARD_BPS` a constant (`static final long CARD_BPS = 108;`, or `const val` in Kotlin) and run again."
    ],
    "code": demo("InitDeadlockDemo", "InitDeadlockDemo"),
    "expect": "Both threads show `state=RUNNABLE` with a top frame inside `<clinit>`, and the detector prints `found nothing`. The JVM exits only because the threads are daemons. In `jstack` each thread is `in Object.wait()` and `waiting on the Class initialization monitor for` the other class. After the fix, `Fees` no longer needs `FxRates`, so both threads print a number and the program ends normally."
   }
  },
  {
   "h": "Same bytes, two loaders: two classes",
   "body": "Because the loader is part of a class's identity, a custom loader can define its own copy of a class the app loader already has. Plugin systems, application servers and Quarkus dev mode do this on purpose. The usual tool is a child-first loader: for its own package prefix it calls `findClass` before it asks the parent.\n\n```java\n@Override\nprotected Class<?> loadClass(String name, boolean resolve) throws ClassNotFoundException {\n    synchronized (getClassLoadingLock(name)) {\n        Class<?> c = findLoadedClass(name);\n        if (c == null && name.startsWith(prefix)) c = findClass(name);   // child-first\n        return c != null ? c : super.loadClass(name, resolve);            // parent-first\n    }\n}\n```\n\n```kotlin\noverride fun loadClass(name: String, resolve: Boolean): Class<*> =\n    synchronized(getClassLoadingLock(name)) {\n        var c = findLoadedClass(name)\n        if (c == null && name.startsWith(prefix)) c = findClass(name)   // child-first\n        c ?: super.loadClass(name, resolve)                              // parent-first\n    }\n```\n\nTwo such loaders over one class file give you two `Class` objects. Each has its own statics, and its static initializer runs once per loader. An object from one copy can't be cast to the other, even though the names match. The message is long, and worth learning to read:\n\n```text\nclass ...TwoLoadersDemo$Counter cannot be cast to class ...TwoLoadersDemo$Counter\n(...$Counter is in unnamed module of loader 'plugin-1' @606d8acf;\n ...$Counter is in unnamed module of loader 'app')\n```\n\nThe same name twice with two loaders means isolation, not a missing jar. The Quarkus class-loading reference describes where you'll meet it: tests and dev mode use several loaders. Your application classes live in a Runtime ClassLoader that is recreated on every hot reload, on top of a Base Runtime ClassLoader that persists. The guide warns that marking a dependency \"parent first\" without also marking its dependencies can cause a `LinkageError`. (That comes from the Quarkus docs; this track didn't run dev mode.)\n\nThe two \"not found\" errors fit the same picture. `ClassNotFoundException` is a checked exception from an explicit lookup by name, such as `Class.forName` or `loadClass`. `NoClassDefFoundError` comes from the JVM while it links or initializes code that was compiled against the class: either the class is missing at run time (the cause is then a `ClassNotFoundException`), or its static initializer already failed.\n\nLeaks have the same shape. A loader stays alive while anything reachable points at one of its classes or objects. In one experiment, a plugin instance added to a static list in a parent-loaded registry kept its whole `URLClassLoader` alive after `close()` and ten `System.gc()` calls, along with a 10 MB static array. Without the registration, the loader was collected. A persistent cache that holds an object from the previous Runtime ClassLoader pins every class of that old copy in the same way.",
   "try": {
    "title": "Two Counters that aren't the same class",
    "minutes": 4,
    "steps": [
     "Read `TwoLoadersDemo`. It loads `Counter` through two child-first loaders and calls `hit()` twice on the copy from `plugin-1`.",
     "Predict the three `hits` values and whether the cast at the end works.",
     "Run it (or the Kotlin twin) and find the two loader names in the exception message."
    ],
    "code": demo("TwoLoadersDemo", "TwoLoadersDemo"),
    "expect": "`same name: true`, `c1 == c2: false` and `c1 == Counter.class: false`. The hits are `plugin-1=2, plugin-2=0, app=0`: three classes, three separate static fields. The cast fails with `... cannot be cast to class ...$Counter`, and the parentheses name loader `'plugin-1'` and loader `'app'`."
   },
   "refs": [
    {"title": "Quarkus: Class loading reference", "url": "https://quarkus.io/guides/class-loading-reference", "kind": "read"}
   ]
  }
 ],
 "analogy": "A class name is like an account number, and the defining loader is the bank. Account 4471 at two banks is two accounts with two balances, and a transfer form for one bank rejects the other bank's account even though the numbers match. Parent-first delegation is a branch that always asks head office whether it already holds the account before it opens a new one, so nobody can open a second \"java.lang.String\". The analogy breaks in one place: two copies of a class are not strangers. They come from the same bytes and share everything their parent loaded, such as `String` and the interfaces they implement, which is why a plugin can still be used through a shared interface.",
 "in_your_world": "Picture an FX service that loads its rate table in a static initializer: `static final RateTable RATES = RateTable.load(Path.of(\"rates.csv\"))`. In a Quarkus test run the file isn't on the test path. The first test fails with `ExceptionInInitializerError`, and the next forty fail with `NoClassDefFoundError: Could not initialize class RateTable`, which sends people looking for a missing dependency. The same class under Quarkus dev mode is defined again by a fresh Runtime ClassLoader on every reload, so a static cache in a parent-first library that keeps old `RateTable` objects pins the old classes in memory. Load data in a bean that the container starts, and keep statics to constants.",
 "mistake": "The common mistake is reading `NoClassDefFoundError` as \"a jar is missing\" and adding dependencies until it goes away. Often the jar is fine: the class's static initializer threw once, earlier, and the JVM now refuses that class for the life of its loader. People make this mistake because the later error is the one that fills the log, and its name sounds like a class-path problem. The fix is to search the log for the first `ExceptionInInitializerError` (or read the cause of the `NoClassDefFoundError` on JDK 21 and later), fix what threw, and move I/O and configuration out of static initializers into lazy or container-managed code.",
 "compare": {
  "title": "When static initialization runs, in Java and Kotlin",
  "java": {"title": "Limits.java", "src": "class Limits {\n    static final int MAX_MINOR = 500_000;   // constant: copied into callers, no init\n    static final Integer CAP = 500_000;     // not a constant: reading it runs <clinit>\n    static Limits defaults() { return new Limits(); }\n\n    static { System.out.println(\"Limits init\"); }\n}\n\n// Limits.MAX_MINOR   -> nothing\n// Limits.CAP         -> \"Limits init\"\n// Limits.defaults()  -> \"Limits init\" (if not done yet)"},
  "kotlin": {"title": "Limits.kt", "src": "object Limits {\n    const val MAX_MINOR = 500_000           // constant: copied into callers, no init\n    val CAP: Int = 500_000                  // private static field + getCAP() on the object\n    fun defaults() = Limits\n\n    init { println(\"Limits init\") }\n}\n\n// Limits.MAX_MINOR   -> nothing\n// Limits.CAP         -> \"Limits init\" (goes through Limits.INSTANCE)\n// Limits.defaults()  -> \"Limits init\" (if not done yet)"},
  "note": "Kotlin has no `static`, but an `object` compiles to a class with a `public static final INSTANCE` field and a static initializer that builds it, so the JVM rules are the same. Only `const val` (primitives and `String`) is inlined into callers like a Java constant variable. A plain `val` in an object becomes a private static field plus a getter, so reading it touches the class and runs its `init` blocks. Companion objects follow the same rules, and their `init` code lands in the outer class's `static {}` block, which is why the Kotlin `FeeSchedule` in section 3 reads 0 exactly like the Java one."
 },
 "worked": {
  "title": "Read a NoClassDefFoundError back to its cause",
  "steps": [
   {"say": "A Quarkus test run shows this, forty times. Before reading on, decide: is a jar missing?", "code": "java.lang.NoClassDefFoundError: Could not initialize class com.acme.fx.RateTable\n    at com.acme.fx.QuoteService.quote(QuoteService.java:31)\n    ...\nCaused by: java.lang.ExceptionInInitializerError: Exception java.lang.IllegalStateException:\n    rates file missing: rates.csv [in thread \"executor-thread-1\"]", "lang": "text"},
   {"say": "No. \"Could not initialize class\" means the JVM found `RateTable` and already tried to initialize it. The cause (JDK 21 and later) points at the first failure. Here is the class. Each chunk of `<clinit>` runs once, in order.", "code": "public final class RateTable {\n    // 1. runs inside <clinit>: any exception here poisons the class for good\n    static final RateTable CURRENT = load(Path.of(\"rates.csv\"));\n\n    static RateTable load(Path p) {\n        if (!Files.exists(p)) throw new IllegalStateException(\"rates file missing: \" + p);\n        return new RateTable(/* parse 4,000 lines */);\n    }\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "class RateTable private constructor() {\n    companion object {\n        // 1. runs inside RateTable's <clinit>: any exception here poisons the class for good\n        val CURRENT: RateTable = load(Path.of(\"rates.csv\"))\n\n        fun load(p: Path): RateTable {\n            check(Files.exists(p)) { \"rates file missing: $p\" }\n            return RateTable(/* parse 4,000 lines */)\n        }\n    }\n}"},
   {"say": "Move the I/O out of class initialization. A bean the container builds at startup fails once, with a clear stack trace, and a fixed file or a restart of the test fixes it. The class itself has no static state left to poison.", "code": "@ApplicationScoped\npublic class RateTableProvider {\n    private volatile RateTable current;\n\n    @PostConstruct\n    void load() {                                   // 2. ordinary code, ordinary exception\n        current = RateTable.load(Path.of(\"rates.csv\"));\n    }\n\n    public RateTable current() { return current; }  // 3. no static state left to poison\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "@ApplicationScoped\nclass RateTableProvider {\n    @Volatile private lateinit var current: RateTable\n\n    @PostConstruct\n    fun load() {                                    // 2. ordinary code, ordinary exception\n        current = RateTable.load(Path.of(\"rates.csv\"))\n    }\n\n    fun current(): RateTable = current              // 3. no static state left to poison\n}"},
   {"say": "If the value must stay static, make it lazy with a holder class (memory model track, lesson 5). A failure still poisons the holder, but only callers that need the table see it, and the error appears at the first real use instead of whenever some unrelated class touched `RateTable`.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Fix an initialization-order bug, then load one class twice",
  "minutes": 14,
  "files": [
   "labs/bytecode/src/main/java/workbench/bytecode/l01/FeeSchedule.java",
   "labs/bytecode/src/main/java/workbench/bytecode/l01/IsolatingLoader.java"
  ],
  "run": "./gradlew :bytecode:test --tests 'workbench.bytecode.l01.*'",
  "steps": [
   "Run the tests once. Eight of ten fail: the unknown-country fee comes back as 0, and every loader test hits `UnsupportedOperationException`.",
   "In `FeeSchedule`, read the static fields from top to bottom as `<clinit>` runs them. Move one line so the constructor sees the real `DEFAULT_BPS`. Don't change any number. Ask yourself why `currency()` was right all along.",
   "In `IsolatingLoader.findClass`, read the class file through the parent with `getParent().getResourceAsStream(name.replace('.', '/') + \".class\")`, then call `defineClass(name, bytes, 0, bytes.length)`. Throw `ClassNotFoundException` when the stream is null.",
   "In `loadClass`, take `getClassLoadingLock(name)`. Return `findLoadedClass(name)` if it isn't null. For names that start with the prefix, call `findClass`. For everything else, return `super.loadClass(name, resolve)`.",
   "Run the tests until all ten pass. Then read `castAcrossLoadersFails` and find which loader names appear in the message."
  ],
  "hints": [
   "Constants such as `\"EUR\"` are inlined by javac, so their order doesn't matter. `Integer.parseInt(...)` is a method call, so `DEFAULT_BPS` is 0 until `<clinit>` reaches its line.",
   "If a test fails with `LinkageError: attempted duplicate class definition`, your `loadClass` defined the same name twice. Check `findLoadedClass` first.",
   "Don't call `super.loadClass` for prefix names before `findClass`: the parent would find the app's copy and you'd get the same `Class` from both loaders."
  ],
  "done_when": "All ten tests in `ClassLoadingTest` pass."
 },
 "drill": {
  "title": "A child-first loader from memory",
  "minutes": 5,
  "prompt": "Close this page and the lab. Write `loadClass(String name, boolean resolve)` for a loader that defines classes under `prefix` itself and delegates everything else to its parent. Then check: did you take the class-loading lock, and did you look for an already-loaded class before defining one?",
  "answer": {
   "lang": "java",
   "src": "@Override\nprotected Class<?> loadClass(String name, boolean resolve) throws ClassNotFoundException {\n    synchronized (getClassLoadingLock(name)) {\n        Class<?> c = findLoadedClass(name);                  // 1. defined here already?\n        if (c == null && name.startsWith(prefix)) {\n            c = findClass(name);                             // 2. child-first for the plugin\n        }\n        if (c == null) return super.loadClass(name, resolve); // 3. parent-first for the rest\n        if (resolve) resolveClass(c);\n        return c;\n    }\n}",
   "alt": {
    "lang": "kotlin",
    "src": "override fun loadClass(name: String, resolve: Boolean): Class<*> =\n    synchronized(getClassLoadingLock(name)) {\n        var c = findLoadedClass(name)                         // 1. defined here already?\n        if (c == null && name.startsWith(prefix)) {\n            c = findClass(name)                               // 2. child-first for the plugin\n        }\n        if (c == null) return super.loadClass(name, resolve)  // 3. parent-first for the rest\n        if (resolve) resolveClass(c)\n        c\n    }"
   }
  }
 },
 "recap": [
  "Three built-in loaders: bootstrap (`null`, `java.base`), platform (other JDK modules), app (your class path). They delegate parent-first.",
  "A class is (binary name, defining loader). The same bytes defined by two loaders are two classes with separate statics, and casts between them fail.",
  "Loading, linking (verify, prepare, resolve) and initialization are separate and lazy. Only initialization runs `<clinit>`.",
  "Initialization triggers: `new`, a static call, a non-constant static read or write, reflection, a subclass. Constants, `X.class`, arrays and `forName(n, false, l)` don't trigger it.",
  "`<clinit>` runs once, in source order, under a lock. A throw gives `ExceptionInInitializerError` once, then `NoClassDefFoundError` forever. Two initializers that need each other can deadlock with both threads RUNNABLE.",
  "`ClassNotFoundException` is an explicit lookup failing. `NoClassDefFoundError` is the JVM failing to link or initialize a class your code was compiled against."
 ],
 "quiz": [
  {
   "q": "`class Parent { static int rate = 290; static { log(\"Parent\"); } }` and `class Child extends Parent { static { log(\"Child\"); } }`. Fresh JVM: your code reads `Child.rate`. What is logged?",
   "options": ["`Parent` then `Child`", "Only `Child`", "Only `Parent`", "Nothing, because `rate` is static"],
   "answer": 2,
   "why": "A static field reference initializes only the class that declares the field, even when you name it through a subclass. `rate` is declared in `Parent`, so only `Parent` runs. `Parent` then `Child` is what `new Child()` or a static method declared in `Child` would log."
  },
  {
   "q": "A service's logs show `NoClassDefFoundError: Could not initialize class com.acme.BinTable` on every request since startup. What do you look for first?",
   "options": [
    "A `bin-table` jar missing from the image",
    "An earlier `ExceptionInInitializerError` (or the NCDFE's cause) showing what `BinTable`'s static initializer threw",
    "A second copy of `BinTable` in another jar",
    "A JIT deoptimization of `BinTable`"
   ],
   "answer": 1,
   "why": "\"Could not initialize class\" means the JVM found the class and its initializer already failed once; the class stays failed for the life of its loader. The first failure was an `ExceptionInInitializerError`, and on JDK 21 the NCDFE's cause names it. A missing jar shows up as an NCDFE caused by `ClassNotFoundException` instead."
  },
  {
   "q": "A Quarkus test fails with `class com.acme.Money cannot be cast to class com.acme.Money (com.acme.Money is in unnamed module of loader 'Quarkus Runtime ClassLoader' ...; com.acme.Money is in unnamed module of loader 'app')`. What happened?",
   "options": [
    "Two different versions of `Money` were compiled",
    "The JVM's class cache is corrupt",
    "`Money` was defined by two loaders, and an object from one copy met a variable typed with the other",
    "`Money` is missing a no-argument constructor"
   ],
   "answer": 2,
   "why": "The same name with two different loaders is two different classes, even from identical bytes. The fix is to make sure both sides use the same copy, for example by not holding `Money` objects in something the app loader owns, or by adjusting what is loaded parent-first. Recompiling changes nothing, because the bytes were never the problem."
  },
  {
   "q": "At startup two threads hang. Both are `RUNNABLE` with a top frame in a `<clinit>`, and `findDeadlockedThreads()` returns null. What is the most likely cause?",
   "options": [
    "A class-initialization deadlock: two static initializers that need each other, started from two threads",
    "A busy loop, because the threads are RUNNABLE",
    "Lock contention on a `synchronized` method",
    "A full GC pause"
   ],
   "answer": 0,
   "why": "Threads waiting for another thread's class initialization show as RUNNABLE, and the JDK's deadlock detector doesn't report them. `jstack` gives it away with `waiting on the Class initialization monitor for ...`. Break the cycle so one initializer no longer reads the other class's statics."
  },
  {
   "q": "From *Lazy init done right*: the holder idiom puts `static final CardBinTable INSTANCE = new CardBinTable();` in a nested `Holder` class. Why doesn't the table get built when the outer class `CardBinTable` is initialized?",
   "options": [
    "Nested classes are loaded by a different class loader",
    "`Holder` is a separate class, and nothing initializes it until `instance()` reads `Holder.INSTANCE`",
    "The JIT removes unused static fields",
    "`static final` fields are always initialized lazily"
   ],
   "answer": 1,
   "why": "A nested class is its own class with its own `<clinit>`. Initializing the outer class doesn't touch it. The first read of `Holder.INSTANCE` is a non-constant static read, which triggers `Holder`'s initialization once, under the JVM's class-init lock. That lock is also why the idiom is thread-safe without `volatile`.",
   "from": "jmm-05"
  }
 ],
 "flashcards": [
  {"front": "Which loader defines `java.lang.String`, and how does `getClassLoader()` show it?", "back": "The bootstrap loader, built into the JVM. `String.class.getClassLoader()` returns `null`."},
  {"front": "In what order does the default `loadClass` look for a class?", "back": "`findLoadedClass` (already defined here?), then the parent's `loadClass`, then its own `findClass`."},
  {"front": "Does reading `static final int MAX = 500;` from another class initialize the declaring class?", "back": "No. It's a constant variable, so javac copied 500 into the caller. `static final Integer MAX = 500;` is not a constant and does initialize it."},
  {"front": "Your code reads `Child.x`, where static field `x` is declared in `Parent`. Which classes initialize?", "back": "Only `Parent`, the class that declares the field."},
  {"front": "A static initializer throws. What do the first and the later uses of the class get?", "back": "First use: `ExceptionInInitializerError`. Every later use: `NoClassDefFoundError: Could not initialize class ...`. The JVM never retries."},
  {"front": "How does a class-initialization deadlock look in a thread dump?", "back": "Threads in `RUNNABLE` state, `waiting on the Class initialization monitor for ...`, and no \"Found one Java-level deadlock\" section."},
  {"front": "Two loaders define `com.acme.Money` from the same bytes. Is `b.isInstance(objectFromA)` true?", "back": "No. A class is (name, defining loader), so these are two classes. A cast between them throws ClassCastException naming both loaders."}
 ],
 "terms": [
  {"term": "Class loader", "plain": "An object that finds class bytes and turns them into `Class` objects. The JDK has bootstrap, platform and app loaders."},
  {"term": "Parent-first delegation", "plain": "A loader asks its parent for a class before trying to find it itself."},
  {"term": "Defining loader", "plain": "The loader that called `defineClass`. It is part of the class's identity."},
  {"term": "Linking", "plain": "Verifying, preparing (static fields set to defaults) and resolving a loaded class, before it is initialized."},
  {"term": "<clinit>", "plain": "The static initializer javac builds from static field initializers and `static {}` blocks, run once per class."},
  {"term": "Constant variable", "plain": "A `final` primitive or `String` with a compile-time constant initializer. javac copies its value into the code that reads it."},
  {"term": "Child-first loader", "plain": "A custom loader that defines certain classes itself before asking its parent, to isolate plugins or reloadable code."}
 ],
 "explain_back": {
  "prompt": "A teammate sees `NoClassDefFoundError: Could not initialize class FeeSchedule` in production and wants to add `fees-core.jar` to the image. Explain what the error really says, how you'd find the cause, and how to stop it happening again.",
  "answer": "The JVM found `FeeSchedule` fine. It already tried to run its static initializer once, that initializer threw, and the JVM marked the class as failed, so every later use gets `NoClassDefFoundError` and it never retries. Adding a jar won't help. I'd look for the first `ExceptionInInitializerError` in the log, or read the cause chain, which on JDK 21 names the original exception and thread. The fix is whatever made the initializer throw, plus moving that work out of `<clinit>`: keep statics to constants and do I/O or configuration in a bean the container starts or in a lazy holder, so a failure is an ordinary exception at the call that needs it."
 },
 "deeper": {
  "minutes": 10,
  "body": "Three details that didn't fit above.\n\nInterfaces have their own initialization rule. Initializing a class initializes its superclass, but its superinterfaces only if they declare a default method. In one experiment, `new Impl()` for a class implementing `WithDefault` (which has a default method) and `NoDefault` (which doesn't) printed `WithDefault.<clinit>` and `Impl.<clinit>`, and `NoDefault` stayed uninitialized until code read one of its fields. HotSpot's `InstanceKlass::initialize_impl` follows the JVMS steps one by one, and its comments quote this rule.\n\nLambdas are hidden classes. A lambda's class has a name like `LoaderInfo$$Lambda/0x00007f2408000a08`, `isHidden()` returns true, and `Class.forName` on that name throws `ClassNotFoundException`. `LambdaMetafactory` defines it with `Lookup.defineHiddenClass` (JDK 15) as a nestmate of the class that contains the lambda. Lesson 3 of this track shows the call site that creates it.\n\nYou can watch the phases. `-Xlog:class+load=info` prints a line per loaded class with its source, and `-Xlog:class+init=info` prints verification start and end and an `Initializing '...'` line per class. A Hello World with one lambda loaded 560 classes on JDK 21 and 645 on JDK 25, most of them from the CDS archive (`source: shared objects file`). The startup track covers that archive and the AOT cache that JDK 24 and 25 build on it.\n\n```bash\njava -Xlog:class+load=info -Xlog:class+init=info -cp bytecode/build/classes/java/demo workbench.bytecode.l01.InitPuzzle | grep -E 'InitPuzzle|Initializing'\n```"
 },
 "sources": [
  {"title": "JVM Specification SE 25, chapter 5: Loading, Linking, and Initializing", "url": "https://docs.oracle.com/javase/specs/jvms/se25/html/jvms-5.html"},
  {"title": "JLS SE 25, section 12.4: Initialization of Classes and Interfaces", "url": "https://docs.oracle.com/javase/specs/jls/se25/html/jls-12.html#jls-12.4.1"},
  {"title": "ClassLoader (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/ClassLoader.html"},
  {"title": "Quarkus: Class loading reference", "url": "https://quarkus.io/guides/class-loading-reference"}
 ]
}
out = ROOT / "content/lessons/cls-01.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
