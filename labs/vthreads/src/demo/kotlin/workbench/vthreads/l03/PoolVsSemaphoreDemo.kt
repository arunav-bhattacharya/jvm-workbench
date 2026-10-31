package workbench.vthreads.l03

import java.util.concurrent.Executors
import java.util.concurrent.Semaphore

/**
 * Each request calls the fraud service (60 ms, no limit) and then the ledger database
 * (10 ms, at most 20 at once). Two ways to respect the database limit:
 * a pool of 20 virtual threads, or one virtual thread per request plus a Semaphore(20).
 */
private const val REQUESTS = 1_000
private const val DB_LIMIT = 20

fun main() {
    // A: the anti-pattern. The pool size limits the database, and also everything else.
    val t0 = System.nanoTime()
    Executors.newFixedThreadPool(DB_LIMIT, Thread.ofVirtual().factory()).use { pool ->
        repeat(REQUESTS) {
            pool.execute {
                Thread.sleep(60)                    // fraud check: needs no limit
                Thread.sleep(10)                    // ledger write: needs the limit
            }
        }
    }
    println("pool of %d virtual threads:        %,5d ms".format(DB_LIMIT, (System.nanoTime() - t0) / 1_000_000))

    // B: one virtual thread per request; the semaphore guards only the database call
    val db = Semaphore(DB_LIMIT)
    val t1 = System.nanoTime()
    Executors.newVirtualThreadPerTaskExecutor().use { perTask ->
        repeat(REQUESTS) {
            perTask.execute {
                Thread.sleep(60)                    // all 1,000 fraud checks overlap
                db.acquire()                        // at most 20 inside the database
                try {
                    Thread.sleep(10)
                } finally {
                    db.release()
                }
            }
        }
    }
    println("virtual thread per task + Semaphore(%d): %,5d ms".format(DB_LIMIT, (System.nanoTime() - t1) / 1_000_000))
}
