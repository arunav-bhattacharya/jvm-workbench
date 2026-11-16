package workbench.flows.l04

import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.buffer
import kotlinx.coroutines.flow.conflate
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

// toString() of a channel flow shows its configuration. It is a debug aid, not an API.
private fun sticker(f: Flow<*>) = f.toString().substringAfterLast(" -> ").replace(Regex("@[0-9a-f]+"), "")

private suspend fun fused(label: String, op: (Flow<Int>) -> Flow<Int>) = coroutineScope {
    var returned = 0
    val gate = CompletableDeferred<Unit>()
    val got = mutableListOf<Int>()
    val src = flow { for (i in 1..200) { emit(i); returned = i } }
    val job = launch { op(src).collect { got += it; if (got.size == 1) gate.await() } }
    delay(100)
    val ahead = returned
    gate.complete(Unit); job.join()
    println("%-24s %-66s ahead %3d, received %3d".format(label, sticker(op(src)), ahead, got.size))
}

fun main() = runBlocking {
    fused("buffer()") { it.buffer() }
    fused("buffer().buffer()") { it.buffer().buffer() }
    fused("buffer(10).buffer(20)") { it.buffer(10).buffer(20) }
    fused("buffer(10).conflate()") { it.buffer(10).conflate() }
    fused("conflate().buffer(10)") { it.conflate().buffer(10) }
    fused("buffer(5).flowOn(IO)") { it.buffer(5).flowOn(Dispatchers.IO) }
}
