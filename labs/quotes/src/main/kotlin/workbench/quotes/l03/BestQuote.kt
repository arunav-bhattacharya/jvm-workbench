package workbench.quotes.l03

import kotlinx.coroutines.Deferred
import kotlinx.coroutines.async
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.supervisorScope
import kotlinx.coroutines.withTimeoutOrNull
import kotlin.coroutines.cancellation.CancellationException
import kotlin.time.Duration

/**
 * Asks every provider at once and answers with the lowest price that arrives within [deadline].
 * When none does, it serves the last live quote from [cache], marked stale; with nothing cached
 * it throws [NoQuoteException].
 */
class BestQuote(
    private val providers: List<Provider>,
    private val deadline: Duration,
    private val cache: QuoteCache = QuoteCache(),
) {
    suspend fun quote(symbol: String): Quote {
        val answers = supervisorScope {                                    // 1. a failed call doesn't cancel the others
            providers
                .map { p -> async { withTimeoutOrNull(deadline) { p.quote(symbol) } } }   // 2. late is null, not an exception
                .map { it.awaitOrNull() }                                  // 3. failed is null too
        }.filterNotNull()
        val best = answers.minByOrNull { it.price }
        if (best != null) {
            cache.remember(best)
            return best
        }
        return cache.lastGood(symbol)?.asStale() ?: throw NoQuoteException(symbol)   // 4. stale beats nothing
    }

    private suspend fun Deferred<Quote?>.awaitOrNull(): Quote? =
        try {
            await()
        } catch (e: CancellationException) {
            currentCoroutineContext().ensureActive()   // we were cancelled ourselves: this rethrows
            null                                        // only the provider's call ended that way: no answer
        } catch (e: Exception) {
            null                                        // the provider failed: no answer from it
        }
}
