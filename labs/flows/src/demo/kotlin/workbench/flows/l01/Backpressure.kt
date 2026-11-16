@file:OptIn(ExperimentalCoroutinesApi::class)

package workbench.flows.l01

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.test.runTest

// A producer that needs 100 ms per settlement line and a ledger writer that needs 300 ms per posting.
// runTest runs on virtual time: delay() moves a fake clock, so the numbers are exact and the
// program finishes at once.
fun main() = runTest {
    val t = { testScheduler.currentTime }

    println("=== the toy flow")
    toyFlow {
        for (id in 1..3) {
            delay(100)
            println("  t=%4d emit %d".format(t(), id))
            emit(id)
        }
    }.collect { id ->
        delay(300)
        println("  t=%4d posted %d".format(t(), id))
    }
    val toyEnd = t()
    println("  total ${toyEnd} ms")

    println("=== kotlinx flow { }")
    flow {
        for (id in 1..3) {
            delay(100)
            println("  t=%4d emit %d".format(t() - toyEnd, id))
            emit(id)
        }
    }.collect { id ->
        delay(300)
        println("  t=%4d posted %d".format(t() - toyEnd, id))
    }
    println("  total ${t() - toyEnd} ms")
}
