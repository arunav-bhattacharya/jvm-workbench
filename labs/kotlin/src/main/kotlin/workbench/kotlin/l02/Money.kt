package workbench.kotlin.l02

import java.math.BigDecimal

/**
 * An amount in euro cents. At run time it is a plain `long` wherever the compiler can manage it.
 *
 * TODO 1: add an init block that rejects a negative amount with
 * IllegalArgumentException("amount must be non-negative, was <cents>"). Use require.
 */
@JvmInline
value class Money(val cents: Long) : Comparable<Money> {

    /** TODO 2: Math.addExact, so an overflow throws ArithmeticException instead of going negative. */
    operator fun plus(other: Money): Money = TODO("Money(Math.addExact(...))")

    /** TODO 3: Math.multiplyExact (convert quantity with toLong()). */
    operator fun times(quantity: Int): Money = TODO("Money(Math.multiplyExact(...))")

    override fun compareTo(other: Money): Int = TODO("compare the cents")

    /** TODO 4: "12.34" for Money(1234). BigDecimal.valueOf(cents, 2).toPlainString(). Keep the ': String'. */
    override fun toString(): String = TODO("BigDecimal.valueOf(cents, 2).toPlainString()")

    companion object {
        /**
         * TODO 5: "12.34" -> Money(1234), "10" -> Money(1000). More than two decimals is an error:
         * BigDecimal(text).setScale(2) throws ArithmeticException when it would have to round.
         * Then .unscaledValue().longValueExact() gives the cents.
         */
        fun parse(text: String): Money = TODO("BigDecimal(text).setScale(2)...")
    }
}
