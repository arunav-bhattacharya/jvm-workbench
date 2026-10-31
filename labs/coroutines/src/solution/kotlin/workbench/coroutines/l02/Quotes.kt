package workbench.coroutines.l02

// Shared model. This file is the same in src/main and src/solution.

/** One FX quote. [rateMicros] is the rate in millionths: 1.084512 is 1_084_512. Higher is better for us. */
data class FxQuote(val provider: String, val pair: String, val rateMicros: Long)

/** A liquidity provider. Each call is a network round trip of 100 to 300 ms. */
interface QuoteProvider {
    val name: String
    suspend fun quote(pair: String): FxQuote
}
