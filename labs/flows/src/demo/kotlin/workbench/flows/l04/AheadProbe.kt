package workbench.flows.l04

import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.channels.consumeEach
import kotlinx.coroutines.channels.produce
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.buffer
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

// The diner's phone rings with dumpling 1 on the plate. How far does the cook get meanwhile?
private suspend fun probe(label: String, op: (Flow<Int>) -> Flow<Int>) = coroutineScope {
    var returned = 0                                    // emits that have returned in the cook's loop
    val callEnds = CompletableDeferred<Unit>()
    val eaten = mutableListOf<Int>()
    val cook = flow { for (dumpling in 1..200) { emit(dumpling); returned = dumpling } }
    val diner = launch { op(cook).collect { eaten += it; if (eaten.size == 1) callEnds.await() } }
    delay(100)                                          // let the cook go as far as she can
    val ahead = returned
    callEnds.complete(Unit); diner.join()
    println("%-22s emits returned while the diner held dumpling 1: %3d   eaten: %d".format(label, ahead, eaten.size))
}

// The buffer KDoc's own sketch of what buffer(n) does: a second coroutine and a channel.
@OptIn(ExperimentalCoroutinesApi::class)
private fun <T> Flow<T>.handMadeBuffer(n: Int): Flow<T> = flow {
    coroutineScope {
        val channel = produce(capacity = n) { collect { send(it) } }
        channel.consumeEach { emit(it) }
    }
}

fun main(args: Array<String>) {
    // -Pargs=8 sets the JVM-wide default size of a BUFFERED channel before anything reads it
    args.firstOrNull()?.let { System.setProperty("kotlinx.coroutines.channels.defaultBuffer", it) }
    runBlocking {
        probe("plain") { it }
        probe("buffer(0)") { it.buffer(0) }
        probe("buffer(1)") { it.buffer(1) }
        probe("buffer(10)") { it.buffer(10) }
        probe("handMadeBuffer(10)") { it.handMadeBuffer(10) }
        probe("buffer()") { it.buffer() }
        probe("buffer(UNLIMITED)") { it.buffer(Channel.UNLIMITED) }
    }
}
