package workbench.quotes.l02

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.future.future
import kotlinx.coroutines.job
import kotlinx.coroutines.supervisorScope
import kotlin.coroutines.cancellation.CancellationException

private val t0 = System.nanoTime()
private fun ms() = (System.nanoTime() - t0) / 1_000_000

private suspend fun call(name: String, latency: Long): String =
    try {
        delay(latency)
        println("  $name answered at ${ms()} ms")
        name
    } catch (e: CancellationException) {
        println("  $name cancelled at ${ms()} ms")
        throw e
    }

/** A request coroutine behind a CompletableFuture. The client hangs up after 120 ms. */
fun main() {
    val scope = CoroutineScope(Dispatchers.Default + SupervisorJob())   // the service's scope
    val request = scope.future {                                         // what QuoteService.quote returns
        supervisorScope {
            listOf("northbank" to 300L, "eastgate" to 400L, "fjord" to 500L)
                .map { (name, latency) -> async { call(name, latency) } }.awaitAll()
        }
    }
    Thread.sleep(120)
    println("client hangs up at ${ms()} ms: the handler calls request.cancel(true)")
    request.cancel(true)
    Thread.sleep(600)
    println("at ${ms()} ms: coroutines still running in the scope: ${scope.coroutineContext.job.children.count()}")
    scope.cancel()
}
