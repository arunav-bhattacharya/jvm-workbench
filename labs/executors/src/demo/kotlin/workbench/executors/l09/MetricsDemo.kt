package workbench.executors.l09

import java.util.concurrent.ArrayBlockingQueue
import java.util.concurrent.RejectedExecutionException
import java.util.concurrent.ThreadPoolExecutor
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.LongAdder

/** 10 tasks of 300 ms hit a pool of 2 threads with a queue of 4. Watch the numbers a dashboard would show. */
fun main() {
    val rejected = LongAdder()
    val pool = ThreadPoolExecutor(2, 2, 0, TimeUnit.MILLISECONDS, ArrayBlockingQueue(4),
        Thread.ofPlatform().name("auth-", 0).factory()) { _, _ ->
        rejected.increment()                                              // count it, then fail like AbortPolicy
        throw RejectedExecutionException("auth pool full")
    }

    repeat(10) {
        try {
            pool.execute { Thread.sleep(300) }
        } catch (e: RejectedExecutionException) {
            // the caller would answer 503 here
        }
    }
    println("  ms  threads  active  queued  done  rejected")
    val t0 = System.nanoTime()
    repeat(6) {
        println("%4d  %7d  %6d  %6d  %4d  %8d".format((System.nanoTime() - t0) / 1_000_000,
            pool.poolSize, pool.activeCount, pool.queue.size, pool.completedTaskCount, rejected.sum()))
        Thread.sleep(200)
    }
    pool.shutdown()
    pool.awaitTermination(5, TimeUnit.SECONDS)
}
