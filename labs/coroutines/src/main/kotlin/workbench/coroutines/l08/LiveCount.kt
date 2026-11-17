package workbench.coroutines.l08

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.runningFold
import kotlinx.coroutines.flow.stateIn

/**
 * The running count of plates served tonight, shown live on screens around the house.
 * [servings] emits the number of plates in each batch that leaves the kitchen.
 *
 * - Start collecting [servings] only when the first screen subscribes.
 * - Every screen shares ONE collection of [servings].
 * - Keep collecting for 5 seconds after the last screen leaves, so a screen that restarts
 *   doesn't restart the upstream; then stop.
 * - The value is 0 before any plate has been served.
 *
 * Bug: Eagerly starts collecting at once, with nobody watching, and never stops.
 */
fun liveServedCount(servings: Flow<Int>, scope: CoroutineScope): StateFlow<Int> =
    servings
        .runningFold(0) { total, plates -> total + plates }
        .stateIn(scope, SharingStarted.Eagerly, 0)
