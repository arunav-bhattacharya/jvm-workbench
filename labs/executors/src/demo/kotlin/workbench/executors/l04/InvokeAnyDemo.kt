package workbench.executors.l04

import java.util.concurrent.Callable
import java.util.concurrent.Executors
import java.util.concurrent.Future
import java.util.concurrent.TimeUnit

private fun provider(name: String, millis: Long, fails: Boolean) = Callable {
    try {
        Thread.sleep(millis)
    } catch (e: InterruptedException) {
        println("  $name: interrupted, cancelled")
        throw e
    }
    if (fails) throw IllegalStateException("$name is down")
    "$name EUR/USD 1.0842"
}

/** Three FX-rate providers with different speeds: invokeAny takes the first, invokeAll waits with a deadline. */
fun main() {
    val providers = listOf(
        provider("alpha", 300, false),
        provider("beta", 100, true),          // fastest, but fails
        provider("gamma", 200, false),
    )
    Executors.newFixedThreadPool(3).use { pool ->
        println("invokeAny -> " + pool.invokeAny(providers))
        Thread.sleep(50)

        println("invokeAll with a 250 ms deadline:")
        val all = pool.invokeAll(providers, 250, TimeUnit.MILLISECONDS)
        for (f in all) {
            val detail = when (f.state()) {
                Future.State.SUCCESS -> ": " + f.resultNow()
                Future.State.FAILED -> ": " + f.exceptionNow().message
                else -> ""
            }
            println("  ${f.state()}$detail")
        }
    }
}
