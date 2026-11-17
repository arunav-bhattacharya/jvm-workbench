package workbench.patterns.l02

/** Who carries a parcel across town: a bike courier for light parcels, a van for heavy ones. */
enum class Courier { BIKE, VAN }

/**
 * A parcel whose weight passed the checks. The constructor is private: the only way to get a
 * [Parcel] is the factory [Parcel.parse], so every [Parcel] in the program has a sensible weight
 * and a courier who can carry it.
 */
class Parcel private constructor(val courier: Courier, val grams: Int) {
    override fun toString() = "$courier parcel, $grams g"

    companion object {
        /**
         * Parses a weight such as "2.5 kg" or "800 g". Never throws: bad input comes back as
         * [ParcelResult.Invalid] with one of these reasons, checked in this order:
         *
         * 1. after trimming, the text is not a number, one space and a unit ("g" or "kg"): "format"
         * 2. the weight, rounded to whole grams, is zero or less: "weight"
         * 3. the courier comes from the weight: up to 5,000 g is BIKE, up to 30,000 g is VAN, and
         *    anything heavier: "too heavy"
         *
         * A good weight comes back as [ParcelResult.Valid] holding the parcel, its courier and its grams.
         */
        fun parse(raw: String): ParcelResult = TODO("check in the order above, then pick the courier from the weight")
    }
}

/** What [Parcel.parse] returns. The caller's `when` must handle both cases, and the compiler checks it. */
sealed interface ParcelResult {
    data class Valid(val parcel: Parcel) : ParcelResult
    data class Invalid(val reason: String) : ParcelResult
}
