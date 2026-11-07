package workbench.generics.l09.demo

import kotlin.reflect.KClass

sealed interface PaymentEvent { val paymentId: String }
data class CardAuthorized(override val paymentId: String, val cents: Long) : PaymentEvent
data class RefundIssued(override val paymentId: String, val cents: Long) : PaymentEvent

fun main() {
    val events: List<PaymentEvent> = listOf(CardAuthorized("pay_1", 1_200), RefundIssued("pay_2", 500))
    for (event in events) {
        val k: KClass<out PaymentEvent> = event::class      // the class of SOME PaymentEvent
        println("${event.paymentId}: ${k.simpleName}, is a card: ${k == CardAuthorized::class}")
    }

    val exact: KClass<CardAuthorized> = CardAuthorized::class   // a class literal is exact
    val note: String? = events.firstOrNull()?.paymentId
    val noteClass: KClass<out String>? = note?.let { it::class }  // no value, no class
    println("exact = ${exact.simpleName}, noteClass = ${noteClass?.simpleName}")

    // Wrong moves. Uncomment one at a time, predict the error, then run.
    // val strict: KClass<PaymentEvent> = events[0]::class      // 1
    // val nullable = note::class                             // 2
    val kn: KClass<String?>? = null                        // 3
}
