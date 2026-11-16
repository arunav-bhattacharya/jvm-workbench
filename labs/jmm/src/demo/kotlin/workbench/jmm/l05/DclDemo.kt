package workbench.jmm.l05

import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.CountDownLatch
import java.util.concurrent.atomic.AtomicInteger
import kotlin.concurrent.thread

/** Eight threads ask a hand-written double-checked lazy for the same value at the same moment. Edit it and rerun. */
private class LazyCardTable(private val loads: AtomicInteger) {
    @Volatile private var table: Any? = null         // try: remove @Volatile

    fun get(): Any {
        val t = table                                // 1. fast path: one volatile read, no lock
        if (t != null) return t
        synchronized(this) {                         // 2. slow path: one thread at a time
            val again = table                        // 3. check again: another thread may have won
            if (again != null) return again          //    (try deleting this line)
            loads.incrementAndGet()
            Thread.sleep(50)                         // reading the card table from a big file
            val fresh = Any()
            table = fresh                            // 4. volatile write publishes the table
            return fresh
        }
    }
}

fun main() {
    for (round in 1..3) {
        val loads = AtomicInteger()
        val lazy = LazyCardTable(loads)
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
        println("round $round: table loaded ${loads.get()} time(s), threads saw ${seen.size} distinct table(s)")
    }
}
