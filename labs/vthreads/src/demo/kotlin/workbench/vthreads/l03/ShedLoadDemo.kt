package workbench.vthreads.l03

import java.util.concurrent.Executors
import java.util.concurrent.Semaphore
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger

/**
 * 1,000 requests arrive at once. The database allows 20 calls at once, each takes 50 ms.
 * A request waits at most 200 ms for a permit, then gives up (a fast "busy, try again" instead of a slow timeout).
 *
 * Args: permits, call ms, max wait ms. Default: 20 50 200.
 */
fun main(args: Array<String>) {
    val permits = args.getOrNull(0)?.toInt() ?: 20
    val callMs = args.getOrNull(1)?.toLong() ?: 50
    val maxWaitMs = args.getOrNull(2)?.toLong() ?: 200

    val db = Semaphore(permits)
    val served = AtomicInteger()
    val shed = AtomicInteger()
    val t0 = System.nanoTime()
    Executors.newVirtualThreadPerTaskExecutor().use { perTask ->
        repeat(1_000) {
            perTask.execute {
                if (!db.tryAcquire(maxWaitMs, TimeUnit.MILLISECONDS)) {
                    shed.incrementAndGet()          // no permit in time: fail fast
                    return@execute
                }
                try {
                    Thread.sleep(callMs)            // the database call
                    served.incrementAndGet()
                } finally {
                    db.release()
                }
            }
        }
    }
    println("permits=%d call=%d ms max wait=%d ms: served %d, shed %d, in %d ms"
        .format(permits, callMs, maxWaitMs, served.get(), shed.get(), (System.nanoTime() - t0) / 1_000_000))
}
