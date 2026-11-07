package workbench.vthreads.l05

import java.util.concurrent.Callable
import java.util.concurrent.ExecutionException
import java.util.concurrent.Executors

/**
 * A quote handler fans out two calls: a slow CRM lookup (2 s) and a credit-limit check
 * that fails after 100 ms. Watch what happens to the slow call once the request has failed.
 */
@Volatile
private var t0 = 0L

private fun log(what: String) = println("%,7d ms  %s".format((System.nanoTime() - t0) / 1_000_000, what))

private fun customer(): String = try {
    Thread.sleep(2_000)                                         // the slow CRM call
    log("customer: call finished, nobody needs the result")
    "ACME Ltd"
} catch (e: InterruptedException) {
    log("customer: interrupted, stopped early")
    throw e
}

private fun limit(): String {
    Thread.sleep(100)
    throw IllegalStateException("credit limit service: 503")
}

// A: an executor per request, closed by use {}
private fun quoteA(): String =
    Executors.newVirtualThreadPerTaskExecutor().use { perTask ->
        val customer = perTask.submit(Callable { customer() })
        val limit = perTask.submit(Callable { limit() })
        limit.get() + " " + customer.get()                      // throws at 100 ms...
    }                                                           // ...but close() waits for the CRM call

private val shared = Executors.newVirtualThreadPerTaskExecutor()

// B: one long-lived executor for the whole service
private fun quoteB(): String {
    val customer = shared.submit(Callable { customer() })
    val limit = shared.submit(Callable { limit() })
    return limit.get() + " " + customer.get()                   // throws at 100 ms, and returns
}

fun main() {
    println("A: executor per request, closed by use {}")
    t0 = System.nanoTime()
    try {
        quoteA()
    } catch (e: ExecutionException) {
        log("request failed: ${e.cause?.message}")
    }

    println("B: one shared executor")
    t0 = System.nanoTime()
    try {
        quoteB()
    } catch (e: ExecutionException) {
        log("request failed: ${e.cause?.message}")
    }
    Thread.sleep(2_500)                                         // stay alive to see what B left behind
    shared.close()
}
