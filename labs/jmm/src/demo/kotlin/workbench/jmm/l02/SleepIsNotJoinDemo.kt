package workbench.jmm.l02

import kotlin.concurrent.thread

private var total = 0L   // written by the worker, read by main

/** main starts a worker that adds up the day's sales of 20 shops, then sleeps and reads the total. */
fun main() {
    val worker = thread {
        var sum = 0L
        for (shop in 0 until 20) {
            sum += fetchShopTotal(shop)   // each call takes about 10 ms
        }
        total = sum
    }

    Thread.sleep(50)   // "plenty of time"
    println("after sleep(50): total = %,d (expected %,d)".format(total, 20 * 100_000L))
}

// stands in for a slow call that fetches one shop's total for the day
private fun fetchShopTotal(@Suppress("UNUSED_PARAMETER") shop: Int): Long {
    Thread.sleep(10)
    return 100_000
}
