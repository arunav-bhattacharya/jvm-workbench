package workbench.coroutines.l02

// Shared model. This file is the same in src/main and src/solution.

/** One grocer's price for an item today, in cents. Lower is better for us. */
data class Price(val grocer: String, val item: String, val cents: Int)

/** A grocer we can ask for prices. Each call is a round trip of 100 to 300 ms, like a text message and its reply. */
interface Grocer {
    val name: String
    suspend fun price(item: String): Price
}
