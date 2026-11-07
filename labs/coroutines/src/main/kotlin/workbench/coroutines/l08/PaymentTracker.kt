package workbench.coroutines.l08

import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow

/**
 * Tracks one payment. Kafka listener threads call [moveTo]; status pages read [status];
 * the audit writer collects [transitions].
 */
class PaymentTracker(private val paymentId: String) {

    /** The current status. Callers can read it but not set it. */
    val status: StateFlow<PaymentStatus>
        field = MutableStateFlow(PaymentStatus.PENDING)

    /**
     * Every transition, in order, for the audit log. No replay: a late subscriber sees only
     * transitions after it subscribed. A subscriber that is busy writing must still receive
     * the transitions that happen meanwhile (buffer at least 64).
     *
     * Bug: a MutableSharedFlow with default parameters has no buffer, so tryEmit fails
     * (returns false) whenever a subscriber is busy, and the transition is lost.
     */
    val transitions: SharedFlow<Transition>
        field = MutableSharedFlow()

    /**
     * Moves to [next] if [PaymentStatus.canMoveTo] allows it from the current status, and
     * publishes the transition. Returns true if this call changed the status.
     * Called from many threads at once: when two threads try the same move, exactly one wins.
     *
     * Bug: check-then-act. Two threads can both read AUTHORIZED, both set CAPTURED and both
     * return true.
     */
    fun moveTo(next: PaymentStatus): Boolean {
        val from = status.value
        if (!from.canMoveTo(next)) return false
        status.value = next
        transitions.tryEmit(Transition(paymentId, from, next))
        return true
    }
}
