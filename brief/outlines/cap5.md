# Track: cap5, "Capstone: dependency injection at compile time" (lab: labs/injector, package workbench.injector.lNN)

Part 5, "Code generation with KSP". The capstone after the ksp track (brief/outlines/ksp.md). Read that outline
first: its "Read first" list, reader, picture, voice, both-languages rule, versions and the five lab moves all
apply here. The lab modules are labs/injector (the processor the reader writes), labs/injector/annotations and
labs/injector/app (a real build using the processor); brief/outlines/ksp-labs.md explains them.

## Why this capstone

In Part 4's capstone (cap4) the reader built a small dependency injection container that wires classes by
reflection while the program runs, and in cap4-03 moved the wiring to a "build time" registry made by a tiny
generator run in a test. Here they build that idea properly with KSP: the wiring code is generated during the
build, mistakes in the wiring become compile errors with a file and line, and nothing is looked up by reflection
when the program starts. Open cap5-01 with a one-sentence reminder of cap4 (what dependency injection is, in
plain words: each class says what it needs in its constructor, and something else builds the objects in the
right order and hands them over), never assuming the reader remembers the details.

Define every term at first use: dependency, dependency injection, constructor injection, binding, singleton,
graph, cycle, component, factory, qualifier.

## Picture: the moving-day plan (continues the ksp track's moving house)

On moving day, people and things depend on each other: the truck needs a driver, the driver needs the route,
the packers need boxes, and the crew can't start until all of them are ready. Someone writes the plan the night
before: who arrives first, who waits for whom, and which people are shared (one truck for the whole day, a
singleton) and which are fresh each time (a new roll of tape per room). Writing the plan the night before is
compile-time wiring; working it out on the street on the day is reflection. A plan that has the driver waiting
for the truck and the truck waiting for the driver is a cycle, and it's far better to spot it the night before.
Map each part and say where it breaks.

## The running example

MoveMate's moving-day crew: `Route`, `Driver(route)`, `Truck(driver)`, `TapeRoll` (a new one each time),
`Packer(tape)`, `Crew(truck, packers)`, `MovingDay(crew, route)`. Annotations in labs/injector/annotations:
`@Inject` on a constructor (or class), `@Singleton`, `@Component` on an interface listing what the app asks
for, `@Module` with `@Provides` functions for things the reader can't annotate (a third-party class), and a
`@Named` qualifier for two bindings of the same type (two routes: "highway" and "back roads").

## Lessons

- cap5-01 The plan the night before: factories and a component. From an `@Inject` constructor generate one
  factory per class (isolating output: it depends only on that class's file), then an aggregating component that
  implements the `@Component` interface and builds the graph in dependency order, with singletons held once.
  Read the generated component aloud: it's the code you would write by hand, in the right order. Compare with
  cap4's reflection container in one table (when the wiring is checked, what runs at start, what the stack trace
  looks like). Java twin: a javac annotation processor generating the same factories, and Java calling the
  generated component. Lab: the factory and component processors; tests compile small graphs in memory and call
  the generated component; the app wires the full MoveMate crew.
- cap5-02 Mistakes caught the night before: missing bindings, cycles and duplicates. Each mistake first as the
  reader's code would meet it at run time in a reflection container (show it), then as a compile error from the
  processor with the full dependency path ("MovingDay needs Crew needs Truck needs Driver: nobody provides
  Driver") on the exact file and line. Cycle detection with the path printed; two bindings for one type and the
  `@Named` fix; `@Module`/`@Provides` for a class the reader can't annotate. Report every problem in one build.
  Lab: the graph checks with tests asserting messages, files and lines; one test per kind of mistake.
- cap5-03 Measure the payoff, then see the real tools. Measure start-up and first-request cost of the generated
  component against the reflection container (loaded-machine numbers, labeled), count the classes loaded at start,
  and confirm the generated code uses no reflection. Incremental behaviour in the app: change one class and read
  the incremental log (factories regenerate alone, the component regenerates because it aggregates). Then the
  real tools in a short aside after the idea, each in one plain sentence from the research notes: Dagger and
  Hilt, kotlin-inject, and Koin (whose KSP processor is now deprecated in favour of a compiler plugin), and how
  their designs differ from ours. Lab: lazy and provider
  injection (`Lazy<T>` or `() -> T` for something expensive, such as the truck's GPS), plus a small benchmark
  demo; tests for laziness and for "no reflection at start" (the generated code references no java.lang.reflect).
  The closing looks back over the whole part.

## Track file

The writer also writes content/tracks/cap5.json (intro, cheatsheet, recap, quiz) like content/tracks/cap4.json.
