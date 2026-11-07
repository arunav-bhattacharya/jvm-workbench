package workbench.coroutines.l08

import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow

class PaymentTracker(
    private val paymentId: String,
    private val beforeMove: (Transition) -> Unit = {},
) {

    // explicit backing field (stable since Kotlin 2.4): callers see a StateFlow, and inside
    // the class `status` smart-casts to the MutableStateFlow in `field`
    val status: StateFlow<PaymentStatus>
        field = MutableStateFlow(PaymentStatus.PENDING)

    // replay 0: no history for late subscribers. extraBufferCapacity 64: tryEmit can hand a
    // transition to a busy subscriber instead of failing. SUSPEND (the default) keeps every one
    // until the buffer is full, and then tryEmit returns false rather than dropping silently.
    val transitions: SharedFlow<Transition>
        field = MutableSharedFlow(replay = 0, extraBufferCapacity = 64)

    fun moveTo(next: PaymentStatus): Boolean {
        while (true) {
            val from = status.value
            if (!from.canMoveTo(next)) return false
            val transition = Transition(paymentId, from, next)
            beforeMove(transition)
            // compareAndSet is atomic: it only moves if the status is still `from`, so only one
            // thread can move AUTHORIZED -> CAPTURED
            if (status.compareAndSet(from, next)) {
                check(transitions.tryEmit(transition)) { "audit buffer full for $paymentId" }
                return true
            }
            // someone else changed the status between our read and our CAS: look again
        }
    }
}
