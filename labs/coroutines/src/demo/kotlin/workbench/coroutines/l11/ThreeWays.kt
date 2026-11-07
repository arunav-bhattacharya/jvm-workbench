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

// one payment-details request: account (100 ms), ledger (300 ms) and risk (200 ms), done at once

suspend fun detailsWithCoroutines(): List<String> = coroutineScope {
    val account = async { delay(100); "account" }
    val ledger = async { delay(300); "ledger" }
    val risk = async { delay(200); "risk" }
    listOf(account.await(), ledger.await(), risk.await())
}

/** The same calls written as BLOCKING code, run on whatever dispatcher you pass. */
suspend fun detailsBlocking(vt: CoroutineDispatcher): List<String> = coroutineScope {
    val account = async(vt) { Thread.sleep(100); "account" }
    val ledger = async(vt) { Thread.sleep(300); "ledger" }
    val risk = async(vt) { Thread.sleep(200); "risk" }
    listOf(account.await(), ledger.await(), risk.await())
}

fun main() = runBlocking {
    repeat(2) { detailsWithCoroutines() } // warm up
    val c = measureTimeMillis { println("coroutines:                       ${detailsWithCoroutines()}") }
    println("  took $c ms on ${Thread.currentThread().name.substringBefore(" @")}")
    Executors.newVirtualThreadPerTaskExecutor().asCoroutineDispatcher().use { vt ->
        val v = measureTimeMillis { println("blocking code on virtual threads: ${detailsBlocking(vt)}") }
        println("  took $v ms")
    }
    val b = measureTimeMillis {
        withContext(Dispatchers.IO) { println("blocking code on Dispatchers.IO: ${detailsBlocking(Dispatchers.IO)}") }
    }
    println("  took $b ms")
}
