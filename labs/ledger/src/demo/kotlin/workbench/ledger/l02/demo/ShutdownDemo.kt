package workbench.ledger.l02.demo

import java.util.concurrent.ArrayBlockingQueue
import java.util.concurrent.Callable
import java.util.concurrent.FutureTask
import java.util.concurrent.ThreadPoolExecutor
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger

private data class QueuedTransfer(val id: Int)

// a FutureTask that remembers its transfer, so the queue hands back transfers, not anonymous Runnables
private class QueuedTask(val transfer: QueuedTransfer, work: Callable<Boolean>) : FutureTask<Boolean>(work)

/**
 * 1,000 transfers wait on 8 threads at 5 ms each, then the service stops. Where does each one end up?
 * Args: "naive" or "drain" (the default), then the grace period in ms (default 100).
 */
fun main(args: Array<String>) {
    val mode = args.getOrElse(0) { "drain" }
    val graceMs = args.getOrNull(1)?.toLong() ?: 100
    val pool = ThreadPoolExecutor(8, 8, 0, TimeUnit.MILLISECONDS,
        ArrayBlockingQueue(1_000), Thread.ofPlatform().name("ledger-", 0).factory())
    val applied = AtomicInteger()
    val interrupted = AtomicInteger()
    val accepted = (0 until 1_000).map { i ->
        QueuedTask(QueuedTransfer(i)) {
            try {
                Thread.sleep(5)                               // the journal write
            } catch (e: InterruptedException) {
                interrupted.incrementAndGet()                 // not journaled, so not applied
                throw e
            }
            applied.incrementAndGet()
            true
        }.also { pool.execute(it) }
    }
    var handedBack = 0
    if (mode == "naive") {
        pool.shutdownNow()                                    // the list of queued tasks it returns is dropped
    } else {
        pool.shutdown()                                       // 1. no new work; the queue keeps draining
        if (!pool.awaitTermination(graceMs, TimeUnit.MILLISECONDS)) {
            val neverStarted = pool.shutdownNow()             // 2. interrupt, take back the queue
            neverStarted.forEach { (it as QueuedTask).cancel(false) }   // 3. wake anyone waiting on them
            handedBack = neverStarted.size                    // 4. log these ids, or replay them on restart
        }
    }
    pool.awaitTermination(5, TimeUnit.SECONDS)
    val neverComplete = accepted.count { !it.isDone }
    println("%s, grace %d ms: accepted 1,000 | applied %,d | interrupted %d | handed back %,d | lost %,d".format(
        mode, graceMs, applied.get(), interrupted.get(), handedBack, 1_000 - applied.get() - interrupted.get() - handedBack))
    println("futures that will never complete: %,d".format(neverComplete))
}
