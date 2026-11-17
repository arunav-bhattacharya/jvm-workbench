package workbench.performance.l08

import java.lang.management.ManagementFactory

// The "cpu=" column of a thread dump, read from inside the process: which platform threads used CPU in the last interval?
data class Hot(val name: String, val cpuNanos: Long)

fun hottest(millis: Long, n: Int): List<Hot> {
    val mx = ManagementFactory.getThreadMXBean()
    val before = mx.allThreadIds.associateWith { mx.getThreadCpuTime(it) }      // platform threads only
    Thread.sleep(millis)
    return mx.allThreadIds.toList().mapNotNull { id ->
        val then = before[id] ?: return@mapNotNull null
        val now = mx.getThreadCpuTime(id)                                       // -1 once a thread has died
        val name = mx.getThreadInfo(id)?.threadName ?: return@mapNotNull null
        if (now > then) Hot(name, now - then) else null
    }.sortedByDescending { it.cpuNanos }.take(n)
}

fun main() {
    Thread.ofPlatform().daemon().name("index-rebuild").start {
        var x = 1L
        while (true) x = x * 31 + 7
    }
    for (h in hottest(500, 3)) println("%-20s %6.1f ms".format(h.name, h.cpuNanos / 1e6))
}
