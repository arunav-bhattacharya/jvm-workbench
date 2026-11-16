package workbench.flows.l08

import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.buffer
import kotlinx.coroutines.flow.callbackFlow

fun FakeGateway.events(): Flow<GatewayEvent> = callbackFlow {
    val registration = register(object : GatewayListener {
        override fun onEvent(event: GatewayEvent) {
            trySend(event)                 // never blocks the SDK thread; the buffer below holds the burst
        }
        override fun onError(error: Throwable) {
            close(error)                   // the collector's collect throws this error
        }
        override fun onClosed() {
            close()                        // the flow completes after the buffered events
        }
    })
    awaitClose { registration.unregister() } // runs on take(n), cancellation, error and close
}.buffer(500) // fused into callbackFlow's own channel: room for the documented 500-event burst
