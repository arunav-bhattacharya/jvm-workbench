package workbench.flows.l02

import kotlinx.coroutines.cancel
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.asFlow
import kotlinx.coroutines.flow.buffer
import kotlinx.coroutines.flow.cancellable
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.transform
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

/**
 * A reconciliation job that cancels its own coroutine when it sees 3, and never suspends.
 * Which flows stop there, and which keep delivering?
 */
suspend fun stopAtThree(name: String, f: Flow<Int>) = coroutineScope {
    val seen = mutableListOf<Int>()
    val job = launch {
        f.collect { v ->
            seen += v
            if (v == 3) cancel()          // cancel this coroutine; no suspension follows
        }
    }
    job.join()
    println("%-40s %s".format(name, seen))
}

fun main() = runBlocking {
    stopAtThree("flow { for (i in 1..5) emit(i) }", flow { for (i in 1..5) emit(i) })
    stopAtThree("(1..5).asFlow()", (1..5).asFlow())
    stopAtThree("flowOf(1, 2, 3, 4, 5)", flowOf(1, 2, 3, 4, 5))
    stopAtThree("(1..5).asFlow().cancellable()", (1..5).asFlow().cancellable())
    stopAtThree("(1..5).asFlow().map { it }", (1..5).asFlow().map { it })
    stopAtThree("(1..5).asFlow().transform { emit(it) }", (1..5).asFlow().transform { emit(it) })

    println()
    println("class behind each one:")
    println("  flow { }      -> ${flow<Int> { }::class.qualifiedName}")
    println("  flowOf(1, 2)  -> ${flowOf(1, 2)::class.java.name}")
    println("  asFlow()      -> ${(1..2).asFlow()::class.java.name}")
    println("  transform { } -> ${flowOf(1).transform<Int, Int> { emit(it) }::class.qualifiedName}")
}
