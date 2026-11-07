package workbench.coroutines.l09

import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope

/**
 * Asks every acquirer for a quote at the same time and returns the FIRST quote to arrive.
 * The other calls are cancelled as soon as the first one answers. If the first to answer
 * fails, fastestQuote fails with that exception.
 *
 * Bug: waits for every acquirer, then returns the first in the list.
 */
suspend fun fastestQuote(acquirers: List<suspend () -> Quote>): Quote = coroutineScope {
    acquirers.map { call -> async { call() } }.awaitAll().first()
}
