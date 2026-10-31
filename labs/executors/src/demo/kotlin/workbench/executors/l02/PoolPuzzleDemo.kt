package workbench.executors.l02

import java.util.concurrent.ArrayBlockingQueue
import java.util.concurrent.LinkedBlockingQueue
import java.util.concurrent.RejectedExecutionException
import java.util.concurrent.SynchronousQueue
import java.util.concurrent.ThreadPoolExecutor
import java.util.concurrent.TimeUnit

/**
 * Seven 500 ms tasks into ThreadPoolExecutor(2, 4, ...). Where does each one go?
 * Args: queue (bounded | unbounded | handoff) and policy (abort | caller | discard | oldest).
 */
fun main(args: Array<String>) {
    val queueKind = args.getOrElse(0) { "bounded" }
    val policyKind = args.getOrElse(1) { "abort" }
    val queue = when (queueKind) {
        "unbounded" -> LinkedBlockingQueue<Runnable>()
        "handoff" -> SynchronousQueue<Runnable>()
        else -> ArrayBlockingQueue<Runnable>(2)
    }
    val policy = when (policyKind) {
        "caller" -> ThreadPoolExecutor.CallerRunsPolicy()
        "discard" -> ThreadPoolExecutor.DiscardPolicy()
        "oldest" -> ThreadPoolExecutor.DiscardOldestPolicy()
        else -> ThreadPoolExecutor.AbortPolicy()
    }
    val pool = ThreadPoolExecutor(2, 4, 60, TimeUnit.SECONDS, queue, policy)
    println("core=2 max=4 queue=$queueKind policy=$policyKind")

    val t0 = System.nanoTime()
    for (id in 1..7) {
        val task = Runnable {
            try { Thread.sleep(500) } catch (e: InterruptedException) { Thread.currentThread().interrupt() }
            println("    task $id done on ${Thread.currentThread().name}")
        }
        try {
            pool.execute(task)
            println("task $id accepted: threads=${pool.poolSize} queued=${pool.queue.size}")
        } catch (e: RejectedExecutionException) {
            println("task $id REJECTED: threads=${pool.poolSize} queued=${pool.queue.size}")
        }
    }
    pool.shutdown()
    pool.awaitTermination(10, TimeUnit.SECONDS)
    println("all done in ${(System.nanoTime() - t0) / 1_000_000} ms, completed tasks: ${pool.completedTaskCount}")
}
