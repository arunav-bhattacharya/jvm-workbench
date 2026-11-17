package workbench.flows.l08

import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.reactor.asFlux
import reactor.core.publisher.Flux

class ProbeApi(private val probe: FakeProbe) {

    fun readings(): Flow<ProbeReading> = probe.readings()

    // Reactor demand becomes suspension: the flow starts at the first request(n), each emit
    // calls onNext, and a cancelled subscription cancels the flow, so awaitClose unregisters
    fun readingsFlux(): Flux<ProbeReading> = probe.readings().asFlux()
}
