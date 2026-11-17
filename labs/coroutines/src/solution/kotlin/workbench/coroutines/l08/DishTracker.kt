package workbench.coroutines.l08

import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow

class DishTracker(
    private val dish: String,
    private val beforeMove: (Transition) -> Unit = {},
) {

    // explicit backing field (stable since Kotlin 2.4): callers see a StateFlow, and inside
    // the class `status` smart-casts to the MutableStateFlow in `field`
    val status: StateFlow<DishStatus>
        field = MutableStateFlow(DishStatus.WAITING)

    // replay 0: no history for late subscribers. extraBufferCapacity 64: tryEmit can hand a
    // transition to a busy subscriber instead of failing. SUSPEND (the default) keeps every one
    // until the buffer is full, and then tryEmit returns false rather than dropping silently.
    val transitions: SharedFlow<Transition>
        field = MutableSharedFlow(replay = 0, extraBufferCapacity = 64)

    fun moveTo(next: DishStatus): Boolean {
        while (true) {
            val from = status.value
            if (!from.canMoveTo(next)) return false
            val transition = Transition(dish, from, next)
            beforeMove(transition)
            // compareAndSet is atomic: it only moves if the status is still `from`, so only one
            // helper can move COOKING -> SERVED
            if (status.compareAndSet(from, next)) {
                check(transitions.tryEmit(transition)) { "kitchen log buffer full for $dish" }
                return true
            }
            // someone else changed the status between our read and our CAS: look again
        }
    }
}
