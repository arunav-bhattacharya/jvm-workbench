package workbench.coroutines.l08

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.runningFold
import kotlinx.coroutines.flow.stateIn

/**
 * The running total of captured amounts (in cents), shown live on ops dashboards.
 *
 * - Start collecting [captures] only when the first dashboard subscribes.
 * - Every dashboard shares ONE collection of [captures].
 * - Keep collecting for 5 seconds after the last dashboard leaves, so a page reload
 *   doesn't restart the upstream; then stop.
 * - The value is 0 before anything has been captured.
 *
 * Bug: Eagerly starts collecting at once, with nobody watching, and never stops.
 */
fun liveCapturedTotal(captures: Flow<Long>, scope: CoroutineScope): StateFlow<Long> =
    captures
        .runningFold(0L) { total, cents -> total + cents }
        .stateIn(scope, SharingStarted.Eagerly, 0L)
