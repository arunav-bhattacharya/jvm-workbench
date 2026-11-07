package workbench.coroutines.l09

import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.buffer
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.flow.conflate
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.runBlocking
import kotlin.system.measureTimeMillis

/** Three FX ticks, 100 ms apart. */
fun ticks(): Flow<Int> = flow {
    for (i in 1..3) { delay(100); emit(i) }
}

fun main() = runBlocking {
    // the collector takes 300 ms per tick (pricing a quote book)
    val plain = measureTimeMillis { ticks().collect { delay(300); print("$it ") } }
    println(" plain:         $plain ms")
    val buffered = measureTimeMillis { ticks().buffer().collect { delay(300); print("$it ") } }
    println(" buffer():      $buffered ms")
    val conflated = measureTimeMillis { ticks().conflate().collect { delay(300); print("$it ") } }
    println(" conflate():    $conflated ms")
    val latest = measureTimeMillis {
        ticks().collectLatest { print("start $it, "); delay(300); print("done $it ") }
    }
    println(" collectLatest: $latest ms")
}
