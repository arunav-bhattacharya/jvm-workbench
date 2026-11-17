@file:OptIn(ExperimentalCoroutinesApi::class)

package workbench.flows.l03

import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.asCoroutineDispatcher
import kotlinx.coroutines.channels.produce
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicInteger

/** flowOn by hand: a second coroutine on [dispatcher] sends into a 64-slot channel, and we drain it. */
fun <T> Flow<T>.myFlowOn(dispatcher: CoroutineDispatcher): Flow<T> = flow {
    coroutineScope {
        val hatch = produce(dispatcher, capacity = 64) {      // the second cook, behind the wall
            this@myFlowOn.collect { send(it) }                 // the upstream's emit now puts a plate in the hatch
        }
        for (value in hatch) emit(value)                       // we stay in the collector's coroutine
    }
}

/** How many emits return while the collector still holds the first value? */
suspend fun ahead(label: String, op: (Flow<Int>) -> Flow<Int>) = coroutineScope {
    val returned = AtomicInteger()
    val gate = CompletableDeferred<Unit>()
    var received = 0
    val source = flow { for (i in 1..200) { emit(i); returned.set(i) } }
    val job = launch { op(source).collect { received++; if (received == 1) gate.await() } }
    delay(200)                                                  // let the producer run as far as it can
    val heldAt = returned.get()
    gate.complete(Unit)
    job.join()
    println("%-22s emits returned while the collector held item 1: %3d (received %d)".format(label, heldAt, received))
}

fun main() = runBlocking {
    val io = Executors.newSingleThreadExecutor { r -> Thread(r, "io-thread") }.asCoroutineDispatcher()

    println("=== who runs where")
    flow { emit("flour"); println("emit flour returned on ${Thread.currentThread().name}") }
        .myFlowOn(io)
        .collect { println("myFlowOn: collected $it on ${Thread.currentThread().name}") }
    flow { emit("flour"); println("emit flour returned on ${Thread.currentThread().name}") }
        .flowOn(io)
        .collect { println("flowOn:   collected $it on ${Thread.currentThread().name}") }

    println("=== how far ahead the producer gets")
    ahead("plain") { it }
    ahead("myFlowOn(io)") { it.myFlowOn(io) }
    ahead("flowOn(io)") { it.flowOn(io) }

    println("=== the collector's stack after flowOn(io)")
    flow { emit("flour") }.flowOn(io).collect {
        Thread.currentThread().stackTrace.drop(1)
            .takeWhile { !it.className.startsWith("kotlinx.coroutines.DispatchedTask") }
            .forEach { println("    at ${it.className.removePrefix("workbench.flows.l03.")}.${it.methodName}") }
    }
    io.close()
}
