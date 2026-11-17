package workbench.functional.l08

import java.time.Clock
import java.time.LocalDate

class ShoppingJob(private val store: HomeStore, private val shopApi: ShopApi, private val clock: Clock) {
    fun run(): ShoppingPlan {
        val today = LocalDate.now(clock)                                         // 1. read
        val plan = planShopping(store.shoppingList(), store.shops(), today)      // 2. decide
        plan.orders.forEach(shopApi::send)                                       // 3. act
        store.saveBudget(store.loadBudget().posting(plan.orders, "shopping-$today"))
        return plan
    }
}
