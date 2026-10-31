package workbench.coroutines.l01

import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlin.system.measureTimeMillis

/** Five coroutines share ONE thread and each waits 200 ms. Pass "sleep" to block instead of suspend. */
fun main(args: Array<String>) {
    val blocking = args.firstOrNull() == "sleep"
    val took = measureTimeMillis {
        runBlocking { // runs every coroutine below on the main thread
            repeat(5) { i ->
                launch {
                    println("payment $i starts waiting on ${Thread.currentThread().name}")
                    if (blocking) Thread.sleep(200) else delay(200)
                }
            }
        }
    }
    val how = if (blocking) "Thread.sleep" else "delay"
    println("5 waits of 200 ms with $how took $took ms")
}
