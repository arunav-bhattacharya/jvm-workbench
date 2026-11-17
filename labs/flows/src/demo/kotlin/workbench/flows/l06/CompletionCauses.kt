package workbench.flows.l06

import kotlinx.coroutines.awaitCancellation
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.flow.emptyFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.onCompletion
import kotlinx.coroutines.flow.single
import kotlinx.coroutines.flow.take
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.runTest
import java.io.IOException

private fun cause(t: Throwable?) = t?.let { "${it::class.qualifiedName}: ${it.message}" } ?: "null"

fun main() = runTest {
    println("== onCompletion: how did the flow end?")
    flowOf(1, 2).onCompletion { println("  success:               ${cause(it)}") }.collect()
    runCatching {
        flow<Int> { emit(1); throw IOException("line dropped") }
            .onCompletion { println("  upstream failure:      ${cause(it)}") }.collect()
    }
    runCatching {
        flowOf(1, 2).onCompletion { println("  collector failure:     ${cause(it)}") }
            .collect { error("the diner dropped the plate") }
    }
    flowOf(1, 2).onCompletion { println("  failure caught below:  ${cause(it)}") }
        .map { error("map failed") }.catch { }.collect()
    flowOf(1, 2, 3).onCompletion { println("  above take(1):         ${cause(it)}") }
        .take(1).onCompletion { println("  below take(1):         ${cause(it)}") }.collect()
    flowOf(1, 2, 3).onCompletion { println("  above first():         ${cause(it)}") }.first()
    val job = launch { flow { emit(1); awaitCancellation() }.onCompletion { println("  job.cancel():          ${cause(it)}") }.collect() }
    delay(10); job.cancel(); job.join()

    println("== terminal operators")
    for ((label, call) in listOf<Pair<String, suspend () -> Any?>>(
        "emptyFlow<Int>().first()" to { emptyFlow<Int>().first() },
        "emptyFlow<Int>().single()" to { emptyFlow<Int>().single() },
        "flowOf(1, 2).single()" to { flowOf(1, 2).single() },
    )) println("  %-28s %s".format(label, runCatching { call() }.fold({ "$it" }, { "throws ${cause(it)}" })))
    var produced = 0
    runCatching { flow { repeat(3) { produced++; emit(it) } }.single() }
    println("  single() on a 3-element flow pulled $produced elements")
    produced = 0
    flow { repeat(3) { produced++; emit(it) } }.first()
    println("  first() on a 3-element flow pulled $produced element")
}
