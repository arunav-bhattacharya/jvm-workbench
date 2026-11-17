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

// One order, five dishes, and how long each one cooks.
private val cookingMs = mapOf("soup" to 300L, "salad" to 100L, "roast" to 200L, "bread" to 50L, "pie" to 150L)
private var onBurners = 0
private var mostOnBurners = 0

private suspend fun cook(dish: String): String {
    onBurners++; mostOnBurners = maxOf(mostOnBurners, onBurners)
    log("    start cooking $dish (on the burners: $onBurners)")
    try { delay(cookingMs.getValue(dish)); return "$dish:plate" } finally { onBurners-- }
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

private fun scenario(title: String, plates: (Flow<String>) -> Flow<String>) = runTest {
    println("== $title")
    mostOnBurners = 0
    plates(cookingMs.keys.asFlow()).collect { log("collector got $it") }
    log("done, most on the burners = $mostOnBurners")
}

fun main() {
    println("DEFAULT_CONCURRENCY = $DEFAULT_CONCURRENCY")
    scenario("flatMapMerge(2): the cooking is INSIDE the returned flow") { dishes ->
        dishes.flatMapMerge(concurrency = 2) { d -> log("  lambda called for $d"); flow { emit(cook(d)) } }
    }
    scenario("flatMapMerge(2): the cooking is IN the lambda") { dishes ->
        dishes.flatMapMerge(concurrency = 2) { d -> val plate = cook(d); flowOf(plate) }
    }
    scenario("mergeLanes(2), the hand-made version") { dishes ->
        dishes.mergeLanes(2) { d -> log("  lambda called for $d"); flow { emit(cook(d)) } }
    }
}
