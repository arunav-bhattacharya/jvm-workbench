rootProject.name = "jvm-workbench-labs"

// one subproject per track; each has exercises (src/main), solutions (src/solution),
// shared tests (src/test) and runnable demos (src/demo)
include("concurrency", "jmm", "executors", "vthreads", "generics", "reactive", "coroutines", "patterns")
include("memory", "performance", "bytecode", "nio", "startup", "kotlin", "modernjava")
