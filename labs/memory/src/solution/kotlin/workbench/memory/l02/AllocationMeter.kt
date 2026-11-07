package workbench.memory.l02

import java.lang.management.ManagementFactory

object AllocationMeter {
    private val threads = ManagementFactory.getThreadMXBean() as com.sun.management.ThreadMXBean

    fun bytesAllocatedBy(block: () -> Unit): Long {
        val before = threads.currentThreadAllocatedBytes
        // -1: a virtual thread, or measurement switched off. A wrong number is worse than none.
        check(before >= 0) { "allocation counter not available on ${Thread.currentThread()}: measure on a platform thread" }
        block()
        return threads.currentThreadAllocatedBytes - before   // exact bytes, headers and padding included
    }
}
