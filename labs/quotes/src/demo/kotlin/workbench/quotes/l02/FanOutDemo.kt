package workbench.quotes.l02

import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.withTimeoutOrNull

// three invented providers: name, latency in ms, price
private val providers = listOf(Triple("northbank", 120L, "1.0845"), Triple("eastgate", 300L, "1.0841"), Triple("fjord", 200L, "1.0843"))

private suspend fun ask(name: String, ms: Long, price: String): String {
    delay(ms)
    return "$name $price"
}

/** One quote from three providers: one after another, all at once, and all at once inside a deadline. */
fun main() = runTest {                                         // virtual time: delays are skipped, the clock still counts
    val deadline = 250L
    var t0 = currentTime
    val inTurn = providers.map { (n, ms, p) -> ask(n, ms, p) }
    println("one after another:     ${currentTime - t0} ms  $inTurn")

    t0 = currentTime
    val atOnce = coroutineScope { providers.map { (n, ms, p) -> async { ask(n, ms, p) } }.awaitAll() }
    println("async, all at once:    ${currentTime - t0} ms  $atOnce")

    t0 = currentTime
    val inTime = coroutineScope {
        providers.map { (n, ms, p) -> async { withTimeoutOrNull(deadline) { ask(n, ms, p) } } }.awaitAll()
    }
    println("with a $deadline ms deadline: ${currentTime - t0} ms  $inTime")
}
