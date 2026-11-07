package workbench.memory.l06

import com.sun.management.HotSpotDiagnosticMXBean
import workbench.memory.Jvm
import java.lang.management.ManagementFactory

/**
 * Shows the max heap the JVM picks for a memory limit, with and without -XX:MaxRAMPercentage.
 * -XX:MaxRAM stands in for a container limit here; it is deprecated in JDK 26 and gone in JDK 27.
 */
fun main(args: Array<String>) {
    if (args.isNotEmpty()) {
        val hotspot = ManagementFactory.getPlatformMXBean(HotSpotDiagnosticMXBean::class.java)
        val max = hotspot.getVMOption("MaxHeapSize").value.toLong()
        println("max heap %,6d MB".format(max shr 20))
        return
    }
    if (Runtime.version().feature() >= 27) {
        println("JDK 27 removed -XX:MaxRAM. Try this inside a container with a memory limit instead.")
        return
    }
    for (limit in listOf("1g", "2g", "4g")) {
        for (percent in listOf("", "-XX:MaxRAMPercentage=75")) {
            val flags = listOf("-XX:MaxRAM=$limit") + listOfNotNull(percent.ifEmpty { null })
            val result = Jvm.lines(flags, "workbench.memory.l06.HeapSizingDemoKt", "child")
                .firstOrNull { it.startsWith("max heap") } ?: "(no answer)"
            println("limit %s %-26s -> %s".format(limit, percent.ifEmpty { "(defaults: 25%)" }, result))
        }
    }
}
