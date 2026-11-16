package workbench.vthreads.l05

import java.util.concurrent.Callable
import java.util.concurrent.ExecutionException
import java.util.concurrent.Executors

/**
 * A checkout asks two services at the same time: the bank, which takes 2 s on a bad day,
 * and the stock service, which says "sold out" after 100 ms. Once the stock check has failed,
 * the bank's answer is useless. Watch what happens to the bank call anyway.
 */
@Volatile
private var t0 = 0L

private fun log(what: String) = println("%,7d ms  %s".format((System.nanoTime() - t0) / 1_000_000, what))

private fun bank(): String = try {
    Thread.sleep(2_000)                                         // the bank, on a bad day
    log("bank: answered, but nobody needs the answer")
    "approved"
} catch (e: InterruptedException) {
    log("bank: interrupted, stopped early")
    throw e
}

private fun stock(): String {
    Thread.sleep(100)
    throw IllegalStateException("stock service: sold out")
}

// A: an executor per checkout, closed by use {}
private fun checkoutA(): String =
    Executors.newVirtualThreadPerTaskExecutor().use { perTask ->
        val bank = perTask.submit(Callable { bank() })
        val stock = perTask.submit(Callable { stock() })
        stock.get() + " " + bank.get()                          // throws at 100 ms...
    }                                                           // ...but close() waits for the bank

private val shared = Executors.newVirtualThreadPerTaskExecutor()

// B: one long-lived executor for the whole shop
private fun checkoutB(): String {
    val bank = shared.submit(Callable { bank() })
    val stock = shared.submit(Callable { stock() })
    return stock.get() + " " + bank.get()                       // throws at 100 ms, and returns
}

fun main() {
    println("A: an executor per checkout, closed by use {}")
    t0 = System.nanoTime()
    try {
        checkoutA()
    } catch (e: ExecutionException) {
        log("checkout failed: ${e.cause?.message}")
    }

    println("B: one shared executor")
    t0 = System.nanoTime()
    try {
        checkoutB()
    } catch (e: ExecutionException) {
        log("checkout failed: ${e.cause?.message}")
    }
    Thread.sleep(2_500)                                         // stay alive to see what B left behind
    shared.close()
}
