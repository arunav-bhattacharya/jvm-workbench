package workbench.memory.l04

import workbench.memory.Jvm

// "GC(12) Pause Young (Mixed) (G1 Evacuation Pause) ..." -> "Pause Young (Mixed)"
private val KIND = Regex("""GC\(\d+\) ((?:Pause \w+(?: \((?:Normal|Concurrent Start|Prepare Mixed|Mixed)\))?)|Concurrent \w+ Cycle)""")

/**
 * Runs the service load for 3 seconds in a child JVM with a tight 256 MB G1 heap, then counts each
 * kind of GC event and prints the first line of each kind.
 */
fun main(args: Array<String>) {
    if (args.isNotEmpty()) {
        serviceLoad(3.0, 0.60)
        return
    }
    val log = Jvm.lines(listOf("-XX:+UseG1GC", "-Xmx256m", "-Xlog:gc"), "workbench.memory.l04.G1CycleDemoKt", "load")
    val events = log.mapNotNull { line ->
        val kind = KIND.find(line)?.groupValues?.get(1)
        if (kind == null || line.endsWith("Cycle")) null else kind to line   // skip the "cycle started" half
    }
    events.groupingBy { it.first }.eachCount().toSortedMap().forEach { (kind, n) -> println("%4d x %s".format(n, kind)) }
    println("${events.count { "(Evacuation Failure)" in it.second }} pauses had an evacuation failure")
    println()
    events.distinctBy { it.first }.forEach { println(it.second) }                    // in the order they first happened
}
