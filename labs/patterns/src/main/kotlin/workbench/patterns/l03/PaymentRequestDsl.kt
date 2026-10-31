package workbench.patterns.l03

/** Marks the builder classes of the payment DSL, so an inner block can't silently reach an outer builder. */
@DslMarker
annotation class PaymentDsl

data class LineItem(val sku: String, val amountMinor: Long)

data class PaymentRequest(
    val idempotencyKey: String,
    val currency: String,
    val lineItems: List<LineItem>,
    val metadata: Map<String, String>,
) {
    /** The total is always the sum of the line items, so it can never disagree with them. */
    val amountMinor: Long get() = lineItems.sumOf { it.amountMinor }
}

/**
 * Builds the `lineItems { ... }` block. TODO: annotate this class with [PaymentDsl].
 */
class LineItemsBuilder {
    /** Adds one line item. */
    fun item(sku: String, amountMinor: Long) {
        TODO("remember the item")
    }

    /** The items added so far, as a read-only copy. */
    fun build(): List<LineItem> = TODO("return a copy of the items")
}

/**
 * Builds a [PaymentRequest]:
 *
 * ```
 * val req = paymentRequest {
 *     idempotencyKey = "order-981-attempt-1"
 *     currency = "EUR"                      // optional, EUR by default
 *     lineItems {
 *         item("sku-1", 1_000)
 *         item("sku-2", 500)
 *     }
 *     metadata("orderId", "981")
 * }
 * ```
 *
 * TODO: annotate this class with [PaymentDsl].
 */
class PaymentRequestBuilder {
    var idempotencyKey: String? = null
    var currency: String = "EUR"

    /** Adds the items from [block]. Calling it twice adds both sets, in order. */
    fun lineItems(block: LineItemsBuilder.() -> Unit) {
        TODO("run the block on a LineItemsBuilder and keep its items")
    }

    /** Adds one metadata entry. A later value for the same key replaces the earlier one. */
    fun metadata(key: String, value: String) {
        TODO("remember the entry")
    }

    /**
     * Validates the whole request and returns it. Throws IllegalArgumentException with a message
     * that contains:
     * - "idempotency key" when the key is missing or blank
     * - "currency" when [currency] is not three capital letters, such as "EUR"
     * - "line item" when there are no items, or when an item's amount is zero or negative
     *
     * The request holds copies of the items and metadata: changing the builder later must not
     * change a request that was already built.
     */
    fun build(): PaymentRequest = TODO("validate, then copy into a PaymentRequest")
}

/** The DSL entry point. Not inline, on purpose: the tests run against your code and the solution. */
fun paymentRequest(block: PaymentRequestBuilder.() -> Unit): PaymentRequest =
    TODO("make a builder, apply the block, build")
