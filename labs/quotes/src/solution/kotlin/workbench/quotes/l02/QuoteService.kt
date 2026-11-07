package workbench.quotes.l02

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.future.future
import kotlinx.coroutines.job
import java.util.concurrent.CompletableFuture
import kotlin.coroutines.CoroutineContext

/**
 * The coroutine side of the server. Each request becomes one coroutine in a scope this service
 * owns, handed to the Java handler as a `CompletableFuture`. Cancelling that future (the handler
 * does it when the client hangs up) cancels the coroutine and its three provider calls.
 */
class QuoteService(context: CoroutineContext, private val best: BestQuote) : QuoteSource, AutoCloseable {
    private val scope = CoroutineScope(context + SupervisorJob())   // one failed request can't cancel the rest

    override fun quote(symbol: String): CompletableFuture<Quote> =
        scope.future { best.quote(symbol) }                          // returns at once; the coroutine runs on context

    /** Requests whose coroutine is still running. */
    val inFlight: Int
        get() = scope.coroutineContext.job.children.count()

    override fun close() = scope.cancel()
}
