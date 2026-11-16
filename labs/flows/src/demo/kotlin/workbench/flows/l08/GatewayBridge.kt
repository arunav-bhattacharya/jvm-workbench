package workbench.flows.l08

import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.flow.take
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.yield
import java.io.IOException

// The gateway's listener API as a Flow.
fun DemoGateway.events(): Flow<PayEvent> = callbackFlow {
    val registration = register(object : PayListener {
        override fun onEvent(event: PayEvent) { trySend(event) }   // never blocks the SDK thread
        override fun onError(error: Throwable) { close(error) }    // the flow fails with this error
        override fun onClosed() { close() }                        // the flow completes normally
    })
    awaitClose { registration.unregister() }                       // on cancel, close and error
}

private fun DemoGateway.eventsWithoutAwaitClose(): Flow<PayEvent> = callbackFlow {
    register(object : PayListener {
        override fun onEvent(event: PayEvent) { trySend(event) }
        override fun onError(error: Throwable) { close(error) }
        override fun onClosed() { close() }
    })
    // forgot awaitClose
}

private suspend fun DemoGateway.awaitRegistered() { while (listeners.isEmpty()) yield() }

fun main() = runBlocking {
    println("== 0. fire right after launch: is the listener there yet?")
    val gw0 = DemoGateway()
    val j0 = launch { gw0.events().collect { println("  got $it") } }
    yield()
    gw0.fire(PayEvent("p-0", "AUTHORIZED"))
    println("  fired with listeners=${gw0.listeners.size}")
    yield()                  // give the collector a turn to print what it got
    j0.cancelAndJoin()

    println("== 1. callbackFlow without awaitClose")
    try { DemoGateway().eventsWithoutAwaitClose().collect { } }
    catch (e: IllegalStateException) { println("  ${e::class.qualifiedName}: ${e.message}") }

    println("== 2. take(2) ends the collection, and awaitClose unregisters")
    val gw = DemoGateway()
    val j2 = launch { println("  got " + gw.events().take(2).toList()) }
    gw.awaitRegistered()
    gw.fire(PayEvent("p-1", "AUTHORIZED")); gw.fire(PayEvent("p-1", "CAPTURED")); gw.fire(PayEvent("p-1", "SETTLED"))
    j2.join()

    println("== 3. the SDK reports an error: close(cause) fails the flow")
    val gw3 = DemoGateway()
    val j3 = launch {
        try { gw3.events().collect { println("  got $it") } }
        catch (e: IOException) { println("  collector caught ${e::class.simpleName}: ${e.message}") }
    }
    gw3.awaitRegistered(); gw3.fire(PayEvent("p-2", "AUTHORIZED")); yield()
    gw3.fail(IOException("gateway connection lost")); j3.join()

    println("== 4. the SDK says it is done: close() completes the flow")
    val gw4 = DemoGateway()
    val j4 = launch { println("  completed with " + gw4.events().toList()) }
    gw4.awaitRegistered(); gw4.fire(PayEvent("p-3", "REFUNDED")); gw4.close(); j4.join()

    println("== 5. trySend after the channel is closed")
    val ch = Channel<Int>(1); ch.close()
    val r = ch.trySend(1)
    println("  isSuccess=${r.isSuccess} isClosed=${r.isClosed} result=$r")
}
