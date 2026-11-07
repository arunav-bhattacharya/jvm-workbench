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

// native segments are counted, and limited, together with direct ByteBuffers
fun directBytes(): Long = ManagementFactory.getPlatformMXBeans(BufferPoolMXBean::class.java)
    .filter { it.name == "direct" }
    .sumOf { it.memoryUsed }

fun main(args: Array<String>) {                                        // args unused; one main keeps every launcher happy
    val before = directBytes()                                            // the JDK may already hold a little
    val escaped: MemorySegment
    Arena.ofConfined().use { arena ->                                     // 1. one owner thread, closed by use {}
        val ledger = arena.allocate(32L * 1024 * 1024)                     // 2. 32 MiB outside the heap
        for (i in 0 until ledger.byteSize() / Long.SIZE_BYTES) {
            ledger.setAtIndex(ValueLayout.JAVA_LONG, i, i * 100)           //    4 million longs, and no objects
        }
        println("entry 1,000 holds ${ledger.getAtIndex(ValueLayout.JAVA_LONG, 1_000)}")
        println("inside the arena: %+d MiB of direct memory".format((directBytes() - before) shr 20))
        escaped = ledger
    }                                                                     // 3. freed here, not by the GC
    println("after close():    %+d MiB of direct memory".format((directBytes() - before) shr 20))
    try {
        escaped.getAtIndex(ValueLayout.JAVA_LONG, 0)                      // 4. use after free is an exception, not a crash
    } catch (e: IllegalStateException) {
        println("reading after close() throws: ${e.message}")
    }
}
