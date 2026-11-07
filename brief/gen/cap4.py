import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")

INTRO = """Across three sittings you build one program: a small dependency injection container for a payment app. Lesson 1 wires classes by reflection: it finds the components from a list or a class path scan, picks each constructor, orders the graph with a readable cycle error, and gives every singleton exactly one instance when eight threads ask at once. Lesson 2 adds `@Timed` and `@Retry`, through a JDK proxy for components with interfaces and a Byte Buddy subclass for the rest, and refuses at start-up what Kotlin's final classes would otherwise break in silence. Lesson 3 measures the result per call with JMH and at start-up with `-Xlog:class+load`, looks inside the running container with a class histogram and a heap dump, then generates the same wiring as plain Java at build time and archives what is left with AppCDS and the AOT cache. At the end you can defend, with numbers you measured, why Spring wires at run time and why Quarkus and Micronaut moved the work to the build.

The capstone draws on every track of this part: class loading, reflection and proxies from *Class loading, bytecode and dynamic proxies*; escape analysis, histograms and heap dumps from *Memory and garbage collection*; JMH and the JIT tiers from *JIT, profiling and benchmarking*; class counts, CDS and the AOT cache from *Startup and footprint*. The holder idiom and double-checked locking come from the memory model track. Each lesson names the earlier lesson it leans on, so you can go back for a mechanism when you need it.

The labs live in `labs/container`, one package per lesson (`workbench.container.l01` to `l03`). Lessons 1 and 3 are Java; lesson 2 is Kotlin, on top of lesson 1's Java container. Each lesson's starter code contains the previous lesson's solution, so you can start any sitting fresh. The tests check behaviour, never time: creation order, cycle messages, one instance under concurrent first access, retry counts, proxy identity, and a generated registry that wires the same graph as the reflective container. Run `./gradlew :container:test --tests 'workbench.container.lNN.*'` from `labs/`, and `./gradlew :container:solutionTest` for the reference answers. The demos run the reference container from `src/solution`, so they work before you finish a lab. Lesson 3's demos start child JVMs and take about ten seconds; its AOT cache commands need JDK 25.0.4 or later and say so."""

CHEAT = """## The program in one picture

`ClassScanner` (or a list) finds the components, `Constructors` picks one constructor each, `BeanGraph` orders them depth first, `Container` builds them lazily in `SingletonCell`s, `Interception` wraps the ones with `@Timed` or `@Retry`, and `RegistryGenerator` writes all of it as Java at build time.

## Finding and building components

| Decision | The lab's choice | Why |
|---|---|---|
| Which classes | A list, or a scan with `ClassLoader.getResources(packagePath)` | A scan loads every class in the package on every start |
| Loading them | `Class.forName(name, false, loader)` | `true` runs every static initializer during the scan |
| Seeing `@Component` | `@Retention(RUNTIME)` | The default `CLASS` retention is invisible to reflection |
| JARs | Need directory entries | A files-only JAR scans as empty, with no error |
| Constructor | The `@Inject` one, or the only public one; never "the first" | Reflection gives no order to rely on |
| Kotlin | Skip `isSynthetic()` constructors; don't default injected parameters | All-default parameters add a no-arg constructor that also gets `@Inject` |
| Parameters | By type, interface to its one implementation | Class files keep no parameter names without `-parameters` |

## Order, cycles, scopes

- Creation order: depth-first post-order; each component after everything it needs; shared ones once.
- Cycle: keep the path you are inside; meeting a class on it again is the cycle. Report from the repeated class: `Dependency cycle: Payouts -> Statements -> Payouts`.
- Check the whole graph in the container's constructor; create objects lazily.
- Singleton: one per container. Not check-then-act on a map (duplicates), not recursive `computeIfAbsent` (`Recursive update`). A cell with double-checked locking on a `volatile` field; nested cell locks can't deadlock on an acyclic graph; a failed factory retries.
- Prototype: new on every get; a singleton that depends on it keeps the one it got.

## Interception

| Component | Proxy | Self-calls | Breaks on |
|---|---|---|---|
| Implements an interface | JDK proxy around a separate target | Not intercepted | Annotations on the class, `get(ImplClass)` |
| No interface | Byte Buddy subclass, built with the real constructor arguments | Intercepted | `final` classes, `final` or `private` methods (Kotlin's default) |

- Handler, in order: `Object` methods by identity; defaults through `invokeDefault`; the chain ending in `method.invoke(target, args)`; unwrap `InvocationTargetException`.
- Chain: `@Timed` outside `@Retry`, so the time includes every attempt. Retry only listed failures, rethrow the original, and only calls that carry an idempotency key. Nested retries multiply.
- Kotlin: `open` class and methods, all-open (or kotlin-spring), or an interface. Refuse the rest at start-up.

## Measure

| Question | Tool | This app's numbers (JDK 21) |
|---|---|---|
| Cost per call | JMH with `-prof gc`, read B/op | direct 0, generated 0, Byte Buddy 160, JDK proxy 208 |
| Classes at start | `-Xlog:class+load`, count by `source:` | reflective 2,207, generated 991 |
| Made at run time | `__dynamic_proxy__`, `__JVM_DefineClass__`, hidden classes | 30 proxies, 3 Byte Buddy classes, 123 hidden |
| What is alive | `jcmd <pid> GC.class_histogram` | 13 `SingletonCell`, 1 `ByteArrayClassLoader`, 119 proxy objects |
| Who holds it | `jcmd <pid> GC.heap_dump file.hprof`, MAT path to GC roots | cell, map, container, `main`'s local |

## Build time

- Run the same graph code in the build; a cycle fails the build.
- Holder class per singleton (lazy, thread-safe under the class init lock), factory per prototype, identity checks in `get`, interceptors written as source with chains from annotation values.
- Costs: a generator in the build, a component set fixed per artifact, holders that fail with `NoClassDefFoundError` until restart if a constructor throws, checked-exception constructors need wrapping.
- AppCDS and the AOT cache archive classes from JARs, not proxies (`Unsupported location`) or classes a custom loader defines. Generated wiring leaves almost nothing to make at start, and suits native image.

## Review questions for any container

1. What does it do at start-up that depends only on the classes?
2. Which of my methods are really intercepted, and how did I check?
3. What allocates per call on the hot path, in B/op?
4. How many classes does a cold start load, and how many are made at run time?
5. What fails at build time, what at start-up, and what on first use?"""

RECAP = [
 "A container automates the wiring block of `main`: find the components, build each one from its constructor, and decide how many instances exist.",
 "Scan with `getResources` and `Class.forName(name, false, loader)`; `@Component` needs `RUNTIME` retention, and every scanned class is loaded on every start.",
 "Pick the `@Inject` or only public constructor, skip Kotlin's synthetic ones, resolve by type, and order the graph depth-first post-order with a path that names any cycle.",
 "A singleton cell with double-checked locking on a `volatile` field builds one instance under concurrent first access; check-then-act and recursive `computeIfAbsent` don't.",
 "Interfaces get a JDK proxy (identity `equals`, `invokeDefault`, unwrap exceptions, annotations on the interface); classes get a Byte Buddy subclass that intercepts self-calls but not final members.",
 "Kotlin is final by default: open the class and methods, use all-open, or add an interface, and let the container refuse what it can't intercept instead of skipping it.",
 "Per call, proxies cost a few hundred bytes at most (B/op is the stable number); at start-up the reflective container loaded 2,207 classes against 991 for generated wiring.",
 "Generated wiring does the graph work in the build and wires with holders and `new`; it gives up run-time flexibility and a failed holder stays failed until restart.",
 "A class histogram says what is alive, a heap dump says who holds it; the container held its beans and Byte Buddy's loader, while JDK proxy classes and annotation instances stay for the life of the app loader.",
 "Archives and caches help most when little is made at run time: AppCDS skips proxies and custom-loader classes, so build-time wiring and an AOT cache work best together."
]

QUIZ = [
 {
  "q": "A teammate's scanner finds no components in production, though the same code finds twelve in the IDE. Production runs from a JAR built by a custom packaging step. What do you check first?",
  "options": ["Whether `@Component` has `@Retention(RUNTIME)`", "Whether the JAR has directory entries for the package", "Whether the classes are compiled with `-parameters`", "Whether the JIT has compiled the scanner"],
  "answer": 1,
  "why": "`getResources(\"com/acme/pay\")` finds a package in a JAR only through the directory's own entry. The IDE runs from a build directory, where every package is a real directory. A retention problem would fail in the IDE too.",
  "from": "cap4-01"
 },
 {
  "q": "Kotlin: `class FeeRules @Inject constructor(val bps: Int = 290, val currency: String = \"EUR\")`. What does the lab's `Constructors.pick` do?",
  "options": ["Picks the primary constructor", "Picks the no-argument constructor", "Refuses: there are two `@Inject` constructors", "Picks the synthetic `DefaultConstructorMarker` constructor"],
  "answer": 2,
  "why": "When every parameter has a default, kotlinc adds a public no-argument constructor, and it copied `@Inject` onto it. The synthetic one is filtered out, but two real marked constructors remain. Don't give injected parameters defaults.",
  "from": "cap4-01"
 },
 {
  "q": "Eight request threads call `get(FxRates.class)` on a fresh container at the same moment. Which implementation builds exactly one `FxRates`?",
  "options": ["`if (map.get(t) == null) map.put(t, create(t))` on a `ConcurrentHashMap`", "A recursive `map.computeIfAbsent(t, this::create)`", "A per-component cell: volatile read, then lock, read again, create", "`synchronized` only around `map.put`"],
  "answer": 2,
  "why": "Check-then-act lets every thread that saw `null` create one, and a lock around `put` alone keeps that gap. A recursive `computeIfAbsent` may throw `Recursive update` when keys share a bin. The cell re-checks under its lock, so only the first thread runs the factory.",
  "from": "jmm-05"
 },
 {
  "q": "`CardIssuerClient` is implemented by a final Kotlin class `HttpIssuerClient`, with `@Retry` on the interface method `authorize`. What does the lab's container do?",
  "options": ["Refuses: the class is final", "Wraps it in a JDK proxy; finality doesn't matter, and retries work", "Builds a Byte Buddy subclass", "Creates it without interception"],
  "answer": 1,
  "why": "A component with an interface gets a JDK proxy, which only needs the interface. Finality only matters for subclass proxies. The bean is then a `$ProxyN`, so callers must ask for `CardIssuerClient`, not `HttpIssuerClient`.",
  "from": "cap4-02"
 },
 {
  "q": "A forwarding proxy's handler sends `equals` to the target like every other method. What breaks?",
  "options": ["`proxy.equals(proxy)` is false, so `ArrayList.remove(proxy)` fails", "`hashCode` throws `UndeclaredThrowableException`", "Nothing, because collections compare references first", "The proxy class can't be generated"],
  "answer": 0,
  "why": "The target is asked whether it equals the proxy, and it doesn't. `HashSet` happens to survive because `HashMap` compares references before calling `equals`; `ArrayList` doesn't. Answer `equals` and `hashCode` by proxy identity.",
  "from": "cls-04"
 },
 {
  "q": "Kotlin `open class Payouts { @Timed fun pay(id: String) {} }` is wired by a container that builds Byte Buddy subclasses without a start-up check. What happens on `pay`?",
  "options": ["Byte Buddy refuses the class", "It runs untimed, with no error, because `pay` is final", "It is timed, because the class is open", "A `VerifyError` when the subclass loads"],
  "answer": 1,
  "why": "`open` on a class doesn't open its members. A subclass can't override a final method, so Byte Buddy leaves it alone and the annotation does nothing. The lab's container checks intercepted methods for `final` and refuses at start-up.",
  "from": "cls-05"
 },
 {
  "q": "Which number from `ProxyCallBench` belongs in a CI check that the issuer proxy hasn't become more expensive?",
  "options": ["ns/op of the JDK proxy row", "The ratio of the JDK proxy time to the direct time", "B/op (`gc.alloc.rate.norm`) with a small margin", "The number of JIT compilations"],
  "answer": 2,
  "why": "On a shared machine the time error was larger than most scores, while bytes per operation came out the same on every run. Keep a margin, because a JDK upgrade or a longer chain can change what escape analysis removes.",
  "from": "perf-03"
 },
 {
  "q": "With a dynamic AppCDS archive on JDK 21, the reflective container still logs 30 `__dynamic_proxy__` and 3 `__JVM_DefineClass__` classes at every start. Why?",
  "options": ["The archive was built with the wrong JDK", "Those classes are made at run time and have no location an archive can verify", "AppCDS only stores JDK classes", "The training run was too short"],
  "answer": 1,
  "why": "At dump time JDK 21 skips each proxy class with `Unsupported location`, and Byte Buddy's subclass is defined from bytes by its own class loader. Classes from JARs, Byte Buddy's own included, do come from the archive.",
  "from": "boot-02"
 },
 {
  "q": "After the reflective container is dropped and a GC runs, which of these is still loaded?",
  "options": ["The Byte Buddy subclass", "Byte Buddy's `ByteArrayClassLoader`", "The JDK proxy class for `CardIssuerClient`", "The `SingletonCell` objects"],
  "answer": 2,
  "why": "Nothing outside the container pointed at the Byte Buddy object, its class or its loader, so the whole chain was collected. The JDK proxy class was defined in the application class loader and is cached by `Proxy` for that loader, so it stays as long as the application runs.",
  "from": "mem-07"
 },
 {
  "q": "Design review: a service starts once a week, runs for days, and loads payment-method plugins from a directory chosen at start-up. Which wiring fits best?",
  "options": ["Run-time wiring: the component set isn't known until start-up, and one slow start a week costs little", "Build-time wiring: it is always faster", "Native image: it starts fastest", "No container: wire everything by hand in `main`"],
  "answer": 0,
  "why": "Build-time wiring needs the component set when you build, and plugins chosen at start-up break that. With one start a week, the 2,000-class start-up cost is paid rarely. Build-time wiring and native image pay off for services that start often or must meet a tight readiness budget.",
  "from": "cap4-03"
 }
]

T = {"id": "cap4", "intro": INTRO, "cheatsheet": CHEAT, "recap": RECAP, "quiz": QUIZ}
out = ROOT / "content/tracks/cap4.json"
out.write_text(json.dumps(T, indent=1, ensure_ascii=False) + "\n")
print("wrote", out)
