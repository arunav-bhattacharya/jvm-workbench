package workbench.executors.l05

import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger

/** A 100 ms schedule whose second run takes 250 ms. Default: fixed rate. Pass "delay" for fixed delay. */
fun main(args: Array<String>) {
    val delay = args.firstOrNull() == "delay"
    val scheduler = Executors.newSingleThreadScheduledExecutor()
    val runs = AtomicInteger()
    val sevenRuns = CountDownLatch(7)
    val t0 = System.nanoTime()
    val sync = Runnable {
        val n = runs.incrementAndGet()
        val start = (System.nanoTime() - t0) / 1_000_000
        val work = if (n == 2) 250L else 10L               // run 2 hits a slow ledger
        try { Thread.sleep(work) } catch (e: InterruptedException) { Thread.currentThread().interrupt() }
        println("run %d started at %4d ms, took %3d ms".format(n, start, work))
        sevenRuns.countDown()
    }
    val f = if (delay) scheduler.scheduleWithFixedDelay(sync, 0, 100, TimeUnit.MILLISECONDS)
            else scheduler.scheduleAtFixedRate(sync, 0, 100, TimeUnit.MILLISECONDS)
    println(if (delay) "scheduleWithFixedDelay, 100 ms" else "scheduleAtFixedRate, 100 ms")
    sevenRuns.await()
    f.cancel(false)
    scheduler.shutdown()
}
