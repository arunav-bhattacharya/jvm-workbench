package workbench.coroutines.l07

import kotlinx.coroutines.flow.filter
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.runBlocking

fun main() = runBlocking {
    // weights in grams from the kitchen scale; a negative reading means it wasn't set to zero
    val pipeline = flowOf(250L, -40L, 1_200L)
        .onEach { println("emit    $it") }
        .filter { it > 0 }.onEach { println("  filter passed $it") }
        .map { "%.2f kg".format(it / 1_000.0) }.onEach { println("    map   -> $it") }
    println("pipeline built: no line above has printed yet")
    pipeline.collect { println("      collect $it") }
}
