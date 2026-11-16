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

    // ---- belt: a buffer by hand ----

    @Test
    fun `belt(10) lets 11 emits return while the collector holds the first value`() = runTest {
        val (returned, _) = ahead { it.belt(10) }
        assertThat(returned).`as`("emits returned: 10 on the belt plus 1 in the collector's hands").isEqualTo(11)
    }

    @Test
    fun `belt(0) is a hand-over with no slots, so exactly one emit returns`() = runTest {
        val (returned, _) = ahead { it.belt(0) }
        assertThat(returned).isEqualTo(1)
    }

    @Test
    fun `belt delivers every value, in order`() = runTest {
        val (_, got) = ahead { it.belt(10) }
        assertThat(got).containsExactlyElementsOf(1..200)
    }

    @Test
    fun `belt lets a 100 ms producer run ahead of a 300 ms collector`() = runTest {
        val seen = mutableListOf<Int>()
        flow { for (i in 1..3) { delay(100); emit(i) } }
            .belt(64)
            .collect { delay(300); seen += it }
        assertThat(seen).containsExactly(1, 2, 3)
        assertThat(currentTime).`as`("virtual ms: 100 + 3 x 300, where plain collection takes 1200").isEqualTo(1000)
    }

    @Test
    fun `belt passes an upstream failure on to the collector`() = runTest {
        val failing = flow { emit(1); emit(2); throw IOException("settlement file truncated") }
        val failure = runCatching { failing.belt(4).collect { } }.exceptionOrNull()
        assertThat(failure).isInstanceOf(IOException::class.java).hasMessage("settlement file truncated")
    }

    // ---- three FX repricing strategies ----

    private fun ticks(): Flow<Rate> = flow {
        for (i in 1..3) { delay(100); emit(Rate("EUR/USD", i, 1.08 + i / 100.0)) }
    }

    private fun repricer(ms: Long): suspend (Rate) -> Quote = { rate ->
        delay(ms)
        Quote(rate.tick, Math.round(4_250 * rate.value))
    }

    @Test
    fun `everyRate reprices all three ticks in 1000 ms`() = runTest {
        val quotes = everyRate(ticks(), repricer(300)).toList()
        assertThat(quotes.map { it.tick }).containsExactly(1, 2, 3)
        assertThat(currentTime).`as`("virtual ms; 1200 means the feed waited for the repricer").isEqualTo(1000)
    }

    @Test
    fun `latestRate skips tick 2 and finishes at 700 ms`() = runTest {
        val quotes = latestRate(ticks(), repricer(300)).toList()
        assertThat(quotes.map { it.tick }).containsExactly(1, 3)
        assertThat(currentTime).isEqualTo(700)
    }

    @Test
    fun `latestRate loses nothing when repricing is faster than the feed`() = runTest {
        val quotes = latestRate(ticks(), repricer(50)).toList()
        assertThat(quotes.map { it.tick }).`as`("conflation drops only what arrives while the repricer is busy")
            .containsExactly(1, 2, 3)
        assertThat(currentTime).isEqualTo(350)
    }

    @Test
    fun `cancelStale finishes only the newest tick, at 600 ms`() = runTest {
        val started = mutableListOf<Int>()
        val quotes = cancelStale(ticks()) { rate -> started += rate.tick; repricer(300)(rate) }.toList()
        assertThat(started).`as`("repricings started").containsExactly(1, 2, 3)
        assertThat(quotes.map { it.tick }).`as`("repricings finished").containsExactly(3)
        assertThat(currentTime).isEqualTo(600)
    }

    // ---- the ledger pipeline must never drop ----

    private fun postings(source: Flow<Int>): Flow<Posting> = flow {
        source.collect { n -> emit(Posting(n, "pay-$n", 100L * n)) }
    }

    @Test
    fun `towardsLedger never drops a posting, even when the ledger is stuck`() = runTest {
        val (_, got) = ahead { ints -> towardsLedger(postings(ints)).map { it.seq } }
        assertThat(got).`as`("postings that reached the ledger").containsExactlyElementsOf(1..200)
    }

    @Test
    fun `towardsLedger lets the reader run exactly 64 postings ahead of a stuck ledger`() = runTest {
        val (returned, _) = ahead { ints -> towardsLedger(postings(ints)).map { it.seq } }
        assertThat(returned).`as`("postings read while the ledger held posting 1: 64 waiting plus 1 in hand").isEqualTo(65)
    }
}
