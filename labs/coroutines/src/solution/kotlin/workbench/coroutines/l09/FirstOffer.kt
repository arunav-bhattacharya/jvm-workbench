package workbench.coroutines.l09

import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.selects.select

suspend fun firstOffer(shops: List<suspend () -> Offer>): Offer = coroutineScope {
    val calls = shops.map { call -> async { call() } }
    // select suspends until the first clause can complete; onAwait completes when that call does
    val first = select { calls.forEach { c -> c.onAwait { it } } }
    calls.forEach { it.cancel() } // the other shops: hang up, we no longer need them
    first
}
