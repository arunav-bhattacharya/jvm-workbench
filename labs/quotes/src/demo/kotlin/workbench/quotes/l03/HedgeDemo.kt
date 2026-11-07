package workbench.quotes.l03

import kotlinx.coroutines.async
import kotlinx.coroutines.cancelChildren
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.selects.select
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.withTimeoutOrNull

private var calls = 0

// Northbank: 40 ms, except every 20th call, which takes 600 ms (its slow 5%)
private suspend fun northbank(): String {
    val n = ++calls
    delay(if (n % 20 == 0) 600 else 40)
    return "northbank 1.0845"
}

private suspend fun <T : Any> hedged(afterMs: Long, call: suspend () -> T): T = coroutineScope {
    val first = async { call() }
    val early = withTimeoutOrNull(afterMs) { first.await() }
    if (early != null) return@coroutineScope early
    val second = async { call() }                        // the hedge
    select { first.onAwait { it }; second.onAwait { it } }.also { coroutineContext.cancelChildren() }
}

/** 200 quotes from Northbank, one after another, with and without a hedge after 80 ms. */
fun main() = runTest {
    for (hedgeAfter in listOf(null, 80L)) {
        calls = 0
        val latencies = (1..200).map {
            val t0 = currentTime
            if (hedgeAfter == null) northbank() else hedged(hedgeAfter) { northbank() }
            currentTime - t0
        }.sorted()
        println("%-15s p50 %3d ms   p99 %3d ms   max %3d ms   calls to Northbank: %d".format(
            if (hedgeAfter == null) "no hedge" else "hedge at $hedgeAfter ms",
            latencies[99], latencies[197], latencies.last(), calls))
    }
}
