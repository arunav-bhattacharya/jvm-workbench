package workbench.coroutines.l07

import kotlinx.coroutines.flow.filter
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.runBlocking

fun main() = runBlocking {
    // amounts in cents; refunds are negative
    val pipeline = flowOf(4_250L, -990L, 12_000L)
        .onEach { println("emit    $it") }
        .filter { it > 0 }.onEach { println("  filter passed $it") }
        .map { "EUR %.2f".format(it / 100.0) }.onEach { println("    map   -> $it") }
    println("pipeline built: no line above has printed yet")
    pipeline.collect { println("      collect $it") }
}
