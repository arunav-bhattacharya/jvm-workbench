import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
read = lambda p: (ROOT / p).read_text()
MAIN = "labs/injector/src/main/kotlin/workbench/injector/l01"
DEMO_K = "labs/injector/src/demo/kotlin/workbench/injector/l01/demo"
DEMO_J = "labs/injector/src/demo/java/workbench/injector/l01/demo"
APP_K = "labs/injector/app/src/l01/kotlin/workbench/injector/app/l01"
APP_J = "labs/injector/app/src/l01/java/workbench/injector/app/l01"


def code(kotlin_file, kotlin_run, java_file, java_run):
    """A Kotlin demo with its runnable Java twin."""
    return {"lang": "kotlin", "title": kotlin_file.rsplit("/", 1)[1], "src": read(kotlin_file), "run": kotlin_run, "file": kotlin_file,
            "alt": {"lang": "java", "title": java_file.rsplit("/", 1)[1], "src": read(java_file), "run": java_run, "file": java_file}}


def pair(java, kotlin):
    """A Java fence and its Kotlin twin, side by side, as the validator expects."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"


# ---------------------------------------------------------------- figure (section 2)
def box(x, y, w, label, cls):
    return (f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="40" rx="8"/>'
            f'<text class="t" x="{x + w / 2:g}" y="{y + 25}" text-anchor="middle">{label}</text>')


FIG = (
    '<svg viewBox="0 0 680 340" role="img" aria-label="The moving-day graph: MovingDay needs Crew and Route, Crew needs Truck and two Packers, '
    'Truck needs Driver, each Packer needs its own TapeRoll, and Driver needs the same Route. Numbers give the order the plan builds them in.">'
    '<rect class="box-a" x="20" y="16" width="16" height="16" rx="4"/>'
    '<text class="t-s" x="44" y="29">one for the whole day: a val</text>'
    '<rect class="box-b" x="20" y="40" width="16" height="16" rx="4"/>'
    '<text class="t-s" x="44" y="53">new every time: a function</text>'
    + box(270, 20, 140, "7. MovingDay", "box-a")
    + box(170, 100, 120, "6. Crew", "box-a")
    + box(30, 180, 110, "3. Truck", "box-a")
    + box(170, 180, 110, "5. Packer", "box-b")
    + box(310, 180, 110, "5. Packer", "box-b")
    + box(30, 260, 110, "2. Driver", "box-a")
    + box(170, 260, 110, "4. TapeRoll", "box-b")
    + box(310, 260, 110, "4. TapeRoll", "box-b")
    + box(520, 260, 130, "1. Route", "box-a")
    + '<line class="ln" x1="320" y1="60" x2="250" y2="98" marker-end="url(#arr)"/>'
    '<line class="ln" x1="390" y1="60" x2="570" y2="256" marker-end="url(#arr)"/>'
    '<line class="ln" x1="200" y1="140" x2="110" y2="178" marker-end="url(#arr)"/>'
    '<line class="ln" x1="228" y1="140" x2="226" y2="178" marker-end="url(#arr)"/>'
    '<line class="ln" x1="262" y1="140" x2="350" y2="178" marker-end="url(#arr)"/>'
    '<line class="ln" x1="85" y1="220" x2="85" y2="258" marker-end="url(#arr)"/>'
    '<line class="ln" x1="225" y1="220" x2="225" y2="258" marker-end="url(#arr)"/>'
    '<line class="ln" x1="365" y1="220" x2="365" y2="258" marker-end="url(#arr)"/>'
    '<path class="ln" d="M85 300 V322 H585 V302" fill="none" marker-end="url(#arr)"/>'
    '<text class="t-s t-m" x="340" y="336" text-anchor="middle">every arrow means "needs"; the numbers are the order of the lines in the generated component</text>'
    '</svg>'
)

# ---------------------------------------------------------------- opening
OPENING = """Picture moving day at a family's house. The truck needs a driver, the driver needs the route, and every packer needs a roll of tape. The crew can't start until the truck and the packers are ready. Someone has to work out the order, and what is shared: one truck for the whole day, but a new roll of tape for each packer.

You can write that plan the night before, or work it out on the street at seven in the morning, with the crew waiting and the meter running. In Part 4's capstone you built a small dependency injection container, a program that builds your objects and hands each one what its constructor asks for. It did the second: it read your classes by reflection every time the program started. The last lesson, Choosing the tool, weighed reflection against KSP.

In this capstone we'll write the plan the night before. In this sitting, a KSP processor writes one factory per class, then a component that builds the whole crew in the right order. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
J_HAND = """Route route = new Route();
Driver driver = new Driver(route);
Truck truck = new Truck(driver);
Crew crew = new Crew(truck, new Packer(new TapeRoll()), new Packer(new TapeRoll()));
MovingDay day = new MovingDay(crew, route);"""
K_HAND = """val route = Route()
val driver = Driver(route)
val truck = Truck(driver)
val crew = Crew(truck, Packer(TapeRoll()), Packer(TapeRoll()))
val day = MovingDay(crew, route)"""
J_NOTES = """@Singleton
public class Truck {
    private final Driver driver;

    @Inject                                      // "build me with this constructor"
    public Truck(Driver driver) { this.driver = driver; }
}

@Component                                       // "what the app asks the plan for"
public interface MovingDayComponent {
    MovingDay movingDay();
    Truck truck();
}"""
K_NOTES = """@Singleton
class Truck @Inject constructor(val driver: Driver)   // "build me with this constructor"

@Component                                             // "what the app asks the plan for"
interface MovingDayComponent {
    fun movingDay(): MovingDay
    fun truck(): Truck
}"""

S0 = """Moving day has a plan even when nobody writes it down. In MoveMate, our small app for a family's move, each person and thing on the crew is a class, and each class says in its constructor what it needs. Here is the plan written by hand, the way most programs do it near `main`:

""" + pair(J_HAND, K_HAND) + """

An object that another object needs is a **dependency**: the route is a dependency of the driver. Handing dependencies in from outside, instead of letting each class build its own, is **dependency injection**. Doing it through the constructor, as here, is **constructor injection**.

Notice what those five lines get right. The driver and the moving day share one route. There is one truck. Each packer gets its own roll of tape. And every object is built after the objects it needs. Five lines are easy to keep right by hand, but eighty are not. Someone adds a parameter to `Truck`, and the block breaks in three places, or still compiles and quietly builds a second truck.

So let's give the block a picture. The night before the move, someone writes the plan for the day on a sheet of paper. Each line of the plan says how to get one kind of thing: "the route: print it from the map", "a driver: call Sam and hand him the route". In code, such a line is a **binding**: what the plan does when someone needs a `Driver`. Some things are shared for the whole day, like the one truck. A thing that exists once per plan is a **singleton**. Others are new each time someone asks, like a roll of tape for each packer. Draw an arrow from each person to what they wait for, and you have the **graph** of the day.

The picture breaks in one place, and it matters. A real planner can improvise in the morning, when a neighbour turns up with a ladder. A plan written by the build can't. Everything it will ever build must be in it when the build runs.

Part 4's container worked the plan out on the street: it read your classes while the program ran. This capstone writes it the night before, with KSP. MoveMate's classes get sticky notes: **annotations**, labels in the code that tools can read. Three come from `labs/injector/annotations`:

""" + pair(J_NOTES, K_NOTES) + """

`@Inject` marks the constructor the plan should call. Put on the class instead, as in `@Inject class Packer(val tape: TapeRoll)`, it means the primary constructor. `@Singleton` asks for one per plan, and `@Component` marks the interface that lists what the app will ask for. Our processors read those notes and write the plan as ordinary Kotlin. The first thing they write is the smallest piece: a card for each member of the crew."""

# ---------------------------------------------------------------- section 1
J_FIND = """// Closest Java equivalent: a javac annotation processor (FactoryDemoJava in the demos)
for (Element element : round.getElementsAnnotatedWith(Inject.class)) {          // 1. Find
    if (element.getKind() != ElementKind.CONSTRUCTOR) { /* error */ continue; }  // 2. Check
    ExecutableElement constructor = (ExecutableElement) element;
    TypeElement type = (TypeElement) constructor.getEnclosingElement();
    for (VariableElement p : constructor.getParameters()) { /* ... */ }          // 3. Read
    Writer out = processingEnv.getFiler()                                         // 4. Write
            .createSourceFile(pkg + "." + name + "Factory", type).openWriter();
}"""
K_FIND = """val (ready, later) = resolver.getSymbolsWithAnnotation(INJECT).toList()       // 1. Find
    .partition { it.validate(apiFeatures = apiFeatures) }
for (symbol in ready) {
    val binding = checked(symbol) ?: continue                                    // 2. Check
    factoryFile(binding)                                                         // 3. Read, 4. Write
        .writeTo(codeGenerator, Dependencies(aggregating = false, binding.declaration.containingFile!!))
}
return later"""
OUT_FACTORY = """--- movemate/DriverFactory.kt
// Generated by FactoryProcessor from Driver. Do not edit.
package movemate

public object DriverFactory {
  public fun create(route: Route): Driver = Driver(route)
}"""

S1 = """A **factory** is a small piece of code whose only job is to build one class. The factory for `Driver` takes a route and calls the constructor. On paper, it's the card the plan keeps for Sam: what he needs, and how to bring him. It's dull code on purpose, and nobody should have to write eight of these by hand.

A processor writes them. A **processor** is a plug-in for the build that reads your declarations and writes new source files. **KSP**, Kotlin Symbol Processing, runs processors during the build, before the Kotlin compiler compiles your code, and then compiles what they wrote along with it. In the KSP track's picture, a processor is the helper with a clipboard. It reads the labels on the boxes, never opens one, and writes new cards that travel with the move. Java has had the same idea since Java 6, as annotation processors that javac runs. KSP is Kotlin's own, faster way to do that job for Kotlin code.

Our factory processor follows the five moves of the KSP track. Find: ask the Resolver, KSP's view of your code, for every symbol, that is, every declaration it can see, that carries `@Inject`. Check: refuse what the plan can't build, such as an interface, with an error on its line. Read: the constructor's parameters. Write: one file per class. Prove: tests, then a real build. Here is the loop, next to the closest Java equivalent:

""" + pair(J_FIND, K_FIND) + """

Find has one surprise. `@Inject` on a constructor gives you a `KSFunctionDeclaration`, while `@Inject` on the class gives you a `KSClassDeclaration`. The given `checked` function turns both into a `Binding`: the class, plus the constructor the plan will call. `factoryFile` then reads that constructor's parameters and builds the file with KotlinPoet, a library for writing Kotlin source from code, one `ParameterSpec` per parameter, as in the KSP track. The demo prints what it wrote:

```text
""" + OUT_FACTORY + """
```

`create` takes what the constructor takes and passes it straight on. KotlinPoet wrote the `public` modifiers and turned the one-statement body into an expression body: `= Driver(route)` instead of a block with `return`.

The last argument of `writeTo` matters most. `Dependencies(aggregating = false, driverFile)` tells KSP that this card depends on `Driver.kt` and on nothing else. That makes it an **isolating** output: when `Truck.kt` changes, KSP has no reason to redo the driver's card. Lesson 3 watches that happen in KSP's own log.

**A factory knows one class. Tie it to that class's file only.**

Eight cards now sit in `build/generated/ksp`, and none of them says when to call it. Sam can't drive before someone has printed the route."""

# ---------------------------------------------------------------- section 2
J_WALK = """// The same walk in Java, over a map from each class to what its constructor needs
void visit(String name, Map<String, List<String>> needs, LinkedHashSet<String> order) {
    if (order.contains(name)) return;                       // already in the plan: shared
    for (String dependency : needs.get(name)) visit(dependency, needs, order);
    order.add(name);                                        // after everything it needs
}"""
K_WALK = """fun visit(binding: Binding) {
    if (binding.key in order) return                        // already in the plan: shared
    for (p in binding.parameters) need(p.type.resolve(), binding.name, p)?.let(::visit)
    order[binding.key] = binding                            // post-order: after everything it needs
}"""
J_PLAN = """// The same plan as a javac annotation processor would write it in Java
public final class GeneratedMovingDayComponent implements MovingDayComponent {
    private final Route route = RouteFactory.create();
    private final Driver driver = DriverFactory.create(route);
    private final Truck truck = TruckFactory.create(driver);
    private final Crew crew = CrewFactory.create(truck, newPacker(), newPacker());
    private final MovingDay movingDay = MovingDayFactory.create(crew, route);

    private TapeRoll newTapeRoll() { return TapeRollFactory.create(); }
    private Packer newPacker() { return PackerFactory.create(newTapeRoll()); }

    @Override public MovingDay movingDay() { return movingDay; }
    @Override public Truck truck() { return truck; }
}"""
K_PLAN = """// Generated by ComponentProcessor from MovingDayComponent. Do not edit. (blank lines removed)
public class GeneratedMovingDayComponent : MovingDayComponent {
  private val route: Route = RouteFactory.create()
  private val driver: Driver = DriverFactory.create(route)
  private val truck: Truck = TruckFactory.create(driver)
  private val crew: Crew = CrewFactory.create(truck, newPacker(), newPacker())
  private val movingDay: MovingDay = MovingDayFactory.create(crew, route)
  private fun newTapeRoll(): TapeRoll = TapeRollFactory.create()
  private fun newPacker(): Packer = PackerFactory.create(newTapeRoll())
  override fun movingDay(): MovingDay = movingDay
  override fun truck(): Truck = truck
}"""

S2 = """The cards say how to bring each member of the crew. The plan for the day says in which order, and what is shared. A **component** is that plan in code: a generated class that implements your `@Component` interface and builds everything the interface hands out. Ours is called `GeneratedMovingDayComponent`.

To write it, the second processor walks the graph. It starts at each function of the interface, `movingDay()` and `truck()`, and follows the constructors down. `MovingDay` needs `Crew` and `Route`, `Crew` needs `Truck` and two packers, and so on, as the figure draws it. The rule fits in one sentence: a binding joins the plan when the walk leaves it, after everything it needs. That order is called post-order, and the walk is depth first:

""" + pair(J_WALK, K_WALK) + """

`need` finds the binding for a parameter's type, or reports that nobody provides it. Then the processor writes the plan: a `private val` for each singleton, in the order the walk found, and a `new...()` function for everything else. Read the result aloud. It is the code you'd write by hand, in the right order:

""" + pair(J_PLAN, K_PLAN) + """

First the route, then the driver who needs it, then the truck. The crew's line calls `newPacker()` twice, and each call makes a new packer with a new roll of tape. So the app prints `one truck for the whole day: true` and `tape rolls made: 2`. The one truck is a field, built once. The tape rolls come from a function, built on every call.

Remember the warm-up? Kotlin runs those initializers from top to bottom, as Java runs field initializers. Write the driver's line above the route's, and the compiler, a stickler for order, refuses: `Variable 'route' must be initialized.` javac says `illegal forward reference` for the same line in Java. The order isn't decoration. It's what makes the class compile.

The component's text depends on many files, so the processor writes it with `Dependencies(aggregating = true, componentFile)`. In the KSP track's words, it's the master list, an **aggregating** output, redone whenever any file changes. KSP also records each type the walk looks up, so it would notice a changed constructor anyway. Aggregating covers new files too, which matters in the next lesson, where a new module can add a line to the plan.

One caution before we move on. The walk remembers what it has finished, but not the path it is on right now. Give it a driver who waits for the truck, and it walks in circles until the stack runs out. The next lesson gives it that memory.

We have the plan, in a file you can open and read. How does it compare with working it out on the street?"""

# ---------------------------------------------------------------- section 3
J_USE = """MovingDayComponent plan = new GeneratedMovingDayComponent();
MovingDay day = plan.movingDay();
System.out.println(plan.truck() == day.getCrew().getTruck());   // true: one truck"""
K_USE = """val plan: MovingDayComponent = GeneratedMovingDayComponent()
val day = plan.movingDay()
println(plan.truck() === day.crew.truck)                           // true: one truck"""
OUT_MISSING = """e: [ksp] .../labs/injector/app/src/l01/kotlin/workbench/injector/app/l01/Truck.kt:8: Truck needs Driver, but nobody provides Driver. Add @Inject to its constructor.

> Task :injector:app:kspL01Kotlin FAILED
   > KSP failed with exit code: PROCESSING_ERROR"""

S3 = """Both ways build the same crew. They differ in when the work happens and in what you see when it goes wrong. Here's the generated component next to Part 4's reflection container:

| | Reflection container (Part 4) | Generated component (this lesson) |
|---|---|---|
| When the wiring is checked | When the program first asks for a part | When the build runs |
| What runs at start | Reading annotations, `getConstructors()` and `newInstance` for every part | One constructor call per part, in order |
| What you can read | Nothing: the plan exists only in memory | A Kotlin file in `build/generated/ksp` |
| A mistake looks like | An exception thrown from inside the container | An error on the file and line of your class |
| Can it change its mind at run time? | Yes: it can scan for parts and choose | No: the plan is fixed when you build |

Let the build settle the fourth row. Delete `@Inject` from `Driver` in `app/src/l01` and run `./gradlew :injector:app:kspL01Kotlin`:

```text
""" + OUT_MISSING + """
```

The program never ran. The error points at line 8 of `Truck.kt`, where the truck asks for a driver, and not at a line of the processor. In a reflection container, the same mistake would surface only when the app first asked for the crew, as an exception from the container's own code. The next lesson shows that stack trace. A stack trace from a reflection container is mostly the container talking about itself.

Using the generated component is ordinary code in either language. It compiles to a plain class, so Java calls it like any other:

""" + pair(J_USE, K_USE) + """

**Wiring that depends only on your classes can be checked when you build. Check it there.**

The last row of the table is the price. The generated plan can't discover a part while the program runs, or choose one from a setting, unless the build wrote code for it. Today's processor has three gaps of its own, too. Its message names only the last step ("Truck needs Driver"), which helps little when ten classes need a driver. It has no answer to a cycle. And it has no way to bind a class you can't put a note on, such as one from a library. Those three are the next lesson."""

# ---------------------------------------------------------------- closing
CLOSING = """We started with a moving-day plan that someone has to write before the crew arrives. KSP now writes it during the build: a factory for each class, the isolating cards, and a component that builds the crew in dependency order, the aggregating master list. One truck, one route, two rolls of tape, and no reflection anywhere.

In your own code, find the block near `main` that calls `new` on helper after helper. That block is a hand-written plan.

Next, we'll break the plan on purpose: a driver nobody provides, a driver who waits for the truck, and two routes with no names. Can the build name every mistake, with its file and line, before anyone moves a box?"""

L = {
 "id": "cap5-01",
 "title": "Factories and a component, generated at build time",
 "minutes": 40,
 "goal": "By the end you can say what dependency injection does, write a KSP processor that generates a factory for each @Inject class and a component that builds the whole graph in dependency order, and compare it with a container that wires by reflection.",
 "opening": OPENING,
 "warmup": {
  "q": "A generated component builds `Route`, then `Driver(route)`, then `Truck(driver)`, each as a `private val` in a Kotlin class. What happens if the generator writes the driver's line above the route's?",
  "options": ["Nothing changes: Kotlin initializes properties in any order it likes", "It compiles, and the driver gets `null` for its route at run time", "It doesn't compile: Kotlin rejects an initializer that reads a property declared below it", "KSP sorts the lines before the compiler sees them"],
  "answer": 2,
  "why": "Kotlin runs property initializers from top to bottom, and the compiler refuses one that reads a property declared further down: `Variable 'route' must be initialized.` (javac says `illegal forward reference` for the Java version). So the generator must write the plan in dependency order, which is the walk in the third section. The `null` answer is tempting because a call through a function can sneak past the check; a direct read can't."
 },
 "sections": [
  {
   "h": "The moving-day plan, written by hand: dependencies, bindings and one shared truck",
   "body": S0
  },
  {
   "h": "One card per class: a factory for each @Inject constructor",
   "body": S1,
   "try": {
    "title": "Watch the factory processor write its cards",
    "minutes": 4,
    "steps": [
     "Run `FactoryDemo` from `labs/`. It compiles three small classes in memory with lesson 1's reference processor and prints every card it wrote.",
     "Run `FactoryDemoJava`, which does the same job with a javac annotation processor on three Java classes. Compare the two `DriverFactory` files line by line.",
     "In `FactoryDemo.kt`, give the truck a second parameter: `class Truck @Inject constructor(val driver: Driver, val route: Route)`. Predict `TruckFactory`, then run again."
    ],
    "code": code(f"{DEMO_K}/FactoryDemo.kt", "./gradlew :injector:demo -Pmain=workbench.injector.l01.demo.FactoryDemoKt",
                 f"{DEMO_J}/FactoryDemoJava.java", "./gradlew :injector:demo -Pmain=workbench.injector.l01.demo.FactoryDemoJava"),
    "expect": "The Kotlin demo prints `exit code: OK` and three files, among them `public fun create(route: Route): Driver = Driver(route)`. The Java twin prints `javac succeeded: true` and `public static Driver create(movemate.Route route)`, with the full type name, because its string template doesn't manage imports the way KotlinPoet does. With the extra parameter, `TruckFactory` becomes `create(driver: Driver, route: Route)`, and no other card changes."
   },
   "refs": [{"title": "KSP overview (Kotlin docs)", "url": "https://kotlinlang.org/docs/ksp-overview.html", "kind": "docs"}]
  },
  {
   "h": "The plan for the whole day: a component that builds the crew in order",
   "body": S2,
   "figure": {"svg": FIG, "caption": "The crew's graph: each arrow means \"needs\". The plan builds every box after the boxes it points at, so the numbers are the order of the lines in the generated component."},
   "try": {
    "title": "Build the plan in a real Gradle build",
    "minutes": 5,
    "steps": [
     "From `labs/`, run `./gradlew :injector:app:kspL01Kotlin` and open `injector/app/build/generated/ksp/l01/kotlin/workbench/injector/app/l01/GeneratedMovingDayComponent.kt`. Find the line that builds the truck. Which lines must come before it?",
     "Run `MovingDayApp` with the command below, then its Java twin, `MovingDayAppJava`.",
     "Delete `@Singleton` above `class Truck` in `app/src/l01/.../Truck.kt`. Predict how the component changes and what `one truck for the whole day` prints. Run `MovingDayApp` again, then put the annotation back."
    ],
    "code": code(f"{APP_K}/MovingDayApp.kt", "./gradlew :injector:app:demo -Pmain=workbench.injector.app.l01.MovingDayAppKt",
                 f"{APP_J}/MovingDayAppJava.java", "./gradlew :injector:app:demo -Pmain=workbench.injector.app.l01.MovingDayAppJava"),
    "expect": "Both languages print `Sam drives truck MOVE-1 on the highway (42 min)`, tape rolls `#1` and `#2`, `one truck for the whole day: true` and `tape rolls made: 2`. Without `@Singleton`, the truck's `val` becomes `private fun newTruck(): Truck`, the crew's line calls `newTruck()`, `truck()` returns `newTruck()`, and the line prints `false`: the crew drives one truck and `truck()` builds another."
   },
   "refs": [{"title": "Incremental processing (Kotlin docs)", "url": "https://kotlinlang.org/docs/ksp-incremental.html", "kind": "docs"}]
  },
  {
   "h": "The night before or on the street: generated wiring next to the reflection container",
   "body": S3,
   "try": {
    "title": "Forget a note, and see who complains",
    "minutes": 3,
    "steps": [
     "In `labs/injector/app/src/l01/kotlin/workbench/injector/app/l01/Driver.kt`, delete `@Inject`. From `labs/`, run `./gradlew :injector:app:kspL01Kotlin`. Which file and line does the error name, and why that one?",
     "Now put the note on the class instead (`@Inject class Driver(val route: Route) { ... }`, keeping `@Singleton` above it) and run the task again.",
     "Open `GeneratedMovingDayComponent.kt` once more. Did anything in it change?"
    ],
    "expect": "The first run fails with `e: [ksp] .../Truck.kt:8: Truck needs Driver, but nobody provides Driver. Add @Inject to its constructor.` and `KSP failed with exit code: PROCESSING_ERROR`: the error names the truck's parameter, where a driver is asked for. With `@Inject` on the class, the build passes, `DriverFactory.kt` is back, and the component is the same as before, because a note on the class means its primary constructor."
   }
  }
 ],
 "compare": {
  "title": "One card, two helpers: the factory javac's processor writes and the one KSP writes",
  "java": {"title": "DriverFactory.java (from FactoryDemoJava)", "src": "// Generated by FactoryAnnotationProcessor from Driver. Do not edit.\npackage movemate;\n\npublic final class DriverFactory {\n    private DriverFactory() {}\n\n    public static Driver create(movemate.Route route) {\n        return new Driver(route);\n    }\n}\n\n// a caller\nDriver driver = DriverFactory.create(new Route());"},
  "kotlin": {"title": "DriverFactory.kt (from FactoryDemo)", "src": "// Generated by FactoryProcessor from Driver. Do not edit.\npackage movemate\n\npublic object DriverFactory {\n  public fun create(route: Route): Driver = Driver(route)\n}\n\n// a caller in Kotlin, then in Java\nval driver = DriverFactory.create(Route())\n// Driver driver = DriverFactory.INSTANCE.create(new Route());"},
  "note": "Both helpers read the same constructor and write a card that takes what it takes and calls it. The Java card is a final class with a static method and a private constructor, so nobody can build the factory itself; the Kotlin card is an `object`, which Java reaches through `INSTANCE`. The javac processor wrote its text with a string template, so it spells `movemate.Route` in full; KotlinPoet manages imports and would add one for a type from another package. Neither card uses reflection, and both are ordinary source that the compiler checks like your own."
 },
 "worked": {
  "title": "Add a moving blanket to the plan",
  "steps": [
   {"say": "The family's piano needs wrapping, so a packer now needs a moving blanket. Start with the class, and give it an `@Inject` constructor.",
    "code": "class Blanket @Inject constructor()", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "public class Blanket {\n    @Inject\n    public Blanket() {}\n}"},
   {"say": "Ask for it where it's needed: in the packer's constructor. That's the only change you make by hand.",
    "code": "@Inject\nclass Packer(val tape: TapeRoll, val blanket: Blanket)", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "public class Packer {\n    @Inject\n    public Packer(TapeRoll tape, Blanket blanket) { /* ... */ }\n}"},
   {"say": "Build. KSP writes `BlanketFactory`, `PackerFactory.create` gains a parameter, and the packer's line in the component changes. The walk put the blanket before the packer, as post-order must.",
    "code": "private fun newBlanket(): Blanket = BlanketFactory.create()\n\nprivate fun newPacker(): Packer = PackerFactory.create(newTapeRoll(), newBlanket())", "lang": "kotlin",
    "alt_lang": "java", "alt_code": "private Blanket newBlanket() { return BlanketFactory.create(); }\n\nprivate Packer newPacker() { return PackerFactory.create(newTapeRoll(), newBlanket()); }"},
   {"say": "Decide whether it's shared. Without `@Singleton`, each packer gets its own blanket, like its own roll of tape. Add `@Singleton` only if one blanket for the whole day is what you mean, because then every packer wraps with the same one.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Write the factory processor and the component processor",
  "minutes": 15,
  "files": [f"{MAIN}/FactoryProcessor.kt", f"{MAIN}/Bindings.kt", f"{MAIN}/ComponentProcessor.kt"],
  "run": "./gradlew :injector:test --tests 'workbench.injector.l01.*'",
  "steps": [
   "Run the tests once. Five of seven fail, each with a warning such as `w: [ksp] l01 not done yet: write <Name>Factory.kt: ...`. The two that pass test the given checks. The crew the tests compile is in `src/test/kotlin/workbench/injector/l01/MoveMateSources.kt`.",
   "Find and Check are given. Read `writeFactories` and `checked` in `FactoryProcessor.kt`, then `writeComponents` and `checkedEntryPoints` in `ComponentProcessor.kt`. Note which `Dependencies` each processor passes, and why.",
   "Write: in `factoryFile`, build one `ParameterSpec` per constructor parameter (`it.type.toTypeName()`), a `create` function that returns `%T(%L)`, and an `objectBuilder` around it. Run `FactoriesTest` until its three tests pass.",
   "Read: in `Bindings.kt`, write `creationOrder`. Walk depth first from each entry point, add a binding when you leave it, and add each one once. For a type nobody provides, log the exact message from the KDoc on the parameter that asks, keep walking, and return null at the end.",
   "Write: in `componentFile`, add a `PropertySpec` for each singleton in the order you're given, a private `FunSpec` for each of the others, then one override per entry point. Use `memberName`, `reference` and `construct`.",
   "Prove: run the tests until all seven pass. Then run your processors in the real build with `./gradlew :injector:app:kspL01Kotlin -Pmine=l01`, open the generated component, and run `./gradlew :injector:app:demo -Pmain=workbench.injector.app.l01.MovingDayAppKt -Pmine=l01`.",
   "From memory: close the files and write the post-order walk on paper, for a map from each class name to the names it needs. Then compare it with your `creationOrder`."
  ],
  "hints": [
   "`binding.parameters` works for both kinds of note: `checked` already found the constructor, whether `@Inject` sat on the class or on the constructor.",
   "`parameters.map { CodeBlock.of(\"%N\", it) }.joinToCode(\", \")` gives `truck, kitchenPacker, bedroomPacker` for the constructor call.",
   "If a test prints `Variable 'route' must be initialized.`, your component lists a singleton before something it needs. The order from `creationOrder` must be post-order: a binding goes in after its dependencies.",
   "KotlinPoet writes all properties before all functions, whatever order you add them in. That's why the vals come first in the file, and why the private functions can be added in any order."
  ],
  "done_when": "All seven tests in `FactoriesTest` and `ComponentTest` pass, and `MovingDayApp` prints `one truck for the whole day: true` with `-Pmine=l01`."
 },
 "drill": {
  "title": "Write the creation order from memory",
  "minutes": 4,
  "prompt": "Close this page. Write `creationOrder(needs, wanted)`: `needs` maps each class name to the names its constructor asks for, and the result lists every name the `wanted` ones need, each after everything it needs, each once. Check it on `MovingDay -> [Crew, Route]`, `Crew -> [Truck, Packer]`, `Truck -> [Driver]`, `Driver -> [Route]`, `Packer -> [TapeRoll]`, wanting `[MovingDay]`. Then write it in Java.",
  "answer": {"lang": "kotlin", "src": "fun creationOrder(needs: Map<String, List<String>>, wanted: List<String>): List<String> {\n    val order = LinkedHashSet<String>()\n    fun visit(name: String) {\n        if (name in order) return                    // already in the plan\n        needs[name].orEmpty().forEach(::visit)       // everything it needs first\n        order += name                                // then the name itself: post-order\n    }\n    wanted.forEach(::visit)\n    return order.toList()\n}\n// [Route, Driver, Truck, TapeRoll, Packer, Crew, MovingDay]",
             "alt": {"lang": "java", "title": "CreationOrder.java", "src": "static List<String> creationOrder(Map<String, List<String>> needs, List<String> wanted) {\n    LinkedHashSet<String> order = new LinkedHashSet<>();\n    for (String name : wanted) visit(name, needs, order);\n    return new ArrayList<>(order);\n}\n\nstatic void visit(String name, Map<String, List<String>> needs, LinkedHashSet<String> order) {\n    if (order.contains(name)) return;                                // already in the plan\n    for (String d : needs.getOrDefault(name, List.of())) visit(d, needs, order);\n    order.add(name);                                                 // post-order\n}"}}
 },
 "recap": [
  "Dependency injection hands each object what its constructor asks for. A binding says how to get one type; a singleton exists once per plan, and anything else is built new for each request.",
  "The factory processor writes one `<Name>Factory` per `@Inject` class: an isolating output, written with `Dependencies(aggregating = false, thatClassFile)`.",
  "The component processor walks the graph depth first from the `@Component` functions and writes the plan in post-order: a `private val` per singleton, a `new...()` function for the rest, an override per entry point.",
  "The order is load-bearing: Kotlin rejects an initializer that reads a property declared below it (`Variable 'route' must be initialized.`), and javac does the same (`illegal forward reference`).",
  "The component is aggregating: built from many files and redone whenever any of them changes. A mistake in the wiring fails the build on the file and line that asked.",
  "The limit: the plan is fixed when you build, the message names only the last step, and the walk has no memory of its path, so a cycle runs it until the stack runs out."
 ],
 "closing": CLOSING,
 "quiz": [
  {"q": "The factory processor writes `DriverFactory.kt` from the `@Inject` constructor in `Driver.kt`. Which `Dependencies` should it pass?",
   "options": ["`Dependencies(aggregating = false, driverFile)`", "`Dependencies(aggregating = true, driverFile)`", "`Dependencies.ALL_FILES`", "`Dependencies(false)`, with no files"],
   "answer": 0,
   "why": "The card depends on `Driver.kt` alone, so it's isolating and names that file. Aggregating would redo it whenever any file changes, and `ALL_FILES` switches incremental processing off. With no files at all, KSP can't tie the output to a source, and an incremental build can delete it as a stale output, the trap from Incremental builds and processor options.",
   "from": "ksp-07"},
  {"q": "`Packer` has no `@Singleton`, and `Crew @Inject constructor(val truck: Truck, val kitchenPacker: Packer, val bedroomPacker: Packer)` is a singleton. How many tape rolls does one component make for its crew?",
   "options": ["One, shared by both packers", "Two, one for each packer", "None until a packer uses one", "It depends on the order of the constructor parameters"],
   "answer": 1,
   "why": "The crew's line calls `newPacker()` twice, and every call builds a new packer with a new tape roll from `newTapeRoll()`. A roll would be shared only if `TapeRoll` were a singleton. The crew itself is built once, so the count stays at two however often you ask for the moving day."},
  {"q": "`Truck` loses its `@Singleton`; everything else stays the same. What does `plan.truck() === plan.movingDay().crew.truck` print?",
   "options": ["`true`, because the crew is a singleton", "A compile error in the generated component", "The generated code throws at run time", "`false`"],
   "answer": 3,
   "why": "The truck becomes `private fun newTruck()`. The crew, still a singleton, got a truck when it was built, and `truck()` now builds another one. Both compile and run fine; they're just two trucks. The demo in the second Try it prints exactly that."},
  {"q": "`Driver` has no `@Inject`, and `Truck @Inject constructor(val driver: Driver)` asks for one. Where does lesson 1's error point?",
   "options": ["At the processor's own source code", "At the generated component", "At `Truck.kt`, on the line of `val driver: Driver`", "At `Driver.kt`, on the class line"],
   "answer": 2,
   "why": "The walk reports a missing binding on the parameter that asks for it, with `logger.error(message, parameter)`. That's the place you'd look first: the request nobody can answer. The generated component isn't written at all when the walk finds a problem."},
  {"q": "Which job could Part 4's reflection container do that the generated component can't?",
   "options": ["Share one instance among many classes", "Pick a part it finds on the class path while the program runs", "Build parts in dependency order", "Report a missing binding"],
   "answer": 1,
   "why": "The generated plan is fixed when you build: it can only build what the processor wrote code for. Both can share singletons, order the graph and report a missing binding; the generated one just does the last two in the build, before the program runs."}
 ],
 "flashcards": [
  {"front": "What is a dependency?", "back": "An object another object needs to do its job. The driver is a dependency of the truck."},
  {"front": "What is constructor injection?", "back": "A class lists what it needs as constructor parameters, and something outside builds those and passes them in."},
  {"front": "Isolating or aggregating: a factory for one `@Inject` class?", "back": "Isolating. It depends only on that class's file: `Dependencies(aggregating = false, file)`."},
  {"front": "Isolating or aggregating: the generated component?", "back": "Aggregating. It's built from many files and is redone whenever any of them changes."},
  {"front": "In what order does the component build its singletons, and why does it matter?", "back": "Depth-first post-order: each one after everything its constructor needs. Kotlin initializes properties top to bottom and rejects a forward read with `Variable '...' must be initialized.`"},
  {"front": "How does the generated component handle a binding without `@Singleton`?", "back": "As a private `new<Name>()` function, so every request builds a new object."}
 ],
 "terms": [
  {"term": "Dependency", "plain": "An object that another object needs in order to do its job."},
  {"term": "Dependency injection", "plain": "Handing an object its dependencies from outside, instead of letting it build them itself."},
  {"term": "Constructor injection", "plain": "Dependency injection through constructor parameters: the class says what it needs, and someone else passes it in."},
  {"term": "Binding", "plain": "One line of the plan: how to get one type, such as \"call the @Inject constructor of Driver\"."},
  {"term": "Singleton", "plain": "A binding that exists once per component and is shared by everyone who asks for it."},
  {"term": "Graph", "plain": "The bindings and the arrows between them: who needs whom."},
  {"term": "Factory", "plain": "Generated code whose only job is to build one class from what its constructor takes."},
  {"term": "Component", "plain": "The generated class that implements a @Component interface and builds the whole graph in dependency order."}
 ],
 "explain_back": {
  "prompt": "A teammate opens `GeneratedMovingDayComponent.kt` and asks three things: what this class is for, why its lines come in exactly that order, and why KSP is told different things about the factories and about the component. Explain.",
  "answer": "It's the plan for the moving day, written by a processor during the build. Each class says in its constructor what it needs, and the component builds everything the `MovingDayComponent` interface hands out, handing each class its dependencies. Singletons, like the one truck, are private vals built once; everything else, like a tape roll, comes from a private function, so each request gets a new one. The lines are in depth-first post-order: every val comes after the vals it reads. Kotlin initializes properties from top to bottom and won't compile a line that reads a property declared below it, so the order is what makes the class compile at all. Each factory depends only on its own class's file, so it's declared isolating, and KSP can leave it alone when another file changes. The component is built from many files, so it's declared aggregating and is redone whenever any file changes."
 },
 "deeper": {
  "minutes": 8,
  "body": "Why generate factories at all, when the component could call each constructor directly? In a single module, it could. The factory earns its keep when classes live in several modules. A library module compiled earlier ships its factories with it, and the component in the app module only calls them. Each factory is compiled once, in the module that owns the class, so the app's build never needs to look inside that class's constructor again beyond its signature.\n\nOur component builds its singletons eagerly, in the constructor. That keeps the generated text in plain dependency order, and it's thread-safe for a simple reason: each `private val` compiles to a `private final` field, and the memory model guarantees that final fields set in a constructor are visible to any thread that sees the finished object (the memory model track has the rule). The cost is that creating the component builds everything, even parts nobody asks for. Lesson 3 adds `Lazy<T>` for the one expensive part.\n\nA singleton here is one per component object, not one per program. Create two `GeneratedMovingDayComponent`s and you get two trucks. That's usually what you want in tests: each test builds its own plan.\n\nThe javac twin of the factory processor has a trap of its own. Since JDK 23, javac doesn't run processors it merely finds on the class path; it needs `--processor-path`, `-processor` or `-proc:full`. Gradle's `annotationProcessor` configuration passes the processor path explicitly, and `FactoryDemoJava` hands the processor to the compiler task directly, so neither is affected."
 },
 "sources": [
  {"title": "KSP overview (Kotlin docs)", "url": "https://kotlinlang.org/docs/ksp-overview.html"},
  {"title": "Incremental processing (Kotlin docs)", "url": "https://kotlinlang.org/docs/ksp-incremental.html"},
  {"title": "KotlinPoet: KSP interop (KotlinPoet docs, 2.4.0)", "url": "https://raw.githubusercontent.com/square/kotlinpoet/2.4.0/docs/interop-ksp.md"},
  {"title": "javax.annotation.processing.Filer (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.compiler/javax/annotation/processing/Filer.html"}
 ]
}
out = ROOT / "content/lessons/cap5-01.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
