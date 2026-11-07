package workbench.memory.l05

import com.sun.management.OperatingSystemMXBean
import workbench.memory.Jvm
import workbench.memory.l04.serviceLoad
import java.lang.management.ManagementFactory

private val PAUSE_MS = Regex("""Pause .*?([\d.]+)ms$""")

/** The same second of service load in a 512 MB heap under each collector, each in its own child JVM. */
fun main(args: Array<String>) {
    if (args.isNotEmpty()) {                                          // child: do the work, report work and CPU
        val rounds = serviceLoad(1.0, 0.30)
        val os = ManagementFactory.getOperatingSystemMXBean() as OperatingSystemMXBean
        println("RESULT $rounds ${os.processCpuTime / 1_000_000}")
        return
    }
    val zgc = if (Runtime.version().feature() < 23) listOf("-XX:+UseZGC", "-XX:+ZGenerational") else listOf("-XX:+UseZGC")
    val collectors = listOf(listOf("-XX:+UseSerialGC"), listOf("-XX:+UseParallelGC"), listOf("-XX:+UseG1GC"), zgc, listOf("-XX:+UseShenandoahGC"))
    println("%-20s %7s %10s %12s %8s %8s".format("collector", "pauses", "longest", "all pauses", "rounds", "CPU ms"))
    for (gc in collectors) {
        val log = Jvm.lines(gc + listOf("-Xmx512m", "-Xlog:gc,gc+phases"), "workbench.memory.l05.CollectorCompareDemoKt", "load")
        val name = gc[0].removePrefix("-XX:+")
        val result = log.firstOrNull { it.startsWith("RESULT ") }
        if (result == null) {
            println("%-20s not in this JDK build".format(name))
            continue
        }
        val pauses = log.mapNotNull { PAUSE_MS.find(it)?.groupValues?.get(1)?.toDouble() }
        val (_, rounds, cpu) = result.split(" ")
        println("%-20s %7d %8.2fms %10.1fms %8s %8s".format(name, pauses.size, pauses.maxOrNull() ?: 0.0, pauses.sum(), rounds, cpu))
    }
}
