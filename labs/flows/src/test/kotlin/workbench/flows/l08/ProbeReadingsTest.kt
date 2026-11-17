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
class ProbeReadingsTest {

    private val first = ProbeReading(1, 61)
    private val second = ProbeReading(2, 63)
    private val third = ProbeReading(3, 65)

    @Test
    fun `a collector registers one listener, and take(2) unregisters it`() = runTest {
        val probe = FakeProbe()
        // Unconfined: the collector runs at once, up to its first suspension, so it has
        // registered before the next line. With the default StandardTestDispatcher it would
        // only register at the next runCurrent(), and a reading fired before that is lost.
        val firstTwo = backgroundScope.async(UnconfinedTestDispatcher(testScheduler)) { probe.readings().take(2).toList() }
        assertThat(probe.listenerCount).`as`("listeners once collection started").isEqualTo(1)
        probe.fire(first); probe.fire(second); probe.fire(third)
        assertThat(firstTwo.await()).containsExactly(first, second)
        assertThat(probe.listenerCount).`as`("listeners after take(2) finished").isZero()
    }

    @Test
    fun `cancelling the collector unregisters the listener`() = runTest {
        val probe = FakeProbe()
        val collector = backgroundScope.launch { probe.readings().collect { } }
        runCurrent()
        assertThat(probe.listenerCount).isEqualTo(1)
        collector.cancel()
        runCurrent()
        assertThat(probe.listenerCount).`as`("listeners after cancel").isZero()
    }

    @Test
    fun `a probe error fails the flow with that error and still unregisters`() = runTest {
        val probe = FakeProbe()
        // Turbine's test {} starts collecting before the block runs, so the listener is in place
        probe.readings().test {
            probe.fire(first)
            assertThat(awaitItem()).isEqualTo(first)
            probe.fail(IOException("probe connection lost"))
            assertThat(awaitError()).isInstanceOf(IOException::class.java).hasMessage("probe connection lost")
        }
        assertThat(probe.listenerCount).`as`("listeners after the error").isZero()
    }

    @Test
    fun `the probe closing completes the flow after the readings it sent`() = runTest {
        val probe = FakeProbe()
        probe.readings().test {
            probe.fire(first)
            probe.fire(second)
            probe.close()
            assertThat(awaitItem()).isEqualTo(first)
            assertThat(awaitItem()).isEqualTo(second)
            awaitComplete()
        }
        assertThat(probe.listenerCount).isZero()
    }

    @Test
    fun `a 500-reading burst on connect reaches the collector in full`() = runTest {
        val probe = FakeProbe()
        val got = mutableListOf<ProbeReading>()
        // Not Turbine and not Unconfined: both take each reading the moment it is sent, so the
        // buffer never fills and a too-small buffer would pass. A Standard collector can't run
        // during the burst, the way a busy collector in a real program can't.
        backgroundScope.launch { probe.readings().collect { got += it } }
        runCurrent()     // registered, and waiting for the first reading
        probe.burst(500) // 500 synchronous callbacks on this thread
        runCurrent()
        assertThat(got).`as`("readings delivered from a 500-reading burst").hasSize(500)
        assertThat(got.first().seq).isEqualTo(0)
        assertThat(got.last().seq).isEqualTo(499)
    }
}
