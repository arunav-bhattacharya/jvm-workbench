package workbench.coroutines.l02

import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlin.system.measureTimeMillis

private suspend fun quote(provider: String, latencyMs: Long): String {
    delay(latencyMs) // stands in for a network call
    return "$provider:${latencyMs}ms"
}

private val latencies = listOf("northbank" to 300L, "fjord-fx" to 120L, "tidewater" to 200L)

suspend fun sequential(): List<String> =
    latencies.map { (p, ms) -> quote(p, ms) }

suspend fun concurrent(): List<String> = coroutineScope {
    latencies.map { (p, ms) -> async { quote(p, ms) } }.awaitAll()
}

fun main() = runBlocking {
    var result: List<String>
    val t1 = measureTimeMillis { result = sequential() }
    println("sequential: $result in $t1 ms")
    val t2 = measureTimeMillis { result = concurrent() }
    println("concurrent: $result in $t2 ms")
}
