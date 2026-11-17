package workbench.coroutines.l09

import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow

/**
 * The probe's readings as a Flow. Registers a listener when collection starts, and unregisters
 * it when the collector stops (finishes, fails or is cancelled), so no listener is left behind.
 * The probe calls the listener on its own thread; never block that thread for long.
 *
 * Bug: the block returns straight after registering, so callbackFlow throws
 * IllegalStateException, and the listener is never unregistered.
 */
fun OvenProbe.readings(): Flow<Reading> = callbackFlow {
    register { reading -> trySend(reading) }
}
