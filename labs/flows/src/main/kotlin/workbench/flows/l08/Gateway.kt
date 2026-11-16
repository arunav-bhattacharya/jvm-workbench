package workbench.flows.l08

import java.util.concurrent.CopyOnWriteArrayList

/** One event from the card gateway, for example p-42 CAPTURED. */
data class GatewayEvent(val paymentId: String, val status: String)

/** What the gateway SDK calls back. It may call it on any of its own threads. */
interface GatewayListener {
    fun onEvent(event: GatewayEvent)
    fun onError(error: Throwable)
    fun onClosed()
}

/** Returned by [FakeGateway.register]. Call [unregister] to stop the callbacks. */
fun interface Registration {
    fun unregister()
}

/**
 * A made-up gateway SDK that tests drive by hand. Register and unregister are thread-safe,
 * and every callback runs on the thread that calls [fire], [fail], [close] or [burst].
 */
class FakeGateway {
    private val listeners = CopyOnWriteArrayList<GatewayListener>()

    val listenerCount: Int get() = listeners.size

    fun register(listener: GatewayListener): Registration {
        listeners += listener
        return Registration { listeners -= listener }
    }

    fun fire(event: GatewayEvent) = listeners.forEach { it.onEvent(event) }
    fun fail(error: Throwable) = listeners.forEach { it.onError(error) }
    fun close() = listeners.forEach { it.onClosed() }

    /** On connect the real SDK replays the pending events in one synchronous burst, like this. */
    fun burst(count: Int) = repeat(count) { fire(GatewayEvent("p-$it", "PENDING_REPLAY")) }
}
