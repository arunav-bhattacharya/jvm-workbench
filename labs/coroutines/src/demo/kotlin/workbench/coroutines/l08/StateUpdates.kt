package workbench.coroutines.l08

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

/** 8 helpers on Default each add 1 plate to a shared count 100,000 times. */
suspend fun countPlates(label: String, add: (MutableStateFlow<Long>) -> Unit) {
    val platesServed = MutableStateFlow(0L)
    coroutineScope {
        repeat(8) { launch(Dispatchers.Default) { repeat(100_000) { add(platesServed) } } }
    }
    println("%-34s expected 800000, got %d".format(label, platesServed.value))
}

fun main() = runBlocking {
    countPlates("value = value + 1") { it.value = it.value + 1 }  // read-modify-write: loses updates
    countPlates("update { it + 1 }") { it.update { plates -> plates + 1 } } // compare-and-set in a loop
}
