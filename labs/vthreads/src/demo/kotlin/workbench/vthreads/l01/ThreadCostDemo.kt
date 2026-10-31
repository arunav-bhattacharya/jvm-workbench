package workbench.vthreads.l01

import java.util.concurrent.CountDownLatch

/**
 * Starts N threads that all block on one latch, so they exist at the same time,
 * then releases them. First with platform threads, then with virtual threads.
 *
 * Args: platform count, virtual count. Default: 4000 100000.
 * Keep the platform count at 5,000 or below on a laptop.
 */
fun main(args: Array<String>) {
    val platform = args.getOrNull(0)?.toInt() ?: 4_000
    val virtual = args.getOrNull(1)?.toInt() ?: 100_000
    startAndRelease("platform", platform, Thread.ofPlatform())
    startAndRelease("virtual", virtual, Thread.ofVirtual())
}

private fun startAndRelease(kind: String, n: Int, builder: Thread.Builder) {
    val release = CountDownLatch(1)
    val t0 = System.nanoTime()
    val threads = List(n) {
        builder.start {
            try {
                release.await()                // every thread stays alive until we let go
            } catch (e: InterruptedException) {
                Thread.currentThread().interrupt()
            }
        }
    }
    val startedMs = (System.nanoTime() - t0) / 1_000_000
    release.countDown()
    threads.forEach { it.join() }
    val totalMs = (System.nanoTime() - t0) / 1_000_000
    println("%-8s %,7d threads alive at once: started in %,5d ms, all finished after %,5d ms (%.1f us per thread)"
        .format(kind, n, startedMs, totalMs, totalMs * 1000.0 / n))
}
