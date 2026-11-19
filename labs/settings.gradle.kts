rootProject.name = "jvm-workbench-labs"

// one subproject per track; each has exercises (src/main), solutions (src/solution),
// shared tests (src/test) and runnable demos (src/demo)
include("concurrency", "jmm", "executors", "vthreads", "generics", "reactive", "coroutines", "patterns")
include("memory", "performance", "bytecode", "nio", "startup", "kotlin", "modernjava")
include("ledger", "quotes", "events", "container")
include("functional")
include("flows")

// processor labs: the KSP track (labs/ksp) and its capstone, compile-time dependency injection (labs/injector).
// Each lab nests two helper projects: <lab>/annotations (what the processors look for) and <lab>/app
// (an ordinary consumer that runs the processors with the real KSP Gradle plugin). See processorLab() in
// build.gradle.kts and brief/outlines/ksp-labs.md.
include("ksp", "ksp:annotations", "ksp:app")
include("injector", "injector:annotations", "injector:app")
