package workbench.functional.l08

import java.math.BigDecimal
import java.math.RoundingMode
import java.time.Clock
import java.time.LocalDate

/**
 * The job as it runs today, every morning. It gives the right answers, but the rules, the clock and the
 * I/O are woven together, so the only way to test a discount rule is with a fake store, a fake shop and
 * a fixed clock. Read it to find the rules. Don't edit it: ShoppingCore.kt and ShoppingJob.kt replace it.
 */
class LegacyShoppingJob(private val store: HomeStore, private val shopApi: ShopApi, private val clock: Clock) {
    fun run() {
        val today = LocalDate.now(clock)
        val shops = store.shops()
        val totals = mutableMapOf<String, BigDecimal>()
        for (item in store.shoppingList()) {
            if (item.crossedOff) continue
            val shop = shops[item.shopId]
            if (shop == null) { println("unknown shop ${item.shopId} for ${item.id}"); continue }
            if (item.neededOn.minusDays(shop.deliveryDays.toLong()).isAfter(today)) { println("waiting ${item.id}"); continue }
            totals[item.shopId] = (totals[item.shopId] ?: BigDecimal.ZERO) + item.price
        }
        var budget = store.loadBudget()
        for ((shopId, total) in totals.toSortedMap()) {
            val discount = (total * shops.getValue(shopId).discountRate).setScale(2, RoundingMode.HALF_EVEN)
            val order = Order(shopId, total, discount, total - discount)
            shopApi.send(order)
            budget = Budget(
                budget.entries
                    .adding(Entry("shop:$shopId", order.toPay, "shopping-$today"))
                    .adding(Entry("discount-saved", discount, "shopping-$today"))
            )
            store.saveBudget(budget)
        }
    }
}
