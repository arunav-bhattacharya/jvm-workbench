package workbench.patterns.l02

/** What [Shipping.ship] returns. */
sealed interface ShipResult {
    data class Booked(val bookingRef: String) : ShipResult
    data class Rejected(val reason: String) : ShipResult
}

/**
 * Takes an order id and a raw weight, and books the parcel with the right courier.
 *
 * The factory comes in as a function, so a test can pass a fake one (or `CourierServices::forCourier`).
 * Shipping must not build services itself and must not know the family classes.
 */
class Shipping(private val servicesFor: (Courier) -> CourierServices) {

    /**
     * Parses [weight] with [Parcel.parse]. A bad weight is [ShipResult.Rejected] with the parse
     * reason, and the factory is never called. A good parcel is booked by the booker of the family
     * for its courier, and the result is [ShipResult.Booked] with the booking reference.
     */
    fun ship(orderId: String, weight: String): ShipResult = TODO("parse, then ask the factory for the parcel's family")
}
