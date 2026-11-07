package workbench.memory.l05

import workbench.memory.Jvm
import workbench.memory.l04.serviceLoad

private val PAUSE = Regex("""Pause .*?([\d.]+)ms$""")
private val CYCLE = Regex("""GC\((\d+)\) (Minor|Major) Collection \(.*\) .*->.* ([\d.]+)s$""")

/**
 * Runs two seconds of service load under generational ZGC in a child JVM. Prints every line of the
 * first minor collection, then compares the real pauses with the collection times.
 */
fun main(args: Array<String>) {
    if (args.isNotEmpty()) {
        serviceLoad(2.0, 0.30)
        return
    }
    val flags = mutableListOf("-XX:+UseZGC", "-Xmx1g", "-Xlog:gc,gc+phases")
    if (Runtime.version().feature() < 23) flags += "-XX:+ZGenerational"         // generational is the default from 23
    val log = Jvm.lines(flags, "workbench.memory.l05.ZgcDemoKt", "load")

    val firstMinor = log.firstOrNull { "Minor Collection" in it }
        ?.let { Regex("""GC\(\d+\)""").find(it)?.value } ?: "none"
    log.filter { "$firstMinor " in it }.forEach { println(it.replace(Regex("\\s+"), " ")) }

    val pauses = log.mapNotNull { PAUSE.find(it)?.groupValues?.get(1)?.toDouble() }
    val cycles = log.mapNotNull { CYCLE.find(it)?.groupValues?.get(3)?.toDouble() }
    println()
    println("%d collections took %.3f s in all, running alongside the application".format(cycles.size, cycles.sum()))
    println("%d stop-the-world pauses took %.3f ms in all; the longest was %.3f ms".format(pauses.size, pauses.sum(), pauses.maxOrNull() ?: 0.0))
    println("allocation stalls: ${log.count { "Allocation Stall (" in it }}")
}
