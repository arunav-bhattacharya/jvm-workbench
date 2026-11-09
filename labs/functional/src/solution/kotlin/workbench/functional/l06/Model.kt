package workbench.functional.l06

// The types the settlement desk works with. You don't need to change this file.

enum class Status { AUTHORIZED, CAPTURED, REFUNDED, DECLINED }

data class Money(val minor: Long, val currency: String)

data class Payment(val id: String, val amount: Money, val status: Status, val cardToken: String?)

/** Posts payments. Returns the new ledger entry id, or null when this payment id was posted before. */
fun interface Ledger {
    fun post(payment: Payment): String?
}

sealed interface SettleResult {
    data class Posted(val entryId: String) : SettleResult
    data class AlreadyPosted(val paymentId: String) : SettleResult
}

/** What the gateway receives. [reference] is the idempotency key the gateway deduplicates on. */
class PaymentRequest {
    var amount: Money? = null
    var merchantId: String = ""
    var reference: String = ""
    val metadata = Metadata()
}

class Metadata {
    var channel: String = ""
    var reference: String = ""   // the merchant's own free-text reference, not the idempotency key
}

data class Order(val id: String, val merchantId: String, val total: Money)

data class Merchant(val id: String, val name: String, val scheduleId: String)

data class FeeSchedule(val id: String, val name: String, val rateBps: Int)
