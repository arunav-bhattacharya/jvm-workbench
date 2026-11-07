package workbench.quotes.l02

import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.withTimeout
import kotlin.time.Duration

/**
 * Asks every provider at once and answers with the lowest price that arrives within [deadline].
 * When none does, it serves the last live quote from [cache], marked stale; with nothing cached
 * it throws [NoQuoteException].
 *
 * This first draft is fast on a good day. Fix what happens on a bad one:
 * 1. One provider that throws cancels the other two (that is what `coroutineScope` does). Use
 *    `supervisorScope`, so each call fails alone.
 * 2. `withTimeout` ends a late call with `TimeoutCancellationException`, a `CancellationException`.
 *    Use `withTimeoutOrNull`, so a late provider is just `null`.
 * 3. A provider that fails, or whose own client timed out, counts as no answer. Await each call
 *    in a try: catch `Exception` as `null`. For `CancellationException`, first call
 *    `currentCoroutineContext().ensureActive()`: it rethrows only if *this* coroutine was cancelled.
 * 4. Keep the lowest price and `cache.remember` it. With no answer, serve `cache.lastGood(symbol)`
 *    marked `asStale()`, or throw `NoQuoteException(symbol)`.
 */
class BestQuote(
    private val providers: List<Provider>,
    private val deadline: Duration,
    private val cache: QuoteCache = QuoteCache(),
) {
    suspend fun quote(symbol: String): Quote = coroutineScope {
        providers
            .map { p -> async { withTimeout(deadline) { p.quote(symbol) } } }
            .awaitAll()
            .minBy { it.price }
    }
}
