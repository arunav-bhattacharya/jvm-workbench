package workbench.flows.l05

// Shared model. This file is the same in src/main and src/solution.

/** A merchant's fee, in basis points of the amount. [source] is "service" or "default". */
data class Fee(val merchant: String, val basisPoints: Int, val source: String = "service")

/** The fee service. One lookup takes tens to hundreds of ms and may throw IOException. */
fun interface FeeService {
    suspend fun lookup(merchant: String): Fee
}

/** A checkout price converted at the latest known USD to EUR rate. */
data class EurPrice(val usdCents: Long, val usdToEur: Double, val eurCents: Long)
