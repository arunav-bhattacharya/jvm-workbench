package workbench.flows.l08

import app.cash.turbine.test
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.async
import kotlinx.coroutines.flow.take
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.io.IOException

@OptIn(ExperimentalCoroutinesApi::class) // UnconfinedTestDispatcher and TestScope.runCurrent are experimental in 1.11.0
class GatewayEventsTest {

    private val authorized = GatewayEvent("p-42", "AUTHORIZED")
    private val captured = GatewayEvent("p-42", "CAPTURED")
    private val settled = GatewayEvent("p-42", "SETTLED")

    @Test
    fun `a collector registers one listener, and take(2) unregisters it`() = runTest {
        val gw = FakeGateway()
        // Unconfined: the collector runs at once, up to its first suspension, so it has
        // registered before the next line. With the default StandardTestDispatcher it would
        // only register at the next runCurrent(), and an event fired before that is lost.
        val firstTwo = backgroundScope.async(UnconfinedTestDispatcher(testScheduler)) { gw.events().take(2).toList() }
        assertThat(gw.listenerCount).`as`("listeners once collection started").isEqualTo(1)
        gw.fire(authorized); gw.fire(captured); gw.fire(settled)
        assertThat(firstTwo.await()).containsExactly(authorized, captured)
        assertThat(gw.listenerCount).`as`("listeners after take(2) finished").isZero()
    }

    @Test
    fun `cancelling the collector unregisters the listener`() = runTest {
        val gw = FakeGateway()
        val collector = backgroundScope.launch { gw.events().collect { } }
        runCurrent()
        assertThat(gw.listenerCount).isEqualTo(1)
        collector.cancel()
        runCurrent()
        assertThat(gw.listenerCount).`as`("listeners after cancel").isZero()
    }

    @Test
    fun `an SDK error fails the flow with that error and still unregisters`() = runTest {
        val gw = FakeGateway()
        // Turbine's test {} starts collecting before the block runs, so the listener is in place
        gw.events().test {
            gw.fire(authorized)
            assertThat(awaitItem()).isEqualTo(authorized)
            gw.fail(IOException("gateway connection lost"))
            assertThat(awaitError()).isInstanceOf(IOException::class.java).hasMessage("gateway connection lost")
        }
        assertThat(gw.listenerCount).`as`("listeners after the error").isZero()
    }

    @Test
    fun `the SDK closing completes the flow after the events it sent`() = runTest {
        val gw = FakeGateway()
        gw.events().test {
            gw.fire(authorized)
            gw.fire(captured)
            gw.close()
            assertThat(awaitItem()).isEqualTo(authorized)
            assertThat(awaitItem()).isEqualTo(captured)
            awaitComplete()
        }
        assertThat(gw.listenerCount).isZero()
    }

    @Test
    fun `a 500-event burst on connect reaches the collector in full`() = runTest {
        val gw = FakeGateway()
        val got = mutableListOf<GatewayEvent>()
        // Not Turbine and not Unconfined: both take each event the moment it is sent, so the
        // buffer never fills and a too-small buffer would pass. A Standard collector can't run
        // during the burst, the way a busy production collector can't.
        backgroundScope.launch { gw.events().collect { got += it } }
        runCurrent()   // registered, and waiting for the first event
        gw.burst(500)  // 500 synchronous callbacks on this thread
        runCurrent()
        assertThat(got).`as`("events delivered from a 500-event burst").hasSize(500)
        assertThat(got.first().paymentId).isEqualTo("p-0")
        assertThat(got.last().paymentId).isEqualTo("p-499")
    }
}
