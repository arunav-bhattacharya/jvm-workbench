package workbench.flows.l08

import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.reactor.asFlux
import reactor.core.publisher.Flux

class GatewayApi(private val gateway: FakeGateway) {

    fun events(): Flow<GatewayEvent> = gateway.events()

    // Reactor demand becomes suspension: the flow starts at the first request(n), each emit
    // calls onNext, and a cancelled subscription cancels the flow, so awaitClose unregisters
    fun eventsFlux(): Flux<GatewayEvent> = gateway.events().asFlux()
}
