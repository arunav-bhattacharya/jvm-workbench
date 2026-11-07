package workbench.generics.l08

import java.math.BigDecimal

sealed interface PaymentEvent { val paymentId: String }
data class CardAuthorized(override val paymentId: String, val cents: Long) : PaymentEvent
data class RefundIssued(override val paymentId: String, val cents: Long) : PaymentEvent

/** An amount in minor units. `Money.parse("12.50 EUR")` is `Money(1250, "EUR")`. */
data class Money(val cents: Long, val currency: String) {
    companion object {
        @JvmStatic
        fun parse(text: String): Money {
            val (amount, currency) = text.trim().split(" ")
            return Money(BigDecimal(amount).movePointRight(2).longValueExact(), currency)
        }
    }
}
