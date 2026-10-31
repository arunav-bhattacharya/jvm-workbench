package workbench.vthreads.l02

import java.util.TreeSet

/**
 * Starts some virtual threads that each print the thread they run on, sleep, and print it again.
 * A virtual thread's toString() shows its carrier after the '@'.
 *
 * Args: number of virtual threads (default 8), and optionally the scheduler's parallelism.
 */
fun main(args: Array<String>) {
    val n = args.getOrNull(0)?.toInt() ?: 8
    // must be set before the first virtual thread is created
    args.getOrNull(1)?.let { System.setProperty("jdk.virtualThreadScheduler.parallelism", it) }

    val before = arrayOfNulls<String>(n)
    val after = arrayOfNulls<String>(n)
    val t0 = System.nanoTime()
    val threads = (0 until n).map { id ->
        Thread.ofVirtual().name("payment-$id").start {
            before[id] = Thread.currentThread().toString()
            try {
                Thread.sleep(50)                 // a blocking call: the thread unmounts here
            } catch (e: InterruptedException) {
                Thread.currentThread().interrupt()
            }
            after[id] = Thread.currentThread().toString()
        }
    }
    threads.forEach { it.join() }
    val ms = (System.nanoTime() - t0) / 1_000_000

    val carriers = TreeSet<String>()
    var moved = 0
    for (i in 0 until n) {
        println("before: %-63s after: %s".format(before[i], after[i]))
        carriers += carrierOf(before[i]!!)
        carriers += carrierOf(after[i]!!)
        if (carrierOf(before[i]!!) != carrierOf(after[i]!!)) moved++
    }
    println("\n$n virtual threads ran on ${carriers.size} carrier threads $carriers (this machine has ${Runtime.getRuntime().availableProcessors()} cores).")
    println("$moved of them woke up on a different carrier than the one they slept on.")
    println("All $n finished after $ms ms.")
    println("Thread.currentThread().isVirtual() inside them: ${threads[0].isVirtual}, daemon: ${threads[0].isDaemon}")
}

// "VirtualThread[#22,payment-0]/runnable@ForkJoinPool-1-worker-3" -> "ForkJoinPool-1-worker-3"
private fun carrierOf(s: String): String {
    val at = s.lastIndexOf('@')
    return if (at < 0) "(not mounted)" else s.substring(at + 1)
}
