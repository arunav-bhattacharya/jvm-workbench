package workbench.memory.l07

import com.sun.management.HotSpotDiagnosticMXBean
import workbench.memory.Jvm
import java.lang.management.ManagementFactory
import java.nio.file.Files
import java.nio.file.Path
import java.util.UUID
import java.util.concurrent.ConcurrentHashMap
import javax.management.ObjectName
import kotlin.io.path.deleteIfExists
import kotlin.io.path.fileSize

class KCachedResponse(val requestId: String, val amountMinor: Long, val receipt: ByteArray)

private val IDEMPOTENCY_CACHE = ConcurrentHashMap<String, KCachedResponse>()     // never evicted

private fun handle(requestId: String) {
    IDEMPOTENCY_CACHE.computeIfAbsent(requestId) { id -> KCachedResponse(id, 1_999, ByteArray(2_048)) }
}

/**
 * A service with an unbounded idempotency cache, run twice in child JVMs: once to print a class
 * histogram and write a heap dump, once with -Xmx64m until it runs out of memory.
 */
fun main(args: Array<String>) {
    val dumps = Files.createDirectories(Path.of("build", "heapdumps"))          // labs/memory/build/heapdumps
    if (args.isEmpty()) {
        println("== 20,000 requests, then a class histogram and a heap dump")
        Jvm.run(listOf("-Xmx256m"), "workbench.memory.l07.LeakDemoKt", "histogram")
        dumps.resolve("oom.hprof").deleteIfExists()
        println("== -Xmx64m -XX:+HeapDumpOnOutOfMemoryError, requests until the heap is full")
        Jvm.lines(listOf("-Xmx64m", "-XX:+HeapDumpOnOutOfMemoryError", "-XX:HeapDumpPath=${dumps.resolve("oom.hprof")}"),
            "workbench.memory.l07.LeakDemoKt", "forever")
            .filterNot { it.startsWith("\tat ") }.forEach(::println)
        return
    }
    if (args[0] == "forever") {
        while (true) handle(UUID.randomUUID().toString())
    }
    repeat(20_000) { handle(UUID.randomUUID().toString()) }
    val histogram = ManagementFactory.getPlatformMBeanServer().invoke(
        ObjectName("com.sun.management:type=DiagnosticCommand"), "gcClassHistogram",
        arrayOf<Any?>(null), arrayOf(Array<String>::class.java.name)) as String
    histogram.lines().take(7).forEach(::println)                                 // the header and the top five classes
    val dump = dumps.resolve("leak.hprof")
    dump.deleteIfExists()
    ManagementFactory.getPlatformMXBean(HotSpotDiagnosticMXBean::class.java).dumpHeap(dump.toString(), true)   // live objects only
    println("heap dump: %s, %,d bytes".format(dump.toAbsolutePath(), dump.fileSize()))
}
