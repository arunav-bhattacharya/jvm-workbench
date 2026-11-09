package workbench.functional.l05

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test

class LazyPipelinesTest {

    // 200,000 payments; every fourth card (ids 1, 5, 9, ...) is foreign
    private val feed = List(200_000) { i ->
        Payment(
            id = i + 1L,
            merchant = "merchant-${i % 40}",
            amountCents = 500L + (i * 7_919L) % 120_000,
            country = if (i % 4 == 0) "DE" else "NL",
        )
    }

    // the fraud model flags four payments; 15,002 is domestic
    private val flagged = setOf(4_217L, 9_001L, 12_345L, 15_002L)

    private class CountingModel(private val flagged: Set<Long>) : (Payment) -> Int {
        var calls = 0
        val domesticCalls get() = seen.count { it.country == "NL" }
        private val seen = mutableListOf<Payment>()
        override fun invoke(p: Payment): Int {
            calls++
            if (p.country == "NL") seen += p
            return if (p.id in flagged) 95 else (p.id % 89).toInt()
        }
    }

    @Test
    fun `firstSuspicious finds the first flagged payment`() {
        val model = CountingModel(flagged)
        assertThat(firstSuspicious(feed, model)?.id).isEqualTo(4_217L)
    }

    @Test
    fun `firstSuspicious scores only up to the first match`() {
        val model = CountingModel(flagged)
        firstSuspicious(feed, model)
        assertThat(model.calls).`as`("risk model calls for a match at position 4,217").isEqualTo(4_217)
    }

    @Test
    fun `firstSuspicious returns null and scores everything when nothing is flagged`() {
        val model = CountingModel(emptySet())
        assertThat(firstSuspicious(feed, model)).isNull()
        assertThat(model.calls).isEqualTo(200_000)
    }

    @Test
    fun `firstSuspiciousForeign stops at the nth match and never scores a domestic card`() {
        val model = CountingModel(flagged)
        assertThat(firstSuspiciousForeign(feed, model, 2)).containsExactly(4_217L, 9_001L)
        assertThat(model.domesticCalls).`as`("domestic payments sent to the model").isZero()
        // foreign ids are 1, 5, 9, ... so 9,001 is the 2,251st foreign payment
        assertThat(model.calls).`as`("risk model calls").isEqualTo(2_251)
    }

    @Test
    fun `firstSuspiciousForeign returns fewer ids when the feed runs out`() {
        val model = CountingModel(flagged)
        assertThat(firstSuspiciousForeign(feed, model, 5)).containsExactly(4_217L, 9_001L, 12_345L)
        assertThat(model.calls).isEqualTo(50_000)
    }

    // ---- allSettlements: a paging sequence ----

    private class FakeApi(private val pages: List<List<Payment>>) : SettlementApi {
        val fetched = mutableListOf<Int>()
        override fun page(number: Int): List<Payment> {
            fetched += number
            return pages.getOrElse(number) { error("page $number does not exist: the client read past the empty page") }
        }
    }

    private fun pay(id: Long, cents: Long) = Payment(id, "acme", cents, "NL")

    private fun threePagesThenEmpty() = FakeApi(
        listOf(
            listOf(pay(1, 1_000), pay(2, 2_000), pay(3, 3_000)),
            listOf(pay(4, 80_000), pay(5, 5_000), pay(6, 6_000)),
            listOf(pay(7, 7_000)),
            emptyList(),
        )
    )

    @Test
    fun `allSettlements fetches nothing until a terminal operation runs`() {
        val api = threePagesThenEmpty()
        val settlements = allSettlements(api).filter { it.amountCents > 0 }.map { it.id }
        assertThat(api.fetched).`as`("pages fetched before anyone asked").isEmpty()
        assertThat(settlements.first()).isEqualTo(1L)
        assertThat(api.fetched).containsExactly(0)
    }

    @Test
    fun `allSettlements fetches only the pages it needs`() {
        val api = threePagesThenEmpty()
        assertThat(allSettlements(api).first { it.amountCents > 50_000 }.id).isEqualTo(4L)
        assertThat(api.fetched).containsExactly(0, 1)
    }

    @Test
    fun `allSettlements returns every payment in order and stops at the empty page`() {
        val api = threePagesThenEmpty()
        assertThat(allSettlements(api).map { it.id }.toList()).containsExactly(1L, 2L, 3L, 4L, 5L, 6L, 7L)
        assertThat(api.fetched).containsExactly(0, 1, 2, 3)
    }

    @Test
    fun `allSettlements starts again from page 0 each time it is iterated`() {
        val api = threePagesThenEmpty()
        val settlements = allSettlements(api)
        assertThat(settlements.count()).isEqualTo(7)
        assertThat(settlements.count()).isEqualTo(7)
        assertThat(api.fetched).containsExactly(0, 1, 2, 3, 0, 1, 2, 3)
    }
}
