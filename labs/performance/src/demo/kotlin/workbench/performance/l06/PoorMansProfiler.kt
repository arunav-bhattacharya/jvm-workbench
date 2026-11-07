package workbench.performance.l06

import java.nio.file.Files
import java.nio.file.Path
import kotlin.concurrent.thread

// Kotlin twin of PoorMansProfiler.java: every 10 ms, take the stack of each worker thread with
// Thread.getStackTrace() and count it. Writes collapsed stacks to build/poor-man-kt.collapsed.
fun main() {
    val until = System.nanoTime() + 4_000_000_000L
    val work = thread { kHammer(2, until) }

    val stacks = HashMap<String, Long>()                       // "frame;frame;frame" -> samples
    while (work.isAlive) {
        Thread.sleep(10)
        for (t in Thread.getAllStackTraces().keys) {
            if (!t.name.startsWith("fees-")) continue
            val st = t.stackTrace                              // the JVM must pause t to walk its stack
            if (st.isEmpty()) continue
            val key = st.reversed().joinToString(";") { "${it.className}.${it.methodName}" }   // root first
            stacks.merge(key, 1L, Long::plus)
        }
    }
    val file = Path.of("build", "poor-man-kt.collapsed")
    Files.createDirectories(file.parent)
    Files.write(file, stacks.map { (k, v) -> "$k $v" })
    println("collapsed stacks written to ${file.toAbsolutePath()}")

    val self = stacks.entries.groupBy({ it.key.substringAfterLast(';') }, { it.value }).mapValues { it.value.sum() }
    val total = self.values.sum()
    println("$total samples; top frames:")
    self.entries.sortedByDescending { it.value }.take(6)
        .forEach { (frame, n) -> println("  %5.1f%%  %s".format(100.0 * n / total, frame)) }
}
