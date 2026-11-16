package workbench.flows.l08

import kotlinx.coroutines.flow.Flow
import reactor.core.publisher.Flux

/**
 * The gateway events for Kotlin and for Java callers. Java can't call a suspend `collect`,
 * so it gets a Flux.
 */
class GatewayApi(private val gateway: FakeGateway) {

    /** For Kotlin callers. */
    fun events(): Flow<GatewayEvent> = gateway.events()

    /**
     * For Java and Reactor callers: the same events as a Flux. Each subscription registers its
     * own listener once it requests items, and cancelling the subscription (`take`, `dispose`)
     * unregisters it.
     */
    fun eventsFlux(): Flux<GatewayEvent> = TODO("hand the same flow to Java as a Flux")
}
