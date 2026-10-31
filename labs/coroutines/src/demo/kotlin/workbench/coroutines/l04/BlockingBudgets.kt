package workbench.coroutines.l04

import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.asCoroutineDispatcher
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicInteger
import kotlin.system.measureTimeMillis

/** 400 blocking calls of 200 ms each, on three different dispatchers. */
suspend fun runBlockingCalls(label: String, dispatcher: CoroutineDispatcher) {
    val active = AtomicInteger()
    val peak = AtomicInteger()
    val took = measureTimeMillis {
        coroutineScope {
            repeat(400) {
                launch(dispatcher) {
                    peak.accumulateAndGet(active.incrementAndGet(), ::maxOf)
                    Thread.sleep(200) // a blocking issuer call
                    active.decrementAndGet()
                }
            }
        }
    }
    println("%-32s %5d ms, peak %3d calls at once".format(label, took, peak.get()))
}

fun main() = runBlocking {
    runBlockingCalls("Dispatchers.IO", Dispatchers.IO)
    runBlockingCalls("IO.limitedParallelism(400)", Dispatchers.IO.limitedParallelism(400))
    Executors.newVirtualThreadPerTaskExecutor().asCoroutineDispatcher().use { vt ->
        runBlockingCalls("virtual-thread executor", vt)
    }
}
