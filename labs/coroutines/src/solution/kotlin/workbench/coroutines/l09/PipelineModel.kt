package workbench.coroutines.l09

// Shared model. This file is the same in src/main and src/solution.

data class PaymentEvent(val paymentId: String, val type: String)

/** A handle for one registered listener. */
fun interface Registration {
    fun unregister()
}

/**
 * A legacy in-process event bus. It calls each listener on its own thread, as events happen,
 * and keeps calling it until the listener is unregistered.
 */
interface PaymentEventBus {
    fun register(listener: (PaymentEvent) -> Unit): Registration
}

data class Quote(val acquirer: String, val feeBasisPoints: Int)
