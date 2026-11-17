package workbench.patterns.l03

@DslMarker
annotation class OrderDsl

data class Item(val name: String, val priceCents: Long)

data class Order(
    val customer: String,
    val currency: String,
    val items: List<Item>,
    val notes: Map<String, String>,
) {
    val totalCents: Long get() = items.sumOf { it.priceCents }
}

@OrderDsl   // inside items { }, the outer builder's members are no longer implicitly in scope
class ItemsBuilder {
    private val items = mutableListOf<Item>()

    fun item(name: String, priceCents: Long) {
        items += Item(name, priceCents)
    }

    fun build(): List<Item> = items.toList()             // a copy, not a view
}

@OrderDsl
class OrderBuilder {
    var customer: String? = null
    var currency: String = "EUR"
    private val items = mutableListOf<Item>()
    private val notes = linkedMapOf<String, String>()

    // a lambda with receiver: inside block, `this` is the ItemsBuilder
    fun items(block: ItemsBuilder.() -> Unit) {
        items += ItemsBuilder().apply(block).build()
    }

    fun note(key: String, value: String) {
        notes[key] = value
    }

    fun build(): Order {
        // 1. check the whole order in one place: the reason a builder still earns its keep
        val who = customer
        require(!who.isNullOrBlank()) { "customer is required" }
        require(currency.matches(Regex("[A-Z]{3}"))) { "currency must be three capital letters, got '$currency'" }
        require(items.isNotEmpty()) { "an order needs at least one item" }
        items.firstOrNull { it.priceCents <= 0 }?.let {
            throw IllegalArgumentException("item ${it.name} must have a positive price")
        }
        // 2. copy, so later changes to the builder can't reach an order that was already built
        return Order(who, currency, items.toList(), notes.toMap())
    }
}

fun order(block: OrderBuilder.() -> Unit): Order =
    OrderBuilder().apply(block).build()
