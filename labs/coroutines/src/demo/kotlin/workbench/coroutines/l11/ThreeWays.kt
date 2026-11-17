package workbench.coroutines.l11

import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.asCoroutineDispatcher
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import java.util.concurrent.Executors
import kotlin.system.measureTimeMillis

// one dinner: soup (100 ms), roast (300 ms) and salad (200 ms), all started at once

suspend fun dinnerWithCoroutines(): List<String> = coroutineScope {
    val soup = async { delay(100); "soup" }
    val roast = async { delay(300); "roast" }
    val salad = async { delay(200); "salad" }
    listOf(soup.await(), roast.await(), salad.await())
}

/** The same dinner written as BLOCKING code, run on whatever dispatcher you pass. */
suspend fun dinnerBlocking(on: CoroutineDispatcher): List<String> = coroutineScope {
    val soup = async(on) { Thread.sleep(100); "soup" }
    val roast = async(on) { Thread.sleep(300); "roast" }
    val salad = async(on) { Thread.sleep(200); "salad" }
    listOf(soup.await(), roast.await(), salad.await())
}

fun main() = runBlocking {
    repeat(2) { dinnerWithCoroutines() } // warm up
    val c = measureTimeMillis { println("coroutines:                       ${dinnerWithCoroutines()}") }
    println("  took $c ms on ${Thread.currentThread().name.substringBefore(" @")}")
    Executors.newVirtualThreadPerTaskExecutor().asCoroutineDispatcher().use { vt ->
        val v = measureTimeMillis { println("blocking code on virtual threads: ${dinnerBlocking(vt)}") }
        println("  took $v ms")
    }
    val b = measureTimeMillis {
        withContext(Dispatchers.IO) { println("blocking code on Dispatchers.IO: ${dinnerBlocking(Dispatchers.IO)}") }
    }
    println("  took $b ms")
}
