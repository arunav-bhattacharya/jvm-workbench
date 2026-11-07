# JVM class loading, bytecode and dynamic proxies (state as of 7 November 2026)

Scope: notes for a 7-lesson track (class loading; reading bytecode; invokedynamic; JDK dynamic proxies, in the most depth; subclass proxies and frameworks; the ClassFile API; agents and instrumentation), for a senior Kotlin/Java backend engineer who uses Quarkus and has used Spring.

How to read the citations:
- **[Source](URL)** means a page or file I fetched in this session. Many official hosts were blocked from this sandbox (openjdk.org, docs.oracle.com, docs.spring.io, quarkus.io, bytebuddy.net, inside.java). So the JDK facts come from the **OpenJDK source at GA tags** on raw.githubusercontent.com. The Spring and Quarkus facts come from the **asciidoc sources** of their reference docs on GitHub, which are the same text the official sites render.
- **(local run: ...)** means a program I wrote and ran in this session. The code is summarised in "Teaching notes". The runtimes were: JDK 21.0.12.1 (system), JDK 24 (24+36), JDK 25.0.4.1, Temurin 25+36 (JMH only), JDK 26.0.2 and JDK 27.0.1.0.3, all Linux x64. I also used kotlinc 2.4.21, Byte Buddy 1.18.17 (SHA-1 checked against Maven Central) and the JUnit 6.1.3 console launcher. These versions match `/home/user/jvm-workbench/labs/build.gradle.kts` (Kotlin 2.4.21, Byte Buddy 1.18.17, JUnit 6.1.3).
- **(spec, not fetched)** marks JVMS or JLS rules stated from the specification without fetching the page, because docs.oracle.com was blocked. Each one was then checked by a local run or against HotSpot source comments.
- JDK GA dates come from `make/conf/version-numbers.conf` at each GA tag: 21 = 2023-09-19, 22 = 2024-03-19, 23 = 2024-09-17, 24 = 2025-03-18, 25 = 2025-09-16, 26 = 2026-03-17, 27 = 2026-09-15, and master is now 28 (2027-03-23) — [jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/make/conf/version-numbers.conf), [jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/make/conf/version-numbers.conf), [master](https://raw.githubusercontent.com/openjdk/jdk/master/make/conf/version-numbers.conf).

## 1. Class loading: built-in loaders, delegation, the loading/linking/initialization phases, initialization triggers and deadlocks, CNFE vs NCDFE, custom loaders, isolation and leaks

### Takeaway
There are three built-in loaders: bootstrap (shown as `null`), platform, and app (system). They delegate parent-first by default. A class's identity is the pair (binary name, defining loader). Loading, linking (verification, preparation, resolution) and initialization are separate steps, and the JVM performs them lazily. Initialization runs only on specific first uses. Constant reads, `X.class`, array creation and `Class.forName(n, false, l)` do not trigger it. `NoClassDefFoundError` usually means the class was resolvable at compile time but not at link time, or that its static initializer already failed. It does not necessarily mean a jar is missing.

### Cited Findings
**Built-in loaders and delegation**
- The ClassLoader Javadoc lists the built-in loaders. The bootstrap loader is "the virtual machine's built-in class loader, typically represented as `null`, and does not have a parent". The platform loader loads "Java SE platform APIs, their implementation classes and JDK-specific run-time classes". The system loader "is also known as *application class loader*… typically used to define classes on the application class path, module path, and JDK-specific tools". The platform loader is its parent or an ancestor — [ClassLoader.java jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/ClassLoader.java)
- The default `loadClass` algorithm is: (1) `findLoadedClass`, (2) the parent's `loadClass` (the VM's built-in loader if the parent is null), (3) `findClass`, then `resolveClass` if `resolve` is true. "Subclasses of ClassLoader are encouraged to override findClass(String), rather than this method." Unless overridden, it "synchronizes on the result of getClassLoadingLock" — [ClassLoader.java jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/ClassLoader.java)
- Observed on JDK 21 and 25 (identical): `java.lang.String` has loader null (bootstrap) in module java.base. `java.sql.Connection` and `java.net.http.HttpClient` have loader `platform`. An application class has loader `app`. The chain is `app (jdk.internal.loader.ClassLoaders$AppClassLoader) -> platform (jdk.internal.loader.ClassLoaders$PlatformClassLoader) -> null (bootstrap)` (local run: LoaderInfo)

**Phases (JVMS chapter 5)**
- JVMS ch.5 splits the work into: creation and loading (§5.3, including §5.3.5 "Deriving a Class from a class File Representation"), linking (§5.4: verification §5.4.1, preparation §5.4.2, resolution §5.4.3), and initialization (§5.5). Preparation creates static fields and sets them to default values. Resolution turns symbolic constant-pool references into direct references and may happen lazily (spec, not fetched). The section numbers are confirmed by the `@jvms` tags on `Lookup.defineHiddenClass`: "@jvms 5.4.3.1 Class and Interface Resolution", "@jvms 5.3.5 Deriving a Class…", "@jvms 5.4 Linking", "@jvms 5.5 Initialization" — [MethodHandles.java jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/invoke/MethodHandles.java)
- HotSpot's `InstanceKlass::initialize_impl` begins with "Make sure klass is linked (verified) before initialization" and "A class could already be verified, since it has been reflected upon". It then implements the JVMS procedure in commented steps ("Step 1" … "Step 10 and 11"). Step 7 is "if C is a class rather than an interface, initialize it's super class and super interfaces… If C implements any interface that declares a non-static, concrete method, the initialization of C triggers initialization of its super interfaces" — [instanceKlass.cpp jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/oops/instanceKlass.cpp)
- The same file quotes JVMS 5.5: "If C is an interface that declares a non-abstract, non-static method, the initialization of a class that implements C directly or indirectly" triggers its initialization, and "when an interface is initialized, it does not look at its supers" — [instanceKlass.cpp jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/oops/instanceKlass.cpp)
- Loading is not linking (local run on JDK 25.0.4.1, BadGen2). I generated a class whose `int answer()` does `ldc "forty-two"; ireturn`. `ClassLoader.defineClass` **succeeded**. The first `getDeclaredMethods()` then threw `java.lang.VerifyError: Bad type on operand stack … Bad.answer()I @2: ireturn … Type 'java/lang/String' (current frame, stack[0]) is not assignable to integer`, from `Class.getDeclaredMethods0`. In contrast, `MethodHandles.Lookup.defineClass` threw the VerifyError right away, from `ClassLoader.defineClass0`. So HotSpot verified eagerly on that path (local run: BadGen). `ClassFile.of().verify(bytes)` reported the same error offline: `[java.lang.VerifyError: Bad type on operand stack in Bad::answer() @2 (integer_type is not assignable from java/lang/String)]` (local run)
- Resolution is lazy. `UsesHelper` references `Helper` in a branch. With `Helper.class` deleted, the program printed "main started, UsesHelper linked fine" and "done". Only when the branch ran did it fail, with `Exception in thread "main" java.lang.NoClassDefFoundError: demo/Helper … Caused by: java.lang.ClassNotFoundException: demo.Helper` (local run, JDK 21)

**When is a class initialized (JLS 12.4.1 / JVMS 5.5)**
- JLS §12.4.1 (spec, not fetched): T is initialized immediately before the first of: an instance of T is created; a static method declared by T is invoked; a static field declared by T is assigned; a static field declared by T is used and is not a constant variable (§4.12.4). Initializing a class first initializes its superclass and the superinterfaces that declare default methods. A static field reference initializes only the class that declares the field, even if accessed through a subclass name. JVMS §5.5 adds the bytecode-level triggers: `new`, `getstatic`, `putstatic`, `invokestatic`; the first invocation of a MethodHandle resolved as REF_getStatic, REF_putStatic, REF_invokeStatic or REF_newInvokeSpecial; some reflective calls; initialization of a subclass; and being the initial class at JVM startup (spec, not fetched)
- All of these were observed on JDK 21 (local run: InitPuzzle, output verbatim):
  - `Child.parentValue` (a static field of Parent read via Child) → `Parent.<clinit>` only
  - `new Child()` → `Child.<clinit>`
  - `Consts.COMPILE_TIME` (`static final int = 42`) → nothing initialized
  - `Consts.S` (a String constant) → nothing
  - `Consts.BOXED` (`static final Integer`, not a constant variable) → `Consts.<clinit>`
  - `new Lazy[3]` → nothing
  - `Lazy.class` → nothing
  - `Class.forName("demo.InitPuzzle$Lazy", false, loader)` → nothing
  - `Lazy.touch()` → `Lazy.<clinit>`
  - `new Impl()` (implements `WithDefault` [has a default method] and `NoDefault`) → `WithDefault.<clinit> Impl.<clinit>`, so NoDefault is *not* initialized
  - `NoDefault.Y` → `NoDefault.<clinit>`
  - `Class.forName("demo.InitPuzzle$Holder")` → `Holder.<clinit>`
- The JUnit lab confirmed it: `Class.forName(name, false, loader)` loads but does not run `<clinit>`, while a reflective `Field.getInt` on a static field does (local run: LabTests.countingLoadedClasses, JDK 21 and 25)

**Class-initialization deadlock**
- Setup: two classes whose static initializers each read the other's static field, started from two threads. On JDK 21.0.12.1 and 25.0.4.1, `jstack` showed both threads as `java.lang.Thread.State: RUNNABLE` with the header `in Object.wait()` and the frame line `- waiting on the Class initialization monitor for demo.InitDeadlock$B` (respectively `$A`). `jstack` printed **no** "Found one Java-level deadlock" section (local run: InitDeadlock)

**ExceptionInInitializerError → NoClassDefFoundError; ClassNotFoundException**
- A static initializer that throws gives `java.lang.ExceptionInInitializerError` (cause `IllegalStateException: config file missing`) on first use. **Every later use** gives `java.lang.NoClassDefFoundError: Could not initialize class demo.NcdfeDemo$Config`, whose cause is `java.lang.ExceptionInInitializerError: Exception java.lang.IllegalStateException: config file missing [in thread "main"]` (local run, JDK 21.0.12.1)
- `Class.forName("com.example.DoesNotExist")` → `java.lang.ClassNotFoundException: com.example.DoesNotExist`, a checked exception thrown by an explicit lookup (local run)

**Custom loaders, identity and isolation**
- Two child-first loaders defined `demo.plugin.Counter` from the same bytes. Results (local run: TwoLoaders, JDK 21):
  - `c1 == c2: false`, and neither equals the app loader's copy
  - statics are per Class object: `c1 -> 2, c2 -> 1`
  - `c2.isInstance(s1): false`
  - the cast failed with: `CCE: class demo.plugin.Counter cannot be cast to class demo.plugin.Counter (demo.plugin.Counter is in unnamed module of loader 'plugin-1' @2a139a55; demo.plugin.Counter is in unnamed module of loader 'app')`
- Lambdas are hidden classes. Names look like `demo.LoaderInfo$$Lambda/0x00007f2408000a08` (JDK 21) or `…$$Lambda/0x0000000049040210` (JDK 25), `isHidden()` is true, and `Class.forName(name)` fails with ClassNotFoundException (local run). `InnerClassLambdaMetafactory` comments "define a hidden nestmate" and passes `NESTMATE_CLASS | STRONG_LOADER_LINK` — [InnerClassLambdaMetafactory.java jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/invoke/InnerClassLambdaMetafactory.java). `Lookup.defineHiddenClass` is `@since 15` — [MethodHandles.java jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/invoke/MethodHandles.java)

**Classloader leaks**
- A `URLClassLoader` loaded `leak.Plugin` (which holds a 10 MB static array), and its instance was added to a static list in a parent-loaded `Registry`. After `close()`, nulling every local and 10× `System.gc()`, a `WeakReference` to the loader was **still set**. Without the registration it **was cleared**. Output: `leaky: loader collected after close()+GC? false` / `fixed: … true` (local run: LeakDemo, JDK 21)

**Counting loaded classes**
- A Hello-world with one lambda and one string concatenation loaded 560 classes on JDK 21.0.12.1 (549 "source: shared objects file", i.e. the CDS archive). It loaded 645 on JDK 25.0.4.1 (636 from CDS), and 594 on JDK 21 with `-Xshare:off`. The counts come from `-Xlog:class+load=info` (local run). With the extra management classes, `ClassLoadingMXBean.getLoadedClassCount()` reported 833 (JDK 21) and 856 (JDK 25) (local run: LoaderInfo)
- `-Xlog:class+init=info` prints "Start class verification for: …", "End class verification…" and "Initializing '…'" lines, which make the separate linking and initialization steps visible (local run, JDK 21)

**Quarkus class loading (dev mode, tests, hot reload)**
- In production fast-jar mode, "almost all dependencies are loaded via the `io.quarkus.bootstrap.runner.RunnerClassLoader` which indexes class at build time". `legacy-jar` and native images use a flat classpath. Tests, dev mode and builds use a multi-loader architecture — [class-loading-reference.adoc](https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/class-loading-reference.adoc)
- The loaders in that architecture are:
  - Base ClassLoader: usually the system loader
  - Augmentation ClassLoader: loads the `-deployment` artifacts; persistent across restarts
  - Deployment ClassLoader: loads the application classes for build steps; re-created on start
  - Base Runtime ClassLoader: loads the runtime extension dependencies; "persistent, even if the application restarts it will remain (which is why it cannot load application classes that may be hot deployed)"
  - Runtime Class Loader: loads "the application classes and other hot deployable resources… recreated when the application is restarted"
  
  "The runtime ClassLoader is always isolated". JDK classes and "parent first" artifacts are the exceptions. "If you mark a dependency as parent first then all of its dependencies must also be parent first, or a `LinkageError` can occur." Also: "Once a class has been loaded it cannot be changed, so if a class is loaded before the transformers have been prepared this will prevent the transformation from working." — [class-loading-reference.adoc](https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/class-loading-reference.adoc)

**Related JDK 24–27 class-loading features (Leyden AOT cache)**
- The `java` man page documents `-XX:AOTCache` and `-XX:AOTMode` from JDK 24 — [java.md jdk-24-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-24-ga/src/java.base/share/man/java.md)
- JDK 25 adds `-XX:AOTCacheOutput` and the modes `auto`, `off`, `record`, `create` and `on` — [java.md jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/man/java.md)
- JDK 27 lists `auto`, `off`, `record`, `create`, `on` and `required`, with "`on` is an alias for `required`" — [java.md jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/java.base/share/man/java.md)

### Inferences
- Triage for NoClassDefFoundError: first look for an earlier ExceptionInInitializerError (on JDK 21+ the NCDFE's cause carries the original exception and thread name, as observed). Then check for compile-time vs runtime classpath skew, or a class visible to one loader but not the defining loader of the referencing class. A missing jar is only one of these cases.
- ClassCastException messages that name the same class twice with two loaders are the signature of an isolation problem. They are common in app servers, Quarkus dev/test mode, and plugin systems.
- Classloader leaks follow one pattern: an object reachable from a long-lived loader (or from a thread, ThreadLocal or static registry it owns) references something defined by a short-lived loader. Quarkus dev mode drops the Runtime ClassLoader on every reload. Anything that a persistent loader (base runtime, or parent-first) holds and that points into it will pin the old classes. This is the same mechanism as the LeakDemo.
- A class-initialization deadlock looks like two RUNNABLE threads, not a classic monitor deadlock. Tell learners to grep thread dumps for "waiting on the Class initialization monitor". The deadlock detector did not flag it in either JDK tested.

### Gaps
- The JVMS ch.5 and JLS §12.4 pages could not be fetched (docs.oracle.com blocked). The rules above come from the specification and were checked by experiment and against HotSpot comments. Lesson writers should link https://docs.oracle.com/javase/specs/jvms/se25/html/jvms-5.html and https://docs.oracle.com/javase/specs/jls/se25/html/jls-12.html#jls-12.4.1 and re-read them.
- I did not run Quarkus dev mode. The hot-reload statements come from the Quarkus class-loading reference only.
- The JEP numbers for the AOT cache work (I believe JEP 483 in JDK 24, and JEPs 514/515 in JDK 25) are unverified because openjdk.org was blocked. Only the options were verified, from the man pages.

## 2. Reading bytecode with javap: operand stack, constant pool, descriptors, and what Kotlin 2.4.21 compiles to

### Takeaway
`javap -c -p` shows instructions working on a per-frame operand stack and local-variable slots. `-v` adds the constant pool, the BootstrapMethods table, stack and locals sizes, and the class-file version. Kotlin's properties, companion objects, default arguments, data classes and inline functions all lower to ordinary JVM members. javap shows that JVM shape, not the Kotlin source structure. The Kotlin-only information (nullability, property structure, defaults) is encoded in the `@kotlin.Metadata` annotation.

### Cited Findings
**Operand stack, by example**
- The generated `$Proxy0.greet(String)` compiled to the sequence below (local run: JDK 25, saved with `-Djdk.proxy.ProxyGenerator.saveGeneratedFiles=true`):
  ```
  aload_0
  getfield Proxy.h:InvocationHandler
  aload_0
  getstatic m4:Method
  iconst_1
  anewarray Object
  dup
  iconst_0
  aload_1
  aastore
  invokeinterface InvocationHandler.invoke:(Object;Method;[Object;)Object
  checkcast String
  areturn
  ```
  Its exception table is: `0 25 25 Class java/lang/Error`, `0 25 25 Class java/lang/RuntimeException` (both rethrown with `athrow`), and `0 25 26 any` → `new UndeclaredThrowableException; dup_x1; swap; invokespecial <init>; athrow`
- In a VerifyError dump, `Bytecode: 0000000: 1206 ac` is the raw code: 0x12 = `ldc` with constant-pool index 06, and 0xac = `ireturn`. The verifier reports `stack: { 'java/lang/String' }` at `bci: @2` (local run: BadGen2)

**Constant pool and descriptors**
- `javap -v` shows typed constant-pool entries. Examples: `#7 = InvokeDynamic #0:#8 // #0:applyAsInt:()Ljava/util/function/IntBinaryOperator;`, `#101 = MethodHandle 6:#102 // REF_invokeStatic IndyDemo.add:(II)I`, `#100 = MethodType #18 // (II)I`, and `#112 = Dynamic #5:#113 // #5:invoke:Ljava/lang/Enum$EnumDesc;` (local run: IndyDemo, javac 21)
- Descriptors seen in the runs:
  - `(II)I` (int,int → int)
  - `(Ljava/lang/String;Ljava/lang/String;C)Ljava/lang/String;` (String, String, char → String)
  - `(J)Ljava/lang/String;` (long → String)
  - `()V`
  - `[Ljava/lang/Class;` (array of Class)
  
  The grammar is JVMS §4.3: B C D F I J S Z for the primitives, `L…;` for references, `[` for arrays, V for void (spec, not fetched). Example outputs from local runs
- Class-file major versions observed (local runs):
  - kotlinc 2.4.21 with no `-jvm-target` → 52 (Java 8)
  - kotlinc `-jvm-target 21` → 65
  - JDK 25 javac → 69

**What Kotlin 2.4.21 compiles to** (local run: kotlinc 2.4.21 `-jvm-target 21`, then `javap -p` / `javap -c -p`)
- `data class User(val name: String, val age: Int = 0)` becomes `public final class kt.User` with:
  - `private final` fields
  - `getName()` and `getAge()`
  - `component1()` and `component2()`
  - `copy(String,int)` and `public static copy$default(User,String,int,int,Object)`
  - `toString()`, `hashCode()`, `equals(Object)`
  - a synthetic constructor `User(String,int,int,kotlin.jvm.internal.DefaultConstructorMarker)` that serves the default argument
  
  `toString()` is `getfield name; getfield age; invokedynamic makeConcatWithConstants:(Ljava/lang/String;I)Ljava/lang/String;` (local run)
- Properties (class `Account`):
  - `var balance … private set` → `private long balance` plus a `getBalance()` getter and **no setter method**
  - `val isEmpty get() = …` → `isEmpty()`, with the "is" prefix kept
  - `lateinit var owner` → a **public field** `owner` plus `getOwner()` and `setOwner()`
  - all methods are `final` (local run)
- The companion object becomes a nested `Account$Companion` class plus a `public static final Account$Companion Companion` field on `Account`:
  - `const val MAX` → `public static final long MAX` on `Account`, so Java can read it as a constant
  - `val DEFAULT_CURRENCY` → a `private static final String DEFAULT_CURRENCY` on `Account`, a `getDEFAULT_CURRENCY()` on the Companion, and a synthetic `access$getDEFAULT_CURRENCY$cp()`
  - `@JvmStatic fun open()` → both `public static final Account open()` on `Account` and `open()` on the Companion
  - a plain `fun create()` → only on the Companion
  
  (local run)
- `object Registry` → `public static final Registry INSTANCE`, a private constructor, and a `static {}` initializer (local run)
- Top-level functions → static methods on `ShapesKt`. Default arguments generate `public static greet$default(String,String,char,int,Object)`. Its bytecode tests mask bits: `iload_3; iconst_2; iand; ifeq …; ldc "Hello"; astore_1` and `iload_3; iconst_4; iand; ifeq …; bipush 33 ('!'); istore_2`, then calls `greet` (local run)
- Every non-null parameter of a public function gets `Intrinsics.checkNotNullParameter(param, "name")` at entry (local run)
- String templates compile to `invokedynamic makeConcatWithConstants` with `-jvm-target 21` and to `new StringBuilder … append … toString` with the default 1.8 target (local run). The Kotlin docs say: "Kotlin 1.5.20 compiles string concatenations into dynamic invocations (`invokedynamic`) on JVM 9+ targets… it uses `StringConcatFactory.makeConcatWithConstants()`… To switch back… add the compiler option `-Xstring-concat=inline`" — [What's new in Kotlin 1.5.20](https://kotlinlang.org/docs/whatsnew1520.html)
- `inline fun measure(block: () -> T)` is still emitted as a static method (`public static final <T> T measure(Function0)`). At the call site, though, its body (`System.nanoTime()`, the println) is copied into `useAll()` and the lambda passed to it is inlined, so no Function0 is allocated. The non-inline lambda `val adder: (Int) -> Int = { it + 1 }` becomes `invokedynamic … LambdaMetafactory.metafactory` producing a `kotlin.jvm.functions.Function1`, with its body in `private static final int useAll$lambda$0(int)`. `typeName<User>()` with `reified T` compiles to `ldc class kt/User` (local run)
- "In Kotlin 2.0.0, invokedynamic has become the default method for lambda generation." Listed limitations: such a lambda "is not serializable", the experimental `reflect()` doesn't support it, and `toString()` is less readable — [What's new in Kotlin 2.0.0](https://kotlinlang.org/docs/whatsnew20.html)
- `javap -v User.class` shows `RuntimeVisibleAnnotations: kotlin.Metadata(mv=[2,4,0], k=1, xi=48, d1=[…protobuf-encoded…], d2=["Lkt/User;","","name","","age",…])`. This is where Kotlin keeps its own view of the class (local run)
- Kotlin classes and members are final by default. `class FinalService { fun work() }` → `public final class kt.FinalService` with `public final java.lang.String work()`, while `open class Service` has non-final members (local run). The all-open compiler plugin "makes classes and their members open at compile time without requiring the open keyword", and it also honours meta-annotations — [All-open compiler plugin](https://kotlinlang.org/docs/all-open-plugin.html). Compiling with `-Xplugin=allopen-compiler-plugin.jar -P plugin:org.jetbrains.kotlin.allopen:annotation=kto.OpenForProxy` produced `public class kto.PaymentService` with non-final `charge(long)` and `getFee()`, while the unannotated `PlainService` stayed final (local run)

### Inferences
- "javap shows the Kotlin source" is false. It shows getters, setters, `$default` bridges, `Companion` and `INSTANCE` holders, and the `@Metadata` blob. Teach learners to translate each back to the Kotlin construct, and to expect public fields from `lateinit` and `@JvmField`.
- The kotlinc 2.4.21 CLI defaults to class-file version 52 (Java 8), and then string concatenation falls back to StringBuilder. A Gradle build normally derives the JVM target from the toolchain, so lesson demos should pass `-jvm-target` explicitly. (The Gradle default was not verified here.)
- Calls on a Kotlin companion from Java go through `Account.Companion.create(…)` unless the function is `@JvmStatic`. That explains the duplicated `open()` in the bytecode.

### Gaps
- JVMS §4 (class-file format, descriptors) was not fetched; the descriptor summary comes from the specification.
- I did not decode the `d1` protobuf of `@kotlin.Metadata`. The kotlin-metadata-jvm library can do that, but it was not tested here.

## 3. invokedynamic and bootstrap methods: lambdas (LambdaMetafactory), string concatenation (JEP 280), records (ObjectMethods), pattern switches, and condy

### Takeaway
`invokedynamic` defers linking a call site to a bootstrap method named in the BootstrapMethods attribute. The bootstrap method runs once per call site and returns a CallSite. javac uses it for:
- lambdas and method references (LambdaMetafactory, Java 8)
- string concatenation (StringConcatFactory, Java 9 / JEP 280)
- record `toString`/`equals`/`hashCode` (ObjectMethods, Java 16)
- pattern switches (SwitchBootstraps)

javac also emits **condy** (`CONSTANT_Dynamic`, resolved through ConstantBootstraps) for enum-constant labels in pattern switches. Since JDK 24 the JDK's own lambda spinner emits bytecode with the ClassFile API.

### Cited Findings
- `LambdaMetafactory` is `@since 1.8` — [LambdaMetafactory.java jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/invoke/LambdaMetafactory.java). `StringConcatFactory` is `@since 9` — [StringConcatFactory.java jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/invoke/StringConcatFactory.java). `java.lang.runtime.ObjectMethods` is `@since 16` — [ObjectMethods.java jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/runtime/ObjectMethods.java). `ConstantBootstraps` is `@since 11` — [ConstantBootstraps.java jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/invoke/ConstantBootstraps.java)
- Method reference `IndyDemo::add` → `invokedynamic #0:applyAsInt:()Ljava/util/function/IntBinaryOperator;`. The bootstrap method is `REF_invokeStatic java/lang/invoke/LambdaMetafactory.metafactory:(Lookup;String;MethodType;MethodType;MethodHandle;MethodType;)CallSite` with arguments `(II)I`, `REF_invokeStatic IndyDemo.add:(II)I`, `(II)I` (local run: javac 21)
- Capturing lambda `x -> x + base` → `invokedynamic #1:applyAsInt:(I)Ljava/util/function/IntUnaryOperator;`. The call-site type's parameter is the **captured** int, and the body is `private static int lambda$main$0(int, int)` with the captured value first (local run)
- `"sum=" + a + ", plus=" + b` → `invokedynamic makeConcatWithConstants:(II)Ljava/lang/String;` with recipe argument `sum=\u0001, plus=\u0001`, where `\u0001` marks argument slots (local run)
- `record Point(int x, int y)`: `toString`, `hashCode` and `equals` are each `aload_0 [aload_1] invokedynamic #0:<name>:(…)` against bootstrap `java/lang/runtime/ObjectMethods.bootstrap`. The static arguments are `IndyDemo$Point`, `"x;y"`, `REF_getField IndyDemo$Point.x:I` and `REF_getField IndyDemo$Point.y:I` (local run)
- Pattern switch over a sealed interface → `invokedynamic typeSwitch:(Ljava/lang/Object;I)I` via `java/lang/runtime/SwitchBootstraps.typeSwitch`. Its static arguments include `IndyDemo$Circle`, `IndyDemo$Square`, and a **condy** entry `#5:invoke:Ljava/lang/Enum$EnumDesc;`. The two condy bootstraps (#5 and #6) are `ConstantBootstraps.invoke`, applied to `Enum$EnumDesc.of` and `ClassDesc.of`, so the `case Square.UNIT` label is built lazily as a constant (local run: javac 21.0.12.1)
- Non-capturing lambdas are linked to a singleton. `InnerClassLambdaMetafactory` keeps a `LAMBDA_INSTANCE$` static field and returns `new ConstantCallSite(caller.findStaticGetter(innerClass, LAMBDA_INSTANCE_FIELD, …))`. Generated classes are named `<target>$$Lambda` and defined as hidden nestmates — [InnerClassLambdaMetafactory.java jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/invoke/InnerClassLambdaMetafactory.java)
- `InnerClassLambdaMetafactory` imports `jdk.internal.org.objectweb.asm.*` at jdk-22-ga and jdk-23-ga, and `java.lang.classfile.ClassBuilder` / `ClassFile` at jdk-24-ga and jdk-25-ga — [jdk-23-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-23-ga/src/java.base/share/classes/java/lang/invoke/InnerClassLambdaMetafactory.java), [jdk-24-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-24-ga/src/java.base/share/classes/java/lang/invoke/InnerClassLambdaMetafactory.java)
- Kotlin 2.4.21 also emits LambdaMetafactory indy for non-inline lambdas, and StringConcatFactory indy when targeting 9+ (local run; see section 2)

### Inferences
- Explain indy as "a call site whose target is decided by library code the first time it runs". The bytecode carries only a name, a type and static arguments, so the strategy can change between JDK versions without recompiling. That is why string concatenation got faster on newer JDKs with the same class files.
- Condy is less familiar than indy, but javac 21 already emits it for enum labels in pattern switches. That is a concrete, gradable javap exercise.

### Gaps
- JEP 280 (Indify String Concatenation) and JEP 309 (condy, JDK 11) pages were not fetched. Their numbers and titles come from memory; the `@since` tags above are what was verified.

## 4. JDK dynamic proxies in depth (java.lang.reflect.Proxy)

### Takeaway
`Proxy.newProxyInstance(loader, interfaces, handler)` generates (or reuses from a cache) a `public final` class named `$ProxyN` that extends `java.lang.reflect.Proxy` and implements exactly the given interfaces. Each method stores its `Method` in a static field, boxes the arguments into `Object[]`, and calls `h.invoke(this, method, args)`. Only interfaces can be proxied. `equals`, `hashCode` and `toString` go to the handler, but `getClass` and other Object methods do not. Default methods can be run with `InvocationHandler.invokeDefault` (JDK 16+). Self-calls inside the target bypass the proxy. Checked exceptions not declared by the interface method come out wrapped in `UndeclaredThrowableException`. On JDK 9+ the proxy class lives in a per-loader dynamic module `jdk.proxyN`, unless a package-private interface forces it into that interface's package.

### Cited Findings
**Specification (Proxy Javadoc, jdk-25-ga)** — [Proxy.java jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/reflect/Proxy.java)
- "A *proxy class* is a class created at runtime that implements a specified list of interfaces… A method invocation on a proxy instance through one of its proxy interfaces will be dispatched to the invoke method of the instance's invocation handler, passing the proxy instance, a `java.lang.reflect.Method` object… and an array of type Object containing the arguments."
- Proxy-class properties:
  - "The unqualified name of a proxy class is unspecified. The space of class names that begin with the string "$Proxy" should be, however, reserved for proxy classes"
  - "A proxy class is *final and non-abstract*"
  - it "extends java.lang.reflect.Proxy"
  - it "implements exactly the interfaces specified at its creation, in the same order"
  - its ProtectionDomain "is the same as that of system classes loaded by the bootstrap class loader"
  - `Proxy.isProxyClass` identifies it
- "An invocation of the `hashCode`, `equals`, or `toString` methods declared in `java.lang.Object` on a proxy instance will be encoded and dispatched to the invocation handler's invoke method… The declaring class of the Method object passed to invoke will be `java.lang.Object`. Other public methods of a proxy instance inherited from `java.lang.Object` are not overridden by a proxy class."
- Duplicate methods across interfaces: the handler receives "the Method object for the method in the foremost interface that contains the method… regardless of the reference type through which the method invocation occurred". The public non-final methods of Object "logically precede all of the proxy interfaces". If `invoke` throws a checked exception "not assignable to any of the exception types declared by the method… then an unchecked `UndeclaredThrowableException` will be thrown".
- `newProxyInstance` throws `IllegalArgumentException` when:
  - an array element is not a "non-hidden and non-sealed" interface (classes and primitives fail)
  - an interface appears twice
  - an interface is not visible by name through the loader (`Class.forName(i.getName(), false, cl) == i`)
  - a type referenced by the public method signatures is not visible
  - non-public interfaces sit in different packages or modules
  - same-signature methods have incompatible return types
  - there are more than 65535 interfaces
- Module membership:
  - If all interfaces are public and in exported packages: "the proxy class is *public* in an unconditionally exported but non-open package. The name of the package and the module are unspecified."
  - If any interface is non-public: "the proxy class is *non-public* in the package and module of the non-public interfaces".
  - If any interface is in a non-exported, non-open package and all are public: the class goes into a non-exported package of a *dynamic module*.
  - "A proxy class defined in a dynamic module is encapsulated and not accessible to any module. Calling Constructor.newInstance on a proxy class in a dynamic module will throw IllegalAccessException; Proxy.newProxyInstance method should be used instead."
- `Proxy.getProxyClass` is `@Deprecated`: "Proxy classes generated in a named module are encapsulated and not accessible to code outside its module… Use newProxyInstance… instead."

**Implementation (jdk-25-ga source)**
- Caching:
  - constructors are cached in `private static final ClassLoaderValue<Constructor<?>> proxyCache`, keyed per loader by the interface list (`proxyCache.sub(intf)` / `proxyCache.sub(intfs).computeIfAbsent(…)`)
  - a `reverseProxyCache` backs `isProxyClass`
  - names come from `proxyClassNamePrefix = "$Proxy"` plus a counter
  - each loader gets one dynamic module: "Define a dynamic module with a package named $MODULE which is unconditionally exported and another package named com.sun.proxy.$MODULE which is encapsulated. Each class loader will have one dynamic module", with `mn = "jdk.proxy" + counter.incrementAndGet()`
  - a `ClassValue<ConcurrentHashMap<Method, MethodHandle>> DEFAULT_METHODS_MAP` caches the method handles behind `invokeDefault`
  - `-Djdk.proxy.debug` enables debug output
  
  — [Proxy.java jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/reflect/Proxy.java)
- `ProxyGenerator` reads `Boolean.getBoolean("jdk.proxy.ProxyGenerator.saveGeneratedFiles")`. It always adds the Object methods first (`addProxyMethod(…OBJECT_HASH_CODE_METHOD…, "m0")`), stores each Method in a `private static final` field `m<N>`, and makes each proxy method `ACC_PUBLIC | ACC_FINAL` — [ProxyGenerator.java jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/reflect/ProxyGenerator.java)
- `ProxyGenerator` imports `jdk.internal.org.objectweb.asm.ClassWriter` at jdk-21-ga and jdk-22-ga, but `java.lang.classfile.*` from jdk-23-ga onward. So JDK proxies have been generated with the ClassFile API since JDK 23 — [ProxyGenerator jdk-21-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-21-ga/src/java.base/share/classes/java/lang/reflect/ProxyGenerator.java), [jdk-23-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-23-ga/src/java.base/share/classes/java/lang/reflect/ProxyGenerator.java), [jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/reflect/ProxyGenerator.java)

**invokeDefault (JDK 16)** — [InvocationHandler.java jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/reflect/InvocationHandler.java)
- `public static Object invokeDefault(Object proxy, Method method, Object... args) throws Throwable` is `@since 16` and `@CallerSensitive`. (`InvocationHandler` itself is `@since 1.3`.)
- It throws `IllegalArgumentException` if:
  - `proxy` is not a proxy instance
  - the method "is not a default method declared in a proxy interface of the proxy class and not inherited from any of its superinterfaces"
  - the method "is overridden directly or indirectly by the proxy interfaces and the method reference to the named method never resolves to the given method"
  - the argument count or types mismatch
  
  It throws `IllegalAccessException` "if the declaring class of the specified default method is inaccessible to the caller class".

**Observed behaviour** (local run: ProxyDemo; identical on JDK 21.0.12.1, 25.0.4.1 and 27.0.1.0.3 except hash codes)
- For `Proxy.newProxyInstance(app loader, {Greeter}, h)`, `pc` is the class of the returned proxy:

  | Property | Observed value |
  |---|---|
  | `pc.getName()` | `jdk.proxy1.$Proxy0` |
  | superclass | `java.lang.reflect.Proxy` |
  | interfaces | `[interface demo.ProxyDemo$Greeter]` |
  | modifiers | `public final` |
  | module | `module jdk.proxy1` |
  | `isProxyClass` | `true` |
  | `isSynthetic` / `isHidden` | `false` / `false` |
  | declared fields | `private static final Method m0 … m4` |
  | declared methods | `private static proxyClassLookup`, `public final equals`, `greet`, `greetTwice`, `hashCode`, `toString` |
- Caching:
  - a second proxy with the same loader and `{Greeter}` gets the same class (`true`)
  - `{Greeter, Auditable}` → `jdk.proxy1.$Proxy1`, but `{Auditable, Greeter}` → `jdk.proxy1.$Proxy2`, so order matters: `same? false`
- Calling `toString(), hashCode(), equals(g), getClass()` made the handler see `[Object.toString, Object.hashCode, Object.equals]`. `getClass()` was not dispatched.
- **Self-invocation pitfall.** The target `GreeterImpl.greetTwice` calls `this.greet(name)` twice. `proxy.greetTwice("Ana")` returned `Hello Ana | Hello Ana`, but the handler saw only `[Greeter.greetTwice]`: the two inner `greet()` calls bypassed the proxy.
- **invokeDefault.** A target-less handler that calls `InvocationHandler.invokeDefault(proxy, m, args)` for `m.isDefault()` returned `Hi Bo / Hi Bo` for the default `greetTwice`. The handler ran **3** times: once for the default method, and twice for the `greet` calls that re-entered *through the proxy*, because the default body's `this` is the proxy.
- Calling `invokeDefault` on an abstract method → `java.lang.IllegalArgumentException: "public abstract java.lang.String demo.ProxyDemo$Greeter.greet(java.lang.String)" is not a default method`.
- Checked exceptions:
  - a handler that throws `IOException` for `Runnable.run()` → `UndeclaredThrowableException` with cause `java.io.IOException: boom`
  - for an interface method declared `throws IOException`, the IOException passes through unchanged
- A naive handler `(p, m, a) -> m.invoke(target, a)` whose target throws `IOException` → `UndeclaredThrowableException -> cause InvocationTargetException -> cause java.io.IOException: from target`. Handlers must unwrap `InvocationTargetException.getCause()`.
- Proxying a class → `java.lang.IllegalArgumentException: demo.ProxyDemo$GreeterImpl is not an interface`.
- A proxy of `Runnable` with a `null` (bootstrap) loader → `jdk.proxy2.$Proxy5 in module jdk.proxy2`. A proxy of `Comparator` with the app loader → `jdk.proxy1.$Proxy7 in module jdk.proxy1`, so there is one dynamic module per loader. A proxy of a package-private interface → `demo.$Proxy8 modifiers=final`, which is non-public and in the interface's package.

**Performance (indicative)**
- JMH 1.37 on Temurin 25+36, 4 vCPU VM, 1 fork, 3×1 s warmup, 5×1 s measurement, average time per call to `add(3,4)` (local run: ProxyBench). The JDK proxy handler forwarded with `m.invoke(target, a)`, and the Byte Buddy subclass used `@SuperCall`. The error bars are wide (shared VM), but the ordering is the useful part:

  | Benchmark | ns/op |
  |---|---|
  | direct | 0.828 ± 0.467 |
  | Byte Buddy subclass with `@SuperCall` | 0.882 ± 0.622 |
  | JDK proxy | 4.328 ± 4.139 |
  | `Method.invoke` with boxing | 11.798 ± 4.258 |

### Inferences
- The proxy is a separate object. Calls arrive at it only through references to the proxy, so anything the target does to `this` is invisible to the handler. This is exactly Spring's self-invocation problem (section 5). With `invokeDefault`, by contrast, the default method's `this` *is* the proxy, so its inner calls *are* intercepted.
- A handler that forwards `equals` to the target breaks reflexivity: `proxy.equals(proxy)` calls `target.equals(proxy)`, which is false. Decorators should handle `equals` and `hashCode` by proxy identity, or delegate them deliberately. The lab solution does the former.
- Per-call cost is a few nanoseconds. That is irrelevant next to a database call or network hop, but it matters for tight loops. The classes themselves are cached per (loader, ordered interface list), so building many proxies with the same interfaces does not generate new classes.
- Kotlin's final-by-default does not affect JDK proxies, because they only need interfaces. It hits class-based proxies (CGLIB, Byte Buddy subclasses, ArC, Hibernate).
- A retry decorator should not retry Object methods or default-method shells (retry the inner abstract calls instead). It should rethrow the original cause, not `UndeclaredThrowableException` or `InvocationTargetException`. These are the graded behaviours in Lab A.

### Gaps
- I found no official statement on per-call proxy overhead. The numbers above are one noisy JMH run and should be presented as indicative only.
- The `Proxy` Javadoc does not specify the `jdk.proxyN` module naming, and the implementation could change.

## 5. Bytecode-generated subclass proxies and the frameworks: Byte Buddy 1.18.x, cglib, Spring AOP (JDK vs CGLIB), Quarkus ArC, Hibernate

### Takeaway
Subclass proxies can wrap classes, but only overridable members: no `final` classes or methods, no `private` methods, and constructors run as normal unless the framework bypasses them (Objenesis). The deciding question for self-invocation is *where the target state lives*:
- **Spring AOP** (JDK or CGLIB): the proxy forwards to a separate target bean, so `this.foo()` is not advised.
- **Quarkus ArC**: generates an intercepted subclass (`Foo_Subclass`) at build time, and self-interception is documented to work.
- **Byte Buddy**: can build either model.

cglib is unmaintained, and Spring ships its own patched copy. Hibernate creates lazy proxies with Byte Buddy, which is why entities must not be final.

### Cited Findings
**Byte Buddy 1.18.x**
- Release notes:
  - latest is "1. November 2026: version 1.18.17"
  - 1.18.15 (13 Oct 2026): "Update ASM to version 9.11 and add support for Java 28"
  - 1.18.9 (1 Jun 2026): "Disable use of Unsafe by default when Java 25or newer is discovered"
  - 1.18.10 (3 Jun 2026): "Delay change of default for unsage use to Java 26"
  - 1.18.7 (1 Mar 2026): "Introduce new versioning concept with *-jdk5* suffix for backwards-compatible jar and Java 8 baseline for regular jar"
  - 1.18.0 (11 Nov 2025): "Add support for `module-info` class files"
  - 1.16.0 (17 Jan 2025): "Include support for JDK Class File API"
  
  — [release-notes.md](https://raw.githubusercontent.com/raphw/byte-buddy/master/release-notes.md)
- README: "As of 1.17.0, support will extend to new Java versions unless previously unknown class file features are discovered. This is possible through Byte Buddy's support of the Class File API". In the compatibility table, 1.18.7 supports Java 25+ with a minimum JVM of 8, and 1.18.7-jdk5 has a minimum of 5. Byte Buddy "is not limited to implementing interfaces for the creation of runtime proxies" — [README.md](https://raw.githubusercontent.com/raphw/byte-buddy/master/README.md). Maven Central lists `1.18.17` and `1.18.17-jdk5` as the newest — [maven-metadata.xml](https://maven-central.storage-download.googleapis.com/maven2/net/bytebuddy/byte-buddy/maven-metadata.xml)
- rebase vs redefine (Javadoc): `rebase` "Rebases the given type where any intercepted method that is declared by the redefined type is preserved within the rebased type's class such that the class's original can be invoked from the new method implementations. Rebasing a type can be seen similarly to creating a subclass where the subclass is later merged with the original class file." For `redefine`: "When a user redefines a class with the purpose of reloading this class using a ClassReloadingStrategy, it is important that no fields or methods are added to the redefined class. Note that some Implementations implicitly add fields or methods." — [ByteBuddy.java](https://raw.githubusercontent.com/raphw/byte-buddy/master/byte-buddy-dep/src/main/java/net/bytebuddy/ByteBuddy.java)
- README examples:
  - `new ByteBuddy().subclass(Object.class).method(named("toString")).intercept(FixedValue.value("Hello World!"))`
  - `MethodDelegation.to(...)`, "which allows for implementing any method in plain Java"
  - `@SuperCall` "injects proxy instances that allow for an invocation of a non-abstract super method"
  - `AgentBuilder.Default().type(nameEndsWith("Timed")).transform(... builder.method(any()).intercept(MethodDelegation.to(TimingInterceptor.class))).installOn(instrumentation)`
  - `Advice` for agents
  
  — [README.md](https://raw.githubusercontent.com/raphw/byte-buddy/master/README.md)
- Observed with Byte Buddy 1.18.17 (local run: BBDemo; same on JDK 21, 25 and 27):
  - subclass proxy name `bb.BBDemo$OrderService$ByteBuddy$gESVFJpE` (random suffix per run), superclass `OrderService`, `public`
  - declared methods `[audit, audit$accessor$YqAKt7K4, place, place$accessor$YqAKt7K4]`: the `final id()` was not overridden, and `id()` still returned "final-method"
  - **Instance-is-subclass with `@SuperCall`**: `place("A1")` (which calls `this.audit`) logged `[timed audit ok, timed place ok]`, so the self-invocation **was** intercepted
  - **Forwarding to a separate target** (Spring-style): `place("B2")` logged only `[forwarded place]`, so the self-invocation **was not** intercepted
  - Subclassing the Kotlin `kt.FinalService` → `IllegalArgumentException: Cannot subclass primitive, array or final types: class kt.FinalService`
  - `rebase(Clock).name("bb.RebasedClock")` intercepting `now` → methods `[final now$original$ksBLA6nx$accessor$MjXCb57x, private now$original$ksBLA6nx, public now]`. `redefine(...)` → `[public now]`, with the original body discarded

**cglib status**
- The cglib README: "IMPORTANT NOTE: cglib is unmaintained and does not work well (or possibly at all?) in newer JDKs, particularly JDK17+. If you need to support newer JDKs, we will accept well-tested well-thought-out patches... but you'll probably have better luck migrating to something like ByteBuddy." — [cglib README](https://raw.githubusercontent.com/cglib/cglib/master/README.md)
- Spring's copy: `org.springframework.cglib` is "Spring's repackaging of CGLIB 3.3 (with Spring-specific patches; for internal use only)… avoids any potential conflicts with dependencies on CGLIB at the application level" — [package-info.java](https://raw.githubusercontent.com/spring-projects/spring-framework/main/spring-core/src/main/java/org/springframework/cglib/package-info.java). spring-core also repackages Objenesis (`objenesisVersion = "3.5"`, task `objenesisRepackJar`) — [spring-core.gradle](https://raw.githubusercontent.com/spring-projects/spring-framework/main/spring-core/spring-core.gradle)

**Spring AOP (Framework 6/7)** — [proxying.adoc (main)](https://raw.githubusercontent.com/spring-projects/spring-framework/main/framework-docs/modules/ROOT/pages/core/aop/proxying.adoc)
- "Spring AOP uses either JDK dynamic proxies or CGLIB… (repackaged into spring-core). If the target object to be proxied implements at least one interface, a JDK dynamic proxy is used, and all of the interfaces implemented by the target type are proxied. If the target object does not implement any interfaces, a CGLIB proxy is created which is a runtime-generated subclass of the target type."
- CGLIB caveats, verbatim:
  - "`final` classes cannot be proxied"
  - "`final` methods cannot be advised"
  - "`private` methods cannot be advised"
  - non-visible methods, "for example, package-private methods in a parent class from a different package – cannot be advised"
  - "The constructor of your proxied object will not be called twice, since the CGLIB proxy instance is created through Objenesis. However, if your JVM does not allow for constructor bypassing, you might see double invocations"
  - module-system limits: "you cannot create a CGLIB proxy for a class from the java.lang package when deploying on the module path"
- Historical contrast: the Spring 3.2 reference said "The constructor of your proxied object will be called twice… For each proxied instance, two objects are created: the actual proxied object and an instance of the subclass that implements the advice" — [aop.xml (3.2.x)](https://raw.githubusercontent.com/spring-projects/spring-framework/3.2.x/src/reference/docbook/aop.xml)
- Forcing proxy types:
  - `proxy-target-class="true"`, or `proxyTargetClass` on `@EnableAspectJAutoProxy` / `@EnableTransactionManagement`, which "are collapsed into a single unified auto-proxy creator… applying the *strongest* proxy settings"
  - "As of 7.0, this applies to individual proxy processors as well, for example `@EnableAsync`"
  - "While the core framework suggests interface-based proxies by default, Spring Boot may… enable class-based proxies by default"
  - "As of 7.0, forcing a specific proxy type for individual beans is possible through the `@Proxyable` annotation… `@Proxyable(INTERFACES)` or `@Proxyable(TARGET_CLASS)`… `@Proxyable(interfaces=...)`"
- `@Proxyable` is `@since 7.0`, `ProxyType value() default ProxyType.DEFAULT`, "Only actually applying in case of a bean actually getting auto-proxied in the first place" — [Proxyable.java](https://raw.githubusercontent.com/spring-projects/spring-framework/main/spring-context/src/main/java/org/springframework/context/annotation/Proxyable.java)
- Spring Boot's `AopAutoConfiguration`: "The proxyTargetClass attribute will be true, by default, but can be overridden by specifying `spring.aop.proxy-target-class=false`" (`@ConditionalOnBooleanProperty(name = "spring.aop.proxy-target-class", matchIfMissing = true)` → `@EnableAspectJAutoProxy(proxyTargetClass = true)`). This is the same in 3.5.x and on main (4.2.0-SNAPSHOT) — [3.5.x](https://raw.githubusercontent.com/spring-projects/spring-boot/3.5.x/spring-boot-project/spring-boot-autoconfigure/src/main/java/org/springframework/boot/autoconfigure/aop/AopAutoConfiguration.java), [main](https://raw.githubusercontent.com/spring-projects/spring-boot/main/core/spring-boot-autoconfigure/src/main/java/org/springframework/boot/autoconfigure/aop/AopAutoConfiguration.java)
- Self-invocation: "once the call has finally reached the target object… any method calls that it may make on itself, such as `this.bar()`… are going to be invoked against the this reference, and not the proxy… self invocation via an explicit or implicit this reference will bypass the advice". The documented options are:
  - avoid self invocation ("the best approach")
  - inject a self reference
  - `AopContext.currentProxy()`, which is "highly discouraged" and requires the ProxyFactory to expose the proxy
  
  — [proxying.adoc](https://raw.githubusercontent.com/spring-projects/spring-framework/main/framework-docs/modules/ROOT/pages/core/aop/proxying.adoc)
- Self injection: "`@Autowired` also considers self references for injection… self injection is a fallback mechanism… use self references as a last resort only – for example, for calling other methods on the same instance through the bean's transactional proxy… Another alternative is to use `@Resource`" — [autowired.adoc](https://raw.githubusercontent.com/spring-projects/spring-framework/main/framework-docs/modules/ROOT/pages/core/beans/annotation-config/autowired.adoc)
- `@Transactional`: "In proxy mode (which is the default), only external method calls coming in through the proxy are intercepted. This means that self-invocation… does not lead to an actual transaction at runtime even if the invoked method is marked with `@Transactional`. Also, the proxy must be fully initialized… you should not rely on this feature in your initialization code — for example, in a `@PostConstruct` method." Use "AspectJ mode… if you expect self-invocations to be wrapped with transactions as well. In this case, there is no proxy in the first place". On visibility: "As of 6.0, protected or package-visible methods can also be made transactional for class-based proxies by default. Note that transactional methods in interface-based proxies must always be public and defined in the proxied interface" — [annotations.adoc](https://raw.githubusercontent.com/spring-projects/spring-framework/main/framework-docs/modules/ROOT/pages/data-access/transaction/declarative/annotations.adoc)
- Versions on Maven Central (checked 2026-11-07):
  - spring-core release tag `7.1.0-RC2`; the newest 7.0.x is 7.0.10
  - Spring Framework `main` builds `7.1.0-SNAPSHOT`
  - spring-boot release tag `4.2.0-RC2`, with 4.1.2 in the 4.1 line
  
  — [spring-core metadata](https://maven-central.storage-download.googleapis.com/maven2/org/springframework/spring-core/maven-metadata.xml), [gradle.properties](https://raw.githubusercontent.com/spring-projects/spring-framework/main/gradle.properties), [spring-boot metadata](https://maven-central.storage-download.googleapis.com/maven2/org/springframework/boot/spring-boot/maven-metadata.xml)
- Kotlin + Spring: "The kotlin-spring compiler plugin… is a preconfigured wrapper around the all-open plugin". It opens classes annotated `@Component`, `@Async`, `@Transactional`, `@Cacheable` or `@SpringBootTest`, plus `@Configuration`, `@Controller`, `@RestController`, `@Service` and `@Repository` through the `@Component` meta-annotation. "If you generate a project template using start.spring.io, the kotlin-spring plugin is enabled by default" — [kotlin-spring plugin](https://kotlinlang.org/docs/kotlin-spring-plugin.html)

**Quarkus ArC (build-time CDI)**
- Client proxies: "A client proxy is basically an object that delegates all method invocations to a target bean instance. It's a container construct that implements `io.quarkus.arc.ClientProxy` and extends the bean class." Example: `class Translator_ClientProxy extends Translator`. "Client proxies only delegate method invocations. So never read or write a field of a normal scoped bean". `@Singleton` has no client proxy — [cdi.adoc](https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/cdi.adoc)
- The generators confirm the naming:
  - `SUBCLASS_SUFFIX = "_Subclass"`, with the comment "Foo_Subclass extends Foo implements Subclass"
  - `CLIENT_PROXY_SUFFIX = "_ClientProxy"`, with "Foo_ClientProxy extends Foo implements ClientProxy"
  - ArC's processor generates them with Gizmo 2 (`io.quarkus.gizmo2` imports)
  
  — [SubclassGenerator.java](https://raw.githubusercontent.com/quarkusio/quarkus/main/independent-projects/arc/processor/src/main/java/io/quarkus/arc/processor/SubclassGenerator.java), [ClientProxyGenerator.java](https://raw.githubusercontent.com/quarkusio/quarkus/main/independent-projects/arc/processor/src/main/java/io/quarkus/arc/processor/ClientProxyGenerator.java)
- Self-invocation: "Quarkus supports what is known as intercepted self-invocation or just self-interception - a scenario where CDI bean invokes its own intercepted method from within another method while triggering any associated interceptors. This is a non-standard feature as CDI specification doesn't define whether self-interception should work or not." With `@Transactional void doSomething()` and `void doSomethingElse() { doSomething(); }`, "any code calling the `doSomething()` method triggers interception… regardless of whether the invocation originated directly from the MyService bean… or from some other bean" — [cdi-reference.adoc](https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/cdi-reference.adoc)
- Final classes and methods: "In normal CDI, classes that are marked as final and / or have final methods are not eligible for proxy creation… very common when trying to use CDI with alternative JVM languages like Kotlin… Quarkus however, can overcome these limitations when `quarkus.arc.transform-unproxyable-classes` is set to `true` (which is the default value)." — [cdi-reference.adoc](https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/cdi-reference.adoc)
- Static methods: "It's possible to annotate a non-private static method with an interceptor binding". The limitations: "Only method-level bindings are considered", "Private static methods are never intercepted", and "`InvocationContext#getTarget()` returns null" — [cdi-reference.adoc](https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/cdi-reference.adoc)
- Private members: "if Quarkus DI needs to access a private member it, *has to use reflection*. That's why Quarkus users are encouraged *not to use private members* in their beans", and package-private is recommended — [cdi-reference.adoc](https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/cdi-reference.adoc)
- `InterceptionProxy` for producers: "at build time, a subclass of MyClass is generated that does the interception and forwarding". The class "should not be final, should not have non-private final methods, and should have a non-private zero-parameter constructor". It "only supports `@AroundInvoke` interceptors declared on interceptor classes" — [cdi-reference.adoc](https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/cdi-reference.adoc)
- Laziness: "injecting a normal scoped bean will not suffice because a client proxy is injected instead of a contextual instance"; the first method invocation creates the bean. Also, "CDI Portable Extensions cannot be supported" because of the build-time design — [cdi-reference.adoc](https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/cdi-reference.adoc)
- The Quarkus Kotlin guide still configures all-open for `jakarta.ws.rs.Path`, says the same is needed for `jakarta.enterprise.context.ApplicationScoped` "and any class that needs to have a dynamic proxy created at runtime, like a JPA Entity class", and adds "Future versions of Quarkus will configure the Kotlin compiler plugin in a way that will make it unnecessary" — [kotlin.adoc](https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/kotlin.adoc)
- Maven Central lists quarkus-core 3.40.1.1 as the newest 3.x, and 4.0.0.Beta1–Beta3 as the newest overall — [quarkus-core metadata](https://maven-central.storage-download.googleapis.com/maven2/io/quarkus/quarkus-core/maven-metadata.xml)

**Hibernate lazy proxies**
- "A proxy is an object that masquerades as a real entity or collection, but doesn't actually hold any state… When you call a method of the proxy, Hibernate will detect the call and fetch the state". The gotchas:
  - after the session ends "its methods throw the hated `LazyInitializationException`"
  - for polymorphic associations "operations like instanceof and typecasts do not work correctly when applied to a proxy"; `@ConcreteProxy` "solves gotcha 2, but at the cost of performance"
  - N+1 selects
  
  — [Interacting.adoc](https://raw.githubusercontent.com/hibernate/hibernate-orm/main/documentation/src/main/asciidoc/introduction/Interacting.adoc)
- "An entity must: be a non-`final` class, with a non-`private` constructor with no parameters". Many-valued sides "must be declared using an interface type like Set or List, and never using a concrete type", because Hibernate proxies them. "Your implementation of equals() must be written to accommodate the possibility that the object passed to the equals() might be a proxy" — [Entities.adoc](https://raw.githubusercontent.com/hibernate/hibernate-orm/main/documentation/src/main/asciidoc/introduction/Entities.adoc)
- hibernate-core on main contains `org.hibernate.proxy.pojo.bytebuddy.ByteBuddyProxyFactory` (HTTP 200) — [ByteBuddyProxyFactory.java](https://raw.githubusercontent.com/hibernate/hibernate-orm/main/hibernate-core/src/main/java/org/hibernate/proxy/pojo/bytebuddy/ByteBuddyProxyFactory.java). The bytecode provider is discovered through `ServiceLoader`, the `"bytebuddy"` name constant is `@Deprecated(forRemoval = true, since = "6.2")`, and without a service it falls back to a "no-op" `BytecodeProviderImpl` — [BytecodeProviderInitiator.java](https://raw.githubusercontent.com/hibernate/hibernate-orm/main/hibernate-core/src/main/java/org/hibernate/bytecode/internal/BytecodeProviderInitiator.java). The main branch is `8.1.0-SNAPSHOT` — [version.properties](https://raw.githubusercontent.com/hibernate/hibernate-orm/main/gradle/version.properties)
- The all-open page says "For JPA entities, use the kotlin-jpa plugin, which makes entities open and generates zero-argument constructors for them" (page dated 21 October 2026) — [All-open compiler plugin](https://kotlinlang.org/docs/all-open-plugin.html)

### Inferences
- Spring's CGLIB proxy is a subclass, but it is *not* the bean. It holds and forwards to a separate target instance, so subclassing alone does not fix self-invocation. ArC's documented self-interception, plus its generated `Foo_Subclass extends Foo`, implies that the intercepted subclass instance *is* the contextual instance, so `this.doSomething()` dispatches virtually to the overriding subclass method. The Byte Buddy run shows both models side by side. The ArC mechanism is inferred from the naming and the docs; I did not trace it in the ArC source.
- Calling a client proxy is different: a `Foo_ClientProxy` forwards to the contextual instance, which (when intercepted) is the `Foo_Subclass`.
- Kotlin implications:
  - Spring needs kotlin-spring (or `open`) for CGLIB proxies.
  - Hibernate needs all-open/kotlin-jpa plus no-arg constructors for entities.
  - Quarkus ArC can transform unproxyable classes by default, but the Quarkus Kotlin guide still recommends all-open for JAX-RS resources, `@ApplicationScoped` beans and entities. Teach both, and point out the possible tension; do not claim either is unnecessary without testing.
- For agents and retransformation, Byte Buddy's `Advice` is the right tool (it inlines code into existing methods without adding members). For subclass proxies, `MethodDelegation` fits (it adds accessor methods and auxiliary types, as observed with `audit$accessor$…`).

### Gaps
- I did not run Spring or Quarkus applications. All framework behaviour comes from their docs and sources, apart from the Byte Buddy simulations of the two models.
- Whether Spring 7's CGLIB fork or Gizmo 2 now emit bytecode through the JDK ClassFile API was not verified.
- I did not confirm, against a running app, which loader Quarkus dev mode uses for the generated `_Subclass` classes.

## 6. The ClassFile API (java.lang.classfile): JEP 457 → 466 → 484

### Takeaway
The standard class-file library is the `java.lang.classfile` package, with subpackages `attribute`, `constantpool` and `instruction`. It was a preview in JDK 22 (JEP 457) and JDK 23 (JEP 466), and became final in JDK 24 (JEP 484), with `@since 24` on the API. The entry point is `ClassFile.of()`, which offers `parse` (to an immutable, lazily inflated `ClassModel`), `build` (via builder lambdas), `transformClass` (via `ClassTransform` "flatMap" over elements) and `verify`. The JDK itself uses it: for proxies since JDK 23 and for lambdas since JDK 24. The JDK's internal ASM copy is gone from the jdk-25-ga tree.

### Cited Findings
- `ClassFile` is in `package java.lang.classfile`. At jdk-22-ga and jdk-23-ga it carries `@since 22` and `@PreviewFeature(feature = PreviewFeature.Feature.CLASSFILE_API)`. At jdk-24-ga and jdk-25-ga it carries `@since 24` and no preview annotation — [jdk-22-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-22-ga/src/java.base/share/classes/java/lang/classfile/ClassFile.java), [jdk-23-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-23-ga/src/java.base/share/classes/java/lang/classfile/ClassFile.java), [jdk-24-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-24-ga/src/java.base/share/classes/java/lang/classfile/ClassFile.java), [jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/classfile/ClassFile.java)
- `PreviewFeature` has `@JEP(number=457, title="ClassFile API", status="Preview") CLASSFILE_API` at jdk-22-ga and `@JEP(number=466, title="ClassFile API", status="Second Preview")` at jdk-23-ga. The jdk-26-ga copy says: "For example, Class-File API became final in JDK 24" — [PreviewFeature jdk-22-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-22-ga/src/java.base/share/classes/jdk/internal/javac/PreviewFeature.java), [jdk-23-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-23-ga/src/java.base/share/classes/jdk/internal/javac/PreviewFeature.java), [jdk-26-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-26-ga/src/java.base/share/classes/jdk/internal/javac/PreviewFeature.java)
- The JEP 484 number for the final version comes from a search listing: the jdk-dev "JEP proposed to target JDK 24: 484: Class-File API" thread, and an implementation commit titled "8334714: Implement JEP 484: Class-File API" (search listing only, page not fetched; mail.openjdk.org link: https://mail.openjdk.org/pipermail/jdk-dev/2024-October/009427.html)
- Package docs (jdk-25-ga) — [package-info.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/classfile/package-info.java):
  - Reading: "`ClassModel cm = ClassFile.of().parse(bytes);`… A ClassModel is an immutable description of a class… A ClassModel is inflated lazily; most parts of the classfile are not parsed until they are actually needed… may lead to IllegalArgumentException due to malformed class file format, as parsing happens lazily."
  - Models and elements: "Models represent complex structures, such as classes, methods, fields, record elements, or the code body of a method. Models can be explored either via random-access navigation… or as a linear sequence of *elements*… For each model type (e.g., MethodModel), there is a corresponding element type (MethodElement). Models and elements are immutable and are inflated lazily."
  - Writing: "ClassFile generation is accomplished through *builders*. For each entity type that has a model, there is also a corresponding builder type… Rather than creating builders directly, builders are provided as an argument to a user-provided lambda."
  - Transforming: "For each kind of builder, XxxBuilder has a method `with(XxxElement)` so that elements that we wish to pass through unchanged can be handed directly back to the builder… Transformation can be viewed as a "flatMap" operation on the sequence of elements; for every element, we could pass it through unchanged, drop it, or replace it with one or more elements… each model type has a corresponding XxxTransform type."
  - The page also has sections on options, symbolic information, "Consistency checks, syntax checks and verification", lifting and composing transforms, constant pool sharing, and unknown elements.
- The JDK's internal ASM copy: `jdk/internal/org/objectweb/asm/ClassWriter.java` and `Opcodes.java` exist at jdk-24-ga (HTTP 200) and return 404 at jdk-25-ga — [Opcodes.java jdk-24-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-24-ga/src/java.base/share/classes/jdk/internal/org/objectweb/asm/Opcodes.java). Proxy generation moved to `java.lang.classfile` in JDK 23 and lambda generation in JDK 24 (see sections 3 and 4).
- Observed (local run: CfDemo on JDK 25.0.4.1, same output on JDK 27.0.1.0.3):
  - `parse` of a JDK 25-compiled class → `major=69`, listing `<init>()V invokes=1`, `add(II)I invokes=1`, `debugLog(Ljava/lang/String;)V invokes=1`, `debugDump()V invokes=0` (invokes counted by filtering `InvokeInstruction` elements)
  - `ClassFile.of().build(ClassDesc.of("Gen"), clb -> clb.withMethodBody("hello", MethodTypeDesc.of(CD_String, CD_String), ACC_PUBLIC|ACC_STATIC, cob -> cob.ldc("Hello, ").aload(0).invokevirtual(CD_String, "concat", …).areturn()))`, defined with `MethodHandles.lookup().defineClass` → `Hello, ClassFile API`
  - `cf.transformClass(cm, ClassTransform.dropping(e -> e instanceof MethodModel m && m.methodName().stringValue().startsWith("debug")))` → methods `[<init>, add]`
  - `cf.verify(gen)` → `[]`
  - compiling the same file on JDK 21 fails: `package java.lang.classfile.instruction does not exist`

### Inferences
- For new tooling that only needs to run on JDK 24+, the ClassFile API removes the need to shade ASM and track each new class-file version. It always matches the running JDK. Libraries that must support older JDKs (Byte Buddy targets Java 5 or 8) bridge to it instead, as Byte Buddy's "ASM to Class File API bridge" release notes show.
- Its immutable-model, builder-lambda design differs from ASM's visitor style. The "transform = flatMap over elements" idea is the key concept for the lesson.

### Gaps
- The JEP 457, 466 and 484 pages and the inside.java articles (Brian Goetz, Adam Sotona) could not be fetched (hosts blocked). The goals and non-goals wording of JEP 484 is therefore not quoted here.
- The exact changes between the second preview and the final API were not verified.

## 7. Java agents and instrumentation: premain/agentmain, Instrumentation, ClassFileTransformer, dynamic attach and JEP 451, Byte Buddy AgentBuilder and ByteBuddyAgent.install()

### Takeaway
Agents start in one of three ways:
- at startup with `-javaagent:jar[=args]`, which calls `premain`
- from an executable JAR's `Launcher-Agent-Class`
- by attaching to a running JVM, which calls `agentmain`

Since JDK 21 (JEP 451), loading an agent dynamically still works but prints a multi-line warning, unless `-XX:+EnableDynamicAgentLoading` is set. `-XX:-EnableDynamicAgentLoading` blocks it. Agents do **not** need a restart to change already-loaded classes: `retransformClasses` swaps method bodies in place. However, they cannot add or remove members or change signatures, modifiers or inheritance, and frames already running keep executing the old code.

### Cited Findings
- `java.lang.instrument` package docs — [package-info.java jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.instrument/share/classes/java/lang/instrument/package-info.java):
  - "The -javaagent option may be used multiple times on the same command-line, thus starting multiple agents. The premain methods will be called in the order that the agents are specified"
  - for agents started in a running JVM, "the main manifest of the agent JAR file must contain the attribute Agent-Class… The agent class must define a public static agentmain method", and "The JVM prints a warning on the standard error stream for each agent that it attempts to start in a running JVM… Warnings can be disabled by means of an implementation-specific command line option"
  - "Implementation Note: For the HotSpot VM, the JVM option -XX:+EnableDynamicAgentLoading is used to opt-in to allow dynamic loading of agents into a running JVM. This option suppresses the warning"
  - `Launcher-Agent-Class` "specifies the binary name of the agent class that is packaged with the application. The agent is started by invoking the agent class agentmain method… before the application main method is invoked"
  - the manifest attributes also include `Premain-Class`, `Can-Redefine-Classes` and `Can-Retransform-Classes`
- HotSpot (jdk-25-ga): `product(bool, EnableDynamicAgentLoading, true, "Allow tools to load agents with the attach mechanism")`. The default is true, i.e. allowed but with a warning — [globals.hpp jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/runtime/globals.hpp)
- JEP 451, "Prepare to Disallow the Dynamic Loading of Agents", was delivered in JDK 21 (number and title confirmed by search listing; page not fetched: https://openjdk.org/jeps/451)
- `retransformClasses` (Javadoc): "If a retransformed method has active stack frames, those active frames continue to run the bytecodes of the original method. The retransformed method will be used on new invokes… redefining a class does not cause its initializers to be run. The values of static variables will remain as they were… Instances of the retransformed class are not affected… If this method throws an exception, no classes have been retransformed." — [Instrumentation.java jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.instrument/share/classes/java/lang/instrument/Instrumentation.java)
- JVMTI: "The retransformation may change method bodies, the constant pool and attributes (unless explicitly prohibited). The retransformation must not add, remove or rename fields or methods, change the signatures of methods, change modifiers, or change inheritance." — [jvmti.xml jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/prims/jvmti.xml)
- `ClassFileTransformer.transform` returns "a well-formed class file buffer (the result of the transform), or null if no transform is performed" — [ClassFileTransformer.java jdk-25-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.instrument/share/classes/java/lang/instrument/ClassFileTransformer.java)
- Observed `-javaagent` (local run: CountingAgent, JDK 21) printed `[agent] premain args=hello, already loaded=929`, `[agent] loading demo/LoaderInfo via app (3356 bytes)`, and at shutdown `[agent] transformer saw 158 class definitions`. No warning appears for a startup agent.
- Observed dynamic self-attach (`ByteBuddyAgent.install()`). On JDK 21.0.12.1, 25.0.4.1, 26.0.2 and 27.0.1.0.3, stderr showed:
  ```
  WARNING: A Java agent has been loaded dynamically (…/byte-buddy-agent-1.18.17.jar)
  WARNING: If a serviceability tool is in use, please run with -XX:+EnableDynamicAgentLoading to hide this warning
  WARNING: If a serviceability tool is not in use, please run with -Djdk.instrument.traceUsage for more information
  WARNING: Dynamic loading of agents will be disallowed by default in a future release
  ```
  With `-XX:+EnableDynamicAgentLoading` the warning disappeared. With `-XX:-EnableDynamicAgentLoading` (JDK 25), `java.lang.IllegalStateException: Could not self-attach to current VM using external process` was thrown from `ByteBuddyAgent.installExternal` (local run: BBDemo)
- Observed "no restart". An already-instantiated `Clock` returned `tick` with an empty log. Then `new AgentBuilder.Default().disableClassFormatChanges().with(RedefinitionStrategy.RETRANSFORMATION).type(is(Clock.class)).transform((b,…) -> b.visit(Advice.to(TimingAdvice.class).on(named("now")))).installOn(inst)` ran, and the **same instance** returned `tick` and logged `[advice bb.BBDemo$Clock.now]`. `isRetransformClassesSupported()` and `isRedefineClassesSupported()` were both true, and `getAllLoadedClasses()` returned 3,291–3,412 classes depending on the JDK (local run; JDK 21, 25, 26 and 27). With hash codes normalised, ProxyDemo's full output was byte-identical across JDK 21, 25 and 27 (diffed)
- On JDK 25 only, the AgentBuilder step also printed JEP 498's warning: `WARNING: sun.misc.Unsafe::objectFieldOffset has been called by net.bytebuddy.dynamic.loading.ClassInjector$UsingUnsafe$Dispatcher$CreationAction`. JDK 26 and 27 printed no Unsafe warning (local run). This matches Byte Buddy 1.18.10's "Delay change of default for unsafe use to Java 26" — [release-notes.md](https://raw.githubusercontent.com/raphw/byte-buddy/master/release-notes.md). JMH 1.37 also triggers this warning on JDK 25 (`org.openjdk.jmh.util.Utils`) (local run)

### Inferences
- Lesson framing: "agents need a restart" is false for method-body changes. Retransformation is live, but it is restricted to bodies, which is why APM agents use Advice-style inlining. Schema changes, or new behaviour in classes not yet loaded, need a transformer registered before the class loads (startup `-javaagent`).
- For tests that call `ByteBuddyAgent.install()` (Mockito's inline mock maker also self-attaches), add `-XX:+EnableDynamicAgentLoading` to the test JVM, or load the agent with `-javaagent`, to stay quiet on JDK 21–27 and ready for the future default. (The Mockito detail is from memory and not verified here.)

### Gaps
- I could not confirm whether any release up to JDK 27 changed the default to *disallow* dynamic loading. The observed JDK 27.0.1 behaviour still warns and allows, and `EnableDynamicAgentLoading` defaults to true at jdk-25-ga. I did not fetch globals.hpp at jdk-27-ga, only observed the behaviour.

## 8. Exact behaviours and versions, JDK 21 → 27 (consolidated)

### Takeaway
The "integrity by default" changes relevant to this track are, so far, all warnings with opt-outs. Nothing between JDK 21 and 27 turned any of them into a hard failure by default: dynamic agents (warn since 21), `sun.misc.Unsafe` memory access (deprecated in 23, warns since 24, still warns in 27), and reflective final-field mutation (warns since 26, still warns in 27). The ClassFile API is final since 24. `invokeDefault` is in 16.

### Cited Findings

| Item | Version | Evidence |
|---|---|---|
| `InvocationHandler.invokeDefault` | JDK 16 | `@since 16` — [InvocationHandler.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/reflect/InvocationHandler.java) |
| ClassFile API preview / 2nd preview / final; package `java.lang.classfile` | 22 (JEP 457) / 23 (JEP 466) / 24 (JEP 484) | `@PreviewFeature` + `@JEP` at 22/23; `@since 24` at 24 — [PreviewFeature jdk-23-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-23-ga/src/java.base/share/classes/jdk/internal/javac/PreviewFeature.java), [ClassFile jdk-24-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-24-ga/src/java.base/share/classes/java/lang/classfile/ClassFile.java) |
| JDK proxies generated with the ClassFile API | JDK 23 | [ProxyGenerator jdk-23-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-23-ga/src/java.base/share/classes/java/lang/reflect/ProxyGenerator.java) |
| Lambda classes generated with the ClassFile API | JDK 24 | [InnerClassLambdaMetafactory jdk-24-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-24-ga/src/java.base/share/classes/java/lang/invoke/InnerClassLambdaMetafactory.java) |
| Internal ASM copy absent | jdk-25-ga | 404 at jdk-25-ga vs 200 at jdk-24-ga — [Opcodes jdk-24-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-24-ga/src/java.base/share/classes/jdk/internal/org/objectweb/asm/Opcodes.java) |
| JEP 451: warn on dynamic agent loading; `-XX:+EnableDynamicAgentLoading` hides it, `-XX:-` blocks | JDK 21 → still warns in 27.0.1 | local runs; [instrument package-info](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.instrument/share/classes/java/lang/instrument/package-info.java); [globals.hpp](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/runtime/globals.hpp) |
| JEP 471: `sun.misc.Unsafe` memory-access methods `@Deprecated(since="23", forRemoval=true)` | JDK 23 | [Unsafe.java jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/jdk.unsupported/share/classes/sun/misc/Unsafe.java) |
| JEP 498: `--sun-misc-unsafe-memory-access=allow\|warn\|debug\|deny`, default `warn` | JDK 24; still `warn` in 25, 26, 27 | man page "The default value when the option is not specified is `warn`" — [java.md jdk-24-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-24-ga/src/java.base/share/man/java.md), [java.md jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/java.base/share/man/java.md); `MemoryAccessOption.defaultValue()` returns `WARN` at jdk-27-ga — [Unsafe.java jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/jdk.unsupported/share/classes/sun/misc/Unsafe.java) |
| JEP 500 "Prepare to Make Final Mean Final": `--enable-final-field-mutation=<modules>\|ALL-UNNAMED`, `--illegal-final-field-mutation=allow\|warn\|debug\|deny`, default `warn` | JDK 26; still `warn` in 27 | [java.md jdk-26-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-26-ga/src/java.base/share/man/java.md), [java.md jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/java.base/share/man/java.md); JEP number from search listing (jdk-dev "JEP proposed to target JDK 26: 500", not fetched) |
| AOT cache options (`-XX:AOTCache`, `AOTMode`; `AOTCacheOutput` in 25; `required` mode in 27) | 24 / 25 / 27 | java.md at each tag (section 1) |

- Observed `Unsafe.allocateMemory` (local run: UnsafeUse):
  - JDK 21: no warning
  - JDK 24, 25.0.4.1, 26.0.2 and 27.0.1: `WARNING: A terminally deprecated method in sun.misc.Unsafe has been called` / `WARNING: sun.misc.Unsafe::allocateMemory has been called by UnsafeUse (file:…)` / `WARNING: Please consider reporting this to the maintainers of class UnsafeUse` / `WARNING: sun.misc.Unsafe::allocateMemory will be removed in a future release`
  - JDK 27 with `--sun-misc-unsafe-memory-access=deny`: `java.lang.UnsupportedOperationException: allocateMemory at jdk.unsupported/sun.misc.Unsafe.beforeMemoryAccessSlow`
- Observed `Field.set` on a `private final` instance field after `setAccessible(true)` (local run: FinalMutation):
  - JDK 21.0.12.1 and 25.0.4.1: silent
  - JDK 26.0.2 and 27.0.1: `WARNING: Final field url in class FinalMutation$Config has been mutated reflectively by class FinalMutation in unnamed module @… (file:…)` / `WARNING: Use --enable-final-field-mutation=ALL-UNNAMED to avoid a warning` / `WARNING: Mutating final fields will be blocked in a future release unless final field mutation is enabled`
  - JDK 26 with `--illegal-final-field-mutation=deny`: `java.lang.IllegalAccessException: class FinalMutation (in unnamed module @…) cannot set final field FinalMutation$Config.url…, unnamed module @… is not allowed to mutate final fields`, thrown from `Field.preSetFinal`
  - with `--enable-final-field-mutation=ALL-UNNAMED`: silent
- Search listings (pages not fetched) describe JEP 498 as delivered in JDK 24, as the successor to JEP 471 (JDK 23), and changing the default of `--sun-misc-unsafe-memory-access` from allow to warn (https://openjdk.org/jeps/498). They describe JEP 500 as a JDK 26 feature that warns on final-field mutation via deep reflection (https://mail.openjdk.org/pipermail/jdk-dev/2025-October/010571.html).
- JDK 27's active previews are Structured Concurrency (Seventh Preview, JEP 533), Lazy Constants (Third Preview, JEP 531) and PEM Encodings (Third Preview, JEP 538). None touches class loading or proxies — [PreviewFeature jdk-27-ga](https://raw.githubusercontent.com/openjdk/jdk/jdk-27-ga/src/java.base/share/classes/jdk/internal/javac/PreviewFeature.java)

### Inferences
- Frameworks that mutate final fields reflectively (some DI, serialization and mocking libraries) now warn on 26 and 27. The tested Kotlin/Quarkus/Spring stacks did not trigger this in these experiments, but I did not test them.
- "Prepare for the future" checklist for learners: run tests with `--sun-misc-unsafe-memory-access=deny`, `--illegal-final-field-mutation=deny`, and without `-XX:+EnableDynamicAgentLoading`, to find dependencies that will break when the defaults change.

### Gaps
- openjdk.org was blocked, so the JEP pages (451, 471, 484, 498, 500) were not read. Their numbers and titles come from in-source `@JEP` annotations (457/466) or search listings (451/484/498/500). JEP 471's number comes from memory plus the matching `@Deprecated(since="23")`.

## 9. Misconceptions to correct

### Takeaway
Each common belief below has a short, runnable counter-demo from this session.

### Cited Findings
- **"Proxies can wrap any class."** JDK proxies are interface-only (`… is not an interface`, local run). Subclass proxies cannot touch `final` classes or methods or `private` methods: Spring docs; Byte Buddy's "Cannot subclass … final types", and the final `id()` not intercepted (local run). Kotlin classes are final unless opened (local run; [all-open](https://kotlinlang.org/docs/all-open-plugin.html)).
- **"@Transactional works on internal calls."** Not in Spring's default proxy mode: "self-invocation… does not lead to an actual transaction at runtime" — [annotations.adoc](https://raw.githubusercontent.com/spring-projects/spring-framework/main/framework-docs/modules/ROOT/pages/data-access/transaction/declarative/annotations.adoc). The JDK-proxy and forwarding-subclass demos show the advice being skipped (local run). Quarkus ArC *does* intercept self-invocation as a non-standard feature — [cdi-reference.adoc](https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/cdi-reference.adoc). So the answer is "it depends on the container", and a Spring→Quarkus migrant can be surprised in either direction.
- **"NoClassDefFoundError means the jar is missing."** It also appears after a failed static initializer (`Could not initialize class …`, local run), and when a class present at compile time is absent at link time. In the latter case it wraps ClassNotFoundException (local run). Duplicate classes across loaders show up as ClassCastException with loader names, not as NCDFE (local run).
- **"javap shows Kotlin source structure."** It shows JVM members: `getX`, `component1`, `copy$default`, `Companion`, `INSTANCE`, `$default` bitmasks, public `lateinit` fields. Kotlin's structure lives in `@kotlin.Metadata` (local run).
- **"Agents need a restart."** `ByteBuddyAgent.install()` plus `RETRANSFORMATION` changed a loaded class's method body on a live instance (local run). There are limits: no member or signature changes — [jvmti.xml](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/prims/jvmti.xml) — and running frames keep the old code — [Instrumentation.java](https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.instrument/share/classes/java/lang/instrument/Instrumentation.java). Dynamic attach also warns since JDK 21.
- **Extra misconceptions worth a slide:**
  - "Loading a class runs its static initializer": no (`Class.forName(n,false,l)`, `X.class`, arrays, constants; local run).
  - "Same class name means same class": no (two loaders; local run).
  - "Lambdas are inner classes": no, hidden classes linked by indy (local run).
  - "CGLIB calls your constructor twice": true only in old Spring (3.2 docs), not with Objenesis — [aop.xml 3.2.x](https://raw.githubusercontent.com/spring-projects/spring-framework/3.2.x/src/reference/docbook/aop.xml), [proxying.adoc](https://raw.githubusercontent.com/spring-projects/spring-framework/main/framework-docs/modules/ROOT/pages/core/aop/proxying.adoc).
  - "Spring Boot uses JDK proxies when there's an interface": Boot defaults `proxyTargetClass=true` — [AopAutoConfiguration](https://raw.githubusercontent.com/spring-projects/spring-boot/main/core/spring-boot-autoconfigure/src/main/java/org/springframework/boot/autoconfigure/aop/AopAutoConfiguration.java).
  - "`getClass()` on a proxy goes to the handler": no (local run; Proxy Javadoc).

### Inferences
- The most valuable single demo for this learner is the side-by-side Byte Buddy pair: an instance-is-subclass proxy (self-call intercepted) and a forwarding proxy (self-call skipped). It explains Spring's behaviour, Quarkus's behaviour, and why "it's a subclass" alone is not the answer.

### Gaps
- None beyond those listed in earlier sections.

## 10. Teaching notes (analogies, demos with captured output, JUnit-gradable labs)

### Takeaway
Every demo and lab below was run in this session. The expected outputs are the real outputs. The labs are plain Java plus JUnit 6.1.3 and Byte Buddy 1.18.17, and they port directly to the course's Kotlin/Gradle labs project.

### Cited Findings
**Suggested 7-lesson mapping** (inference, for writers):
1. Class loaders and delegation, identity, CNFE vs NCDFE
2. Loading → linking → initialization, init triggers, init deadlocks
3. Reading bytecode (javap, the stack, the constant pool, Kotlin lowering)
4. invokedynamic and condy
5. JDK dynamic proxies in depth (the largest lesson; consider splitting it across lesson 5 and the labs)
6. Subclass proxies: Byte Buddy, Spring, ArC, Hibernate
7. ClassFile API, plus agents and instrumentation, plus JDK 24–27 integrity warnings

**Analogies**
- Class identity = "(fully qualified name, defining loader)", like a database row keyed by (tenant, id). The same id in two tenants is two rows.
- A JDK proxy = a receptionist that takes every call to the listed extensions and hands a written note (Method + Object[]) to one person (the handler). Calls staff make to each other inside the office never pass reception (self-invocation).
- ArC subclass = the staff member has an assistant built into their own desk, so even calls they make to themselves go through it. Spring proxy = a separate front office.
- indy = "dial a number that is wired up to a destination the first time anyone dials it". condy = the same, for a constant.

**Demo programs** (all ran; source summarised; outputs quoted in sections 1–8)
- `ProxyDemo` (JDK 21/25/27):
  - class anatomy table
  - caching and order sensitivity
  - Object-method dispatch
  - the self-invocation pitfall
  - `invokeDefault` (3 handler calls)
  - `IllegalArgumentException` for a non-default method
  - `UndeclaredThrowableException` vs a declared checked exception
  - the ITE-unwrapping bug
  - class not an interface
  - one dynamic module per loader
  - package-private interface → proxy in that package
  
  Add `-Djdk.proxy.ProxyGenerator.saveGeneratedFiles=true` and run `javap -p -c 'jdk/proxy1/$Proxy0.class'` to show the generated code (section 2).
- `InitPuzzle` (12 cases, section 1); `InitDeadlock` (jstack frames, section 1); `NcdfeDemo` and `UsesHelper` (delete `Helper.class` and run with and without an argument); `TwoLoaders`; `LoaderInfo`; `LeakDemo`; `BadGen`/`BadGen2` (VerifyError, eager vs lazy linking).
- `IndyDemo` (javac 21): one file yields LambdaMetafactory, StringConcatFactory, ObjectMethods, SwitchBootstraps, and **condy** ConstantBootstraps entries in `javap -v`.
- `Shapes.kt` (kotlinc 2.4.21): data class, properties, companion, object, default args, inline/reified, lambda. Compile twice (`-jvm-target 21` vs default) to show indy vs StringBuilder concat and class-file version 65 vs 52. `Svc.kt` with the all-open plugin shows `final` disappearing.
- `BBDemo` (Byte Buddy 1.18.17): subclass naming, accessor methods, final method skipped, self-invocation (subclass vs forwarding), final Kotlin class rejected, rebase vs redefine method lists, live retransformation with Advice, and the JEP 451 / JEP 498 warnings.
- `CountingAgent`: a `Premain-Class` jar printing the classes the transformer sees.
- `CfDemo` (JDK 25/27): parse/build/transform/verify.
- `FinalMutation` and `UnsafeUse`: the version matrix in section 8.
- `ProxyBench` (JMH): direct ≈ Byte Buddy `@SuperCall` < JDK proxy < `Method.invoke` (section 4).

**Lab A: retrying/timing JDK proxy** (all graded tests passed on JDK 21.0.12.1 and 25.0.4.1)
```java
public static <T> T create(Class<T> iface, T target, int maxAttempts) {
  InvocationHandler h = (proxy, m, args) -> {
    if (m.getDeclaringClass() == Object.class) return switch (m.getName()) {
        case "equals" -> proxy == args[0]; case "hashCode" -> System.identityHashCode(proxy);
        default -> "RetryingProxy[" + target + "]"; };
    if (m.isDefault()) return InvocationHandler.invokeDefault(proxy, m, args); // body re-enters proxy
    Throwable last = null;
    for (int i = 1; i <= maxAttempts; i++) {
      ATTEMPTS.incrementAndGet();
      try { return m.invoke(target, args); } catch (InvocationTargetException e) { last = e.getCause(); }
    }
    throw last;
  };
  return (T) Proxy.newProxyInstance(iface.getClassLoader(), new Class<?>[]{iface}, h);
}
```
Tests:
- `retriesUntilSuccess`: target fails 2×, `maxAttempts=3` → returns `row7`; target calls = 3; attempts = 3
- `givesUpWithOriginalException`: always failing → `IllegalStateException("flaky 3")`, not UndeclaredThrowableException
- `defaultMethodBodyRunsThroughTheProxy`: `default loadTwice()` with 1 failure and `maxAttempts=2` → `"row1+row1"` and attempts = 3, proving the default method's inner calls were retried
- `objectMethodsAreSane`: `repo.equals(repo)` is true; toString starts with `RetryingProxy[`; attempts = 0
- `proxyAnatomy`: `isProxyClass`, simple name starts with `$Proxy`, interfaces == `[Repo]`

A timing variant can wrap the same handler with `System.nanoTime()` (not separately graded here).

**Lab B: Byte Buddy subclass interceptor** (passed)
- `CallCounter.instrument(Checkout.class)` uses `subclass(type).method(isPublic().and(isDeclaredBy(type))).intercept(MethodDelegation.to(Interceptor.class))`, where the interceptor uses `@Origin Method` and `@SuperCall Callable`.
- Expected: `c.pay(500)` → `"paid 500 5"`; counts == `{pay=1, fee=1}`, with the self-invoked `fee` counted and the `final id()` not counted; the class name contains `$ByteBuddy$`.

**Lab C: class-initialization order puzzle** (passed). The Singleton has `static final Singleton INSTANCE = new Singleton();` followed by `static int created = 0;` and a constructor that does `created++`. Expected log sequence:
1. read `Derived.CONST` (a constant) → `[]`
2. read `Derived.BASE_FIELD` → `["Base"]` (only the declaring class)
3. `Derived.counter++` → `["Base","Derived"]`
4. `Singleton.created` == **0**, with log entry `"ctor created=1"`: the field initializer ran after the constructor

**Lab D: one class file, two loaders** (passed). An `IsolatingLoader` (child-first for prefix `lab.plugin.`, overriding `loadClass`/`findClass`, using `getClassLoadingLock` and `defineClass`). Expected:
- `assertNotSame(a, b)`
- same `getName()`
- `b.isInstance(ga)` false
- `b.cast(ga)` throws ClassCastException
- `get()` returns `"hi from A"`, using the loader name
- each copy's static `INITS` == 1

**Lab E: counting and lazy initialization** (passed). `ClassLoadingMXBean.getTotalLoadedClassCount()` increases by at least 1 after `Class.forName("lab.plugin.Greeting", false, newLoader)`. A parent-loaded event log shows no `"Greeting init in C"` until a reflective static read, after which `INITS` == 1 and the event is present.

Run command used: `java -jar junit-platform-console-standalone-6.1.3.jar execute -cp out:byte-buddy-1.18.17.jar --select-class lab.LabTests` → `9 tests successful, 0 tests failed` on both JDKs.

**Pitfalls for lab authors** (observed)
- JUnit and Byte Buddy on JDK 25 print the JEP 498 Unsafe warning only when Byte Buddy's Unsafe injector is used (the AgentBuilder path). The plain `subclass().make().load()` in Lab B printed nothing.
- Labs that use `ByteBuddyAgent.install()` print the JEP 451 warning unless the test JVM gets `-XX:+EnableDynamicAgentLoading`.
- Gradle's test JVM arguments are configured with `tasks.test { jvmArgs(...) }`. This is standard Gradle usage, not run here.

### Inferences
- Grade Lab A with exact attempt counts. Students who forget to unwrap ITE, or who retry Object methods, fail deterministic tests.
- Lab C's Singleton case is the classic "static initializers run in textual order" trap. Pair it with the javap of `<clinit>`.

### Gaps
- No timing/latency assertions were graded; they would be flaky in CI.
- I did not run a Quarkus self-interception lab (it needs a Quarkus build). A doc-based explanation plus the Byte Buddy simulation stands in for it.

## 11. Verified URLs (fetched in this session)

### Takeaway
Primary sources only: the OpenJDK source at GA tags, framework doc sources on GitHub, kotlinlang.org, and Maven Central metadata. Hosts that were blocked are listed separately.

### Cited Findings
OpenJDK (raw.githubusercontent.com/openjdk/jdk):
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/reflect/Proxy.java
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/reflect/InvocationHandler.java
- https://raw.githubusercontent.com/openjdk/jdk/jdk-21-ga/src/java.base/share/classes/java/lang/reflect/ProxyGenerator.java
- https://raw.githubusercontent.com/openjdk/jdk/jdk-22-ga/src/java.base/share/classes/java/lang/reflect/ProxyGenerator.java
- https://raw.githubusercontent.com/openjdk/jdk/jdk-23-ga/src/java.base/share/classes/java/lang/reflect/ProxyGenerator.java
- https://raw.githubusercontent.com/openjdk/jdk/jdk-24-ga/src/java.base/share/classes/java/lang/reflect/ProxyGenerator.java
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/reflect/ProxyGenerator.java
- https://raw.githubusercontent.com/openjdk/jdk/jdk-22-ga/src/java.base/share/classes/java/lang/classfile/ClassFile.java (also jdk-23-ga, jdk-24-ga, jdk-25-ga)
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/classfile/package-info.java
- https://raw.githubusercontent.com/openjdk/jdk/jdk-22-ga/src/java.base/share/classes/jdk/internal/javac/PreviewFeature.java (also jdk-23-ga, jdk-24-ga, jdk-25-ga, jdk-26-ga, jdk-27-ga)
- https://raw.githubusercontent.com/openjdk/jdk/jdk-24-ga/src/java.base/share/man/java.md (also jdk-25-ga, jdk-26-ga, jdk-27-ga)
- https://raw.githubusercontent.com/openjdk/jdk/jdk-24-ga/src/jdk.unsupported/share/classes/sun/misc/Unsafe.java (also jdk-25-ga, jdk-26-ga, jdk-27-ga)
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/invoke/LambdaMetafactory.java
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/invoke/InnerClassLambdaMetafactory.java (also jdk-22-ga, jdk-23-ga, jdk-24-ga)
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/invoke/StringConcatFactory.java
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/runtime/ObjectMethods.java
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/invoke/ConstantBootstraps.java
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/invoke/MethodHandles.java
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.base/share/classes/java/lang/ClassLoader.java
- https://raw.githubusercontent.com/openjdk/jdk/jdk-23-ga/src/java.base/share/classes/jdk/internal/org/objectweb/asm/ClassWriter.java (200); jdk-24-ga ClassWriter.java and Opcodes.java (200); jdk-25-ga same paths (404)
- https://raw.githubusercontent.com/openjdk/jdk/jdk-21-ga/src/java.instrument/share/classes/java/lang/instrument/package-info.java (also jdk-25-ga)
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.instrument/share/classes/java/lang/instrument/Instrumentation.java
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/java.instrument/share/classes/java/lang/instrument/ClassFileTransformer.java
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/runtime/globals.hpp
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/oops/instanceKlass.cpp
- https://raw.githubusercontent.com/openjdk/jdk/jdk-25-ga/src/hotspot/share/prims/jvmti.xml
- https://raw.githubusercontent.com/openjdk/jdk/jdk-26-ga/src/java.base/share/classes/java/lang/reflect/Field.java (also jdk-27-ga; downloaded, not quoted)
- https://raw.githubusercontent.com/openjdk/jdk/jdk-21-ga/make/conf/version-numbers.conf (and jdk-22-ga … jdk-27-ga, master)

Spring:
- https://raw.githubusercontent.com/spring-projects/spring-framework/main/framework-docs/modules/ROOT/pages/core/aop/proxying.adoc
- https://raw.githubusercontent.com/spring-projects/spring-framework/main/framework-docs/modules/ROOT/pages/core/aop/introduction-proxies.adoc
- https://raw.githubusercontent.com/spring-projects/spring-framework/main/framework-docs/modules/ROOT/pages/data-access/transaction/declarative/annotations.adoc
- https://raw.githubusercontent.com/spring-projects/spring-framework/main/framework-docs/modules/ROOT/pages/core/beans/annotation-config/autowired.adoc
- https://raw.githubusercontent.com/spring-projects/spring-framework/main/spring-context/src/main/java/org/springframework/context/annotation/Proxyable.java
- https://raw.githubusercontent.com/spring-projects/spring-framework/main/spring-core/src/main/java/org/springframework/cglib/package-info.java
- https://raw.githubusercontent.com/spring-projects/spring-framework/main/spring-core/spring-core.gradle
- https://raw.githubusercontent.com/spring-projects/spring-framework/main/gradle.properties
- https://raw.githubusercontent.com/spring-projects/spring-framework/3.2.x/src/reference/docbook/aop.xml
- https://raw.githubusercontent.com/spring-projects/spring-boot/3.5.x/spring-boot-project/spring-boot-autoconfigure/src/main/java/org/springframework/boot/autoconfigure/aop/AopAutoConfiguration.java
- https://raw.githubusercontent.com/spring-projects/spring-boot/main/core/spring-boot-autoconfigure/src/main/java/org/springframework/boot/autoconfigure/aop/AopAutoConfiguration.java

Quarkus:
- https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/cdi-reference.adoc
- https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/cdi.adoc
- https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/class-loading-reference.adoc
- https://raw.githubusercontent.com/quarkusio/quarkus/main/docs/src/main/asciidoc/kotlin.adoc
- https://raw.githubusercontent.com/quarkusio/quarkus/main/independent-projects/arc/processor/src/main/java/io/quarkus/arc/processor/SubclassGenerator.java
- https://raw.githubusercontent.com/quarkusio/quarkus/main/independent-projects/arc/processor/src/main/java/io/quarkus/arc/processor/ClientProxyGenerator.java

Byte Buddy, cglib, Hibernate:
- https://raw.githubusercontent.com/raphw/byte-buddy/master/README.md
- https://raw.githubusercontent.com/raphw/byte-buddy/master/release-notes.md
- https://raw.githubusercontent.com/raphw/byte-buddy/master/byte-buddy-dep/src/main/java/net/bytebuddy/ByteBuddy.java
- https://raw.githubusercontent.com/cglib/cglib/master/README.md
- https://raw.githubusercontent.com/hibernate/hibernate-orm/main/documentation/src/main/asciidoc/introduction/Entities.adoc
- https://raw.githubusercontent.com/hibernate/hibernate-orm/main/documentation/src/main/asciidoc/introduction/Interacting.adoc
- https://raw.githubusercontent.com/hibernate/hibernate-orm/main/hibernate-core/src/main/java/org/hibernate/bytecode/internal/BytecodeProviderInitiator.java
- https://raw.githubusercontent.com/hibernate/hibernate-orm/main/hibernate-core/src/main/java/org/hibernate/proxy/pojo/bytebuddy/ByteBuddyProxyFactory.java (existence check only)
- https://raw.githubusercontent.com/hibernate/hibernate-orm/main/gradle/version.properties

Kotlin:
- https://kotlinlang.org/docs/all-open-plugin.html
- https://kotlinlang.org/docs/kotlin-spring-plugin.html
- https://kotlinlang.org/docs/whatsnew20.html
- https://kotlinlang.org/docs/whatsnew1520.html

Maven Central metadata (mirror):
- https://maven-central.storage-download.googleapis.com/maven2/net/bytebuddy/byte-buddy/maven-metadata.xml
- https://maven-central.storage-download.googleapis.com/maven2/org/jetbrains/kotlin/kotlin-compiler-embeddable/maven-metadata.xml (2.4.21 present)
- https://maven-central.storage-download.googleapis.com/maven2/org/springframework/spring-core/maven-metadata.xml
- https://maven-central.storage-download.googleapis.com/maven2/org/springframework/boot/spring-boot/maven-metadata.xml
- https://maven-central.storage-download.googleapis.com/maven2/io/quarkus/quarkus-core/maven-metadata.xml
- https://maven-central.storage-download.googleapis.com/maven2/org/hibernate/orm/hibernate-core/maven-metadata.xml
- Jars downloaded with matching .sha1: byte-buddy-1.18.17.jar, byte-buddy-agent-1.18.17.jar, junit-platform-console-standalone-6.1.3.jar

Seen only as web-search listings (not fetched; do not cite as verified):
- https://openjdk.org/jeps/451
- https://openjdk.org/jeps/498
- https://mail.openjdk.org/pipermail/jdk-dev/2024-October/009427.html (JEP 484 targeted to JDK 24)
- https://mail.openjdk.org/pipermail/jdk-dev/2025-October/010571.html (JEP 500 targeted to JDK 26)

### Inferences
- Lesson writers who can reach openjdk.org and docs.oracle.com should add links to the JVMS SE 25 chapter 5, JLS 12.4, and JEPs 280, 371, 451, 457, 466, 471, 484, 498 and 500, and the java.lang.reflect.Proxy / java.lang.classfile Javadoc for JDK 25. These pages could not be reached from this sandbox.

### Gaps
- Blocked hosts: openjdk.org, docs.oracle.com, docs.spring.io, quarkus.io, bytebuddy.net, inside.java, github.com (HTML pages and the API; raw.githubusercontent.com worked).
