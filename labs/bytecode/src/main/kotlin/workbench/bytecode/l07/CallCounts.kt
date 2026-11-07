package workbench.bytecode.l07

import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.atomic.AtomicLong

/**
 * Call counts by method name, such as `"workbench.bytecode.l07.SettlementJob.settle"`.
 * Public on purpose: the advice code is copied INTO the instrumented class, and from there it
 * calls [hit], so this class must be visible to that class.
 */
object CallCounts {
    private val counts = ConcurrentHashMap<String, AtomicLong>()

    @JvmStatic
    fun hit(method: String) {
        counts.computeIfAbsent(method) { AtomicLong() }.incrementAndGet()
    }

    @JvmStatic
    fun of(method: String): Long = counts[method]?.get() ?: 0

    @JvmStatic
    fun reset() = counts.clear()
}
