package workbench.coroutines.l02

import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlin.system.measureTimeMillis

private suspend fun price(grocer: String, latencyMs: Long): String {
    delay(latencyMs) // stands in for a text message and its reply
    return "$grocer:${latencyMs}ms"
}

private val latencies = listOf("greengrocer" to 300L, "market" to 120L, "farm-stand" to 200L)

suspend fun sequential(): List<String> =
    latencies.map { (g, ms) -> price(g, ms) }

suspend fun concurrent(): List<String> = coroutineScope {
    latencies.map { (g, ms) -> async { price(g, ms) } }.awaitAll()
}

fun main() = runBlocking {
    var result: List<String>
    val t1 = measureTimeMillis { result = sequential() }
    println("sequential: $result in $t1 ms")
    val t2 = measureTimeMillis { result = concurrent() }
    println("concurrent: $result in $t2 ms")
}
