package workbench.executors.l01

import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.atomic.LongAdder

private val work = LongAdder()

private fun task() {
    work.add(System.nanoTime().toString(16).length.toLong())    // a few nanoseconds of real work
}

/** 5,000 tiny tasks: one new thread per task, then the same tasks on a pool of 4 threads. */
fun main(args: Array<String>) {
    val tasks = args.firstOrNull()?.toInt() ?: 5_000
    for (round in 1..2) {
        // 1. a brand-new platform thread for every task
        var t0 = System.nanoTime()
        val done = CountDownLatch(tasks)
        repeat(tasks) {
            Thread { task(); done.countDown() }.start()
        }
        done.await()
        val perTask = (System.nanoTime() - t0) / 1_000_000

        // 2. the same tasks on four threads that are created once and reused
        t0 = System.nanoTime()
        Executors.newFixedThreadPool(4).use { pool ->
            repeat(tasks) { pool.execute(::task) }
        }   // close() waits for all of them
        val pooled = (System.nanoTime() - t0) / 1_000_000

        println("round %d: %,d tasks  new thread each: %,d ms  pool of 4: %,d ms".format(round, tasks, perTask, pooled))
    }
}
