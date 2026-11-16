package workbench.executors.l09

import java.util.concurrent.CompletableFuture
import java.util.concurrent.Executors
import java.util.concurrent.ThreadPoolExecutor
import java.util.concurrent.TimeUnit
import java.util.concurrent.TimeoutException

private fun fetchLines(table: String) = listOf("$table-1", "$table-2")   // fast: the problem isn't speed

/** Two bill tasks on a 2-thread pool, each waiting for a fetch on the same pool. Pass "fixed" to compose instead. */
fun main(args: Array<String>) {
    val fixed = args.firstOrNull() == "fixed"
    val pool = Executors.newFixedThreadPool(2, Thread.ofPlatform().name("bills-", 0).factory())
    try {
        if (fixed) {
            val bills = listOf("t1", "t2").map { t ->
                CompletableFuture.supplyAsync({ fetchLines(t) }, pool)
                    .thenApply { lines -> "$t: ${lines.size} lines" }       // nobody waits inside the pool
            }
            bills.forEach { println(it.join()) }
            return
        }
        val bills = listOf("t1", "t2").map { t ->
            pool.submit<String> {
                val lines = pool.submit<List<String>> { fetchLines(t) }    // queued behind us
                "$t: ${lines.get().size} lines"                           // waits for it
            }
        }
        Thread.sleep(300)
        val tpe = pool as ThreadPoolExecutor
        println("after 300 ms: active=${tpe.activeCount}, queued=${tpe.queue.size}, completed=${tpe.completedTaskCount}")
        try {
            println(bills[0].get(2, TimeUnit.SECONDS))
        } catch (e: TimeoutException) {
            println("no bill after 2 s: both threads wait for fetches that can never start")
        }
    } finally {
        pool.shutdownNow()                                                // interrupts the stuck get() calls
    }
}
