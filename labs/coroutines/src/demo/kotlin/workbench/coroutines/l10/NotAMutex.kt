package workbench.coroutines.l10

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.joinAll
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeoutOrNull

fun main() = runBlocking {
    val oneAtATime = Dispatchers.Default.limitedParallelism(1)

    println("limitedParallelism(1):")
    List(3) { i ->
        launch(oneAtATime) {
            println("  credit $i: read balance")
            delay(20) // the FX call suspends: the single thread is free for someone else
            println("  credit $i: write balance")
        }
    }.joinAll()

    println("Mutex.withLock:")
    val mutex = Mutex()
    List(3) { i ->
        launch(Dispatchers.Default) {
            mutex.withLock {
                println("  credit $i: read balance")
                delay(20) // still suspends, but nobody else can enter the lock
                println("  credit $i: write balance")
            }
        }
    }.joinAll()

    println("Mutex is not reentrant:")
    val nested = withTimeoutOrNull(500) {
        mutex.withLock {
            withContext(Dispatchers.Default) { mutex.withLock { "inner" } } // the same coroutine tree locks again
        }
    }
    println("  nested withLock -> ${nested ?: "timed out after 500 ms: it waits for itself"}")
}
