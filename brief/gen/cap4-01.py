import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/container/src"
J = "java/workbench/container/l01"
K = "kotlin/workbench/container/l01"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :container:demo -Pmain=workbench.container.l01.demo."


def demo(name, title=None, kt_title=None):
    """A Try-it code object for a Java demo and its Kotlin twin, read from disk."""
    return {"lang": "java", "title": title or f"{name}.java", "src": read(f"{lab}/demo/{J}/demo/{name}.java"),
            "run": RUN + name, "file": f"{lab}/demo/{J}/demo/{name}.java",
            "alt": {"lang": "kotlin", "title": kt_title or f"{name}.kt", "src": read(f"{lab}/demo/{K}/demo/{name}.kt"),
                    "run": RUN + name + "Kt", "file": f"{lab}/demo/{K}/demo/{name}.kt"}}


FIGURE = """<svg viewBox="0 0 680 270" role="img" aria-label="The demo app's dependency graph. PaymentService points to HttpIssuerClient, FeeCalculator and Ledger; HttpIssuerClient points to IssuerConfig; FeeCalculator points to FxRates. Numbers give the creation order.">
<rect class="box-a" x="20" y="112" width="150" height="40" rx="8"/><text class="t" x="95" y="137" text-anchor="middle">6 PaymentService</text>
<rect class="box" x="250" y="32" width="160" height="40" rx="8"/><text class="t" x="330" y="57" text-anchor="middle">2 HttpIssuerClient</text>
<rect class="box" x="250" y="112" width="160" height="40" rx="8"/><text class="t" x="330" y="137" text-anchor="middle">4 FeeCalculator</text>
<rect class="box" x="250" y="192" width="160" height="40" rx="8"/><text class="t" x="330" y="217" text-anchor="middle">5 Ledger</text>
<rect class="box-ok" x="490" y="32" width="150" height="40" rx="8"/><text class="t" x="565" y="57" text-anchor="middle">1 IssuerConfig</text>
<rect class="box-ok" x="490" y="112" width="150" height="40" rx="8"/><text class="t" x="565" y="137" text-anchor="middle">3 FxRates</text>
<line class="ln" x1="170" y1="124" x2="248" y2="62" marker-end="url(#arr)"/>
<line class="ln" x1="170" y1="132" x2="248" y2="132" marker-end="url(#arr)"/>
<line class="ln" x1="170" y1="140" x2="248" y2="204" marker-end="url(#arr)"/>
<line class="ln" x1="410" y1="52" x2="488" y2="52" marker-end="url(#arr)"/>
<line class="ln" x1="410" y1="132" x2="488" y2="132" marker-end="url(#arr)"/>
<text class="t-s t-m" x="150" y="84" text-anchor="middle">via CardIssuerClient</text>
<text class="t-s t-m" x="565" y="200" text-anchor="middle">green: no dependencies,</text>
<text class="t-s t-m" x="565" y="218" text-anchor="middle">created first</text>
<text class="t-s t-a" x="340" y="262" text-anchor="middle">arrow = "my constructor needs this"; number = creation order</text>
</svg>"""

L = {
 "id": "cap4-01",
 "title": "Wire classes by reflection",
 "minutes": 38,
 "goal": "By the end you can build a small dependency injection container: find components from a list or a class path scan, pick each one's constructor, create them in dependency order with a readable cycle error, and give each singleton exactly one instance when many threads ask at once.",
 "warmup": {
  "q": "`FeeCalculator` and `QuoteService` each take an `FxRates` in their constructor, and `PaymentService` takes both. A ten-line container builds `PaymentService` by calling each constructor it finds, after building that constructor's parameters the same way. How many `FxRates` objects does it create?",
  "options": ["One: the JVM reuses an object when the same class is asked for twice", "Two: one for each constructor that asks for it", "Three: one per class in the graph", "None until a method is called on `FxRates`"],
  "answer": 1,
  "why": "Recursion with no memory builds a fresh dependency every time a constructor asks for one. To share one `FxRates`, the container has to remember what it already made: a cache of instances per type. That cache is what a container means by the singleton scope."
 },
 "sections": [
  {
   "h": "A container is the main method that calls new, written once",
   "body": """Most services start with a block like this somewhere near `main`:

```java
IssuerConfig config = new IssuerConfig();
FxRates rates = new FxRates();
PaymentService payments = new PaymentService(
        new HttpIssuerClient(config),
        new FeeCalculator(rates),
        new Ledger());
```

```kotlin
val config = IssuerConfig()
val rates = FxRates()
val payments = PaymentService(
    HttpIssuerClient(config),
    FeeCalculator(rates),
    Ledger())
```

That is **dependency injection** done by hand. Each class receives what it needs through its constructor and never calls `new` on its collaborators, so a test can pass in a fake issuer. The block has two jobs that get harder as the service grows: it must create things in the right order (`config` before the issuer client), and it must share the right instances (one `rates` for everyone). With six classes you do it in your head. With eighty, someone adds a constructor parameter and the block stops compiling in three places.

A **container** does that block for you. It needs three decisions per class. Which classes take part? We call them **components**. How do you build one? Its constructor says what it needs. How many instances should exist? That is its **scope**.

The smallest version is ten lines of reflection. `type.getConstructors()` returns the public constructors as `Constructor` objects. `getParameterTypes()` lists what each one needs, and `newInstance(args)` calls it, which allocates the object and runs the constructor exactly as `new` would. Build the parameters first, recursively, and you have a container:

```java
static Object build(Class<?> type) throws ReflectiveOperationException {
    Constructor<?> c = type.getConstructors()[0];
    Object[] args = new Object[c.getParameterCount()];
    for (int i = 0; i < args.length; i++) args[i] = build(c.getParameterTypes()[i]);
    return c.newInstance(args);
}
```

```kotlin
fun build(type: Class<*>): Any {
    val c = type.constructors[0]
    return c.newInstance(*c.parameterTypes.map { build(it) }.toTypedArray())
}
```

It works, and it is wrong in four ways you'll fix in this lesson. It takes "the first" constructor. It loops forever on a cycle. It has no list of components. And it never remembers anything, so it builds a new `FxRates` every time a constructor asks for one.""",
   "try": {
    "title": "Count the FxRates",
    "minutes": 4,
    "steps": [
     "Read `TinyContainerDemo` (or the Kotlin twin). `FeeCalculator` and `QuoteService` both need an `FxRates`. Predict how many times `new FxRates` prints in each half.",
     "Run it from `labs/`.",
     "Give `build` a memory: add `static final Map<Class<?>, Object> made = new HashMap<>();`, return `made.get(type)` when it is there, and `made.put(type, result)` before returning. In Kotlin, `made.getOrPut(type) { ... }` does both. Run it again."
    ],
    "code": demo("TinyContainerDemo"),
    "expect": "By hand, `new FxRates` prints once, because you passed the same `rates` twice. By reflection it prints twice: once for `FeeCalculator` and once for `QuoteService`. With the map it prints once. That map is a singleton scope in its simplest form, and section 4 shows why the plain version breaks under threads."
   }
  },
  {
   "h": "Find the components: a list you write, or a scan of the class path",
   "body": """The simplest way to tell the container which classes take part is a list: `new Container(List.of(PaymentService.class, Ledger.class, ...))`. It is fast and obvious, and it is one more file to keep in step with the code. The usual alternative is to mark classes with an annotation and scan for them.

A scan asks a class loader for the package's directory. `loader.getResources("workbench/container/l01/app")` returns one URL for every class path entry that contains that package. For a build directory it is a `file:` URL, and for a JAR it is a `jar:file:/srv/app.jar!/workbench/...` URL. You list the `.class` files under it and turn each file name into a binary class name.

Then you load each class, and the flag you pass decides what runs. `Class.forName(name, false, loader)` loads and links the class without initializing it. As *Class loading: loaders, delegation, linking and initialization* showed, the one-argument `Class.forName(name)` also initializes it, so every static initializer in the package would run during the scan, components or not. After loading, `c.isAnnotationPresent(Component.class)` keeps the components. That only works because `@Component` has `@Retention(RUNTIME)`. With the default retention, `CLASS`, javac writes the annotation into the class file, but the JVM never exposes it to reflection, and the scan finds nothing.

A scan has a price. It loads every class in the package, including the ones that turn out not to be components. In `ScanDemo`, scanning an 11-class package loaded 272 classes: the 11, plus the JDK code for listing directories, streams and reading annotations. *Why the JVM starts slowly, and how to measure it* showed that every class the JVM loads is found, parsed and verified on every launch. A large service scans thousands of classes at every start. Quarkus avoids this by indexing the classes when the application is built, which is where lesson 3 of this track ends up.

One more trap, found while writing the demo. `getResources` finds a package inside a JAR only when the JAR has an entry for the directory itself. Most build tools write those entries, but a JAR built with "files only" gives the scan zero roots. Nothing fails; the container just has no components.""",
   "try": {
    "title": "Scan a package, then run its initializers by accident",
    "minutes": 4,
    "steps": [
     "Read `ScanDemo` (or `ScanDemo.kt`). `FeeTable` and `AuditTrail` in the `app` package print a line from their static initializers.",
     "Predict: does either line print during the scan? Then run it.",
     "Set `INITIALIZE = true` and run it again. Then look at the last two lines: the same package in two JAR files."
    ],
    "code": demo("ScanDemo"),
    "expect": "With `INITIALIZE = false` no initializer runs. The scan lists nine components (`MoneyFormat` and the interface are skipped) and reports about 270 classes loaded (200 in the Kotlin run, which had loaded more before it started counting). With `true`, `FeeTable.<clinit>: loading 40,000 fee rows` and `AuditTrail.<clinit>: opening the audit file` print in the middle of the scan, although nothing has asked for either component. The JAR with directory entries gives one `jar:` root; the files-only JAR gives none."
   },
   "refs": [
    {"title": "ClassLoader.getResources (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/ClassLoader.html", "kind": "docs"}
   ]
  },
  {
   "h": "Pick one constructor, then walk the graph depth first",
   "body": """A container must never guess which constructor to call, because reflection gives you no order to rely on. The lab's rule is the one most containers use: if exactly one public constructor carries `@Inject`, use it; if there is only one public constructor, use that; otherwise refuse with a message that says what to do.

Kotlin makes "only one public constructor" harder than it looks. `class KotlinFees(val rates: FxRates, val bps: Int = 290)` has two public constructors on the JVM: yours, and a synthetic `KotlinFees(FxRates, int, int, DefaultConstructorMarker)` that Kotlin callers use when they leave out `bps`. It is the `$default` trick from *Reading bytecode: javap, the operand stack and Kotlin's output*, applied to a constructor. Skip it with `isSynthetic()`. When every parameter has a default, kotlinc adds a third, a real public no-argument constructor, and in this track's run it copied `@Inject` onto that one too. The container then sees two marked constructors and refuses. Don't give injected parameters defaults.

Parameters are resolved by type, not by name. Class files don't keep parameter names unless javac runs with `-parameters` (`-java-parameters` for kotlinc), so reflection reports `arg0` and `arg1`. A parameter of interface type, such as `CardIssuerClient`, resolves to the one component that implements it. None or two is an error.

Now the order. Visit a component, visit everything its constructor needs, and only then append the component to the list. This is a **depth-first, post-order** walk, and the result is a creation order in which every class comes after its dependencies. A shared dependency is appended once, because the walk skips classes that are already done.

The same walk finds cycles. Keep a path: the components you are inside right now. If you reach a component that is on the path, you've come back to something that is still waiting for its own dependencies. Report the slice of the path from that component back to itself:

```text
Dependency cycle: Payouts -> Statements -> Reconciler -> Payouts
```

The lab's container computes this order in its constructor. A cycle or a missing dependency then fails the deploy, not the first payment of the night. Creating the objects can still wait until someone asks for them.""",
   "figure": {"svg": FIGURE, "caption": "The demo app's graph. Depth-first post-order numbers it: IssuerConfig and FxRates have no dependencies and come first, PaymentService comes last."},
   "try": {
    "title": "Predict the order, then make a cycle",
    "minutes": 5,
    "steps": [
     "Read `GraphDemo`. The scan returns the components in name order, and the walk starts from each in turn. Write down the creation order you expect.",
     "Run it and compare. Then run the Kotlin twin, which ends with two refusals.",
     "In `app/Ledger.java`, change the constructor to `public Ledger(PaymentService payments) {}`. Predict the cycle message, then run `GraphDemo` again."
    ],
    "code": demo("GraphDemo"),
    "expect": "The order is `[AuditTrail, FxRates, FeeCalculator, FeeTable, IssuerConfig, HttpIssuerClient, Ledger, PaymentService, PayoutJob]`: `FxRates` lands right before `FeeCalculator` because the walk reaches it from there. Neither static initializer prints, because nobody asked for `PayoutJob`. The Kotlin twin prints `Dependency cycle: GPayouts -> GStatements -> GReconciler -> GPayouts` and `GFeeRules has 2 @Inject constructors; keep one`. With your change, the scan fails with `Dependency cycle: Ledger -> PaymentService -> Ledger`. Undo the change afterwards."
   },
   "refs": [
    {"title": "Kotlin docs: Classes and constructors", "url": "https://kotlinlang.org/docs/classes.html", "kind": "docs"}
   ]
  },
  {
   "h": "One singleton per container, even when eight threads ask first",
   "body": """A **singleton** component has one instance per container, created the first time someone needs it. A **prototype** component is created again on every request. Singleton is the default, and it is where the bugs are, because the first request often arrives on eight threads at once.

The map from the first Try it is check-then-act, the race from *Race conditions: why count++ lies*. Every thread that reads `null` before the first `put` builds its own `FxRates`. In `SingletonRaceDemo` all eight threads did, and got eight different objects.

`ConcurrentHashMap.computeIfAbsent` looks like the fix, but a container calls it recursively: building `payouts` means building `ledger` first, from inside the mapping function. The Javadoc forbids that: the function must not modify the map. In practice it works when the two keys land in different bins of the map's table and throws `IllegalStateException: Recursive update` when they share one. With `Class` keys the bin depends on identity hash codes, so the same container fails on some starts and not others.

The JVM has its own lazy singleton, the holder idiom from *Why the JVM starts slowly, and how to measure it*: a nested class whose `static final` field is set on first use, under the class initialization lock. It is the best tool when you can write one holder class per singleton before compiling. A reflective container can't, because it learns its components at run time. Lesson 3 generates those holder classes.

So the lab gives each singleton a cell that uses double-checked locking, the pattern *Lazy init done right: double-checked locking and holders* proved correct:

```java
T value = instance;                    // volatile read: no lock once it is built
if (value == null) {
    synchronized (this) {
        value = instance;              // someone may have built it while we waited
        if (value == null) instance = value = factory.get();
    }
}
return value;
```

```kotlin
var value = instance                   // @Volatile var instance: T? = null
if (value == null) {
    synchronized(this) {
        value = instance
        if (value == null) { value = factory(); instance = value }
    }
}
return value!!
```

`volatile` is what makes the unlocked first read safe: a thread that reads a non-null reference also sees every write the constructor made before the reference was stored. Without it, a thread could see the reference and still read the new object's fields as zero.

Building `PaymentService` holds its cell's lock while it builds `FeeCalculator`, which takes another lock. Nested locks usually mean deadlock risk. Here every lock is taken along an arrow of the graph, from a component to something it needs. Two threads could only wait for each other if the arrows formed a loop, and the constructor already rejected loops. One more difference from a holder: if the factory throws, the cell stays empty and the next `get` tries again. A static initializer that throws fails once and gives `NoClassDefFoundError` from then on.""",
   "try": {
    "title": "Race for the first FxRates",
    "minutes": 4,
    "steps": [
     "Read `SingletonRaceDemo` (or the Kotlin twin). Each row releases eight threads at the same moment, and `FxRates` takes 20 ms to build.",
     "Predict the two numbers on each of the first two rows, and which `computeIfAbsent` line fails.",
     "Run it twice. Do the numbers change?"
    ],
    "code": demo("SingletonRaceDemo"),
    "expect": "`check-then-act on a map  constructor ran 8 times, threads saw 8 instance(s)` (sometimes slightly fewer), then `SingletonCell ... 1 times ... 1 instance(s)` on every run. `paymentService needs feeCalculator: worked`, but `payouts needs ledger: java.lang.IllegalStateException: Recursive update`, because those two strings hash into the same bin of a 16-bin table. Change either name and the result may flip. That is why nobody should rely on it."
   },
   "refs": [
    {"title": "ConcurrentHashMap.computeIfAbsent (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ConcurrentHashMap.html", "kind": "docs"}
   ]
  }
 ],
 "analogy": "A container is a kitchen's prep list. Every dish card lists what it needs, and the prep cook sorts the cards so stocks are made before the sauces that use them. A singleton is the one pot of stock that every dish ladles from; a prototype is a garnish made fresh for each plate. A card that needs a sauce that needs the same card is a cycle, and a good prep cook refuses it at the start of the shift, not at the first order. The analogy breaks at improvisation: a cook can make do when a card is unclear, while a container that guesses which constructor you meant is a bug.",
 "in_your_world": "Your Quarkus services already run a container: ArC reads your `@ApplicationScoped` and `@Inject` declarations, works out the graph, and reports an unsatisfied dependency when you build, not when the pod starts. Spring Boot does the same work at start-up, with a class path scan and reflection, and since Boot 2.6 it refuses circular references by default. The lab's container is the Spring shape in about 200 lines. The habits carry over directly: keep constructors cheap, keep static initializers empty, give every Kafka consumer, issuer client and ledger repository its collaborators through the constructor, and read a cycle error as a design smell.",
 "mistake": "The most common mistake is \"fixing\" a cycle error instead of the cycle. `Ledger` needs `AuditTrail` and `AuditTrail` needs `Ledger`, the container refuses, and someone switches one side to field injection or a lazy lookup so the error goes away. The two classes still can't exist without each other: you've moved the failure from start-up to the first call that finds a half-built object. People do it because the error appears at the worst moment, in the middle of a feature. The fix is to ask what each side needs while it is being built. Usually a third class (the store both of them read) breaks the loop, as the worked example shows.",
 "compare": {
  "title": "The same component in Java and Kotlin, as reflection sees it",
  "java": {
   "title": "FeeCalculator.java",
   "src": "@Component\npublic class FeeCalculator {\n    private final FxRates rates;\n    private final int bps;\n\n    @Inject                                    // two public constructors: say which one\n    public FeeCalculator(FxRates rates) {\n        this(rates, 290);\n    }\n\n    public FeeCalculator(FxRates rates, int bps) {\n        this.rates = rates;\n        this.bps = bps;\n    }\n}\n// getConstructors(): (FxRates) and (FxRates, int). No synthetic ones."
  },
  "kotlin": {
   "title": "FeeCalculator.kt",
   "src": "@Component\nclass FeeCalculator(private val rates: FxRates, private val bps: Int = 290)\n\n// getConstructors():\n//   FeeCalculator(FxRates, int)\n//   FeeCalculator(FxRates, int, int, DefaultConstructorMarker)   synthetic, skip it\n// The container picks (FxRates, int), then can't find a component for int.\n// Give bps no default, or move it into a FeeRules component."
  },
  "note": "Java gives you exactly the constructors you write. Kotlin's default arguments are compiled into an extra public synthetic constructor, and if every parameter has a default, into a real no-argument constructor as well, which receives the same annotations. So a container must filter `isSynthetic()` and must not be fooled by an `@Inject` that kotlinc copied. In both languages the class file keeps no parameter names by default, so the container resolves by type. The Kotlin class is also `final`, which is harmless here and becomes the main problem in lesson 2."
 },
 "worked": {
  "title": "Break a cycle the container reported",
  "steps": [
   {
    "say": "The container refuses to start with `Dependency cycle: Ledger -> AuditTrail -> Ledger`. Here are the two constructors. Read them and ask what each one needs while it is being built, and what it only needs later, inside a method.",
    "code": "@Component\npublic class Ledger {\n    private final LedgerStore store = new LedgerStore();   // hidden inside\n    private final AuditTrail audit;\n    public Ledger(AuditTrail audit) { this.audit = audit; }\n    public void post(Entry e) { store.add(e); audit.record(e); }\n    public long balance(String account) { return store.balance(account); }\n}\n\n@Component\npublic class AuditTrail {\n    private final Ledger ledger;\n    public AuditTrail(Ledger ledger) { this.ledger = ledger; }\n    public void record(Entry e) { if (ledger.balance(e.account()) < 0) alert(e); }\n}",
    "lang": "java",
    "alt_lang": "kotlin",
    "alt_code": "@Component\nclass Ledger(private val audit: AuditTrail) {\n    private val store = LedgerStore()                      // hidden inside\n    fun post(e: Entry) { store.add(e); audit.record(e) }\n    fun balance(account: String): Long = store.balance(account)\n}\n\n@Component\nclass AuditTrail(private val ledger: Ledger) {\n    fun record(e: Entry) { if (ledger.balance(e.account) < 0) alert(e) }\n}"
   },
   {
    "say": "`AuditTrail` doesn't need a `Ledger` at all. It needs balances, which live in the ledger's store. `Ledger` needs the store to write to and the audit trail to notify. The loop exists because the store is hidden inside `Ledger`."
   },
   {
    "say": "Give the store its own component. Both classes depend on it, and the arrows no longer close a loop: `LedgerStore` is created first, then `AuditTrail`, then `Ledger`.",
    "code": "@Component\npublic class LedgerStore {\n    public void add(Entry e) { /* ... */ }\n    public long balance(String account) { /* ... */ return 0; }\n}\n\n@Component\npublic class AuditTrail {\n    private final LedgerStore store;\n    public AuditTrail(LedgerStore store) { this.store = store; }\n    public void record(Entry e) { if (store.balance(e.account()) < 0) alert(e); }\n}\n\n@Component\npublic class Ledger {\n    private final LedgerStore store;\n    private final AuditTrail audit;\n    public Ledger(LedgerStore store, AuditTrail audit) { this.store = store; this.audit = audit; }\n    public void post(Entry e) { store.add(e); audit.record(e); }\n}",
    "lang": "java",
    "alt_lang": "kotlin",
    "alt_code": "@Component\nclass LedgerStore {\n    fun add(e: Entry) { /* ... */ }\n    fun balance(account: String): Long = 0 /* ... */\n}\n\n@Component\nclass AuditTrail(private val store: LedgerStore) {\n    fun record(e: Entry) { if (store.balance(e.account) < 0) alert(e) }\n}\n\n@Component\nclass Ledger(private val store: LedgerStore, private val audit: AuditTrail) {\n    fun post(e: Entry) { store.add(e); audit.record(e) }\n}"
   },
   {
    "say": "If the two really do need each other at call time, production containers offer a lookup instead of an object: `jakarta.inject.Provider<Ledger>` in CDI, `ObjectProvider<Ledger>` in Spring. The constructor then receives something that finds the `Ledger` later, inside a method. The lab's container doesn't support that, on purpose. Reach for it after you've tried the split, not before."
   }
  ]
 },
 "lab": {
  "title": "Write the four decisive parts of the container",
  "minutes": 15,
  "files": [
   f"{lab}/main/{J}/Constructors.java",
   f"{lab}/main/{J}/BeanGraph.java",
   f"{lab}/main/{J}/SingletonCell.java",
   f"{lab}/main/{J}/Container.java"
  ],
  "run": "./gradlew :container:test --tests 'workbench.container.l01.*'",
  "steps": [
   "Run the tests once. Eleven of twelve fail with `UnsupportedOperationException`. The one that passes tests `ClassScanner`, which is given: read it once, it is section 2 in code. The test fixtures are a small payment app in `src/test/java/.../l01/app`.",
   "Write `Constructors.pick`. Filter `getConstructors()` with `!c.isSynthetic()`, then apply the three rules from its Javadoc. The tests check the exact messages, including two Kotlin classes from `KotlinBeans.kt`.",
   "Write `BeanGraph.creationOrder` as a depth-first, post-order walk. Keep a `Set` of finished classes and a `LinkedHashSet` path of the classes you are inside. Build the cycle message from the part of the path that starts at the repeated class.",
   "Write `SingletonCell.get` with double-checked locking on the `volatile` field.",
   "Write `Container.create`: pick the constructor, map `graph.dependenciesOf(component)` through `instanceOf`, and call `newInstance`. Then `instanceOf`: the cell's `get()` for singletons, `create` for prototypes. Run the tests until all twelve pass, then twice more."
  ],
  "hints": [
   "In `creationOrder`, check `done` before `path`. A class that is finished is not a cycle, even when two components both depend on it.",
   "A recursive helper `visit(c, done, path, order)` keeps the main method to three lines. Add `c` to `path` before visiting its dependencies and remove it after.",
   "`Constructor.newInstance` wraps whatever the constructor throws in `InvocationTargetException`. The test wants the original `IllegalStateException` as the cause of your `ContainerException`: use `e.getCause()`.",
   "If the concurrency test sees two `SlowRates`, you read `instance` once outside the lock but not again inside it."
  ],
  "done_when": "All twelve tests in `WiringTest` pass, three runs in a row."
 },
 "drill": {
  "title": "Order a graph from memory",
  "minutes": 5,
  "prompt": "Close the lab. Given `Map<String, List<String>> needs` (component name to the names its constructor needs), write `List<String> creationOrder(Map<String, List<String>> needs)` that returns each name after everything it needs, and throws `IllegalStateException(\"cycle: a -> b -> a\")` on a cycle. Then compare with the answer. Did you check `done` before the path?",
  "answer": {
   "lang": "java",
   "src": "static List<String> creationOrder(Map<String, List<String>> needs) {\n    List<String> order = new ArrayList<>();\n    Set<String> done = new HashSet<>();\n    for (String name : needs.keySet()) visit(name, needs, done, new LinkedHashSet<>(), order);\n    return order;\n}\n\nstatic void visit(String name, Map<String, List<String>> needs, Set<String> done,\n                  LinkedHashSet<String> path, List<String> order) {\n    if (done.contains(name)) return;                       // finished earlier: not a cycle\n    if (path.contains(name)) {                             // back at a name we are still inside\n        List<String> loop = new ArrayList<>(path);\n        loop = loop.subList(loop.indexOf(name), loop.size());\n        throw new IllegalStateException(\"cycle: \" + String.join(\" -> \", loop) + \" -> \" + name);\n    }\n    path.add(name);\n    for (String dep : needs.getOrDefault(name, List.of())) visit(dep, needs, done, path, order);\n    path.remove(name);\n    done.add(name);\n    order.add(name);                                       // after everything it needs\n}",
   "alt": {
    "lang": "kotlin",
    "src": "fun creationOrder(needs: Map<String, List<String>>): List<String> {\n    val order = mutableListOf<String>()\n    val done = mutableSetOf<String>()\n    val path = linkedSetOf<String>()\n\n    fun visit(name: String) {\n        if (name in done) return                           // finished earlier: not a cycle\n        if (name in path) {                                // back at a name we are still inside\n            val loop = path.dropWhile { it != name } + name\n            throw IllegalStateException(\"cycle: \" + loop.joinToString(\" -> \"))\n        }\n        path += name\n        needs[name].orEmpty().forEach(::visit)\n        path -= name\n        done += name\n        order += name                                      // after everything it needs\n    }\n\n    needs.keys.forEach(::visit)\n    return order\n}"
   }
  }
 },
 "recap": [
  "A container does the wiring block of `main` for you: it finds the components, builds each one from its constructor, and decides how many instances exist.",
  "A scan uses `ClassLoader.getResources` on the package path and `Class.forName(name, false, loader)`, so no static initializer runs; `@Component` needs `@Retention(RUNTIME)`. Every scanned class is loaded on every start, and a JAR without directory entries scans as empty.",
  "Pick the `@Inject` constructor or the only public one, never \"the first\". Kotlin adds a synthetic constructor for default arguments, and a no-argument one (carrying your annotations) when every parameter has a default.",
  "Create components in depth-first post-order. A path of the components you are inside finds cycles, and the slice from the repeated class is the error message. Check the graph in the container's constructor.",
  "A singleton is one instance per container. Check-then-act on a map builds duplicates, and a recursive `computeIfAbsent` can throw `Recursive update`. A cell with double-checked locking on a `volatile` field builds exactly one, and can't deadlock on an acyclic graph."
 ],
 "quiz": [
  {
   "q": "Your scanner calls `Class.forName(name)`, with one argument, for every class in `com.acme.pay`. `FeeTable` has `static final Map<String, Fee> ROWS = loadFromDisk();` and is never injected anywhere. When does `loadFromDisk()` run?",
   "options": [
    "Never, because nothing injects `FeeTable`",
    "During the scan, because the one-argument `forName` initializes every class it loads",
    "When the JIT compiles `FeeTable`",
    "Only if `FeeTable` is annotated `@Component`"
   ],
   "answer": 1,
   "why": "The one-argument `Class.forName` loads, links and initializes, so `<clinit>` runs during the scan for every class in the package, component or not. `Class.forName(name, false, loader)` loads and links without initializing. Being a component doesn't matter either way: the scan only checks the annotation after the class is loaded.",
   "from": "cls-01"
  },
  {
   "q": "A container resolves constructor parameters by name with `Parameter.getName()`. Gradle compiles `PaymentService(CardIssuerClient issuer, Ledger ledger)` with javac's default options. What names does the container see?",
   "options": [
    "`arg0` and `arg1`",
    "`issuer` and `ledger`",
    "`CardIssuerClient` and `Ledger`",
    "A `NoSuchFieldException`, because the names are private"
   ],
   "answer": 0,
   "why": "Method descriptors carry types, not names, and javac only writes a `MethodParameters` attribute when you pass `-parameters` (`-java-parameters` for kotlinc). Without it, reflection makes up `arg0`, `arg1`. That's why the lab resolves by type: the type is always in the descriptor.",
   "from": "cls-02"
  },
  {
   "q": "A service's container scans 4,000 classes at start-up, though only 300 are components, and none of the 4,000 has a static initializer. What does the scan add to every start?",
   "options": [
    "Nothing, because classes without static initializers are free",
    "Only the cost of calling 300 constructors",
    "Finding, parsing and verifying 4,000 classes, and reading their annotations",
    "A garbage collection to unload the 3,700 non-components"
   ],
   "answer": 2,
   "why": "Loading is the expensive part even without initialization: the JVM finds each class file, parses it into metaspace and verifies its bytecode, on every launch. The 3,700 non-components stay loaded; nothing unloads classes of the application loader. Initialization would add the static initializers on top.",
   "from": "boot-01"
  },
  {
   "q": "A teammate's `SingletonCell` uses double-checked locking, but the `instance` field is a plain field, not `volatile`. What can go wrong?",
   "options": [
    "Two threads can both run the factory",
    "The nested locks can deadlock",
    "Nothing on x86, so it is fine in production",
    "A thread can see a non-null reference and still read the new object's fields as zero"
   ],
   "answer": 3,
   "why": "The lock makes the factory run once. What the unlocked first read lacks is a happens-before edge to the constructor's writes: without `volatile`, the reference can become visible before the fields it points to. `volatile` on the field gives that edge. \"It works on x86\" describes one CPU and one JIT, not what the memory model allows.",
   "from": "jmm-05"
  },
  {
   "q": "`Ledger` needs `AuditTrail`, `AuditTrail` needs `PaymentService`, and `PaymentService` needs `Ledger`. The container is built with the list `[Ledger, PaymentService, AuditTrail]`. What message does the lab's `creationOrder` throw?",
   "options": [
    "`Dependency cycle: Ledger -> AuditTrail -> PaymentService -> Ledger`",
    "`Dependency cycle: PaymentService -> Ledger -> AuditTrail -> PaymentService`",
    "A `StackOverflowError`, because the walk never ends",
    "`Dependency cycle: Ledger -> PaymentService -> AuditTrail -> Ledger`"
   ],
   "answer": 0,
   "why": "The walk starts at the first component in the list, `Ledger`, follows its constructor to `AuditTrail`, then to `PaymentService`, and then reaches `Ledger`, which is still on the path. The message is the path from the repeated class back to itself, in the order the walk went. Without a path the recursion would overflow the stack, which is what the ten-line container from section 1 does."
  }
 ],
 "flashcards": [
  {"front": "What does `Class.forName(name, false, loader)` do that `Class.forName(name)` doesn't?", "back": "It loads and links the class without initializing it, so no static initializer runs. A scanner should always pass `false`."},
  {"front": "Why does `@Component` need `@Retention(RUNTIME)`?", "back": "With the default `CLASS` retention the annotation is in the class file, but reflection can't see it, so `isAnnotationPresent` returns false."},
  {"front": "Kotlin `class Fees(val rates: FxRates, val bps: Int = 290)`: how many public constructors does `getConstructors()` return?", "back": "Two: `(FxRates, int)` and a synthetic `(FxRates, int, int, DefaultConstructorMarker)` for default arguments. Filter with `isSynthetic()`."},
  {"front": "In what order does a container create components?", "back": "Depth-first post-order: each component after everything its constructor needs. Shared dependencies appear once."},
  {"front": "How does a depth-first walk detect a dependency cycle?", "back": "It keeps a path of the components it is still inside. Reaching one of them again is a cycle; the path from that component back to itself is the message."},
  {"front": "Why not build a container's singletons with a recursive `ConcurrentHashMap.computeIfAbsent`?", "back": "The mapping function must not modify the map. If the inner key lands in the same bin, it throws `IllegalStateException: Recursive update`, and with `Class` keys that depends on identity hash codes."},
  {"front": "Why can nested `SingletonCell` locks not deadlock?", "back": "Each lock is taken along a dependency arrow, from a component to what it needs. A deadlock would need the arrows to form a loop, and the container rejects cycles at start-up."}
 ],
 "terms": [
  {"term": "Dependency injection", "plain": "A class receives the objects it needs, usually through its constructor, instead of creating them itself."},
  {"term": "Component", "plain": "A class the container creates and hands to others. Spring and CDI call the instances beans."},
  {"term": "Container", "plain": "The code that finds components, works out the order to build them in, builds them and keeps the shared ones."},
  {"term": "Scope", "plain": "How many instances of a component exist: one per container (singleton) or a new one per request (prototype)."},
  {"term": "Creation order", "plain": "A list of all components in which each one comes after everything it depends on. Also called a topological order."},
  {"term": "Class path scan", "plain": "Finding classes by asking a class loader for a package directory and loading every class file in it."},
  {"term": "Double-checked locking", "plain": "Read a volatile field without a lock; only if it is empty, lock, read again, and build. Fast after the first call."}
 ],
 "explain_back": {
  "prompt": "A colleague asks why the container's constructor walks the whole graph when it could just create things lazily on the first `get`. Explain what the walk gives you, what still happens lazily, and why the two together are a good trade.",
  "answer": "The walk only reads constructors and resolves types, so it is cheap. It proves at start-up that every dependency has exactly one provider, that every class has a constructor the container can call, and that there are no cycles, and it gives the creation order. A broken graph then fails the deploy with a clear message instead of failing the first request that happens to touch the bad part. What stays lazy is running the constructors: a singleton is built on first use, inside its cell, so start-up doesn't pay for components nobody uses. The trade is that a constructor that throws still surprises you on first use, which is why constructors should only store their arguments."
 },
 "deeper": {
  "minutes": 10,
  "body": """Spring creates singletons eagerly at the end of start-up by default, after the scan and the graph work, so that a constructor that throws stops the deploy too. The lab's container is lazy, like a CDI client proxy that creates its bean on the first method call. Neither is wrong; they put the same failure at different times.

Spring can also resolve some cycles that the lab refuses. With field or setter injection it can hand out a reference to an object whose constructor has finished but whose fields aren't all set yet, from a cache of "early" singleton references. Constructor injection can never do that, because the object doesn't exist until its constructor's arguments do. That is one reason constructor injection is the recommended style: an impossible graph fails loudly. Since Spring Boot 2.6, even the setter-injection kind of cycle is refused unless you set `spring.main.allow-circular-references=true`.

Three things a production container adds to this lesson's graph: qualifiers, when two components implement the same interface and the injection point must say which (`@Named`, `@Qualifier`); generic types, so that `Repository<Payment>` and `Repository<Refund>` are different dependencies (the lab compares erased classes only); and injection of lookups such as `Provider<T>`, which turn a hard edge into one that is followed at call time. Each one makes the graph work harder, and each one is easier to check at build time than at start-up, which is lesson 3's argument."""
 },
 "sources": [
  {"title": "ClassLoader (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/ClassLoader.html"},
  {"title": "Class (Java SE 25 API): forName and getConstructors", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Class.html"},
  {"title": "ConcurrentHashMap (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ConcurrentHashMap.html"},
  {"title": "Kotlin docs: Classes and constructors", "url": "https://kotlinlang.org/docs/classes.html"},
  {"title": "Quarkus: Contexts and Dependency Injection reference", "url": "https://quarkus.io/guides/cdi-reference"}
 ]
}

out = ROOT / "content/lessons/cap4-01.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print("wrote", out)
