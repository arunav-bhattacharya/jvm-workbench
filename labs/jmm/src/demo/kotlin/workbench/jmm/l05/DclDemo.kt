package workbench.jmm.l05

import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.CountDownLatch
import java.util.concurrent.atomic.AtomicInteger
import kotlin.concurrent.thread

/** Eight threads ask a hand-written double-checked lazy for the same value at the same moment. Edit it and rerun. */
private class LazySigningKey(private val loads: AtomicInteger) {
    @Volatile private var key: Any? = null           // try: remove @Volatile

    fun get(): Any {
        val k = key                                  // 1. fast path: one volatile read, no lock
        if (k != null) return k
        synchronized(this) {                         // 2. slow path: one thread at a time
            val again = key                          // 3. check again: another thread may have won
            if (again != null) return again          //    (try deleting this line)
            loads.incrementAndGet()
            Thread.sleep(50)                         // fetching a signing key from a vault
            val fresh = Any()
            key = fresh                              // 4. volatile write publishes the key
            return fresh
        }
    }
}

fun main() {
    for (round in 1..3) {
        val loads = AtomicInteger()
        val lazy = LazySigningKey(loads)
        val seen = ConcurrentHashMap.newKeySet<Any>()
        val ready = CountDownLatch(8)
        val go = CountDownLatch(1)
        val threads = List(8) {
            thread {
                ready.countDown()
                go.await()
                seen += lazy.get()
            }
        }
        ready.await()
        go.countDown()
        threads.forEach { it.join() }
        println("round $round: key loaded ${loads.get()} time(s), threads saw ${seen.size} distinct key(s)")
    }
}
