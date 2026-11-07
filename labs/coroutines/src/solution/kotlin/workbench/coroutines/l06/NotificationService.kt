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

class NotificationService(
    dispatcher: CoroutineDispatcher,
    private val reportFailure: (paymentId: String, error: Throwable) -> Unit,
) {
    // 2. children of a SupervisorJob are roots for error handling, so this handler sees their failures.
    //    The CoroutineName set in notifyLater tells us which payment failed.
    private val handler = CoroutineExceptionHandler { context, error ->
        reportFailure(context[CoroutineName]?.name ?: "unknown", error)
    }

    // 1. the supervisor goes in the scope's constructor: children fail alone, and the scope still
    //    waits for, counts and cancels every one of them
    private val scope = CoroutineScope(dispatcher + SupervisorJob() + handler)

    fun notifyLater(paymentId: String, sender: Sender): Job =
        scope.launch(CoroutineName(paymentId)) { sender.send(paymentId) }

    val pending: Int
        get() = scope.coroutineContext.job.children.count()

    suspend fun close() {
        scope.coroutineContext.job.cancelAndJoin()
    }
}
