package workbench.memory.l01

import java.lang.management.BufferPoolMXBean
import java.lang.management.ManagementFactory
import java.lang.management.MemoryType
import java.nio.ByteBuffer

private const val MB = 1024L * 1024

/** Lists the memory areas this JVM reports, heap and non-heap, then adds a 64 MiB direct buffer. */
fun main() {
    println("max heap (-Xmx or its default): %,d MB".format(Runtime.getRuntime().maxMemory() / MB))
    for (pool in ManagementFactory.getMemoryPoolMXBeans()) {
        println("%-9s %-32s used %,6d KB  committed %,7d KB".format(
            if (pool.type == MemoryType.HEAP) "heap" else "non-heap",
            pool.name, pool.usage.used / 1024, pool.usage.committed / 1024))
    }
    println("live threads: ${ManagementFactory.getThreadMXBean().threadCount}, each with a stack outside the heap")

    val direct = ByteBuffer.allocateDirect((64 * MB).toInt())           // off-heap: not in any pool above
    ManagementFactory.getPlatformMXBeans(BufferPoolMXBean::class.java)
        .filter { it.name == "direct" }
        .forEach { println("direct buffers: %d, %,d MB, outside the heap".format(it.count, it.memoryUsed / MB)) }
    println("buffer capacity ${direct.capacity()}")
}
