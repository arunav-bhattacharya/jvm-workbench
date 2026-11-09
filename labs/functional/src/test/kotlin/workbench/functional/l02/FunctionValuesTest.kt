package workbench.functional.l02

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.util.concurrent.CountDownLatch
import kotlin.concurrent.thread

class FunctionValuesTest {
    private val ok = Payment("pay_1", 12_000, "EUR", "NL")

    @Test
    fun `amountAtMost rejects amounts above the limit and lets the limit itself through`() {
        val rule = amountAtMost(50_000)
        assertThat(rule(ok.copy(amountCents = 50_000))).isNull()
        assertThat(rule(ok.copy(id = "pay_2", amountCents = 50_001))).isEqualTo(Rejection("amount-limit", "pay_2"))
    }

    @Test
    fun `two amount rules keep their own limits`() {
        val small = amountAtMost(1_000)
        val large = amountAtMost(1_000_000)
        assertThat(small(ok)).isEqualTo(Rejection("amount-limit", "pay_1"))
        assertThat(large(ok)).isNull()
    }

    @Test
    fun `countryServed rejects countries outside the served set`() {
        assertThat(countryServed(ok)).isNull()
        assertThat(countryServed(ok.copy(country = "US"))).isEqualTo(Rejection("country-not-served", "pay_1"))
    }

    @Test
    fun `currencyRule and supportedCurrency agree`() {
        val jpy = ok.copy(currency = "JPY")
        assertThat(supportedCurrency(ok)).isNull()
        assertThat(supportedCurrency(jpy)).isEqualTo(Rejection("currency-not-supported", "pay_1"))
        assertThat(currencyRule(ok)).isNull()
        assertThat(currencyRule(jpy)).isEqualTo(Rejection("currency-not-supported", "pay_1"))
    }

    @Test
    fun `firstRejection returns the first rejection in rule order, or null`() {
        val rules = listOf(amountAtMost(50_000), countryServed, currencyRule)
        assertThat(firstRejection(ok, rules)).isNull()
        val bad = ok.copy(amountCents = 90_000, country = "US")
        assertThat(firstRejection(bad, rules)).isEqualTo(Rejection("amount-limit", "pay_1"))
        assertThat(firstRejection(bad, rules.reversed())).isEqualTo(Rejection("country-not-served", "pay_1"))
    }

    @Test
    fun `firstRejection stops at the first rejection`() {
        var fraudApiCalls = 0
        val fraudCheck: Rule = { fraudApiCalls++; null }
        firstRejection(ok.copy(country = "US"), listOf(countryServed, fraudCheck))
        assertThat(fraudApiCalls).`as`("rules after the first rejection must not run").isZero()
        firstRejection(ok, listOf(countryServed, fraudCheck))
        assertThat(fraudApiCalls).isEqualTo(1)
    }

    @Test
    fun `allRejections collects every rejection in rule order`() {
        val rules = listOf(amountAtMost(50_000), countryServed, currencyRule)
        val bad = Payment("pay_9", 90_000, "JPY", "US")
        assertThat(allRejections(bad, rules).map { it.rule })
            .containsExactly("amount-limit", "country-not-served", "currency-not-supported")
        assertThat(allRejections(ok, rules)).isEmpty()
    }

    @Test
    fun `screen calls the optional callback only on rejection`() {
        val rules = listOf(countryServed)
        assertThat(screen(ok, rules)).isTrue()
        assertThat(screen(ok.copy(country = "US"), rules)).`as`("no callback given: must not fail").isFalse()

        val seen = mutableListOf<Rejection>()
        assertThat(screen(ok, rules) { seen += it }).isTrue()
        assertThat(screen(ok.copy(country = "US"), rules) { seen += it }).isFalse()
        assertThat(seen).containsExactly(Rejection("country-not-served", "pay_1"))
    }

    @Test
    fun `makeCounter counts 1, 2, 3 and two counters are independent`() {
        val a = makeCounter()
        val b = makeCounter()
        assertThat(listOf(a(), a(), a())).containsExactly(1, 2, 3)
        assertThat(b()).isEqualTo(1)
        assertThat(a()).isEqualTo(4)
    }

    @Test
    fun `a shared counter loses no updates on 8 threads`() {
        val threads = 8
        val perThread = 200_000
        // Several rounds: one lucky round proves nothing, a broken counter loses updates in at least one.
        repeat(5) { round ->
            val counter = makeSharedCounter()
            val ready = CountDownLatch(threads)
            val go = CountDownLatch(1)
            val workers = List(threads) {
                thread {
                    ready.countDown()
                    go.await()
                    repeat(perThread) { counter() }
                }
            }
            ready.await()
            go.countDown()
            workers.forEach { it.join() }
            val expectedNext = threads.toLong() * perThread + 1
            assertThat(counter()).`as`("round ${round + 1}: the next value after ${threads * perThread} calls").isEqualTo(expectedNext)
        }
    }
}
