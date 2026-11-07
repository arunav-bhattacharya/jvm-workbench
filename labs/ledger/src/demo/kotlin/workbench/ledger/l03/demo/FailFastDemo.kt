package workbench.ledger.l03.demo

import java.util.concurrent.Callable
import java.util.concurrent.ExecutorCompletionService
import java.util.concurrent.Executors

private var t0 = 0L
private fun ms() = (System.nanoTime() - t0) / 1_000_000

// the slow check: answers after 500 ms, unless it is interrupted first
private fun fraudCheck(): Boolean {
    try {
        Thread.sleep(500)
        println("  %4d ms  fraud check answered".format(ms()))
        return true
    } catch (e: InterruptedException) {
        println("  %4d ms  fraud check interrupted".format(ms()))
        throw e
    }
}

// the fast check: says no after 10 ms
private fun limitsCheck(): Boolean {
    Thread.sleep(10)
    return false
}

/** One transfer, two checks. The limits check says no at 10 ms. When does the request get its answer? */
fun main() {
    println("in order: get() the fraud check, then the limits check")
    t0 = System.nanoTime()
    Executors.newVirtualThreadPerTaskExecutor().use { perTask ->
        val fraud = perTask.submit(Callable { fraudCheck() })
        val limits = perTask.submit(Callable { limitsCheck() })
        val verdict = if (fraud.get() && limits.get()) "approved" else "declined"
        println("  %4d ms  verdict: %s".format(ms(), verdict))
    }

    println("fail fast: take results as they finish, stop the rest at the first no")
    t0 = System.nanoTime()
    val perTask = Executors.newVirtualThreadPerTaskExecutor()
    try {
        val done = ExecutorCompletionService<Boolean>(perTask)
        done.submit { fraudCheck() }
        done.submit { limitsCheck() }
        var verdict = "approved"
        for (i in 1..2) {
            if (!done.take().get()) { verdict = "declined"; break }   // completion order, not submit order
        }
        println("  %4d ms  verdict: %s".format(ms(), verdict))
    } finally {
        perTask.shutdownNow()                        // interrupt the check nobody needs any more
        perTask.close()                              // and wait until its thread has ended
    }
}
