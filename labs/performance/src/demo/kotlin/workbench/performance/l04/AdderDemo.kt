package workbench.performance.l04

import java.util.concurrent.CountDownLatch
import java.util.concurrent.atomic.AtomicLong
import java.util.concurrent.atomic.LongAdder
import kotlin.concurrent.thread

// Kotlin twin of AdderDemo.java: four threads count 10 million requests each,
// into one AtomicLong and then into one LongAdder.

private const val THREADS = 4
private const val PER_THREAD = 10_000_000

private fun timeAll(perThread: () -> Unit): Long {
    val go = CountDownLatch(1)
    val ts = List(THREADS) { thread { go.await(); perThread() } }
    val t0 = System.nanoTime()
    go.countDown()
    ts.forEach { it.join() }
    return (System.nanoTime() - t0) / 1_000_000
}

fun main() {
    for (round in 1..3) {
        val atomic = AtomicLong()
        val msAtomic = timeAll { repeat(PER_THREAD) { atomic.incrementAndGet() } }
        val adder = LongAdder()
        val msAdder = timeAll { repeat(PER_THREAD) { adder.increment() } }
        println("round %d: AtomicLong %,5d ms (%,d)   LongAdder %,5d ms (%,d)"
            .format(round, msAtomic, atomic.get(), msAdder, adder.sum()))
    }
}
