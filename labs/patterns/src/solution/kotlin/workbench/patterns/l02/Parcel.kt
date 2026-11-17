package workbench.patterns.l02

import kotlin.math.roundToInt

enum class Courier { BIKE, VAN }

class Parcel private constructor(val courier: Courier, val grams: Int) {
    override fun toString() = "$courier parcel, $grams g"

    companion object {
        // the only way to make a Parcel: every Parcel that exists passed these checks
        fun parse(raw: String): ParcelResult {
            val parts = raw.trim().split(" ")
            if (parts.size != 2) return ParcelResult.Invalid("format")                      // 1. shape
            val number = parts[0].toDoubleOrNull() ?: return ParcelResult.Invalid("format")
            val grams = when (parts[1]) {
                "g" -> number
                "kg" -> number * 1_000
                else -> return ParcelResult.Invalid("format")
            }.roundToInt()
            if (grams <= 0) return ParcelResult.Invalid("weight")                           // 2. a real weight
            val courier = courierFor(grams)                                                 // 3. pick the product
                ?: return ParcelResult.Invalid("too heavy")
            // inside the class the private constructor is visible; outside, nobody can call it
            return ParcelResult.Valid(Parcel(courier, grams))
        }

        private fun courierFor(grams: Int): Courier? = when {
            grams <= 5_000 -> Courier.BIKE
            grams <= 30_000 -> Courier.VAN
            else -> null
        }
    }
}

sealed interface ParcelResult {
    data class Valid(val parcel: Parcel) : ParcelResult
    data class Invalid(val reason: String) : ParcelResult
}
