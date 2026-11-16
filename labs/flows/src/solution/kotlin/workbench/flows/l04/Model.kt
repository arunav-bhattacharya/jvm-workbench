package workbench.flows.l04

// Shared model. This file is the same in src/main and src/solution.

/** One tick of an FX feed. [tick] counts from 1. */
data class Rate(val pair: String, val tick: Int, val value: Double)

/** A checkout price, repriced at the rate of one tick. */
data class Quote(val tick: Int, val priceCents: Long)

/** One posting read from the acquirer's settlement file, on its way to the ledger. */
data class Posting(val seq: Int, val paymentId: String, val amountCents: Long)
