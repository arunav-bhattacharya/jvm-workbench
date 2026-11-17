package workbench.coroutines.l03

import kotlinx.coroutines.DelicateCoroutinesApi
import kotlinx.coroutines.GlobalScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import kotlin.coroutines.CoroutineContext

/**
 * Bakes trays in the background, while the rest of the program carries on.
 * The program calls [switchOff] when the kitchen closes for the night.
 *
 * Give the class its own scope, built from [context] plus a new Job, and start every
 * tray in that scope. (Tests pass a test dispatcher as [context].)
 */
class Oven(
    private val context: CoroutineContext,
    private val bake: suspend (tray: String) -> Unit,
) {
    /** Starts baking [tray] in the background and returns at once. Throws IllegalStateException after [switchOff]. */
    @OptIn(DelicateCoroutinesApi::class)
    fun put(tray: String): Job =
        GlobalScope.launch(context) { bake(tray) }

    /** How many trays are still baking. */
    val inOven: Int
        get() = TODO("count the active children of your scope's Job")

    /** Cancels every tray still baking and returns only when all of them have stopped. */
    suspend fun switchOff() {
        // nothing to cancel: GlobalScope owns the work, not this class
    }
}
