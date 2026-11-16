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

// A merchant search box: the user picks merchant 1, then 2 after 100 ms, then 3 after another 100 ms.
private fun picks(): Flow<Int> = flow {
    for (n in 1..3) {
        if (n > 1) delay(100)
        log("outer emits $n")
        emit(n)
    }
}

// The details for merchant n: part a after 50 ms, part b 150 ms later.
private fun details(n: Int): Flow<String> = flow {
    delay(50); emit("$n-a")
    delay(150); emit("$n-b")
}.onCompletion { cause -> if (cause != null) log("  inner $n cancelled: ${cause::class.simpleName}: ${cause.message}") }

private fun timeline(name: String, op: (Flow<Int>) -> Flow<String>) = runTest {
    println("== $name")
    op(picks()).collect { log("    collector got $it") }
    log("done")
}

fun main() {
    timeline("flatMapConcat") { it.flatMapConcat { n -> details(n) } }
    timeline("flatMapMerge") { it.flatMapMerge { n -> details(n) } }
    timeline("flatMapLatest") { it.flatMapLatest { n -> details(n) } }
    timeline("buffer() then flatMapConcat") { it.buffer().flatMapConcat { n -> details(n) } }
}
