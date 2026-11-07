package workbench.coroutines.l06

import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.CoroutineName
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.job
import kotlinx.coroutines.launch

/**
 * Sends notifications in the background, after the payment response has gone out.
 * One instance lives as long as the service.
 *
 * Rules:
 * - A failed notification must not cancel the other notifications, or the service.
 * - Every failure is passed to [reportFailure] with its payment id.
 * - [close] cancels the notifications still running and waits until they have stopped.
 *
 * Bug: the scope has a plain Job, so the first failure cancels the scope and with it every
 * other notification, and the service never runs another one. Failures go to the thread's
 * uncaught exception handler instead of [reportFailure].
 *
 * Don't fix it with launch(SupervisorJob()): the last section of the lesson shows why that breaks [close].
 */
class NotificationService(
    dispatcher: CoroutineDispatcher,
    private val reportFailure: (paymentId: String, error: Throwable) -> Unit,
) {
    private val scope = CoroutineScope(dispatcher + Job())

    /** Starts sending in the background and returns at once. */
    fun notifyLater(paymentId: String, sender: Sender): Job =
        scope.launch(CoroutineName(paymentId)) { sender.send(paymentId) }

    /** How many notifications are still running. */
    val pending: Int
        get() = scope.coroutineContext.job.children.count()

    suspend fun close() {
        scope.coroutineContext.job.cancelAndJoin()
    }
}
