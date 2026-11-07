package workbench.concurrency.l08

import java.util.concurrent.CountDownLatch
import java.util.concurrent.atomic.AtomicLong
import kotlin.concurrent.thread

// A hand-written compare-and-set increment. Count how often the CAS fails as threads are added.
private val counter = AtomicLong()

// returns how many times compareAndSet failed before it worked
private fun increment(): Long {
    var failures = 0L
    while (true) {
        val seen = counter.get()                               // 1. read
        if (counter.compareAndSet(seen, seen + 1)) {           // 2. write only if still `seen`
            return failures
        }
        failures++                                             // 3. someone else won: retry
    }
}

fun main() {
    val perThread = 1_000_000
    for (threads in listOf(1, 2, 4, 8)) {
        counter.set(0)
        val failed = AtomicLong()
        val go = CountDownLatch(1)                             // start them all together
        val ts = List(threads) {
            thread {
                go.await()
                var mine = 0L
                repeat(perThread) { mine += increment() }
                failed.addAndGet(mine)
            }
        }
        go.countDown()
        ts.forEach { it.join() }
        println("threads: %d  counter: %,10d  failed CAS: %,10d  (%.2f per increment)"
            .format(threads, counter.get(), failed.get(), failed.get() / counter.get().toDouble()))
    }
}
