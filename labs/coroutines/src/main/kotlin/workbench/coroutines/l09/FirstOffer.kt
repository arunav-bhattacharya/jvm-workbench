package workbench.coroutines.l09

import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope

/**
 * Phones every shop at the same time and returns the FIRST offer to arrive. The other calls
 * are cancelled as soon as the first one answers. If the first to answer fails, firstOffer
 * fails with that exception.
 *
 * Bug: waits for every shop, then returns the first one in the list.
 */
suspend fun firstOffer(shops: List<suspend () -> Offer>): Offer = coroutineScope {
    shops.map { call -> async { call() } }.awaitAll().first()
}
