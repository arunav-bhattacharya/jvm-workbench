package workbench.flows.l07

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.TestCoroutineScheduler
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runTest

// An FX poller shared with stateIn. Each run of the upstream is numbered and emits
// run * 100 + i every 1,000 ms, so you can see when a run starts over. Virtual time.
private class Poller(private val clock: TestCoroutineScheduler) {
    var starts = 0
    @OptIn(ExperimentalCoroutinesApi::class)
    val flow: Flow<Int> = flow {
        val run = ++starts
        println("  t=${clock.currentTime}: upstream START #$run")
        try {
            var i = 0
            while (true) { emit(run * 100 + i++); delay(1_000) }
        } finally { println("  t=${clock.currentTime}: upstream STOP #$run") }
    }
}

@OptIn(ExperimentalCoroutinesApi::class)
private fun dashboard(started: SharingStarted) = runTest {
    println("== $started, initialValue = -1")
    val poller = Poller(testScheduler)
    val rate: StateFlow<Int> = poller.flow.stateIn(backgroundScope, started, initialValue = -1)
    fun open() = backgroundScope.launch { rate.collect { println("  t=$currentTime: A got $it") } }
    var a = open()
    delay(2_500); a.cancel(); println("  t=$currentTime: A leaves")
    delay(1_500); println("  t=$currentTime: A comes back"); a = open()
    delay(2_000); a.cancel(); println("  t=$currentTime: A leaves")
    delay(8_000); println("  t=$currentTime: A comes back"); open()
    delay(1_500); println("  t=$currentTime: end, upstream starts=${poller.starts}")
}

// Request handlers that only read .value and never collect.
@OptIn(ExperimentalCoroutinesApi::class)
private fun readOnly() = runTest {
    println("== a cache that request handlers only read with .value")
    for (started in listOf(SharingStarted.WhileSubscribed(5_000), SharingStarted.Lazily, SharingStarted.Eagerly)) {
        var fetches = 0
        val feed = flow { while (true) { fetches++; emit("1.08${50 + fetches}"); delay(1_000) } }
        val scope = CoroutineScope(SupervisorJob() + StandardTestDispatcher(testScheduler))
        val eurUsd: StateFlow<String?> = feed.stateIn(scope, started, initialValue = null)
        delay(3_500)
        println("  $started: three requests read ${List(3) { eurUsd.value }}, upstream fetches=$fetches")
        scope.cancel()
    }
}

fun main(args: Array<String>) {
    when (args.firstOrNull()) {
        "expire" -> dashboard(SharingStarted.WhileSubscribed(5_000, replayExpirationMillis = 0))
        "stop0" -> dashboard(SharingStarted.WhileSubscribed())
        else -> { dashboard(SharingStarted.WhileSubscribed(5_000)); readOnly() }
    }
}
