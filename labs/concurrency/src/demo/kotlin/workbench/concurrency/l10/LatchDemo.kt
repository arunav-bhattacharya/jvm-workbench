package workbench.concurrency.l10

import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import kotlin.concurrent.thread

// A shop's program loads three lists in parallel and opens its doors when all three are loaded.
// Run with -Pargs=sleep to open after a fixed 250 ms nap instead, or -Pargs=stuck to make one load hang.
fun main(args: Array<String>) {
    val mode = args.firstOrNull() ?: "latch"
    val lists = listOf("price list" to 200L, "stock counts" to 400L, "today's offers" to if (mode == "stuck") 60_000L else 300L)
    val loaded = CountDownLatch(lists.size)
    val t0 = System.nanoTime()

    for ((i, list) in lists.withIndex()) {
        val (name, ms) = list
        thread(isDaemon = true, name = "load-$i") {
            try {
                Thread.sleep(ms)                                       // pretend to load
                println("%5d ms  %s loaded".format((System.nanoTime() - t0) / 1_000_000, name))
            } catch (e: InterruptedException) {
                Thread.currentThread().interrupt()
            } finally {
                loaded.countDown()                                     // count down even if loading failed
            }
        }
    }

    if (mode == "sleep") {                                             // Naive: a guess about how long loading takes
        Thread.sleep(250)
        println("%5d ms  doors open after a 250 ms nap, lists still loading: %d"
            .format((System.nanoTime() - t0) / 1_000_000, loaded.count))
        return
    }

    val ready = loaded.await(2, TimeUnit.SECONDS)                      // never wait forever at startup
    println("%5d ms  ready=%s, count=%d".format((System.nanoTime() - t0) / 1_000_000, ready, loaded.count))

    // a latch is one-shot: once at zero, await() returns at once, forever
    if (ready) {
        loaded.countDown()
        println("after another countDown(): count=${loaded.count}, await returns at once: ${loaded.await(0, TimeUnit.MILLISECONDS)}")
    }
}
