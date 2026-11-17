package workbench.functional.l08

import java.math.RoundingMode
import java.time.LocalDate

fun planShopping(items: List<Item>, shops: Map<String, Shop>, today: LocalDate): ShoppingPlan {
    val live = items.filterNot { it.crossedOff }
    val (known, unknown) = live.partition { it.shopId in shops }
    val (due, waiting) = known.partition { item ->
        !item.neededOn.minusDays(shops.getValue(item.shopId).deliveryDays.toLong()).isAfter(today)
    }
    val orders = due.groupBy { it.shopId }
        .toSortedMap()                                         // orders sorted by shop id
        .map { (shopId, its) ->
            val total = its.sumOf { it.price }                 // the BigDecimal overload of sumOf
            val discount = (total * shops.getValue(shopId).discountRate)
                .setScale(2, RoundingMode.HALF_EVEN)           // scale 2, or 3.63950 != 3.64 in equals
            Order(shopId, total, discount, total - discount)
        }
    return ShoppingPlan(orders, waiting.map { it.id }, unknown.map { it.id })
}

fun Budget.posting(orders: List<Order>, ref: String): Budget =
    copy(entries = entries.addingAll(orders.flatMap { o ->
        listOf(Entry("shop:${o.shopId}", o.toPay, ref), Entry("discount-saved", o.discount, ref))
    }))                                                        // a new list; the old one is untouched
