package workbench.events.l03

import java.math.BigDecimal

/**
 * The id of one payment, such as `pay_7781`. At run time it is a plain String wherever the
 * compiler can manage it, but a `PaymentId` parameter no longer accepts any other String.
 */
@JvmInline
value class PaymentId(val value: String) {
    init {
        // runs in PaymentId.constructor-impl, on every PaymentId(...) call
        require(PATTERN.matches(value)) { "invalid payment id: '$value'" }
    }

    override fun toString(): String = value

    companion object {
        private val PATTERN = Regex("pay_[A-Za-z0-9]{4,24}")
    }
}

/**
 * An amount in euro cents. This service settles in euros only, so the currency is not stored:
 * a value class can hold exactly one field.
 */
@JvmInline
value class Money(val minor: Long) {
    init {
        require(minor >= 0) { "amount must not be negative: $minor" }
    }

    // addExact throws ArithmeticException instead of wrapping around to a negative number
    operator fun plus(other: Money): Money = Money(Math.addExact(minor, other.minor))

    // a result below zero fails in the constructor above
    operator fun minus(other: Money): Money = Money(Math.subtractExact(minor, other.minor))

    // keep the explicit ': String': without it, this Java call's platform type crashes kotlinc 2.4.21 on "$money"
    override fun toString(): String = BigDecimal.valueOf(minor, 2).toPlainString()

    companion object {
        val ZERO = Money(0)
    }
}
