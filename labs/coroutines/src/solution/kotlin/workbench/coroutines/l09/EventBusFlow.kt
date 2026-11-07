package workbench.coroutines.l09

import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow

fun PaymentEventBus.events(): Flow<PaymentEvent> = callbackFlow {
    // trySend never blocks the bus's thread; with the default buffer (64) it fails only if
    // the collector has fallen 64 events behind
    val registration = register { event -> trySend(event) }
    // suspend here until the collector stops, then clean up
    awaitClose { registration.unregister() }
}
