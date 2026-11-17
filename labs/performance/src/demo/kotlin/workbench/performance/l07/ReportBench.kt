package workbench.performance.l07

import java.lang.management.ManagementFactory

// ReportBench.java proves the fix with JMH, which needs Java classes in this lab. This Kotlin twin
// proves it for the Kotlin versions in ReportInvestigation.kt with the per-thread allocation counter,
// the same measurement the lab's test uses: warm up, then bytes per call over 100,000 calls.

private val counter = ManagementFactory.getThreadMXBean() as com.sun.management.ThreadMXBean
private var sink = 0L                                   // results go somewhere the JIT can't ignore

private inline fun bytesPerCall(call: () -> Long): Double {   // inline: no boxing of the Long
    var best = Double.MAX_VALUE
    repeat(10) {                                        // the first rounds include warm-up; keep the best
        val before = counter.currentThreadAllocatedBytes
        repeat(100_000) { sink += call() }
        best = minOf(best, (counter.currentThreadAllocatedBytes - before) / 100_000.0)
    }
    return best
}

fun main() {
    val d = KtDocument("doc-7", "fr", "the rain came early and the river rose over the old stone")
    println("ktSlow:    %8.1f B/call".format(bytesPerCall { ktSlow(d) }))
    println("ktHoisted: %8.1f B/call".format(bytesPerCall { ktHoisted(d) }))
    println("ktScanned: %8.1f B/call".format(bytesPerCall { ktScanned(d) }))
    println("ktNoRegex: %8.1f B/call".format(bytesPerCall { ktNoRegex(d) }))
    println("(checksum $sink)")
}
