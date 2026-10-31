package workbench.generics.l05

/** Payment events. An interface hierarchy, so a handler of PaymentEvent can serve any of them. */
interface PaymentEvent {
    val paymentId: String
}

data class CardAuthorized(override val paymentId: String, val cents: Long) : PaymentEvent

data class RefundIssued(override val paymentId: String, val cents: Long) : PaymentEvent
