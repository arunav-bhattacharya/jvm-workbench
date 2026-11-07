package workbench.executors.l09

import java.util.concurrent.ExecutionException
import java.util.concurrent.Executors

/** Named threads with an UncaughtExceptionHandler. Which failures does the handler see? */
fun main() {
    val factory = Thread.ofPlatform()
        .name("ledger-", 0)                                               // ledger-0, ledger-1, ...
        .uncaughtExceptionHandler { t, e -> println("  handler: ${t.name} died of $e") }
        .factory()
    Executors.newFixedThreadPool(1, factory).use { pool ->
        println("1. execute() a task that throws")
        pool.execute { throw IllegalStateException("ledger row locked") }
        Thread.sleep(200)
        println("   the next task runs on " + pool.submit<String> { Thread.currentThread().name }.get())

        println("2. submit() a task that throws")
        val f = pool.submit<Unit> { throw IllegalStateException("negative amount") }
        Thread.sleep(200)
        println("   (nothing printed) the next task runs on " + pool.submit<String> { Thread.currentThread().name }.get())
        try {
            f.get()
        } catch (e: ExecutionException) {
            println("   only get() shows it: ${e.cause}")
        }
    }
}
