package workbench.quotes.l02

import java.util.concurrent.CompletableFuture
import kotlin.coroutines.CoroutineContext

/**
 * The coroutine side of the server. Each request becomes one coroutine in a scope this service
 * owns, handed to the Java handler as a `CompletableFuture`. Cancelling that future (the handler
 * does it when the client hangs up) must cancel the coroutine and its three provider calls.
 *
 * 1. Give the class a private scope: `CoroutineScope(context + SupervisorJob())`. Why a supervisor?
 *    A request coroutine that fails must not cancel every other request.
 * 2. `quote` starts `best.quote(symbol)` with `scope.future { }` (from `kotlinx.coroutines.future`)
 *    and returns the future at once. Never `runBlocking` here: the caller is an event loop.
 * 3. `inFlight` counts the children of the scope's job; `close` cancels the scope.
 */
class QuoteService(context: CoroutineContext, private val best: BestQuote) : QuoteSource, AutoCloseable {

    override fun quote(symbol: String): CompletableFuture<Quote> = TODO("scope.future { best.quote(symbol) }")

    /** Requests whose coroutine is still running. */
    val inFlight: Int
        get() = TODO("the number of children of the scope's job")

    override fun close(): Unit = TODO("cancel the scope")
}
