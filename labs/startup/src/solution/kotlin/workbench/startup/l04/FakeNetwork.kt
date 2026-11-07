package workbench.startup.l04

import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.atomic.AtomicInteger

/** A connection. [id] is unique per network, so a reconnected socket is visibly a new one. Don't change it. */
class FakeSocket(val peer: String, val id: Int) {
    @Volatile
    var isOpen = true
        private set

    fun close() {
        isOpen = false
    }

    override fun toString() = "FakeSocket#$id($peer, ${if (isOpen) "open" else "closed"})"
}

/** Hands out sockets and remembers them, so a checkpoint can check that none is still open. Don't change it. */
class FakeNetwork {
    private val ids = AtomicInteger()
    private val all = CopyOnWriteArrayList<FakeSocket>()

    fun open(peer: String): FakeSocket = FakeSocket(peer, ids.incrementAndGet()).also { all += it }

    fun openSockets(): List<FakeSocket> = all.filter { it.isOpen }
}
