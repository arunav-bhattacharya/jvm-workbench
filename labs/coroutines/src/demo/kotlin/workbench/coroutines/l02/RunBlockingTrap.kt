package workbench.coroutines.l02

import kotlinx.coroutines.asCoroutineDispatcher
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import java.util.concurrent.Executors
import kotlin.system.measureTimeMillis

/** A suspend function that "helpfully" calls runBlocking inside. Pass "bad" to use it. */
suspend fun lookupBad(id: Int): Int {
    runBlocking { delay(200) } // blocks the calling thread for 200 ms
    return id
}

suspend fun lookupGood(id: Int): Int {
    delay(200) // suspends; the thread serves other coroutines meanwhile
    return id
}

fun main(args: Array<String>) {
    val bad = args.firstOrNull() == "bad"
    // a pool with only two threads, like a small request pool
    Executors.newFixedThreadPool(2).asCoroutineDispatcher().use { pool ->
        val took = measureTimeMillis {
            runBlocking {
                withContext(pool) {
                    repeat(8) { id -> launch { if (bad) lookupBad(id) else lookupGood(id) } }
                }
            }
        }
        println("8 lookups of 200 ms on 2 threads (${if (bad) "runBlocking inside" else "delay"}): $took ms")
    }
}
