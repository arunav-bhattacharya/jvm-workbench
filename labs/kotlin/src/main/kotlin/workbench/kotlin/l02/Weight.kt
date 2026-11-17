package workbench.kotlin.l02

import java.math.BigDecimal

/**
 * The weight of a parcel of printed work, in grams. At run time it is a plain `long` wherever the
 * compiler can manage it.
 *
 * TODO 1: add an init block that rejects a negative weight with
 * IllegalArgumentException("weight must be non-negative, was <grams>"). Use require.
 */
@JvmInline
value class Weight(val grams: Long) : Comparable<Weight> {

    /** TODO 2: Math.addExact, so an overflow throws ArithmeticException instead of going negative. */
    operator fun plus(other: Weight): Weight = TODO("Weight(Math.addExact(...))")

    /** TODO 3: Math.multiplyExact (convert count with toLong()). */
    operator fun times(count: Int): Weight = TODO("Weight(Math.multiplyExact(...))")

    override fun compareTo(other: Weight): Int = TODO("compare the grams")

    /** TODO 4: "1.250" (kilograms) for Weight(1250). BigDecimal.valueOf(grams, 3).toPlainString(). Keep the ': String'. */
    override fun toString(): String = TODO("BigDecimal.valueOf(grams, 3).toPlainString()")

    companion object {
        /**
         * TODO 5: kilograms in, grams out. "1.25" -> Weight(1250), "10" -> Weight(10000). More than
         * three decimals is an error: BigDecimal(text).setScale(3) throws ArithmeticException when
         * it would have to round. Then .unscaledValue().longValueExact() gives the grams.
         */
        fun parse(kilograms: String): Weight = TODO("BigDecimal(kilograms).setScale(3)...")
    }
}
