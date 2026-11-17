package workbench.flows.l08

import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow

/**
 * The probe's readings as a cold Flow. Each collector registers its own listener when it starts
 * collecting, and unregisters it when it stops for any reason: `take(n)`, cancellation, a probe
 * error or the probe closing.
 *
 * - `onReading`: deliver every reading, in order. The probe calls it on its own thread, and that
 *   thread must never block.
 * - On connect the probe replays up to 500 stored readings in one synchronous burst (see
 *   [FakeProbe.burst]). None of them may be lost, even if the collector is slow to start.
 * - `onError(e)`: the flow fails with `e`.
 * - `onClosed()`: the flow completes normally.
 *
 * Bug: a helper's first version. Collecting it throws, and it ignores errors and close.
 */
fun FakeProbe.readings(): Flow<ProbeReading> = callbackFlow {
    register(object : ProbeListener {
        override fun onReading(reading: ProbeReading) {
            trySend(reading)
        }
        override fun onError(error: Throwable) {}
        override fun onClosed() {}
    })
}
