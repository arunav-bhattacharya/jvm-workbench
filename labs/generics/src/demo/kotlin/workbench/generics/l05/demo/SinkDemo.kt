package workbench.generics.l05.demo

interface PaymentEvent { val paymentId: String }
data class CardAuthorized(override val paymentId: String, val cents: Long) : PaymentEvent
data class RefundIssued(override val paymentId: String, val cents: Long) : PaymentEvent

/** A consumer: T only goes in. `in` tells the compiler so. */
interface Sink<in T> {
    fun accept(item: T)
}

/** An audit log takes ANY payment event. */
class AuditLog : Sink<PaymentEvent> {
    override fun accept(item: PaymentEvent) = println("audit: ${item.paymentId}")
}

/** Needs a place to put card authorizations. Any sink that takes them will do. */
fun forwardAuthorizations(events: List<CardAuthorized>, to: Sink<CardAuthorized>) {
    for (e in events) to.accept(e)
}

fun main() {
    val audit: Sink<PaymentEvent> = AuditLog()
    forwardAuthorizations(listOf(CardAuthorized("pay_1", 1_200), CardAuthorized("pay_2", 350)), audit)

    val cardSink: Sink<CardAuthorized> = audit        // a Sink<PaymentEvent> IS a Sink<CardAuthorized>
    cardSink.accept(CardAuthorized("pay_3", 99))

    // Wrong move. Uncomment, predict the error, then run.
    // val back: Sink<PaymentEvent> = cardSink
}
