package workbench.coroutines.l08

import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow

/**
 * Tracks one dish. Helpers in the kitchen call [moveTo] from their own threads; the board in
 * the hall reads [status]; the kitchen log collects [transitions].
 *
 * [beforeMove] is the kitchen's hook for checks that must pass before a move (is the plate
 * warm?). It can be slow, and it runs on the calling thread.
 */
class DishTracker(
    private val dish: String,
    private val beforeMove: (Transition) -> Unit = {},
) {

    /** The current status. Callers can read it but not set it. */
    val status: StateFlow<DishStatus>
        field = MutableStateFlow(DishStatus.WAITING)

    /**
     * Every transition, in order, for the kitchen log. No replay: a late subscriber sees only
     * transitions after it subscribed. A subscriber that is busy writing must still receive
     * the transitions that happen meanwhile (buffer at least 64).
     *
     * Bug: a MutableSharedFlow with default parameters has no buffer, so tryEmit fails
     * (returns false) whenever the flow has a subscriber, and the transition is lost.
     */
    val transitions: SharedFlow<Transition>
        field = MutableSharedFlow()

    /**
     * Moves to [next] if [DishStatus.canMoveTo] allows it from the current status, and
     * publishes the transition. Returns true if this call changed the status.
     * Called from many threads at once: when two helpers try the same move, exactly one wins.
     *
     * Bug: check-then-act. Two helpers can both read COOKING, both set SERVED and both
     * return true.
     */
    fun moveTo(next: DishStatus): Boolean {
        val from = status.value
        if (!from.canMoveTo(next)) return false
        val transition = Transition(dish, from, next)
        beforeMove(transition)
        status.value = next
        transitions.tryEmit(transition)
        return true
    }
}
