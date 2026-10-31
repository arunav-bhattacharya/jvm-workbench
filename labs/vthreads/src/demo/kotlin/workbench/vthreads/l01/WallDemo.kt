package workbench.vthreads.l01

import java.time.Duration
import java.util.concurrent.Executors

/**
 * Runs N fake "authorize a payment" requests that each block for a while,
 * first on a fixed pool, then with one virtual thread per request.
 *
 * Args: pool size, number of requests, latency in ms. Default: 100 2000 100.
 */
fun main(args: Array<String>) {
    val poolSize = args.getOrNull(0)?.toInt() ?: 100
    val requests = args.getOrNull(1)?.toInt() ?: 2_000
    val latency = Duration.ofMillis(args.getOrNull(2)?.toLong() ?: 100)

    val authorize = Runnable {
        try {
            Thread.sleep(latency)              // stands in for the card issuer call
        } catch (e: InterruptedException) {
            Thread.currentThread().interrupt()
        }
    }

    val t0 = System.nanoTime()
    Executors.newFixedThreadPool(poolSize).use { pool ->
        repeat(requests) { pool.execute(authorize) }
    }                                          // use {} = try-with-resources: close() waits
    report("fixed pool of $poolSize", requests, t0)

    val t1 = System.nanoTime()
    Executors.newVirtualThreadPerTaskExecutor().use { perTask ->
        repeat(requests) { perTask.execute(authorize) }
    }
    report("virtual thread per task", requests, t1)
}

private fun report(label: String, requests: Int, startNanos: Long) {
    val ms = (System.nanoTime() - startNanos) / 1_000_000
    println("%-26s %,6d requests in %,6d ms  = %,8.0f requests/s".format(label, requests, ms, requests * 1000.0 / maxOf(ms, 1)))
}
