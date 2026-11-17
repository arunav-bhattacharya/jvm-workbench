package workbench.bytecode.l05

/**
 * The theatre's box office: a plain Kotlin class with no interface. The tests wrap it in
 * Byte Buddy subclass proxies.
 *
 * Kotlin classes and their members are final unless you say otherwise, and a subclass can't
 * override what is final. Make this class and the three price methods `open`. Leave [welcome]
 * final on purpose: the tests check what a proxy does with a method it can't override.
 */
class BoxOffice {
    /** Filled in after construction, the way a framework sets up an object it has built. */
    var venue: String = "unset"

    /** The price of [seats] seats in [zone], plus the booking fee. Calls two methods on `this`. */
    fun price(zone: String, seats: Int): Int =
        seats * seatPrice(zone) + bookingFee(seats)

    fun seatPrice(zone: String): Int = when (zone) {
        "stalls" -> 45
        "circle" -> 32
        else -> throw IllegalArgumentException("unknown zone $zone")
    }

    /** One per seat. */
    fun bookingFee(seats: Int): Int = seats

    /** Stays final in the solution too. */
    fun welcome(): String = "welcome to $venue"
}
