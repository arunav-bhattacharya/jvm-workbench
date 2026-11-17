package workbench.patterns.l02

fun interface Booker {
    fun book(parcel: Parcel, orderId: String): String
}

fun interface Tracker {
    fun track(bookingRef: String): String
}

interface CourierServices {
    val courier: Courier
    val company: String
    fun booker(): Booker
    fun tracker(): Tracker

    companion object {
        // the one switch that knows which family belongs to which courier; no else, so a new
        // Courier constant is a compile error here and nowhere else
        fun forCourier(courier: Courier): CourierServices = when (courier) {
            Courier.BIKE -> PretendServices(Courier.BIKE, "Pedal Post", "PP")
            Courier.VAN -> PretendServices(Courier.VAN, "Big Blue Vans", "BB")
        }
    }
}

// one family = one company's settings; both products are built from the same settings, so they can't mismatch
private class PretendServices(
    override val courier: Courier,
    override val company: String,
    private val prefix: String,
) : CourierServices {

    override fun booker() = Booker { parcel, orderId ->
        require(parcel.courier == courier) { "a $courier booker cannot book a ${parcel.courier} parcel" }
        "$prefix-$orderId-${parcel.grams}"
    }

    override fun tracker() = Tracker { bookingRef ->
        require(bookingRef.startsWith("$prefix-")) { "booking $bookingRef is not from $company" }
        "$company: $bookingRef is on its way"
    }
}
