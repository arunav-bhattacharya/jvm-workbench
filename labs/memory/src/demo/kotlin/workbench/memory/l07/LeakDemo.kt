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

class KCachedThumbnail(val uploadId: String, val createdAtMillis: Long, val format: String, val pixels: ByteArray)

private val FORMATS = listOf("image/jpeg", "image/png")                         // another GC root
private val THUMBNAILS = ConcurrentHashMap<String, KCachedThumbnail>()          // never evicted

private fun handle(uploadId: String) {
    THUMBNAILS.computeIfAbsent(uploadId) { id -> KCachedThumbnail(id, System.currentTimeMillis(), FORMATS[0], ByteArray(2_048)) }
}

// the same as: jcmd <pid> GC.class_histogram
private fun histogram(): String = ManagementFactory.getPlatformMBeanServer().invoke(
    ObjectName("com.sun.management:type=DiagnosticCommand"), "gcClassHistogram",
    arrayOf<Any?>(null), arrayOf(Array<String>::class.java.name)) as String

// the histogram's last line: Total <objects> <bytes>
private fun liveBytes(): Long = histogram().trim().lines().last().trim().split(Regex("\\s+"))[2].toLong()

/**
 * A thumbnail service whose cache never forgets, run twice in child JVMs: once to print a class
 * histogram, write a heap dump and measure what the cache keeps alive, once with -Xmx64m until it
 * runs out of memory.
 */
fun main(args: Array<String>) {
    val dumps = Files.createDirectories(Path.of("build", "heapdumps"))          // labs/memory/build/heapdumps
    if (args.isEmpty()) {
        println("== 20,000 uploads, then a class histogram and a heap dump")
        Jvm.run(listOf("-Xmx256m"), "workbench.memory.l07.LeakDemoKt", "histogram")
        dumps.resolve("oom.hprof").deleteIfExists()
        println("== -Xmx64m -XX:+HeapDumpOnOutOfMemoryError, uploads until the heap is full")
        Jvm.lines(listOf("-Xmx64m", "-XX:+HeapDumpOnOutOfMemoryError", "-XX:HeapDumpPath=${dumps.resolve("oom.hprof")}"),
            "workbench.memory.l07.LeakDemoKt", "forever")
            .filterNot { it.startsWith("\tat ") }.forEach(::println)
        return
    }
    if (args[0] == "forever") {
        while (true) handle(UUID.randomUUID().toString())
    }
    repeat(20_000) { handle(UUID.randomUUID().toString()) }
    histogram().lines().take(7).forEach(::println)                               // the header and the top five classes
    val dump = dumps.resolve("leak.hprof")
    dump.deleteIfExists()
    ManagementFactory.getPlatformMXBean(HotSpotDiagnosticMXBean::class.java).dumpHeap(dump.toString(), true)   // live objects only
    println("heap dump: %s, %,d bytes".format(dump.toAbsolutePath(), dump.fileSize()))
    val withCache = liveBytes()
    THUMBNAILS.clear()                                                           // drop every note the cache holds
    val without = liveBytes()
    println("live heap %,d bytes with the cache full, %,d after clear(): it kept %,d bytes alive".format(withCache, without, withCache - without))
}
