package workbench.executors.l02

import java.util.concurrent.ArrayBlockingQueue
import java.util.concurrent.RejectedExecutionException
import java.util.concurrent.ThreadPoolExecutor
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicLong

val rejectedAuths = AtomicLong()

// Java constructors take no named arguments in Kotlin, so the comments do that job.
fun authPool(): ThreadPoolExecutor = ThreadPoolExecutor(
    4, 8,                               // core, max
    30, TimeUnit.SECONDS,               // keep-alive for threads above core
    ArrayBlockingQueue(16),             // Runnable is inferred from the parameter type
) { _, pool ->                          // RejectedExecutionHandler, written as a trailing lambda
    rejectedAuths.incrementAndGet()
    throw RejectedExecutionException("rejected: queued=${pool.queue.size}")
}.apply { prestartAllCoreThreads() }

fun main() {
    val pool = authPool()
    println("threads before any task: ${pool.poolSize}")
    pool.shutdown()
}
