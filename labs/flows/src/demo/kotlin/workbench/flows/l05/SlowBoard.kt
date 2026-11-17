package workbench.flows.l05

import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.buffer
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.conflate
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.test.TestCoroutineScheduler
import kotlinx.coroutines.test.runTest

@OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
private suspend fun now() = currentCoroutineContext()[TestCoroutineScheduler]!!.currentTime
private suspend fun log(msg: String) = println("%5d ms  %s".format(now(), msg))

// The thermometer ticks every 10 ms (10 ticks); the dial is one value, 180.
// The oven-door screen that collects the slate needs 100 ms to draw each update.
private fun ticks(verbose: Boolean) = flow { for (i in 1..10) { delay(10); if (verbose) log("  thermometer emits $i"); emit(i) } }

fun main() {
    runTest {
        println("== combine, slow collector")
        combine(ticks(verbose = true), flowOf(180)) { i, d -> "$i/$d" }
            .collect { log("-> $it (screen busy 100 ms)"); delay(100) }
        log("done")
    }
    runTest {
        println("== combine(...).conflate(), slow collector")
        combine(ticks(verbose = false), flowOf(180)) { i, d -> "$i/$d" }.conflate()
            .collect { log("-> $it"); delay(100) }
    }
    runTest {
        println("== combine(...).buffer(UNLIMITED), slow collector")
        val got = combine(ticks(verbose = false), flowOf(180)) { i, d -> "$i/$d" }
            .buffer(Channel.UNLIMITED).onEach { delay(100) }.toList()
        log("got ${got.size}: $got")
    }
}
