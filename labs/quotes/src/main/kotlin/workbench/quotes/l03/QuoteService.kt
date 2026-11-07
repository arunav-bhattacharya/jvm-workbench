package workbench.quotes.l03

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.future.future
import kotlinx.coroutines.job
import java.util.concurrent.CompletableFuture
import kotlin.coroutines.CoroutineContext
import kotlin.time.Duration

/** The service is full: the request was refused at once, before any provider was asked. */
class BusyException : Exception("busy")

/** The service is stopping and takes no new requests. */
class ShuttingDownException : Exception("shutting down")

/**
 * The coroutine side of the server, as lesson 2 left it. Add the two load rules:
 *
 * 1. Admission. At most [maxInFlight] requests may run at once. Keep a `Semaphore(maxInFlight)`;
 *    in `quote`, `tryAcquire()` a permit, and if there is none return
 *    `CompletableFuture.failedFuture(BusyException())` at once. Release the permit when the reply
 *    future completes, however it completes (`whenComplete`).
 * 2. Shutdown. After [shutdown] starts, `quote` returns a future failed with
 *    [ShuttingDownException]. [shutdown] waits up to `grace` for the requests in flight (join the
 *    scope job's children inside `withTimeoutOrNull`), then cancels what is left with
 *    `cancelAndJoin()` and returns how many that was.
 */
class QuoteService(
    context: CoroutineContext,
    private val best: BestQuote,
    private val maxInFlight: Int = 256,
) : QuoteSource, AutoCloseable {
    private val scope = CoroutineScope(context + SupervisorJob())   // one failed request can't cancel the rest

    override fun quote(symbol: String): CompletableFuture<Quote> =
        scope.future { best.quote(symbol) }                          // TODO: admission and shutdown

    /** Requests whose coroutine is still running. */
    val inFlight: Int
        get() = scope.coroutineContext.job.children.count()

    /**
     * Refuse new requests, give the ones in flight [grace] to finish, then cancel the rest and wait
     * until they have stopped. Returns how many had to be cancelled.
     */
    suspend fun shutdown(grace: Duration): Int = TODO("stop intake, wait up to grace, cancel and join the rest")

    override fun close() = scope.cancel()
}
