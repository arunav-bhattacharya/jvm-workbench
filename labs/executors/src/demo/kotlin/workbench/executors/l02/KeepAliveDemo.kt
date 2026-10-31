package workbench.executors.l02

import java.util.concurrent.ArrayBlockingQueue
import java.util.concurrent.ThreadPoolExecutor
import java.util.concurrent.TimeUnit

/**
 * A pool grows to max under a burst, then shrinks back when threads sit idle longer than keepAlive.
 * Pass "core" to call allowCoreThreadTimeOut(true) as well.
 */
fun main(args: Array<String>) {
    val pool = ThreadPoolExecutor(2, 4, 300, TimeUnit.MILLISECONDS, ArrayBlockingQueue(2))
    if (args.firstOrNull() == "core") pool.allowCoreThreadTimeOut(true)

    println("before any task: threads=${pool.poolSize}")
    repeat(6) {
        pool.execute {
            try { Thread.sleep(200) } catch (e: InterruptedException) { Thread.currentThread().interrupt() }
        }
    }
    val t0 = System.nanoTime()
    for (tick in 0..8) {
        println("%4d ms: threads=%d active=%d queued=%d".format((System.nanoTime() - t0) / 1_000_000,
            pool.poolSize, pool.activeCount, pool.queue.size))
        Thread.sleep(150)
    }
    println("largest pool size seen: ${pool.largestPoolSize}")
    pool.shutdown()
}
