package workbench.patterns.l02

/** Books a pickup for a parcel. Returns a booking reference. */
fun interface Booker {
    fun book(parcel: Parcel, orderId: String): String
}

/** Tells you where a booked parcel is. Takes a booking reference from the same courier company. */
fun interface Tracker {
    fun track(bookingRef: String): String
}

/**
 * Abstract factory: one family of services for one courier company. Everything a family creates
 * talks to the same company, so you can never book with the bike courier and then ask the van
 * company where the parcel is.
 *
 * The families behave like this (they are pretend services: no real calls):
 *
 * | courier | company       | booking reference          | tracking answer                    |
 * |---------|---------------|----------------------------|------------------------------------|
 * | BIKE    | Pedal Post    | "PP-<orderId>-<grams>"     | "Pedal Post: <reference> is on its way"    |
 * | VAN     | Big Blue Vans | "BB-<orderId>-<grams>"     | "Big Blue Vans: <reference> is on its way" |
 *
 * A family's booker throws IllegalArgumentException for a parcel meant for the other courier, and
 * its tracker throws IllegalArgumentException for a reference that does not start with its own
 * prefix ("PP-" or "BB-").
 */
interface CourierServices {
    val courier: Courier
    val company: String
    fun booker(): Booker
    fun tracker(): Tracker

    companion object {
        /** The family for [courier]. Use an exhaustive `when`, with no `else`. */
        fun forCourier(courier: Courier): CourierServices = TODO("return the right family for each courier")
    }
}
