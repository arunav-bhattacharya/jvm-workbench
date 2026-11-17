package workbench.events.l01

import java.math.BigDecimal

/**
 * The tracking number of one parcel, such as `PP-7781`. At run time it is a plain String wherever
 * the compiler can manage it, but a `ParcelId` parameter no longer accepts any other String.
 */
@JvmInline
value class ParcelId(val value: String) {
    init {
        // TODO 1: refuse anything that doesn't match PATTERN, with
        //   IllegalArgumentException("invalid parcel id: '<value>'")  (require does this)
    }

    override fun toString(): String = value

    companion object {
        private val PATTERN = Regex("PP-[0-9]{4,12}")
    }
}

/**
 * A weight in whole grams. A value class can hold exactly one field, so the unit lives in the
 * name of the type: a Weight is never a count of parcels or a number of minutes.
 */
@JvmInline
value class Weight(val grams: Long) {
    init {
        // TODO 2: refuse a negative weight ("weight must not be negative: <grams>")
    }

    /** TODO 2: add exactly. Overflow must throw ArithmeticException (Math.addExact does). */
    operator fun plus(other: Weight): Weight = TODO("add with Math.addExact")

    /** TODO 2: subtract exactly. A result below zero must fail, like any negative Weight. */
    operator fun minus(other: Weight): Weight = TODO("subtract with Math.subtractExact")

    // 2500 grams prints as "2.5 kg"; the explicit ': String' keeps Java's String! out of the signature
    override fun toString(): String = BigDecimal.valueOf(grams, 3).stripTrailingZeros().toPlainString() + " kg"

    companion object {
        val ZERO = Weight(0)
    }
}
