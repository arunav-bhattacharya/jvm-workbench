package workbench.events.l02.demo

// The lesson 1 hierarchy, with plain String ids and Long cents to keep the demos short.
sealed interface PaymentEvent { val paymentId: String }
data class PaymentAuthorized(override val paymentId: String, val cents: Long) : PaymentEvent
data class PaymentDeclined(override val paymentId: String, val reason: String) : PaymentEvent

sealed interface MoneyMovement : PaymentEvent { val cents: Long }
data class PaymentCaptured(override val paymentId: String, override val cents: Long) : MoneyMovement
data class PaymentRefunded(override val paymentId: String, override val cents: Long) : MoneyMovement
