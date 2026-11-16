package workbench.flows.l07

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn

/**
 * The FX cache that payment request handlers read. Handlers only ever call `.value`; they
 * never collect.
 *
 * - Collect [feed] once for the whole service, in [scope], from the moment the cache is built.
 * - `.value` is `null` until the first rate arrives, then always the latest rate.
 * - The feed sometimes fails with an `IOException` (the provider resets the connection).
 *   Keep serving the last rate, wait 1,000 ms, and collect the feed again.
 *
 * Bug: a teammate copied this from the dashboard code. Handlers see `null` for ever.
 */
fun requestCache(feed: Flow<Rate>, scope: CoroutineScope): StateFlow<Rate?> =
    feed.stateIn(scope, SharingStarted.WhileSubscribed(5_000), null)

/**
 * The live rate pushed to ops dashboards over server-sent events. Each open dashboard
 * collects the returned flow.
 *
 * - Don't collect [feed] while no dashboard is open.
 * - All dashboards share one collection of [feed].
 * - A dashboard that reconnects within 5,000 ms of the last one leaving must not restart the
 *   feed (a page reload is not a reason to reconnect to the provider).
 * - Stop collecting 5,000 ms after the last dashboard leaves.
 * - Once the feed has stopped, a dashboard that opens later must not be shown the old rate:
 *   it gets `null` until the fresh feed delivers its first rate.
 *
 * Bug: the defaults restart the provider connection on every page reload.
 */
fun dashboardFeed(feed: Flow<Rate>, scope: CoroutineScope): StateFlow<Rate?> =
    feed.stateIn(scope, SharingStarted.WhileSubscribed(), null)
