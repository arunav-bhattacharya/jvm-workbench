package workbench.memory.l02

import com.sun.management.ThreadMXBean
import java.lang.management.ManagementFactory

private val THREADS = ManagementFactory.getThreadMXBean() as ThreadMXBean

@Volatile
private var sink: Any? = null                                     // results escape here, so nothing is optimized away

private fun bytes(work: () -> Unit): Long {
    val before = THREADS.currentThreadAllocatedBytes
    work()
    return THREADS.currentThreadAllocatedBytes - before
}

private fun show(what: String, work: () -> Unit) {
    val first = bytes(work)                                        // the first run also pays for one-time setup
    val second = bytes(work)
    println("%-34s %,10d %,11d".format(what, first, second))
}

/** Counts the bytes a few small pieces of code allocate, twice each, using the JVM's per-thread counter. */
fun main() {
    println("%-34s %10s %11s".format("bytes allocated by", "first run", "second run"))
    show("ByteArray(1 MiB)") { sink = ByteArray(1 shl 20) }
    show("1,000 x boxing (i % 128).toLong()") { for (i in 0 until 1_000) sink = (i % 128).toLong() }
    show("1,000 x boxing (1_000 + i).toLong()") { for (i in 0 until 1_000) sink = (1_000 + i).toLong() }
    show("1,000 x \"pay-\$i\"") { for (i in 0 until 1_000) sink = "pay-$i" }

    Thread.ofVirtual().start {
        println("on a virtual thread the counter says ${THREADS.currentThreadAllocatedBytes}")
    }.join()
}
