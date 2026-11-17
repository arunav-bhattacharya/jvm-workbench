package workbench.patterns.l03

/** Marks the builder classes of the order DSL, so an inner block can't silently reach an outer builder. */
@DslMarker
annotation class OrderDsl

data class Item(val name: String, val priceCents: Long)

data class Order(
    val customer: String,
    val currency: String,
    val items: List<Item>,
    val notes: Map<String, String>,
) {
    /** The total is always the sum of the items, so it can never disagree with them. */
    val totalCents: Long get() = items.sumOf { it.priceCents }
}

/**
 * Builds the `items { ... }` block. TODO: annotate this class with [OrderDsl].
 */
class ItemsBuilder {
    /** Adds one item. */
    fun item(name: String, priceCents: Long) {
        TODO("remember the item")
    }

    /** The items added so far, as a read-only copy. */
    fun build(): List<Item> = TODO("return a copy of the items")
}

/**
 * Builds an [Order]:
 *
 * ```
 * val o = order {
 *     customer = "anna@example.com"
 *     currency = "EUR"                      // optional, EUR by default
 *     items {
 *         item("rye bread", 450)
 *         item("oat milk", 220)
 *     }
 *     note("door", "blue gate")
 * }
 * ```
 *
 * TODO: annotate this class with [OrderDsl].
 */
class OrderBuilder {
    var customer: String? = null
    var currency: String = "EUR"

    /** Adds the items from [block]. Calling it twice adds both sets, in order. */
    fun items(block: ItemsBuilder.() -> Unit) {
        TODO("run the block on an ItemsBuilder and keep its items")
    }

    /** Adds one note for the driver. A later value for the same key replaces the earlier one. */
    fun note(key: String, value: String) {
        TODO("remember the note")
    }

    /**
     * Checks the whole order and returns it. Throws IllegalArgumentException with a message
     * that contains:
     * - "customer" when the customer is missing or blank
     * - "currency" when [currency] is not three capital letters, such as "EUR"
     * - "item" when there are no items, or when an item's price is zero or negative
     *
     * The order holds copies of the items and notes: changing the builder later must not
     * change an order that was already built.
     */
    fun build(): Order = TODO("check, then copy into an Order")
}

/** The DSL entry point. Not inline, on purpose: the tests run against your code and the solution. */
fun order(block: OrderBuilder.() -> Unit): Order =
    TODO("make a builder, apply the block, build")
