package workbench.concurrency.l12

import java.lang.management.ManagementFactory
import java.util.concurrent.Semaphore
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.locks.ReentrantLock
import kotlin.concurrent.thread
import kotlin.concurrent.withLock

// Five philosophers, five forks, 200 meals each. Run as is (left fork, then right),
// with -Pargs=ordered (lower-numbered fork first) or -Pargs=waiter (at most 4 may sit down).
fun main(args: Array<String>) {
    val mode = args.firstOrNull() ?: "naive"
    val n = 5
    val forks = Array(n) { ReentrantLock() }
    val seats = Semaphore(n - 1)                                     // the waiter: one chair short
    val meals = AtomicInteger()

    val ps = List(n) { i ->
        val left = i
        val right = (i + 1) % n
        val first = if (mode == "ordered") minOf(left, right) else left
        val second = if (mode == "ordered") maxOf(left, right) else right
        thread(isDaemon = true, name = "philosopher-$i") {
            repeat(200) {
                if (mode == "waiter") seats.acquire()
                try {
                    forks[first].withLock {
                        Thread.sleep(1)                              // reach for the other fork
                        forks[second].withLock { meals.incrementAndGet() }
                    }
                } finally {
                    if (mode == "waiter") seats.release()
                }
            }
        }
    }
    val t0 = System.nanoTime()
    val deadline = t0 + 3_000_000_000L                               // 3 s for the whole table
    ps.forEach { it.join(maxOf(1L, (deadline - System.nanoTime()) / 1_000_000)) }
    val stuck = ManagementFactory.getThreadMXBean().findDeadlockedThreads()
    println("%s: %d of 1,000 meals in %d ms, deadlocked philosophers: %d"
        .format(mode, meals.get(), (System.nanoTime() - t0) / 1_000_000, stuck?.size ?: 0))
}
