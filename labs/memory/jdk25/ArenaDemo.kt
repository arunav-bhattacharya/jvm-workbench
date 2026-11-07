// JDK 22 or later: the Foreign Function and Memory API is final since JDK 22 (JEP 454). Written for JDK 25.
// Needs the Kotlin command-line compiler. From labs/:
//     kotlinc memory/jdk25/ArenaDemo.kt -include-runtime -d memory/build/arena-demo.jar
//     java -jar memory/build/arena-demo.jar
//     java -XX:MaxDirectMemorySize=16m -jar memory/build/arena-demo.jar
// Not part of the Gradle build, because the labs compile for JDK 21, where this API is a preview.

import java.lang.foreign.Arena
import java.lang.foreign.MemorySegment
import java.lang.foreign.ValueLayout
import java.lang.management.BufferPoolMXBean
import java.lang.management.ManagementFactory

// native segments count against the same limit as direct ByteBuffers
fun direct(): String = ManagementFactory.getPlatformMXBeans(BufferPoolMXBean::class.java)
    .firstOrNull { it.name == "direct" }
    ?.let { "${it.count} direct allocation(s), ${it.memoryUsed shr 20} MiB" } ?: "?"

fun main() {
    val escaped: MemorySegment
    Arena.ofConfined().use { arena ->                                     // 1. one owner thread, closed by use {}
        val ledger = arena.allocate(32L * 1024 * 1024)                     // 2. 32 MiB outside the heap
        for (i in 0 until ledger.byteSize() / Long.SIZE_BYTES) {
            ledger.setAtIndex(ValueLayout.JAVA_LONG, i, i * 100)           //    4 million longs, and no objects
        }
        println("entry 1,000 holds ${ledger.getAtIndex(ValueLayout.JAVA_LONG, 1_000)}")
        println("inside the arena: ${direct()}")
        escaped = ledger
    }                                                                     // 3. freed here, not by the GC
    println("after close():    ${direct()}")
    try {
        escaped.getAtIndex(ValueLayout.JAVA_LONG, 0)                      // 4. use after free is an exception, not a crash
    } catch (e: IllegalStateException) {
        println("reading after close() throws: ${e.message}")
    }
}
