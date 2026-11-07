package workbench.patterns.l11

import java.util.concurrent.CountDownLatch
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger
import kotlin.concurrent.thread

// Balking: eight triggers fire at once, and the settlement run refuses to start while one is in progress.

class SettlementJob {
    private val running = AtomicBoolean()

    fun runIfIdle(settle: () -> Unit): Boolean {
        if (!running.compareAndSet(false, true)) return false          // balk: a run is already in progress
        try {
            settle()
            return true
        } finally {
            running.set(false)
        }
    }
}

fun main() {
    val job = SettlementJob()
    val inside = AtomicInteger()
    val mostAtOnce = AtomicInteger()
    val ran = AtomicInteger()
    val balked = AtomicInteger()
    val settle = {
        mostAtOnce.accumulateAndGet(inside.incrementAndGet(), ::maxOf)
        repeat(2_000_000) { Thread.onSpinWait() }                       // settling takes a moment
        inside.decrementAndGet()
        Unit
    }

    val go = CountDownLatch(1)
    val triggers = List(8) {                                            // the scheduler, a retry, an operator's button...
        thread {
            go.await()
            if (job.runIfIdle(settle)) ran.incrementAndGet() else balked.incrementAndGet()
        }
    }
    go.countDown()
    triggers.forEach { it.join() }
    println("ran $ran, balked $balked, most runs at once: $mostAtOnce")
}
