package workbench.events.l01

import java.math.BigDecimal

/**
 * The id of one payment, such as `pay_7781`. At run time it is a plain String wherever the
 * compiler can manage it, but a `PaymentId` parameter no longer accepts any other String.
 */
@JvmInline
value class PaymentId(val value: String) {
    init {
        // TODO 1: refuse anything that doesn't match PATTERN, with
        //   IllegalArgumentException("invalid payment id: '<value>'")  (require does this)
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
        // TODO 2: refuse a negative amount ("amount must not be negative: <minor>")
    }

    /** TODO 2: add exactly. Overflow must throw ArithmeticException (Math.addExact does). */
    operator fun plus(other: Money): Money = TODO("add with Math.addExact")

    /** TODO 2: subtract exactly. A result below zero must fail, like any negative Money. */
    operator fun minus(other: Money): Money = TODO("subtract with Math.subtractExact")

    // keep the explicit ': String': without it, this Java call's platform type crashes kotlinc 2.4.21 on "$money"
    override fun toString(): String = BigDecimal.valueOf(minor, 2).toPlainString()

    companion object {
        val ZERO = Money(0)
    }
}
