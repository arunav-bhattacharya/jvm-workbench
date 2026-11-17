package workbench.functional.l08

import kotlinx.collections.immutable.persistentListOf
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.math.BigDecimal
import java.time.Clock
import java.time.LocalDate
import java.time.ZoneOffset

class FunctionalCoreTest {

    private val today = LocalDate.of(2026, 3, 10)
    private val shops = mapOf(
        "s-market" to Shop("s-market", BigDecimal("0.029"), deliveryDays = 2),
        "s-farm" to Shop("s-farm", BigDecimal("0.015"), deliveryDays = 7),
    )

    private fun item(id: String, shop: String, euros: String, inDays: Long, crossedOff: Boolean = false) =
        Item(id, shop, BigDecimal(euros), today.plusDays(inDays), crossedOff)

    // ---- the core: plain values in, a plan out; no clock, no store, no fakes ----

    @Test
    fun `due items are summed per shop with the discount rounded to cents`() {
        val plan = planShopping(listOf(item("i1", "s-market", "100.00", 1), item("i2", "s-market", "25.50", 2)), shops, today)
        // 125.50 * 0.029 = 3.63950, rounded HALF_EVEN to 3.64
        assertThat(plan.orders).containsExactly(Order("s-market", BigDecimal("125.50"), BigDecimal("3.64"), BigDecimal("121.86")))
    }

    @Test
    fun `items needed after the delivery time are waiting`() {
        val plan = planShopping(listOf(item("i1", "s-market", "10.00", 3), item("i2", "s-market", "20.00", 2)), shops, today)
        assertThat(plan.waiting).containsExactly("i1")
        assertThat(plan.orders.single().total).isEqualTo(BigDecimal("20.00"))
    }

    @Test
    fun `crossed-off items are skipped and unknown shops are reported`() {
        val plan = planShopping(
            listOf(item("i1", "s-market", "10.00", 1, crossedOff = true), item("i2", "s-corner", "9.90", 1), item("i3", "s-market", "40.00", 1)),
            shops, today,
        )
        assertThat(plan.unknownShops).containsExactly("i2")
        assertThat(plan.waiting).isEmpty()
        assertThat(plan.orders.map { it.total }).containsExactly(BigDecimal("40.00"))
    }

    @Test
    fun `orders are sorted by shop id`() {
        val plan = planShopping(listOf(item("i1", "s-market", "50.00", 1), item("i2", "s-farm", "200.00", 1)), shops, today)
        assertThat(plan.orders.map { it.shopId }).containsExactly("s-farm", "s-market")
        assertThat(plan.orders[0]).isEqualTo(Order("s-farm", BigDecimal("200.00"), BigDecimal("3.00"), BigDecimal("197.00")))
    }

    @Test
    fun `an empty list gives an empty plan`() {
        assertThat(planShopping(emptyList(), shops, today)).isEqualTo(ShoppingPlan(emptyList(), emptyList(), emptyList()))
    }

    @Test
    fun `the date is an input, so a later day can order a waiting item`() {
        val items = listOf(item("i1", "s-farm", "80.00", 10))
        assertThat(planShopping(items, shops, today).waiting).containsExactly("i1")
        assertThat(planShopping(items, shops, today.plusDays(3)).waiting).isEmpty()
    }

    @Test
    fun `posting returns a new budget and leaves the old one alone`() {
        val before = Budget(persistentListOf(Entry("opening", BigDecimal("0.00"), "init")))
        val after = before.posting(listOf(Order("s-market", BigDecimal("125.50"), BigDecimal("3.64"), BigDecimal("121.86"))), "shopping-2026-03-10")
        assertThat(after.entries).containsExactly(
            Entry("opening", BigDecimal("0.00"), "init"),
            Entry("shop:s-market", BigDecimal("121.86"), "shopping-2026-03-10"),
            Entry("discount-saved", BigDecimal("3.64"), "shopping-2026-03-10"),
        )
        assertThat(before.entries).`as`("the budget we posted to").containsExactly(Entry("opening", BigDecimal("0.00"), "init"))
    }

    // ---- the shell: one test with fakes checks the wiring ----

    private class FakeStore(private val items: List<Item>, private val shops: Map<String, Shop>) : HomeStore {
        val saved = mutableListOf<Budget>()
        override fun shoppingList() = items
        override fun shops() = shops
        override fun loadBudget() = Budget(persistentListOf())
        override fun saveBudget(budget: Budget) { saved += budget }
    }

    @Test
    fun `the shell sends every order and saves the budget once`() {
        val store = FakeStore(listOf(item("i1", "s-market", "50.00", 1), item("i2", "s-farm", "200.00", 1), item("i3", "s-market", "5.00", 5)), shops)
        val sent = mutableListOf<Order>()
        val clock = Clock.fixed(today.atStartOfDay().toInstant(ZoneOffset.UTC), ZoneOffset.UTC)

        val plan = ShoppingJob(store, { sent += it }, clock).run()

        assertThat(sent).isEqualTo(plan.orders)
        assertThat(sent.map { it.shopId }).containsExactly("s-farm", "s-market")
        assertThat(plan.waiting).containsExactly("i3")
        assertThat(store.saved).`as`("budget saves").hasSize(1)
        assertThat(store.saved.single().entries.map { it.ref }.distinct()).containsExactly("shopping-2026-03-10")
        assertThat(store.saved.single().entries).hasSize(4)
    }
}
