// JDK 22 or later: the Foreign Function and Memory API is final since JDK 22 (JEP 454). Written for JDK 25.
// Needs the Kotlin command-line compiler. From labs/:
//     kotlinc memory/jdk25/ArenaDemo.kt -include-runtime -d memory/build/arena-demo.jar
//     java -XX:NativeMemoryTracking=summary -jar memory/build/arena-demo.jar
//     java -XX:MaxDirectMemorySize=16m -jar memory/build/arena-demo.jar
// Not part of the Gradle build, because the labs compile for JDK 21, where this API is a preview.

import java.lang.foreign.Arena
import java.lang.foreign.MemorySegment
import java.lang.foreign.ValueLayout
import java.lang.management.BufferPoolMXBean
import java.lang.management.ManagementFactory
import javax.management.ObjectName

// Native Memory Tracking's "Other" row, where arena memory shows up (the same as jcmd <pid> VM.native_memory summary)
fun nativeOther(): String {
    val summary = ManagementFactory.getPlatformMBeanServer().invoke(
        ObjectName("com.sun.management:type=DiagnosticCommand"), "vmNativeMemory",
        arrayOf<Any>(arrayOf("summary", "scale=MB")), arrayOf(Array<String>::class.java.name)) as String
    if ("Total" !in summary) return "(start java with -XX:NativeMemoryTracking=summary to see it)"
    return summary.lines().firstOrNull { " Other (" in it }?.trim()?.removePrefix("-")?.trim() ?: "Other: under 1 MB, so NMT leaves it out"
}

// what the JDK counts against -XX:MaxDirectMemorySize: direct ByteBuffers and automatic arenas
fun directBytes(): Long = ManagementFactory.getPlatformMXBeans(BufferPoolMXBean::class.java)
    .filter { it.name == "direct" }
    .sumOf { it.memoryUsed }

fun main(args: Array<String>) {                                        // args unused; one main keeps every launcher happy
    val escaped: MemorySegment
    Arena.ofConfined().use { arena ->                                     // 1. one owner thread, closed by use {}
        val block = arena.allocate(32L * 1024 * 1024)                      // 2. 32 MiB outside the heap
        for (i in 0 until block.byteSize() / Long.SIZE_BYTES) {
            block.setAtIndex(ValueLayout.JAVA_LONG, i, i * 100)            //    4 million longs, and no objects
        }
        println("entry 1,000 holds ${block.getAtIndex(ValueLayout.JAVA_LONG, 1_000)}")
        println("inside the arena:  ${nativeOther()}")
        escaped = block
    }                                                                     // 3. freed here, not by the GC
    println("after close():     ${nativeOther()}")
    try {
        escaped.getAtIndex(ValueLayout.JAVA_LONG, 0)                      // 4. use after free is an exception, not a crash
    } catch (e: IllegalStateException) {
        println("reading after close() throws: ${e.message}")
    }

    val auto = Arena.ofAuto().allocate(32L * 1024 * 1024)                 // 5. freed only after the GC finds it unreachable,
    println("an automatic arena: %d MiB counted as direct memory".format(directBytes() shr 20))   //    so it counts with direct buffers
    println("segment ${auto.byteSize()}")
}
