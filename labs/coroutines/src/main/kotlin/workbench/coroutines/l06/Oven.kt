package workbench.coroutines.l06

import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.CoroutineName
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.job
import kotlinx.coroutines.launch

/**
 * The oven from lesson 3 of this track: it bakes trays in the background while the cook does
 * other things. One instance lives as long as the kitchen is open.
 *
 * Rules:
 * - A burned tray must not cancel the other trays, or switch the oven off.
 * - Every failure is passed to [reportBurned] with the name of its tray.
 * - [switchOff] cancels the trays still baking and waits until they have stopped.
 *
 * Bug: the scope has a plain Job, so the first burned tray cancels the scope and with it every
 * other tray, and the oven never bakes again. Failures go to the thread's uncaught exception
 * handler instead of [reportBurned].
 *
 * Don't fix it with launch(SupervisorJob()): the last section of the lesson shows why that
 * breaks [switchOff].
 */
class Oven(
    dispatcher: CoroutineDispatcher,
    private val reportBurned: (tray: String, error: Throwable) -> Unit,
) {
    private val scope = CoroutineScope(dispatcher + Job())

    /** Puts a tray in the oven and returns at once. */
    fun put(tray: String, baker: Baker): Job =
        scope.launch(CoroutineName(tray)) { baker.bake(tray) }

    /** How many trays are still baking. */
    val inOven: Int
        get() = scope.coroutineContext.job.children.count()

    suspend fun switchOff() {
        scope.coroutineContext.job.cancelAndJoin()
    }
}
