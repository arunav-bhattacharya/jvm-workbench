package workbench.performance.l03

// WordCountBench.java measures with JMH, which needs Java classes in this lab. This Kotlin twin runs
// the same two word counts written in Kotlin and reads the JVM's per-thread allocation counter
// around 100,000 calls: the same bytes-per-call idea as JMH's gc.alloc.rate.norm.
// Allocation is steady enough to count this way. Time is not (remember NanoLoop).
import java.lang.management.ManagementFactory

private val lines = Array(100) { "the report counts every word on line number $it" }

fun wordsBySplit(): Long {
    var total = 0L
    for (line in lines) total += line.split(' ').size   // Kotlin's split returns a List of new Strings
    return total
}

fun wordsByScan(): Long {
    var total = 0L
    for (line in lines) {
        var inWord = false
        for (c in line) {
            val letter = c != ' '
            if (letter && !inWord) total++
            inWord = letter
        }
    }
    return total
}

private val threads = ManagementFactory.getThreadMXBean() as com.sun.management.ThreadMXBean
private var sink = 0L                                    // results go somewhere the JIT can't ignore

private inline fun bytesPerCall(calls: Int, block: () -> Long): Double {
    repeat(50_000) { sink += block() }                   // warm up first, so C2 code is measured
    val before = threads.currentThreadAllocatedBytes
    repeat(calls) { sink += block() }
    return (threads.currentThreadAllocatedBytes - before).toDouble() / calls
}

fun main() {
    val split = bytesPerCall(100_000) { wordsBySplit() }
    val scan = bytesPerCall(100_000) { wordsByScan() }
    println("wordsBySplit: %10.3f B/op".format(split))
    println("wordsByScan:  %10.3f B/op".format(scan))
    println("(checksum $sink)")
}
