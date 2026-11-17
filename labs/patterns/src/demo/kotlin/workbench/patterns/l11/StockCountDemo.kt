package workbench.patterns.l11

import java.util.concurrent.CountDownLatch
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger
import kotlin.concurrent.thread

// Balking: eight triggers fire at once, and the stock count refuses to start while one is already running.

class StockCount {
    private val running = AtomicBoolean()

    fun runIfIdle(count: () -> Unit): Boolean {
        if (!running.compareAndSet(false, true)) return false          // balk: a count is already running
        try {
            count()
            return true
        } finally {
            running.set(false)
        }
    }
}

fun main() {
    val stockCount = StockCount()
    val inside = AtomicInteger()
    val mostAtOnce = AtomicInteger()
    val ran = AtomicInteger()
    val balked = AtomicInteger()
    val count = {
        mostAtOnce.accumulateAndGet(inside.incrementAndGet(), ::maxOf)
        repeat(2_000_000) { Thread.onSpinWait() }                       // counting the shelves takes a moment
        inside.decrementAndGet()
        Unit
    }

    val go = CountDownLatch(1)
    val triggers = List(8) {                                            // the closing-time timer, the manager's button, a retry...
        thread {
            go.await()
            if (stockCount.runIfIdle(count)) ran.incrementAndGet() else balked.incrementAndGet()
        }
    }
    go.countDown()
    triggers.forEach { it.join() }
    println("ran $ran, balked $balked, most counts at once: $mostAtOnce")
}
