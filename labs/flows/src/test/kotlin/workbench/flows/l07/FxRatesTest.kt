package workbench.flows.l07

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.advanceTimeBy
import kotlinx.coroutines.test.runTest
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.io.IOException
import java.math.BigDecimal

@OptIn(ExperimentalCoroutinesApi::class) // advanceTimeBy on TestScope is experimental in 1.11.0
class FxRatesTest {

    /** Rate number [i] of feed run [run]: run 1 gives 1.0900, 1.0901, ...; run 2 gives 1.1000, ... */
    private fun rate(run: Int, i: Int) = Rate("EURUSD", BigDecimal.valueOf(10_800L + 100L * run + i, 4))

    /**
     * A provider feed that sends a rate at once and then one every 1,000 virtual ms. Each
     * collection is a new "run" and counts as a start; [failRun1At] makes run 1 throw an
     * IOException instead of sending that rate.
     */
    private class Feed(private val failRun1At: Int? = null) {
        var starts = 0
        var stops = 0
        fun rate(run: Int, i: Int) = Rate("EURUSD", BigDecimal.valueOf(10_800L + 100L * run + i, 4))
        val flow: Flow<Rate> = flow {
            val run = ++starts
            try {
                var i = 0
                while (true) {
                    if (run == 1 && i == failRun1At) throw IOException("provider reset the connection")
                    emit(rate(run, i++))
                    delay(1_000)
                }
            } finally {
                stops++
            }
        }
    }

    // ---- requestCache: read through .value only ----

    @Test
    fun `request handlers that only read value get the latest rate, from one feed`() = runTest {
        val feed = Feed()
        val cache = requestCache(feed.flow, backgroundScope)
        advanceTimeBy(3_500) // rates arrived at 0, 1000, 2000 and 3000
        val reads = List(100) { cache.value } // 100 requests read the cache, none collects
        assertThat(feed.starts).`as`("feed collections").isEqualTo(1)
        assertThat(reads).`as`("what the 100 requests read").containsOnly(rate(1, 3))
    }

    @Test
    fun `a feed failure keeps the last rate and restarts the feed one second later`() = runTest {
        val feed = Feed(failRun1At = 2) // run 1 sends at 0 and 1000, then fails at 2000
        val cache = requestCache(feed.flow, backgroundScope)
        advanceTimeBy(2_500)
        assertThat(cache.value).`as`("value at t=2500, after the failure").isEqualTo(rate(1, 1))
        assertThat(feed.starts).`as`("starts at t=2500").isEqualTo(1)
        advanceTimeBy(1_000) // t=3500: the retry waited 1000 ms, then collected again at 3000
        assertThat(feed.starts).`as`("starts at t=3500").isEqualTo(2)
        assertThat(cache.value).`as`("value at t=3500").isEqualTo(rate(2, 0))
    }

    // ---- dashboardFeed: collected by each open dashboard ----

    @Test
    fun `nothing collects the feed while no dashboard is open`() = runTest {
        val feed = Feed()
        val live = dashboardFeed(feed.flow, backgroundScope)
        advanceTimeBy(3_000)
        assertThat(feed.starts).`as`("feed collections with no dashboard").isZero()
        assertThat(live.value).isNull()
    }

    @Test
    fun `two dashboards and a reload within 5 seconds share one feed run`() = runTest {
        val feed = Feed()
        val live = dashboardFeed(feed.flow, backgroundScope)
        val b = backgroundScope.launch { live.collect { } }
        val a = backgroundScope.launch { live.collect { } }
        advanceTimeBy(2_500)
        a.cancel(); b.cancel() // both tabs reload...
        advanceTimeBy(1_500)   // ...and come back at t=4000
        backgroundScope.launch { live.collect { } }
        advanceTimeBy(1_000)
        assertThat(feed.starts).`as`("feed collections").isEqualTo(1)
        assertThat(feed.stops).`as`("feed stops").isZero()
    }

    @Test
    fun `the feed stops 5 seconds after the last dashboard leaves`() = runTest {
        val feed = Feed()
        val live = dashboardFeed(feed.flow, backgroundScope)
        val dashboard = backgroundScope.launch { live.collect { } }
        advanceTimeBy(1_000)
        dashboard.cancel()
        advanceTimeBy(4_900)
        assertThat(feed.stops).`as`("stops 4.9 s after the last dashboard left").isZero()
        advanceTimeBy(200)
        assertThat(feed.stops).`as`("stops 5.1 s after the last dashboard left").isEqualTo(1)
    }

    @Test
    fun `a dashboard that opens after the stop sees null, then a fresh rate`() = runTest {
        val feed = Feed()
        val live = dashboardFeed(feed.flow, backgroundScope)
        val first = backgroundScope.launch { live.collect { } }
        advanceTimeBy(2_500) // run 1 sent rates at 0, 1000 and 2000
        first.cancel()
        advanceTimeBy(8_000) // t=10500: the feed stopped at 7500
        val seen = mutableListOf<Rate?>()
        backgroundScope.launch { live.collect { seen += it } }
        advanceTimeBy(500)
        assertThat(seen).`as`("what the late dashboard was shown").containsExactly(null, rate(2, 0))
        assertThat(feed.starts).`as`("feed collections").isEqualTo(2)
    }
}
