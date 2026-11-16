package workbench.flows.l05

import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.emptyFlow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.onCompletion
import kotlinx.coroutines.flow.zip
import kotlinx.coroutines.test.TestCoroutineScheduler
import kotlinx.coroutines.test.runTest

@OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
private suspend fun now() = currentCoroutineContext()[TestCoroutineScheduler]!!.currentTime
private suspend fun log(msg: String) = println("%5d ms  %s".format(now(), msg))

// Checkout prices in USD cents every 100 ms from t=100; the USD to EUR rate at t=250 and t=550.
private fun prices() = flow { for (p in listOf(1000, 1010, 1020, 1030, 1040, 1050)) { delay(100); log("price  $p"); emit(p) } }
private fun fxRates() = flow { delay(250); log("fx     0.92"); emit(0.92); delay(300); log("fx     0.95"); emit(0.95) }

fun main() {
    runTest {
        println("== zip: a zipper, pairs by index")
        prices().onCompletion { log("prices ended: $it") }
            .zip(fxRates()) { p, fx -> "$p@$fx" }
            .collect { log("  -> $it") }
    }
    runTest {
        println("== combine: a board with the latest of each")
        combine(prices(), fxRates()) { p, fx -> "$p@$fx" }.collect { log("  -> $it") }
    }
    runTest {
        println("== combine with a rate feed that never emits")
        combine(prices(), emptyFlow<Double>()) { p, fx -> "$p@$fx" }.collect { log("  -> $it") }
        log("done, nothing combined")
    }
}
