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

// The oven thermometer reads every 100 ms from t=100; the dial is turned to 180 at t=250 and to 200 at t=550.
private fun readings() = flow { for (c in listOf(150, 152, 154, 156, 158, 160)) { delay(100); log("reading $c"); emit(c) } }
private fun dial() = flow { delay(250); log("dial    180"); emit(180); delay(300); log("dial    200"); emit(200) }

fun main() {
    runTest {
        println("== zip: a zipper, pairs by number")
        readings().onCompletion { log("readings ended: $it") }
            .zip(dial()) { c, d -> "$c of $d" }
            .collect { log("  screen shows $it") }
    }
    runTest {
        println("== combine: a slate with the latest of each")
        combine(readings(), dial()) { c, d -> "$c of $d" }.collect { log("  screen shows $it") }
    }
    runTest {
        println("== combine with a dial that is never turned")
        combine(readings(), emptyFlow<Int>()) { c, d -> "$c of $d" }.collect { log("  screen shows $it") }
        log("done, nothing combined")
    }
}
