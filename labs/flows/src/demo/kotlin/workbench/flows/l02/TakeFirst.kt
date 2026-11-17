package workbench.flows.l02

import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.onCompletion
import kotlinx.coroutines.flow.take
import kotlinx.coroutines.runBlocking

/** Five dishes, numbered. The producer reports what comes out of emit, and when its finally runs. */
fun source(tag: String) = flow {
    try {
        for (i in 1..5) {
            println("  [$tag] emit $i")
            emit(i)
        }
    } catch (e: Throwable) {
        println("  [$tag] emit threw ${e::class.qualifiedName}: ${e.message}")
        throw e
    } finally {
        println("  [$tag] finally")
    }
}

fun main() = runBlocking {
    println("take(2):")
    source("take").onCompletion { println("  [take] onCompletion cause=$it") }.take(2).collect { println("  got $it") }

    println("first():")
    println("  first = " + source("first").first())

    println("first { it > 2 }:")
    println("  first = " + source("firstP").first { it > 2 })

    println("a producer that swallows the abort:")
    try {
        flow {
            try { emit(1) } catch (e: Throwable) { println("  swallowed ${e::class.simpleName}") }
            emit(2)
        }.take(1).collect { println("  got $it") }
    } catch (e: IllegalStateException) {
        println("  collect threw: " + e.message!!.lineSequence().take(2).joinToString(" "))
    }
}
