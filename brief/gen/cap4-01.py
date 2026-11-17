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


FIG_PLAN = """<svg viewBox="0 0 700 230" role="img" aria-label="The container we will build over three sittings. Lesson 1: find the parts from a list or a scan, read each constructor, put the parts in order, and build each shared part once. Lesson 2: wrap some parts in proxies. Lesson 3: measure all of it, then do the same work at build time.">
<text class="t t-a" x="290" y="40" text-anchor="middle">lesson 1: wire the parts by reflection</text>
<rect class="box-a" x="10" y="60" width="120" height="54" rx="8"/><text class="t" x="70" y="84" text-anchor="middle">find the parts</text><text class="t-s t-m" x="70" y="103" text-anchor="middle">list or scan</text>
<rect class="box-a" x="148" y="60" width="140" height="54" rx="8"/><text class="t" x="218" y="84" text-anchor="middle">read constructors</text><text class="t-s t-m" x="218" y="103" text-anchor="middle">pick one each</text>
<rect class="box-a" x="306" y="60" width="110" height="54" rx="8"/><text class="t" x="361" y="84" text-anchor="middle">put in order</text><text class="t-s t-m" x="361" y="103" text-anchor="middle">refuse a loop</text>
<rect class="box-a" x="434" y="60" width="125" height="54" rx="8"/><text class="t" x="496" y="84" text-anchor="middle">build each once</text><text class="t-s t-m" x="496" y="103" text-anchor="middle">one cell per part</text>
<rect class="box-b" x="577" y="60" width="113" height="54" rx="8"/><text class="t" x="633" y="84" text-anchor="middle">add proxies</text><text class="t-s t-m" x="633" y="103" text-anchor="middle">lesson 2</text>
<line class="ln" x1="130" y1="87" x2="146" y2="87" marker-end="url(#arr)"/>
<line class="ln" x1="288" y1="87" x2="304" y2="87" marker-end="url(#arr)"/>
<line class="ln" x1="416" y1="87" x2="432" y2="87" marker-end="url(#arr)"/>
<line class="ln" x1="559" y1="87" x2="575" y2="87" marker-end="url(#arr)"/>
<rect class="box-dim" x="10" y="150" width="680" height="54" rx="8"/>
<text class="t" x="350" y="174" text-anchor="middle">lesson 3: measure it, then do the same work once, at build time</text>
<text class="t-s t-m" x="350" y="193" text-anchor="middle">a generated registry of holder classes; nothing left to scan when the program starts</text>
<line class="ln-d" x1="350" y1="114" x2="350" y2="148" marker-end="url(#arr)"/>
</svg>"""

FIG_GRAPH = """<svg viewBox="0 0 700 270" role="img" aria-label="The box office's parts. BoxOffice points to RemoteBookingClient, PriceList and SalesBook; RemoteBookingClient points to BookingConfig; PriceList points to SeatingPlan. Numbers give the order in which the walk creates them, starting at BoxOffice.">
<rect class="box-a" x="20" y="112" width="140" height="40" rx="8"/><text class="t" x="90" y="137" text-anchor="middle">6 BoxOffice</text>
<rect class="box" x="235" y="32" width="190" height="40" rx="8"/><text class="t" x="330" y="57" text-anchor="middle">2 RemoteBookingClient</text>
<rect class="box" x="235" y="112" width="190" height="40" rx="8"/><text class="t" x="330" y="137" text-anchor="middle">4 PriceList</text>
<rect class="box" x="235" y="192" width="190" height="40" rx="8"/><text class="t" x="330" y="217" text-anchor="middle">5 SalesBook</text>
<rect class="box-ok" x="505" y="32" width="170" height="40" rx="8"/><text class="t" x="590" y="57" text-anchor="middle">1 BookingConfig</text>
<rect class="box-ok" x="505" y="112" width="170" height="40" rx="8"/><text class="t" x="590" y="137" text-anchor="middle">3 SeatingPlan</text>
<line class="ln" x1="160" y1="124" x2="233" y2="62" marker-end="url(#arr)"/>
<line class="ln" x1="160" y1="132" x2="233" y2="132" marker-end="url(#arr)"/>
<line class="ln" x1="160" y1="140" x2="233" y2="204" marker-end="url(#arr)"/>
<line class="ln" x1="425" y1="52" x2="503" y2="52" marker-end="url(#arr)"/>
<line class="ln" x1="425" y1="132" x2="503" y2="132" marker-end="url(#arr)"/>
<text class="t-s t-m" x="140" y="84" text-anchor="middle">via BookingClient</text>
<text class="t-s t-m" x="590" y="200" text-anchor="middle">green: needs nothing,</text>
<text class="t-s t-m" x="590" y="218" text-anchor="middle">created first</text>
<text class="t-s t-a" x="350" y="262" text-anchor="middle">arrow = "my constructor needs this"; number = creation order</text>
</svg>"""

OPENING = """Remember the theatre company from the Class loading track? It sells tickets through a box office program. Before the doors open, the program sets up its parts: a seating plan, a price list, a sales book, and a link to the city's booking service, which holds the seats for every theatre in town. The box office needs all four.

Something has to build those parts in the right order and hand each one what it needs. The easy trap is to let every class build its own helpers with `new`. It works on the first night. Then the price list and the seat finder, which picks free seats, each make a seating plan of their own, and nobody knows which one is right.

The Startup track ended with a toolbox for starting a program fast. Part 4 now ends with three sittings that build a dependency injection container: a small program that builds your objects and hands each one the other objects it needs, so classes don't build their own helpers. In this sitting, we'll find the parts, read their constructors, order them and build each shared part once. Before we start, make a guess, and keep it in mind."""

S1 = """Most programs start with a block like this somewhere near `main`. Here it sets up the box office:

```java
BookingConfig config = new BookingConfig();
SeatingPlan plan = new SeatingPlan();
BoxOffice office = new BoxOffice(
        new RemoteBookingClient(config),     // talks to the city's booking service
        new PriceList(plan),
        new SalesBook());
```

```kotlin
val config = BookingConfig()
val plan = SeatingPlan()
val office = BoxOffice(
    RemoteBookingClient(config),             // talks to the city's booking service
    PriceList(plan),
    SalesBook())
```

That block is **dependency injection** done by hand. A dependency is an object that another object needs to do its job, and injecting it means handing it in from outside, here through the constructor. `BoxOffice` never calls `new` on its helpers, so a test can hand it a fake booking service and never touch the network. The block has two jobs, and both get harder as the program grows. It must build things in the right order: `config` before the booking client that reads it. And it must share the right objects: one `plan` for everyone. With six classes you do that in your head. With eighty, someone adds a constructor parameter, and the block stops compiling in three places.

Picture the theatre's front-of-house manager an hour before the doors open. Every desk in the foyer has a card that says what it needs before it can open. The box office card says "the booking link, the price list, the sales book", and the price list's card says "the seating plan". The manager reads every card, sets things out so that nothing opens before what it needs, and puts a single seating plan where everyone can reach it. A container is that manager, written in code, and the cards are the constructors.

The manager makes three decisions for each desk, and so does a container. Which classes take part? We'll call them **components**. How do you build one? Its constructor says what it needs. How many of each should exist? That's its scope. Over three sittings, we'll build a container that makes all three decisions, as the figure shows. This sitting wires the parts by reflection, the JDK's way of asking a class about itself while the program runs. The next one wraps some parts in proxies, the stand-ins from the Class loading track, to time and retry their calls. The last one measures what all of it costs, then writes the same wiring out before the program starts. Each lab begins with the previous lab's solution, so you can pick up at any sitting.

The smallest container fits in ten lines. `type.getConstructors()` returns a class's public constructors as `Constructor` objects. `getParameterTypes()` lists what one needs, and `newInstance(args)` calls it, which creates the object and runs the constructor exactly as `new` would. Build each parameter first, the same way, and you have a container:

```java
static Object build(Class<?> type) throws ReflectiveOperationException {
    Constructor<?> c = type.getConstructors()[0];          // the card: what it needs
    Object[] args = new Object[c.getParameterCount()];
    for (int i = 0; i < args.length; i++) args[i] = build(c.getParameterTypes()[i]);   // build those first
    return c.newInstance(args);                            // then the part itself
}
```

```kotlin
fun build(type: Class<*>): Any {
    val c = type.constructors[0]                           // the card: what it needs
    return c.newInstance(*c.parameterTypes.map { build(it) }.toTypedArray())   // those first, then the part
}
```

Read it as one sentence: to build a part, build everything its constructor asks for, then call the constructor. The demo hands it a box office whose `PriceList` and `SeatFinder` both need a `SeatingPlan`. By hand, `new SeatingPlan` printed once. By reflection it printed twice:

```text
by reflection:
  new SeatingPlan
  new PriceList
  new SeatingPlan
  new SeatFinder
  new BoxOffice
```

Two seating plans for one hall, and each of them is sure it's the real one. Our ten lines have no memory, so they build a fresh plan for every constructor that asks. That's one of four flaws, and this lesson fixes all of them. The code takes "the first" constructor, when a class may have several. It has no list of the classes that take part. It would loop forever if two cards needed each other. And it builds a shared part once per request instead of once. Let's start with the list."""

S2 = """The simplest way to tell a container which classes take part is a list you write: `new Container(List.of(BoxOffice.class, SalesBook.class, ...))`. A list is fast and plain, and it's one more file to keep in step with the code. The usual alternative is to mark each component with an annotation, a label in the source that tools can read, such as `@Component`, and then to search for the label.

That search goes through a class loader. A class loader is the props team from Class loading: loaders, delegation, linking and initialization. It fetches each class only when a scene first needs it, and asks its senior first. `loader.getResources("workbench/container/l01/demo/app")` asks the team where a package's directory is. It answers with one URL for every place on the class path (the list of directories and JAR files the JVM loads classes from) that holds the package. For a build directory it's a `file:` URL; inside a JAR it's a `jar:file:...!/workbench/...` URL. You list the `.class` files there and turn each file name into a class name.

Then you load each class, and one argument decides what runs:

```java
Class<?> c = Class.forName(name, false, loader);           // load and link, no <clinit>
if (c.isAnnotationPresent(Component.class)) components.add(c);
```

```kotlin
val c = Class.forName(name, false, loader)                 // load and link, no <clinit>
if (c.isAnnotationPresent(Component::class.java)) components += c
```

`false` means "fetch the prop and check it, but don't hold its dress rehearsal". The rehearsal is `<clinit>`, a class's static initializer, the code that sets its static fields, and the JVM runs it once, on the class's first real use. The one-argument `Class.forName(name)` holds the rehearsal on the spot. In a scan, that runs every static initializer in the package, components or not, before anyone has asked for anything. The demo's package has two classes whose initializers print a line, and with `true` both lines appear in the middle of the scan:

```text
  AttendanceLog.<clinit>: opening the attendance file
  TicketArchive.<clinit>: loading 40,000 old tickets
```

The annotation needs one setting too. `@Component` must carry `@Retention(RUNTIME)`. With the default, `CLASS`, javac writes the label into the class file, but the JVM never shows it to reflection, so `isAnnotationPresent` says false and the scan finds nothing. Nothing fails, either. The container just starts empty.

A scan has a price that a list doesn't. It loads every class in the package, including the ones that turn out not to be components. In the demo, scanning an 11-class package loaded 272 classes: the 11, plus the JDK code for listing directories, reading streams and checking annotations. Why the JVM starts slowly, and how to measure it pictured the JVM as a corner shop that unpacks and checks every box each morning: every class it loads is found, read and checked again on every launch. A large program that scans thousands of classes pays for all of them at every start, even for the ones it throws away.

One more trap hides in JAR files. `getResources` finds a package inside a JAR only when the JAR has an entry for the directory itself. Most build tools write those entries, but a JAR packed with files only gives the scan zero roots. Again nothing fails: the props team simply reports an empty store.

So the lab's container takes a list, and a `ClassScanner` (given complete) can build that list with `forName(name, false, loader)`. Next, the container must read each card."""

ASIDE = {
    "title": "Do real frameworks scan like this?",
    "body": "Spring, a widely used framework (a library that creates your program's parts and connects them for you), scans the class path at every start, much as this section does, and reads the annotations with reflection. Quarkus and Micronaut, two newer frameworks, do the scan while the program is being built and write down what they found, so a start reads a ready-made list. Both choices work. They pay the same bill at different times, at every start or once per build, and lesson 3 of this track measures the difference on our box office.",
}

S3 = """Every card must be readable, and in code a card is a constructor. A class can have several, and reflection hands them back in no order you can rely on, so "the first" is a coin toss. The lab's rule is the one most containers use. If exactly one public constructor carries `@Inject`, use it. If the class has only one public constructor, use that. Otherwise refuse, with a message that says what to do: `TwoDoors has 2 public constructors; mark the one to use with @Inject`.

Kotlin makes "only one public constructor" harder than it looks. Write `class PriceList(val plan: SeatingPlan, val feePercent: Int = 3)`, and the JVM sees two public constructors: yours, and a synthetic one, made by the compiler rather than by you, that takes an extra `int` and a `DefaultConstructorMarker`. Kotlin callers use it when they leave `feePercent` out. It's the `$default` trick that Reading bytecode: javap, the operand stack and Kotlin's output found in the prompt book's shorthand, applied to a constructor. The container skips it with `isSynthetic()`. When every parameter has a default, kotlinc adds a third, a real no-argument constructor, and in this track's run it copied `@Inject` onto that one too. The container then sees two marked constructors and refuses. The cure is simple: don't give injected parameters defaults.

Each parameter is matched by its type, never by its name. A class file keeps parameter names only when javac runs with `-parameters` (`-java-parameters` for kotlinc), so reflection usually reports `arg0` and `arg1`. The type is always there. A parameter of interface type, such as `BookingClient`, goes to the one component that implements it, here `RemoteBookingClient`. None, or two, is an error.

Now the order. Visit a component, visit everything its constructor needs, and only then add the component to the list. That's a depth-first, post-order walk: depth first because it follows one card's needs all the way down before it moves on, and post-order because a component joins the list after its needs. The result is a **creation order**, a list in which every component comes after everything it depends on. A shared part joins once, because the walk skips anything already done. The figure numbers the box office's parts in the order the walk adds them.

The same walk finds loops. Keep a path: the components you're inside right now. If you reach one that's already on the path, you've come back to a card that is still waiting for its own needs. Picture three cards that point in a circle: the rota of who works which night needs the cast list, the cast list needs the rehearsal plan, and the rehearsal plan needs the rota. The container reports the slice of the path from the repeated class back to itself:

```text
Dependency cycle: Rota -> CastList -> RehearsalPlan -> Rota
```

Here the manager picture breaks, in a useful way. A manager can improvise when a card is unclear or two cards point at each other, and often gets away with it. A container that improvises, picking a constructor or breaking a loop by guessing, builds a program nobody wrote. So the lab's container reads every card in its own constructor, before it builds a single part.

**A container should refuse a card it can't read, before the doors open. Check the whole graph when the container is created.**

A missing part, a doubtful constructor or a loop then stops the program as it starts, with a message, instead of at the first ticket of the night. Building the parts can still wait until someone asks for them, and that's where the last flaw lives."""

S4 = """A **singleton** component has one instance per container, created the first time someone asks for it: the one seating plan. A **prototype** component is created again on every request, like a fresh basket for each customer at the box office. Singleton is the default, and it's where the bugs live, because the first request often arrives on several threads at once. (A thread is one path of work running beside others in the same program.) When the doors open, eight customers can reach the box office in the same second.

The obvious memory for our ten lines is a map from class to instance: look the class up, and build the part only if it's missing. That's check-then-act, the race from Race conditions: why count++ lies. Every thread that reads `null` before the first `put` builds a plan of its own. The demo releases eight threads at once on a `SeatingPlan` that takes 20 ms to read the hall's map:

```text
check-then-act on a map  constructor ran 8 times, threads saw 8 instance(s)
```

Eight customers, eight seating plans. `ConcurrentHashMap.computeIfAbsent` looks like the fix, because it builds a missing value atomically, in one step that no other thread can split. But a container calls it recursively: building `BoxOffice` means building `SalesBook` first, from inside the function that builds `BoxOffice`. The Javadoc forbids that; the function must not change the map. In practice the result depends on luck. The map keeps its entries in numbered buckets called bins, chosen from each key's hash code. Two keys in different bins work. Two in the same bin throw:

```text
computeIfAbsent, boxOffice needs priceList: worked
computeIfAbsent, boxOffice needs salesBook: java.lang.IllegalStateException: Recursive update
```

With `Class` keys, the hash code changes from run to run, so the same container would fail on some starts and not on others. Nobody wants to debug that on opening night.

The JVM has a lazy singleton of its own: the holder idiom from Lazy init done right: double-checked locking and holders. A nested class keeps the instance in a `static final` field, and the JVM sets that field in the class's dress rehearsal, once, under the class initialization lock. It's the best tool when you can write one holder class per singleton before you compile. A reflective container can't, because it learns its components only when the program runs. Lesson 3 of this track generates those holder classes.

So the lab gives each singleton a small cell that uses double-checked locking. In that lesson's shop, two assistants saw the stockroom door shut and both went to open it. The fix was to look, and only if the door is shut, take the key and look again:

```java
T value = instance;                      // volatile read: no lock once it's built
if (value == null) {
    synchronized (this) {
        value = instance;                // someone may have built it while we waited
        if (value == null) instance = value = factory.get();
    }
}
return value;
```

```kotlin
var value = instance                     // @Volatile var instance: T? = null
if (value == null) {
    synchronized(this) {
        value = instance                 // someone may have built it while we waited
        if (value == null) { value = factory(); instance = value }
    }
}
return value!!
```

`volatile` is what makes the first, unlocked read safe. A thread that reads a non-null reference also sees every write the constructor made before the reference was stored. Without it, a thread could see the reference and still read the new object's fields as zero: the stockroom door open, the lights still off. In the demo, the cell ran the constructor once, and all eight threads saw one instance.

You may worry about the locks. Building `BoxOffice` holds its cell's lock while it builds `PriceList`, which takes another cell's lock. Nested locks usually bring a risk of deadlock: two threads each waiting for a lock the other holds. Deadlock, livelock and starvation showed that such a freeze needs the waits to form a loop. Here every lock is taken along an arrow of the graph, from a component to something it needs, and the container has already refused loops. One more difference from a holder: if the constructor throws, the cell stays empty and the next `get` tries again. A dress rehearsal that fails is a failure for good, and the class answers `NoClassDefFoundError` from then on."""

CLOSING = """We started with a box office that built two seating plans for one hall. Now the container reads every card before the doors open. It picks one constructor per part, puts the parts in order, names any loop, and builds each shared part once, however many customers arrive in the same second.

Now look in your own code for a constructor that calls `new` on a helper, or for a static `getInstance()` method. Each one is a class building its own seating plan.

Next, we'll have the box office's calls to the booking service timed and retried, without changing a line of `BoxOffice`. How can a container slip extra work around a method call?"""

L = {
 "id": "cap4-01",
 "title": "Wire classes by reflection",
 "minutes": 40,
 "goal": "By the end you can build a small dependency injection container: find its components from a list or a class path scan, pick each one's constructor, create them in dependency order with a readable error for a loop, and give each singleton exactly one instance when many threads ask at once.",
 "opening": OPENING,
 "warmup": {
  "q": "`PriceList` and `SeatFinder` each take a `SeatingPlan` in their constructor, and `BoxOffice` takes both. A ten-line container builds `BoxOffice` by calling each constructor it finds, after building that constructor's parameters the same way. How many `SeatingPlan` objects does it create?",
  "options": ["One: the JVM reuses an object when the same class is asked for twice", "Two: one for each constructor that asks for it", "Three: one per class in the graph", "None until a method is called on `SeatingPlan`"],
  "answer": 1,
  "why": "Recursion with no memory builds a fresh dependency every time a constructor asks for one, so `PriceList` gets one plan and `SeatFinder` another. To share one `SeatingPlan`, the container has to remember what it already made: one stored instance per type. That memory is what a container calls the singleton scope."
 },
 "sections": [
  {
   "h": "What we'll build: a container for the box office, starting with ten lines of reflection",
   "body": S1,
   "figure": {"svg": FIG_PLAN, "caption": "The container over three sittings. This one builds the four steps on the left; lesson 2 adds proxies, and lesson 3 moves the same work to the build."},
   "try": {
    "title": "Count the seating plans",
    "minutes": 4,
    "steps": [
     "Read `TinyContainerDemo` (or the Kotlin twin). `PriceList` and `SeatFinder` both need a `SeatingPlan`. Predict how many times `new SeatingPlan` prints in each half.",
     "Run it from `labs/`.",
     "Give `build` a memory: add `static final Map<Class<?>, Object> made = new HashMap<>();`, return `made.get(type)` when it's there, and call `made.put(type, result)` before returning. In Kotlin, `made.getOrPut(type) { ... }` does both. Run it again."
    ],
    "code": demo("TinyContainerDemo"),
    "expect": "By hand, `new SeatingPlan` prints once, because you passed the same `plan` twice. By reflection it prints twice: once for `PriceList` and once for `SeatFinder`. With the map it prints once. That map is a singleton scope in its simplest form, and section 4 shows why the plain version breaks when several threads ask at once."
   }
  },
  {
   "h": "Find the parts: a list you write, or a scan through a class loader",
   "body": S2,
   "aside": ASIDE,
   "try": {
    "title": "Scan a package, then hold every dress rehearsal by accident",
    "minutes": 4,
    "steps": [
     "Read `ScanDemo` (or `ScanDemo.kt`). `TicketArchive` and `AttendanceLog` in the `app` package print a line from their static initializers.",
     "Predict: does either line print during the scan? Then run it.",
     "Set `INITIALIZE = true` and run it again. Then read the last two lines: the same package packed into two JAR files.",
     "Set `INITIALIZE` back to `false`."
    ],
    "code": demo("ScanDemo"),
    "expect": "With `INITIALIZE = false`, no initializer runs. The scan lists nine components (`PriceFormat` and the `BookingClient` interface are skipped) and reports 272 classes loaded (200 in the Kotlin run, which had loaded more before it started counting). With `true`, `AttendanceLog.<clinit>: opening the attendance file` and `TicketArchive.<clinit>: loading 40,000 old tickets` print in the middle of the scan, although nothing has asked for either component. The JAR with directory entries gives one `jar:` root; the files-only JAR gives none."
   },
   "refs": [
    {"title": "ClassLoader.getResources (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/ClassLoader.html", "kind": "docs"}
   ]
  },
  {
   "h": "Read each card: pick one constructor, then put the parts in order",
   "body": S3,
   "figure": {"svg": FIG_GRAPH, "caption": "The box office's parts. Starting at BoxOffice, the depth-first walk adds BookingConfig first and BoxOffice last."},
   "try": {
    "title": "Predict the order, then make a loop",
    "minutes": 5,
    "steps": [
     "Read `GraphDemo`. The scan returns the components in name order, and the walk starts from each one in turn. Write down the creation order you expect for all nine.",
     "Run it and compare. Then run the Kotlin twin, which ends with two refusals.",
     "In `app/SalesBook.java`, change the constructor to `public SalesBook(BoxOffice office) {}`. Predict the message, then run `GraphDemo` again. Undo the change afterwards."
    ],
    "code": demo("GraphDemo"),
    "expect": "The order is `[AttendanceLog, BookingConfig, RemoteBookingClient, SeatingPlan, PriceList, SalesBook, BoxOffice, TicketArchive, ClosingJob]`. `BookingConfig` comes second because `AttendanceLog` needs nothing, and the walk reaches `BookingConfig` from `BoxOffice` through `RemoteBookingClient`. Neither static initializer prints, because nobody asked for `ClosingJob`. The Java run ends with `cycle: Dependency cycle: Rota -> CastList -> RehearsalPlan -> Rota`. The Kotlin twin prints `refused: Dependency cycle: GRota -> GCastList -> GRehearsalPlan -> GRota` and `refused: GPriceRules has 2 @Inject constructors; keep one`. With your change, the scan itself throws `ContainerException: Dependency cycle: BoxOffice -> SalesBook -> BoxOffice`."
   },
   "refs": [
    {"title": "Kotlin docs: Classes and constructors", "url": "https://kotlinlang.org/docs/classes.html", "kind": "docs"}
   ]
  },
  {
   "h": "Build each shared part once, even when eight threads ask first",
   "body": S4,
   "try": {
    "title": "Race for the first seating plan",
    "minutes": 4,
    "steps": [
     "Read `SingletonRaceDemo` (or the Kotlin twin). Each row releases eight threads at the same moment, and `SeatingPlan` takes 20 ms to build.",
     "Predict the two numbers on each of the first two rows, and which `computeIfAbsent` line fails.",
     "Run it twice. Do the numbers change?"
    ],
    "code": demo("SingletonRaceDemo"),
    "expect": "`check-then-act on a map  constructor ran 8 times, threads saw 8 instance(s)` (now and then slightly fewer), then `SingletonCell ... 1 times ... 1 instance(s)` on every run. `boxOffice needs priceList: worked`, but `boxOffice needs salesBook: java.lang.IllegalStateException: Recursive update`, because those two strings land in the same bin of a 16-bin table. Change either name and the result may flip, which is exactly why nobody should rely on it."
   },
   "refs": [
    {"title": "ConcurrentHashMap.computeIfAbsent (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ConcurrentHashMap.html", "kind": "docs"}
   ]
  }
 ],
 "compare": {
  "title": "The same component in Java and Kotlin, as reflection sees it",
  "java": {
   "title": "PriceList.java",
   "src": "@Component\npublic class PriceList {\n    private final SeatingPlan plan;\n    private final int feePercent;\n\n    @Inject                                    // two public constructors: say which one\n    public PriceList(SeatingPlan plan) {\n        this(plan, 3);\n    }\n\n    public PriceList(SeatingPlan plan, int feePercent) {\n        this.plan = plan;\n        this.feePercent = feePercent;\n    }\n}\n// getConstructors(): (SeatingPlan) and (SeatingPlan, int). No synthetic ones."
  },
  "kotlin": {
   "title": "PriceList.kt",
   "src": "@Component\nclass PriceList(private val plan: SeatingPlan, private val feePercent: Int = 3)\n\n// getConstructors():\n//   PriceList(SeatingPlan, int)\n//   PriceList(SeatingPlan, int, int, DefaultConstructorMarker)   synthetic, skip it\n// The container picks (SeatingPlan, int), then finds no component for int.\n// Give feePercent no default, or move it into a FeeRules component."
  },
  "note": "Java gives you exactly the constructors you write. Kotlin compiles default arguments into an extra public synthetic constructor, and if every parameter has a default, into a real no-argument constructor as well, which receives the same annotations. So a container must filter `isSynthetic()` and must not be fooled by an `@Inject` that kotlinc copied. In both languages the class file keeps no parameter names by default, so the container matches by type. The Kotlin class is also `final`, which is harmless here and becomes the main problem in lesson 2."
 },
 "worked": {
  "title": "Break a loop the container reported",
  "steps": [
   {
    "say": "The container refuses to start with `Dependency cycle: BoxOffice -> SeatFinder -> BoxOffice`. Here are the two classes. Read them and ask what each one needs while it's being built, and what it only needs later, inside a method.",
    "code": "@Component\npublic class BoxOffice {\n    private final SoldSeats sold = new SoldSeats();        // hidden inside\n    private final SeatFinder finder;\n    public BoxOffice(SeatFinder finder) { this.finder = finder; }\n    public String sellBestSeat() { String seat = finder.bestFreeSeat(); sold.add(seat); return seat; }\n    public boolean isSold(String seat) { return sold.contains(seat); }\n}\n\n@Component\npublic class SeatFinder {\n    private final BoxOffice office;\n    public SeatFinder(BoxOffice office) { this.office = office; }\n    public String bestFreeSeat() {\n        return SEATS.stream().filter(s -> !office.isSold(s)).findFirst().orElseThrow();\n    }\n}",
    "lang": "java",
    "alt_lang": "kotlin",
    "alt_code": "@Component\nclass BoxOffice(private val finder: SeatFinder) {\n    private val sold = SoldSeats()                         // hidden inside\n    fun sellBestSeat(): String = finder.bestFreeSeat().also { sold.add(it) }\n    fun isSold(seat: String): Boolean = sold.contains(seat)\n}\n\n@Component\nclass SeatFinder(private val office: BoxOffice) {\n    fun bestFreeSeat(): String = SEATS.first { !office.isSold(it) }\n}"
   },
   {
    "say": "`SeatFinder` doesn't need a `BoxOffice` at all. It needs to know which seats are sold, and that list lives in `SoldSeats`, hidden inside `BoxOffice`. `BoxOffice` needs the list to write to and the finder to ask. The loop exists only because the list is hidden."
   },
   {
    "say": "Give the list its own component. Both classes depend on it, and the arrows no longer close a loop: `SoldSeats` is created first, then `SeatFinder`, then `BoxOffice`.",
    "code": "@Component\npublic class SoldSeats {\n    private final Set<String> seats = ConcurrentHashMap.newKeySet();\n    public void add(String seat) { seats.add(seat); }\n    public boolean contains(String seat) { return seats.contains(seat); }\n}\n\n@Component\npublic class SeatFinder {\n    private final SoldSeats sold;\n    public SeatFinder(SoldSeats sold) { this.sold = sold; }\n    public String bestFreeSeat() { return SEATS.stream().filter(s -> !sold.contains(s)).findFirst().orElseThrow(); }\n}\n\n@Component\npublic class BoxOffice {\n    private final SoldSeats sold;\n    private final SeatFinder finder;\n    public BoxOffice(SoldSeats sold, SeatFinder finder) { this.sold = sold; this.finder = finder; }\n    public String sellBestSeat() { String seat = finder.bestFreeSeat(); sold.add(seat); return seat; }\n}",
    "lang": "java",
    "alt_lang": "kotlin",
    "alt_code": "@Component\nclass SoldSeats {\n    private val seats = ConcurrentHashMap.newKeySet<String>()\n    fun add(seat: String) { seats += seat }\n    fun contains(seat: String): Boolean = seat in seats\n}\n\n@Component\nclass SeatFinder(private val sold: SoldSeats) {\n    fun bestFreeSeat(): String = SEATS.first { !sold.contains(it) }\n}\n\n@Component\nclass BoxOffice(private val sold: SoldSeats, private val finder: SeatFinder) {\n    fun sellBestSeat(): String = finder.bestFreeSeat().also { sold.add(it) }\n}"
   },
   {
    "say": "If two parts really do need each other at call time, real containers offer a lookup instead of an object: `jakarta.inject.Provider<BoxOffice>` in the Jakarta standard, `ObjectProvider<BoxOffice>` in Spring. The constructor then receives something that finds the `BoxOffice` later, inside a method. The lab's container doesn't offer that, on purpose. Reach for it after you've tried the split, not before."
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
   "Run the tests once. Eleven of twelve fail with `UnsupportedOperationException`. The one that passes tests `ClassScanner`, which is given: read it once, because it's section 2 in code. The test fixtures are a small box office in `src/test/java/.../l01/app`.",
   "Write `Constructors.pick`. Filter `getConstructors()` with `!c.isSynthetic()`, then apply the three rules from its Javadoc. The tests check the exact messages, including two Kotlin classes from `KotlinBeans.kt`.",
   "Write `BeanGraph.creationOrder` as a depth-first, post-order walk. Keep a `Set` of finished classes and a `LinkedHashSet` path of the classes you're inside. Build the cycle message from the part of the path that starts at the repeated class.",
   "Write `SingletonCell.get` with double-checked locking on the `volatile` field.",
   "Write `Container.create`: pick the constructor, map `graph.dependenciesOf(component)` through `instanceOf`, and call `newInstance`. Then write `instanceOf`: the cell's `get()` for singletons, `create` for prototypes. Run the tests until all twelve pass, then twice more."
  ],
  "hints": [
   "In `creationOrder`, check `done` before `path`. A finished class is not a loop, even when two components both depend on it.",
   "A recursive helper `visit(c, done, path, order)` keeps the main method to three lines. Add `c` to `path` before visiting its dependencies, and remove it after.",
   "`Constructor.newInstance` wraps whatever the constructor throws in `InvocationTargetException`. The test wants the original `IllegalStateException` as the cause of your `ContainerException`: use `e.getCause()`.",
   "If the concurrency test sees two `SlowPlan`s, you read `instance` once outside the lock but not again inside it."
  ],
  "done_when": "All twelve tests in `WiringTest` pass, three runs in a row."
 },
 "drill": {
  "title": "Order a graph from memory",
  "minutes": 5,
  "prompt": "Close the lab. Given `Map<String, List<String>> needs` (component name to the names its constructor needs), write `List<String> creationOrder(Map<String, List<String>> needs)` that returns each name after everything it needs, and throws `IllegalStateException(\"cycle: a -> b -> a\")` on a loop. Then compare with the answer. Did you check `done` before the path?",
  "answer": {
   "lang": "java",
   "src": "static List<String> creationOrder(Map<String, List<String>> needs) {\n    List<String> order = new ArrayList<>();\n    Set<String> done = new HashSet<>();\n    for (String name : needs.keySet()) visit(name, needs, done, new LinkedHashSet<>(), order);\n    return order;\n}\n\nstatic void visit(String name, Map<String, List<String>> needs, Set<String> done,\n                  LinkedHashSet<String> path, List<String> order) {\n    if (done.contains(name)) return;                       // finished earlier: not a loop\n    if (path.contains(name)) {                             // back at a name we are still inside\n        List<String> loop = new ArrayList<>(path);\n        loop = loop.subList(loop.indexOf(name), loop.size());\n        throw new IllegalStateException(\"cycle: \" + String.join(\" -> \", loop) + \" -> \" + name);\n    }\n    path.add(name);\n    for (String dep : needs.getOrDefault(name, List.of())) visit(dep, needs, done, path, order);\n    path.remove(name);\n    done.add(name);\n    order.add(name);                                       // after everything it needs\n}",
   "alt": {
    "lang": "kotlin",
    "src": "fun creationOrder(needs: Map<String, List<String>>): List<String> {\n    val order = mutableListOf<String>()\n    val done = mutableSetOf<String>()\n    val path = linkedSetOf<String>()\n\n    fun visit(name: String) {\n        if (name in done) return                           // finished earlier: not a loop\n        if (name in path) {                                // back at a name we are still inside\n            val loop = path.dropWhile { it != name } + name\n            throw IllegalStateException(\"cycle: \" + loop.joinToString(\" -> \"))\n        }\n        path += name\n        needs[name].orEmpty().forEach(::visit)\n        path -= name\n        done += name\n        order += name                                      // after everything it needs\n    }\n\n    needs.keys.forEach(::visit)\n    return order\n}"
   }
  }
 },
 "recap": [
  "A container does the wiring block of `main` for you, the way a front-of-house manager reads each desk's card: it finds the components, builds each one from its constructor, and decides how many of each exist.",
  "A scan asks a class loader for the package's directory and loads each class with `Class.forName(name, false, loader)`, so no static initializer runs. `@Component` needs `@Retention(RUNTIME)`, every scanned class is loaded on every start, and a JAR without directory entries scans as empty.",
  "Pick the `@Inject` constructor or the only public one, never \"the first\". Skip Kotlin's synthetic constructors, don't give injected parameters defaults, and match parameters by type.",
  "Create components in depth-first post-order, and keep a path to find loops. Check the whole graph when the container is created, so a broken card stops the start, not the first sale.",
  "A singleton is one instance per container. Check-then-act on a map builds duplicates, and a recursive `computeIfAbsent` can throw `Recursive update`. A cell with double-checked locking on a `volatile` field builds exactly one, and can't deadlock on a graph without loops.",
  "Where today's container stops: it hands out plain objects. It can't time a call or try it again when the booking service doesn't answer; lesson 2 puts proxies around the parts."
 ],
 "closing": CLOSING,
 "quiz": [
  {
   "q": "Your scanner calls `Class.forName(name)`, with one argument, for every class in `com.acme.theatre`. `TicketArchive` has `static final List<Ticket> OLD = loadFromDisk();` and nobody ever asks the container for it. When does `loadFromDisk()` run?",
   "options": [
    "Never, because nothing asks for `TicketArchive`",
    "During the scan, because the one-argument `forName` initializes every class it loads",
    "When the JIT compiles `TicketArchive`",
    "Only if `TicketArchive` is annotated `@Component`"
   ],
   "answer": 1,
   "why": "The one-argument `Class.forName` loads, links and initializes, so `<clinit>` runs during the scan for every class in the package, component or not. `Class.forName(name, false, loader)` loads and links without initializing. Being a component doesn't matter either way, which is why the last option tempts: the scan checks the annotation only after the class is loaded.",
   "from": "cls-01"
  },
  {
   "q": "A container matches constructor parameters by name with `Parameter.getName()`. Gradle compiles `BoxOffice(BookingClient booking, SalesBook book)` with javac's default options. What names does the container see?",
   "options": [
    "`arg0` and `arg1`",
    "`booking` and `book`",
    "`BookingClient` and `SalesBook`",
    "A `NoSuchFieldException`, because the names are private"
   ],
   "answer": 0,
   "why": "A method's descriptor in the class file carries types, not names, and javac writes a `MethodParameters` attribute only when you pass `-parameters` (`-java-parameters` for kotlinc). Without it, reflection makes up `arg0` and `arg1`. The second option is what the source says, and that's the trap. It's also why the lab matches by type: the type is always in the descriptor.",
   "from": "cls-02"
  },
  {
   "q": "A program's container scans 4,000 classes at start-up, though only 300 are components, and none of the 4,000 has a static initializer. What does the scan add to every start?",
   "options": [
    "Nothing, because classes without static initializers are free",
    "Only the cost of calling 300 constructors",
    "Finding, parsing and verifying 4,000 classes, and reading their annotations",
    "A garbage collection to unload the 3,700 non-components"
   ],
   "answer": 2,
   "why": "Loading is the expensive part even without initialization: the JVM finds each class file, parses it into metaspace and verifies its bytecode, on every launch. The 3,700 non-components stay loaded, because nothing unloads classes of the application class loader. Initialization would add the static initializers on top.",
   "from": "boot-01"
  },
  {
   "q": "A teammate's `SingletonCell` uses double-checked locking, but the `instance` field is a plain field, not `volatile`. What can go wrong?",
   "options": [
    "Two threads can both run the factory",
    "The nested locks can deadlock",
    "Nothing on x86, so it's fine in production",
    "A thread can see a non-null reference and still read the new object's fields as zero"
   ],
   "answer": 3,
   "why": "The lock still makes the factory run once, so the first option doesn't happen. What the unlocked first read lacks is a happens-before edge to the constructor's writes: without `volatile`, the reference can become visible before the fields behind it, the stockroom door open with the lights still off. \"It works on x86\" describes one processor and one JIT, not what the memory model allows.",
   "from": "jmm-05"
  },
  {
   "q": "`SalesBook` needs `AttendanceLog`, `AttendanceLog` needs `BoxOffice`, and `BoxOffice` needs `SalesBook`. The container is built with the list `[SalesBook, BoxOffice, AttendanceLog]`. What message does the lab's `creationOrder` throw?",
   "options": [
    "`Dependency cycle: SalesBook -> AttendanceLog -> BoxOffice -> SalesBook`",
    "`Dependency cycle: BoxOffice -> SalesBook -> AttendanceLog -> BoxOffice`",
    "A `StackOverflowError`, because the walk never ends",
    "`Dependency cycle: SalesBook -> BoxOffice -> AttendanceLog -> SalesBook`"
   ],
   "answer": 0,
   "why": "The walk starts at the first component in the list, `SalesBook`, follows its constructor to `AttendanceLog`, then to `BoxOffice`, and then reaches `SalesBook`, which is still on the path. The message is the path from the repeated class back to itself, in the order the walk went. Without a path, the recursion would overflow the stack, which is what the ten-line container from section 1 does."
  }
 ],
 "flashcards": [
  {"front": "What does `Class.forName(name, false, loader)` do that `Class.forName(name)` doesn't?", "back": "It loads and links the class without initializing it, so no static initializer runs. A scanner should always pass `false`."},
  {"front": "Why does `@Component` need `@Retention(RUNTIME)`?", "back": "With the default `CLASS` retention the annotation is in the class file, but reflection can't see it, so `isAnnotationPresent` returns false."},
  {"front": "Kotlin `class Prices(val plan: SeatingPlan, val feePercent: Int = 3)`: how many public constructors does `getConstructors()` return?", "back": "Two: `(SeatingPlan, int)` and a synthetic `(SeatingPlan, int, int, DefaultConstructorMarker)` for the default argument. Filter with `isSynthetic()`."},
  {"front": "In what order does a container create components?", "back": "Depth-first post-order: each component after everything its constructor needs. Shared dependencies appear once."},
  {"front": "How does a depth-first walk detect a dependency loop?", "back": "It keeps a path of the components it is still inside. Reaching one of them again is a loop; the path from that component back to itself is the message."},
  {"front": "Why not build a container's singletons with a recursive `ConcurrentHashMap.computeIfAbsent`?", "back": "The mapping function must not change the map. If the inner key lands in the same bin, it throws `IllegalStateException: Recursive update`, and with `Class` keys that depends on identity hash codes."},
  {"front": "Why can nested `SingletonCell` locks not deadlock?", "back": "Each lock is taken along a dependency arrow, from a component to what it needs. A deadlock would need the arrows to form a loop, and the container rejects loops at start-up."}
 ],
 "terms": [
  {"term": "Dependency injection", "plain": "Handing a class the objects it needs, usually through its constructor, instead of letting it create them itself."},
  {"term": "Dependency injection container", "plain": "A small program that builds your objects and hands each one the other objects it needs, so classes don't build their own helpers."},
  {"term": "Component", "plain": "A class the container creates and hands to others. Spring and other frameworks call the instances beans."},
  {"term": "Scope", "plain": "How many instances of a component exist: one per container (singleton) or a new one per request (prototype)."},
  {"term": "Creation order", "plain": "A list of all components in which each one comes after everything it depends on. Also called a topological order."},
  {"term": "Class path scan", "plain": "Finding classes by asking a class loader for a package's directory and loading every class file in it."},
  {"term": "Double-checked locking", "plain": "Read a volatile field without a lock; only if it is empty, lock, read it again, and build. Fast after the first call."}
 ],
 "explain_back": {
  "prompt": "A colleague asks why the container's constructor walks the whole graph when it could simply create things on the first `get`. Explain what the walk gives you, what still happens lazily, and why the two together are a good trade.",
  "answer": "The walk only reads constructors and matches types, so it's cheap. It proves at start-up that every dependency has exactly one provider, that every class has a constructor the container can call, and that there are no loops, and it produces the creation order. A broken graph then stops the program as it starts, with a clear message, instead of failing the first request that happens to touch the bad part. What stays lazy is running the constructors: a singleton is built on first use, inside its cell, so the start doesn't pay for components nobody uses. The cost of the trade is that a constructor that throws still surprises you on first use, which is why constructors should only store their arguments."
 },
 "deeper": {
  "minutes": 10,
  "body": """Spring creates its singletons eagerly at the end of start-up by default, after the scan and the graph work, so that a constructor that throws stops the start too. The lab's container is lazy, like a CDI client proxy (CDI is the Jakarta standard for dependency injection), which creates its bean on the first method call. Neither is wrong; they put the same failure at different times.

Spring can also resolve some loops that the lab refuses. With field or setter injection, it can hand out a reference to an object whose constructor has finished but whose fields aren't all set yet, from a cache of "early" singleton references. Constructor injection can never do that, because the object doesn't exist until its constructor's arguments do. That's one reason constructor injection is the recommended style: an impossible graph fails loudly. Since Spring Boot 2.6, even the setter-injection kind of loop is refused unless you set `spring.main.allow-circular-references=true`.

Three things a production container adds to this lesson's graph. Qualifiers, for when two components implement the same interface and the injection point must say which (`@Named`, `@Qualifier`). Generic types, so that `Repository<Show>` and `Repository<Seat>` are different dependencies (the lab compares erased classes only). And lookups such as `Provider<T>`, which turn a hard edge into one that is followed at call time. Each one makes the graph work harder, and each one is easier to check at build time than at start-up, which is where lesson 3 of this track ends up."""
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
