package workbench.coroutines.l08

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

/** 8 coroutines on Default each add 1 cent to a shared StateFlow 100,000 times. */
suspend fun addCents(label: String, add: (MutableStateFlow<Long>) -> Unit) {
    val capturedCents = MutableStateFlow(0L)
    coroutineScope {
        repeat(8) { launch(Dispatchers.Default) { repeat(100_000) { add(capturedCents) } } }
    }
    println("%-34s expected 800000, got %d".format(label, capturedCents.value))
}

fun main() = runBlocking {
    addCents("value = value + 1") { it.value = it.value + 1 }  // read-modify-write: loses updates
    addCents("update { it + 1 }") { it.update { cents -> cents + 1 } } // compare-and-set in a loop
}
