package workbench.flows.l08

import app.cash.turbine.test
import app.cash.turbine.turbineScope
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.launch
import kotlinx.coroutines.reactor.asFlux
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import reactor.core.publisher.Flux
import java.io.IOException
import kotlin.time.Duration.Companion.milliseconds
import kotlin.time.Duration.Companion.seconds

/** A payment whose status is set twice in a row, with no suspension in between. */
class TourTracker {
    private val _status = MutableStateFlow("PENDING")
    val status: StateFlow<String> = _status.asStateFlow()
    fun authorizeAndCapture() { _status.value = "AUTHORIZED"; _status.value = "CAPTURED" }
    fun statusFlux(): Flux<String> = status.asFlux()   // for the Java twin, StepVerifierTourTest
}

/**
 * The Try it for Turbine in lesson 8 (not part of the lab): what Turbine sees, and what it hides.
 * Every test passes. Read each one, predict the commented line, then run the class.
 */
@OptIn(ExperimentalCoroutinesApi::class) // TestScope.runCurrent is experimental in 1.11.0
class TurbineTourTest {

    @Test
    fun `1 items and completion are awaited in order`() = runTest {
        flowOf("AUTHORIZED", "CAPTURED").test {
            assertThat(awaitItem()).isEqualTo("AUTHORIZED")
            assertThat(awaitItem()).isEqualTo("CAPTURED")
            awaitComplete()
        }
    }

    @Test
    fun `2 an event you did not read fails the test`() = runTest {
        val failure = runCatching { flowOf("one", "two").test { awaitItem() } }.exceptionOrNull()
        assertThat(failure).hasMessageContaining("Unconsumed events found") // lists Item(two) and Complete
    }

    @Test
    fun `3 an error arrives as an event, not as a thrown exception`() = runTest {
        flow { emit(1); throw IOException("issuer 503") }.test {
            assertThat(awaitItem()).isEqualTo(1)
            assertThat(awaitError()).hasMessage("issuer 503")
        }
    }

    @Test
    fun `4 Turbine sees every StateFlow value, a Standard collector does not`() = runTest {
        val tracker = TourTracker()
        tracker.status.test {
            assertThat(awaitItem()).isEqualTo("PENDING")
            tracker.authorizeAndCapture()
            assertThat(awaitItem()).isEqualTo("AUTHORIZED") // Turbine collects on UnconfinedTestDispatcher
            assertThat(awaitItem()).isEqualTo("CAPTURED")
        }
        val other = TourTracker()
        val seen = mutableListOf<String>()
        backgroundScope.launch { other.status.toList(seen) } // StandardTestDispatcher, closer to production
        runCurrent()
        other.authorizeAndCapture()
        runCurrent()
        assertThat(seen).containsExactly("PENDING", "CAPTURED")
    }

    @Test
    fun `5 Turbine never lets a callbackFlow buffer fill`() = runTest {
        val gw = FakeGateway()
        val defaultBuffer: Flow<GatewayEvent> = callbackFlow { // 64 slots, as callbackFlow has by default
            val r = gw.register(object : GatewayListener {
                override fun onEvent(event: GatewayEvent) { trySend(event) }
                override fun onError(error: Throwable) { close(error) }
                override fun onClosed() { close() }
            })
            awaitClose { r.unregister() }
        }
        defaultBuffer.test {
            gw.burst(500)
            repeat(500) { awaitItem() } // all 500 arrive: each one was taken the moment it was sent
            cancelAndIgnoreRemainingEvents()
        }
        val seen = mutableListOf<GatewayEvent>()
        backgroundScope.launch { defaultBuffer.collect { seen += it } }
        runCurrent()
        gw.burst(500)
        runCurrent()
        assertThat(seen).hasSize(65) // a Standard collector: 64 buffered plus 1 handed straight over
    }

    @Test
    fun `6 a SharedFlow value emitted before test {} is lost`() = runTest {
        val events = MutableSharedFlow<String>()
        events.emit("AUTHORIZED") // nobody is subscribed yet, and replay = 0
        val failure = runCatching { events.test(timeout = 500.milliseconds) { awaitItem() } }.exceptionOrNull()
        assertThat(failure).hasMessage("No value produced in 500ms") // after 500 ms of REAL time
    }

    @Test
    fun `7 the flow's delays are virtual, Turbine's timeout is wall-clock`() = runTest {
        flow { delay(10.seconds); emit("late") }.test(timeout = 200.milliseconds) {
            assertThat(awaitItem()).isEqualTo("late")
            awaitComplete()
        }
    }

    @Test
    fun `8 several flows at once with turbineScope and testIn`() = runTest {
        turbineScope {
            val rates = flowOf(1.0850, 1.0851).testIn(backgroundScope, name = "rates")
            val alerts = flowOf("drift").testIn(backgroundScope, name = "alerts")
            assertThat(rates.awaitItem()).isEqualTo(1.0850)
            assertThat(alerts.awaitItem()).isEqualTo("drift")
            assertThat(rates.awaitItem()).isEqualTo(1.0851)
            rates.awaitComplete()
            alerts.awaitComplete()
        }
    }
}
