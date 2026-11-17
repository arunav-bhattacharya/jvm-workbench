package workbench.bytecode.l05

// open: Byte Buddy (like CGLIB, ArC and Hibernate) can only subclass a non-final class
open class BoxOffice {
    var venue: String = "unset"

    // open members: a subclass can only intercept what it can override
    open fun price(zone: String, seats: Int): Int =
        seats * seatPrice(zone) + bookingFee(seats)

    open fun seatPrice(zone: String): Int = when (zone) {
        "stalls" -> 45
        "circle" -> 32
        else -> throw IllegalArgumentException("unknown zone $zone")
    }

    open fun bookingFee(seats: Int): Int = seats

    // still final: a proxy runs it on ITSELF, never intercepted and never forwarded
    fun welcome(): String = "welcome to $venue"
}
