package workbench.flows.l08

import kotlinx.coroutines.flow.Flow
import reactor.core.publisher.Flux

/**
 * The probe's readings for Kotlin and for Java callers. Java can't call a suspend `collect`,
 * so it gets a Flux.
 */
class ProbeApi(private val probe: FakeProbe) {

    /** For Kotlin callers. */
    fun readings(): Flow<ProbeReading> = probe.readings()

    /**
     * For Java and Reactor callers: the same readings as a Flux. Each subscription registers its
     * own listener once it requests items, and cancelling the subscription (`take`, `dispose`)
     * unregisters it.
     */
    fun readingsFlux(): Flux<ProbeReading> = TODO("hand the same flow to Java as a Flux")
}
