package workbench.events.l03

import java.math.BigDecimal

/**
 * The tracking number of one parcel, such as `PP-7781`. At run time it is a plain String wherever
 * the compiler can manage it, but a `ParcelId` parameter no longer accepts any other String.
 */
@JvmInline
value class ParcelId(val value: String) {
    init {
        // runs in ParcelId.constructor-impl, on every ParcelId(...) call
        require(PATTERN.matches(value)) { "invalid parcel id: '$value'" }
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
        require(grams >= 0) { "weight must not be negative: $grams" }
    }

    // addExact throws ArithmeticException instead of wrapping around to a negative number
    operator fun plus(other: Weight): Weight = Weight(Math.addExact(grams, other.grams))

    // a result below zero fails in the constructor above
    operator fun minus(other: Weight): Weight = Weight(Math.subtractExact(grams, other.grams))

    // 2500 grams prints as "2.5 kg"; the explicit ': String' keeps Java's String! out of the signature
    override fun toString(): String = BigDecimal.valueOf(grams, 3).stripTrailingZeros().toPlainString() + " kg"

    companion object {
        val ZERO = Weight(0)
    }
}
