package workbench.coroutines.l02

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.delay
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runTest
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.util.concurrent.atomic.AtomicInteger

/** A grocer that answers after [latencyMs] of virtual time. */
private class FakeGrocer(override val name: String, private val latencyMs: Long, private val cents: Int) : Grocer {
    val calls = AtomicInteger()
    val answered = AtomicInteger()

    override suspend fun price(item: String): Price {
        calls.incrementAndGet()
        delay(latencyMs)
        answered.incrementAndGet()
        return Price(name, item, cents)
    }
}

@OptIn(ExperimentalCoroutinesApi::class)
class PriceCheckTest {
    private val slow = FakeGrocer("greengrocer", 300, 189)
    private val fast = FakeGrocer("market", 120, 149)
    private val mid = FakeGrocer("farm-stand", 200, 175)
    private val grocers = listOf(slow, fast, mid)

    @Test
    fun `allPrices returns one price per grocer in grocer order`() = runTest {
        val prices = PriceCheck(grocers).allPrices("tomatoes")
        assertThat(prices.map { it.grocer }).containsExactly("greengrocer", "market", "farm-stand")
    }

    @Test
    fun `allPrices takes as long as the slowest grocer, not the sum`() = runTest {
        PriceCheck(grocers).allPrices("tomatoes")
        // 300 + 120 + 200 = 620 if the calls run one after another
        assertThat(currentTime).`as`("virtual ms").isEqualTo(300)
    }

    @Test
    fun `cheapest picks the lowest price after asking everyone at once`() = runTest {
        val best = PriceCheck(grocers).cheapest("tomatoes")
        assertThat(best.grocer).isEqualTo("market")
        assertThat(currentTime).isEqualTo(300)
        assertThat(grocers.map { it.calls.get() }).containsExactly(1, 1, 1)
    }

    @Test
    fun `callAhead asks every grocer and returns only when all have answered`() = runTest {
        PriceCheck(grocers).callAhead()
        assertThat(grocers.map { it.answered.get() }).`as`("answered when callAhead returned").containsExactly(1, 1, 1)
        assertThat(currentTime).isEqualTo(300)
    }

    @Test
    fun `priceList asks every item and grocer at the same time`() = runTest {
        val list = PriceCheck(grocers).priceList(listOf("tomatoes", "basil"))
        assertThat(list.keys).containsExactlyInAnyOrder("tomatoes", "basil")
        assertThat(list.getValue("basil").map { it.grocer }).containsExactly("greengrocer", "market", "farm-stand")
        assertThat(currentTime).`as`("virtual ms for 2 items x 3 grocers").isEqualTo(300)
        assertThat(grocers.sumOf { it.calls.get() }).isEqualTo(6)
    }
}
