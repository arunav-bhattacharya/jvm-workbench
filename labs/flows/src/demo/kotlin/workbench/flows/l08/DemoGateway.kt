package workbench.flows.l08

import java.util.concurrent.CopyOnWriteArrayList

// A made-up payment-gateway SDK with a listener API, used by the demos of this lesson.
data class PayEvent(val paymentId: String, val status: String)

interface PayListener {
    fun onEvent(event: PayEvent)
    fun onError(error: Throwable)
    fun onClosed()
}

fun interface PayRegistration {
    fun unregister()
}

class DemoGateway {
    val listeners = CopyOnWriteArrayList<PayListener>()

    fun register(listener: PayListener): PayRegistration {
        listeners += listener
        println("    [gateway] registered (listeners=${listeners.size})")
        return PayRegistration { listeners -= listener; println("    [gateway] unregistered (listeners=${listeners.size})") }
    }

    fun fire(event: PayEvent) = listeners.forEach { it.onEvent(event) }
    fun fail(error: Throwable) = listeners.forEach { it.onError(error) }
    fun close() = listeners.forEach { it.onClosed() }
}
