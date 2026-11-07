package workbench.quotes.l02

/** One FX liquidity provider. [quote] suspends while the provider thinks, and may throw. */
interface Provider {
    val name: String
    suspend fun quote(symbol: String): Quote
}

/** No provider answered in time and nothing was cached. */
class NoQuoteException(symbol: String) : Exception("no quote for $symbol")
