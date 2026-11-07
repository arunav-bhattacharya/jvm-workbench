package workbench.memory.l06

import workbench.memory.Jvm
import java.lang.management.BufferPoolMXBean
import java.lang.management.ManagementFactory
import java.nio.ByteBuffer
import java.nio.file.Path
import java.util.concurrent.CountDownLatch
import kotlin.concurrent.thread
import kotlin.io.path.exists
import kotlin.io.path.readLines

private const val MB = 1024L * 1024

/**
 * A child JVM with -Xmx256m that does what services do: a 64 MiB direct buffer (think Netty) and 50
 * threads. It then compares what the JVM reports with what the operating system says it uses.
 */
fun main(args: Array<String>) {
    if (args.isEmpty()) {
        // AlwaysPreTouch touches every heap page at startup, like a service that has run for a while
        Jvm.run(listOf("-Xmx256m", "-Xms256m", "-XX:+AlwaysPreTouch"), "workbench.memory.l06.FootprintDemoKt", "child")
        return
    }
    val direct = ByteBuffer.allocateDirect((64 * MB).toInt())
    val never = CountDownLatch(1)
    repeat(50) { thread(isDaemon = true) { try { never.await() } catch (e: InterruptedException) { } } }
    val memory = ManagementFactory.getMemoryMXBean()
    val directBytes = ManagementFactory.getPlatformMXBeans(BufferPoolMXBean::class.java)
        .filter { it.name == "direct" }.sumOf { it.memoryUsed }
    println("heap committed      %,5d MB  (-Xmx256m)".format(memory.heapMemoryUsage.committed / MB))
    println("non-heap committed  %,5d MB  (metaspace, class space, code cache)".format(memory.nonHeapMemoryUsage.committed / MB))
    println("direct buffers      %,5d MB".format(directBytes / MB))
    println("live threads        %,5d     (each with its own stack)".format(ManagementFactory.getThreadMXBean().threadCount))
    val status = Path.of("/proc/self/status")
    if (status.exists()) {                                          // Linux only
        status.readLines().filter { it.startsWith("VmRSS") }.forEach {
            println("resident in RAM     %,5d MB  (what the container limit counts)".format(it.filter(Char::isDigit).toLong() / 1024))
        }
    } else {
        println("resident in RAM     not available here (/proc is Linux only)")
    }
    println("buffer ${direct.capacity()}")
}
