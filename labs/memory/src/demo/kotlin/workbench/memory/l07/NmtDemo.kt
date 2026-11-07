package workbench.memory.l07

import workbench.memory.Jvm
import java.lang.management.ManagementFactory
import java.nio.ByteBuffer
import java.util.concurrent.CountDownLatch
import javax.management.ObjectName
import kotlin.concurrent.thread

private val CATEGORY = Regex("""^-?\s*(Total|[A-Z][\w ]+?):? \(?reserved=(\d+)MB, committed=(\d+)MB""")

// the same as: jcmd <pid> VM.native_memory summary scale=MB
private fun nativeMemory(): String = ManagementFactory.getPlatformMBeanServer().invoke(
    ObjectName("com.sun.management:type=DiagnosticCommand"), "vmNativeMemory",
    arrayOf<Any>(arrayOf("summary", "scale=MB")), arrayOf(Array<String>::class.java.name)) as String

private fun printNmt(title: String) {
    println(title)
    nativeMemory().lines().mapNotNull { CATEGORY.find(it) }.forEach { m ->
        val (name, reserved, committed) = m.destructured
        println("  %-20s committed %,5d MB  (reserved %,5d MB)".format(name, committed.toLong(), reserved.toLong()))
    }
}

/**
 * Native Memory Tracking from inside a child JVM: the summary before and after a 64 MiB direct buffer
 * and 100 extra threads. Then a direct buffer that doesn't fit under -XX:MaxDirectMemorySize.
 */
fun main(args: Array<String>) {
    if (args.isEmpty()) {
        Jvm.run(listOf("-Xmx256m", "-XX:NativeMemoryTracking=summary"), "workbench.memory.l07.NmtDemoKt", "track")
        Jvm.run(listOf("-Xmx256m", "-XX:MaxDirectMemorySize=32m"), "workbench.memory.l07.NmtDemoKt", "limit")
        return
    }
    if (args[0] == "limit") {
        try {
            ByteBuffer.allocateDirect(64 * 1024 * 1024)
        } catch (e: OutOfMemoryError) {
            println("with -XX:MaxDirectMemorySize=32m: $e")
        }
        return
    }
    printNmt("at startup")
    val direct = ByteBuffer.allocateDirect(64 * 1024 * 1024)               // what Netty does for socket buffers
    val never = CountDownLatch(1)
    repeat(100) { thread(isDaemon = true) { try { never.await() } catch (e: InterruptedException) { } } }
    printNmt("after a 64 MiB direct buffer and 100 more threads")
    println("buffer ${direct.capacity()}")
}
