package workbench.functional.l08

import java.time.LocalDate

/**
 * The functional core: decides today's shopping from plain values. No clock, no store, no shop, no
 * println. The same arguments must always give an equal plan. The rules, from LegacyShoppingJob:
 * - crossed-off items are skipped;
 * - an item whose shop isn't in [shops] goes to unknownShops;
 * - an item is due when neededOn minus the shop's deliveryDays is not after [today]; otherwise it goes
 *   to waiting;
 * - due items are summed per shop into one Order: discount = total * discountRate, rounded HALF_EVEN
 *   to 2 decimals, and toPay = total - discount. Orders are sorted by shop id.
 */
fun planShopping(items: List<Item>, shops: Map<String, Shop>, today: LocalDate): ShoppingPlan =
    TODO("filterNot, partition, groupBy and sumOf, as in the collections lesson")

/**
 * Returns a new Budget with two entries per order, in order: Entry("shop:<shopId>", toPay, ref),
 * then Entry("discount-saved", discount, ref). The receiver is not changed.
 */
fun Budget.posting(orders: List<Order>, ref: String): Budget =
    TODO("copy(entries = entries.addingAll(...))")
