package workbench.coroutines.l06

import kotlinx.coroutines.async
import kotlinx.coroutines.supervisorScope
import kotlinx.coroutines.withTimeoutOrNull
import kotlin.coroutines.cancellation.CancellationException
import kotlin.time.Duration

suspend fun bakeAll(order: String, bakers: Map<Tray, Baker>, timeout: Duration): Map<Tray, Outcome> =
    // 1. a supervisor: a failed child does not cancel its siblings or this scope.
    //    Its exception is kept in its Deferred, and await() rethrows it.
    supervisorScope {
        val trays = bakers.mapValues { (_, baker) ->
            // 2. each tray gets its own deadline; null means "timed out"
            async { withTimeoutOrNull(timeout) { baker.bake(order) } }
        }
        trays.mapValues { (_, tray) ->
            try {
                if (tray.await() == null) Outcome.Failed("timed out") else Outcome.Baked
            } catch (e: CancellationException) {
                throw e // 3. the caller was cancelled: don't turn that into an outcome
            } catch (e: Exception) {
                Outcome.Failed(e.message ?: e.toString())
            }
        }
    }
