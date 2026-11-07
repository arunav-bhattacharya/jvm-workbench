package workbench.ledger.l02.demo

import java.util.concurrent.ArrayBlockingQueue
import java.util.concurrent.Callable
import java.util.concurrent.ExecutorService
import java.util.concurrent.ThreadPoolExecutor
import java.util.concurrent.TimeUnit

/**
 * Month-end statements on the ledger pool: each statement task asks the same 2-thread pool for a
 * balance and waits for the answer. Run it, then take a thread dump while it hangs.
 * Arg: how many seconds to stay hung (default 4).
 */
fun main(args: Array<String>) {
    val seconds = args.firstOrNull()?.toInt() ?: 4
    val pool = ThreadPoolExecutor(2, 2, 0, TimeUnit.MILLISECONDS,
        ArrayBlockingQueue(100), Thread.ofPlatform().name("ledger-", 0).factory())
    for (merchant in listOf("m-001", "m-002", "m-003")) {
        pool.submit(Callable { statement(pool, merchant) })
    }
    val pid = ProcessHandle.current().pid()
    println("pid $pid, hanging for $seconds s. In another terminal: jcmd $pid Thread.print -l")
    Thread.sleep(seconds * 1_000L)
    println("after $seconds s: active=${pool.activeCount}, queued=${pool.queue.size}, completed=${pool.completedTaskCount}")
    pool.shutdownNow()                                        // interrupts the two get() calls that will never return
}

private fun statement(pool: ExecutorService, merchant: String): String {
    val balance = pool.submit(Callable { balanceOf(merchant) })   // queued behind the other statements
    return "$merchant: ${balance.get()}"                           // waits for a thread that is never free
}

private fun balanceOf(merchant: String): Long = 4_200                // fast: the problem is not speed
