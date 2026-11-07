package workbench.concurrency.l08

import java.util.concurrent.atomic.AtomicLong
import java.util.concurrent.atomic.LongAdder
import kotlin.concurrent.thread

// 8 threads each count 2,000,000 events: once on one AtomicLong, once on a LongAdder.
private fun time(perThreadWork: () -> Unit): Long {
    val t0 = System.nanoTime()
    List(8) { thread { perThreadWork() } }.forEach { it.join() }
    return (System.nanoTime() - t0) / 1_000_000
}

fun main() {
    val n = 2_000_000
    for (round in 1..3) {
        val atomic = AtomicLong()
        val adder = LongAdder()
        val a = time { repeat(n) { atomic.incrementAndGet() } }
        val b = time { repeat(n) { adder.increment() } }
        println("round %d: AtomicLong %,d in %4d ms   LongAdder %,d in %4d ms".format(round, atomic.get(), a, adder.sum(), b))
    }
}
