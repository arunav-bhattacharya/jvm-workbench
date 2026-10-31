package workbench.vthreads.l03

import java.util.concurrent.Executors
import java.util.concurrent.Semaphore
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger

/**
 * 1,000 requests arrive at once. The issuer allows 20 calls in flight, each takes 50 ms.
 * A request waits at most 200 ms for a slot, then gives up (a fast 503 instead of a slow timeout).
 *
 * Args: permits, call ms, max wait ms. Default: 20 50 200.
 */
fun main(args: Array<String>) {
    val permits = args.getOrNull(0)?.toInt() ?: 20
    val callMs = args.getOrNull(1)?.toLong() ?: 50
    val maxWaitMs = args.getOrNull(2)?.toLong() ?: 200

    val issuer = Semaphore(permits)
    val served = AtomicInteger()
    val shed = AtomicInteger()
    val t0 = System.nanoTime()
    Executors.newVirtualThreadPerTaskExecutor().use { perTask ->
        repeat(1_000) {
            perTask.execute {
                if (!issuer.tryAcquire(maxWaitMs, TimeUnit.MILLISECONDS)) {
                    shed.incrementAndGet()          // no slot in time: fail fast
                    return@execute
                }
                try {
                    Thread.sleep(callMs)            // the issuer call
                    served.incrementAndGet()
                } finally {
                    issuer.release()
                }
            }
        }
    }
    println("permits=%d call=%d ms max wait=%d ms: served %d, shed %d, in %d ms"
        .format(permits, callMs, maxWaitMs, served.get(), shed.get(), (System.nanoTime() - t0) / 1_000_000))
}
