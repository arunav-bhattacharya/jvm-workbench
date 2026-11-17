package workbench.functional.l08

import kotlinx.collections.immutable.PersistentList
import java.math.BigDecimal
import java.time.LocalDate

// The types for the shopping job. Every one is a data class of vals holding immutable values.
// You don't need to change this file.

/** One line on the shopping list. */
data class Item(
    val id: String,
    val shopId: String,
    val price: BigDecimal,             // in euros, scale 2: BigDecimal("12.50")
    val neededOn: LocalDate,           // the day a planned meal needs it
    val crossedOff: Boolean = false,   // crossed off the list: we have it after all
)

/** [discountRate] is a fraction: 0.029 means 2.9 % off. The shop needs [deliveryDays] to deliver. */
data class Shop(val id: String, val discountRate: BigDecimal, val deliveryDays: Int)

data class Order(val shopId: String, val total: BigDecimal, val discount: BigDecimal, val toPay: BigDecimal)

/** What the job decided to do today. */
data class ShoppingPlan(
    val orders: List<Order>,         // one per shop with items due, sorted by shop id
    val waiting: List<String>,       // ids of items not yet due to be ordered, in input order
    val unknownShops: List<String>,  // ids of items whose shop we don't know, in input order
)

data class Entry(val account: String, val amount: BigDecimal, val ref: String)

/** The household budget book is a value: posting returns a new Budget, and the old one stays as it was. */
data class Budget(val entries: PersistentList<Entry>)

// The shell's dependencies: everything that does I/O.

/** The app's storage on the phone. */
interface HomeStore {
    fun shoppingList(): List<Item>
    fun shops(): Map<String, Shop>
    fun loadBudget(): Budget
    fun saveBudget(budget: Budget)
}

/** Sends an order to a shop's website. */
fun interface ShopApi {
    fun send(order: Order)
}
