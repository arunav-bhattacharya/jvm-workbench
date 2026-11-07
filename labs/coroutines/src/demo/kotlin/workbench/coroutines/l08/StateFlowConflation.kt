package workbench.coroutines.l08

import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

data class Rate(val pair: String, val mid: Double)

fun main() = runBlocking {
    val eurUsd = MutableStateFlow(Rate("EUR/USD", 1.0810))
    val dashboard = launch(start = CoroutineStart.UNDISPATCHED) {
        eurUsd.collect { rate ->
            println("dashboard shows ${rate.mid}")
            delay(100) // rendering is slow
        }
    }
    // three ticks arrive while the dashboard is busy rendering the first value
    eurUsd.value = Rate("EUR/USD", 1.0811)
    eurUsd.value = Rate("EUR/USD", 1.0812)
    eurUsd.value = Rate("EUR/USD", 1.0813)
    delay(150)
    println("setting an equal rate again (a new object, same fields)")
    eurUsd.value = Rate("EUR/USD", 1.0813)
    delay(150)
    println("value is ${eurUsd.value.mid}; the collector is still waiting, because a StateFlow never completes")
    dashboard.cancel()
}
