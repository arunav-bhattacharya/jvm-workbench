package workbench.functional.l08

import java.time.Clock

/**
 * The imperative shell: reads, calls the core, then carries out the plan. It holds no rules.
 * run() must:
 * 1. read today's date from [clock] once, and load the shopping list and the shops;
 * 2. call planShopping;
 * 3. send every order, in plan order;
 * 4. post all orders to the budget with the ref "shopping-<today>" and save it ONCE;
 * 5. return the plan.
 */
class ShoppingJob(private val store: HomeStore, private val shopApi: ShopApi, private val clock: Clock) {
    fun run(): ShoppingPlan = TODO("read, decide, act")
}
