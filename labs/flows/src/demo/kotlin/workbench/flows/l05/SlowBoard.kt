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

// A price feed ticks every 10 ms (10 ticks); the merchant config is one value.
// The dashboard that collects the board needs 100 ms per update.
private fun ticks(verbose: Boolean) = flow { for (i in 1..10) { delay(10); if (verbose) log("  feed emits $i"); emit(i) } }

fun main() {
    runTest {
        println("== combine, slow collector")
        combine(ticks(verbose = true), flowOf("cfg")) { i, c -> "$i/$c" }
            .collect { log("-> $it (dashboard busy 100 ms)"); delay(100) }
        log("done")
    }
    runTest {
        println("== combine(...).conflate(), slow collector")
        combine(ticks(verbose = false), flowOf("cfg")) { i, c -> "$i/$c" }.conflate()
            .collect { log("-> $it"); delay(100) }
    }
    runTest {
        println("== combine(...).buffer(UNLIMITED), slow collector")
        val got = combine(ticks(verbose = false), flowOf("cfg")) { i, c -> "$i/$c" }
            .buffer(Channel.UNLIMITED).onEach { delay(100) }.toList()
        log("got ${got.size}: $got")
    }
}
