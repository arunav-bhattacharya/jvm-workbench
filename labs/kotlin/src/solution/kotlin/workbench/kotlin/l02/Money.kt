package workbench.kotlin.l02

import java.math.BigDecimal

/**
 * An amount in euro cents. At run time it is a plain `long` wherever the compiler can manage it.
 */
@JvmInline
value class Money(val cents: Long) : Comparable<Money> {
    init {
        // runs in Money.constructor-impl(long), on every Money(...) call
        require(cents >= 0) { "amount must be non-negative, was $cents" }
    }

    // addExact and multiplyExact throw ArithmeticException instead of wrapping around
    operator fun plus(other: Money): Money = Money(Math.addExact(cents, other.cents))

    operator fun times(quantity: Int): Money = Money(Math.multiplyExact(cents, quantity.toLong()))

    override fun compareTo(other: Money): Int = cents.compareTo(other.cents)

    // keep the explicit ': String': without it Kotlin 2.4.21 crashes on "EUR $amount" (see the lesson)
    override fun toString(): String = BigDecimal.valueOf(cents, 2).toPlainString()

    companion object {
        /** "12.34" -> Money(1234). setScale(2) throws ArithmeticException if rounding would be needed. */
        fun parse(text: String): Money = Money(BigDecimal(text).setScale(2).unscaledValue().longValueExact())
    }
}
