package workbench.coroutines.l02

/**
 * Asks several liquidity providers for FX quotes.
 *
 * Every function here must ask the providers at the same time, so it takes as long as the
 * slowest provider, not the sum of all of them. Every function must also return only after
 * the work it started is finished.
 */
class QuoteAggregator(private val providers: List<QuoteProvider>) {

    /**
     * One quote from every provider, in the same order as [providers].
     * This version works but asks them one after another. Make it concurrent.
     */
    suspend fun allQuotes(pair: String): List<FxQuote> =
        providers.map { it.quote(pair) }

    /** The quote with the highest [FxQuote.rateMicros]. Ask all providers at once. */
    suspend fun bestQuote(pair: String): FxQuote {
        TODO("reuse allQuotes")
    }

    /**
     * Asks every provider for a "EURUSD" quote to open its connection, and ignores the answers.
     * Returns only after every provider has answered. Use launch: you need no result.
     */
    suspend fun warmUp() {
        TODO("one launch per provider inside coroutineScope")
    }

    /** All quotes for every pair, with every pair and every provider asked at the same time. */
    suspend fun quoteBoard(pairs: List<String>): Map<String, List<FxQuote>> {
        TODO("one async per pair, each calling allQuotes")
    }
}
