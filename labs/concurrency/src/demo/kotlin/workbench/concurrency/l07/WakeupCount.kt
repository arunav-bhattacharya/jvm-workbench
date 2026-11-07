package workbench.concurrency.l07

import java.util.concurrent.locks.Condition
import java.util.concurrent.locks.ReentrantLock
import kotlin.concurrent.thread
import kotlin.concurrent.withLock

// 4 producers and 4 consumers move 20,000 items through a one-slot buffer, twice:
// once with one Condition and signalAll(), once with notFull/notEmpty and signal().
// A wake-up is "wasted" when the thread wakes, re-checks, and has to wait again.
private class CountingBuffer(private val shared: Boolean) {
    private val lock = ReentrantLock()
    private val notFull: Condition = lock.newCondition()
    private val notEmpty: Condition = if (shared) notFull else lock.newCondition()   // same queue, or two
    private val items = ArrayDeque<Int>()
    var wasted = 0L                                           // guarded by lock
        private set

    fun put(x: Int) = lock.withLock {
        while (items.size == 1) {
            notFull.await()
            if (items.size == 1) wasted++                     // woke up for nothing
        }
        items.addLast(x)
        if (shared) notEmpty.signalAll() else notEmpty.signal()
    }

    fun take(): Int = lock.withLock {
        while (items.isEmpty()) {
            notEmpty.await()
            if (items.isEmpty()) wasted++
        }
        val x = items.removeFirst()
        if (shared) notFull.signalAll() else notFull.signal()
        x
    }
}

fun main() {
    for (one in listOf(true, false)) {
        val buffer = CountingBuffer(one)
        val t0 = System.nanoTime()
        val threads = (1..4).flatMap {
            listOf(
                thread { repeat(5_000) { n -> buffer.put(n) } },
                thread { repeat(5_000) { buffer.take() } },
            )
        }
        threads.forEach { it.join() }
        val label = if (one) "one condition, signalAll():" else "notFull + notEmpty, signal():"
        println("%-34s wasted wake-ups: %,9d   (%d ms)".format(label, buffer.wasted, (System.nanoTime() - t0) / 1_000_000))
    }
}
