package workbench.events.l01.demo.edge

@JvmInline
value class PaymentId(val value: String) {
    init { require(Regex("pay_[A-Za-z0-9]{4,24}").matches(value)) { "invalid payment id: '$value'" } }
    override fun toString(): String = value
}

@JvmInline
value class Money(val minor: Long) {
    init { require(minor >= 0) { "amount must not be negative: $minor" } }
    override fun toString(): String = "$minor cents"
}

sealed interface PaymentEvent { val paymentId: PaymentId }
data class PaymentCaptured(override val paymentId: PaymentId, val amount: Money) : PaymentEvent
data class PaymentRefunded(override val paymentId: PaymentId, val amount: Money) : PaymentEvent

sealed interface Parsed {
    data class Ok(val event: PaymentEvent) : Parsed
    data class Rejected(val reason: String) : Parsed
}

/** The edge: raw fields in, a model value or a reason out. It never throws. */
fun parse(fields: Map<String, String>): Parsed {
    fun field(name: String) = fields[name] ?: throw IllegalArgumentException("missing field '$name'")
    fun amount(): Money {
        val raw = field("amountMinor")
        return Money(raw.toLongOrNull() ?: throw IllegalArgumentException("amountMinor is not a whole number: '$raw'"))
    }
    return try {
        when (val type = field("type")) {
            "captured" -> Parsed.Ok(PaymentCaptured(PaymentId(field("paymentId")), amount()))
            "refunded" -> Parsed.Ok(PaymentRefunded(PaymentId(field("paymentId")), amount()))
            else -> Parsed.Rejected("unknown event type: '$type'")
        }
    } catch (e: IllegalArgumentException) {
        Parsed.Rejected(e.message ?: "invalid event")       // a constructor or a reader said no
    }
}

fun main() {
    val inbox = listOf(
        mapOf("type" to "captured", "paymentId" to "pay_7781", "amountMinor" to "1999"),
        mapOf("type" to "captured", "paymentId" to "pay_7782", "amountMinor" to "12.50"),
        mapOf("type" to "refunded", "paymentId" to "7781", "amountMinor" to "500"),
        mapOf("type" to "refunded", "paymentId" to "pay_7781", "amountMinor" to "-500"),
        mapOf("type" to "captured", "paymentId" to "pay_7783"),
        mapOf("type" to "declined", "paymentId" to "pay_7784", "reason" to "CARD_EXPIRED"),
    )
    var accepted = 0
    for (fields in inbox) {
        when (val p = parse(fields)) {
            is Parsed.Ok -> { accepted++; println("OK        ${p.event}") }
            is Parsed.Rejected -> println("REJECTED  ${p.reason}")
        }
    }
    println("$accepted accepted, ${inbox.size - accepted} rejected")
}
