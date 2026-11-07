package workbench.coroutines.l08

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.onCompletion
import kotlinx.coroutines.flow.onStart
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

private var t0 = 0L
private fun at(msg: String) = println("%5d ms  %s".format((System.nanoTime() - t0) / 1_000_000, msg))

fun main(args: Array<String>) = runBlocking {
    t0 = System.nanoTime()
    val started = when (args.firstOrNull()) {
        "eagerly" -> SharingStarted.Eagerly
        "lazily" -> SharingStarted.Lazily
        else -> SharingStarted.WhileSubscribed(stopTimeoutMillis = 300)
    }
    // a cold flow that polls the FX provider every 100 ms
    val polls = flow {
        var n = 0
        while (true) { emit(1.0800 + n++ / 10_000.0); delay(100) }
    }.onStart { at("upstream: polling started") }.onCompletion { at("upstream: polling stopped") }

    val appScope = CoroutineScope(SupervisorJob() + Dispatchers.Default) // the owner of the sharing
    val rate = polls.stateIn(appScope, started, initialValue = 0.0)
    at("stateIn returned; waiting 200 ms before the first dashboard")
    delay(200)

    val a = launch { rate.collect { } }
    val b = launch { rate.collect { } }
    at("two dashboards subscribed")
    delay(250)
    a.cancel(); b.cancel()
    at("both dashboards left; rate.value = ${rate.value}")
    delay(500)
    at("done")
    appScope.cancel()
}
