package workbench.quotes.l03

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.future.future
import kotlinx.coroutines.job
import kotlinx.coroutines.joinAll
import kotlinx.coroutines.sync.Semaphore
import kotlinx.coroutines.withTimeoutOrNull
import java.util.concurrent.CompletableFuture
import kotlin.coroutines.CoroutineContext
import kotlin.time.Duration

/** The service is full: the request was refused at once, before any provider was asked. */
class BusyException : Exception("busy")

/** The service is stopping and takes no new requests. */
class ShuttingDownException : Exception("shutting down")

/**
 * The coroutine side of the server. Each request becomes one coroutine in a scope this service
 * owns, handed to the Java handler as a `CompletableFuture`. At most [maxInFlight] requests run at
 * once; the next one is shed with [BusyException].
 */
class QuoteService(
    context: CoroutineContext,
    private val best: BestQuote,
    private val maxInFlight: Int = 256,
) : QuoteSource, AutoCloseable {
    private val scope = CoroutineScope(context + SupervisorJob())   // one failed request can't cancel the rest
    private val admission = Semaphore(maxInFlight)
    @Volatile private var accepting = true

    override fun quote(symbol: String): CompletableFuture<Quote> {
        if (!accepting) return CompletableFuture.failedFuture(ShuttingDownException())
        if (!admission.tryAcquire()) return CompletableFuture.failedFuture(BusyException())   // 1. shed at once
        val reply = scope.future { best.quote(symbol) }
        reply.whenComplete { _, _ -> admission.release() }         // 2. however the request ends
        return reply
    }

    /** Requests whose coroutine is still running. */
    val inFlight: Int
        get() = scope.coroutineContext.job.children.count()

    /**
     * Refuse new requests, give the ones in flight [grace] to finish, then cancel the rest and wait
     * until they have stopped. Returns how many had to be cancelled.
     */
    suspend fun shutdown(grace: Duration): Int {
        accepting = false                                           // 1. stop intake
        val job = scope.coroutineContext.job
        withTimeoutOrNull(grace) { job.children.toList().joinAll() }   // 2. let them finish, up to grace
        val left = job.children.count()
        job.cancelAndJoin()                                         // 3. cancel the rest, wait for them to stop
        return left
    }

    override fun close() = scope.cancel()
}
