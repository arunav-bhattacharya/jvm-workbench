package workbench.memory.l02

import com.sun.management.ThreadMXBean
import workbench.memory.Jvm
import java.lang.management.ManagementFactory

data class KPoint(val x: Long, val y: Long)                       // 12-byte header + 16 bytes of fields: 32 bytes

fun sumPoints(n: Int): Long {
    var s = 0L
    for (i in 0 until n) {
        val p = KPoint(i.toLong(), i + 1L)                         // p never leaves this function
        s += p.x + p.y
    }
    return s
}

/**
 * Sums a million short-lived points per round and counts the bytes each round allocates.
 * The demo runs the experiment twice, in child JVMs: with escape analysis, and without it.
 */
fun main(args: Array<String>) {
    if (args.isEmpty()) {
        println("== default flags: escape analysis on")
        Jvm.run(listOf(), "workbench.memory.l02.EscapeDemoKt", "measure")
        println("== -XX:-DoEscapeAnalysis")
        Jvm.run(listOf("-XX:-DoEscapeAnalysis"), "workbench.memory.l02.EscapeDemoKt", "measure")
        return
    }
    val threads = ManagementFactory.getThreadMXBean() as ThreadMXBean
    var checksum = 0L
    for (round in 0 until 10) {
        val before = threads.currentThreadAllocatedBytes
        checksum += sumPoints(1_000_000)
        val bytes = threads.currentThreadAllocatedBytes - before
        println("round %d: %,12d bytes".format(round, bytes))
    }
    println("checksum $checksum")
}
