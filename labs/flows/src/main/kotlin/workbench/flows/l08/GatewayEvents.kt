package workbench.flows.l08

import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow

/**
 * The gateway's events as a cold Flow. Each collector registers its own listener when it starts
 * collecting, and unregisters it when it stops for any reason: `take(n)`, cancellation, an SDK
 * error or the SDK closing.
 *
 * - `onEvent`: deliver every event, in order. The SDK calls it on its own thread, and that thread
 *   must never block.
 * - On connect the SDK replays up to 500 pending events in one synchronous burst (see
 *   [FakeGateway.burst]). None of them may be lost, even if the collector is slow to start.
 * - `onError(e)`: the flow fails with `e`.
 * - `onClosed()`: the flow completes normally.
 *
 * Bug: a teammate's first version. Collecting it throws, and it ignores errors and close.
 */
fun FakeGateway.events(): Flow<GatewayEvent> = callbackFlow {
    register(object : GatewayListener {
        override fun onEvent(event: GatewayEvent) {
            trySend(event)
        }
        override fun onError(error: Throwable) {}
        override fun onClosed() {}
    })
}
