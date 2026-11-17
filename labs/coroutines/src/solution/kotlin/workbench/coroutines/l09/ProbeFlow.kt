package workbench.coroutines.l09

import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow

fun OvenProbe.readings(): Flow<Reading> = callbackFlow {
    // trySend never blocks the probe's thread; with the default buffer (64) it fails only if
    // the collector has fallen 64 readings behind
    val registration = register { reading -> trySend(reading) }
    // suspend here until the collector stops, then clean up
    awaitClose { registration.unregister() }
}
