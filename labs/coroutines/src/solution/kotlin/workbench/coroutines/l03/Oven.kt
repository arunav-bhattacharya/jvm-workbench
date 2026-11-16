package workbench.coroutines.l03

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.isActive
import kotlinx.coroutines.job
import kotlinx.coroutines.launch
import kotlin.coroutines.CoroutineContext

class Oven(
    context: CoroutineContext,
    private val bake: suspend (tray: String) -> Unit,
) {
    // 1. the class owns a scope: its Job is the parent of every tray
    private val scope = CoroutineScope(context + Job())

    fun put(tray: String): Job {
        // 2. a cancelled scope would start the tray already cancelled; refuse loudly instead
        check(scope.isActive) { "the oven is switched off" }
        return scope.launch { bake(tray) }
    }

    // completed children leave the list, so this counts the trays still baking
    val inOven: Int
        get() = scope.coroutineContext.job.children.count()

    suspend fun switchOff() {
        // 3. cancel the parent Job: every child is cancelled; join waits until they have stopped
        scope.coroutineContext.job.cancelAndJoin()
    }
}
