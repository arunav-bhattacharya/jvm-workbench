package workbench.coroutines.l04

import kotlinx.coroutines.CoroutineName
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.asCoroutineDispatcher
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import java.util.concurrent.Executors

private fun here() = Thread.currentThread().toString()

fun main() {
    // debug mode adds " @name#id" to thread names. Set it before any coroutine starts.
    System.setProperty("kotlinx.coroutines.debug", "on")
    runBlocking(CoroutineName("statement")) {
        println("runBlocking           ${here()}")
        withContext(Dispatchers.Default) { println("Default               ${here()}") }
        withContext(Dispatchers.IO) { println("IO                    ${here()}") }
        withContext(Dispatchers.Unconfined) {
            println("Unconfined, before    ${here()}")
            delay(10) // resumes on whatever thread finishes the delay
            println("Unconfined, after     ${here()}")
        }
        Executors.newSingleThreadExecutor { r -> Thread(r, "ledger-writer") }.asCoroutineDispatcher().use { single ->
            withContext(single + CoroutineName("ledger")) { println("single-thread exec    ${here()}") }
        }
        Executors.newVirtualThreadPerTaskExecutor().asCoroutineDispatcher().use { vt ->
            withContext(vt) { println("virtual-thread exec   ${here()}") }
        }
    }
}
