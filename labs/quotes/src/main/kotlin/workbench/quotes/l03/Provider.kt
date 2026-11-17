package workbench.quotes.l03

/** One courier company that quotes parcel prices. [quote] suspends while the courier works out its price, and may throw. */
interface Provider {
    val name: String

    /**
     * True only if asking twice for one request does no harm. Northline and Eastgate only look up
     * a price, so a repeat is harmless. Fjord's prices are bookings: each call holds a place on one
     * of Fjord's vans, so it must never be retried or hedged.
     */
    val idempotent: Boolean
        get() = false

    suspend fun quote(destination: String): Quote
}

/** No provider answered in time and nothing was cached. */
class NoQuoteException(destination: String) : Exception("no quote for $destination")
