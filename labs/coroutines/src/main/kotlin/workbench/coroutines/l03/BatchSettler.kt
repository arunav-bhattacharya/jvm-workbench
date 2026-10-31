package workbench.coroutines.l03

import kotlinx.coroutines.DelicateCoroutinesApi
import kotlinx.coroutines.GlobalScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import kotlin.coroutines.CoroutineContext

/**
 * Settles card batches in the background, one instance per Kafka partition.
 * The application calls [shutdown] when the partition is revoked or the service stops.
 *
 * Give the class its own scope, built from [context] plus a new Job, and start every
 * batch in that scope. (Tests pass a test dispatcher as [context].)
 */
class BatchSettler(
    private val context: CoroutineContext,
    private val settle: suspend (batchId: String) -> Unit,
) {
    /** Starts settling [batchId] in the background and returns at once. Throws IllegalStateException after [shutdown]. */
    @OptIn(DelicateCoroutinesApi::class)
    fun submit(batchId: String): Job =
        GlobalScope.launch(context) { settle(batchId) }

    /** How many submitted batches are still running. */
    val inFlight: Int
        get() = TODO("count the active children of your scope's Job")

    /** Cancels every batch still running and returns only when all of them have stopped. */
    suspend fun shutdown() {
        // nothing to cancel: GlobalScope owns the work, not this class
    }
}
