@file:OptIn(ExperimentalCoroutinesApi::class, FlowPreview::class)

package workbench.flows.l05

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.FlowPreview
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.DEFAULT_CONCURRENCY
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.asFlow
import kotlinx.coroutines.flow.channelFlow
import kotlinx.coroutines.flow.flatMapMerge
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Semaphore
import kotlinx.coroutines.test.TestCoroutineScheduler
import kotlinx.coroutines.test.runTest

private suspend fun now() = currentCoroutineContext()[TestCoroutineScheduler]!!.currentTime
private suspend fun log(msg: String) = println("%5d ms  %s".format(now(), msg))

private val latencyMs = mapOf("m1" to 300L, "m2" to 100L, "m3" to 200L, "m4" to 50L, "m5" to 150L)
private var inFlight = 0
private var maxInFlight = 0

private suspend fun feeLookup(merchant: String): String {
    inFlight++; maxInFlight = maxOf(maxInFlight, inFlight)
    log("    start lookup $merchant (in flight: $inFlight)")
    try { delay(latencyMs.getValue(merchant)); return "$merchant:fee" } finally { inFlight-- }
}

// flatMapMerge, built by hand: one coroutine runs the lambda per value, a semaphore caps the lanes,
// and each lane is its own coroutine sending into one shared channel.
private fun <T, R> Flow<T>.mergeLanes(lanes: Int, transform: suspend (T) -> Flow<R>): Flow<R> = channelFlow {
    val permits = Semaphore(lanes)
    collect { value ->
        val inner = transform(value)          // runs here, one value at a time
        permits.acquire()                     // wait for a free lane
        launch { try { inner.collect { send(it) } } finally { permits.release() } }
    }
}

private fun scenario(title: String, fees: (Flow<String>) -> Flow<String>) = runTest {
    println("== $title")
    maxInFlight = 0
    fees(latencyMs.keys.asFlow()).collect { log("collector got $it") }
    log("done, max in flight = $maxInFlight")
}

fun main() {
    println("DEFAULT_CONCURRENCY = $DEFAULT_CONCURRENCY")
    scenario("flatMapMerge(2): the lookup is INSIDE the returned flow") { merchants ->
        merchants.flatMapMerge(concurrency = 2) { m -> log("  lambda called for $m"); flow { emit(feeLookup(m)) } }
    }
    scenario("flatMapMerge(2): the lookup is IN the lambda") { merchants ->
        merchants.flatMapMerge(concurrency = 2) { m -> val fee = feeLookup(m); flowOf(fee) }
    }
    scenario("mergeLanes(2), the hand-made version") { merchants ->
        merchants.mergeLanes(2) { m -> log("  lambda called for $m"); flow { emit(feeLookup(m)) } }
    }
}
