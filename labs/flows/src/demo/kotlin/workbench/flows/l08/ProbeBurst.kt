package workbench.flows.l08

import kotlinx.coroutines.channels.BufferOverflow
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.channels.trySendBlocking
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.buffer
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.flow.conflate
import kotlinx.coroutines.flow.count
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.flow.take
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.runBlocking
import kotlin.concurrent.thread

// 200 synchronous callbacks inside the block, while the collector already waits in receive().
private fun burst(n: Int): Flow<Int> = callbackFlow {
    var failed = 0
    repeat(n) { if (trySend(it).isFailure) failed++ }
    println("    trySend failures: $failed of $n")
    awaitClose { }
}

// A probe library that pushes 200 readings from its own thread as fast as it can. REAL time.
private fun probeThread(blocking: Boolean): Flow<Int> = callbackFlow {
    var failed = 0
    val probe = thread(name = "probe-io") {
        val t0 = System.nanoTime()
        repeat(200) { if (blocking) trySendBlocking(it) else if (trySend(it).isFailure) failed++ }
        println("    probe thread done after ${(System.nanoTime() - t0) / 1_000_000} ms, trySend failures=$failed")
        channel.close()
    }
    awaitClose { probe.join() }
}

fun main() = runBlocking {
    println("== 1. a burst of 200 callbacks before the collector can run")
    println("  default buffer (64, SUSPEND):"); println("    collector got ${burst(200).take(64).count()}, then cancelled")
    println("  buffer(Channel.UNLIMITED):"); println("    collector got ${burst(200).buffer(Channel.UNLIMITED).take(200).count()}")
    println("  conflate():"); println("    collector got ${burst(200).conflate().take(2).toList()}")
    println("  buffer(10, DROP_OLDEST):"); println("    collector got ${burst(200).buffer(10, BufferOverflow.DROP_OLDEST).take(11).toList()}")

    println("== 2. the probe's own thread, collector takes 2 ms per reading (REAL time, numbers vary)")
    for (blocking in listOf(false, true)) {
        println("  ${if (blocking) "trySendBlocking" else "trySend"} into the default buffer:")
        println("    collector received ${probeThread(blocking).onEach { delay(2) }.count()}")
    }
}
