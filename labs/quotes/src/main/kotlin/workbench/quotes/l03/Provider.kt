package workbench.quotes.l03

/** One FX liquidity provider. [quote] suspends while the provider thinks, and may throw. */
interface Provider {
    val name: String

    /**
     * True only if asking twice for one request does no harm. Northbank and Eastgate stream
     * indicative prices, so a repeat is harmless. Fjord's quotes are firm: each call reserves
     * liquidity on Fjord's side, so it must never be retried or hedged.
     */
    val idempotent: Boolean
        get() = false

    suspend fun quote(symbol: String): Quote
}

/** No provider answered in time and nothing was cached. */
class NoQuoteException(symbol: String) : Exception("no quote for $symbol")
