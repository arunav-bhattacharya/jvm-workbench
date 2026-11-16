package workbench.flows.l05

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.asFlow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runTest
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.io.IOException

@OptIn(ExperimentalCoroutinesApi::class) // currentTime is experimental in kotlinx-coroutines-test 1.11.0
class FlatteningTest {

    /** A fake fee service on virtual time. It counts how many lookups are in flight at once. */
    private class FakeFees(private val latencyMs: (String) -> Long, private val failFor: Set<String> = emptySet()) : FeeService {
        var inFlight = 0
        var maxInFlight = 0
        var calls = 0
        override suspend fun lookup(merchant: String): Fee {
            calls++
            inFlight++
            maxInFlight = maxOf(maxInFlight, inFlight)
            try {
                delay(latencyMs(merchant))
                if (merchant in failFor) throw IOException("fee service 503 for $merchant")
                return Fee(merchant, 290)
            } finally {
                inFlight--
            }
        }
    }

    /** Collects a flow and records the virtual time at which each value arrived. */
    private suspend fun <T> TestScope.timed(flow: Flow<T>): List<Pair<Long, T>> {
        val seen = mutableListOf<Pair<Long, T>>()
        flow.collect { seen += currentTime to it }
        return seen
    }

    // ---- fees: bounded fan-out ----

    @Test
    fun `fees runs 4 lookups at once, so 10 lookups of 100 ms take 300 ms`() = runTest {
        val service = FakeFees({ 100 })
        val merchants = (1..10).map { "m$it" }
        val result = fees(merchants.asFlow(), service).toList()
        assertThat(result.map { it.merchant }).containsExactlyInAnyOrderElementsOf(merchants)
        assertThat(service.maxInFlight).`as`("lookups in flight at the busiest moment").isEqualTo(4)
        assertThat(currentTime).`as`("virtual ms: three waves of 4, 4 and 2").isEqualTo(300)
    }

    @Test
    fun `fees never goes over the cap of 4, even with 40 merchants`() = runTest {
        val service = FakeFees({ 100 })
        val result = fees((1..40).map { "m$it" }.asFlow(), service).toList()
        assertThat(result).hasSize(40)
        assertThat(service.maxInFlight).isEqualTo(4)
        assertThat(currentTime).isEqualTo(1000)
    }

    @Test
    fun `fees passes results on in completion order`() = runTest {
        val latency = mapOf("m1" to 300L, "m2" to 100L, "m3" to 200L)
        val seen = timed(fees(latency.keys.asFlow(), FakeFees({ latency.getValue(it) })))
        assertThat(seen.map { it.second.merchant to it.first })
            .containsExactly("m2" to 100L, "m3" to 200L, "m1" to 300L)
    }

    // ---- feesOrDefault: one failure must not take the others down ----

    private val default = { merchant: String -> Fee(merchant, 350, "default") }

    @Test
    fun `feesOrDefault gives a failing merchant the default fee and keeps the others`() = runTest {
        val latency = mapOf("m1" to 300L, "m2" to 100L, "m3" to 200L)
        val service = FakeFees({ latency.getValue(it) }, failFor = setOf("m2"))
        val seen = timed(feesOrDefault(latency.keys.asFlow(), service, default))
        assertThat(seen.map { Triple(it.second.merchant, it.second.source, it.first) }).containsExactly(
            Triple("m2", "default", 100L),
            Triple("m3", "service", 200L),
            Triple("m1", "service", 300L),
        )
    }

    @Test
    fun `feesOrDefault still caps the lookups at 4`() = runTest {
        val service = FakeFees({ 100 }, failFor = setOf("m3", "m7"))
        val result = feesOrDefault((1..10).map { "m$it" }.asFlow(), service, default).toList()
        assertThat(result.filter { it.source == "default" }.map { it.merchant }).containsExactlyInAnyOrder("m3", "m7")
        assertThat(service.maxInFlight).isEqualTo(4)
        assertThat(currentTime).isEqualTo(300)
    }

    // ---- eurPrices: the latest of each ----

    /** USD prices 1000, 1010, ... 1050 cents, one every 100 ms from t=100. */
    private fun prices(): Flow<Long> = flow { for (p in 1000L..1050L step 10) { delay(100); emit(p) } }

    /** The USD to EUR rate: 0.92 at t=250, 0.95 at t=550. */
    private fun rates(): Flow<Double> = flow { delay(250); emit(0.92); delay(300); emit(0.95) }

    @Test
    fun `eurPrices waits for a rate, then uses the latest price`() = runTest {
        val first = timed(eurPrices(prices(), rates())).first()
        assertThat(first.first).`as`("virtual ms of the first EUR price: when the first rate arrived").isEqualTo(250)
        assertThat(first.second).isEqualTo(EurPrice(1010, 0.92, 929))
    }

    @Test
    fun `eurPrices emits once per update of either flow`() = runTest {
        val seen = timed(eurPrices(prices(), rates()))
        assertThat(seen.map { it.first to "${it.second.usdCents}@${it.second.usdToEur}" }).containsExactly(
            250L to "1010@0.92",
            300L to "1020@0.92",
            400L to "1030@0.92",
            500L to "1040@0.92",
            550L to "1040@0.95",
            600L to "1050@0.95",
        )
    }
}
