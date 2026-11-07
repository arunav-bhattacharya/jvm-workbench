package workbench.patterns.l06

// Alerts (what happened) and channels (how it travels) vary on their own: 2 + 2 pieces, not 2 x 2.

// the implementor side: one method, so a lambda is enough
fun interface AlertChannel { fun deliver(to: String, body: String): String }

private val sms = AlertChannel { to, body -> "SMS   to $to: $body" }
private val email = AlertChannel { to, body -> "EMAIL to $to: $body" }

// the abstraction side: what happened. Each alert HOLDS a channel instead of being one.
sealed interface PaymentAlert {
    val channel: AlertChannel
    fun raise(to: String): String

    data class PaymentFailed(override val channel: AlertChannel, val paymentId: String, val reason: String) : PaymentAlert {
        override fun raise(to: String) = channel.deliver(to, "payment $paymentId failed: $reason")
    }

    data class FraudSuspected(override val channel: AlertChannel, val last4: String, val score: Int) : PaymentAlert {
        override fun raise(to: String) = channel.deliver(to, "card ****$last4 flagged, risk $score")
    }
}

fun main() {
    val channels = listOf(sms, email)
    for (ch in channels) {
        println(PaymentAlert.PaymentFailed(ch, "pay_881", "issuer declined (51)").raise("on-call"))
        println(PaymentAlert.FraudSuspected(ch, "4242", 91).raise("risk-team"))
    }
}
