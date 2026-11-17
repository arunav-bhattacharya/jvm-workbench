package workbench.coroutines.l06

import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.CoroutineExceptionHandler
import kotlinx.coroutines.CoroutineName
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.job
import kotlinx.coroutines.launch

class Oven(
    dispatcher: CoroutineDispatcher,
    private val reportBurned: (tray: String, error: Throwable) -> Unit,
) {
    // 2. children of a SupervisorJob are roots for error handling, so this handler sees their
    //    failures. The CoroutineName set in put tells us which tray burned.
    private val handler = CoroutineExceptionHandler { context, error ->
        reportBurned(context[CoroutineName]?.name ?: "unknown", error)
    }

    // 1. the supervisor goes in the scope's constructor: children fail alone, and the scope still
    //    waits for, counts and cancels every one of them
    private val scope = CoroutineScope(dispatcher + SupervisorJob() + handler)

    fun put(tray: String, baker: Baker): Job =
        scope.launch(CoroutineName(tray)) { baker.bake(tray) }

    val inOven: Int
        get() = scope.coroutineContext.job.children.count()

    suspend fun switchOff() {
        scope.coroutineContext.job.cancelAndJoin()
    }
}
