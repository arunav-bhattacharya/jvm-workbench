package workbench.flows.l04

import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.channels.BufferOverflow.DROP_LATEST
import kotlinx.coroutines.channels.BufferOverflow.DROP_OLDEST
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.buffer
import kotlinx.coroutines.flow.conflate
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

// 200 FX ticks arrive while the repricer is stuck on tick 1. Which ticks does it see afterwards?
private suspend fun policy(label: String, op: (Flow<Int>) -> Flow<Int>) = coroutineScope {
    val unstuck = CompletableDeferred<Unit>()
    val seen = mutableListOf<Int>()
    val ticks = flow { for (tick in 1..200) emit(tick) }
    val repricer = launch { op(ticks).collect { seen += it; if (seen.size == 1) unstuck.await() } }
    delay(100)
    unstuck.complete(Unit); repricer.join()
    val shown = if (seen.size > 6) "${seen.take(3)} ... ${seen.takeLast(2)}" else "$seen"
    println("%-40s saw %3d ticks: %s".format(label, seen.size, shown))
}

fun main() = runBlocking {
    policy("buffer(10)                  SUSPEND") { it.buffer(10) }
    policy("buffer(10, DROP_OLDEST)") { it.buffer(10, DROP_OLDEST) }
    policy("buffer(10, DROP_LATEST)") { it.buffer(10, DROP_LATEST) }
    policy("conflate()") { it.conflate() }
    policy("buffer(onBufferOverflow = DROP_OLDEST)") { it.buffer(onBufferOverflow = DROP_OLDEST) }
    policy("buffer(0, DROP_LATEST)") { it.buffer(0, DROP_LATEST) }
}
