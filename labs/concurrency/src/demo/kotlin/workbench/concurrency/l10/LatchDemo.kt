package workbench.concurrency.l10

import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import kotlin.concurrent.thread

// A service warms three caches in parallel and opens for traffic when all three are loaded.
// Run with -Pargs=stuck to make one warm-up hang.
fun main(args: Array<String>) {
    val stuck = args.firstOrNull() == "stuck"
    val caches = listOf("bin-ranges" to 200L, "fx-rates" to 400L, "merchant-config" to if (stuck) 60_000L else 300L)
    val warmedUp = CountDownLatch(caches.size)
    val t0 = System.nanoTime()

    for ((name, ms) in caches) {
        thread(isDaemon = true, name = "warm-$name") {
            try {
                Thread.sleep(ms)                                       // pretend to load
                println("%5d ms  %s loaded".format((System.nanoTime() - t0) / 1_000_000, name))
            } catch (e: InterruptedException) {
                Thread.currentThread().interrupt()
            } finally {
                warmedUp.countDown()                                   // count down even if loading failed
            }
        }
    }

    val ready = warmedUp.await(2, TimeUnit.SECONDS)                   // never wait forever at startup
    println("%5d ms  ready=%s, count=%d".format((System.nanoTime() - t0) / 1_000_000, ready, warmedUp.count))

    // a latch is one-shot: once at zero, await() returns at once, forever
    if (ready) {
        warmedUp.countDown()
        println("after another countDown(): count=${warmedUp.count}, await returns at once: ${warmedUp.await(0, TimeUnit.MILLISECONDS)}")
    }
}
