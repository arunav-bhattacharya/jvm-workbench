package workbench.jmm.l02

import kotlin.concurrent.thread

private var total = 0L   // written by the worker, read by main

/** main starts a worker that adds up merchant settlements, then sleeps and reads the total. */
fun main() {
    val worker = thread {
        var sum = 0L
        for (merchant in 0 until 20) {
            sum += fetchSettlement(merchant)   // each call takes about 10 ms
        }
        total = sum
    }

    Thread.sleep(50)   // "plenty of time"
    println("after sleep(50): total = %,d (expected %,d)".format(total, 20 * 100_000L))
}

// stands in for a call to the settlement service for one merchant
private fun fetchSettlement(@Suppress("UNUSED_PARAMETER") merchant: Int): Long {
    Thread.sleep(10)
    return 100_000
}
