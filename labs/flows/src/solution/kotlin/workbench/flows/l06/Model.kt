package workbench.flows.l06

import kotlinx.coroutines.flow.Flow

// Shared model. This file is the same in src/main and src/solution.

/** An FX rate for a currency pair, and which provider gave it. */
data class Rate(val pair: String, val value: Double, val source: String)

/** An FX provider. Every collection of [rate] is one call to the provider. */
fun interface RateProvider {
    fun rate(pair: String): Flow<Rate>
}

/** A payment from the acquirer's settlement feed. [id] is unique per payment. */
data class Payment(val id: String, val amountCents: Long)
