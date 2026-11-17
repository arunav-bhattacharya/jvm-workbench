package workbench.quotes.l02

/** One courier company that quotes parcel prices. [quote] suspends while the courier works out its price, and may throw. */
interface Provider {
    val name: String
    suspend fun quote(destination: String): Quote
}

/** No provider answered in time and nothing was cached. */
class NoQuoteException(destination: String) : Exception("no quote for $destination")
