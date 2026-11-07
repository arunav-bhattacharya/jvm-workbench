package workbench.generics.l11

/** Events: produced by the bus, consumed by handlers. */
interface PaymentEvent { val paymentId: String }
data class CardAuthorized(override val paymentId: String, val cents: Long) : PaymentEvent
data class RefundIssued(override val paymentId: String, val cents: Long) : PaymentEvent

/** Entities with ids of different types. */
data class Merchant(override val id: Long, val name: String) : Entity<Long>
data class Settlement(override val id: String, val cents: Long) : Entity<String>
