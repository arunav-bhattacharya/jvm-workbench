package workbench.coroutines.l09

import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.selects.select

suspend fun fastestQuote(acquirers: List<suspend () -> Quote>): Quote = coroutineScope {
    val calls = acquirers.map { call -> async { call() } }
    // select suspends until the first clause can complete; onAwait completes when that call does
    val first = select { calls.forEach { c -> c.onAwait { it } } }
    calls.forEach { it.cancel() } // the losers: we no longer need them
    first
}
