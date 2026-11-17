package workbench.flows.l07

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn

/**
 * The board in the hall that shows the latest oven reading. People only glance at it with
 * `.value` as they walk past; nobody collects it.
 *
 * - Collect [feed] once for the whole house, in [scope], from the moment the board is built.
 * - `.value` is `null` until the first reading arrives, then always the latest reading.
 * - The feed sometimes fails with an `IOException` (the thermometer drops its connection).
 *   Keep showing the last reading, wait 1,000 ms, and collect the feed again.
 *
 * Bug: a helper copied this from the screen code. The board shows `null` for ever.
 */
fun hallBoard(feed: Flow<Reading>, scope: CoroutineScope): StateFlow<Reading?> =
    feed.stateIn(scope, SharingStarted.WhileSubscribed(5_000), null)

/**
 * The live reading for the screens on the kitchen wall. Each screen that is switched on
 * collects the returned flow.
 *
 * - Don't collect [feed] while no screen is on.
 * - All screens share one collection of [feed].
 * - A screen that comes back on within 5,000 ms of the last one going off must not restart the
 *   feed (a screen that flickers off and on is no reason to reconnect to the thermometer).
 * - Stop collecting 5,000 ms after the last screen goes off.
 * - Once the feed has stopped, a screen switched on later must not show the old reading:
 *   it shows `null` until the fresh feed delivers its first reading.
 *
 * Bug: the defaults reconnect to the thermometer every time a screen flickers.
 */
fun screenFeed(feed: Flow<Reading>, scope: CoroutineScope): StateFlow<Reading?> =
    feed.stateIn(scope, SharingStarted.WhileSubscribed(), null)
