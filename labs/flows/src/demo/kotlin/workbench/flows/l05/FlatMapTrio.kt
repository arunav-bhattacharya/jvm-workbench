@file:OptIn(ExperimentalCoroutinesApi::class)

package workbench.flows.l05

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.buffer
import kotlinx.coroutines.flow.flatMapConcat
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.flatMapMerge
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.onCompletion
import kotlinx.coroutines.test.TestCoroutineScheduler
import kotlinx.coroutines.test.runTest

private suspend fun now() = currentCoroutineContext()[TestCoroutineScheduler]!!.currentTime
private suspend fun log(msg: String) = println("%5d ms  %s".format(now(), msg))

// A table that keeps changing its mind: order 1, then order 2 after 100 ms, then order 3 after another 100 ms.
private fun orders(): Flow<Int> = flow {
    for (n in 1..3) {
        if (n > 1) delay(100)
        log("outer emits $n")
        emit(n)
    }
}

// The sub-recipe for order n: part a is ready after 50 ms, part b 150 ms later.
private fun dish(n: Int): Flow<String> = flow {
    delay(50); emit("$n-a")
    delay(150); emit("$n-b")
}.onCompletion { cause -> if (cause != null) log("  inner $n cancelled: ${cause::class.simpleName}: ${cause.message}") }

private fun timeline(name: String, op: (Flow<Int>) -> Flow<String>) = runTest {
    println("== $name")
    op(orders()).collect { log("    collector got $it") }
    log("done")
}

fun main() {
    timeline("flatMapConcat") { it.flatMapConcat { n -> dish(n) } }
    timeline("flatMapMerge") { it.flatMapMerge { n -> dish(n) } }
    timeline("flatMapLatest") { it.flatMapLatest { n -> dish(n) } }
    timeline("buffer() then flatMapConcat") { it.buffer().flatMapConcat { n -> dish(n) } }
}
