package workbench.events.l01.demo.exhaustive

sealed interface PaymentEvent { val paymentId: String }
data class PaymentAuthorized(override val paymentId: String, val cents: Long) : PaymentEvent
data class PaymentDeclined(override val paymentId: String, val reason: String) : PaymentEvent

sealed interface MoneyMovement : PaymentEvent { val cents: Long }
data class PaymentCaptured(override val paymentId: String, override val cents: Long) : MoneyMovement
data class PaymentRefunded(override val paymentId: String, override val cents: Long) : MoneyMovement

// Step 2: uncomment this line, then run the demo again (Gradle compiles it first).
// data class PaymentDisputed(override val paymentId: String, val cents: Long) : PaymentEvent

/** One branch per leaf, no else: checked by the compiler. */
fun summary(e: PaymentEvent): String = when (e) {
    is PaymentAuthorized -> "${e.paymentId} authorized ${e.cents}"
    is PaymentDeclined -> "${e.paymentId} declined: ${e.reason}"
    is PaymentCaptured -> "${e.paymentId} captured ${e.cents}"
    is PaymentRefunded -> "${e.paymentId} refunded ${e.cents}"
}

/** One branch covers the whole sealed middle level, and the check still holds. */
fun movesMoney(e: PaymentEvent): Boolean = when (e) {
    is MoneyMovement -> true
    is PaymentAuthorized, is PaymentDeclined -> false
}

/** An else branch: compiles today, and after every change anyone ever makes. */
fun label(e: PaymentEvent): String = when (e) {
    is PaymentCaptured -> "capture"
    is PaymentRefunded -> "refund"
    else -> "other"
}

fun main() {
    val events = listOf(
        PaymentAuthorized("pay_7781", 1_999),
        PaymentCaptured("pay_7781", 1_999),
        PaymentRefunded("pay_7781", 500),
        PaymentDeclined("pay_7782", "CARD_EXPIRED"),
    )
    for (e in events) println("%-34s moves money: %-5s label: %s".format(summary(e), movesMoney(e), label(e)))
}
