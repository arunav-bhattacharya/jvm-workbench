package workbench.executors.l09

import java.util.concurrent.CompletableFuture
import java.util.concurrent.Executors
import java.util.concurrent.ThreadPoolExecutor
import java.util.concurrent.TimeUnit
import java.util.concurrent.TimeoutException

private fun fetchLines(merchant: String) = listOf("$merchant-1", "$merchant-2")   // fast: the problem isn't speed

/** Two statement tasks on a 2-thread pool, each waiting for a fetch on the same pool. Pass "fixed" to compose instead. */
fun main(args: Array<String>) {
    val fixed = args.firstOrNull() == "fixed"
    val pool = Executors.newFixedThreadPool(2, Thread.ofPlatform().name("stmt-", 0).factory())
    try {
        if (fixed) {
            val statements = listOf("m1", "m2").map { m ->
                CompletableFuture.supplyAsync({ fetchLines(m) }, pool)
                    .thenApply { lines -> "$m: ${lines.size} lines" }       // nobody waits inside the pool
            }
            statements.forEach { println(it.join()) }
            return
        }
        val statements = listOf("m1", "m2").map { m ->
            pool.submit<String> {
                val lines = pool.submit<List<String>> { fetchLines(m) }    // queued behind us
                "$m: ${lines.get().size} lines"                           // waits for it
            }
        }
        Thread.sleep(300)
        val tpe = pool as ThreadPoolExecutor
        println("after 300 ms: active=${tpe.activeCount}, queued=${tpe.queue.size}, completed=${tpe.completedTaskCount}")
        try {
            println(statements[0].get(2, TimeUnit.SECONDS))
        } catch (e: TimeoutException) {
            println("no statement after 2 s: both threads wait for fetches that can never start")
        }
    } finally {
        pool.shutdownNow()                                                // interrupts the stuck get() calls
    }
}
