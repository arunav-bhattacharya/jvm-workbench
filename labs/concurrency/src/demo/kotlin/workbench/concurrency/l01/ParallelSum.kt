package workbench.concurrency.l01

private const val N = 400_000_000

// Splits a CPU-bound job over 1, 2, 4 and 8 threads and times each run.
fun main() {
    println("cores: ${Runtime.getRuntime().availableProcessors()}")
    repeat(3) { timed(4) }                          // warm-up runs, so the JIT has compiled the loop
    for (threads in intArrayOf(1, 2, 4, 8)) {
        val t0 = System.nanoTime()
        val result = timed(threads)
        println("%d thread(s): %4d ms  (checksum %d)".format(threads, (System.nanoTime() - t0) / 1_000_000, result))
    }
}

private fun timed(threads: Int): Long {
    val partial = LongArray(threads)
    val chunk = N / threads
    val workers = List(threads) { w ->
        val from = w * chunk
        val to = if (w == threads - 1) N else from + chunk
        Thread {
            var sum = 0L
            for (i in from until to) sum += (i * 31L) % 7   // pure CPU work
            partial[w] = sum
        }.apply { start() }
    }
    workers.forEach { it.join() }
    return partial.sum()
}
