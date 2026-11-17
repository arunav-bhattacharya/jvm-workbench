package workbench.events.l03

/**
 * Everything that can happen to a parcel at Pedal Post. The list is closed: every direct subtype
 * is declared in this package and module, so a `when` over a ParcelEvent can be checked for
 * exhaustiveness.
 */
sealed interface ParcelEvent {
    val parcelId: ParcelId
}

/** A sender booked a pickup for a parcel of [weight]. Nothing has moved yet. */
data class ParcelBooked(override val parcelId: ParcelId, val weight: Weight) : ParcelEvent {
    init {
        require(weight.grams > 0) { "booked weight must be positive: $weight" }
    }
}

/** A rider tried to deliver the parcel and couldn't. */
data class DeliveryFailed(override val parcelId: ParcelId, val reason: FailReason) : ParcelEvent

/**
 * The moments a parcel changes hands. Sealed again, one level down: a handler or a `when` branch
 * for Handover covers collections and deliveries, and the compiler still knows there are only two.
 */
sealed interface Handover : ParcelEvent {
    val weight: Weight
}

/** A rider collected the parcel from the sender. */
data class ParcelCollected(override val parcelId: ParcelId, override val weight: Weight) : Handover {
    init {
        require(weight.grams > 0) { "collected weight must be positive: $weight" }
    }
}

/** A rider handed the parcel over at the door. */
data class ParcelDelivered(override val parcelId: ParcelId, override val weight: Weight) : Handover {
    init {
        require(weight.grams > 0) { "delivered weight must be positive: $weight" }
    }
}

enum class FailReason { NOBODY_HOME, ADDRESS_NOT_FOUND, PARCEL_DAMAGED }
