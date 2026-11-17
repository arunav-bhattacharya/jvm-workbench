package workbench.kotlin.l02

import java.math.BigDecimal

/**
 * The weight of a parcel of printed work, in grams. At run time it is a plain `long` wherever the
 * compiler can manage it.
 */
@JvmInline
value class Weight(val grams: Long) : Comparable<Weight> {
    init {
        // runs in Weight.constructor-impl(long), on every Weight(...) call
        require(grams >= 0) { "weight must be non-negative, was $grams" }
    }

    // addExact and multiplyExact throw ArithmeticException instead of wrapping around
    operator fun plus(other: Weight): Weight = Weight(Math.addExact(grams, other.grams))

    operator fun times(count: Int): Weight = Weight(Math.multiplyExact(grams, count.toLong()))

    override fun compareTo(other: Weight): Int = grams.compareTo(other.grams)

    // keep the explicit ': String': without it Kotlin 2.4.21 crashes on "Parcel $weight kg" (see the lesson)
    override fun toString(): String = BigDecimal.valueOf(grams, 3).toPlainString()

    companion object {
        /** "1.25" kilograms -> Weight(1250). setScale(3) throws ArithmeticException if rounding would be needed. */
        fun parse(kilograms: String): Weight = Weight(BigDecimal(kilograms).setScale(3).unscaledValue().longValueExact())
    }
}
