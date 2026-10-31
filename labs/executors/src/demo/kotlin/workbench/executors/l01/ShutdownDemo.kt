package workbench.executors.l01

import java.util.concurrent.Executors
import java.util.concurrent.RejectedExecutionException
import java.util.concurrent.TimeUnit

private val T0 = System.nanoTime()

private fun log(msg: String) = println("%5d ms  %s".format((System.nanoTime() - T0) / 1_000_000, msg))

private fun settle(id: Int) = Runnable {
    try {
        Thread.sleep(300)                       // a 300 ms call to the ledger
        log("settled batch $id")
    } catch (e: InterruptedException) {
        log("batch $id interrupted")
        Thread.currentThread().interrupt()
    }
}

/** shutdown, awaitTermination and shutdownNow on a pool of 2 threads with 6 queued 300 ms tasks. */
fun main(args: Array<String>) {
    val now = args.firstOrNull() == "now"
    val pool = Executors.newFixedThreadPool(2)
    for (i in 1..6) pool.execute(settle(i))

    if (now) {
        Thread.sleep(100)
        val neverStarted = pool.shutdownNow()
        log("shutdownNow returned ${neverStarted.size} tasks that never started")
    } else {
        pool.shutdown()
        log("shutdown returned. isShutdown=${pool.isShutdown} isTerminated=${pool.isTerminated}")
    }

    try {
        pool.execute(settle(7))
    } catch (e: RejectedExecutionException) {
        log("batch 7 rejected: the pool is shut down")
    }

    val done = pool.awaitTermination(5, TimeUnit.SECONDS)
    log("awaitTermination returned $done. isTerminated=${pool.isTerminated}")
}
