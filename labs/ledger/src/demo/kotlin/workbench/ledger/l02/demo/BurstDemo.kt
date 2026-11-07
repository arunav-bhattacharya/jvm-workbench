package workbench.ledger.l02.demo

import java.util.concurrent.ArrayBlockingQueue
import java.util.concurrent.RejectedExecutionException
import java.util.concurrent.RejectedExecutionHandler
import java.util.concurrent.ThreadPoolExecutor
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger

/**
 * A burst of 300 transfers hits a pool sized with Little's law: 8 threads, 80 queue slots, 5 ms
 * per transfer. Pass "callerRuns" to swap the counting abort policy for CallerRunsPolicy.
 */
fun main(args: Array<String>) {
    val callerRuns = args.firstOrNull() == "callerRuns"
    val rejected = AtomicInteger()
    val policy: RejectedExecutionHandler =
        if (callerRuns) ThreadPoolExecutor.CallerRunsPolicy()           // the submitting thread runs it itself
        else RejectedExecutionHandler { _, _ ->                         // count it, then throw at the caller
            rejected.incrementAndGet()
            throw RejectedExecutionException("ledger pool full")
        }
    val pool = ThreadPoolExecutor(8, 8, 0, TimeUnit.MILLISECONDS,
        ArrayBlockingQueue(80), Thread.ofPlatform().name("ledger-", 0).factory(), policy)
    pool.prestartAllCoreThreads()
    val ranOnCaller = AtomicInteger()
    val caller = Thread.currentThread().name
    val t0 = System.nanoTime()
    var accepted = 0
    repeat(300) {
        try {
            pool.execute {
                if (Thread.currentThread().name == caller) ranOnCaller.incrementAndGet()
                Thread.sleep(5)                                         // the journal write
            }
            accepted++
        } catch (e: RejectedExecutionException) {
            // an HTTP handler would answer 503 with Retry-After here
        }
    }
    val submitMs = (System.nanoTime() - t0) / 1_000_000
    pool.shutdown()
    pool.awaitTermination(10, TimeUnit.SECONDS)
    val doneMs = (System.nanoTime() - t0) / 1_000_000
    println("%s: accepted %d, rejected %d, run by the submitting thread %d"
        .format(if (callerRuns) "CallerRunsPolicy" else "counting abort", accepted, rejected.get(), ranOnCaller.get()))
    println("submitting took $submitMs ms, all done after $doneMs ms")
}
