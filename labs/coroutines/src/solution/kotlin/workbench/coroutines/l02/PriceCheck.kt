package workbench.coroutines.l02

import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.launch

class PriceCheck(private val grocers: List<Grocer>) {

    suspend fun allPrices(item: String): List<Price> = coroutineScope {
        // 1. start one child per grocer; async returns at once with a Deferred
        val pending = grocers.map { g -> async { g.price(item) } }
        // 2. wait for all of them; the list keeps the grocers' order
        pending.awaitAll()
    }

    suspend fun cheapest(item: String): Price =
        allPrices(item).minBy { it.cents }

    suspend fun callAhead() = coroutineScope {
        // launch: we want the side effect, not a value. coroutineScope waits for every child.
        grocers.forEach { g -> launch { g.price("bread") } }
    }

    suspend fun priceList(items: List<String>): Map<String, List<Price>> = coroutineScope {
        // each item runs allPrices, which starts its own children: a small tree of coroutines
        items.map { item -> async { item to allPrices(item) } }.awaitAll().toMap()
    }
}
