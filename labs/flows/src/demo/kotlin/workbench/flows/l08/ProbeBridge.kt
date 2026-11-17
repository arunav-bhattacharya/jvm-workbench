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

// The probe's listener API as a Flow.
fun DemoProbe.events(): Flow<ProbeEvent> = callbackFlow {
    val registration = register(object : ProbeEventListener {
        override fun onEvent(event: ProbeEvent) { trySend(event) } // never blocks the probe's thread
        override fun onError(error: Throwable) { close(error) }    // the flow fails with this error
        override fun onClosed() { close() }                        // the flow completes normally
    })
    awaitClose { registration.unregister() }                       // on cancel, close and error
}

private fun DemoProbe.eventsWithoutAwaitClose(): Flow<ProbeEvent> = callbackFlow {
    register(object : ProbeEventListener {
        override fun onEvent(event: ProbeEvent) { trySend(event) }
        override fun onError(error: Throwable) { close(error) }
        override fun onClosed() { close() }
    })
    // forgot awaitClose
}

private suspend fun DemoProbe.awaitRegistered() { while (listeners.isEmpty()) yield() }

fun main() = runBlocking {
    println("== 0. fire right after launch: is the listener there yet?")
    val probe0 = DemoProbe()
    val j0 = launch { probe0.events().collect { println("  got $it") } }
    yield()
    probe0.fire(ProbeEvent(0, 61))
    println("  fired with listeners=${probe0.listeners.size}")
    yield()                  // give the collector a turn to print what it got
    j0.cancelAndJoin()

    println("== 1. callbackFlow without awaitClose")
    try { DemoProbe().eventsWithoutAwaitClose().collect { } }
    catch (e: IllegalStateException) { println("  ${e::class.qualifiedName}: ${e.message}") }

    println("== 2. take(2) ends the collection, and awaitClose unregisters")
    val probe = DemoProbe()
    val j2 = launch { println("  got " + probe.events().take(2).toList()) }
    probe.awaitRegistered()
    probe.fire(ProbeEvent(1, 62)); probe.fire(ProbeEvent(2, 63)); probe.fire(ProbeEvent(3, 64))
    j2.join()

    println("== 3. the probe reports an error: close(cause) fails the flow")
    val probe3 = DemoProbe()
    val j3 = launch {
        try { probe3.events().collect { println("  got $it") } }
        catch (e: IOException) { println("  collector caught ${e::class.simpleName}: ${e.message}") }
    }
    probe3.awaitRegistered(); probe3.fire(ProbeEvent(4, 65)); yield()
    probe3.fail(IOException("probe connection lost")); j3.join()

    println("== 4. the probe says it is done: close() completes the flow")
    val probe4 = DemoProbe()
    val j4 = launch { println("  completed with " + probe4.events().toList()) }
    probe4.awaitRegistered(); probe4.fire(ProbeEvent(5, 66)); probe4.close(); j4.join()

    println("== 5. trySend after the channel is closed")
    val ch = Channel<Int>(1); ch.close()
    val r = ch.trySend(1)
    println("  isSuccess=${r.isSuccess} isClosed=${r.isClosed} result=$r")
}
