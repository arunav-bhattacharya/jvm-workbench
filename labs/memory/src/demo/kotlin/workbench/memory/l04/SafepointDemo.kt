package workbench.memory.l04

import workbench.memory.Jvm

/** Logs every safepoint during one second of service load and prints the GC ones. */
fun main(args: Array<String>) {
    if (args.isNotEmpty()) {
        serviceLoad(1.0, 0.30)
        return
    }
    Jvm.lines(listOf("-XX:+UseG1GC", "-Xmx256m", "-Xlog:safepoint"), "workbench.memory.l04.SafepointDemoKt", "load")
        .filter { "G1CollectForAllocation" in it }
        .take(5)
        .forEach(::println)
}
