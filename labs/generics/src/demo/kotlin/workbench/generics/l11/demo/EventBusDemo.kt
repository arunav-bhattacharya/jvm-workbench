package workbench.generics.l11.demo

import kotlin.reflect.KClass
import kotlin.reflect.safeCast

interface PaymentEvent { val paymentId: String }
data class CardAuthorized(override val paymentId: String, val cents: Long) : PaymentEvent
data class RefundIssued(override val paymentId: String, val cents: Long) : PaymentEvent

/** The smallest typed router: one list of adapters, each of which checks the event's class. */
class Router {
    private val adapters = mutableListOf<(PaymentEvent) -> Unit>()

    fun <E : PaymentEvent> on(type: KClass<E>, handler: (E) -> Unit) {
        // adapters.add(handler)                                       // wrong move 1
        adapters.add { event -> type.safeCast(event)?.let(handler) }   // takes any event, passes on only an E
    }

    fun publish(event: PaymentEvent) = adapters.forEach { it(event) }
}

fun main() {
    val router = Router()
    val auditAll: (PaymentEvent) -> Unit = { println("audit ${it.paymentId}") }
    router.on(CardAuthorized::class) { println("fraud check ${it.cents}") }
    router.on(CardAuthorized::class, auditAll)       // a handler for the supertype fits: in P
    router.on(RefundIssued::class) { println("refund ${it.cents}") }

    router.publish(CardAuthorized("pay_1", 1_200))   // events flow out of the publisher...
    router.publish(RefundIssued("pay_2", 500))       // ...and into the handlers that accept them

    // Wrong move 2. Uncomment, predict the error, then run.
    // router.on(PaymentEvent::class) { e: CardAuthorized -> println(e.cents) }
}
