package workbench.patterns.l02

sealed interface ShipResult {
    data class Booked(val bookingRef: String) : ShipResult
    data class Rejected(val reason: String) : ShipResult
}

class Shipping(private val servicesFor: (Courier) -> CourierServices) {

    fun ship(orderId: String, weight: String): ShipResult =
        when (val parsed = Parcel.parse(weight)) {                // exhaustive: Valid or Invalid, no else
            is ParcelResult.Invalid -> ShipResult.Rejected(parsed.reason)
            is ParcelResult.Valid -> {
                val parcel = parsed.parcel
                // the factory picks the family; Shipping only knows the Booker interface
                ShipResult.Booked(servicesFor(parcel.courier).booker().book(parcel, orderId))
            }
        }
}
