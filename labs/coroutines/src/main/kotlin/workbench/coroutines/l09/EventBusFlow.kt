package workbench.coroutines.l09

import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow

/**
 * The bus's events as a Flow. Registers a listener when collection starts, and unregisters it
 * when the collector stops (finishes, fails or is cancelled), so no listener leaks.
 * The bus calls the listener on its own thread; never block that thread for long.
 *
 * Bug: the block returns straight after registering, so callbackFlow throws
 * IllegalStateException, and the listener is never unregistered.
 */
fun PaymentEventBus.events(): Flow<PaymentEvent> = callbackFlow {
    register { event -> trySend(event) }
}
