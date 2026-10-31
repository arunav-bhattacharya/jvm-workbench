package workbench.coroutines.l03

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.isActive
import kotlinx.coroutines.job
import kotlinx.coroutines.launch
import kotlin.coroutines.CoroutineContext

class BatchSettler(
    context: CoroutineContext,
    private val settle: suspend (batchId: String) -> Unit,
) {
    // 1. the class owns a scope: its Job is the parent of every batch
    private val scope = CoroutineScope(context + Job())

    fun submit(batchId: String): Job {
        // 2. a cancelled scope would start the batch already cancelled; refuse loudly instead
        check(scope.isActive) { "settler is shut down" }
        return scope.launch { settle(batchId) }
    }

    // completed children leave the list, so this counts the batches still running
    val inFlight: Int
        get() = scope.coroutineContext.job.children.count()

    suspend fun shutdown() {
        // 3. cancel the parent Job: every child is cancelled; join waits until they have stopped
        scope.coroutineContext.job.cancelAndJoin()
    }
}
