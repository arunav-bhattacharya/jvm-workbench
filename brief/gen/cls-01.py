import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/bytecode/src"
P = "java/workbench/bytecode/l01"
K = "kotlin/workbench/bytecode/l01"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :bytecode:demo -Pmain=workbench.bytecode.l01."


def demo(java, kt):
    """Try-it code object for a Java demo and its Kotlin twin (FooKt)."""
    return {"lang": "java", "title": f"{java}.java", "src": read(f"{lab}/demo/{P}/{java}.java"),
            "run": RUN + java, "file": f"{lab}/demo/{P}/{java}.java",
            "alt": {"lang": "kotlin", "title": f"{kt}.kt", "src": read(f"{lab}/demo/{K}/{kt}.kt"),
                    "run": RUN + kt + "Kt", "file": f"{lab}/demo/{K}/{kt}.kt"}}


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


FIG = """<svg viewBox="0 0 680 270" role="img" aria-label="Three steps: loading, then linking (verify, prepare, resolve), then initialization, which runs the static initializer. Constant reads, X.class, arrays and forName with false stop before initialization; new, static calls, non-constant static reads, reflection and subclass initialization trigger it.">
<rect class="box" x="20" y="40" width="170" height="90" rx="8"/>
<text class="t" x="105" y="68" text-anchor="middle">Loading</text>
<text class="t-s t-m" x="105" y="92" text-anchor="middle">fetch the bytes</text>
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

OPENING = """Picture a small theatre company putting on a play. Props are fetched only when a scene first needs them. Before making a new crown, the stage manager asks the head of props whether the company has one. And before the first night there is one dress rehearsal, held exactly once.

The JVM, the program that runs your compiled Java and Kotlin, works the same way. It brings in each class only when some code first needs it, through objects called class loaders, and it runs the class's start-up code once. Most days you never notice. Then a program that worked for months tells the violinist to arrive 0 minutes before curtain-up. Or a log fills with `NoClassDefFoundError` for a class that is sitting right there in the jar.

Both traps are easy to walk into, because nothing in the source says *when* its code runs. Part 3 ended with an API that Java and Kotlin callers share; Part 4 goes inside the JVM. In this lesson, we'll meet its three class loaders, follow one class from loading to its first run, and load a class twice on purpose. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_WHO = """System.out.println(String.class.getClassLoader());               // null
System.out.println(java.sql.Connection.class.getClassLoader());   // ...ClassLoaders$PlatformClassLoader@<hash>
System.out.println(ShowProgram.class.getClassLoader());          // ...ClassLoaders$AppClassLoader@<hash>"""
K_WHO = """println(String::class.java.classLoader)                // null
println(java.sql.Connection::class.java.classLoader)   // ...ClassLoaders$PlatformClassLoader@<hash>
println(ShowProgram::class.java.classLoader)           // ...ClassLoaders$AppClassLoader@<hash>"""

S0 = """Your compiled program is a pile of class files in folders and jars (a jar is a zip file of class files). The JVM reads none of them until some code needs one. The object that finds a class's bytes and turns them into a `Class` the JVM can run is a **class loader**.

Let's set the theatre up properly before we lean on it. The building has its own store of things every show needs, such as chairs and the curtain. The company has a props department for rarer items. And each production has a stage manager who looks after the props made for that show. A class loader is one of these three people. A class is a prop, and its class file is the drawing the prop is made from.

Ask three classes who loaded them, and you get three answers. `ShowProgram` here is our own main class:

""" + pair(J_WHO, K_WHO) + """

The JDK has three built-in class loaders. The **bootstrap loader** is part of the JVM itself and loads `java.base`, the module that holds `String`, `List` and the other basics. A module is a named group of packages. The bootstrap loader has no Java object of its own, so `getClassLoader()` returns `null`. The building's store has no name badge.

The **platform loader** loads the rest of the JDK's modules, such as `java.sql` for databases. The **app loader** loads your class path, the list of folders and jars you give the `java` command: your own code and every library you added, Kotlin's standard library included.

Each loader has a parent. The app loader's parent is the platform loader, and the platform loader's parent is the bootstrap loader. When code asks a loader for a class, the default `loadClass` method does three things in order:

1. It checks whether it already loaded that name (`findLoadedClass`).
2. If not, it asks its parent, which asks its own parent first.
3. Only when every parent says no does it look for the class itself (`findClass`).

That's the stage manager asking the head of props, who asks the building's store, before anyone makes a new crown. It's called **parent-first delegation**. It's why `java.lang.String` always comes from the bootstrap loader, even if some jar on your class path holds a class with that very name. A stray jar can't replace a JDK class.

The loader that finally builds the class, by calling `defineClass`, is its **defining loader**, and it is part of the class's identity. At run time a class is the pair (name, defining loader). The name is the binary name, the full name such as `theatre.Scene`, or `theatre.Scene$Cue` for a class nested inside `Scene`. Two loaders can each define a class with the same name, and the last section shows what that does to a cast.

Kotlin adds nothing special here. `kotlin.Unit` is an ordinary class in an ordinary jar, so the app loader loads it like any other library class.

**Every loader asks its parent first. That's why the JDK's own classes always win.**

So far, "loading a class" has sounded like one event. Inside the JVM it's three."""

# ---------------------------------------------------------------- section 1
S1 = """Loading a class and running its start-up code are separate events, and they can happen far apart. Chapter 5 of the JVM specification, the document that says how every JVM must behave, splits the work into three steps. HotSpot, the JVM inside the JDK you installed, runs each step as late as it is allowed to.

A new prop goes through the same three steps. Someone fetches it. Before any scene uses it, the crew checks it, gives it a labelled spot on the props table and fills in the cue sheet that says where it's needed. Last comes the dress rehearsal, the only step that puts actors on stage.

1. **Loading** finds the bytes, in a folder, a jar, or made in memory, and turns them into a `Class` object with `defineClass`. That's fetching the prop.
2. **Linking** gets the class ready, in three parts. *Verification* checks that the bytecode, the instructions the compiler wrote into the class file (the next lesson reads them), is type-safe: no instruction treats a number as a string. *Preparation* creates the static fields and sets them to their defaults, `0`, `false` or `null`: an empty, labelled spot on the table. *Resolution* turns the names the class uses, such as "method `fire` in class `Lights`", into direct links, and may do it one name at a time, the first time each is used.
3. **Initialization** runs the class's static initializer, which javac names `<clinit>` ("class init"): every static field initializer and `static {}` block, top to bottom. That's the dress rehearsal.

Two small experiments show the gaps between the steps. A generated class with broken bytecode was accepted by `defineClass` on JDK 25, and the `VerifyError` came only when code first asked for its methods. A class that referred to a deleted `Helper` class loaded and ran fine. It failed with `NoClassDefFoundError` only when the branch that used `Helper` ran.

That second experiment is where the picture breaks. A real crew checks a whole prop before the show. The JVM may fill in the cross-references lazily, one name at a time, and never at all for code that never runs.

Initialization is the step your code can see, and its triggers are exact. Section 12.4.1 of the Java Language Specification lists them: creating an instance, calling a static method, assigning a static field, or reading a static field that isn't a **constant variable**. Initializing a class first initializes its superclass. Reflection such as `Class.forName(name)` counts too.

These do not initialize a class:

- reading a `static final` primitive or `String` whose value the compiler can work out, because javac copied the value into your class file;
- `Limits.class`, `new Limits[3]` and `Class.forName(name, false, loader)`;
- reading an inherited static field through a subclass: `Child.parentValue` initializes only `Parent`, the class that declares the field.

The constant rule surprises people most, and it's the warm-up question. `static final int MAX_CAST = 12` is a constant variable. `static final Integer CAP = 12` is not, because boxing calls `Integer.valueOf`. Reading the first leaves `Limits` alone, and reading the second runs `<clinit>`. Kotlin draws the same line between `const val` and a plain `val`.

**Loading isn't initialization. Only the first real use runs `<clinit>`.**

So `<clinit>` runs late, and it runs once. Those two facts are behind three real bugs, and the call sheet has the first one."""

# ---------------------------------------------------------------- section 2
J_SHEET = """// Naive: the shared instance is built too early
public final class CallSheet {
    private static final Map<String, Integer> MINUTES_BY_ROLE = Map.of("LEAD", 90, "CHORUS", 45);
    public static final CallSheet INSTANCE = new CallSheet();       // runs here
    private static final int DEFAULT_MINUTES =
            Integer.parseInt(System.getProperty("calls.default.minutes", "60"));

    private final int fallbackMinutes = DEFAULT_MINUTES;            // still 0 here
}"""
K_SHEET = """// Naive: the shared instance is built too early
class CallSheet private constructor() {
    val fallbackMinutes = DEFAULT_MINUTES                           // still 0 here

    companion object {
        private val MINUTES_BY_ROLE = mapOf("LEAD" to 90, "CHORUS" to 45)
        @JvmField val INSTANCE = CallSheet()                        // runs here
        private val DEFAULT_MINUTES = System.getProperty("calls.default.minutes", "60").toInt()
    }
}"""
J_SCRIPT = """static class Script {
    static final String TEXT = load(Path.of("hamlet.txt"));   // runs inside <clinit>

    static String load(Path p) {
        if (!Files.exists(p)) throw new IllegalStateException("script file missing: " + p);
        return "To be, or not to be";
    }
}"""
K_SCRIPT = """object Script {
    val TEXT: String = load(Path.of("hamlet.txt"))           // runs inside <clinit>

    fun load(p: Path): String {
        check(Files.exists(p)) { "script file missing: $p" }
        return "To be, or not to be"
    }
}"""

S2 = """The show program keeps a call sheet: the list that tells each player how many minutes before curtain-up to arrive. Leads come 90 minutes early and the chorus 45, and anyone else gets a default of 60, read from a setting. Here it is, trimmed from the lab's starting code:

""" + pair(J_SHEET, K_SHEET) + """

Ask it about the violinist, a role the table doesn't list, and the lab's test reports:

```text
CallSheet: an unlisted role gets the 60-minute default, not 0 FAILED
    expected: 60
     but was: 0
```

Nothing threw. The violinist is now part of the overture. The JVM did exactly what the source says: `<clinit>` runs top to bottom, and the `INSTANCE` line builds the object before the next line has set `DEFAULT_MINUTES`. The constructor reads that field while it still holds the 0 from preparation. Picture a dress rehearsal that plays the scenes in script order, even when scene 2 needs a prop that only scene 3 brings on.

With a constant initializer (`= 60`) the bug would disappear, because javac copies a constant into the code that reads it. That's why this bug tends to arrive on the day someone makes a constant configurable. You'll fix it in the lab.

`<clinit>` has two more properties, and both cause real outages. It runs once, and a failure is permanent. Here's a class that reads a script file while it initializes:

""" + pair(J_SCRIPT, K_SCRIPT) + """

With the file missing, a small program touched `Script.TEXT` three times. On JDK 25 it printed:

```text
1: java.lang.ExceptionInInitializerError
   cause: java.lang.IllegalStateException: script file missing: hamlet.txt
2: java.lang.NoClassDefFoundError: Could not initialize class Rehearsal$Script
   cause: java.lang.ExceptionInInitializerError: Exception java.lang.IllegalStateException: script file missing: hamlet.txt [in thread "main"]
3: java.lang.NoClassDefFoundError: Could not initialize class Rehearsal$Script
   cause: ...the same as 2
```

The first use gets `ExceptionInInitializerError`. The JVM marks the class as failed, and every later use, from any thread, gets `NoClassDefFoundError: Could not initialize class`. Since JDK 21 that error's cause names the first exception and the thread it happened in. A theatre would hold the dress rehearsal again tomorrow. The JVM never tries again, for as long as that class loader lives, and that's where the picture breaks. In a long log you often see the `NoClassDefFoundError` hundreds of times, and the real cause once, near the top.

The third property is that `<clinit>` runs under a lock. One thread runs it, and every other thread that needs the class waits. That lock is what made the holder idiom in the memory model track safe, and it can also deadlock. In the Try it below, `Cast`'s initializer reads `Costumes`, `Costumes`'s initializer reads `Cast`, and two threads start one each. Each thread holds one class's lock and waits for the other's.

Both threads report `RUNNABLE`, the most hopeful state a stuck thread can show. `ThreadMXBean.findDeadlockedThreads()`, the JDK's deadlock detector, finds nothing. `jstack`, a JDK tool that prints every thread's stack, shows this on JDK 25:

```text
"cast" #21 ... in Object.wait()
   java.lang.Thread.State: RUNNABLE
	at workbench.bytecode.l01.InitDeadlockDemo$Cast.<clinit>(InitDeadlockDemo.java:10)
	- waiting on the Class initialization monitor for workbench.bytecode.l01.InitDeadlockDemo$Costumes
```

There's no "Found one Java-level deadlock" section. When a program hangs at start-up, search the dump for `Class initialization monitor`.

**Keep static initializers boring: constants and small fixed tables only.**

Reading files, calling other computers and reading other classes' statics belong in ordinary code that runs at start-up, or in a lazy holder. One question from the start is still open: how can a class with a familiar name be a stranger?"""

# ---------------------------------------------------------------- section 3
J_CHILD = """@Override
protected Class<?> loadClass(String name, boolean resolve) throws ClassNotFoundException {
    synchronized (getClassLoadingLock(name)) {
        Class<?> c = findLoadedClass(name);
        if (c == null && name.startsWith(prefix)) c = findClass(name);   // child-first
        return c != null ? c : super.loadClass(name, resolve);            // parent-first
    }
}"""
K_CHILD = """override fun loadClass(name: String, resolve: Boolean): Class<*> =
    synchronized(getClassLoadingLock(name)) {
        var c = findLoadedClass(name)
        if (c == null && name.startsWith(prefix)) c = findClass(name)   // child-first
        c ?: super.loadClass(name, resolve)                              // parent-first
    }"""

S3 = """Because the loader is part of a class's identity, a loader of your own can define a second copy of a class the app loader already has. Programs that load plugins, pieces of code added after the program was built, do this on purpose. Our show program loads each scene as a plugin. If every plugin gets its own copy of its classes, two plugins can't trip over each other's statics.

The usual tool is a **child-first loader**. For names in its own package it calls `findClass` before it asks its parent, and for everything else it delegates as usual:

""" + pair(J_CHILD, K_CHILD) + """

Read it as "mine first, then my parent's". The lock from `getClassLoadingLock` stops two threads from defining the same class twice, and `findLoadedClass` returns the copy this loader already made.

Two such loaders over one class file give you two `Class` objects. Each has its own statics, and its static initializer runs once per loader. Here the theatre picture breaks, and it's worth saying out loud. Two crowns made from the same drawing are as good as each other: any actor can wear either. Two classes defined from the same bytes are strangers. An object of one can't be cast to the other, even though the names match.

`TwoLoadersDemo` in the Try it loads a small `Counter` class through two child-first loaders. It calls `hit()` twice on the copy from `plugin-1`, then casts that object to the app loader's `Counter`. On JDK 25 it printed:

```text
same name: true
c1 == c2: false, c1 == Counter.class: false
hits: plugin-1=2, plugin-2=0, app=0
class ...TwoLoadersDemo$Counter cannot be cast to class ...TwoLoadersDemo$Counter
(...$Counter is in unnamed module of loader 'plugin-1' @626b2d4a;
 ...$Counter is in unnamed module of loader 'app')
```

Three classes, and three separate `hits` fields. The cast message is long, but it's worth learning to read. The same name twice, with two loaders in the parentheses, means two copies, not a missing jar.

The two "not found" errors fit the same picture. `ClassNotFoundException` is a checked exception from a lookup by name that your code asked for, with `Class.forName` or `loadClass`: someone asked for a prop that nobody has. `NoClassDefFoundError` comes from the JVM itself, while it links or initializes code that was compiled against the class. Either the class is missing at run time (the error's cause is then a `ClassNotFoundException`), or its static initializer already failed, as in the last section.

Leaks have the same shape. A loader stays alive as long as anything reachable points at one of its classes or objects. In one experiment for this track, a plugin object added to a static list in a parent-loaded registry kept its whole `URLClassLoader` alive after `close()` and ten `System.gc()` calls, along with a 10 MB static array. (`URLClassLoader` is the JDK's loader for folders and jars, and `System.gc()` asks the garbage collector to run.) Without the registration, the loader was collected.

**The same name with two loaders is two classes. Read both loader names in the message.**

That's the whole journey of a class, from fetching its bytes to its first run. What we haven't seen yet is what those bytes say."""

ASIDE3 = {
    "title": "Where will I meet several class loaders?",
    "body": "Anywhere a program runs code it didn't start with. Application servers give each deployed application its own loader, so two applications can use different versions of one library. Test runners and build tools often load your classes in a loader of their own. Quarkus, a framework for writing Java web services, uses several loaders in its tests and in its dev mode: your classes live in a loader that is thrown away and rebuilt on every reload, on top of one that stays. Its class-loading guide warns that marking a library \"parent first\" without also marking the libraries it uses can cause a `LinkageError`. That detail comes from the Quarkus docs; this track didn't run dev mode.",
}

L = {
 "id": "cls-01",
 "title": "Class loading: loaders, delegation, linking and initialization",
 "minutes": 35,
 "goal": "By the end you can say which loader defines a class and why, predict exactly when a static initializer runs, and read a NoClassDefFoundError or a class that \"cannot be cast to\" itself for what it really means.",
 "opening": OPENING,
 "warmup": {
  "q": "`Limits` has `static final int MAX_CAST = 12;`, `static final Integer CAP = 12;` and a `static {}` block that prints \"init\". Another class prints `Limits.MAX_CAST`, then `Limits.CAP`. When does \"init\" appear?",
  "options": [
   "Before the first value, because touching any member of a class runs its start-up code",
   "Between the two values: reading `MAX_CAST` doesn't run `Limits`'s start-up code, reading `CAP` does",
   "Never, because both fields are `static final`",
   "Twice, once per field"
  ],
  "answer": 1,
  "why": "`MAX_CAST` is a constant variable: a `static final` primitive or `String` whose value the compiler can work out. javac copies `12` into the caller's class file, so at run time the caller never touches `Limits`. `CAP` is boxed (`Integer.valueOf` runs), so it isn't a constant, and reading it runs `Limits`'s static initializer. A class runs that code at most once, so \"init\" can't print twice. The section on the three steps shows it in a demo."
 },
 "sections": [
  {
   "h": "Three class loaders, and why each asks its parent first",
   "body": S0,
   "try": {
    "title": "Who loaded what",
    "minutes": 3,
    "steps": [
     "Before you run it, write down the loader and the module you expect for `String`, `java.sql.Connection`, the demo class itself and `kotlin.Unit`.",
     "Run `LoaderTour` from the `labs/` folder with the command below, then run the Kotlin twin.",
     "Compare the two \"classes loaded so far\" numbers. Why might the Kotlin one be higher?"
    ],
    "code": demo("LoaderTour", "LoaderTour"),
    "expect": "`String` has the bootstrap loader (printed as `null`, shown here as bootstrap) in `java.base`, and `java.sql.Connection` has the platform loader in `java.sql`. The demo class and `kotlin.Unit` both have the app loader and no module name (`module=null`), because the class path is one unnamed module. The chain is `app -> platform -> bootstrap`. On JDK 25 one run counted 948 loaded classes for Java and 986 for Kotlin: the Kotlin program touches more of its standard library, and every class it touches is loaded."
   },
   "refs": [
    {"title": "ClassLoader (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/ClassLoader.html", "kind": "docs"}
   ]
  },
  {
   "h": "Loading, linking and initialization: three steps, and only the last runs your code",
   "body": S1,
   "figure": {"svg": FIG, "caption": "Fetch, check and label, then the dress rehearsal: a class can be loaded and linked long before it is initialized. Only the triggers in the bottom box run its static initializer."},
   "try": {
    "title": "The initialization puzzle",
    "minutes": 5,
    "steps": [
     "Read `InitPuzzle` (or `InitPuzzle.kt`). For each of the eight steps, write down whether a `<clinit>` line prints after it, and which one.",
     "Run it and check your list.",
     "Change `CAP` to `static final int CAP = 12;` (in Kotlin, make it `const val`). Predict step 4, then run it again."
    ],
    "code": demo("InitPuzzle", "InitPuzzle"),
    "expect": "Step 1 prints only `Parent.<clinit>`, because the field belongs to `Parent`. Step 2 prints only `Child.<clinit>`, because `Parent` is already done. Step 4 prints `Limits.<clinit>`, step 8 prints `Lazy.<clinit>`, and steps 3, 5, 6 and 7 print nothing. After the change, step 4 prints nothing too, and `Limits` is never initialized at all. The Kotlin twin shows the same pattern with `KParent`, `KChild`, `KLimits` and `KLazy`."
   },
   "refs": [
    {"title": "JVM Specification SE 25, chapter 5: Loading, Linking, and Initializing", "url": "https://docs.oracle.com/javase/specs/jvms/se25/html/jvms-5.html", "kind": "docs"},
    {"title": "JLS SE 25, section 12.4.1: When initialization occurs", "url": "https://docs.oracle.com/javase/specs/jls/se25/html/jls-12.html#jls-12.4.1", "kind": "docs"}
   ]
  },
  {
   "h": "The dress rehearsal runs once: order, failure and deadlock",
   "body": S2,
   "try": {
    "title": "Deadlock two classes",
    "minutes": 4,
    "steps": [
     "Run `InitDeadlockDemo` (or the Kotlin twin). It starts two threads, one that needs `Cast` and one that needs `Costumes`, and waits one second.",
     "Read the state and the top frame it prints for each thread, and what the deadlock detector says.",
     "Optional: run it with `-Pargs=wait`, then run the printed `jstack` command in a second terminal and search for `Class initialization monitor`.",
     "Fix it: make `Costumes.COUNT` a constant (`static final long COUNT = 36;` with no `static` block, or `const val COUNT = 36L` in Kotlin) and run it again."
    ],
    "code": demo("InitDeadlockDemo", "InitDeadlockDemo"),
    "expect": "Both threads show `state=RUNNABLE` with a top frame inside a `<clinit>`, and the detector prints `found nothing`. The JVM exits only because the threads are daemons, threads it doesn't wait for. In `jstack` each thread is `in Object.wait()` and `waiting on the Class initialization monitor for` the other class. After the fix, `Cast` reads a constant and no longer needs `Costumes` to initialize, so the threads print `12` and `36`, both show `state=TERMINATED at (finished)`, and the program ends normally."
   }
  },
  {
   "h": "Same drawing, two stage managers: one class defined twice",
   "body": S3,
   "aside": ASIDE3,
   "try": {
    "title": "Two Counters that aren't the same class",
    "minutes": 4,
    "steps": [
     "Read `TwoLoadersDemo`. It loads `Counter` through two child-first loaders and calls `hit()` twice on the copy from `plugin-1`.",
     "Predict the three `hits` values, and whether the cast at the end works.",
     "Run it (or the Kotlin twin) and find the two loader names in the exception message."
    ],
    "code": demo("TwoLoadersDemo", "TwoLoadersDemo"),
    "expect": "`same name: true`, `c1 == c2: false` and `c1 == Counter.class: false`. The hits are `plugin-1=2, plugin-2=0, app=0`: three classes, three separate static fields. The cast fails with `... cannot be cast to class ...$Counter`, and the parentheses name loader `'plugin-1'` and loader `'app'`. The number after the `@` changes from run to run."
   },
   "refs": [
    {"title": "Quarkus: Class loading reference", "url": "https://quarkus.io/guides/class-loading-reference", "kind": "read"}
   ]
  }
 ],
 "compare": {
  "title": "When static initialization runs, in Java and Kotlin",
  "java": {"title": "Limits.java", "src": "class Limits {\n    static final int MAX_CAST = 12;         // constant: copied into callers, no init\n    static final Integer CAP = 12;          // not a constant: reading it runs <clinit>\n    static Limits defaults() { return new Limits(); }\n\n    static { System.out.println(\"Limits init\"); }\n}\n\n// Limits.MAX_CAST    -> nothing\n// Limits.CAP         -> \"Limits init\"\n// Limits.defaults()  -> \"Limits init\" (if not done yet)"},
  "kotlin": {"title": "Limits.kt", "src": "object Limits {\n    const val MAX_CAST = 12                 // constant: copied into callers, no init\n    val CAP: Int = 12                       // private static field + getCAP() on the object\n    fun defaults() = Limits\n\n    init { println(\"Limits init\") }\n}\n\n// Limits.MAX_CAST    -> nothing\n// Limits.CAP         -> \"Limits init\" (goes through Limits.INSTANCE)\n// Limits.defaults()  -> \"Limits init\" (if not done yet)"},
  "note": "Kotlin has no `static`, but an `object` compiles to a class with a `public static final INSTANCE` field and a static initializer that builds it, so the JVM's rules are the same. Only `const val` (primitives and `String`) is copied into callers like a Java constant variable. A plain `val` in an object becomes a private static field plus a getter, so reading it touches the class and runs its `init` blocks. Companion objects follow the same rules, and their `init` code lands in the outer class's static initializer. That's why the Kotlin `CallSheet` in the section on the dress rehearsal reads 0 exactly like the Java one: a quick run of it printed `VIOLIN: 0`."
 },
 "worked": {
  "title": "Read a NoClassDefFoundError back to its cause",
  "steps": [
   {"say": "A test run of the show program prints this forty times. Before you read on, decide: is a jar missing?", "code": "java.lang.NoClassDefFoundError: Could not initialize class theatre.ScriptBook\n    at theatre.Rehearsals.start(Rehearsals.java:31)\n    ...\nCaused by: java.lang.ExceptionInInitializerError: Exception java.lang.IllegalStateException:\n    script file missing: hamlet.txt [in thread \"main\"]", "lang": "text"},
   {"say": "No. \"Could not initialize class\" means the JVM found `ScriptBook` and already tried its static initializer once. The cause (JDK 21 and later) points at that first failure. Here is the class. Every static field initializer is a line of `<clinit>`, run once, in order.", "code": "public final class ScriptBook {\n    // 1. runs inside <clinit>: any exception here poisons the class for good\n    static final ScriptBook CURRENT = load(Path.of(\"hamlet.txt\"));\n\n    static ScriptBook load(Path p) {\n        if (!Files.exists(p)) throw new IllegalStateException(\"script file missing: \" + p);\n        return new ScriptBook(/* read 4,000 lines */);\n    }\n}", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "class ScriptBook private constructor() {\n    companion object {\n        // 1. runs inside ScriptBook's <clinit>: any exception here poisons the class for good\n        val CURRENT: ScriptBook = load(Path.of(\"hamlet.txt\"))\n\n        fun load(p: Path): ScriptBook {\n            check(Files.exists(p)) { \"script file missing: $p\" }\n            return ScriptBook(/* read 4,000 lines */)\n        }\n    }\n}"},
   {"say": "Move the file reading out of class initialization, into an ordinary object that the program builds once at start-up. If the file is missing, start-up fails once, with a clear stack trace, and the next run after the file is fixed simply works. The class has no static state left to poison.", "code": "public final class Scripts {\n    private final ScriptBook current;\n\n    public Scripts(Path file) {\n        current = ScriptBook.load(file);              // 2. ordinary code, ordinary exception\n    }\n\n    public ScriptBook current() { return current; }    // 3. no static state left to poison\n}\n\n// at start-up, once: Scripts scripts = new Scripts(Path.of(\"hamlet.txt\"));", "lang": "java",
    "alt_lang": "kotlin", "alt_code": "class Scripts(file: Path) {\n    private val current: ScriptBook = ScriptBook.load(file)   // 2. ordinary code, ordinary exception\n\n    fun current(): ScriptBook = current                        // 3. no static state left to poison\n}\n\n// at start-up, once: val scripts = Scripts(Path.of(\"hamlet.txt\"))"},
   {"say": "If the value must stay static, make it lazy with a holder class (memory model track, lesson 5). A failure still poisons the holder, but only callers that need the script see it, and the error appears at the first real use instead of whenever some unrelated code touched `ScriptBook`.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Fix the call sheet, then load one class twice",
  "minutes": 14,
  "files": [
   "labs/bytecode/src/main/java/workbench/bytecode/l01/CallSheet.java",
   "labs/bytecode/src/main/java/workbench/bytecode/l01/IsolatingLoader.java"
  ],
  "run": "./gradlew :bytecode:test --tests 'workbench.bytecode.l01.*'",
  "steps": [
   "Run the tests once. Eight of ten fail: an unlisted role gets 0 minutes instead of 60, and every loader test hits `UnsupportedOperationException`.",
   "In `CallSheet`, read the static fields from top to bottom, the way `<clinit>` runs them. Move one line so the constructor sees the real `DEFAULT_MINUTES`. Don't change any number. Ask yourself why `unit()` was right all along.",
   "`IsolatingLoader` is a child-first loader for the show program's scene plugins. In its `findClass`, read the class file through the parent with `getParent().getResourceAsStream(name.replace('.', '/') + \".class\")`, then call `defineClass(name, bytes, 0, bytes.length)`. Throw `ClassNotFoundException` when the stream is null.",
   "In `loadClass`, take `getClassLoadingLock(name)`. Return `findLoadedClass(name)` if it isn't null. For names that start with the prefix, call `findClass`. For everything else, return `super.loadClass(name, resolve)`.",
   "Run the tests until all ten pass. Then read `castAcrossLoadersFails` and find which loader names appear in the message."
  ],
  "hints": [
   "Constants such as `\"minutes\"` are copied into the code by javac, so their order doesn't matter. `Integer.parseInt(...)` is a method call, so `DEFAULT_MINUTES` is 0 until `<clinit>` reaches its line.",
   "If a test fails with `LinkageError: attempted duplicate class definition`, your `loadClass` defined the same name twice. Check `findLoadedClass` first.",
   "Don't call `super.loadClass` for prefix names before `findClass`: the parent would find the app's copy, and you'd get the same `Class` from both loaders."
  ],
  "done_when": "All ten tests in `ClassLoadingTest` pass."
 },
 "drill": {
  "title": "A child-first loader from memory",
  "minutes": 5,
  "prompt": "Close this page and the lab. Write `loadClass(String name, boolean resolve)` for a loader that defines classes under `prefix` itself and asks its parent for everything else. Then check: did you take the class-loading lock, and did you look for an already-loaded class before defining one?",
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
  "Three built-in loaders: bootstrap (`null`, `java.base`), platform (the other JDK modules) and app (your class path). Each asks its parent first, so the JDK's classes can't be replaced.",
  "A class is (binary name, defining loader). The same bytes defined by two loaders are two classes with separate statics, and casts between them fail with both loader names in the message.",
  "Loading, linking (verify, prepare, resolve) and initialization are separate and lazy. Only initialization runs `<clinit>`, on first real use: `new`, a static call, a non-constant static read or write, reflection, a subclass.",
  "`<clinit>` runs once, top to bottom, under a lock. A throw gives `ExceptionInInitializerError` once, then `NoClassDefFoundError: Could not initialize class` forever. Two initializers that need each other can deadlock with both threads RUNNABLE.",
  "`ClassNotFoundException` is a lookup by name that failed. `NoClassDefFoundError` is the JVM failing to link or initialize a class your code was compiled against.",
  "The limit: loaders and initialization rules tell you when a class arrives and when its start-up code runs, not what the compiled code actually does. For that you read the bytecode."
 ],
 "closing": "We started with a theatre that fetches each prop only when a scene needs it, asks the head of props first, and holds one dress rehearsal. The JVM does the same: three loaders that ask their parents first, three steps of which only the last runs your code, and a `<clinit>` that runs once, in order, under a lock, and never again.\n\nNow open a project of yours and search for `static final` fields whose initializer calls a method, such as `load(`, `read`, `parse` or `getProperty`. Each one runs in a rehearsal you can't hold twice.\n\nNext, we'll open a class file and read the instructions inside `<clinit>` and every other method: what does the compiler really write down?",
 "quiz": [
  {
   "q": "`class Parent { static int seats = 290; static { log(\"Parent\"); } }` and `class Child extends Parent { static { log(\"Child\"); } }`. In a fresh JVM, your code reads `Child.seats`. What is logged?",
   "options": ["`Parent` then `Child`", "Only `Child`", "Only `Parent`", "Nothing, because `seats` is static"],
   "answer": 2,
   "why": "A static field read initializes only the class that declares the field, even when you name it through a subclass. `seats` is declared in `Parent`, so only `Parent` runs its static initializer. `Parent` then `Child` is what `new Child()`, or a static method declared in `Child`, would log."
  },
  {
   "q": "A program's log shows `NoClassDefFoundError: Could not initialize class theatre.SeatPlan` on every request since start-up. What do you look for first?",
   "options": [
    "A `seat-plan` jar missing from the class path",
    "An earlier `ExceptionInInitializerError` (or the error's cause) showing what `SeatPlan`'s static initializer threw",
    "A second copy of `SeatPlan` in another jar",
    "A bug in the JIT compiler"
   ],
   "answer": 1,
   "why": "\"Could not initialize class\" means the JVM found the class and its initializer already failed once. The class stays failed for the life of its loader. The first failure was an `ExceptionInInitializerError`, and since JDK 21 the later error's cause names it. A missing jar shows up as a `NoClassDefFoundError` caused by `ClassNotFoundException` instead."
  },
  {
   "q": "A plugin test fails with `class theatre.Scene cannot be cast to class theatre.Scene (theatre.Scene is in unnamed module of loader 'plugin-1' ...; theatre.Scene is in unnamed module of loader 'app')`. What happened?",
   "options": [
    "Two different versions of `Scene` were compiled",
    "The JVM's class cache is corrupt",
    "`Scene` was defined by two loaders, and an object from one copy met a variable typed with the other",
    "`Scene` is missing a no-argument constructor"
   ],
   "answer": 2,
   "why": "The same name with two different loaders is two different classes, even from identical bytes. The fix is to make both sides use one copy: for example, share an interface loaded by the parent, and keep the plugin's own classes inside the plugin. Recompiling changes nothing, because the bytes were never the problem."
  },
  {
   "q": "At start-up two threads hang. Both are `RUNNABLE` with a top frame in a `<clinit>`, and `findDeadlockedThreads()` returns null. What is the most likely cause?",
   "options": [
    "A class-initialization deadlock: two static initializers that need each other, started from two threads",
    "A busy loop, because the threads are RUNNABLE",
    "Two threads fighting over a `synchronized` method",
    "A long garbage-collection pause"
   ],
   "answer": 0,
   "why": "Threads waiting for another thread's class initialization show as RUNNABLE, and the JDK's deadlock detector doesn't report them. `jstack` gives it away with `waiting on the Class initialization monitor for ...`. Break the cycle so one initializer no longer reads the other class's statics."
  },
  {
   "q": "From *Lazy init done right*: the holder idiom puts `static final Table INSTANCE = new Table();` in a nested `Holder` class. Why isn't the table built when the outer class `Table` is initialized?",
   "options": [
    "Nested classes are loaded by a different class loader",
    "`Holder` is a separate class, and nothing initializes it until `instance()` reads `Holder.INSTANCE`",
    "The JIT removes unused static fields",
    "`static final` fields are always initialized lazily"
   ],
   "answer": 1,
   "why": "A nested class is its own class with its own `<clinit>`. Initializing the outer class doesn't touch it. The first read of `Holder.INSTANCE` is a non-constant static read, which runs `Holder`'s initialization once, under the JVM's class-initialization lock. That lock is also why the idiom is thread-safe without `volatile`.",
   "from": "jmm-05"
  }
 ],
 "flashcards": [
  {"front": "Which loader defines `java.lang.String`, and how does `getClassLoader()` show it?", "back": "The bootstrap loader, built into the JVM. `String.class.getClassLoader()` returns `null`."},
  {"front": "In what order does the default `loadClass` look for a class?", "back": "`findLoadedClass` (already defined here?), then the parent's `loadClass`, then its own `findClass`."},
  {"front": "Does reading `static final int MAX = 12;` from another class initialize the declaring class?", "back": "No. It's a constant variable, so javac copied 12 into the caller. `static final Integer MAX = 12;` is not a constant, and reading it does initialize the class."},
  {"front": "Your code reads `Child.x`, where the static field `x` is declared in `Parent`. Which classes initialize?", "back": "Only `Parent`, the class that declares the field."},
  {"front": "A static initializer throws. What do the first use and the later uses of the class get?", "back": "First use: `ExceptionInInitializerError`. Every later use: `NoClassDefFoundError: Could not initialize class ...`. The JVM never retries."},
  {"front": "How does a class-initialization deadlock look in a thread dump?", "back": "Threads in `RUNNABLE` state, `waiting on the Class initialization monitor for ...`, and no \"Found one Java-level deadlock\" section."},
  {"front": "Two loaders define `theatre.Scene` from the same bytes. Is `b.isInstance(objectFromA)` true?", "back": "No. A class is (name, defining loader), so these are two classes. A cast between them throws `ClassCastException` naming both loaders."}
 ],
 "terms": [
  {"term": "Class loader", "plain": "An object that finds a class's bytes and turns them into a `Class` object. The JDK has bootstrap, platform and app loaders."},
  {"term": "Parent-first delegation", "plain": "A loader asks its parent for a class before it tries to find the class itself."},
  {"term": "Defining loader", "plain": "The loader that called `defineClass` for a class. It is part of the class's identity."},
  {"term": "Linking", "plain": "Verifying, preparing (static fields set to defaults) and resolving a loaded class, before it is initialized."},
  {"term": "<clinit>", "plain": "The static initializer javac builds from static field initializers and `static {}` blocks, run once per class."},
  {"term": "Constant variable", "plain": "A `final` primitive or `String` whose value the compiler can work out. javac copies the value into the code that reads it."},
  {"term": "Child-first loader", "plain": "A custom loader that defines certain classes itself before asking its parent, to keep plugins or reloadable code apart."}
 ],
 "explain_back": {
  "prompt": "A teammate sees `NoClassDefFoundError: Could not initialize class CallSheet` in a running program and wants to add `call-sheet.jar` to the class path. Explain what the error really says, how you'd find the cause, and how to stop it happening again.",
  "answer": "The JVM found `CallSheet` fine. It already tried to run its static initializer once, that initializer threw, and the JVM marked the class as failed, so every later use gets `NoClassDefFoundError` and it never tries again. Adding a jar won't help. I'd look for the first `ExceptionInInitializerError` in the log, or read the error's cause, which since JDK 21 names the original exception and the thread. The fix is whatever made the initializer throw, plus moving that work out of `<clinit>`: keep statics to constants and small fixed tables, and do file reading or configuration in ordinary code that runs at start-up, or in a lazy holder, so a failure is an ordinary exception at the call that needs it."
 },
 "deeper": {
  "minutes": 10,
  "body": "Three details that didn't fit above.\n\nInterfaces have their own initialization rule. Initializing a class initializes its superclass, but its superinterfaces only if they declare a default method. In one experiment, `new Impl()` for a class implementing `WithDefault` (which has a default method) and `NoDefault` (which doesn't) printed `WithDefault.<clinit>` and `Impl.<clinit>`, and `NoDefault` stayed uninitialized until code read one of its fields. HotSpot's `InstanceKlass::initialize_impl` follows the specification's steps one by one, and its comments quote this rule.\n\nLambdas are hidden classes. A lambda's class has a name like `InitDeadlockDemo$$Lambda/0x0000000055080210` (you can spot one in the `jstack` output above), `isHidden()` returns true, and `Class.forName` on that name throws `ClassNotFoundException`. `LambdaMetafactory` defines it with `Lookup.defineHiddenClass` (JDK 15) as a nestmate of the class that contains the lambda, which means it may use that class's private members. Lesson 3 of this track shows the call that creates it.\n\nYou can watch the steps happen. `-Xlog:class+load=info` prints a line for each loaded class with where it came from, and `-Xlog:class+init=info` prints when verification starts and ends and an `Initializing '...'` line for each class. A Hello World with one lambda loaded 560 classes on JDK 21 and 645 on JDK 25, most of them from the CDS archive (`source: shared objects file`), a file of JDK classes that were already parsed when the JDK was built. The startup track covers that archive and the AOT cache that JDK 24 and 25 build on it.\n\n```bash\njava -Xlog:class+load=info -Xlog:class+init=info -cp bytecode/build/classes/java/demo workbench.bytecode.l01.InitPuzzle | grep -E 'InitPuzzle|Initializing'\n```"
 },
 "sources": [
  {"title": "JVM Specification SE 25, chapter 5: Loading, Linking, and Initializing", "url": "https://docs.oracle.com/javase/specs/jvms/se25/html/jvms-5.html"},
  {"title": "JLS SE 25, section 12.4: Initialization of Classes and Interfaces", "url": "https://docs.oracle.com/javase/specs/jls/se25/html/jls-12.html#jls-12.4.1"},
  {"title": "ClassLoader (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/ClassLoader.html"},
  {"title": "Quarkus: Class loading reference", "url": "https://quarkus.io/guides/class-loading-reference"}
 ]
}
# spread the correct answers over the option positions
for q, idx in zip(L["quiz"], [2, 1, 3, 0, 1]):
    right = q["options"].pop(q["answer"])
    q["options"].insert(idx, right)
    q["answer"] = idx
out = ROOT / "content/lessons/cls-01.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
