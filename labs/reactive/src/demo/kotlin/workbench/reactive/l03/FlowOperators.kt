package workbench.reactive.l03

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flatMapMerge
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.mapLatest
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.runBlocking

// The same source as OrderingDemo: 3, 1, 2, where item i takes i x 100 ms.
private suspend fun slowCall(i: Int): Int {
    delay(i * 100L)
    return i
}

@OptIn(ExperimentalCoroutinesApi::class)
fun main() = runBlocking {
    val source: Flow<Int> = flowOf(3, 1, 2)

    // like flatMap: inner flows run concurrently, results merge as they finish
    val merged = source.flatMapMerge(concurrency = 4) { i -> flow { emit(slowCall(i)) } }.toList()

    // like concatMap: a suspending map already waits for each item before taking the next
    val sequential = source.map { i -> slowCall(i) }.toList()

    // like switchMap: a new item cancels the block still running for the previous one
    val latest = flow {
        emit("EUR"); delay(50)
        emit("GBP"); delay(250)
        emit("JPY")
    }.mapLatest { ccy -> delay(100); "$ccy=quote" }.onEach { println("quote $it") }.toList()

    println("flatMapMerge: $merged, map: $sequential, mapLatest: $latest")
}
