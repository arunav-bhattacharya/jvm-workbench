package workbench.events.l01

/**
 * Every event the payments service can see. The list is closed: every direct subtype is declared
 * in this package and module, so a `when` over a PaymentEvent can be checked for exhaustiveness.
 */
sealed interface PaymentEvent {
    val paymentId: PaymentId
}

/** The issuer reserved [amount] on the card. No money has moved yet. */
data class PaymentAuthorized(override val paymentId: PaymentId, val amount: Money) : PaymentEvent {
    // TODO 3: refuse an amount of zero ("authorized amount must be positive: <amount>")
}

/** The issuer said no. */
data class PaymentDeclined(override val paymentId: PaymentId, val reason: DeclineReason) : PaymentEvent

/**
 * The events that move money. Sealed again, one level down: a handler or a `when` branch for
 * MoneyMovement covers captures and refunds, and the compiler still knows there are only two.
 */
sealed interface MoneyMovement : PaymentEvent {
    val amount: Money
}

data class PaymentCaptured(override val paymentId: PaymentId, override val amount: Money) : MoneyMovement {
    // TODO 3: refuse an amount of zero
}

data class PaymentRefunded(override val paymentId: PaymentId, override val amount: Money) : MoneyMovement {
    // TODO 3: refuse an amount of zero
}

enum class DeclineReason { INSUFFICIENT_FUNDS, SUSPECTED_FRAUD, CARD_EXPIRED }
