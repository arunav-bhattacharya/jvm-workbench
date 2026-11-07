package workbench.vthreads.l06

import java.math.BigDecimal
import java.util.concurrent.Callable
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import java.util.concurrent.Semaphore

class QuoteService(private val db: CustomerDb, private val fx: FxApi) : AutoCloseable {

    // 1. one new virtual thread per request: no size to pick, nothing to pool
    private val requests: ExecutorService = Executors.newVirtualThreadPerTaskExecutor()

    // 2. the limit the old pool gave you by accident, now explicit and tied to the real resource.
    //    Fair, so a burst is served in arrival order and no request waits far longer than the rest.
    private val dbPermits = Semaphore(db.poolSize, true)

    fun quoteAll(requests: List<QuoteRequest>): List<Quote> {
        val futures = requests.map { r -> this.requests.submit(Callable { quote(r) }) }
        return futures.map { it.get() }
    }

    fun quote(request: QuoteRequest): Quote {
        val tier = withDbPermit { db.tier(request.customerId) }   // only the database call holds a permit
        val rate = fx.rate(request.pair)                          // FX calls are no longer capped at 10
        return Quote(request.customerId, request.pair, rate, fee(tier, request.amount))
    }

    // 3. a gauge for the dashboard: requests queued for the database right now
    fun dbWaiting(): Int = dbPermits.queueLength

    // 4. close() on the executor waits for every request still in flight
    override fun close() = requests.close()

    private inline fun <T> withDbPermit(block: () -> T): T {
        dbPermits.acquire()              // outside the try: an interrupted wait must not release
        try {
            return block()
        } finally {
            dbPermits.release()          // always give it back
        }
    }

    private fun fee(tier: String, amount: BigDecimal): BigDecimal =
        amount.multiply(if (tier == "gold") BigDecimal("0.0010") else BigDecimal("0.0025"))
}
