package workbench.coroutines.l08

// Shared model. This file is the same in src/main and src/solution.

enum class PaymentStatus {
    PENDING, AUTHORIZED, CAPTURED, DECLINED, REFUNDED;

    fun canMoveTo(next: PaymentStatus): Boolean = when (this) {
        PENDING -> next == AUTHORIZED || next == DECLINED
        AUTHORIZED -> next == CAPTURED || next == DECLINED
        CAPTURED -> next == REFUNDED
        DECLINED, REFUNDED -> false
    }
}

data class Transition(val paymentId: String, val from: PaymentStatus, val to: PaymentStatus)
