package workbench.functional.l07

import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlin.coroutines.cancellation.CancellationException

fun main() = runBlocking<Unit> {
    println("1. runCatching around a suspend call, cancelled after 50 ms:")
    val ledger = mutableListOf<String>()
    val swallowing = launch {
        val r = runCatching { delay(1_000); "auth-1" }
        println("  runCatching returned: isFailure=${r.isFailure} ex=${r.exceptionOrNull()?.javaClass?.simpleName}")
        println("  isActive after swallow = $isActive")
        ledger += "charged card"
        println("  charging card anyway (code with no suspension point keeps running)")
        try {
            delay(1)
        } catch (e: CancellationException) {
            println("  next suspension point throws: ${e.javaClass.simpleName}")
            throw e
        }
    }
    delay(50)
    swallowing.cancelAndJoin()
    println("  ledger: $ledger")

    println("2. the same, with CancellationException rethrown:")
    val ledger2 = mutableListOf<String>()
    val rethrowing = launch {
        val r = runCatching { delay(1_000); "auth-1" }.onFailure { if (it is CancellationException) throw it }
        ledger2 += "charged card ($r)"
    }
    delay(50)
    rethrowing.cancelAndJoin()
    println("  cancelled=${rethrowing.isCancelled}, ledger: $ledger2")

    println("3. map rethrows, mapCatching captures:")
    val parsed = runCatching { "12".toLong() }
    println("  mapCatching: ${parsed.mapCatching { error("boom") }}")
    try {
        parsed.map { error("boom") }
    } catch (e: IllegalStateException) {
        println("  map threw: IllegalStateException: ${e.message}")
    }
}
