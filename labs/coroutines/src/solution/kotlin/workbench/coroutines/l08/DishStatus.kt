package workbench.coroutines.l08

// Shared model. This file is the same in src/main and src/solution.

enum class DishStatus {
    WAITING, COOKING, SERVED, CANCELLED, CLEARED;

    fun canMoveTo(next: DishStatus): Boolean = when (this) {
        WAITING -> next == COOKING || next == CANCELLED
        COOKING -> next == SERVED || next == CANCELLED
        SERVED -> next == CLEARED
        CANCELLED, CLEARED -> false
    }
}

data class Transition(val dish: String, val from: DishStatus, val to: DishStatus)
