package workbench.concurrency.l13

import java.util.concurrent.CountDownLatch
import kotlin.concurrent.thread

// The same racy counter, tested twice: the way most tests are written, and the way that finds the bug.
private class RacyCounter {
    @Volatile var count = 0                       // @Volatile only stops the JIT from hiding the race (lesson 3)
    fun hit() { count++ }                         // the bug: read, add, write
}

// 2 threads, 1,000 hits each, no start line
private fun naiveRound(): Boolean {
    val c = RacyCounter()
    val a = thread { repeat(1_000) { c.hit() } }
    val b = thread { repeat(1_000) { c.hit() } }
    a.join(); b.join()
    return c.count == 2_000
}

// 8 threads, 100,000 hits each, released together
private fun stressRound(): Boolean {
    val c = RacyCounter()
    val go = CountDownLatch(1)
    val ts = List(8) { thread { go.await(); repeat(100_000) { c.hit() } } }
    go.countDown()
    ts.forEach { it.join() }
    return c.count == 800_000
}

fun main() {
    val naiveFailed = (1..20).count { !naiveRound() }
    val stressFailed = (1..20).count { !stressRound() }
    println("naive test  (2 threads x 1,000, no start line): failed $naiveFailed of 20 runs")
    println("stress test (8 threads x 100,000, start latch): failed $stressFailed of 20 runs")
}
