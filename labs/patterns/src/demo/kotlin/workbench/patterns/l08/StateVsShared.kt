package workbench.patterns.l08

import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.yield

// The same three sales at the counter, observed through a StateFlow and through a SharedFlow.

fun main() = runBlocking {
    val state = MutableStateFlow("nothing yet")         // state: the latest value; equal values are dropped
    val events = MutableSharedFlow<String>()            // events: every value, to every collector

    val fromState = mutableListOf<String>()
    val fromEvents = mutableListOf<String>()
    val collectors = listOf(
        launch(start = CoroutineStart.UNDISPATCHED) { state.collect { fromState += it } },
        launch(start = CoroutineStart.UNDISPATCHED) { events.collect { fromEvents += it } },
    )

    for (update in listOf("rye bread", "rye bread", "jam")) {   // two loaves sold, then a jar of jam
        state.value = update
        events.emit(update)                             // suspends until every collector has taken it
        yield()
    }
    collectors.forEach { it.cancel() }

    println("StateFlow collector saw:  $fromState")
    println("SharedFlow collector saw: $fromEvents")
}
