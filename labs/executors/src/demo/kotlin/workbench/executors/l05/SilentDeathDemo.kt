package workbench.executors.l05

import java.util.concurrent.ExecutionException
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger

/** A health check every 100 ms that throws on its third run. Pass "safe" to catch inside the task. */
fun main(args: Array<String>) {
    val safe = args.firstOrNull() == "safe"
    val scheduler = Executors.newSingleThreadScheduledExecutor()
    val runs = AtomicInteger()
    val check = Runnable {
        val n = runs.incrementAndGet()
        println("health check $n")
        if (n == 3) throw IllegalStateException("ledger ping timed out")
    }
    val task = if (!safe) check else Runnable {
        try {
            check.run()
        } catch (e: RuntimeException) {
            println("  caught and logged: ${e.message}")
        }
    }
    val f = scheduler.scheduleAtFixedRate(task, 0, 100, TimeUnit.MILLISECONDS)

    Thread.sleep(1_000)                                    // ten periods
    println("after 1 s: runs=${runs.get()} isDone=${f.isDone}")
    if (f.isDone) {
        try {
            f.get()
        } catch (e: ExecutionException) {
            println("get() threw ExecutionException, cause: ${e.cause}")
        }
    }
    scheduler.shutdownNow()
}
