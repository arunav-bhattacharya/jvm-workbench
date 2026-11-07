package workbench.patterns.l06

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import workbench.patterns.l06.PricingRule.AllOf
import workbench.patterns.l06.PricingRule.Capped
import workbench.patterns.l06.PricingRule.CheapestOf
import workbench.patterns.l06.PricingRule.Flat
import workbench.patterns.l06.PricingRule.Percent
import java.util.Collections
import java.util.IdentityHashMap
import java.util.concurrent.CountDownLatch
import kotlin.concurrent.thread

class CompositeFlyweightTest {

    // ---- composite ----

    private val standard = AllOf(Flat(30), Percent(290), AllOf(Flat(5)))

    @Test
    fun `a flat fee, a percentage and a nested bundle add up to 325 on 10,000`() {
        assertThat(standard.fee(10_000)).isEqualTo(325)
        assertThat(standard.fee(100_000)).isEqualTo(2_935)
    }

    @Test
    fun `leaves price on their own, with integer division in basis points`() {
        assertThat(Flat(30).fee(10_000)).isEqualTo(30)
        assertThat(Percent(150).fee(999)).isEqualTo(14)
        assertThat(AllOf().fee(10_000)).`as`("an empty AllOf").isEqualTo(0)
    }

    @Test
    fun `CheapestOf charges the smallest fee of its rules`() {
        val plan = CheapestOf(Percent(290), AllOf(Flat(100), Percent(100)))
        assertThat(plan.fee(10_000)).`as`("290 vs 200").isEqualTo(200)
        assertThat(plan.fee(1_000)).`as`("29 vs 110").isEqualTo(29)
    }

    @Test
    fun `Capped never charges more than its cap, at any depth`() {
        val plan = Capped(AllOf(Flat(30), Percent(290)), 500)
        assertThat(plan.fee(10_000)).isEqualTo(320)
        assertThat(plan.fee(100_000)).isEqualTo(500)
        val nested = AllOf(Flat(10), Capped(CheapestOf(Percent(400), Flat(900)), 250))
        assertThat(nested.fee(10_000)).`as`("10 + min(min(400, 900), 250)").isEqualTo(260)
    }

    @Test
    fun `describe renders every node type`() {
        assertThat(standard.describe()).isEqualTo("(30 + 2.90% + (5))")
        assertThat(Capped(CheapestOf(Percent(5), Flat(25)), 500).describe()).isEqualTo("min(cheapest(0.05%, 25), 500)")
        assertThat(AllOf().describe()).isEqualTo("()")
        assertThat(Percent(1_000).describe()).isEqualTo("10.00%")
    }

    // ---- flyweight ----

    @Test
    fun `the same code always gives the same instance`() {
        val a = MerchantCategory.of("5411")
        val b = MerchantCategory.of("5411")
        assertThat(a).isSameAs(b)
        assertThat(a.description).isEqualTo("Grocery stores, supermarkets")
        assertThat(MerchantCategory.of("5812")).isNotSameAs(a)
    }

    @Test
    fun `an unknown code is rejected and never pooled`() {
        assertThatThrownBy { MerchantCategory.of("0000") }
            .isInstanceOf(IllegalArgumentException::class.java)
            .hasMessage("unknown MCC: 0000")
    }

    @Test
    fun `eight threads asking at once share one instance and build it at most once`() {
        val before = MerchantCategory.instancesCreated
        val seen: MutableSet<MerchantCategory> = Collections.synchronizedSet(Collections.newSetFromMap(IdentityHashMap()))
        val go = CountDownLatch(1)
        val threads = List(8) {
            thread {
                go.await()
                repeat(2_000) { seen += MerchantCategory.of("4111") }
            }
        }
        go.countDown()
        threads.forEach { it.join() }
        assertThat(seen).`as`("distinct instances handed out").hasSize(1)
        assertThat(MerchantCategory.instancesCreated - before).`as`("constructor runs").isLessThanOrEqualTo(1)
    }
}
