package workbench.executors.l01

import java.util.concurrent.Executors
import java.util.concurrent.RejectedExecutionException
import java.util.concurrent.TimeUnit

private val T0 = System.nanoTime()

private fun log(msg: String) = println("%5d ms  %s".format((System.nanoTime() - T0) / 1_000_000, msg))

private fun cook(id: Int) = Runnable {
    try {
        Thread.sleep(300)                       // 300 ms to cook one order
        log("cooked order $id")
    } catch (e: InterruptedException) {
        log("order $id interrupted")
        Thread.currentThread().interrupt()
    }
}

/** shutdown, awaitTermination and shutdownNow on a kitchen of 2 cooks (threads) with 6 orders of 300 ms each. */
fun main(args: Array<String>) {
    val now = args.firstOrNull() == "now"
    val pool = Executors.newFixedThreadPool(2)
    for (i in 1..6) pool.execute(cook(i))

    if (now) {
        Thread.sleep(100)
        val neverStarted = pool.shutdownNow()
        log("shutdownNow returned ${neverStarted.size} tasks that never started")
    } else {
        pool.shutdown()
        log("shutdown returned. isShutdown=${pool.isShutdown} isTerminated=${pool.isTerminated}")
    }

    try {
        pool.execute(cook(7))
    } catch (e: RejectedExecutionException) {
        log("order 7 rejected: the kitchen is closed")
    }

    val done = pool.awaitTermination(5, TimeUnit.SECONDS)
    log("awaitTermination returned $done. isTerminated=${pool.isTerminated}")
}
