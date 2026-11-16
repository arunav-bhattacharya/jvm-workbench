package workbench.coroutines.l02

/**
 * Asks several grocers for today's prices.
 *
 * Every function here must ask the grocers at the same time, so it takes as long as the
 * slowest grocer, not the sum of all of them. Every function must also return only after
 * the work it started is finished.
 */
class PriceCheck(private val grocers: List<Grocer>) {

    /**
     * One price from every grocer, in the same order as [grocers].
     * This version works but asks them one after another. Make it concurrent.
     */
    suspend fun allPrices(item: String): List<Price> =
        grocers.map { it.price(item) }

    /** The price with the fewest [Price.cents]. Ask all grocers at once. */
    suspend fun cheapest(item: String): Price {
        TODO("reuse allPrices")
    }

    /**
     * Asks every grocer for the price of "bread", so each shop knows we'll be ordering today,
     * and ignores the answers. Returns only after every grocer has answered.
     * Use launch: you need no result.
     */
    suspend fun callAhead() {
        TODO("one launch per grocer inside coroutineScope")
    }

    /** All prices for every item, with every item and every grocer asked at the same time. */
    suspend fun priceList(items: List<String>): Map<String, List<Price>> {
        TODO("one async per item, each calling allPrices")
    }
}
