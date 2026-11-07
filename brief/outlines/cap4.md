# Track: cap4, "Capstone: a tiny dependency injection container" (lab: labs/container, package workbench.container.lNN)

Part 4, Inside the JVM (cls, mem, perf, boot). Draws on every track in the part.
Dependencies allowed in labs/container/build.gradle.kts: byte-buddy, jmh-core and the JMH annotation
processor on demo only (copy the setup from labs/performance), jol-core for demos.

The program: a small DI container that wires classes by constructor, adds interceptors through
proxies, and is then measured and made to start fast. It shows why Spring does this at run time and
Quarkus and Micronaut move it to build time.

- cap4-01 Wiring by reflection: find the classes to wire (an explicit list or a scan through a class
  loader's resources), pick constructors, resolve a dependency graph, detect cycles, singleton and
  prototype scopes, lazy init with the holder idiom. Tests: graph order, cycle error message, one
  instance per singleton under concurrent first access.
- cap4-02 Interceptors with proxies: @Timed and @Retry via java.lang.reflect.Proxy for interfaces,
  Byte Buddy subclassing for classes, why final classes and Kotlin's default-final break this (all-open),
  equals and hashCode on proxies, invokeDefault. Tests: retry counts, interception on both kinds,
  identity semantics.
- cap4-03 Measure it, then make it start fast: a JMH benchmark of direct vs proxy vs Byte Buddy calls
  (demo source set, results labelled indicative), allocation per call from JFR or the allocation meter,
  class count and time at start with -Xlog:class+load, then move the wiring to a generated "build
  time" registry (a small code generator run in the test) and show what that saves; AppCDS/AOT cache
  commands in Try-it steps. Tests: the generated registry wires the same graph as the reflective one.
  Ends with the design review (run-time vs build-time wiring).
