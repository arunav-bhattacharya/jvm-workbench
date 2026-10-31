package workbench.executors.l03

import java.util.concurrent.Executors
import java.util.concurrent.Semaphore

/**
 * 200 requests that each wait 50 ms on a downstream call, on pools of 5, 10, 20 and 40 threads.
 * Little's law predicts throughput = threads / 0.05 s. Pass "db" to make every request also hold
 * one of only 10 database connections while it waits.
 */
fun main(args: Array<String>) {
    val db = args.firstOrNull() == "db"
    val connections = Semaphore(10)                     // a 10-connection pool, when "db" is on
    val requests = 200
    val latencySeconds = 0.050
    for (threads in listOf(5, 10, 20, 40)) {
        val t0 = System.nanoTime()
        Executors.newFixedThreadPool(threads).use { pool ->
            repeat(requests) {
                pool.execute {
                    try {
                        if (db) connections.acquire()
                        try {
                            Thread.sleep(50)            // the downstream call
                        } finally {
                            if (db) connections.release()
                        }
                    } catch (e: InterruptedException) {
                        Thread.currentThread().interrupt()
                    }
                }
            }
        }
        val seconds = (System.nanoTime() - t0) / 1e9
        println("%2d threads: %4.0f req/s measured, %4.0f predicted by threads / W".format(
            threads, requests / seconds, threads / latencySeconds))
    }
}
