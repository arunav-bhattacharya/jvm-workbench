package workbench.flows.l04

import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runTest
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.io.IOException

@OptIn(ExperimentalCoroutinesApi::class) // currentTime and advanceUntilIdle are experimental in kotlinx-coroutines-test 1.11.0
class BufferingTest {

    /**
     * Runs [op] over a 200-value flow. The collector holds value 1 until the producer has gone as
     * far as it can (virtual time makes "as far as it can" exact), then takes the rest.
     * Returns how many emits had returned while value 1 was held, and everything received.
     */
    private suspend fun TestScope.ahead(op: (Flow<Int>) -> Flow<Int>): Pair<Int, List<Int>> {
        var returned = 0
        val gate = CompletableDeferred<Unit>()
        val got = mutableListOf<Int>()
        val source = flow { for (i in 1..200) { emit(i); returned = i } }
        val job = launch { op(source).collect { got += it; if (got.size == 1) gate.await() } }
        advanceUntilIdle()
        val heldAhead = returned
        gate.complete(Unit)
        job.join()
        return heldAhead to got
    }

    // ---- shelf: a buffer by hand ----

    @Test
    fun `shelf(10) lets 11 emits return while the collector holds the first value`() = runTest {
        val (returned, _) = ahead { it.shelf(10) }
        assertThat(returned).`as`("emits returned: 10 on the shelf plus 1 in the collector's hands").isEqualTo(11)
    }

    @Test
    fun `shelf(0) is a hand-over with no spots, so exactly one emit returns`() = runTest {
        val (returned, _) = ahead { it.shelf(0) }
        assertThat(returned).isEqualTo(1)
    }

    @Test
    fun `shelf delivers every value, in order`() = runTest {
        val (_, got) = ahead { it.shelf(10) }
        assertThat(got).containsExactlyElementsOf(1..200)
    }

    @Test
    fun `shelf lets a 100 ms producer run ahead of a 300 ms collector`() = runTest {
        val seen = mutableListOf<Int>()
        flow { for (i in 1..3) { delay(100); emit(i) } }
            .shelf(64)
            .collect { delay(300); seen += it }
        assertThat(seen).containsExactly(1, 2, 3)
        assertThat(currentTime).`as`("virtual ms: 100 + 3 x 300, where plain collection takes 1200").isEqualTo(1000)
    }

    @Test
    fun `shelf passes an upstream failure on to the collector`() = runTest {
        val failing = flow { emit(1); emit(2); throw IOException("delivery note torn") }
        val failure = runCatching { failing.shelf(4).collect { } }.exceptionOrNull()
        assertThat(failure).isInstanceOf(IOException::class.java).hasMessage("delivery note torn")
    }

    // ---- three ways to show the oven thermometer ----

    private fun readings(): Flow<Reading> = flow {
        for (i in 1..3) { delay(100); emit(Reading("oven", i, 180 + i)) }
    }

    private fun screen(ms: Long): suspend (Reading) -> Shown = { reading ->
        delay(ms)
        Shown(reading.tick, "${reading.celsius} C")
    }

    @Test
    fun `everyReading shows all three readings in 1000 ms`() = runTest {
        val shown = everyReading(readings(), screen(300)).toList()
        assertThat(shown.map { it.tick }).containsExactly(1, 2, 3)
        assertThat(currentTime).`as`("virtual ms; 1200 means the thermometer waited for the screen").isEqualTo(1000)
    }

    @Test
    fun `latestReading skips reading 2 and finishes at 700 ms`() = runTest {
        val shown = latestReading(readings(), screen(300)).toList()
        assertThat(shown.map { it.tick }).containsExactly(1, 3)
        assertThat(currentTime).isEqualTo(700)
    }

    @Test
    fun `latestReading loses nothing when the screen is faster than the thermometer`() = runTest {
        val shown = latestReading(readings(), screen(50)).toList()
        assertThat(shown.map { it.tick }).`as`("conflation drops only what arrives while the screen is busy")
            .containsExactly(1, 2, 3)
        assertThat(currentTime).isEqualTo(350)
    }

    @Test
    fun `cancelStale finishes only the newest reading, at 600 ms`() = runTest {
        val started = mutableListOf<Int>()
        val shown = cancelStale(readings()) { reading -> started += reading.tick; screen(300)(reading) }.toList()
        assertThat(started).`as`("drawings started").containsExactly(1, 2, 3)
        assertThat(shown.map { it.tick }).`as`("drawings finished").containsExactly(3)
        assertThat(currentTime).isEqualTo(600)
    }

    // ---- plates for the table must never be dropped ----

    private fun plates(source: Flow<Int>): Flow<Plate> = flow {
        source.collect { n -> emit(Plate(n, "dumpling")) }
    }

    @Test
    fun `towardsTable never drops a plate, even when the diner is stuck`() = runTest {
        val (_, got) = ahead { ints -> towardsTable(plates(ints)).map { it.seq } }
        assertThat(got).`as`("plates that reached the table").containsExactlyElementsOf(1..200)
    }

    @Test
    fun `towardsTable lets the cook run exactly 64 plates ahead of a stuck diner`() = runTest {
        val (returned, _) = ahead { ints -> towardsTable(plates(ints)).map { it.seq } }
        assertThat(returned).`as`("plates sent while the diner held plate 1: 64 waiting plus 1 in hand").isEqualTo(65)
    }
}
