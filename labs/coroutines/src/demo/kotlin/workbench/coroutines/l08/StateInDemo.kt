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
    // a cold flow that reads the oven thermometer every 100 ms
    val readings = flow {
        var n = 0
        while (true) { emit(180 + n++); delay(100) }
    }.onStart { at("thermometer: reading started") }.onCompletion { at("thermometer: reading stopped") }

    val appScope = CoroutineScope(SupervisorJob() + Dispatchers.Default) // the owner of the sharing
    val temperature = readings.stateIn(appScope, started, initialValue = 0)
    at("stateIn returned; waiting 200 ms before the first screen")
    delay(200)

    val hall = launch { temperature.collect { } }
    val kitchen = launch { temperature.collect { } }
    at("two screens subscribed")
    delay(250)
    hall.cancel(); kitchen.cancel()
    at("both screens left; temperature.value = ${temperature.value}")
    delay(500)
    at("done")
    appScope.cancel()
}
