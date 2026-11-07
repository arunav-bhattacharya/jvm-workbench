package workbench.vthreads.l06

import java.math.BigDecimal

/** One quote request, as it arrives at the HTTP endpoint. */
data class QuoteRequest(val customerId: String, val pair: String, val amount: BigDecimal)

/** The answer: the rate to use and the fee for this customer's tier. */
data class Quote(val customerId: String, val pair: String, val rate: BigDecimal, val fee: BigDecimal)

/**
 * The customer database, reached through a connection pool with [poolSize] connections.
 * Each [tier] call borrows one connection for as long as the query runs.
 */
interface CustomerDb {
    val poolSize: Int
    fun tier(customerId: String): String
}

/** The FX provider's HTTP API. It takes about 100 ms and allows far more calls in flight than you'll send. */
fun interface FxApi {
    fun rate(pair: String): BigDecimal
}
