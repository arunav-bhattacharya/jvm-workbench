package workbench.memory.l02

import java.lang.management.ManagementFactory

/**
 * Counts the heap bytes the current thread allocates while it runs a block of code.
 *
 * HotSpot keeps an exact per-thread counter of allocated bytes. `com.sun.management.ThreadMXBean`
 * (a subtype of the standard `java.lang.management.ThreadMXBean`) exposes it as
 * `currentThreadAllocatedBytes`. On a virtual thread that property returns -1.
 */
object AllocationMeter {
    private val threads = ManagementFactory.getThreadMXBean() as com.sun.management.ThreadMXBean

    /**
     * Returns how many bytes [block] allocated on this thread: read the counter, run the block, read it again.
     * Throws [IllegalStateException] when the counter is not available (it returns -1 on a virtual thread).
     */
    fun bytesAllocatedBy(block: () -> Unit): Long {
        TODO("read threads.currentThreadAllocatedBytes before and after block(); fail on -1")
    }
}
