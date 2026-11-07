package workbench.events.l01.demo.values

import java.math.BigDecimal

@JvmInline
value class PaymentId(val value: String) {
    init { require(Regex("pay_[A-Za-z0-9]{4,24}").matches(value)) { "invalid payment id: '$value'" } }
    override fun toString(): String = value
}

@JvmInline
value class Money(val minor: Long) {
    init { require(minor >= 0) { "amount must not be negative: $minor" } }
    override fun toString(): String = BigDecimal.valueOf(minor, 2).toPlainString()
}

data class PaymentCaptured(val paymentId: PaymentId, val amount: Money)

/** The same event with raw types: nothing stops a caller from swapping the two Longs. */
data class RawRefund(val paymentId: String, val amountMinor: Long, val feeMinor: Long)

fun main() {
    println(PaymentCaptured(PaymentId("pay_7781"), Money(1_999)))
    println(RawRefund("pay_7781", 30, 500))               // amount and fee swapped: compiles, wrong money

    // Step 2: uncomment. The arguments are in the wrong order.
    // println(PaymentCaptured(Money(1_999), PaymentId("pay_7781")))

    for (attempt in listOf({ PaymentId("7781") }, { Money(-500) })) {
        try {
            attempt()
        } catch (e: IllegalArgumentException) {
            println("refused: ${e.message}")
        }
    }

    // What the JVM stores: the value classes are gone, only their one field is left
    for (f in PaymentCaptured::class.java.declaredFields) println("field ${f.name}: ${f.type.name}")
}
