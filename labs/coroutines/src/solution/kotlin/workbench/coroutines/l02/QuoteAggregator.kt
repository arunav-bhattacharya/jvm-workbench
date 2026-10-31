package workbench.coroutines.l02

import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.launch

class QuoteAggregator(private val providers: List<QuoteProvider>) {

    suspend fun allQuotes(pair: String): List<FxQuote> = coroutineScope {
        // 1. start one child per provider; async returns at once with a Deferred
        val pending = providers.map { p -> async { p.quote(pair) } }
        // 2. wait for all of them; the list keeps provider order
        pending.awaitAll()
    }

    suspend fun bestQuote(pair: String): FxQuote =
        allQuotes(pair).maxBy { it.rateMicros }

    suspend fun warmUp() = coroutineScope {
        // launch: we want the side effect, not a value. coroutineScope waits for every child.
        providers.forEach { p -> launch { p.quote("EURUSD") } }
    }

    suspend fun quoteBoard(pairs: List<String>): Map<String, List<FxQuote>> = coroutineScope {
        // each pair runs allQuotes, which starts its own children: a small tree of coroutines
        pairs.map { pair -> async { pair to allQuotes(pair) } }.awaitAll().toMap()
    }
}
