package workbench.patterns.l03

@DslMarker
annotation class PaymentDsl

data class LineItem(val sku: String, val amountMinor: Long)

data class PaymentRequest(
    val idempotencyKey: String,
    val currency: String,
    val lineItems: List<LineItem>,
    val metadata: Map<String, String>,
) {
    val amountMinor: Long get() = lineItems.sumOf { it.amountMinor }
}

@PaymentDsl   // inside lineItems { }, the outer builder's members are no longer implicitly in scope
class LineItemsBuilder {
    private val items = mutableListOf<LineItem>()

    fun item(sku: String, amountMinor: Long) {
        items += LineItem(sku, amountMinor)
    }

    fun build(): List<LineItem> = items.toList()          // a copy, not a view
}

@PaymentDsl
class PaymentRequestBuilder {
    var idempotencyKey: String? = null
    var currency: String = "EUR"
    private val items = mutableListOf<LineItem>()
    private val metadata = linkedMapOf<String, String>()

    // a lambda with receiver: inside block, `this` is the LineItemsBuilder
    fun lineItems(block: LineItemsBuilder.() -> Unit) {
        items += LineItemsBuilder().apply(block).build()
    }

    fun metadata(key: String, value: String) {
        metadata[key] = value
    }

    fun build(): PaymentRequest {
        // 1. validate the whole request in one place: the reason a builder still earns its keep
        val key = idempotencyKey
        require(!key.isNullOrBlank()) { "idempotency key is required" }
        require(currency.matches(Regex("[A-Z]{3}"))) { "currency must be three capital letters, got '$currency'" }
        require(items.isNotEmpty()) { "a payment needs at least one line item" }
        items.firstOrNull { it.amountMinor <= 0 }?.let {
            throw IllegalArgumentException("line item ${it.sku} must have a positive amount")
        }
        // 2. copy, so later changes to the builder can't reach a request that was already built
        return PaymentRequest(key, currency, items.toList(), metadata.toMap())
    }
}

fun paymentRequest(block: PaymentRequestBuilder.() -> Unit): PaymentRequest =
    PaymentRequestBuilder().apply(block).build()
