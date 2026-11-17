package workbench.functional.l07.demo

import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlin.coroutines.cancellation.CancellationException

fun main() = runBlocking<Unit> {
    println("1. runCatching around a suspend call, cancelled after 50 ms:")
    val placed = mutableListOf<String>()
    val swallowing = launch {
        val r = runCatching { delay(1_000); "basket-1" }          // waiting for the shop to answer
        println("  runCatching returned: isFailure=${r.isFailure} ex=${r.exceptionOrNull()?.javaClass?.simpleName}")
        println("  isActive after swallow = $isActive")
        placed += "placed the order"
        println("  placing the order anyway (code with no suspension point keeps running)")
        try {
            delay(1)
        } catch (e: CancellationException) {
            println("  next suspension point throws: ${e.javaClass.simpleName}")
            throw e
        }
    }
    delay(50)
    swallowing.cancelAndJoin()
    println("  orders: $placed")

    println("2. the same, with CancellationException rethrown:")
    val placed2 = mutableListOf<String>()
    val rethrowing = launch {
        val r = runCatching { delay(1_000); "basket-1" }.onFailure { if (it is CancellationException) throw it }
        placed2 += "placed the order ($r)"
    }
    delay(50)
    rethrowing.cancelAndJoin()
    println("  cancelled=${rethrowing.isCancelled}, orders: $placed2")

    println("3. map rethrows, mapCatching captures:")
    val parsed = runCatching { "12".toInt() }
    println("  mapCatching: ${parsed.mapCatching { error("boom") }}")
    try {
        parsed.map { error("boom") }
    } catch (e: IllegalStateException) {
        println("  map threw: IllegalStateException: ${e.message}")
    }
}
