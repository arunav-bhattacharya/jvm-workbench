package workbench.coroutines.l08

import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.channels.BufferOverflow
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

/** Emits five events with tryEmit while one subscriber is busy, and reports what got through. */
suspend fun tryFive(label: String, events: MutableSharedFlow<String>) = kotlinx.coroutines.coroutineScope {
    val received = mutableListOf<String>()
    val auditor = launch(start = CoroutineStart.UNDISPATCHED) {
        events.collect { delay(50); received += it } // the audit write takes 50 ms
    }
    val accepted = (1..5).map { events.tryEmit("e$it") }
    delay(400)
    auditor.cancel()
    println("%-40s tryEmit: %s  received: %s".format(label, accepted, received))
}

fun main() = runBlocking {
    tryFive("default (no replay, no buffer)", MutableSharedFlow())
    tryFive("extraBufferCapacity = 2", MutableSharedFlow(extraBufferCapacity = 2))
    tryFive("extraBufferCapacity = 2, DROP_OLDEST", MutableSharedFlow(extraBufferCapacity = 2, onBufferOverflow = BufferOverflow.DROP_OLDEST))
    tryFive("extraBufferCapacity = 64", MutableSharedFlow(extraBufferCapacity = 64))

    // replay: what a subscriber that arrives later gets first
    val replayed = MutableSharedFlow<String>(replay = 2)
    (1..5).forEach { replayed.emit("e$it") } // no subscribers yet
    println("a late subscriber to replay = 2 first gets: ${replayed.replayCache}")
}
