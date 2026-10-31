package workbench.coroutines.l02

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.delay
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runTest
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.util.concurrent.atomic.AtomicInteger

/** A provider that answers after [latencyMs] of virtual time. */
private class FakeProvider(override val name: String, private val latencyMs: Long, private val rate: Long) : QuoteProvider {
    val calls = AtomicInteger()
    val answered = AtomicInteger()

    override suspend fun quote(pair: String): FxQuote {
        calls.incrementAndGet()
        delay(latencyMs)
        answered.incrementAndGet()
        return FxQuote(name, pair, rate)
    }
}

@OptIn(ExperimentalCoroutinesApi::class)
class QuoteAggregatorTest {
    private val slow = FakeProvider("northbank", 300, 1_084_100)
    private val fast = FakeProvider("fjord-fx", 120, 1_084_512)
    private val mid = FakeProvider("tidewater", 200, 1_083_900)
    private val providers = listOf(slow, fast, mid)

    @Test
    fun `allQuotes returns one quote per provider in provider order`() = runTest {
        val quotes = QuoteAggregator(providers).allQuotes("EURUSD")
        assertThat(quotes.map { it.provider }).containsExactly("northbank", "fjord-fx", "tidewater")
    }

    @Test
    fun `allQuotes takes as long as the slowest provider, not the sum`() = runTest {
        QuoteAggregator(providers).allQuotes("EURUSD")
        // 300 + 120 + 200 = 620 if the calls run one after another
        assertThat(currentTime).`as`("virtual ms").isEqualTo(300)
    }

    @Test
    fun `bestQuote picks the highest rate after asking everyone at once`() = runTest {
        val best = QuoteAggregator(providers).bestQuote("EURUSD")
        assertThat(best.provider).isEqualTo("fjord-fx")
        assertThat(currentTime).isEqualTo(300)
        assertThat(providers.map { it.calls.get() }).containsExactly(1, 1, 1)
    }

    @Test
    fun `warmUp asks every provider and returns only when all have answered`() = runTest {
        QuoteAggregator(providers).warmUp()
        assertThat(providers.map { it.answered.get() }).`as`("answered when warmUp returned").containsExactly(1, 1, 1)
        assertThat(currentTime).isEqualTo(300)
    }

    @Test
    fun `quoteBoard asks every pair and provider at the same time`() = runTest {
        val board = QuoteAggregator(providers).quoteBoard(listOf("EURUSD", "GBPUSD"))
        assertThat(board.keys).containsExactlyInAnyOrder("EURUSD", "GBPUSD")
        assertThat(board.getValue("GBPUSD").map { it.provider }).containsExactly("northbank", "fjord-fx", "tidewater")
        assertThat(currentTime).`as`("virtual ms for 2 pairs x 3 providers").isEqualTo(300)
        assertThat(providers.sumOf { it.calls.get() }).isEqualTo(6)
    }
}
