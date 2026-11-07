package workbench.quotes.l02

import java.util.concurrent.ConcurrentHashMap

/** The last live quote per symbol, served (marked stale) when no provider answers in time. */
class QuoteCache {
    private val last = ConcurrentHashMap<String, Quote>()

    fun remember(quote: Quote) {
        last[quote.symbol] = quote
    }

    fun lastGood(symbol: String): Quote? = last[symbol]
}
