package workbench.coroutines.l06

import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlin.time.Duration

/**
 * Bakes every tray of a bake-sale [order] at the same time and returns how each tray went.
 * The caller waits for the result.
 *
 * Rules:
 * - One burned tray must not stop the others: its outcome is Failed(<exception message>).
 * - A tray that takes longer than [timeout] counts as Failed("timed out").
 * - If the caller is cancelled, every tray is cancelled and bakeAll does not return a map.
 *
 * Bug: runCatching around await() looks like it handles failures, but a failed async
 * cancels this coroutineScope (and the other trays) whether or not anyone awaits it.
 * There is no timeout either.
 */
suspend fun bakeAll(order: String, bakers: Map<Tray, Baker>, timeout: Duration): Map<Tray, Outcome> =
    coroutineScope {
        val trays = bakers.mapValues { (_, baker) -> async { baker.bake(order) } }
        trays.mapValues { (_, tray) ->
            runCatching { tray.await() }
                .fold({ Outcome.Baked }, { Outcome.Failed(it.message ?: it.toString()) })
        }
    }
