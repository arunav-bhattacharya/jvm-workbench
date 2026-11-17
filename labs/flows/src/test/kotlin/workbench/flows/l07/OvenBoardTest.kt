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

@OptIn(ExperimentalCoroutinesApi::class) // advanceTimeBy on TestScope is experimental in 1.11.0
class OvenBoardTest {

    /** Reading number [i] of feed run [run]: run 1 reads 100, 101, ...; run 2 reads 200, ... (made-up numbers that show the run). */
    private fun reading(run: Int, i: Int) = Reading("main oven", 100 * run + i)

    /**
     * A thermometer feed that sends a reading at once and then one every 1,000 virtual ms. Each
     * collection is a new "run" and counts as a start; [failRun1At] makes run 1 throw an
     * IOException instead of sending that reading.
     */
    private class Feed(private val failRun1At: Int? = null) {
        var starts = 0
        var stops = 0
        fun reading(run: Int, i: Int) = Reading("main oven", 100 * run + i)
        val flow: Flow<Reading> = flow {
            val run = ++starts
            try {
                var i = 0
                while (true) {
                    if (run == 1 && i == failRun1At) throw IOException("the thermometer dropped its connection")
                    emit(reading(run, i++))
                    delay(1_000)
                }
            } finally {
                stops++
            }
        }
    }

    // ---- hallBoard: read through .value only ----

    @Test
    fun `people who only read value get the latest reading, from one feed`() = runTest {
        val feed = Feed()
        val board = hallBoard(feed.flow, backgroundScope)
        advanceTimeBy(3_500) // readings arrived at 0, 1000, 2000 and 3000
        val glances = List(100) { board.value } // 100 people glance at the board, none collects
        assertThat(feed.starts).`as`("feed collections").isEqualTo(1)
        assertThat(glances).`as`("what the 100 glances read").containsOnly(reading(1, 3))
    }

    @Test
    fun `a feed failure keeps the last reading and restarts the feed one second later`() = runTest {
        val feed = Feed(failRun1At = 2) // run 1 sends at 0 and 1000, then fails at 2000
        val board = hallBoard(feed.flow, backgroundScope)
        advanceTimeBy(2_500)
        assertThat(board.value).`as`("value at t=2500, after the failure").isEqualTo(reading(1, 1))
        assertThat(feed.starts).`as`("starts at t=2500").isEqualTo(1)
        advanceTimeBy(1_000) // t=3500: the retry waited 1000 ms, then collected again at 3000
        assertThat(feed.starts).`as`("starts at t=3500").isEqualTo(2)
        assertThat(board.value).`as`("value at t=3500").isEqualTo(reading(2, 0))
    }

    // ---- screenFeed: collected by each screen that is on ----

    @Test
    fun `nothing collects the feed while no screen is on`() = runTest {
        val feed = Feed()
        val live = screenFeed(feed.flow, backgroundScope)
        advanceTimeBy(3_000)
        assertThat(feed.starts).`as`("feed collections with no screen on").isZero()
        assertThat(live.value).isNull()
    }

    @Test
    fun `two screens and a flicker within 5 seconds share one feed run`() = runTest {
        val feed = Feed()
        val live = screenFeed(feed.flow, backgroundScope)
        val b = backgroundScope.launch { live.collect { } }
        val a = backgroundScope.launch { live.collect { } }
        advanceTimeBy(2_500)
        a.cancel(); b.cancel() // both screens flicker off...
        advanceTimeBy(1_500)   // ...and one comes back on at t=4000
        backgroundScope.launch { live.collect { } }
        advanceTimeBy(1_000)
        assertThat(feed.starts).`as`("feed collections").isEqualTo(1)
        assertThat(feed.stops).`as`("feed stops").isZero()
    }

    @Test
    fun `the feed stops 5 seconds after the last screen goes off`() = runTest {
        val feed = Feed()
        val live = screenFeed(feed.flow, backgroundScope)
        val screen = backgroundScope.launch { live.collect { } }
        advanceTimeBy(1_000)
        screen.cancel()
        advanceTimeBy(4_900)
        assertThat(feed.stops).`as`("stops 4.9 s after the last screen went off").isZero()
        advanceTimeBy(200)
        assertThat(feed.stops).`as`("stops 5.1 s after the last screen went off").isEqualTo(1)
    }

    @Test
    fun `a screen switched on after the stop shows null, then a fresh reading`() = runTest {
        val feed = Feed()
        val live = screenFeed(feed.flow, backgroundScope)
        val first = backgroundScope.launch { live.collect { } }
        advanceTimeBy(2_500) // run 1 sent readings at 0, 1000 and 2000
        first.cancel()
        advanceTimeBy(8_000) // t=10500: the feed stopped at 7500
        val seen = mutableListOf<Reading?>()
        backgroundScope.launch { live.collect { seen += it } }
        advanceTimeBy(500)
        assertThat(seen).`as`("what the late screen showed").containsExactly(null, reading(2, 0))
        assertThat(feed.starts).`as`("feed collections").isEqualTo(2)
    }
}
