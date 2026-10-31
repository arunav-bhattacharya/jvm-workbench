package workbench.coroutines.l04

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlin.system.measureTimeMillis

/** 32 blocking 200 ms calls, then one tiny CPU task on Default. Pass "io" to run the blocking calls on IO. */
fun main(args: Array<String>) = runBlocking {
    val onIo = args.firstOrNull() == "io"
    val blockingDispatcher = if (onIo) Dispatchers.IO else Dispatchers.Default
    val cores = Runtime.getRuntime().availableProcessors()
    var cpuWaitMs = 0L
    val took = measureTimeMillis {
        coroutineScope {
            repeat(32) { launch(blockingDispatcher) { Thread.sleep(200) } } // JDBC-style blocking calls
            delay(20) // let them start
            val asked = System.nanoTime()
            val heartbeat = async(Dispatchers.Default) { System.nanoTime() } // 1 microsecond of CPU work
            cpuWaitMs = (heartbeat.await() - asked) / 1_000_000
        }
    }
    val where = if (onIo) "Dispatchers.IO" else "Dispatchers.Default"
    println("32 blocking calls on $where ($cores cores): $took ms")
    println("a tiny CPU task on Default waited $cpuWaitMs ms to start")
}
