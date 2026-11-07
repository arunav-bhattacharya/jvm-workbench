package workbench.vthreads.l06

import java.math.BigDecimal
import java.util.concurrent.Callable
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

/**
 * Quotes FX conversions. Each request looks up the customer's tier in the database, then asks
 * the FX provider for a rate.
 *
 * This is the version running in production today. Request handling runs on a fixed pool of
 * 10 platform threads, sized to match the 10-connection database pool. Migrate it:
 *
 * 1. Run each request on its own new virtual thread.
 * 2. Keep the database safe. Hold a permit from a [java.util.concurrent.Semaphore] around the
 *    database call, and only that call, with one permit per pooled connection ([CustomerDb.poolSize]).
 * 3. Report how many requests are waiting for a database permit ([dbWaiting]).
 * 4. Close the new executor in [close].
 */
class QuoteService(private val db: CustomerDb, private val fx: FxApi) : AutoCloseable {

    // TODO 1: one new virtual thread per request instead of this pool
    // 10 platform threads, because the database pool has 10 connections
    private val workers: ExecutorService = Executors.newFixedThreadPool(10)

    // TODO 2: a Semaphore with db.poolSize permits

    /** Handles a burst of requests the way the HTTP layer would: one task per request. Results come back in input order. */
    fun quoteAll(requests: List<QuoteRequest>): List<Quote> {
        val futures = requests.map { r -> workers.submit(Callable { quote(r) }) }
        return futures.map { it.get() }
    }

    /** One request: the database call, then the FX call. */
    fun quote(request: QuoteRequest): Quote {
        val tier = db.tier(request.customerId)          // TODO 2: hold a database permit around this call only
        val rate = fx.rate(request.pair)
        return Quote(request.customerId, request.pair, rate, fee(tier, request.amount))
    }

    /** How many requests are waiting for a database permit right now. Export it as a gauge. */
    fun dbWaiting(): Int = TODO("TODO 3: ask the semaphore how many threads are queued on it")

    override fun close() {
        // TODO 4: close the new executor (close() waits for requests in flight)
        workers.shutdown()
        workers.awaitTermination(30, TimeUnit.SECONDS)
    }

    private fun fee(tier: String, amount: BigDecimal): BigDecimal =
        amount.multiply(if (tier == "gold") BigDecimal("0.0010") else BigDecimal("0.0025"))
}
